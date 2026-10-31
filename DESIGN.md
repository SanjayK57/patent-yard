# Patent Yard design system

Shipped on branch `overhaul` (2026-10-31), replacing the dark "spatial" look of 2026-10-27. Source of truth: the top of
`web/static/assets/site.css`. `.impeccable/design.json` still describes the previous look and needs regenerating.

## Idea
A drafting room, not a dashboard. Patent drawings are the only pictures; everything around them is paper, ink and
hairlines. The one place the patent-sheet idea shows is the drawing itself: a white sheet with a `FIG.` caption.

## Type
| Role | Face | Where |
|---|---|---|
| Patent Yard's words | IBM Plex Sans (variable 100-700) | UI, headings, summaries, notes |
| The patent's own words | IBM Plex Serif 400/400i/600 | abstract (`.source`), claims (`.claimlist`), description (`.desc`) |
| Numbers and identifiers | IBM Plex Mono 400/500/600 | patent numbers, dates, counts, small labels (`.num`, `.kicker`) |

Big metrics (`.statband b`) use the sans with tabular figures, not mono. Headings 600, tracking -0.012em
(hero -0.025em). Body 16/1.6. Self-hosted woff2 in `assets/fonts` (OFL), Latin + Latin Extended.

## Color
Light: paper `#F7F6F2`, surface `#FFFFFF`, sunken `#EFEDE7`, lines `#E3E0D8`/`#CDC9BE`, ink `#17171A`/`#44444A`/`#66656B`.
Dark: graphite `#0F1012`, surface `#16171A`, lines `#26272B`/`#36383D`, ink `#EDECE8`/`#BDBCB7`/`#93928D`.
Accent (safety orange): `#D9480F` light, `#FF7A3D` dark; link text `#B33A0C` / `#FF9A66`. Used for focus, links,
the active nav and selection, never for status. Primary buttons are ink-filled (`--fill`), not orange.

Status colors are fixed and always paired with a word:
| Status | Light | Dark | Badge |
|---|---|---|---|
| Expired (full term, design, past term) | `#1E7A4A` | `#5CC98F` | solid dot |
| Lapsed, fee not paid (can be reinstated) | `#9A5B00` | `#E9A944` | solid dot |
| Likely abandoned application (inferred) | `#5B6370` | `#A1A9B6` | hollow dot, dashed border |
| Reserved | `#2F5D8C` | `#8DB4E2` | solid dot |
| Error | `#B42318` | `#F97066` | text only |

## Shape and depth
Radius 6 (controls) and 10 (panels, cards, drawings). Hairline borders do the work; shadows only on hover and
floating layers. No glows, gradient text, background grids, glass blur or fake window chrome.

## Components (selectors)
Buttons `.btn.primary|secondary|quiet|link` (sm, lg). Filter chips `.chip` (pressed = ink fill). Status `.badge.<status>`.
Cards `.card` (figure on a white sheet with `FIG. 1` lower-left, badge top-left). Ledger numbers `.statband`.
Ranking explanation `details.why`. Honeypot `.trap`. Optional field tag `.opt`.

## Motion
One curve `--ease: cubic-bezier(.22,.8,.24,1)`; durations `--t1` .16s (controls), `--t2` .24s (fields, cards),
`--t3` .42s (sections). Home drawing is plotted onto canvas; sections rise once on entry; cards lift 2px on hover.
Everything stops under the OS reduced-motion setting or the site's Motion: Reduce setting.
