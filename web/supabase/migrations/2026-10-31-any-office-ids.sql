-- 2026-10-31. Run once in the Supabase SQL editor (also folded into schema.sql).
-- 1. "Report a problem" and saved inventions failed for patents from other offices (EP, CA, AU and the world
--    records): the patent_id checks accepted US numbers only. Accept any office's number, the same shape the site's
--    functions use (functions/_lib.js worldId). Reservations stay US-only on purpose.
alter table public.messages drop constraint if exists messages_patent_id_check;
alter table public.messages add constraint messages_patent_id_check
  check (patent_id is null or patent_id ~ '^[A-Z]{2}-[A-Z0-9]{1,24}(-[A-Z][0-9]?)?$');
alter table public.ideas drop constraint if exists ideas_patent_id_check;
alter table public.ideas add constraint ideas_patent_id_check
  check (patent_id is null or patent_id ~ '^[A-Z]{2}-[A-Z0-9]{1,24}(-[A-Z][0-9]?)?$');
-- 2. Supabase's own rls_auto_enable() helper is SECURITY DEFINER and callable through the API by anyone (advisor 0028/0029).
--    Nothing on the site calls it.
revoke execute on function public.rls_auto_enable() from public, anon, authenticated;
