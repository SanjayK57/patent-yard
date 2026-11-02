---
name: Patent Yard
description: A free register of expired, lapsed and abandoned patents, where the patent drawing is the product shot and the interface recedes around it.
colors:
  accent: "#116289"
  accent-hover: "#015477"
  accent-ink: "#FFFFFF"
  accent-soft: "#E1F1FC"
  link: "#005F88"
  focus: "#1F7FB0"
  bg: "#F5F7F8"
  surface: "#FFFFFF"
  surface-2: "#FAFBFB"
  sunken: "#EEF1F2"
  band: "#ECF0F2"
  plate: "#FFFFFF"
  line: "#DDE0E2"
  line-strong: "#C6CBCE"
  ink: "#161A1D"
  ink-2: "#484E52"
  ink-3: "#676E73"
  expired: "#1A763F"
  expired-soft: "#E0F7E5"
  lapsed: "#995600"
  lapsed-soft: "#FFEFD4"
  aband: "#59656D"
  aband-soft: "#E9EDF0"
  reserved: "#724AAB"
  reserved-soft: "#F3ECFF"
  danger: "#BA2B28"
  accent-dark: "#64B5E4"
  link-dark: "#75C2EF"
  bg-dark: "#111416"
  surface-dark: "#181B1D"
  plate-dark: "#141719"
  line-dark: "#2A2F31"
  ink-dark: "#EEF0F2"
  ink-2-dark: "#BABEC1"
  ink-3-dark: "#969B9F"
typography:
  display:
    fontFamily: "Hanken Grotesk, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif"
    fontSize: "clamp(34px, 5.6vw, 76px)"
    fontWeight: 650
    lineHeight: 1.02
    letterSpacing: "-0.038em"
  headline:
    fontFamily: "Hanken Grotesk, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif"
    fontSize: "40px"
    fontWeight: 600
    lineHeight: 1.08
    letterSpacing: "-0.03em"
  title:
    fontFamily: "Hanken Grotesk, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif"
    fontSize: "28px"
    fontWeight: 600
    lineHeight: 1.14
    letterSpacing: "-0.022em"
  body:
    fontFamily: "Hanken Grotesk, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.55
  source:
    fontFamily: "Source Serif 4, Iowan Old Style, Charter, Georgia, serif"
    fontSize: "17px"
    fontWeight: 400
    lineHeight: 1.65
  label:
    fontFamily: "Hanken Grotesk, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif"
    fontSize: "12px"
    fontWeight: 550
    lineHeight: 1
  identifier:
    fontFamily: "ui-monospace, SF Mono, SFMono-Regular, Menlo, Consolas, Liberation Mono, monospace"
    fontSize: "0.92em"
    letterSpacing: "-0.01em"
rounded:
  xs: "4px"
  sm: "6px"
  r: "8px"
  md: "12px"
  lg: "16px"
  xl: "22px"
spacing:
  s1: "4px"
  s2: "8px"
  s3: "12px"
  s4: "16px"
  s5: "20px"
  s6: "24px"
  s7: "32px"
  s8: "40px"
  s9: "48px"
  s10: "64px"
  s11: "80px"
  s12: "112px"
components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.accent-ink}"
    rounded: "{rounded.r}"
    padding: "0 14px"
    height: "36px"
  button-primary-hover:
    backgroundColor: "{colors.accent-hover}"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.r}"
    padding: "0 14px"
    height: "36px"
  button-quiet:
    textColor: "{colors.ink-2}"
    rounded: "{rounded.r}"
    padding: "0 10px"
    height: "36px"
  chip-filter-on:
    backgroundColor: "{colors.accent-soft}"
    textColor: "{colors.link}"
    rounded: "{rounded.r}"
    padding: "0 11px"
    height: "30px"
  field:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.r}"
    padding: "8px 12px"
    height: "38px"
  badge-lapsed:
    backgroundColor: "{colors.lapsed-soft}"
    textColor: "{colors.lapsed}"
    rounded: "{rounded.sm}"
    padding: "0 8px"
    height: "22px"
  badge-expired:
    backgroundColor: "{colors.expired-soft}"
    textColor: "{colors.expired}"
    rounded: "{rounded.sm}"
    padding: "0 8px"
    height: "22px"
  badge-abandoned:
    backgroundColor: "{colors.aband-soft}"
    textColor: "{colors.aband}"
    rounded: "{rounded.sm}"
    padding: "0 8px"
    height: "22px"
  badge-reserved:
    backgroundColor: "{colors.reserved-soft}"
    textColor: "{colors.reserved}"
    rounded: "{rounded.sm}"
    padding: "0 8px"
    height: "22px"
  card-sheet:
    backgroundColor: "{colors.plate}"
    rounded: "{rounded.lg}"
    padding: "38px 22px 26px"
  panel:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.md}"
    padding: "20px 24px"
---

# Design System: Patent Yard

## Overview

**Creative North Star: "The Drawing Is the Product Shot"**

Patent Yard is desktop-class software for reading old patents. A cool near-white page (near-black charcoal in dark mode) carries white surfaces drawn with 1px hairline rings, Hanken Grotesk for everything the site says, and one Prussian blue accent, the color of the cyanotype blueprints patent drawings were once copied as. The interface stays quiet so the patent drawing, always on its sheet, carries each page.

Density follows the task. The home page persuades with one large headline, the biggest search box on the site and a plotted drawing. Browse and account pages operate with chips, segmented controls and dense grids. Patent pages read like a well-set technical document with the drawing first and the patent's own text in a serif.

All values live in `web/styles/tokens.css`. Dark mode is written once as `:root[data-theme="dark"]`, and `pipeline/site_ui/styles.py` copies each dark rule for visitors whose system is dark and who have not picked a theme. Templates and scripts use token names only.

**Key Characteristics:**
- Cool neutrals, one blue accent, four status colors that always come with a word.
- Hairlines as 1px box-shadow rings, not borders; most content sits directly on the page.
- Two voices in type: grotesk for Patent Yard, serif for the patent, system mono for identifiers.
- 8px controls, 12 to 22px containers, a raised thumb in segmented controls.
- Motion refines arrival and never gates content; reduced motion stops all of it.

## Colors

Cool, low-chroma neutrals with one saturated blue and four muted status hues, each with a soft tint for label backgrounds.

### Primary
- **Prussian Blue** (accent; `accent-dark` in dark mode): primary buttons, the current-page underline in the nav, focus rings, pressed filter chips, the save button when on. Hover deepens to `accent-hover`.
- **Link Blue** (link; `link-dark`): text links and the text of pressed chips. Links inside running text are also underlined, never told apart by color alone.
- **Blueprint Wash** (accent-soft): fill for pressed chips, highlighted claims, menu and palette selection, and the focus halo around fields and the big search.

### Status
- **Lapsed Amber** (lapsed on lapsed-soft): a maintenance fee was not paid.
- **Past-Term Green** (expired on expired-soft): the term ended. The same green is `--free` for success messages.
- **Inferred Gray** (aband on aband-soft): likely abandoned. Its dot is hollow because the status is inferred, not recorded.
- **Reserved Violet** (reserved on reserved-soft): a builder reserved it.
- **Danger Red** (danger): form errors and patents pulled from the register only.

### Neutral
- **Cool Page** (bg; `bg-dark`): the page itself.
- **White Surface** (surface, surface-2; `surface-dark`): panels, menus, dialogs, fields, secondary buttons.
- **Sunken** (sunken) and **Band** (band): recessed tracks, small chips, skeletons; the footer and full-bleed section bands.
- **The Sheet** (plate; `plate-dark`): the ground every patent drawing sits on.
- **Hairlines** (line, line-strong; `line-dark`): 1px rings and dividers; the strong line for hover and field borders.
- **Ink** (ink, ink-2, ink-3): headings and values, running text, captions and meta.

### Named Rules
**The Accent Has Four Jobs Rule.** The accent marks primary actions, links, focus and selection, and the state that follows from them (your own reservation, the current document in its family, reading progress, the plotter's pen). The brand mark is the one fill of identity. Decoration is never blue: callouts, icon tiles and notices use the neutral surfaces.

**The Word With a Color Rule.** A status is always a word with its color: lapsed amber, expired or past-term green, likely-abandoned gray with a hollow dot, reserved violet. Color never carries a status alone.

## Typography

**Display and UI Font:** Hanken Grotesk (self-hosted, weights 300 to 800, system sans fallback)
**Source Font:** Source Serif 4 (self-hosted, 400 to 600 with italics, Charter and Georgia fallback)
**Identifier Font:** the system mono stack (no web font)

**Character:** A crisp grotesk that tightens its tracking as it grows, set against a calm book serif reserved for the patent's own words.

### Hierarchy
- **Display** (650, clamp 34 to 76px, 1.02): the home headline only, centered, about 13.5em wide.
- **Headline** (600, 40px, 1.08): page titles; patent titles run clamp 30 to 46px. Drops to 32px under 700px.
- **Title** (600, 28px, 1.14): section heads; patent sections use 26px. Drops to 24px under 700px.
- **Body** (400, 16px, 1.55): interface text. Lead text is 19px; section intros 17px in ink-3, about 64ch.
- **Source** (400, 17px, 1.65 to 1.75): abstract, claims and description, 70 to 76ch measure.
- **Label** (550, 12 to 13.5px): status labels, chips, field labels, meta. Sentence case, no added tracking.
- **Identifier** (mono, 0.92em): patent and application numbers, classification codes, citations, family members.

### Named Rules
**The Two Voices Rule.** The patent's own words (abstract, claims, description) are set in Source Serif 4. Everything Patent Yard writes, including labels inside those sections, is Hanken Grotesk.

**The Numbers That Identify Rule.** Mono appears only on identifiers and on the prompts the Studio writes for Claude (text meant to be copied as it is). Counts and dates use the grotesk with tabular figures.

## Layout

A centered page of 1200px (header 1320px) with a fluid gutter of 16 to 40px, on a 4px spacing scale (`s1` to `s12`). Sections sit 112px apart (80px under 700px). The header is 52px (`--header-h`) and sticky. Reading columns cap at 68ch.

- **Home:** centered hero and a 640px search, then a 1080px drawing sheet at 16:9 (4:3 under 700px). Below: the collections as a ruled ledger beside its intro, today's picks as one lead card plus four across, a ruled list of more picks, a compact field index, three steps, and one dark Studio band.
- **Browse:** a filter toolbar panel over a card grid (`minmax(240px, 1fr)`) that can switch to a dense table view.
- **Patent page:** title and actions over a 184px sticky contents list and one reading column. Under 980px the contents become a sticky horizontal tab row.
- Navigation collapses to a menu sheet under 1080px; header search becomes a palette button under 1180px.

**The Page, Not the Box Rule.** Most content sits directly on the page. Panels group related rows; they are not wrapped around every section.

## Elevation & Depth

Mostly flat, with hairline rings for edges and soft, offset shadows only for things that lift: hovered cards, menus, dialogs, toasts and the home drawing sheet. In dark mode shadows deepen and surfaces gain a faint top highlight (`--edge`).

### Shadow Vocabulary
- **Rest** (`--sh-1`): buttons and the raised thumb of a segmented control.
- **Lift** (`--sh-2`): hovered cards and drawings, the big search box.
- **Float** (`--sh-3`): menus, suggestions, dialogs, toasts.
- **Sheet** (`--sh-sheet`): the home plotter's drawing sheet only.

**The Ring, Not the Border Rule.** Edges are `box-shadow: 0 0 0 1px var(--line)` (inset on drawings). Form fields are the exception and use a real 1px border.

## Shapes

Gently rounded, growing with size: 4px for focus outlines and tiny marks, 6px for status labels and nav items, 8px for every control, 12px for panels and menus, 16px for drawing sheets and dialogs, 22px for the home plotter. Avatars and the dialog close button are circles. Large buttons use 10px; the big search box 14px.

## Components

### Buttons
- **Shape:** 8px corners, 36px tall (30px small, 46px large), weight 550.
- **Primary:** accent fill, accent-ink text, a faint inner top highlight. One per view where possible.
- **Secondary:** white surface with a strong hairline ring. **Quiet and Link:** no fill; quiet is ink-2, link is link blue.
- **States:** hover tints in 120ms; press scales to 0.97 on the spring; disabled is 45% opacity; loading swaps the label for a spinner.

### Chips and Segmented Controls
- **Filter chips:** text buttons, 30px tall, no fill at rest, an ink tint on hover, accent-soft fill with link text at weight 600 when pressed.
- **Segmented controls:** a recessed track (ink at 7%) with a raised thumb (`--thumb`, Rest shadow) on the chosen option.

### Status Labels
- 22px tall, 6px corners, 12px at weight 550, tinted background with a 6px dot in the status color; likely abandoned has a hollow dot. `card_html` and the `badge()` helper in `cards.js` always emit the class and the word together.

### Cards
- **Patent card:** the drawing on its sheet (4:3, 16px corners, inset hairline), then the words with no box around them: field and number, a 17px title, two lines of summary, a ruled meta row. Status labels sit over the sheet's top-left corner; the save button appears top-right on hover (always on touch screens).
- **Hover:** the sheet lifts 3px with the Lift shadow, the drawing scales to 1.04, the title turns link blue.
- **Lead card:** drawing large on the right, words on the left; stacks under 820px.
- **Contract:** server markup (`pipeline/site_ui/components.py` `card_html`) and browser markup (`web/static/assets/js/cards.js`) are one contract, checked by `web/dev/test_cards.mjs`.

### Inputs
- 38px, 1px line-strong border, 8px corners, white surface. Focus turns the border accent with a 4px accent-soft halo. Invalid uses the danger border.
- **Big search:** the largest control on the site, 14px corners, Lift shadow, a filled Search button inside.

### Navigation
- A sticky translucent bar in the page color; a hairline appears once the page scrolls under it. Items are 14px weight 500 in ink-2; the current page is ink with a 2px accent underline on the bar's bottom edge. Under 1080px the links open as a full-width sheet of ruled 17px rows.

### Drawings
- Every drawing sits on `--plate` with an inset hairline. Images use `--fig-blend` and `--fig-filter`: multiplied onto white in light mode, inverted and screened onto the dark sheet in dark mode, and black on white again when the visitor picks original drawings (`data-drawings="original"`). The full-screen viewer is a dark stage in both themes with each sheet on white.

### The Plotter (signature)
- On the home sheet a pen traces the drawing's strokes in order over about 3s on an ease-in-out cubic, with ink settling behind the pen over 220ms (`web/static/assets/js/home.js`). A loupe magnifies under the pointer on wide screens. With reduced motion the finished drawing shows at once.

### Motion
- One ease-out curve (`--ease`), an ease-in-out for the theme fade, a spring for presses and small arrivals, four durations (120, 200, 360, 520ms). Pages cross-fade on navigation; a card's drawing flies into the patent page's first drawing through the `pfig` view transition (`theme.js`); switching theme is a slow whole-page cross-fade (`app.js`). Content is visible without motion; motion only refines how it arrives.

**The Stillness Rule.** Reduced motion, from the system setting or the site's own `data-motion="reduce"`, stops every animation, transition and view transition, and the scripts skip the plotter, digit strikes and celebrations.

## Do's and Don'ts

### Do:
- **Do** take every value from `tokens.css`, and write dark overrides once under `:root[data-theme="dark"]`.
- **Do** show a status as its word plus its color, with the hollow dot for likely abandoned.
- **Do** set abstract, claims and description in Source Serif 4, and everything else in Hanken Grotesk.
- **Do** put identifiers (patent and application numbers, classification codes) in the system mono stack.
- **Do** keep every drawing on its sheet (`--plate`) and pass it through `--fig-blend` and `--fig-filter`.
- **Do** draw edges as 1px rings and keep content on the page rather than in boxes.
- **Do** check new motion under both reduced-motion switches.

### Don't:
- **Don't** use the accent for anything but primary actions, links, focus and selection.
- **Don't** put eyebrow or kicker labels above headings.
- **Don't** use gradient text, decorative glass, or glow.
- **Don't** set Patent Yard's own copy in the serif, or counts and prose in mono.
- **Don't** show a drawing off its sheet, or uninverted in dark mode unless the visitor chose original drawings.
- **Don't** hide content behind an entrance animation.

## Where to change it

| Request | File |
|---|---|
| Accent or any color, type size, spacing, radius, shadow, duration | `web/styles/tokens.css` (light block, then the dark block) |
| Nav height | `--header-h` in `web/styles/tokens.css` |
| Header, nav, footer | `pipeline/site_ui/shell.py`; styles in `web/styles/layout.css` |
| Card radius, card hover, list view | `web/styles/cards.css` (`.card .fig`); markup in `components.py` and `cards.js` together |
| Buttons, chips, fields, status labels | `web/styles/controls.css` |
| Patent page density and layout | `web/styles/pages/patent.css`; markup in `pipeline/site_ui/pages/patent.py` |
| Home layout | `pipeline/site_ui/pages/home.py` and `web/styles/pages/home.css` |
| Plotter speed and ink | `web/static/assets/js/home.js` (`DUR`, `FADE`) |
| Page, theme and card-to-patent transitions | `web/styles/motion.css`, `web/static/assets/js/app.js`, `web/static/assets/js/theme.js` |
| One page's own styles | `web/styles/pages/<page>.css`, imported in `web/styles/site.css` |
