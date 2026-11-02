---
version: 1
slug: "pipeline-website-py"
primary_target: "pipeline/website.py"
related_targets: ["web/styles/site.css","pipeline/site_ui/pages/home.py"]
---

## Mode

Persuade on the home page; Operate on browse, All patents, Studio, saved, settings and account; Read on patent pages, Opportunities, Insights, how it works and legal. One visual world across all of them.

## Direction contract

THESIS: Patent Yard 2.0, pinned by Sanjay's brief (2026-11-02): desktop-class software with Apple-level care for type, spacing, controls and motion, but its own identity. The patent drawing is the product shot; the interface recedes around it. Refuses the AI-site defaults the old look had: tracked mono eyebrow labels, boxes around everything, cream paper with an orange accent, equal card grids as page structure.

OWN-WORLD: Cool near-white #F5F7F8 page and white surfaces in light, near-black charcoal #111416 and #181B1D in dark; hairlines drawn as 1px box-shadow rings; Prussian (cyanotype) blue accent #116289 / #64B5E4 used for primary buttons, links, focus, selection only; Hanken Grotesk for everything Patent Yard says, Source Serif 4 for the patent's own words, system mono only for identifiers; 8px controls, 12–22px containers; segmented controls with a raised thumb; drawings always on their sheet, inverted in dark mode.

STORY: A visitor reads one sentence, searches from the largest control on the page, watches a real drawing get plotted stroke by stroke, sees what the yard holds and where each count comes from, then opens a patent whose page reads like a well-set technical document with the drawing first.

FIRST VIEWPORT: Centered two-line headline (76px max), one-paragraph lede, a 640px search with a filled Search button and suggestion words beneath, the link to all patents worldwide, and the top edge of a 1080px-wide white drawing sheet with a long soft shadow.

FORM: Brief-pinned direction (the standing canon at full fidelity, bar: Apple product pages and macOS apps), executed in the site's own Python/HTML/CSS stack. seed: none (unavailable). Signature interaction: the pen plotter tracing the drawing's strokes with ink settling behind it; a card's drawing flies into the patent page; the theme switch cross-fades.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
