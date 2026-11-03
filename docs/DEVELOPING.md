# Working on the website

A short map for changing how Patent Yard looks and behaves. DESIGN.md says what the design is; this file says where
it lives and how to check a change.

## How the site is made

Python writes plain HTML pages into `web/dist`; Cloudflare Pages serves them, and Pages Functions serve patent pages,
drawings and kit data out of packed shard files. Plain JavaScript modules add search, filters, accounts and the
Studio. There is no framework and no bundler; the only build step for the front end is the stylesheet bundle below.

```
pipeline/website.py          the data side of the build: archive, shards, catalog, the swap into web/dist
pipeline/site_ui/            everything the pages look like
  base.py                    shared constants and small helpers (escaping, dates, icons, status labels, navigation)
  shell.py                   <head>, header and footer around every page
  components.py              shared pieces: patent cards (card_html), pick rows, browse filters
  styles.py                  bundles web/styles into one stylesheet
  ranking.py                 the home page's picks and the Opportunities score
  outputs.py                 files that aren't pages: assets, catalog, feeds, sitemaps, link checker
  pages/home.py              one module per page or group of pages:
  pages/browse.py              browse, field pages, the fields index, the archive page shell
  pages/all_patents.py         All patents
  pages/patent.py              patent pages and the Claude kit data
  pages/opportunities.py, insights.py, studio.py
  pages/account.py             My bench, saved patents, settings
  pages/content.py             How it works, About, Contact, legal pages, 404
web/styles/                  the stylesheet in source form (site.css lists the files in order)
web/static/                  copied into web/dist as is: assets/js, fonts, vendor libraries, favicon, _headers
web/functions/               Pages Functions; _archive.js and _world.js draw archive and worldwide patent pages
web/dev/                     previews, the local server and the checks
```

## Where to change things

| Change | Where |
|---|---|
| Page, glass, vellum, text, action, mark or status colors | `web/styles/tokens.css` (light block, then the dark block). Nothing else sets a color. The browser's theme color and the web manifest follow `--bg` automatically. `--act` is the graphite of buttons and selected chips; `--mark` is the vermilion kept for the one live thing (focus, the pen, the current step). |
| Fonts, widths, type sizes, letter spacing | `tokens.css` (`--sans`, `--serif`, `--mono`, `--wide`, `--semiwide`, `--narrow`, `--fs-*`, `--track-*`); Archivo is one variable file with a width axis, so a heading's width is `font-stretch`; the files are in `web/static/assets/fonts` and declared in `web/styles/fonts.css` |
| Spacing, widths, header height, corner radius | `tokens.css` (`--s1`..`--s12`, `--page`, `--gutter`, `--header-h`, `--r-*`, `--control-h*`) |
| Buttons, chips, segmented controls, fields, status labels | `web/styles/controls.css` |
| Header, navigation, footer, page heads, panels | `web/styles/layout.css` and `pipeline/site_ui/shell.py` |
| Patent results (list, cards, table) | look: `web/styles/cards.css` (`.grid.as-list`, `.grid`, `.grid.as-table`); markup: `card_html` in `site_ui/components.py` and `card` in `web/static/assets/js/cards.js` (change both, then run the card test); the view switch is `VIEWTOG` in `site_ui/base.py` and `setView` in `assets/js/app.js` |
| The register's filters and toolbar | `filters()` and `toolbar()` in `site_ui/components.py`, laid out by `web/styles/pages/browse.css` (`.workspace`, `.fside`, `.countbar`) |
| Glass, vellum and corner ticks | `.glass` in `web/styles/drawings.css`; `.vellum` and `.ticks` in `web/styles/base.css` |
| Drawings and the full-screen viewer | `web/styles/drawings.css` |
| Dialogs, command palette, menus, toasts | `web/styles/overlays.css` |
| Animation timing and page transitions | `--ease`, `--spring`, `--t1`..`--t4` in `tokens.css`; keyframes and transitions in `web/styles/motion.css`; the home plotter in `assets/js/home.js` |
| One page's layout | its template in `site_ui/pages/` and its stylesheet in `web/styles/pages/` |
| Words on a page | the page's template; shared labels (statuses, build levels) are in `site_ui/base.py` |

Some examples: "make the navigation shorter" is `--header-h`; "change the live mark" is `--mark` (and `--focus`) in
both theme blocks; "rounder patent cards" is `.card .fig` in `cards.css`; "a more compact patent page" is
`web/styles/pages/patent.css` (`.psec`, `.playout`, `.claimlist`).

Rules that keep it easy to change: use the tokens rather than raw values, add a class rather than a `style=""`
attribute (the only inline styles left are computed values such as chart bar widths), keep one page's styles in its
page file, and keep the Python and JavaScript card renderers in step.

## Generated files: don't edit by hand

`web/dist/` (the built site), `web/functions/site.json` (shard count and headers, written by the build),
`assets/site.<hash>.css` (bundled from `web/styles`), `assets/js/config.js` (written by the build) and anything a
preview writes.

## Preview locally

On any computer, with invented sample data (no production data needed, a few seconds):

```
python3 web/dev/fixtures.py /tmp/py-sample
python3 web/dev/serve.py /tmp/py-sample 8000        # open http://localhost:8000
```

Every page of the sample build says it holds sample data; its patents are numbered far above any real US patent.
It is built as of one fixed day (`SAMPLE_DAY` in `fixtures.py`), so it looks the same whenever it's built. Rebuild
after a change; restart the server if you delete and rebuild its folder.

On the publishing Mac, with the real records (about a minute):

```
python3 web/dev/build_preview.py /tmp/py-web --live ~/PatentYard/web/dist
cd web && npx wrangler@4 pages dev /tmp/py-web --port 8788
```

`--live` links the shards of the last full build, so every patent page and drawing works; the shards holding a few
test patents and the home page's picks are rendered fresh. For a quick look at a stylesheet change without a rebuild,
`python3 -c "import sys; sys.path.insert(0, 'pipeline'); from site_ui.styles import bundle_css; print(bundle_css())" > /tmp/py-web/assets/site.<hash>.css`
(the hash is the file already there).

Light and dark: use the moon button, or your system setting. Phone widths: the browser's device toolbar.

## Checks

```
cd pipeline && python3 -m unittest test_pipeline      # the pipeline and page helpers
python3 pipeline/site_ui/styles.py                    # the stylesheet bundles
node web/dev/test_cards.mjs                           # Python and JavaScript cards are identical
node web/dev/check.mjs http://localhost:8788          # browser suites (mock accounts) and no sideways scroll
```

`check.mjs` needs Playwright with Chromium (`cd web/dev && npm install --no-save playwright && npx playwright install
chromium`). Against a real-data preview it runs every smoke suite; against the sample site it runs the checks that
hold for any data. The suites are in `web/dev/smoke.js`; they also run by hand in a page's console
(`await runSuite("browse")`) on a preview made with `web/dev/preview.py --mock`.

Visual regression, on the sample site:

```
node web/dev/visual.mjs http://localhost:8000 /tmp/py-gold                         # once, before a change
node web/dev/visual.mjs http://localhost:8000 /tmp/py-now --against /tmp/py-gold   # after it
```

It takes full-page screenshots of nine pages at 1440 and 390 wide, light and dark, with motion settled, and fails a
page whose height changes or whose pixels change by more than 0.5% (a pixel counts only when a channel moves by more
than 48 of 255, so anti-aliasing passes); each failure writes a `.diff.png` with the changes in red. The goldens are
not kept in the repository: make them from the commit you are comparing against.

`web/dev/prototypes/` holds the three homepage prototypes v3 was chosen from (see its README).

## Build and deploy

`python3 pipeline/pipeline.py web` builds the whole site into `web/dist` (it needs the production data). Deploying is
in README.md ("Website: test and deploy"); the publisher on the Mac does it every two hours from `main`.
