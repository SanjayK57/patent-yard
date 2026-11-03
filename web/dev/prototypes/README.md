# Homepage prototypes for v3 (2026-11-02)

Three art directions for the home page, built as plain HTML pages with real data from the preview, before the
redesign was built. Prototype A became Patent Yard v3; docs/REDESIGN-V3.md compares them.

- `a-light-table.html`: the drawing lies on lit glass, with its record on a vellum card (chosen).
- `b-catalogue.html`: the drawing as an object on a studio sweep, with a specification table.
- `c-reference-numerals.html`: the drawing's own lead lines run out to the facts. Declined: lines pointing at parts
  of a drawing say those parts mean something, which the page can't back up.

To view them, serve a folder holding the pages under `proto/`, their fonts under `proto/fonts/`
(`archivo-latin.woff2`, `Schibsted-Grotesk.woff2`, `Onest.woff2`, `sourceserif-latin.woff2`,
`sourceserif-italic-latin.woff2`) and the drawings at `img/p/<id>/1.png`, with a plain static server
(`python3 -m http.server`). The site's own server sends a Content-Security-Policy that blocks their inline styles.
They are not part of the site and are never deployed.
