---
version: 1
slug: "pipeline-website-py"
primary_target: "pipeline/website.py"
related_targets: ["web/static/assets/site.css"]
---

## Mode

Persuade on the home page; Operate on browse, All patents, saved, settings and account; Read on patent pages, how it works and legal. One visual world across all of them.

## Direction contract

THESIS: Patent Yard as a precise technical instrument, following the brief Sanjay pasted from Gemini on 2026-10-27 (after rejecting the Apple-style pass as still "AI-looking"): spatial dark, monospace data, blueprint-framed drawings. Refuses generic rounded-card grids, plain pill filters and giant centered headers on internal pages.

OWN-WORLD: Dark #070709 base, #0F0F13 containers, #1E1E24 borders, a near-invisible indigo ambient glow (rgba(99,102,241,.03)) behind the hero and search; light mode mirrors it (#FAFAFB, white, #E4E4E9). Inter for words, JetBrains Mono for every patent number, code, date and label. Hairline borders, 12px radius, white primary buttons in dark (black in light), indigo links, emerald status dots for free, amber for inferred.

STORY: A visitor sees at once that these inventions are free to build on, searches from a command-palette field, sees a real drawing plotted in a blueprint frame with its number and status, and goes deeper or into Reinvent with Claude.

FIRST VIEWPORT: Centered headline and subhead over the faint glow, the command-palette search with a ⌘K badge and a white Search button, suggestion chips, the worldwide link, and the top of the blueprint-framed drawing with its FIG tag.

FORM: User-supplied brief (Gemini prompt) executed in the site's own HTML/CSS stack. seed:f4072c5c67787f3e (original roll, superseded by the user's brief). Signature interaction: the plotted drawing inside a blueprint frame, with a magnifier; cards lift with a border-luminance shift; digits strike into place; skeleton shimmer while loading. Honest data only: no invented trends or "live" claims.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
