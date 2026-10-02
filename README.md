# Patent Yard

A free register of US patents whose protection has ended. Every listing links to the official record it came from,
is rechecked against USPTO records daily, and comes with its full file: claims, description, original drawing sheets,
family and citations. Builders can reserve a patent and take it to their own Claude with a ready-made prompt and PDF
brief (modern directions, novelty screen, provisional draft, sketches, prototype plan).

Two front ends share one data pipeline:

- **Website** (`web/`): Cloudflare Pages, one real page per patent. Accounts and reservations use Supabase's free tier. No AI runs on the site; the "Reinvent with Claude" kit writes a prompt and a PDF brief in the
  visitor's browser for their own Claude account. Address: https://patentyard.pages.dev.
- **claude.ai version** (`site/`): the original single-page app, published as a claude.ai Artifact
  (https://claude.ai/artifact/9Qg7NM7egHbxqJ2FWMEAmt, private until shared), where the AI tools run inside Claude.

## Layout

```
pipeline/            data pipeline, Python 3.9+ standard library only
  pipeline.py        command line (below)
  uspto.py           USPTO sources: Official Gazette parser, Patent Public Search client
  patents.py         fields, text parsing, and the rules for "free to use"
  drawings.py        drawing sheet -> small cropped PNG (nothing added to the drawing)
  register.py        harvest, dossier download, daily verification, notes
  build.py           collect() for both front ends; writes site/data/ for the claude.ai version
  website.py         writes web/dist/ (pages, shards, catalog, sitemaps, feed) and checks every link
  test_pipeline.py   checks for everything above
  curation.json      plain-English notes per patent (Patent Yard's editorial layer)
  raw/               downloaded records, drawings and Gazette cache (not published)
web/
  config.json        site address and the Supabase project URL + anon key (public values)
  static/            copied into dist: site.css, assets/js/*.js, favicon, _headers (security and cache headers)
  functions/         Cloudflare Pages Functions: serve patent pages, drawings and kit data out of the shards
                     (site.json is written by the build)
  supabase/schema.sql  tables, row-level security and functions for accounts, reservations, saved inventions
                     and contact / "report a problem" messages
  dev/               preview.py (local copy, --mock adds a stand-in backend), serve.py, mock-backend.js, smoke.js
  dist/              the built site (generated)
site/                the claude.ai version: index.html + data/
dev/                 test tools for the claude.ai version
```

## Sources

| Status on the site | Where it comes from | Rule |
|---|---|---|
| Lapsed, fee not paid | USPTO Official Gazette, "Notice of Expiration of Patents Due to Failure to Pay Maintenance Fee" | Issues 4-12 months old; any patent on a year of "Patents Reinstated" notices is excluded |
| Expired, full term | USPTO Patent Public Search, patents filed 1996-2001 | Filed 24+ years ago and granted within 4 years of filing (so term adjustments are small); drug and chemistry classes skipped |
| Likely abandoned | USPTO Patent Public Search, applications filed 2013-2017 | No patent anywhere in the family and no family filing in 7+ years; labeled as inferred |

Every candidate must pass the family check: no other US family member may still be in force or pending.
Each patent page links to its source record, the USPTO PDF, Patent Center, Patent Public Search, Google Patents,
Justia, FreePatentsOnline and Espacenet for cross-checking.

## Commands

```
cd pipeline
python3 pipeline.py bulk [--minutes 300]  # every lapsed patent of the past year (about 180,000): family check (those
                                          # that pass are listed at once), then text and first drawings side by side,
                                          # then the remaining sheets; resumable, 4 sessions per step
python3 pipeline.py archive               # everything that can no longer be in force, as compact records: utility
                                          # patents past their full term (1790-2012), designs granted 15+ years ago,
                                          # applications published 2001-2016 with no patent and no family filing in
                                          # 7 years; resumable (raw/archive/done.json)
python3 pipeline.py publish [--every 120] # rebuild and redeploy every N minutes, until stopped (holds web/.build.lock)
python3 pipeline.py harvest --per 6       # new patents per field from all sources; --sources lapsed,expired
                                          # --only robotics,ai  --resume (continue a partial run)
python3 pipeline.py todo [--limit 40]     # the most promising patents without a note (JSON lines)
python3 pipeline.py notes < notes.json    # merge notes {"US-...": {"name","hook","twist","build","tags","ind"} | {"skip": true}}
python3 pipeline.py enrich [--sheets 400] # full dossier for new patents (up to 8 drawing sheets each),
                                          # then at most N extra sheets for existing ones
python3 pipeline.py verify                # Gazette and term check for every listing, family recheck for 3,000 a day
python3 pipeline.py web                   # build web/dist (fails on any broken internal link)
python3 pipeline.py build                 # write site/data/ for the claude.ai version
python3 pipeline.py test
```

USPTO allows about one request a second. The client slows itself down when USPTO answers "too many requests",
rate-limited downloads are retried after a pause, and anything still missing is picked up by the next run.

The scheduled task "Patent Yard daily check and refresh" runs verify, a capped sheet top-up, the builds and the deploys
every morning, and harvest + notes + enrich once the last harvest is 6 days old (normally Wednesdays, the day after
the Official Gazette publishes), so a missed day catches up by itself.

## How the website holds 180,000 patents for free

A free Cloudflare Pages site may hold 20,000 files, so patent pages, drawing sheets and kit data are packed into
2,048 shard files each (`dist/shard/{p,i,k}/<patent number % 2048>.bin`: a 4-byte length, a JSON index, then the
items; pages and kit data gzipped). The Functions in `web/functions` answer `/patents/<id>/`, `/img/p/<id>/<n>.png` and
`/data/p/<id>.json` from them (and `/patents/<number>` redirects to the full id). Browse, field pages, search and the
studio picker load the catalog in pieces: `/data/latest.json` names the current version, then `/v/<version>/keys.bin`
(field, status, build and dates for every patent, for filtering and sorting), `c/<n>.json` (card text, 256 patents
per file) and `s/<ab>.json` (search index for words starting with "ab"). Nothing on a patent page depends on the date
(the verified date and totals are filled in from latest.json), so unchanged shards are not uploaded again.
Patents without a written note are listed under their official title and the first sentence of their abstract.
Free-plan ceiling: Functions get 100,000 requests a day (a patent page view is one, plus one per drawing shown).

Fields follow a patent's main (first) CPC classification, longest prefix first (patents.py FIELDS); a prefix longer
than a subclass names a main group and must match whole (G06F1 is G06F1/16, not G06F12/02). USPTO text fields are
cleaned of markup and HTML entities (patents.plain), and typo'd dates (year 0204) are ignored.

## The archive

Archive patents have no pre-built page: `dist/shard/a/<n>.bin` holds one small gzipped record each, and
`functions/_archive.js` pours it into the page shell `dist/tpl/archive/`. Archive search uses its own files under
`/v/x<hash>/`: `s/<crc32(word) % 1024>.json` (exact words; words in more than 1.5% of titles are not indexed and are
skipped in queries) and `c/<n>.json` (card text, 1,536 per file, newest first). Browse switches to it with `?in=archive`.
Builds go to `web/dist.new` and are swapped in when complete, so a deploy never sees half a site.

## Website features

Every patent has its own page (drawings with a viewer, claims with a claim tree, full description, timeline, fee
history, family, citations, sources and cross-check links). Browse has whole-word search ranked by relevance (names,
then titles, summaries, tags, owners and abstracts), filters and sorting, all kept in the URL. The header has instant
search suggestions and a light/dark switch; /settings/ has theme, drawings-in-dark-mode, text size, motion and default
sort (saved in the browser) plus account settings (name, password, sign out, delete). Also: a command palette (Ctrl or
Cmd + K), "Surprise me", saved patents and recently viewed (this browser), previous/next in a field ([ and ]), an
Insights page with animated charts, a "just added" ticker, Google sign-in, and a slot for every drawing sheet (ones
not downloaded yet link to the USPTO PDF). The stylesheet's file name carries
its content hash so it can be cached for a year without ever going stale; scripts always revalidate.

## Website: test and deploy

```
python3 web/dev/preview.py /tmp/py-web --mock      # local copy with a stand-in account backend
python3 web/dev/serve.py /tmp/py-web 8766          # then open http://localhost:8766
```
In the browser console of a page: `await runSuite("header" | "home" | "browse" | "patent" | "patent2" | "studio" |
"contact" | "account" | "account2" | "google" | "google2" | "features" | "features2" | "insights" | "settings" | "settings2" | "redirects")`.
The local server reads patent pages from the shards the same way the Functions do. The server sends the production security headers from `_headers`.

Live at https://patentyard.pages.dev. Deploy from `web/` so the Functions go too (Cloudflare Pages, free; logged in
once with `npx wrangler login`): `cd web && npx --yes wrangler@4 pages deploy dist --project-name patentyard --branch main --commit-dirty=true`.
The site works without accounts; to turn them on:

1. Create a free Supabase project, open its SQL editor, and run `web/supabase/schema.sql`.
2. In Authentication > URL configuration, set the Site URL to the site address and add `<site>/account/` as a redirect URL.
3. Copy the project URL and the anon public key into `web/config.json`, rebuild and deploy.
4. Optional, for "Continue with Google": create an OAuth client (Web application) in Google Cloud Console with the
   redirect URI `https://<project>.supabase.co/auth/v1/callback`, then paste its client ID and secret into Supabase,
   Authentication > Sign In / Providers > Google, and enable it. The button appears on its own once it's on.

Messages from the contact form and each patent's "Report a problem" button land in the `messages` table; read them
in Supabase's table editor. Supabase's built-in email sender allows only a few emails an hour. If sign-ups grow, add a custom SMTP sender
(for example a free Resend account) in Supabase's Auth settings.

## claude.ai version: publishing

Republish `site/index.html` with every file in `site/data/` (mapped to `data/<name>`) to the artifact URL above.
One publish call accepts at most 255 file entries including removals, so send the doc bundles in a second call.

## Reservations

One holder per patent, 30-day holds, at most 5 per account, renewable in the last 7 days. On the website they live in
Supabase and are enforced by the database functions in `schema.sql`; on the claude.ai version they live in the
artifact's database with per-viewer access rules. A reservation is a courtesy flag between users with no legal effect.

## Deadline

Patent Public Search will require a USPTO.gov sign-in from **November 7, 2026**. After that, harvest, enrich and verify
need either a signed-in session or the USPTO Open Data Portal API (free key at data.uspto.gov/apikey). The Gazette part
keeps working without an account.

Not legal advice.
