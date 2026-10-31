-- Patent Yard database (Supabase Postgres). Paste into the Supabase SQL editor and run once; it is safe to re-run.
--
--   profiles       display name per account (created automatically at sign-up)
--   reservations   one holder per patent, 30-day holds, at most 5 per account, renew in the last 7 days
--   ideas          saved inventions, private to their owner
--   messages       contact form and "report a problem" (write-only from the site; read them in the dashboard)
--
-- Browsers use the anon key. Row-level security and the functions below are the only way in:
-- nobody can read another person's email, ideas or account id, or change their reservations.
-- Function errors carry a short code the site understands: not_signed_in, taken, limit, not_yours, too_early, bad_patent, bad_note.

-- ---------------------------------------------------------------- profiles
create table if not exists public.profiles (
  id uuid primary key references auth.users on delete cascade,
  display_name text not null default '' check (char_length(display_name) <= 40),
  created_at timestamptz not null default now()
);
alter table public.profiles enable row level security;
drop policy if exists "read own profile" on public.profiles;
create policy "read own profile" on public.profiles for select to authenticated using (id = auth.uid());

create or replace function public.handle_new_user() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  insert into public.profiles (id, display_name)
  values (new.id, left(trim(coalesce(new.raw_user_meta_data ->> 'display_name', '')), 40))
  on conflict (id) do nothing;
  return new;
end $$;
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created after insert on auth.users for each row execute function public.handle_new_user();

create or replace function public.set_display_name(p_name text) returns void
language plpgsql security definer set search_path = '' as $$
begin
  if auth.uid() is null then raise exception 'not_signed_in'; end if;
  insert into public.profiles (id, display_name) values (auth.uid(), left(trim(coalesce(p_name, '')), 40))
  on conflict (id) do update set display_name = excluded.display_name;
end $$;

-- ---------------------------------------------------------------- reservations
create table if not exists public.reservations (
  patent_id text primary key check (patent_id ~ '^US-[A-Z]*[0-9]{5,11}-[A-Z][0-9]?$'),
  user_id uuid not null references auth.users on delete cascade,
  note text not null default '' check (char_length(note) <= 140),
  reserved_at timestamptz not null default now(),
  renewed_at timestamptz,
  expires_at timestamptz not null
);
create index if not exists reservations_user on public.reservations (user_id);
alter table public.reservations enable row level security;  -- no policies: only the functions below touch it

-- Active holds for everyone to see: who (display name only), the note and the dates. Never the account id.
create or replace function public.list_reservations()
returns table (patent_id text, holder text, note text, reserved_at timestamptz, renewed_at timestamptz, expires_at timestamptz, mine boolean)
language sql stable security definer set search_path = '' as $$
  select r.patent_id, coalesce(nullif(p.display_name, ''), 'A builder'), r.note, r.reserved_at, r.renewed_at, r.expires_at,
         coalesce(r.user_id = auth.uid(), false)
  from public.reservations r left join public.profiles p on p.id = r.user_id
  where r.expires_at > now()
  order by r.reserved_at
$$;

create or replace function public.reserve_patent(p_patent text, p_note text) returns void
language plpgsql security definer set search_path = '' as $$
declare uid uuid := auth.uid();
begin
  if uid is null then raise exception 'not_signed_in'; end if;
  if p_patent is null or p_patent !~ '^US-[A-Z]*[0-9]{5,11}-[A-Z][0-9]?$' then raise exception 'bad_patent'; end if;
  if char_length(coalesce(p_note, '')) > 140 then raise exception 'bad_note'; end if;
  perform pg_advisory_xact_lock(hashtext('reserve:' || uid::text));  -- one request at a time per account, so the limit holds
  delete from public.reservations where patent_id = p_patent and expires_at <= now();
  if (select count(*) from public.reservations where user_id = uid and expires_at > now()) >= 5 then raise exception 'limit'; end if;
  insert into public.reservations (patent_id, user_id, note, expires_at) values (p_patent, uid, coalesce(p_note, ''), now() + interval '30 days');
exception when unique_violation then
  raise exception 'taken';
end $$;

create or replace function public.release_patent(p_patent text) returns void
language plpgsql security definer set search_path = '' as $$
begin
  if auth.uid() is null then raise exception 'not_signed_in'; end if;
  delete from public.reservations where patent_id = p_patent and user_id = auth.uid();
  if not found then raise exception 'not_yours'; end if;
end $$;

create or replace function public.renew_patent(p_patent text) returns void
language plpgsql security definer set search_path = '' as $$
declare r public.reservations;
begin
  if auth.uid() is null then raise exception 'not_signed_in'; end if;
  select * into r from public.reservations where patent_id = p_patent and user_id = auth.uid() and expires_at > now() for update;
  if not found then raise exception 'not_yours'; end if;
  if r.expires_at - now() > interval '7 days' then raise exception 'too_early'; end if;
  update public.reservations set expires_at = now() + interval '30 days', renewed_at = now() where patent_id = p_patent;
end $$;

-- ---------------------------------------------------------------- saved inventions
create table if not exists public.ideas (
  id uuid primary key,
  user_id uuid not null default auth.uid() references auth.users on delete cascade,
  patent_id text check (patent_id is null or patent_id ~ '^[A-Z]{2}-[A-Z0-9]{1,24}(-[A-Z][0-9]?)?$'),  -- any office (functions/_lib.js worldId)
  data jsonb not null check (pg_column_size(data) < 100000),
  updated_at timestamptz not null default now()
);
create index if not exists ideas_user on public.ideas (user_id, updated_at desc);
alter table public.ideas enable row level security;
drop policy if exists "own ideas: read" on public.ideas;
drop policy if exists "own ideas: add" on public.ideas;
drop policy if exists "own ideas: change" on public.ideas;
drop policy if exists "own ideas: delete" on public.ideas;
create policy "own ideas: read" on public.ideas for select to authenticated using (user_id = auth.uid());
create policy "own ideas: add" on public.ideas for insert to authenticated with check (user_id = auth.uid());
create policy "own ideas: change" on public.ideas for update to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid());
create policy "own ideas: delete" on public.ideas for delete to authenticated using (user_id = auth.uid());

create or replace function public.ideas_cap() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  if (select count(*) from public.ideas where user_id = new.user_id) >= 200 then raise exception 'limit'; end if;
  return new;
end $$;
drop trigger if exists ideas_cap on public.ideas;
create trigger ideas_cap before insert on public.ideas for each row execute function public.ideas_cap();

-- ---------------------------------------------------------------- contact form and "report a problem" (read them in the Supabase table editor)
create table if not exists public.messages (
  id bigint generated always as identity primary key,
  kind text not null check (kind in ('contact', 'report')),
  patent_id text check (patent_id is null or patent_id ~ '^[A-Z]{2}-[A-Z0-9]{1,24}(-[A-Z][0-9]?)?$'),  -- any office (functions/_lib.js worldId)
  email text not null default '' check (char_length(email) <= 200),
  body text not null check (char_length(body) between 1 and 4000),
  user_id uuid default auth.uid() references auth.users on delete set null,
  created_at timestamptz not null default now()
);
alter table public.messages enable row level security;
drop policy if exists "anyone can send" on public.messages;
create policy "anyone can send" on public.messages for insert to anon, authenticated
  with check (user_id is null or user_id = auth.uid());

create or replace function public.messages_flood_guard() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  if (select count(*) from public.messages where created_at > now() - interval '1 hour') >= 60 then raise exception 'limit'; end if;
  return new;
end $$;
drop trigger if exists messages_flood_guard on public.messages;
create trigger messages_flood_guard before insert on public.messages for each row execute function public.messages_flood_guard();

-- ---------------------------------------------------------------- account deletion (removes everything above through the cascades)
create or replace function public.delete_my_account() returns void
language plpgsql security definer set search_path = '' as $$
begin
  if auth.uid() is null then raise exception 'not_signed_in'; end if;
  delete from auth.users where id = auth.uid();
end $$;

-- ---------------------------------------------------------------- who may call what
revoke all on public.reservations from anon, authenticated;
revoke all on public.profiles from anon, authenticated;
revoke all on public.ideas from anon, authenticated;
revoke all on public.messages from anon, authenticated;
grant insert on public.messages to anon, authenticated;
grant select on public.profiles to authenticated;
grant select, insert, update, delete on public.ideas to authenticated;

revoke execute on function public.list_reservations(), public.reserve_patent(text, text), public.release_patent(text), public.renew_patent(text),
  public.set_display_name(text), public.delete_my_account(), public.handle_new_user(), public.ideas_cap(), public.messages_flood_guard() from public, anon, authenticated;
grant execute on function public.list_reservations() to anon, authenticated;
grant execute on function public.reserve_patent(text, text), public.release_patent(text), public.renew_patent(text),
  public.set_display_name(text), public.delete_my_account() to authenticated;
