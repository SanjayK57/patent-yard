---
name: Patent Yard
description: A free register of expired patents, presented as a quiet modern product site where the patent drawing is the product shot.
colors:
  action-blue: "#0A66D8"
  action-blue-hover: "#0758BD"
  action-blue-soft: "#E8F1FD"
  free-green: "#1E7B3C"
  free-green-soft: "#E6F4EA"
  abandoned-amber: "#8A5300"
  abandoned-amber-soft: "#FDF2DE"
  reserved-violet: "#5B46C9"
  reserved-violet-soft: "#EFECFB"
  alert-red: "#C4371F"
  alert-red-soft: "#FCEBE7"
  paper: "#FFFFFF"
  band-gray: "#F5F5F7"
  sunken-gray: "#EDEDF0"
  hairline: "#E3E3E8"
  hairline-strong: "#C9C9CF"
  ink: "#1D1D1F"
  ink-secondary: "#424245"
  ink-tertiary: "#6E6E73"
  dark-bg: "#000000"
  dark-tile: "#1C1C1E"
  dark-sunken: "#2C2C2E"
  dark-band: "#0F0F10"
  dark-hairline-strong: "#48484A"
  dark-ink: "#F5F5F7"
  dark-ink-secondary: "#D1D1D6"
  dark-ink-tertiary: "#98989D"
  dark-link-blue: "#4DA2FF"
  dark-fill-hover: "#1C74E4"
  dark-free-green: "#4CC774"
  dark-abandoned-amber: "#F2B544"
  dark-reserved-violet: "#A99BFF"
  dark-alert-red: "#FF7A63"
typography:
  display:
    fontFamily: "-apple-system, BlinkMacSystemFont, SF Pro Display, Inter, Helvetica Neue, Arial, sans-serif"
    fontSize: "clamp(44px, 7vw, 84px)"
    fontWeight: 600
    lineHeight: 1.04
    letterSpacing: "-0.025em"
  headline:
    fontFamily: "-apple-system, BlinkMacSystemFont, SF Pro Display, Inter, Helvetica Neue, Arial, sans-serif"
    fontSize: "clamp(36px, 5vw, 56px)"
    fontWeight: 600
    lineHeight: 1.07
    letterSpacing: "-0.022em"
  section:
    fontFamily: "-apple-system, BlinkMacSystemFont, SF Pro Display, Inter, Helvetica Neue, Arial, sans-serif"
    fontSize: "clamp(28px, 3.4vw, 40px)"
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: "-0.02em"
  title:
    fontFamily: "-apple-system, BlinkMacSystemFont, SF Pro Display, Inter, Helvetica Neue, Arial, sans-serif"
    fontSize: "19px"
    fontWeight: 600
    lineHeight: 1.22
    letterSpacing: "-0.022em"
  lede:
    fontFamily: "-apple-system, BlinkMacSystemFont, SF Pro Text, Inter, Helvetica Neue, Arial, sans-serif"
    fontSize: "clamp(19px, 1.9vw, 24px)"
    fontWeight: 400
    lineHeight: 1.38
    letterSpacing: "-0.016em"
  body:
    fontFamily: "-apple-system, BlinkMacSystemFont, SF Pro Text, Inter, Helvetica Neue, Arial, sans-serif"
    fontSize: "17px"
    fontWeight: 400
    lineHeight: 1.47
    letterSpacing: "-0.011em"
    fontFeature: "\"cv11\", \"ss01\""
  label:
    fontFamily: "-apple-system, BlinkMacSystemFont, SF Pro Text, Inter, Helvetica Neue, Arial, sans-serif"
    fontSize: "13px"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "0"
  mono:
    fontFamily: "ui-monospace, SF Mono, Menlo, Consolas, monospace"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.6
rounded:
  sm: "12px"
  md: "18px"
  card-lg: "24px"
  plate: "28px"
  pill: "980px"
spacing:
  gap: "20px"
  page-inline: "20px"
  page-inline-wide: "40px"
  section: "96px"
  band-block: "64px 72px"
  container: "1180px"
components:
  button-primary:
    backgroundColor: "{colors.action-blue}"
    textColor: "{colors.paper}"
    rounded: "{rounded.pill}"
    padding: "8px 18px"
    height: "38px"
  button-primary-hover:
    backgroundColor: "{colors.action-blue-hover}"
  button-primary-lg:
    backgroundColor: "{colors.action-blue}"
    textColor: "{colors.paper}"
    rounded: "{rounded.pill}"
    padding: "12px 26px"
    height: "48px"
  button-secondary:
    backgroundColor: "transparent"
    textColor: "{colors.action-blue}"
    rounded: "{rounded.pill}"
    padding: "8px 18px"
    height: "38px"
  button-link:
    backgroundColor: "transparent"
    textColor: "{colors.action-blue}"
    padding: "8px 6px"
  chip:
    backgroundColor: "{colors.band-gray}"
    textColor: "{colors.ink}"
    rounded: "{rounded.pill}"
    padding: "0 14px"
    height: "32px"
  chip-pressed:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
  badge-free:
    backgroundColor: "{colors.free-green-soft}"
    textColor: "{colors.free-green}"
    rounded: "{rounded.pill}"
    padding: "0 10px"
    height: "24px"
  input-field:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sm}"
    padding: "10px 14px"
    height: "44px"
  search-pill:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.pill}"
    padding: "6px 6px 6px 20px"
    width: "640px"
  card:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
  tile:
    backgroundColor: "{colors.band-gray}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "24px"
  drawing-plate:
    backgroundColor: "{colors.paper}"
    rounded: "{rounded.plate}"
  brand-mark:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
    rounded: "8px"
    size: "28px"
---

# Design System: Patent Yard

## Overview

**Creative North Star: "The Drawing Is the Product Shot"**

Patent Yard is a modern product site in the Apple manner. White pages alternate with full-bleed light gray bands, headlines are large and semibold, controls are pills, and containers are softly rounded tiles. Everything recedes so the real USPTO line drawings can be shown big, the way a product site shows its hardware. The home page plots one patent drawing live inside a large rounded frame, with a round magnifier that follows the pointer.

Density is generous on persuasive surfaces (home, how it works) and tighter on working surfaces (browse filters, patent pages, account), but it stays one world: the same tokens, radii and pill controls everywhere, including the archive and worldwide patent pages served by the edge functions. Dark mode follows the system and goes to true black with #1C1C1E tiles; drawings are inverted and screen-blended so they read as white line art.

The user rejected an earlier standards-manual direction for this one. The confirmed refusals: no neon on black, no glows, no gradient text, no eyebrow labels, no icon-card grids.

**Key Characteristics:**
- White and #F5F5F7 bands; one blue for links and filled buttons; color otherwise reserved for status.
- System SF type, semibold, tightly tracked at large sizes.
- Pills for every control, 18px tiles, a 28px frame for the hero drawing.
- Real patent drawings, multiply-blended on white, inverted in dark mode.
- Thin translucent sticky header; flat surfaces, soft shadows only on lift and overlays.

## Colors

A near-monochrome Apple palette: white, cool grays and near-black ink, with a single blue as the action color and four muted status hues.

### Primary
- **Action Blue** (action-blue): links, filled pill buttons, focus rings, the selected command-palette row, chart bars and the reading-progress bar. Hover deepens to action-blue-hover. In dark mode, links lift to dark-link-blue while filled buttons keep action-blue so white labels stay legible.
- **Pale Blue Wash** (action-blue-soft): highlighted claims, the selected task tile, the archive hint strip and the source link card.

### Secondary
- **Free Green** (free-green, on free-green-soft): only for the "free to use" status (lapsed and expired badges), success ticks and success toasts.

### Tertiary
- **Abandoned Amber** (abandoned-amber, on its soft wash): abandoned status, warnings and reservation notes.
- **Reserved Violet** (reserved-violet, on its soft wash): reserved status and the reserved mark on cards.
- **Alert Red** (alert-red, on its soft wash): errors and the reinstated-patent notice. Never used for lapsed status.

### Neutral
- **Paper** (paper): page and card background; the plate behind every drawing.
- **Band Gray** (band-gray): full-bleed alternating section bands, tiles, chips, panels and the footer.
- **Sunken Gray** (sunken-gray): hover state for gray tiles and chips, empty chart tracks.
- **Hairlines** (hairline, hairline-strong): card borders and section dividers; the strong line for input strokes and dependent-claim rules.
- **Ink** (ink, ink-secondary, ink-tertiary): headlines and primary text; body prose; supporting and meta text.
- **Dark set** (dark-*): black page, #1C1C1E tiles and cards, #2C2C2E sunken and hairlines. Shadows other than the overlay shadow are removed in dark mode.

### Named Rules
**The One Blue Rule.** Blue is the only interactive color. Status hues never act as buttons, and blue never marks a status.

**The Green Means Free Rule.** Green appears only where a patent is free to use or an action succeeded.

## Typography

**Display Font:** SF Pro Display via the system stack (Inter, Helvetica Neue, Arial fallbacks)
**Body Font:** SF Pro Text via the system stack (same fallbacks)
**Label/Mono Font:** ui-monospace / SF Mono, only for the generated Claude prompt

**Character:** One family in two optical sizes, semibold for every heading, negative tracking that grows with size. Numbers use tabular figures wherever they align or count.

### Hierarchy
- **Display** (600, clamp(44px, 7vw, 84px), 1.04, -0.025em): the home hero headline only, max 13ch, centered.
- **Headline** (600, clamp(36px, 5vw, 56px), 1.07): page titles; patent titles use clamp(32px, 4.4vw, 50px) at max 22ch.
- **Section** (600, clamp(28px, 3.4vw, 40px), 1.1): section heads, paired with a tertiary-ink paragraph at max 62ch.
- **Title** (600, 16 to 24px, 1.2 to 1.3): card titles (19px, 17.5px in grids), tile and step titles.
- **Lede** (400, clamp(19px, 1.9vw, 24px), 1.38, tertiary ink): the subhead under the hero and page heads.
- **Body** (400, 17px, 1.47; long prose 16.5 to 17px at 1.6 to 1.7, max 76ch).
- **Label** (600, 12 to 13px, no tracking, sentence case): badges, block headings on patent pages, footer column labels.
- **Stat figures** (600, clamp(26px, 2.7vw, 38px), tabular): the statband numbers.

### Named Rules
**The Semibold Headline Rule.** Every heading is weight 600. Tracking runs from -0.011em at body size to -0.025em at display size and never tighter.

**The Sentence Case Rule.** Labels are sentence case at zero tracking. No uppercase tracked labels.

## Layout

A single centered column, max 1180px (820px for narrow reading pages), with 20px side padding, 40px from 900px up. Sections sit 96px apart; full-bleed gray bands extend to the viewport edges behind the column (64px top, 72px bottom padding) while content stays in the column. The grid gap is 20px everywhere.

Cards flow in auto-fill grids (min 250px), a horizontal snap rail on home (4 across, 3 below 1100px, 1.6 below 760px, 82% on phones), and a 1/2/3 column wall with a full-width featured card. Patent pages use a 190px sticky contents rail beside the reading column, collapsing to a horizontal scroller below 980px. Breakpoints observed: 520, 640, 700, 820, 900, 980, 1100, 1180px. Below 900px the header nav moves into a full-width dropdown; below 720px dialogs go full screen.

## Elevation & Depth

Flat by default. Depth comes from tone (white on gray, gray on white) and 1px hairlines. Shadows appear on the hero search pill, on cards when they lift, and on overlays (menus, suggestions, dialogs, toasts). Dark mode drops all shadows except the overlay shadow.

### Shadow Vocabulary
- **Soft lift** (`0 2px 6px rgba(0,0,0,.04), 0 12px 32px -12px rgba(0,0,0,.12)`): the hero search pill, the drawing frame, card hover.
- **Overlay** (`0 4px 12px rgba(0,0,0,.06), 0 30px 70px -20px rgba(0,0,0,.28)`): menus, suggestions, dialogs, toasts, the magnifier.
- **Hairline ring** (`0 0 0 1px` hairline): framing the drawing plate and big figures instead of a border.

### Named Rules
**The Lift on Intent Rule.** A surface gains a shadow only when it floats (overlays) or responds to the pointer (cards). Resting tiles are flat.

## Shapes

Continuous soft rounding. Controls are full pills (980px); tiles, cards, panels and filters 18px; inputs, small tiles and fees 12px; the auth card and prompt card 24px; the hero drawing frame 28px; dialogs 22px. Thumbnails inside rows use 10px. Avatars, step numbers, icon buttons, the magnifier and status dots are circles. Icons are 16 to 18px stroked SVG (1.7 stroke, round caps) from one sprite.

## Components

### Buttons
Quiet pills with one filled call to action per group.
- **Shape:** full pill (980px), 38px tall; small 30px; large 48px.
- **Primary:** action-blue fill, white 15px medium label; hover deepens; press scales to 0.97.
- **Secondary:** blue 1px outline and blue label; fills blue on hover.
- **Link / quiet:** blue text with a trailing "›" where it leads on; underlines on hover.
- **Loading:** label hidden, a 15px spinning ring centered.

### Chips
- **Style:** band-gray pill, 32px, ink 14px medium; hover goes to sunken gray. On gray filter panels chips flip to white.
- **State:** pressed chips invert to ink fill with page-color text. Field chips on home carry a tabular count in tertiary ink.

### Status badges
24px pills, 12px semibold, a 6px currentColor dot, status hue on its soft wash (free green, abandoned amber, reserved violet; plain and info badges drop the dot).

### Cards / Containers
- **Corner Style:** 18px.
- **Background:** white with a 1px hairline (borderless on gray bands); the drawing sits on a white plate at 4:3 with 18px inset.
- **Shadow Strategy:** lifts 3px with the soft-lift shadow on hover; the drawing scales to 1.04.
- **Internal Padding:** 16px 18px body, a three-column meta row below in 12 to 13px.
- **Featured card:** drawing and text side by side, 420px minimum height, a pale "Modern angle" note.
- **Tiles and panels:** band-gray fill, 18px radius, 24px padding, no border.

### Inputs / Fields
- **Style:** white, 1px strong hairline, 12px radius, 44px minimum height.
- **Focus:** blue border plus a 4px blue halo at 22% (the hero search pill uses 20%). Elsewhere a 3px focus outline at 55% blue.

### Navigation
A 52px sticky header at 80% page color with saturate-and-blur behind it and a 70% hairline. Brand at left: the house mark (two strokes) on a 28px ink square with 8px corners, then "Patent Yard" in 17px semibold. Center links are 13.5px secondary ink, current page in semibold ink. A gray pill search field with a "/" hint sits right (hidden below 1180px), then the theme toggle and account pill. The footer is a band-gray block with sentence-case column labels and 12.5px tertiary links.

### Drawing plotter (signature)
The home hero frame: a white plate with 28px corners and a hairline ring, 16:9 (square on phones, 660px max height). The patent drawing is plotted onto a canvas as if drawn by pen; on pointers wider than 900px a 220px circular magnifier at 3x follows the cursor with a 44px blue ring marking the spot.

### Motion
One easing curve, cubic-bezier(.25, 1, .5, 1). Hero elements rise 16px in sequence (80ms stagger, 0.9s). Sections ease up 28px as they scroll in. Cards lift on hover and enter grids with a 30ms stagger. Big numbers strike into place digit by digit, never tweened. Dialogs fade and rise with a dimmed backdrop; page navigations cross-fade. Everything collapses to static under reduced motion or the site's own motion setting.

## Do's and Don'ts

### Do:
- **Do** show the real patent drawing large, on a white plate, multiply-blended (inverted and screen-blended in dark mode).
- **Do** alternate white sections with full-bleed band-gray bands at 96px section spacing.
- **Do** keep exactly one filled blue pill per action group; pair it with a link-style "›" action.
- **Do** set every heading at weight 600 with tracking between -0.011em and -0.025em.
- **Do** use tabular figures for counts, dates, claim numbers and stats.
- **Do** keep green for "free to use" and success only.

### Don't:
- **Don't** use gradients on surfaces, buttons or text. Gradients appear only as functional fade masks on scrolling rows and in the loading shimmer.
- **Don't** use glows, neon on black, or colored shadows.
- **Don't** put eyebrow or kicker labels above headlines, and don't use uppercase tracked labels.
- **Don't** track headlines tighter than -0.025em or set them heavier than 600.
- **Don't** build icon-card grids; tiles carry drawings or text, not decorative icons.
- **Don't** put two filled buttons side by side.
