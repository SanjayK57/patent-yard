# Patent Yard 2.0: redesign and frontend refactor

Branch `v2` (worktree `~/PatentYard-v2`), started 2026-11-02 from main `bee7e6d`. Nothing is pushed or deployed:
that waits for Sanjay's go-ahead. The brief is the "Patent Yard 2.0, source-aware professional redesign and frontend
refactor" prompt. Earlier work (docs/OVERHAUL.md, docs/REPORT.md) is kept: statuses, rights wording, provenance,
security fixes, CSP, local fonts and libraries, reduced motion, view transitions and the tests.

## 1. The design, before and after

Before: a "drafting room": warm cream paper, IBM Plex in three families, small uppercase mono labels over almost
every block, a hairline box around every group, a safety-orange accent. It read as a generated template.

After: desktop-class software with Patent Yard's own identity.
- **Color.** A cool near-white page (#F5F7F8) with white surfaces; near-black charcoal (#111416, #181B1D) in dark mode.
  One accent, Prussian blue (#116289, #64B5E4 in dark): the color of the cyanotype blueprints patent drawings were
  once copied as. It marks actions, links, focus, selection and their state, nothing decorative. Status colors stay
  semantic and always carry their word. Every text color passes 4.5:1 on every surface in both themes.
- **Type.** Hanken Grotesk (variable, self-hosted) for everything Patent Yard says, from a 76px headline to 12px
  labels; Source Serif 4 for the patent's own words (abstract, claims, description); the system mono only for
  identifiers. IBM Plex is gone.
- **Shape and depth.** 8px controls, 12 to 22px containers, hairlines drawn as 1px rings, soft offset shadows; the
  home page's drawing sheet gets a long product-shot shadow. No eyebrow labels, no gradient text, no glow; the only
  translucency is the sticky header and dialog title bars.
- **Controls.** One vocabulary: filled accent primary buttons, ringed secondary buttons, quiet text buttons, filter
  chips that fill with the accent tint, segmented controls with a raised thumb (collection, document type, theme,
  view), native-feeling fields with an accent focus ring.
- **Pages.** Home: a centered headline and the site's largest control (the search), the plotted drawing as a wide
  white sheet, the collections as a grouped list where each count says what it counts and where it comes from,
  today's picks (one lead, four drawing-first cards, a ruled list), fields, three steps, and one dark Studio band.
  Cards: the drawing on its sheet, then the words, no box. Register and All patents: a toolbar-style filter panel.
  Patent pages: badges, a large title, a toolbar of actions, a sticky contents list, the drawing first, a spec-style
  facts table, claims set in the serif with dependents indented. Studio: a two-pane workspace with selectable tasks.
  Account, settings, legal and content pages follow the same grouped-list and segmented-control language.
- **Motion.** The plotter now follows the drawing's strokes (keeps direction, lifts to the nearest undrawn line),
  ink settles in over 220 ms, about 3 s eased; ink follows the sheet, so original drawings in dark mode plot in dark
  ink. Theme switching cross-fades. Buttons and small arrivals use the spring; cards lift; dialogs scale in over a
  blurred scrim; the mobile menu slides. The card-to-patent drawing transition ("pfig") is unchanged. Everything stops
  under reduced motion, from the system or the site setting.

DESIGN.md is the full system (rewritten from the built CSS); `.impeccable/design.json` is its machine-readable twin.

## 2. The frontend refactor

- `pipeline/website.py` (1,855 lines) now holds only the data side of the build (archive, shards, catalog, the swap
  into web/dist), about 300 lines. Every page renderer moved, unchanged, into `pipeline/site_ui/`; the rebuilt site was
  byte-identical to the old one apart from build timestamps before any design change was made.
- The stylesheet is source in `web/styles/` (19 files: tokens, fonts, base, layout, controls, drawings, cards,
  overlays, motion, print, one per page). `site_ui/styles.py` bundles it into one hashed file, so the site still
  makes one request for its styles. Dark mode is written once; the bundler adds the copy for system-dark visitors.
- One source for brand colors: `tokens.css`. The browser theme color and the web manifest read `--bg` from it
  (the old hard-coded #FAFAFB / #070709 meta values are gone).
- Patent cards had five renderers (Python, and four places in JavaScript). Now one function per language draws them
  from the same fields: `site_ui/components.py card_html` and `assets/js/cards.js card`. `web/dev/test_cards.mjs`
  renders shared fixtures with both and fails if a single character differs.
- 45 static inline styles became classes. Left on purpose: the home page's stagger order (`--d`), the icon sprite,
  computed chart values, and the Functions' standalone error page (it has no stylesheet).
- `.wrangler/` is no longer tracked (see 8).

## 3. Source organization

```
pipeline/website.py            data and build orchestration
pipeline/site_ui/              base, shell, components, styles, ranking, outputs, site, pages/*.py
web/styles/                    site.css (the import list), tokens, fonts, base, layout, controls, drawings, cards,
                               overlays, motion, print, pages/{home,browse,patent,opportunities,insights,studio,account,content}.css
web/static/assets/js/cards.js  the browser's card renderer
web/dev/                       fixtures.py, build_preview.py, preview.py, serve.py, check.mjs, test_cards.mjs, smoke.js, mock-backend.js
docs/DEVELOPING.md             the guide
```

## 4. Editing the UI later

docs/DEVELOPING.md has the full table. Accent: `--accent` and its neighbours in both blocks of `tokens.css`.
Navigation height: `--header-h`. Card corners: `.card .fig` in `cards.css`. A more compact patent page:
`web/styles/pages/patent.css`. The home layout: `site_ui/pages/home.py` and `web/styles/pages/home.css`.

## 5. Local preview

Any computer, invented sample data, a few seconds: `python3 web/dev/fixtures.py /tmp/py-sample` then
`python3 web/dev/serve.py /tmp/py-sample 8000`. Every page says it is sample data; numbers sit above any real US
patent (US 98,000,001 and up). The publishing Mac, real data, about a minute:
`python3 web/dev/build_preview.py /tmp/py-web --live ~/PatentYard/web/dist`, served with `wrangler pages dev`.

## 6. Test results (2026-11-02, on the real-data preview unless noted)

- Unit tests (`pipeline/test_pipeline.py`): 31/31.
- Card contract (`web/dev/test_cards.mjs`): 5/5 cards identical in Python and JavaScript.
- Smoke suites with the mock backend (`web/dev/check.mjs`): header 8/8, home 6/6, browse 17/17, patent 24/24,
  studio 6/6, account 2/2. The home suite now checks the collections list instead of the old stat band.
- All patents filters and number lookup: 17/17 (the test reads country and year from the card's number and facts;
  the attribute it used only fed the old FIG caption).
- Functional checks: 11/11 (account library loads, contact form appears with its honeypot hidden, Studio prompt
  carries the patent and careful rights wording, prior-art task has no score, the PDF brief downloads with jsPDF
  4.2.1, no third-party hosts but the project's Supabase).
- No sideways scrolling on 16 routes at 320, 375, 390, 768 and 1024 px, and on register, archive and worldwide
  patent pages at 390 and 1440. No script errors.
- Lighthouse (local preview, mobile emulation): performance 99 to 100, best practices 100, SEO 100, accessibility 100
  on home, browse, a patent page, Studio, Insights, Opportunities, All patents, account, settings, how it works,
  about, contact, saved and fields (after raising the accent tint and the disclosure targets).
- Keyboard: every tab stop on five pages shows a focus ring (the search fields ring their whole box).
- Sample-data site: account 2/2, layout and script-error checks pass at 320/390/768.
- Finish review (Impeccable finish reviewer): 10 fixes, all applied: no gap between the studio band and the footer,
  patent pages with one toolbar row of actions, smaller balanced long titles, one active mark in the contents list,
  tighter Opportunities method text, one identifier size, a quiet rank badge, one search field per screen, the home
  drawing in its own proportions on phones, a normal field with a short placeholder for the register's search on
  phones. Every check above was re-run after them and passes.
- Full production build of the branch (`pipeline.py web`, real data): passed in 829 s: 131,020 patents in 1,024
  shards, 11,699,375 archive records, 14,318 files (Cloudflare Pages allows 20,000), largest file under 25 MiB, and the
  link check across every page found no broken links. It ran before the finish-review fixes, which touch styles and
  templates only.

## 7. Screenshots

Desktop and phone, light and dark, are in the session scratchpad and were sent with the hand-off; the preview can
regenerate them at any time.

## 8. Security and data integrity

- No backend, policy or header change: Supabase schema and RLS, Functions logic, CSP and `_headers` are untouched;
  the Functions changed only class names. No new third-party requests; fonts are self-hosted under the OFL.
- Both card renderers escape every field; the sheet count is coerced to an integer.
- `.wrangler/cache/wrangler-account.json`, which the public repository received on 2026-11-02, holds the Cloudflare
  account id and the account's label. Neither is a credential, but the label is personal. It is untracked from now on; it stays in the public history unless the history is rewritten
  and force-pushed, which needs Sanjay's say-so.
- Wording kept to the earlier data-integrity rules: worldwide counts are "patent records" (granted patents and
  published applications), statuses keep their sourced words, reservations still say they don't stop anyone, and AI
  drafting is still disclosed. "Rechecked for reinstatement every day" holds: the daily job runs the check; its
  source, the Official Gazette, publishes weekly.

## 9. Remaining limitations

- **USPTO access, 2026-11-07.** Patent Public Search will require a USPTO.gov sign-in. The pipeline is ready to fail
  safely: harvest, enrich, verify's family checks and bulk stop with a clear message and retry once a day, and the
  Gazette expiry and reinstatement checks keep running. It is not ready to keep collecting new patents: that needs
  a free Open Data Portal API key (data.uspto.gov/apikey, an adult must request it) and a client for that API, which
  can't be written and tested without the key. No workaround was attempted.
- The browser suites expect the real register; on the sample site only the data-independent checks run.
- The home page's "worldwide" figures need web/world (the 54 GB export); a clean clone builds without that page.
- Supabase leaked-password protection and a per-sender contact limit remain as in docs/REPORT.md.

## 10. Deployment readiness

Ready for review, not deployed. The branch builds the whole site cleanly (see 6). Deploying means merging `v2` into `main` (the publisher then builds and deploys
within two hours) or a manual deploy from `web/`; both need Sanjay's explicit go-ahead. The first full build after
the merge rewrites every shard, so the whole site switches to the new design at once.
