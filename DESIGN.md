---
name: Patent Yard
description: A free register of expired patents, set like a drafting room: paper, ink, hairlines, and the patent drawing as the only picture.
colors:
  paper: "#F7F6F2"
  surface: "#FFFFFF"
  surface-2: "#FBFAF7"
  sunken: "#EFEDE7"
  band: "#F0EEE8"
  plate: "#FFFFFF"
  line: "#E3E0D8"
  line-strong: "#CDC9BE"
  ink: "#17171A"
  ink-2: "#44444A"
  ink-3: "#66656B"
  fill: "#17171A"
  fill-hover: "#2E2E33"
  accent: "#D9480F"
  accent-hover: "#B93A0A"
  accent-soft: "#FCEBE2"
  link: "#B33A0C"
  expired: "#1E7A4A"
  expired-soft: "#E3F1E8"
  lapsed: "#9A5B00"
  lapsed-soft: "#F8EED9"
  abandoned: "#5B6370"
  abandoned-soft: "#EAECEF"
  reserved: "#2F5D8C"
  reserved-soft: "#E4ECF5"
  danger: "#B42318"
  dark-paper: "#0F1012"
  dark-surface: "#16171A"
  dark-surface-2: "#1A1B1E"
  dark-sunken: "#1F2024"
  dark-band: "#131417"
  dark-plate: "#121316"
  dark-line: "#26272B"
  dark-line-strong: "#36383D"
  dark-ink: "#EDECE8"
  dark-ink-2: "#BDBCB7"
  dark-ink-3: "#93928D"
  dark-accent: "#FF7A3D"
  dark-accent-hover: "#FF9663"
  dark-link: "#FF9A66"
  dark-expired: "#5CC98F"
  dark-lapsed: "#E9A944"
  dark-abandoned: "#A1A9B6"
  dark-reserved: "#8DB4E2"
  dark-danger: "#F97066"
typography:
  display:
    fontFamily: "IBM Plex Sans, -apple-system, BlinkMacSystemFont, Helvetica Neue, Arial, sans-serif"
    fontSize: "clamp(36px, 4.4vw, 58px)"
    fontWeight: 600
    lineHeight: 1.04
    letterSpacing: "-0.025em"
  headline:
    fontFamily: "IBM Plex Sans, -apple-system, BlinkMacSystemFont, Helvetica Neue, Arial, sans-serif"
    fontSize: "clamp(28px, 3.4vw, 40px)"
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: "-0.028em"
  title:
    fontFamily: "IBM Plex Sans, -apple-system, BlinkMacSystemFont, Helvetica Neue, Arial, sans-serif"
    fontSize: "clamp(22px, 2.3vw, 28px)"
    fontWeight: 600
    lineHeight: 1.15
    letterSpacing: "-0.022em"
  card-title:
    fontFamily: "IBM Plex Sans, -apple-system, BlinkMacSystemFont, Helvetica Neue, Arial, sans-serif"
    fontSize: "16.5px"
    fontWeight: 600
    lineHeight: 1.28
    letterSpacing: "-0.012em"
  body:
    fontFamily: "IBM Plex Sans, -apple-system, BlinkMacSystemFont, Helvetica Neue, Arial, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.6
    letterSpacing: "0"
  source:
    fontFamily: "IBM Plex Serif, Charter, Georgia, Times New Roman, serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.7
  claim:
    fontFamily: "IBM Plex Serif, Charter, Georgia, Times New Roman, serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.7
  number:
    fontFamily: "IBM Plex Mono, ui-monospace, SF Mono, Menlo, Consolas, monospace"
    fontSize: "11.5px"
    fontWeight: 500
    lineHeight: 1.2
    letterSpacing: "0.01em"
    fontFeature: "tnum"
  label:
    fontFamily: "IBM Plex Mono, ui-monospace, SF Mono, Menlo, Consolas, monospace"
    fontSize: "10.5px"
    fontWeight: 500
    lineHeight: 1
    letterSpacing: "0.08em"
  metric:
    fontFamily: "IBM Plex Sans, -apple-system, BlinkMacSystemFont, Helvetica Neue, Arial, sans-serif"
    fontSize: "clamp(22px, 2vw, 28px)"
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: "-0.015em"
    fontFeature: "tnum"
rounded:
  control: "6px"
  panel: "10px"
  pill: "999px"
spacing:
  gap: "16px"
  page-inline: "20px"
  page-inline-wide: "40px"
  section: "80px"
  container: "1240px"
  narrow: "820px"
components:
  button-primary:
    backgroundColor: "{colors.fill}"
    textColor: "{colors.surface}"
    rounded: "{rounded.control}"
    padding: "8px 16px"
    height: "38px"
  button-primary-hover:
    backgroundColor: "{colors.fill-hover}"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "8px 16px"
    height: "38px"
  button-quiet:
    backgroundColor: "transparent"
    textColor: "{colors.ink-2}"
    rounded: "{rounded.control}"
    padding: "8px 10px"
  button-quiet-hover:
    backgroundColor: "{colors.sunken}"
    textColor: "{colors.ink}"
  chip:
    backgroundColor: "transparent"
    textColor: "{colors.ink-2}"
    rounded: "{rounded.control}"
    padding: "0 11px"
    height: "30px"
  chip-pressed:
    backgroundColor: "{colors.fill}"
    textColor: "{colors.surface}"
  badge-expired:
    backgroundColor: "{colors.expired-soft}"
    textColor: "{colors.expired}"
    rounded: "{rounded.control}"
    padding: "0 8px"
    height: "22px"
  badge-lapsed:
    backgroundColor: "{colors.lapsed-soft}"
    textColor: "{colors.lapsed}"
    rounded: "{rounded.control}"
    padding: "0 8px"
    height: "22px"
  badge-abandoned:
    backgroundColor: "{colors.abandoned-soft}"
    textColor: "{colors.abandoned}"
    rounded: "{rounded.control}"
    padding: "0 8px"
    height: "22px"
  badge-reserved:
    textColor: "{colors.reserved}"
    rounded: "{rounded.control}"
    padding: "0 8px"
    height: "22px"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "9px 12px"
    height: "40px"
  card:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.panel}"
  card-figure:
    backgroundColor: "{colors.plate}"
    padding: "42px 16px 30px"
  panel:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.panel}"
    padding: "22px"
  nav-link:
    textColor: "{colors.ink-3}"
    rounded: "{rounded.control}"
    padding: "7px 10px"
  nav-link-current:
    backgroundColor: "{colors.sunken}"
    textColor: "{colors.ink}"
---

# Design System: Patent Yard

Shipped on branch `overhaul` (2026-10-31), replacing the dark "spatial" indigo look of 2026-10-27. Source of truth is
the token block at the top of `web/static/assets/site.css`: `:root` for light, the same names redefined under
`prefers-color-scheme: dark` (unless `data-theme="light"`) and under `:root[data-theme="dark"]`. The `dark-*` keys in
the frontmatter are those dark values of the same CSS variables, not separate variables.

## Overview

**Creative North Star: "The Drafting Room"**

A drafting room, not a dashboard. Patent drawings are the only pictures; everything around them is paper, ink and
hairlines. Light mode is warm drafting paper, dark mode is graphite. Type is ink-black, there is one safety-orange
accent for focus, links and selection, and filled actions are ink, not orange. The one place the patent-sheet idea
shows is the drawing itself: a white sheet with a mono `FIG. 1` caption in its lower-left corner.

Three voices are kept apart by face. IBM Plex Sans is Patent Yard speaking (interface, headings, summaries, notes).
IBM Plex Serif is the patent's own text (abstract, claims, description), so source text always reads differently from
ours. IBM Plex Mono is every patent number, date, count and small label.

Working pages are left-aligned and dense: headings sit left with their action at the right edge, filters are grouped
text buttons with micro-counters, card grids collapse into a ruled table, and data sits in hairline-divided cells
instead of boxes. The visitor controls theme, drawing treatment in dark mode, text size and motion from the settings
page.

**Key Characteristics:**
- Warm paper (light) and graphite (dark) grounds; ink type in three steps.
- Hairlines (1px `line` / `line-strong`) do the structural work; shadows only for hover and floating layers.
- Two radii: 6px for controls, 10px for panels, cards and drawings.
- Status color is fixed site-wide and always paired with a word.
- Drawings sit on a plate with a mono FIG caption; in dark mode the linework is inverted onto graphite unless the visitor asks for original white sheets.
- One easing curve; every animation stops under reduced motion (OS or site setting).

## Colors

A near-neutral warm palette with one orange accent and four fixed status hues; dark mode keeps the same roles at
higher lightness.

### Primary
- **Safety Orange** (`accent`, dark `dark-accent`): focus rings (`--focus` equals it), text selection (30% mix),
  the active table-of-contents rule, the reading-progress bar, the pressed save button, the user avatar, chart lines,
  and the soft wash (`accent-soft`) behind focused fields, targeted claims and the archive hint. Never a status.
- **Redline Link** (`link`, dark `dark-link`): link text and the mono step numbers and claim labels that act as
  wayfinding. Darker than the accent so it reaches text contrast on paper (5.5:1).

### Neutral
- **Drafting Paper** (`paper`): page ground. **Sheet White** (`surface`): cards, panels, fields, menus.
  **Warm Off-white** (`surface-2`): asides (`.angle`) and keycaps. **Sunken** (`sunken`): hover and pressed backgrounds
  for quiet controls, nav, rows and segmented choices. **Band** (`band`): full-bleed section bands.
  **Plate** (`plate`): the ground every drawing sits on.
- **Hairline** (`line`) and **Strong Hairline** (`line-strong`): borders; a third, translucent `--hair`
  (`rgba(23,21,14,.07)`, dark `rgba(255,255,255,.06)`) divides cells inside a bordered container.
- **Ink** (`ink`, `ink-2`, `ink-3`): primary text, secondary text and body of long text, muted metadata and labels.
- **Ink Fill** (`fill`, `fill-hover`): the primary button, the pressed chip, the brand mark and the skip link. In
  dark mode the fill turns light (`#EDECE8`) with dark ink on it.
- **Graphite** (`dark-paper`, `dark-surface`, `dark-surface-2`, `dark-sunken`, `dark-band`, `dark-plate`,
  `dark-line`, `dark-line-strong`, `dark-ink*`): the dark-theme equivalents of the roles above.

### Status
| Status | Token | Light | Dark | Badge |
|---|---|---|---|---|
| Expired (full term, design, past term) | `--expired` (= `--free`) | `expired` | `dark-expired` | solid dot, soft green wash |
| Lapsed, fee not paid (can be reinstated) | `--lapsed` (= `--warn`) | `lapsed` | `dark-lapsed` | solid dot, soft amber wash |
| Likely abandoned application (inferred) | `--aband` | `abandoned` | `dark-abandoned` | hollow ring dot, dashed border |
| Reserved | `--reserved` | `reserved` | `dark-reserved` | solid dot, default hairline border |
| Error | `--danger` | `danger` | `dark-danger` | text only (`.status.err`) |

Soft washes are the `*-soft` tokens (light: tints; dark: the status hue at 12% alpha). Badge borders are the status
hue mixed to 30% (55% and dashed for abandoned).

### Named Rules
**The Status Is Not The Accent Rule.** Orange means "you can act here" or "you are here"; status meaning comes only
from the four status hues, and each badge carries its word.

**The Ink Fill Rule.** The filled primary action is ink, never orange. Orange stays rare enough to mark focus.

## Typography

**Display Font:** IBM Plex Sans (variable 100-700, with -apple-system, Helvetica Neue, Arial)
**Body Font:** IBM Plex Sans; IBM Plex Serif 400 / 400 italic / 600 (with Charter, Georgia) for source text
**Label/Mono Font:** IBM Plex Mono 400 / 500 / 600 (with ui-monospace, SF Mono, Menlo)

**Character:** One humanist-grotesque family in three cuts, so the voices differ by register rather than by
personality. Self-hosted woff2 in `assets/fonts` (OFL), Latin plus Latin Extended for sans and serif 400.

### Hierarchy
- **Display** (600, `clamp(36px,4.4vw,58px)`, 1.04, -0.025em, max 14ch): home hero only.
- **Headline** (600, `clamp(28px,3.4vw,40px)`, 1.1, -0.028em): page `h1` in `.sechead`; patent title `.phead h1`
  runs `clamp(28px,3.6vw,42px)` at -0.03em, max 24ch.
- **Title** (600, `clamp(22px,2.3vw,28px)`, 1.15, -0.022em): section `h2`; patent sections `clamp(20px,2vw,24px)`.
- **Card title** (600, 16.5px, 1.28, -0.012em): card `h3`; featured card grows to `clamp(22px,2.2vw,28px)`.
- **Body** (400, 16px, 1.6): default. Lede `clamp(17px,1.6vw,19px)`/1.5 in `ink-3`, max 52-58ch. Long prose 16/1.7
  in `ink-2`.
- **Source** (Serif 400, 16px, 1.7): abstract (`.source`); claims 15/1.7 (`.claimlist li`); description 15.5/1.75,
  max 76ch (`.desc p`).
- **Number** (Mono 500, 11.5px, tabular): patent numbers (`.num-id`, `.num`), dates, counts, chart text, captions.
- **Label** (Mono 500, 10-11px, uppercase, 0.06-0.1em tracking): data labels in fact grids and card meta
  (`.facts small`, `.cmeta small`), filter row labels, FIG captions, section labels inside patent blocks.
- **Metric** (Sans 600, `clamp(22px,2vw,28px)`, tabular figures): the big numbers in `.statband`.

All headings: weight 600, `text-wrap: balance`, tracking -0.012em by default. Paragraphs use `text-wrap: pretty`.

### Named Rules
**The Three Voices Rule.** Sans for what Patent Yard writes, Serif for what the patent says, Mono for numbers and
identifiers. A quoted claim in the sans, or a summary in the serif, is a bug.

**The Sans Metric Rule.** Big ledger numbers are sans with tabular figures, not mono; mono is for small numbers.

## Layout

Body padding 20px inline (40px from 900px). Content sits in `.wrap` (max 1240px, centered); reading pages use
`.narrow` (820px). The header is sticky (56px) with a 1px bottom hairline; sections are spaced 80px apart, the footer
96px below content. Grids use one gap token (16px).

- **Card grids:** `.grid` auto-fill at min 250px; `.wall` 1/2/3 columns at 640/1000px with a full-width featured card;
  `.bento` 4/3/2/1 columns at 1100/820/520px; `.rail` horizontal scroll-snap, four visible on desktop.
- **Patent page:** `.playout` 190px sticky table of contents plus content (single column under 980px, where the TOC
  becomes a horizontal tab strip); `.ov` overview of drawing and facts side by side under 900px collapses.
- **Data cells:** `.statband`, `.facts`, `.fees`, `.steps3`, `.pipe`, `.omethod`, `.fchips` share one pattern: a
  bordered container whose cells are divided by `--hair` lines, collapsing to 2 or 1 columns on narrow screens.
- **Navigation breakpoints:** header search hides under 1180px (command button appears); main nav folds into a menu
  under 1080px; theme button hides under 520px.
- Sticky asides and in-page anchors offset by 76px (`scroll-padding-top: 72px` on `html`).

## Elevation & Depth

Flat by default; hairlines carry structure. Depth appears only as a response to hover or for layers that float over
content. In dark mode `--shadow-sm` is none and the other two become deep, low-opacity black drops.

### Shadow Vocabulary
- **Rest** (`--shadow-sm: 0 1px 2px rgba(23,21,14,.05)`): the home search field at rest.
- **Lift** (`--shadow: 0 1px 2px rgba(23,21,14,.05), 0 10px 28px -14px rgba(23,21,14,.18)`): card, tile, gallery and
  opportunity hover; the home plotter and the sign-in card.
- **Float** (`--shadow-lg: 0 2px 6px rgba(23,21,14,.06), 0 28px 64px -24px rgba(23,21,14,.3)`): dialogs, menus,
  suggestion lists, pickers, toasts, the loupe.
- **Focus wash** (`0 0 0 3px var(--accent-soft)`): fields and the search bar on focus, in addition to the ink border.

### Named Rules
**The Flat-At-Rest Rule.** Containers rest flat with a hairline; a shadow is a state (hover) or a layer (floating).

## Shapes

Two radii: 6px (`--radius-sm`) for buttons, chips, badges, fields, small tiles and claim rows; 10px (`--radius`) for
cards, panels, drawings, dialogs and menus. Circles only for dots, avatars and spinners. Borders are always 1px
hairlines except the dashed edge that marks inferred status and empty states (`.empty`, `.nofig`). Keycaps carry a 2px
bottom border. On phones (under 720px) dialogs go full-screen with no radius.

## Components

### Buttons (`.btn.primary | secondary | quiet | link`, sizes `.sm`, `.lg`)
- **Shape:** gently squared (6px), min-height 38px (30 small, 46 large), Sans 500 14px.
- **Primary:** ink fill with paper text; hover to `fill-hover`. One per group.
- **Secondary:** sheet white with a strong hairline; hover darkens the border to `ink-3`.
- **Quiet / Link:** transparent, `ink-2` (link uses `link` color), hover fills `sunken`.
- **States:** press scales to .97; disabled at 40% opacity; `.loading` hides the label behind a 14px spinner.

### Chips (`.chip`, `.chip.sm`)
- **Style:** text buttons 30px tall, transparent, `ink-2`, with a mono micro-counter in `ink-3`.
- **State:** hover fills `sunken`; pressed (`aria-pressed="true"`) is ink fill, the counter at 70% of the fill ink.
  `.chip.sm` is a static 22px mono tag with a hairline.

### Status badges (`.badge.expired | lapsed | abandoned | reserved | ok | plain`)
- 22px tall, 6px radius, Sans 500 11.5px, a 6px dot before the word. Colors per the Status table. On cards they sit
  top-left over the drawing (`.over`).

### Cards (`.card`, `.card.feat`, `.card.acard`, `.card.skel`)
- **Corner Style:** 10px, hairline border, sheet white.
- **Figure:** `.fig` is a 4:3 plate with the drawing contained (multiply blend in light, inverted screen blend in
  dark), `FIG. 1` in Mono 500 10px at the lower-left, the sheet count lower-right. No drawing on file: the field glyph
  and the patent number in mono (`.fig.plate`, `.numart`).
- **Body:** mono number, sans title (the whole card is the link via a stretched `::after`), 3-line clamped summary,
  then `.cmeta`, a hairline-divided row of mono labels over values.
- **Hover:** border to `line-strong`, Lift shadow, 2px rise, drawing scales 1.05. In the table view (`.grid.as-table`)
  cards become flat ruled rows with no lift.
- **Featured:** text left, drawing right, full grid width; stacks under 640px.
- **Loading:** `.card.skel` shimmer placeholders.

### Inputs / Fields (`.field`, `.fgroup`, `.bigsearch`, `.hsearch`)
- **Style:** sheet white, strong hairline, 6px radius, min-height 40px; labels Sans 500 13.5px, hints 12.5px `ink-3`.
- **Focus:** border goes to ink plus the 3px accent wash (header search: accent border). No outline ring on fields.
- **Error:** status text in `danger` below the form (`.status.err`); the sign-in status shakes once.
- **Home search** (`.bigsearch`): a 10px-radius command bar, 16.5px input, keycap hints, primary button inside.

### Navigation (`.top`, `.mainnav`, `.toc`, `.crumbs`, `.legalnav`)
- Sticky header on the page ground with a bottom hairline; brand mark is a 28px ink tile (8px radius) that tilts on
  hover. Nav links Sans 500 13.5px in `ink-3`; hover and current page fill `sunken` with ink text. Under 1080px the nav
  opens as a full-width list of 17px ruled rows, the current page in link color.
- Patent table of contents: a left hairline; the current section takes a 1px accent rule.

### Data ledger (`.statband`, `.facts`)
- Hairline-ruled cells. Statband: sans metric numbers, a mono note above, a 13px caption below. Facts: mono label
  over a mono value.

### Drawing plate (`.bigfig`, `.gallery figure`, `.ofig`, `.plotter`, `.gfront`)
- The signature: every patent drawing on `plate`, strong hairline, 10px radius, zoom-in cursor, `FIG. 1` caption
  lower-left, and a full-screen `#viewer` on near-black with the sheet on white. The home plotter draws the figure on
  canvas with a magnifying loupe.

### Claims (`.claimlist`)
- Serif 15/1.7, mono claim numbers. Independent claims are bordered sheet-white blocks; dependents indent by depth
  (20/40/60px) behind a strong left hairline; a targeted claim takes the accent wash.

### Ranking explanation (`details.why`)
- A hairline-topped disclosure with a mono plus/minus marker, the score right-aligned in mono, and factor rows below.

### Dialogs and overlays (`dialog`, `.cmdk`, `.sugg`, `.acctmenu .menu`, `.toast`)
- Sheet white, strong hairline, 10px radius, Float shadow. Dialogs rise 10px and fade in; backdrop is graphite at 55%.
  Toasts sit bottom-center with a status-colored icon dot.

### Utilities
- Honeypot `.trap` (off-screen, inert). Optional-field tag `.opt` (12.5px `ink-3`). Skip link `.skip` (ink fill,
  appears on focus). Screen-reader text `.sr`.

## Motion

Not a canonical DESIGN.md section in the spec's eight, kept here because the motion tokens are part of the system;
the sidecar carries them as `extensions.motion`.

- **Curves:** `--ease: cubic-bezier(.22,.8,.24,1)` for every transition and entry; `--spring` (a `linear()` damped spring,
  about 5% overshoot) only for things that are pressed or arrive small: button release, saved/reserved/copied pops, toasts.
- **Durations:** `--t1` .16s (link color, buttons, ruled-list hover), `--t2` .24s (home search focus, page view
  transitions), `--t3` .42s (section reveal). Most hover transitions in the stylesheet use a literal .3s with
  `--ease`; drawing zoom on hover is .6s.
- **Page to page:** cross-document view transitions (`@view-transition { navigation: auto }`), root cross-fade at
  `--t2` with the header held still (`view-transition-name: top`). Opening a patent from a card carries that card's
  drawing into the patent page's drawing (`theme.js` names the pair `pfig` on `pageswap`/`pagereveal`, `--t3`), only
  when the target drawing is on screen.
- **Entry:** sections rise 14px once on scroll (`.reveal`); new card batches stagger in 30ms apart; charts draw in.
- **Reduced motion:** under `prefers-reduced-motion: reduce` or the site's `data-motion="reduce"`, all animations,
  transitions and view transitions are disabled, the ticker stops and charts render at their final state.

## Accessibility

- **Underlined links in running text:** links inside `p`, `dd`, prose list items and check lists are underlined
  (1px, offset 2px, 45% current color, full on hover), never told apart by color alone. Nav, buttons and chips are
  exempt.
- **Focus:** every focusable element gets a 2px `--focus` outline at 2px offset; fields use the ink border plus wash.
- **Contrast (measured):** `ink-3` on paper 5.3:1, on sunken 4.9:1; `link` on paper 5.5:1; status text on its own wash
  4.6-5.1:1 (light) and 7.5-8.7:1 (dark on surface); dark `ink-3` on graphite 6.1:1.
- **Status by word:** every status color appears with its word; inferred status adds a dashed edge and hollow dot so
  it does not rely on hue.
- **Visitor settings:** theme, original white drawings in dark mode, large text (zoom 1.12) and reduced motion.

## Do's and Don'ts

### Do:
- **Do** take every color from the CSS variables so light, dark and the settings page all follow.
- **Do** put any new patent drawing on `plate` with the multiply/invert blend variables and a mono FIG caption.
- **Do** set patent-quoted text in Plex Serif, numbers and dates in Plex Mono, and everything else in Plex Sans.
- **Do** pair every status color with its word, and draw inferred status with the dashed edge.
- **Do** divide data with hairlines inside one bordered container rather than boxing each value.
- **Do** use 6px for controls and 10px for containers; nothing else.
- **Do** honor both reduced-motion switches for any new animation.

### Don't:
- **Don't** use orange for status, or a status hue for actions.
- **Don't** fill the primary button with the accent.
- **Don't** add glows, gradient text, background grids, glass blur, corner brackets or fake window chrome.
- **Don't** put shadows on resting containers.
- **Don't** add pictures other than patent drawings.
