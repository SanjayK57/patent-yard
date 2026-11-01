# Patent Yard overhaul: final report

The directive Sanjay pasted on 2026-10-31 asked for these deliverables (its section 32). This report covers them.
Work happened on branch `overhaul` (worktree `~/PatentYard-overhaul`) and was fast-forwarded into `main` batch by batch;
the publisher in `~/PatentYard` deploys `main` every ~2 hours. The running record, with how each item was verified, is
`docs/OVERHAUL.md`.

## 1. Source changes
16 commits, `66576e9` to `5c481ec` (plus checklist commits). Main areas: `pipeline/website.py` (templates, copy,
statistics, Opportunities model), `web/static/assets/site.css` (design system), `web/static/assets/js/*` (Studio
prompts, PDF, viewer, cards), `web/functions/*` (archive and world pages), `web/static/_headers` (CSP),
`web/supabase/` (schema and migration), new `web/static/assets/fonts` and `web/static/assets/vendor`.

## 2. Design system
`DESIGN.md`. In short: IBM Plex Sans for Patent Yard's words, IBM Plex Serif for the patent's own text, IBM Plex Mono
for numbers; warm paper (light) and graphite (dark); one safety-orange accent for focus and links, ink-filled primary
buttons; fixed status colors, each always with its word; drawings on a white sheet with a FIG caption; no glows,
gradient text, background grids, glass blur, fake window chrome or "PATENT YARD //" labels. Motion: one curve, three
durations, cross-page view transitions, all off under reduced motion.

## 3. Security report
Reviewed: Supabase schema, RLS policies, grants and CHECK constraints against the live database (read-only SQL); every
definer function; Pages Functions' HTML escaping, input validation and caching; client-side rendering of user text
(reservation notes, idea names); CSP and other headers on static and Function responses; third-party requests;
vendored dependencies (`npm audit`).

Fixed:
- `public.rls_auto_enable()` was a SECURITY DEFINER function callable by anyone through the API. Execute revoked
  (verified: not executable by `anon` or `authenticated`).
- Third-party code and fonts (jsDelivr, cdnjs, Google Fonts) replaced by copies served from the site; CSP is now
  `script-src 'self'`, `font-src 'self'`, styles from the site only (inline style attributes allowed, no inline style
  blocks), `connect-src` limited to the project's own Supabase host and the world-data host. jsPDF moved from 2.5.1
  (known issues) to 4.2.1. `npm audit` on the vendored versions: 0 vulnerabilities.
- The contact form no longer renders a submittable form without JavaScript (a plain submit would have put the message
  and email in the URL); it appears only once the backend has loaded. The account library load times out after 10 s
  instead of leaving pages waiting.
- Report-a-problem and saved inventions for non-US patents failed a US-only CHECK; widened to any office's number
  (migration run with Sanjay's approval; tested with a rolled-back anonymous insert).

Confirmed sound, no change needed: cross-account isolation (ideas and profiles readable only by their owner via RLS;
reservations only through functions that check `auth.uid()`), the 5-reservation limit under concurrency (per-account
advisory lock), escaping of record text in every Function template and of user text in every client template,
public-only caching (no Function serves per-user data), HSTS, COOP, X-Frame-Options, nosniff, Referrer-Policy,
Permissions-Policy, noindex on account, saved and settings pages.

Remaining and not verified:
- Supabase leaked-password protection is off. It is a dashboard setting (Authentication), possibly on a paid plan;
  Sanjay's call.
- The contact form's flood guard is global (60 messages an hour). One sender could block it for an hour; a
  per-sender limit needs request-IP access in Postgres. Low impact, documented.
- Sign-up, Google sign-in, password reset and account deletion were not exercised end to end: they create accounts or
  send email, which Claude does not do. The code paths are unchanged apart from the library being served locally, and
  the sign-in form loads on the live site.
- No penetration test was run against production (the directive rules out destructive testing there).
- Drawing sheets for older US patents load from Google Patents' image store, so viewers' IP addresses reach Google
  when they view them. Stated in the privacy policy; images are requested with no referrer.

## 4. Data integrity report
- One definition per statistic. Reinstatements: About said 2,693, Insights 2,699 (different windows and per-issue
  counting); both now use unique patent numbers in the Gazette issues of the past 365 days (2,693). Gazette fee
  lapses (181,815) are explained as a larger population than the register (130,843 lapsed in the register).
- Home numbers state what they count, their source and date; "+N this week" says "added".
- "122.8 million patents" now reads "records (granted patents and published applications)"; office count derived from
  the data.
- Ownership: "Owner"/"Solo inventor" replaced by "Assignee" / "No assignee recorded"; CIPO's field labeled as the
  CIPO record; the filter is "No assignee".
- Opportunities: claim word count no longer used or called breadth. The rank is the sum of listed factors (fees paid
  for years, company assignee at grant, editorial field weighting, inventors, drawings), each shown with its points.
  Notes are labeled as drafted with Claude and not reviewed by a patent professional.
- AI provenance: names, summaries, modern angles, build levels and Opportunities notes are disclosed as drafted with
  Claude during data preparation (About, privacy, footer, patent pages, PDF). No AI runs on the servers; user input
  never leaves the browser unless the user pastes it into Claude.
- Rights language: no "nobody owns", "make them yours" or "free to make, use and sell". Claims notes, FAQ, picks,
  prompts and the PDF say an ended patent frees its own claims only, lapsed patents can be reinstated, abandoned
  applications never had enforceable claims, and other rights still apply.
- Worldwide status: US patents filed after 2000-05-29 can carry a term adjustment for USPTO delay, which the world
  data doesn't hold; they are no longer called "past their term" until 20 years after grant (26 for medicines).
  Utility models are labeled as registered, not as applications. Truncated world abstracts are marked.
- Build levels defined as prototype-effort estimates; statuses labeled "Likely abandoned application" and "Expired
  design patent".

- All patents filters: type (granted or registered / applications), field and first-published year, built from the
  data already loaded; the granted count on All patents and Insights uses the same rule as the filter and the badge
  (81.3 M granted patents or registered utility models, 41.6 M applications). Where a filter list keeps only its newest
  250,000 records, the count says "at least" or "no matches in reach" instead of showing a wrong total.

Remaining limitations: the worldwide "past term" count in stats.json still uses the 20-years-from-filing rule (the
label says exactly that); worldwide records carry no legal status beyond granted / not; likely-abandoned status is
inferred and labeled so; family checks are US-only and say so.

## 5. Testing report
- Unit tests (`pipeline/test_pipeline.py`): 31/31, including a new test that the Opportunities score is the sum of
  its listed factors and uses no claim-length factor.
- Browser suites (`web/dev/smoke.js`, mock backend, headless Chromium): header 8/8, home 6/6, browse 17/17, patent
  24/24, studio 6/6 (live), account 2/2. Tests updated where the pages changed on purpose.
- All patents filters and number lookup (`allf.mjs`): 17/17, including exact year counts, word + year,
  country + type, field, the "no matches in reach" case, URL state, table status column, the phone toggle, and
  CN / KR / US application numbers typed the way their offices print them.
- Card-to-patent drawing transition: checked on live pages with the new code injected, frame by frame.
- Functional checks (`func.mjs`): bundled account library loads, contact form appears, Studio prompt carries the
  patent and careful rights wording, prior-art task has no score, the PDF brief downloads (jsPDF 4.2.1), no
  third-party hosts other than the project's Supabase.
- Lighthouse (live, mobile emulation): performance 100 on home, a patent page and browse (LCP 1.3-1.6 s, CLS <= 0.022,
  TBT <= 20 ms); accessibility raised from 88-93 to 100 on home, patent, browse, studio and insights; best practices
  and SEO 100.
- Contrast: every text token against every surface >= 4.5:1 in both themes (script check).
- Keyboard: tab walk on five pages, every focusable control shows a focus ring.
- Responsive: 17 routes at 390 px and key routes at 1440 px, light and dark: no horizontal overflow.
- Database: migration verified with a rolled-back anonymous insert and privilege checks.
- No type checker or linter is part of this project (plain JS and Python, no build step). One-off lint runs on
  2026-11-01: ESLint 8 recommended rules over every browser script and Function (2 notes left, both intentional: a
  function declared in a block, valid in modules; a field destructured out on purpose so it isn't saved) and pyflakes over
  the pipeline (clean). Unused imports, an unused global and placeholder-less f-strings were removed. `node --check` and
  Python import checks run on every changed file.

## 6. Visual review
Screenshots from each pass are in the session scratchpad (`shots/`, `live/`); the live site is the reference:
https://patentyard.pages.dev

## 7. Product ideas (directive 27), decisions
- Verification confidence: done as categories, not a number: each patent page lists why it's listed, what wasn't
  checked, and when it was added and last checked.
- Family explorer: register patents already show their US family and timeline; a cross-office explorer would need
  family data the archive and world records don't carry. Not built.
- Comparison and saved searches: not built. Comparison invites misleading legal comparisons; saved searches need a
  new table and policies. Revisit if users ask.
- Opportunity explanations, problem reports, research continuity (Studio keeps the patent; the bench links back):
  done.

## 8. Final status
Live and verified. Waiting on Sanjay: deploying the new filter lists to the cards project (a production deploy; the
filter rows stay hidden until then). Open: leaked-password protection (Sanjay's dashboard), a per-sender contact limit, worldwide
filters beyond country and age (needs a new world export), and the USPTO API key needed from 2026-11-07 for new
patents to keep arriving.
