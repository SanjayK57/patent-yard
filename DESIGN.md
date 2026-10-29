---
name: Patent Yard
description: A free register of expired patents, built as a precise technical instrument; spatial dark, monospace data, every drawing in a blueprint frame.
colors:
  indigo: "#4F46E5"
  indigo-hover: "#4338CA"
  indigo-soft: "#EEF0FF"
  fill: "#0B0B0F"
  fill-hover: "#26262E"
  free-emerald: "#0E8A5F"
  free-emerald-soft: "#E5F6EF"
  inferred-amber: "#B45309"
  inferred-amber-soft: "#FEF4E2"
  reserved-violet: "#6D28D9"
  reserved-violet-soft: "#F1EAFE"
  alert-orange: "#C2410C"
  alert-orange-soft: "#FFF1E8"
  canvas: "#FAFAFB"
  surface: "#FFFFFF"
  surface-raised: "#F4F4F6"
  sunken: "#ECECF0"
  hairline: "#E4E4E9"
  hairline-strong: "#CDCDD5"
  hair: "rgba(10,10,14,.07)"
  grid-line: "rgba(11,11,15,.055)"
  glow: "rgba(99,102,241,.07)"
  ink: "#0B0B0F"
  ink-secondary: "#3B3B45"
  ink-tertiary: "#5F5F6B"
  dark-canvas: "#070709"
  dark-surface: "#0F0F13"
  dark-plate: "#0B0B0E"
  dark-sunken: "#16161C"
  dark-hairline: "#1E1E24"
  dark-hairline-strong: "#2C2C35"
  dark-hair: "rgba(255,255,255,.06)"
  dark-grid-line: "rgba(255,255,255,.045)"
  dark-glow: "rgba(99,102,241,.03)"
  dark-ink: "#EDEDF1"
  dark-ink-secondary: "#B9B9C3"
  dark-ink-tertiary: "#8B8B97"
  dark-indigo: "#8B8EF7"
  dark-indigo-hover: "#A5A8FA"
  dark-fill-hover: "#FFFFFF"
  dark-free-emerald: "#34D399"
  dark-inferred-amber: "#FBBF24"
  dark-reserved-violet: "#C4B5FD"
  dark-alert-orange: "#FB923C"
typography:
  display:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, Helvetica Neue, Arial, sans-serif"
    fontSize: "clamp(40px, 6.4vw, 76px)"
    fontWeight: 600
    lineHeight: 1.02
    letterSpacing: "-0.04em"
  headline:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, Helvetica Neue, Arial, sans-serif"
    fontSize: "clamp(28px, 3.4vw, 40px)"
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: "-0.028em"
  section:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, Helvetica Neue, Arial, sans-serif"
    fontSize: "clamp(22px, 2.3vw, 28px)"
    fontWeight: 600
    lineHeight: 1.15
    letterSpacing: "-0.022em"
  title:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, Helvetica Neue, Arial, sans-serif"
    fontSize: "16.5px"
    fontWeight: 600
    lineHeight: 1.28
    letterSpacing: "-0.012em"
  lede:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, Helvetica Neue, Arial, sans-serif"
    fontSize: "clamp(17px, 1.6vw, 19px)"
    fontWeight: 400
    lineHeight: 1.5
  body:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, Helvetica Neue, Arial, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.55
    letterSpacing: "0"
    fontFeature: "\"cv11\", \"ss01\", \"ss03\""
  data:
    fontFamily: "JetBrains Mono, ui-monospace, SF Mono, Menlo, Consolas, monospace"
    fontSize: "clamp(19px, 1.75vw, 25px)"
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: "-0.045em"
    fontFeature: "\"tnum\""
  code:
    fontFamily: "JetBrains Mono, ui-monospace, SF Mono, Menlo, Consolas, monospace"
    fontSize: "11.5px"
    fontWeight: 500
    lineHeight: 1.2
    letterSpacing: "0.01em"
  label:
    fontFamily: "JetBrains Mono, ui-monospace, SF Mono, Menlo, Consolas, monospace"
    fontSize: "10.5px"
    fontWeight: 500
    lineHeight: 1
    letterSpacing: "0.08em"
  eyebrow:
    fontFamily: "JetBrains Mono, ui-monospace, SF Mono, Menlo, Consolas, monospace"
    fontSize: "11.5px"
    fontWeight: 500
    lineHeight: 1
    letterSpacing: "0.12em"
rounded:
  micro: "5px"
  xs: "6px"
  sm: "8px"
  md: "12px"
spacing:
  gap: "16px"
  gutter-mobile: "20px"
  gutter-desktop: "40px"
  grid-cell: "20px"
  fig-bar: "30px"
  card-body: "14px 16px 12px"
  panel: "22px"
  section: "80px"
components:
  button-primary:
    backgroundColor: "{colors.fill}"
    textColor: "{colors.surface}"
    rounded: "{rounded.sm}"
    padding: "8px 16px"
    height: "38px"
  button-primary-hover:
    backgroundColor: "{colors.fill-hover}"
    textColor: "{colors.surface}"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sm}"
    padding: "8px 16px"
    height: "38px"
  button-quiet:
    backgroundColor: "transparent"
    textColor: "{colors.ink-secondary}"
    rounded: "{rounded.sm}"
    padding: "8px 10px"
    height: "38px"
  button-quiet-hover:
    backgroundColor: "{colors.sunken}"
    textColor: "{colors.ink}"
  chip:
    backgroundColor: "transparent"
    textColor: "{colors.ink-secondary}"
    rounded: "{rounded.sm}"
    padding: "0 11px"
    height: "30px"
  chip-pressed:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
  badge:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink-secondary}"
    rounded: "{rounded.xs}"
    padding: "0 8px"
    height: "22px"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sm}"
    padding: "9px 12px"
    height: "40px"
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "{spacing.card-body}"
  stat-block:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.data}"
    padding: "18px 20px"
  view-toggle:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink-tertiary}"
    rounded: "{rounded.sm}"
    padding: "2px"
    height: "30px"
---

# Design System: Patent Yard

## Overview

**Creative North Star: "The Drafting Instrument"**

Patent Yard reads like a precision tool laid over the patent record: a deep spatial dark (#070709 base, light mode mirrors it on #FAFAFB), words in Inter, every number, code and date in JetBrains Mono, hairline borders in place of filled boxes, and every patent drawing pinned inside a blueprint frame with a window bar, a FIG tag and a 20px grid. The drawing is the specimen; the chrome around it is the instrument.

Density is calm on the home page (centered hero, command-palette search, one large plotted drawing) and dense on working pages (left-aligned headings, grouped segmented filters with micro-counters, cards that collapse into a table). Motion is spring-like and short: cards lift with a border-luminance shift, numbers strike into place digit by digit, sections reveal once on scroll, and every motion honors both the OS reduced-motion preference and the site's own setting.

The system was set by Sanjay's Gemini-sourced brief of 2026-10-27, which replaced an earlier Apple-style light pass he rejected as still "AI-looking". It is a dark technical instrument, not neon: the indigo glow behind the hero and search sits at 3% opacity in dark.

**Key Characteristics:**
- Spatial dark by default with a true light mirror; theme follows the system unless the visitor picks.
- Inter for words, JetBrains Mono for numbers, codes, dates and short uppercase instrument labels.
- Hairline borders (1px) and hairline dividers inside containers; shadows only on hover and floating layers.
- Blueprint frame (30px window bar with three dots, FIG tag, 20px grid) around every patent drawing.
- One filled button per action group: white in dark, black in light.
- Honest data only: every figure on screen is counted from the catalog.

## Colors

A near-monochrome instrument palette: graphite surfaces, one indigo voice for links and focus, and status colors that only ever mean status.

### Primary
- **Signal Indigo** (light `indigo`, dark `dark-indigo`): links, focus rings, the `//` in eyebrows, active TOC rail, claim numbers of independent claims, selected task outlines, bar-chart fills. Never a button fill.
- **Indigo Wash** (`indigo-soft`, in dark an indigo at 14%): focus halo around inputs and search, highlighted claims, archive hint strip.
- **Instrument Fill** (`fill` / `fill-hover`; in dark it inverts to `dark-ink` with `dark-fill-hover`): the one filled primary button, the brand mark tile, the skip link.

### Secondary
- **Free Emerald** (`free-emerald`, dark `dark-free-emerald`): the status dot for lapsed and expired patents (free to use), success toasts, check marks in "Is it free to use?", the "+N this week" stat tag.

### Tertiary
- **Inferred Amber** (`inferred-amber`, dark `dark-inferred-amber`): "Likely abandoned" (an inference, not a fact) and warnings.
- **Reserved Violet** (`reserved-violet`, dark `dark-reserved-violet`): the reserved marker on cards.
- **Alert Orange** (`alert-orange`, dark `dark-alert-orange`): errors, the password meter, "pulled from the register" notices. (The CSS variable is named `--lapsed`; it is not used for lapsed patents, which are emerald.)

### Neutral
- **Canvas** (`canvas` / `dark-canvas`): page background.
- **Surface** (`surface` / `dark-surface`): cards, panels, filter bar, dialogs, stat band.
- **Plate** (`surface` / `dark-plate`): the paper under drawings; with the "original drawings" setting it is always white.
- **Sunken** (`sunken` / `dark-sunken`): hover and pressed backgrounds for nav, quiet buttons, segmented controls, table rows.
- **Hairline / Hairline Strong** (`hairline`, `hairline-strong` and dark pairs): container borders; pressed-chip, input and specimen-frame borders.
- **Hair** (`hair` / `dark-hair`): the 6-7% dividers inside a container (stat cells, card meta cells, facts grid).
- **Grid Line** (`grid-line` / `dark-grid-line`): the 20px blueprint grid.
- **Ink, Ink Secondary, Ink Tertiary**: headings and values, body copy, captions and labels.

### Named Rules
**The Status-Only Color Rule.** Emerald, amber, violet and orange appear only as status: a dot, a check, a tag, a notice. They never decorate.

**The Faint Glow Rule.** The indigo glow is ambient and near invisible (7% light, 3% dark), placed only behind the hero, the hero search, the plotter, the sign-in card and the CTA band. It is never a neon edge.

## Typography

**Display Font:** Inter (with -apple-system, Helvetica Neue, Arial)
**Body Font:** Inter, with stylistic sets cv11, ss01, ss03
**Label/Mono Font:** JetBrains Mono (with ui-monospace, SF Mono, Menlo)

**Character:** Inter carries every word at tight negative tracking for headings; JetBrains Mono is the instrument readout, reserved for what a machine would print.

### Hierarchy
- **Display** (600, clamp(40px, 6.4vw, 76px), 1.02, -0.04em): the home hero headline only, max 15ch, centered.
- **Headline** (600, clamp(28px, 3.4vw, 40px), 1.1): page titles in the left-aligned section head; patent titles run slightly larger (clamp(28px, 3.6vw, 42px), max 24ch).
- **Section** (600, clamp(22px, 2.3vw, 28px), 1.15): section heads; the lead card title uses clamp(22px, 2.2vw, 28px).
- **Title** (600, 16.5px, 1.28): card titles.
- **Lede** (400, clamp(17px, 1.6vw, 19px), 1.5, ink-tertiary): hero subhead, max 56-58ch.
- **Body** (400, 16px, 1.55): prose at 1.7 line height, descriptions at 15.5px / 1.75, max 68-80ch.
- **Data** (Mono 600, clamp(19px, 1.75vw, 25px), -0.045em, tabular): metric block figures.
- **Code** (Mono 500, 11.5px): patent numbers, claim numbers, counts, dates, keyboard keys.
- **Label** (Mono 500, 10-10.5px, 0.06-0.1em, uppercase): filter row labels, card meta labels, fact labels, FIG tags, block headings.
- **Eyebrow** (Mono 500, 11.5px, 0.12em, uppercase): "PATENT YARD // SECTION" above page headings, with the `//` in indigo.

### Named Rules
**The Mono-For-Machines Rule.** JetBrains Mono is for numbers, patent numbers and codes, dates, counts, keyboard keys, and short uppercase instrument labels. Never for names (patent titles, field names, owners) or sentences. Exception: a prompt shown as terminal input (`$ ` prefix, prompt textarea) counts as code.

**The Tabular Rule.** Every number set in mono uses tabular figures so columns and counters do not jitter.

## Layout

Fluid page with a 20px gutter (40px from 900px), content capped at 1240px (820px for narrow reading pages). A sticky 56px header blurs the canvas beneath it. Sections stack at 80px; working pages start 36px under the header with left-aligned section heads (eyebrow, headline, 68ch subhead, action on the right). Only the home hero is centered.

- **Bento:** four columns (three under 1100px, two under 820px, one under 520px), 16px gap, dense flow. The lead card spans the full row as a split card: text and meta on the left, the blueprint drawing on the right (flex 1.15); under 640px it stacks with the drawing on top.
- **Card grid:** auto-fill columns of at least 250px; the view toggle flips the same grid into a table (one row per card, drawing hidden, field name 200px, meta 340px; both hide under 860px). The choice is remembered per grid.
- **Metric band:** auto-fit columns of at least 170px in one bordered container, cells divided by hair lines; two columns under 820px, the first cell spanning when there are five.
- **Patent page:** 190px sticky TOC beside the content (becomes a horizontal tab strip under 980px); the overview splits drawing and facts.
- **Filters:** one bordered panel of labeled rows (84px mono label + chips); under 700px only the search row shows until "Filters" opens the rest.
- Scroll padding is 72px so anchors clear the sticky header.

## Elevation & Depth

Flat at rest, separated by hairlines and tonal steps (canvas, surface, sunken). Shadows appear in three places only: a card or tile on hover, floating layers (menus, suggestions, dialogs, toasts, magnifier), and the framed hero specimens (plotter, hero search, sign-in card) where a soft glow sits under them. In dark the small shadow is removed entirely and the larger ones become pure black falloffs.

### Shadow Vocabulary
- **Rest hint** (`box-shadow: 0 1px 2px rgba(11,11,15,.04)`; none in dark): pressed chips.
- **Lift** (`box-shadow: 0 1px 2px rgba(11,11,15,.04), 0 12px 32px -16px rgba(11,11,15,.18)`; dark `0 16px 40px -20px rgba(0,0,0,.8)`): card, tile, gallery and opportunity hover.
- **Float** (`box-shadow: 0 2px 6px rgba(11,11,15,.06), 0 32px 72px -24px rgba(11,11,15,.32)`; dark `0 32px 80px -24px rgba(0,0,0,.9)`): menus, suggestions, dialogs, toasts, magnifier.
- **Specimen glow** (`box-shadow: 0 40px 100px -40px var(--glow), var(--shadow)`): the plotter frame and the sign-in card.

### Named Rules
**The Lift-On-Touch Rule.** Containers rest flat. On hover a card rises 4px (tiles 2px) and its border brightens toward ink at 20%; the shadow follows the lift, never the reverse.

## Shapes

Gently squared: 12px for containers (cards, panels, filter bar, metric band, dialogs, frames), 8px for controls (buttons, chips, inputs, toggles, small cards), 6px for badges and inner pressed segments, 5px for kbd keys, stat tags and dependent-claim chips. Circles only for status dots, avatars and spinners. Borders are always 1px; dashed only for empty states. Containers clip their contents so inner dividers meet the rounded edge.

## Components

### Buttons
Quiet, compact, one loud button per group.
- **Shape:** 8px radius, 38px tall (sm 30px, lg 46px), Inter 500 14px.
- **Primary:** Instrument Fill with its inverse ink (black on light, white on dark), a 1px inner top highlight; hover lifts 1px and shifts to fill-hover. Press scales to .97. Loading swaps the label for a spinner.
- **Secondary:** surface with a hairline-strong border; hover darkens the border and lifts 1px.
- **Quiet:** transparent, ink-secondary; hover takes the sunken background. **Link:** the quiet button in indigo, usually ending in "›".
- **Focus:** 2px indigo outline, 2px offset, everywhere.

### Chips (segmented filters)
- **Style:** text buttons without a border, 30px, Inter 500 13.5px, ink-secondary, each followed by a mono 11px micro-counter in ink-tertiary.
- **State:** hover takes sunken; pressed (`aria-pressed="true"`) takes surface, a hairline-strong border and the rest hint, like a selected segment. Rows of chips sit after a mono uppercase row label. Small chips (22px, mono) are read-only tags.

### Status Badges
22px, 6px radius, hairline border over a 92% surface with a 6px blur, Inter 500 11.5px, led by a 6px solid dot with a 3px soft ring in the status color (emerald for lapsed and expired, amber for likely abandoned, violet for reserved).

### Cards / Containers
- **Corner Style:** 12px.
- **Background:** surface; the drawing area sits on plate.
- **Shadow Strategy:** flat at rest, Lift on hover (see Elevation).
- **Border:** hairline; hover brightens it toward ink.
- **Internal Padding:** body 14px 16px 12px; the meta row below is three hair-divided cells (mono uppercase 10px labels over Inter 500 values: Build or Filed, Lapsed or Term ended, Owner).
- **Drawing:** a blueprint frame (see Signature) at 4:3, the status badge top-left and a sheet count bottom-right; the image scales 1.05 on hover.
- **Lead card:** the same card split horizontally, title at section size, plus a "Modern angle" note (mono indigo label over surface-raised).

### Inputs / Fields
- **Style:** surface, hairline-strong border, 8px radius, 40px tall (42px in the filter search). Inside the filter panel inputs sit on canvas.
- **Focus:** border turns indigo with a 3px indigo-wash halo; no outline.
- **Hero search:** a command palette: 12px radius, search icon, mono ⌘K keys, the primary Search button inside the right edge, faint glow beneath; focus adds a 4px indigo-wash ring.

### Navigation
Sticky 56px header on a 78% canvas with a 16px blur and a hairline bottom. Brand mark is a 28px fill tile that tilts on hover. Nav links are Inter 500 13.5px in ink-tertiary, 6px radius; hover and current page take sunken with ink. A compact search with a "/" key and an icon theme toggle sit right. Under 1080px the nav collapses into a full-width drawer of 17px rows divided by hairlines; the current page turns indigo.

### Metric Blocks
One bordered surface container split into hair-divided cells: a small mono tag (with an emerald dot, or emerald text for a counted weekly delta), the figure in Data type, and an Inter 13px caption. Figures carry a vertical ink gradient (ink at 30% to ink at 55%) clipped to the text, and strike into place digit by digit when they enter view. Cells are links; hover takes sunken.

### View Toggle
A 2px-padded segmented control (hairline border, surface) with two 30 x 26px icon buttons, cards and rows; the pressed one takes sunken and ink. It sits at the right of the count bar, opposite the mono result count.

### Blueprint Frame (signature)
Every patent drawing (home plotter, cards, patent page figure, gallery, opportunity cards, prompt card) sits on plate with a 1px grid-line lattice every 20px, under a 30px window bar: three 7px dots on the left, a mono 10px uppercase FIG tag on the right ("FIG. 1", "FIG. 1 · US 6,530,510 B2", "No drawing"), the bar at 86% surface with a hairline bottom. In dark the drawing is inverted and screened onto the plate; the "original drawings" setting restores white paper. On the home page the drawing is redrawn cell by cell like a pen plotter, with a magnifier loupe on hover (hidden under 700px).

### Number Plate (no drawing on file)
When a patent has no drawing, the blueprint frame stays and carries the patent's field glyph (a 30px 1.2-stroke line icon from the `#f-<field>` sprite, ink-tertiary, indigo and 1.08 scale on card hover) above its number in mono 15-18px. The FIG tag reads "No drawing" (archive cards: "US · no drawing").

## Do's and Don'ts

### Do:
- **Do** set every patent number, code, count and date in JetBrains Mono with tabular figures, and every name and sentence in Inter.
- **Do** put every patent drawing in the blueprint frame: window bar with three dots, FIG tag, 20px grid on plate.
- **Do** use a single primary (filled) button per action group; everything else is secondary, quiet or link.
- **Do** separate cells inside a container with hair lines (6-7%), not gaps or nested boxes.
- **Do** show filter options as segmented chips with mono micro-counters of real counts, grouped under mono row labels.
- **Do** offer the card/table toggle on every result grid and remember the choice.
- **Do** keep the eyebrow "PATENT YARD // SECTION" above page headings on section pages; it is a recorded exception requested in the user's brief, limited to that one form.
- **Do** honor reduced motion from both the OS and the site setting: no strike, no reveal, no plotting, no lift.

### Don't:
- **Don't** set names, titles, owners or sentences in mono.
- **Don't** invent trends, deltas, activity or "live" claims; a tag like "+N this week" appears only when counted from the catalog.
- **Don't** invent or generate an image for a patent without a drawing; use its field glyph and number plate.
- **Don't** fill buttons with indigo or status colors; the filled button is white in dark and black in light.
- **Don't** use status colors decoratively, or raise the indigo glow above its faint ambient level.
- **Don't** extend the gradient-filled figures beyond the metric blocks; they are a recorded exception from the user's brief, not a text treatment for headings or other numbers.
- **Don't** center headings on working pages; only the home hero is centered.
