# Patent Yard 2.0 redesign: checklist

Branch `v2` (worktree `~/PatentYard-v2`), started 2026-11-02 from main `bee7e6d`. Not pushed or deployed: that needs
Sanjay's go-ahead. The brief is the "Patent Yard 2.0 — source-aware professional redesign and frontend refactor" prompt.

## Done
- [x] Stage 1 audit: live screenshots (home, browse, patent, studio, both themes); the drafting-room look came from small
      tracked mono labels, boxes around everything, IBM Plex on warm cream. Inline styles, duplicated card markup in
      Python and four JS places, stale theme-color values, duplicated dark tokens, `.wrangler` cache tracked (it held
      the Cloudflare account id and an account label with Sanjay's email).
- [x] Stage 3a: `pipeline/website.py` (1,855 lines) split into `pipeline/site_ui/` (shell, components, outputs, ranking,
      styles, base, one module per page). Output byte-identical except build timestamps. `.wrangler/` untracked.
- [x] Stage 2 direction: Hanken Grotesk (UI and display), Source Serif 4 (the patent's own words), system mono for
      identifiers; cool near-white / near-black charcoal; Prussian-blue accent (#116289 light, #64B5E4 dark);
      status colors kept semantic; tokens in `web/styles/tokens.css`.
- [x] Stage 3b: `web/styles/` modular source, bundled by `site_ui/styles.py` into one hashed file; dark theme written once.
- [x] Stage 3c: one card contract: `assets/js/cards.js` + `site_ui/components.py card_html`, test `web/dev/test_cards.mjs`.
- [x] Stage 4 home recomposed (hero, plotted sheet, collections list, picks, fields, steps, studio band).
- [x] Static inline styles replaced by classes (left: CSS custom properties for stagger, the icon sprite, the
      standalone Function error page).

## To do
- [ ] Stage 5: check and refine browse, All patents, patent page, Opportunities, Insights, Fields
- [ ] Stage 6: Studio, saved, My bench, account, settings
- [ ] Stage 7: How it works, About, FAQ, Contact, legal, 404
- [ ] Stage 8: motion: plotter (stroke-following, ink fade), microinteractions, view transitions
- [ ] Dev fixtures: `web/dev/fixtures.py` preview without production data
- [ ] Stage 9 QA: unit tests, card contract, smoke suites (mock backend), screenshots 1440/1280/1024/768/390/375/320
      light and dark, contrast, keyboard, Lighthouse, link check
- [ ] Stage 10 docs: DESIGN.md, PRODUCT.md, docs/DEVELOPING.md, README, .impeccable metadata, report
- [ ] USPTO API key change (2026-11-07): verify the pipeline's readiness, keep it in the report
