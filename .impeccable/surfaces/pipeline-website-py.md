---
version: 1
slug: "pipeline-website-py"
primary_target: "pipeline/website.py"
related_targets: ["web/styles/site.css","pipeline/site_ui/pages/home.py"]
---

## Mode

Persuade on the home page; Operate on browse, All patents, Studio, saved, settings and account; Read on patent pages, Opportunities, Insights, how it works and legal. One visual world across all of them: expressive and composed on home, dense and operational in the research app.

## Direction contract

THESIS: Patent Yard v3, "the light table" (Sanjay's v3 brief, 2026-11-02; prototype A of three, chosen over a catalogue plate and a reference-numeral callout layout). An old invention lies on lit glass as the original sheet; everything Patent Yard adds is drawn on vellum laid over it. Refuses v2's centered headline over a search over a boxed drawing, equal card grids, and blue-accented cool surfaces.

OWN-WORLD: Neutral near-white table #F3F3F1, lit glass #FDFDFC panels that bleed off one edge, graphite ink #17191A, frosted vellum overlays for Patent Yard's own notes, registration ticks at sheet corners instead of boxes, sheet margin labels set vertically. One vermilion mark #C23B27 / #FF7D66, only for the one live thing in view (the pen, the current selection, the active step). Archivo across three widths: expanded for display, normal for UI, semi-condensed for dense data; Source Serif 4 for the patent's own words. Graphite pill actions.

STORY: The visitor reads two lines, searches from a pill field beside the glass, sees a real drawing plotted on the table with its record on vellum, then one invention up close, the yard's scale in three counted numbers, today's sheets, the field index, the Discover, Investigate, Develop path, and the studio's brief traced over a patent.

FIRST VIEWPORT: Split. Left: "Old inventions. New possibilities." two-tone, expanded, about 88px, a one-paragraph lede, the search pill with its Search button, try-words, the worldwide link, a one-line rights qualification. Right: lit glass bleeding off the right edge, the plotted drawing with corner ticks and a vertical sheet label, a vellum record card (status, title, dates, record link) overlapping the sheet's lower left.

FORM: Brief-pinned split hero, built code-led in the site's Python/HTML/CSS stack. seed:9dba14ec348c0722. Raises from the declined hand: color only on what matters now (glazier wall); record and reinvention as one object, the studio brief on vellum over the patent (HyperCard); focus isolates and dims the rest, in the drawing viewer (event display); the chosen sheet face-out, the rest as spines, in the featured picks (pulp rack). Signature interaction: the pen plotting the drawing onto the glass, the loupe, the card drawing flying into the patent page.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, a rewritten DESIGN.md and its sidecar, and every shipping raster carrying its provenance
