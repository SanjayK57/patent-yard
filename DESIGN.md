---
name: Patent Yard
description: A free register of patents whose protection has ended, laid out as a light table, where the original drawing lies on lit glass and everything Patent Yard adds is drawn on vellum over it.
colors:
  table: "#F3F3F1"
  glass: "#FDFDFC"
  surface: "#FFFFFF"
  surface-2: "#F8F8F6"
  sunken: "#E9E9E6"
  band: "#ECECE9"
  plate: "#FFFFFF"
  vellum: "rgba(253,253,252,.76)"
  vellum-solid: "#FAFAF8"
  line: "#DCDCD8"
  line-strong: "#C3C3BE"
  hair: "rgba(23,25,26,.08)"
  ink: "#17191A"
  ink-2: "#45494C"
  ink-3: "#62676B"
  graphite: "#17191A"
  graphite-hover: "#33373A"
  graphite-ink: "#FFFFFF"
  vermilion: "#C23B27"
  vermilion-soft: "#FBEAE6"
  expired: "#1C6B3E"
  expired-soft: "#E1F0E6"
  lapsed: "#8A5100"
  lapsed-soft: "#F7ECDA"
  abandoned: "#5A6065"
  abandoned-soft: "#E7E8E8"
  reserved: "#6A47A2"
  reserved-soft: "#EEE8F8"
  danger: "#B32A1F"
  table-dark: "#121314"
  glass-dark: "#1A1B1D"
  surface-dark: "#1C1D1F"
  lit-glass-dark: "#CFCEC9"
  plate-dark: "#D9D8D3"
  vellum-dark: "rgba(38,39,42,.74)"
  line-dark: "#2C2E31"
  ink-dark: "#EDEDEB"
  ink-2-dark: "#BBBDBF"
  ink-3-dark: "#979A9D"
  vermilion-dark: "#FF7D66"
  expired-dark: "#74C893"
  lapsed-dark: "#EAB566"
  abandoned-dark: "#A4A9AD"
  reserved-dark: "#BFA3F1"
  danger-dark: "#FF8A7A"
typography:
  display:
    fontFamily: "Archivo, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif"
    fontSize: "clamp(44px, 5.4vw, 82px)"
    fontWeight: 640
    lineHeight: 0.95
    letterSpacing: "-0.04em"
    fontVariation: "\"wdth\" 118"
  numeral:
    fontFamily: "Archivo, sans-serif"
    fontSize: "clamp(48px, 5.6vw, 88px)"
    fontWeight: 560
    lineHeight: 1
    letterSpacing: "-0.05em"
    fontFeature: "\"tnum\" 1"
    fontVariation: "\"wdth\" 118"
  headline:
    fontFamily: "Archivo, sans-serif"
    fontSize: "46px"
    fontWeight: 620
    lineHeight: 1.02
    letterSpacing: "-0.035em"
    fontVariation: "\"wdth\" 108"
  section:
    fontFamily: "Archivo, sans-serif"
    fontSize: "32px"
    fontWeight: 620
    lineHeight: 1.08
    letterSpacing: "-0.03em"
    fontVariation: "\"wdth\" 108"
  title:
    fontFamily: "Archivo, sans-serif"
    fontSize: "20px"
    fontWeight: 620
    lineHeight: 1.16
    letterSpacing: "-0.015em"
  card-title:
    fontFamily: "Archivo, sans-serif"
    fontSize: "17px"
    fontWeight: 620
    lineHeight: 1.26
    letterSpacing: "-0.016em"
  lead:
    fontFamily: "Archivo, sans-serif"
    fontSize: "19px"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "-0.01em"
  body:
    fontFamily: "Archivo, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.55
  ui:
    fontFamily: "Archivo, sans-serif"
    fontSize: "14px"
    fontWeight: 580
    lineHeight: 1
    letterSpacing: "-0.005em"
  label:
    fontFamily: "Archivo, sans-serif"
    fontSize: "12.5px"
    fontWeight: 600
    lineHeight: 1
  data:
    fontFamily: "Archivo, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.4
    letterSpacing: "0.005em"
    fontFeature: "\"tnum\" 1"
    fontVariation: "\"wdth\" 90"
  source:
    fontFamily: "Source Serif 4, Iowan Old Style, Charter, Georgia, serif"
    fontSize: "17px"
    fontWeight: 400
    lineHeight: 1.68
  prompt:
    fontFamily: "Source Serif 4, Iowan Old Style, Charter, Georgia, serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.65
rounded:
  xs: "4px"
  sm: "6px"
  base: "10px"
  md: "14px"
  lg: "20px"
  xl: "28px"
  pill: "999px"
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
  s11: "88px"
  s12: "128px"
  gap: "20px"
  gutter: "clamp(16px, 4vw, 48px)"
  page: "1240px"
  page-wide: "1400px"
  header: "56px"
components:
  button-primary:
    backgroundColor: "{colors.graphite}"
    textColor: "{colors.graphite-ink}"
    typography: "{typography.ui}"
    rounded: "{rounded.pill}"
    padding: "0 16px"
    height: "38px"
  button-primary-hover:
    backgroundColor: "{colors.graphite-hover}"
    textColor: "{colors.graphite-ink}"
  button-primary-lg:
    backgroundColor: "{colors.graphite}"
    textColor: "{colors.graphite-ink}"
    rounded: "{rounded.pill}"
    padding: "0 24px"
    height: "50px"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.ui}"
    rounded: "{rounded.pill}"
    padding: "0 16px"
    height: "38px"
  button-quiet:
    backgroundColor: "transparent"
    textColor: "{colors.ink-2}"
    rounded: "{rounded.pill}"
    padding: "0 12px"
    height: "38px"
  chip:
    backgroundColor: "transparent"
    textColor: "{colors.ink-2}"
    rounded: "{rounded.pill}"
    padding: "0 13px"
    height: "32px"
  chip-on:
    backgroundColor: "{colors.graphite}"
    textColor: "{colors.graphite-ink}"
    rounded: "{rounded.pill}"
    padding: "0 13px"
    height: "32px"
  segmented-thumb:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.pill}"
    padding: "0 14px"
    height: "30px"
  field:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.base}"
    padding: "9px 14px"
    height: "42px"
  search-pill:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.pill}"
    padding: "0 7px 0 22px"
    height: "62px"
  badge-expired:
    backgroundColor: "{colors.expired-soft}"
    textColor: "{colors.expired}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "0 10px 0 9px"
    height: "24px"
  badge-lapsed:
    backgroundColor: "{colors.lapsed-soft}"
    textColor: "{colors.lapsed}"
    rounded: "{rounded.pill}"
    padding: "0 10px 0 9px"
    height: "24px"
  badge-abandoned:
    backgroundColor: "{colors.abandoned-soft}"
    textColor: "{colors.abandoned}"
    rounded: "{rounded.pill}"
    padding: "0 10px 0 9px"
    height: "24px"
  badge-reserved:
    backgroundColor: "{colors.reserved-soft}"
    textColor: "{colors.reserved}"
    rounded: "{rounded.pill}"
    padding: "0 10px 0 9px"
    height: "24px"
  card-sheet:
    backgroundColor: "{colors.plate}"
    rounded: "{rounded.lg}"
    padding: "26px 22px"
  glass-panel:
    backgroundColor: "{colors.glass}"
    rounded: "{rounded.xl}"
    padding: "48px"
  vellum-note:
    backgroundColor: "{colors.vellum}"
    textColor: "{colors.ink}"
    rounded: "{rounded.lg}"
    padding: "20px 24px"
  panel:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.lg}"
    padding: "20px 24px"
  intent-card:
    backgroundColor: "{colors.glass}"
    textColor: "{colors.ink}"
    rounded: "{rounded.xl}"
    padding: "24px 32px"
  task:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "12px 16px"
  prompt-document:
    backgroundColor: "{colors.plate}"
    textColor: "{colors.ink}"
    typography: "{typography.prompt}"
    rounded: "{rounded.lg}"
    padding: "24px 32px"
  toast:
    backgroundColor: "{colors.graphite}"
    textColor: "{colors.graphite-ink}"
    rounded: "{rounded.pill}"
    padding: "11px 18px 11px 12px"
---

# Design System: Patent Yard

## Overview

**Creative North Star: "The Light Table"**

An old invention lies on lit glass as the original sheet, and everything Patent Yard adds is drawn on frosted vellum laid over it. The page itself is the table: a neutral near-white (charcoal at night) on which glass panels, sheets and notes are placed, not boxed. The original drawing is the content and the brightest thing in view; the interface is graphite and recedes around it. A single vermilion mark appears only on the one thing that is live right now.

One world serves two densities. The home page is composed and expressive: split compositions, an expanded display face, a real drawing plotted by a pen onto glass that bleeds off the window edge, numbers struck into place. The research application (Free to use, All patents, Studio, saved, settings, account) is dense and operational, like desktop software: compact titles instead of heroes, a filter sidebar, three result views, ruled lists. Reading pages (a patent, Opportunities, Insights, How it works, legal) sit between the two, with the patent's own words in a serif.

This world replaces v2 entirely: no blue accent, no cool tinted surfaces, no centered headline over a search over a boxed drawing, no equal grids of identical cards as the only layout.

**Key Characteristics:**
- Materials, not boxes: table, lit glass, sheet and vellum, each with its own surface and shadow.
- Registration ticks at a sheet's corners in place of a border.
- Graphite does all the work: pill buttons, filled chips, the 1.5px ink focus ring on fields.
- One vermilion mark, reserved for the live thing.
- Archivo in three widths for Patent Yard's voice; Source Serif 4 only for the patent's own words and the Studio prompt.
- Statuses always carry their word; color is never the only signal.
- Motion that settles: one long ease-out, a spring for presses, sheets laying down out of a slight blur.

## Colors

A warm-neutral grey palette with graphite ink, carrying exactly one chromatic accent and four status hues that never appear without their word.

### Primary
- **Graphite** (`{colors.graphite}`): every action. Primary pill buttons, chips and list rows that are on, the segmented thumb's text, the avatar, toasts, the saved mark. It is the same value as the ink, so an action reads as ink pressed into the table rather than as a brand color. In dark mode graphite inverts to the light ink (`{colors.ink-dark}`) with charcoal text.
- **Vermilion Mark** (`{colors.vermilion}`; `{colors.vermilion-dark}` in dark): the live thing in view and nothing else. Keyboard focus outlines, the pen tip plotting the drawing, the loupe's crosshair ring, the current step in the Studio stage bar, the selected Studio intent card and task (an 8px dot), the current section in the patent page's contents rail (a 2px bar), the reading progress bar, the text caret, the selection tint (a 20% mix), the targeted claim (`{colors.vermilion-soft}`), the selected command's icon in the palette.

### Neutral
- **The Table** (`{colors.table}`; `{colors.table-dark}`): the page background. Content sits directly on it unless it needs grouping.
- **Lit Glass** (`{colors.glass}`; `{colors.glass-dark}`, or `{colors.lit-glass-dark}` where it holds an original): the large panel an original lies on, with a radial inner glow and a long low shadow.
- **Sheet** (`{colors.plate}`; `{colors.plate-dark}`): the paper of a drawing. White in light; a warm paper grey in dark, so a drawing still reads as paper.
- **Vellum** (`{colors.vellum}`, solid fallback `{colors.vellum-solid}`; `{colors.vellum-dark}`): translucent frosted film for Patent Yard's own notes over an original.
- **Surface, Surface 2, Sunken, Band** (`{colors.surface}`, `{colors.surface-2}`, `{colors.sunken}`, `{colors.band}`): fields and grouped panels; soft panels and row hover; recessed tracks, small chips and skeletons; the footer and full-bleed bands.
- **Line, Line Strong, Hair** (`{colors.line}`, `{colors.line-strong}`, `{colors.hair}`): rules between rows, field strokes, the hairline edge of a sheet.
- **Ink, Ink 2, Ink 3** (`{colors.ink}`, `{colors.ink-2}`, `{colors.ink-3}`): headings and values; body and secondary text; labels, captions and metadata.

### Status
- **Expired, full term** (`{colors.expired}` on `{colors.expired-soft}`): also the free and success color.
- **Lapsed, fee not paid** (`{colors.lapsed}` on `{colors.lapsed-soft}`): also warnings.
- **Likely abandoned** (`{colors.abandoned}` on `{colors.abandoned-soft}`): drawn with a hollow dot because it is inferred.
- **Reserved** (`{colors.reserved}` on `{colors.reserved-soft}`).
- **Danger** (`{colors.danger}`): invalid fields and a patent pulled from the register.

### Named Rules
**The One Mark Rule.** Vermilion marks only the single live thing in view: focus, the pen, the current step, the current section, the selected task. If two things on a screen are vermilion at once and are not both live, one of them is wrong. Actions are graphite, never vermilion.

**The Word With Every Color Rule.** A status color always travels with its word ("Lapsed, fee not paid"), with a dot, on its own tint. Links in running text are underlined, never told apart by color alone.

**The Lit Glass Rule.** In dark mode the table goes charcoal but glass that holds an original stays lit: a panel holding a drawing (the home stage, the patent's first sheet, card sheets, Opportunities figures, the archive front page, the Studio intro, gallery sheets, the prompt document, thumbnails) re-scopes ink, lines and vellum to their light values, so what is written on the glass stays readable. Drawings are inverted only when the visitor chooses inverted drawings in Settings.

## Typography

**Display Font:** Archivo (variable, width 88 to 120%, weight 400 to 700, self-hosted), with the system sans as fallback
**Body Font:** Archivo
**Reading Font:** Source Serif 4 (400 to 600, roman and italic), with Iowan Old Style, Charter and Georgia
**Mono:** the system monospace, only for raw identifiers in code

**Character:** one grotesque family speaking at three widths, so Patent Yard's voice changes register without changing family: expanded and tight for announcements, normal for the interface, narrow and tabular for numbers. The serif belongs to the patent, so the invention's own words are always visibly someone else's.

### Hierarchy
- **Display** (640, clamp(44px, 5.4vw, 82px), 0.95, width 118%, -0.04em): the home hero, two lines with the second in ink-3. Reading-page titles use the same width at clamp(40px, 5.2vw, 76px); the Studio intro and the sign-in pitch run up to 56 and 60px.
- **Numeral** (560, clamp(48px, 5.6vw, 88px), 1, width 118%, -0.05em, tabular): the yard's counted numbers; Insights key figures at 28 to 44px; the Opportunities rank.
- **Headline** (620, 46px, 34px under 700px, 1.02, width 108%, -0.035em): application page titles. The patent masthead runs clamp(34px, 4.6vw, 64px) at 640, at most 22ch, and drops to clamp(28px, 3.2vw, 42px) for long titles.
- **Section** (620, 32px, 26px under 700px, 1.08, width 108%, -0.03em): section heads; patent sections at clamp(26px, 2.6vw, 34px).
- **Title** (620, 20px, 1.16, -0.015em): h3 and group titles; dialog titles at 17px, width 108%.
- **Card title** (620, 17px, 1.26): card and row titles; 18px at width 108% in the list view, 14.5px at 560 in the table view; breaks inside very long words.
- **Lead and Body** (400, 19px/1.5 and 16px/1.55): ledes and running text; Patent Yard's own reading pages at 16px/1.68.
- **UI** (500 to 580, 14px): buttons, navigation, toolbars; chips and segments at 13.5px and 520, 600 when on.
- **Label** (600, 12.5px): status labels, field labels (13.5px), group labels in ink-3. Sentence case, no added tracking.
- **Data** (400 to 560, 12 to 13px, width 90%, tabular figures): patent numbers, dates, the sheet margin label, list-view facts, the whole table view, gallery captions, the viewer bar.
- **Source** (Source Serif 4, 400, 17px, 1.68 to 1.75): the abstract, background, claims and description; the home close-up's abstract at 20px; the Studio prompt at 16px/1.65 and the Studio brief on the home page at 19px.

### Named Rules
**The Three Widths Rule.** Width carries register: 118% for display and big numbers, 108% for headings, 100% for the interface, 90% for identifiers and dense data. Weight stays between 520 and 660; hierarchy comes from width and size, not from heavy weights.

**The Patent's Own Words Rule.** Source Serif 4 is used only for text the patent itself says and for the Studio prompt document. Patent Yard never sets its own copy in the serif.

## Layout

Content sits in a centered 1240px column (1400px for the header and footer) inside a fluid body gutter of clamp(16px, 4vw, 48px). Spacing runs on 4px steps from 4 to 128px, with a 20px grid gap. Sections are 128px apart (88px under 700px); bands and the footer span the whole window.

**Bleeding glass.** Hero and feature glass bleeds off one edge of the window: its block-level parent takes `margin-right` (or `margin-left`) of `calc(50% - 50vw)`, and the glass squares its two outer corners. This is used on block-level parents only (the home hero, the close-up feature, the Studio intro, the band backdrop), never on inline or flex children, and is removed under 980px (860px for the close-up), where the glass returns to fully rounded inside the gutter.

**Home: split compositions.** The hero is 5:7: copy and search on the table at left; at right the lit glass with the plotted sheet, its corner ticks, a vertical sheet margin label (12px, width 90%, set with `writing-mode: vertical-rl`) beside the sheet, and the vellum record card overlapping the sheet's lower left. Later sections alternate: the close-up (glass bleeding left), the yard's three numbers over a ruled four-office ledger, today's sheets as one face-out on glass beside rows (7:5) over a ruled list, a field index with dotted leaders in three columns, three steps ruled in ink with a real piece of interface each, and the Studio brief on vellum over a patent (5:7, glass bleeding right).

**Application pages: denser.** A compact title, then the working layout. Free to use and All patents put a 272px sticky filter sidebar beside the search pill and results; on wide screens the sidebar folds away and the results take the full width; under 900px it becomes a sheet from the bottom. Patent pages put a 196px sticky contents rail beside the sections; under 980px the rail becomes a horizontal, frosted, sticky strip. Studio is a 1 : 1.15 split with the output sticky.

**Rules over boxes.** Groups open with a 1.5px ink rule (the yard's numbers, the field index, the steps, the filter head, the Opportunities method and ranked lists, reading-page heads, the patent masthead) and rows are separated by 1px line rules.

Breakpoints in use: 1180px (the header search becomes the command button; the loupe hides), 1080px (navigation becomes a sheet), 980px (the hero, the patent rail and the list view collapse), 900px (filter sheet, single-column features), 860px, 760px, 720px (dialogs go full-screen), 700px (heading sizes drop), 560px (card status moves above the field and number), 520px (phone).

## Elevation & Depth

Depth is material. The table is flat; glass lies on it with a long, low shadow; a sheet lies on glass with a short one; vellum floats with a tight lift and a backdrop blur. Shadows are neutral, offset downward, drawn from ink at low alpha in light mode and from black in dark mode. Edges are 1px box-shadow rings, not CSS borders, so they never shift layout.

### Shadow Vocabulary
- **Rest** (`box-shadow: 0 1px 2px rgba(23,25,26,.06), 0 1px 1px rgba(23,25,26,.03)`): primary buttons, segmented thumbs, card sheets at rest.
- **Raised** (`box-shadow: 0 1px 2px rgba(23,25,26,.05), 0 10px 24px -10px rgba(23,25,26,.16)`): list-view hover, the selected task, link cards on hover.
- **Lifted** (`box-shadow: 0 2px 6px rgba(23,25,26,.06), 0 28px 60px -20px rgba(23,25,26,.26)`): card sheets on hover, dialogs, menus, toasts.
- **Glass** (`box-shadow: 0 0 0 1px var(--line), inset 0 0 0 1px rgba(255,255,255,.9), 0 50px 90px -50px rgba(23,25,26,.28)`): every lit-glass panel.
- **Vellum** (`box-shadow: 0 0 0 1px rgba(23,25,26,.09), 0 22px 44px -22px rgba(23,25,26,.32)`): vellum notes and the save button over a drawing.
- **Sheet** (`box-shadow: 0 1px 2px rgba(23,25,26,.06), 0 18px 40px -20px rgba(23,25,26,.22)`): the plotted sheet on the home glass.

### Named Rules
**The Materials Rule.** Every surface is one of four materials: the table, lit glass (28px corners, a radial glow at 50% 45%, the glass shadow), a sheet (the plate color with a hairline edge), or vellum (translucent, `saturate(1.3) blur(18px)` behind it, the vellum shadow, 20px corners, a solid fallback where backdrop-filter is missing). Original drawings go on sheets on glass; Patent Yard's own notes (the record card, the modern angle, the archive hint, the explain note, the Patent Yard note on a patent, the Studio brief) go on vellum. Plain grouped panels are surface with a 1px ring.

**The Ticks Not Boxes Rule.** A sheet on glass is framed by four registration ticks (14px by 1px corner marks in ink at 50% opacity, 18px outside the sheet), never by a border or a box. A blank sheet with no drawing on file gets the same ticks in ink-3, inset.

## Shapes

Rounded but not soft. Controls are full pills (999px): buttons, chips, segmented tracks and thumbs, the search fields, status labels, toasts. Containers step up with size: fields 10px; small cards, claims and the task tiles 14px; card sheets, panels and vellum notes 20px; glass, dialogs, intent cards and grouped lists 28px. Glass that bleeds off the window squares its two outer corners. Thumbnails take 10px, viewer sheets 6px. Circles are kept for icon buttons, the avatar, the save button, the stage numerals and the loupe. Lines are 1px for rules and rings and 1.5px for ink rules, the focus ring and the selected outline; icons are line icons at a 1.6px stroke.

## Components

### Buttons
Graphite pills, pressed like keys.
- **Shape:** full pill (999px), 38px tall (32px small, 50px large).
- **Primary:** graphite with white text, 0 16px, 14px at 580, the rest shadow; hover lightens to graphite-hover.
- **Secondary:** surface with a 1px line-strong ring; hover darkens the ring toward ink.
- **Quiet and Link:** transparent in ink-2 with a 7% ink wash on hover; link buttons underline at 35% and go solid on hover.
- **Press:** scale(.97) on the spring; disabled at 40% opacity; loading swaps the label for a 15px spinner.
- **Icon buttons:** 36px circles in ink-2, a 7% ink wash on hover, scale(.92) on press.

### Chips
- **Style:** transparent text pills, 32px tall, a 1px line ring, 13.5px at 520, counts in ink-3 tabular figures.
- **State:** on fills graphite with white text at 600, like a key held down; hover raises to surface with a line-strong ring. Small static chips (24px) sit on sunken with no ring. In the filter sidebar's field list, chips become full-width rows with the count at the right.

### Segmented Controls
A recessed pill track (7% ink) with 3px padding; the chosen option is a raised thumb (surface in light, a charcoal thumb in dark) with the rest shadow, a 0.5px line ring and 600 weight. The result view switch (list, cards, table) is the same control with 36px icon segments. On sign-in the thumb slides between options.

### Inputs / Fields
- **Style:** surface, 42px tall, 10px corners (14px for textareas), an inset 1px line-strong ring, 15px text, a vermilion caret.
- **Hover:** the ring darkens to 40% ink.
- **Focus:** an inset 1.5px ink ring plus a 4px halo of 9% ink; no outline.
- **Error:** an inset 1.5px danger ring.
- **Search pills:** the home search is a 62px pill (56px on phones) with a 48px graphite Search button inside and key hints that hide on focus; focus draws a 1.5px ink ring, a deeper shadow and a 1px lift. The browse search is a 52px pill with a drawn magnifier. The header search is a 34px tinted pill that widens from 230 to 320px on focus.

### Status Labels
24px pills, 12.5px at 600: the status word in its color with a 6px dot, on its soft tint. Abandoned (inferred) uses a hollow ring dot. In cards the label drops its tint and rides with the words above the title.

### Patent Results
One card markup, three views, remembered per page.
- **List** (the register's default): rows with a 168px sheet, the words, and a 248px facts column in the narrow cut, separated by line rules; a 140px sheet under 980px; a 96px sheet with no abstract and two facts under 560px.
- **Cards:** sheets laid on the table, auto-filling from 250px. The sheet (4:3, 20px corners, hairline edge) lifts 4px with the lifted shadow on hover and the drawing scales to 1.035; a vellum "n drawings" tag sits at its corner; the save button appears on hover as a vellum circle. The status sits beside the field and number above the title, and above them both under 560px.
- **Table:** one line each inside a surface panel with a line ring, all in the narrow cut, with title, field, status and facts in fixed columns.
- **Edge cases:** titles break inside very long words; skeletons shimmer on sunken; a sheet with no drawing shows the number between ticks.

### Filter Sidebar and Phone Sheet
A 272px sticky column: a head ruled in 1.5px ink, then groups with an ink-3 label over their chips or a vertical segmented list. On wide screens a Filters toggle folds it away, and the choice is remembered. Under 900px it becomes a bottom sheet with 28px top corners and a sticky full-width Done button, sliding up over 0.6s.

### Patent Masthead and Contents Rail
The masthead: status labels first, the title in the semi-wide headline, the "as filed" line with the number in the narrow cut, the actions as a pill row with the primary first, all closed by a 1.5px ink rule. The contents rail: a hairline left edge, section links in ink-3 with their counts, the current section in ink at 600 with a 2px vermilion bar that grows in on the ease. Under 980px it becomes a horizontal frosted strip with the bar underneath. The first sheet sits on glass with ticks; Patent Yard's note sits beside it on vellum; claims are in the serif, independent claims as surface cards, dependents indented under a 2px line.

### Opportunities Features and Rows
The method as a four-column statement ruled in ink. The first picks are editorial features: the drawing large on glass (440px minimum) with an expanded rank numeral at its corner, the words beside it, alternating sides. The rest form a two-column ranked list (narrow rank, thumbnail, title) and one-line notes that open in place; every factor behind a rank is one disclosure away.

### Studio
- **Intent cards:** two lit-glass cards (28px corners) with a line icon, a semi-wide title and a line of ink-3; hover lifts 2px; selected gets a 1.5px ink ring and an 8px vermilion dot.
- **Stage bar:** numbered 22px circles joined by hairlines; the current stage fills vermilion with white numerals; done stages show a green tick on the expired tint.
- **Task grid:** two columns of surface tiles with a 1px line ring, the first spanning both; selected gets a 1.5px ink ring, the raised shadow and the vermilion dot.
- **Prompt document:** a sheet with a docbar (name, size, copy) and the prompt in Source Serif 4 at 16px/1.65; focus rings the whole frame in 1.5px ink. It stays lit in dark mode.

### Navigation
A 56px sticky header in translucent table color with an 18px blur; a hairline appears once the page scrolls under it. The wordmark is expanded (118%) beside a mark that turns 90 degrees on hover. Links are 14px ink-2 pills; the current page is ink at 600 with a 4px graphite dot beneath. Under 1080px the links become a full-width sheet of 22px semi-wide rows. The footer is the table's far edge: a band with the wordmark large and four route columns, each under a plain 13px heading.

### Dialogs, Palette, Toasts, Viewer
Dialogs are surface with 28px corners and the lifted shadow, rising from 12px and 98% scale over a lightly blurred scrim; they go full-screen under 720px. The command palette (Cmd/Ctrl K) shares the frame. Toasts are graphite pills that arrive on the spring. The drawing viewer is a dark room in either theme: one sheet at a time laid down with sheetLay, the current thumbnail ringed in vermilion.

### Motion
- **Tokens:** `--ease` cubic-bezier(.16,1,.3,1) for everything that moves; `--ease-in-out` for the theme fade and pulses; `--spring`, a linear() overshoot, for presses and small arrivals; durations `--t1` .12s (color and hover), `--t2` .2s (state), `--t3` .36s (presses, arrivals, dialogs), `--t4` .6s (sheets, the theme fade, the filter sheet).
- **sheetLay and vellumIn:** a sheet settles from 14px below at 98.5% scale out of a 3px blur (the home sheet, the viewer); vellum rises 18px as its backdrop blur comes in (the home record card, after .55s).
- **The pen plotter:** on home, the day's real drawing is redrawn by a vermilion pen dot that follows its strokes, with faint ink crosshairs, in about 3 seconds paced by the clock; wet ink dries into the sheet over 220ms. On wide screens the loupe (a 200px round glass at 3x) follows the pointer over the sheet.
- **Card to patent:** a card's drawing flies into the patent page's drawing through the named view transition `pfig` over 0.6s; other page changes cross-fade, .16s out and .32s in.
- **Theme switch:** a slow whole-page cross-fade (0.6s, ease-in-out) through a view transition.
- **Reduced motion:** the system preference and the site setting each stop every animation and transition, view transitions included; the pen does not run (the still drawing shows) and charts are drawn at their final size.

## Do's and Don'ts

### Do:
- **Do** put every original drawing on a sheet on lit glass, framed by registration ticks, and every note Patent Yard writes about it on vellum.
- **Do** make actions graphite pills, and fill a chip with graphite when it is on.
- **Do** reserve vermilion for the single live thing: focus, the pen, the current step, the current contents section, the selected Studio intent or task.
- **Do** show every status with its word, its dot and its tint.
- **Do** set the patent's own words (abstract, background, claims, description) and the Studio prompt in Source Serif 4, and everything Patent Yard says in Archivo.
- **Do** choose Archivo's width by register: 118% for display and big numbers, 108% for headings, 100% for the interface, 90% with tabular figures for identifiers and dense data.
- **Do** keep glass that holds an original lit in dark mode, and invert drawings only when the visitor asks for it.
- **Do** bleed hero and feature glass off the window edge with calc(50% - 50vw) on a block-level parent, square its outer corners, and bring it back inside the gutter on narrow screens.
- **Do** give application pages a compact title and a dense working layout; keep split, expressive compositions for the home page.
- **Do** move only with the motion tokens, and stop all motion under either reduced-motion signal.

### Don't:
- **Don't** put a border or box around a sheet on glass; use the ticks.
- **Don't** use vermilion for buttons, links, decoration, numbering, or more than one thing at a time.
- **Don't** bring back v2's blue accent, cool tinted surfaces, the centered headline over a search over a boxed drawing, or grids of identical cards as the only layout.
- **Don't** let a status color stand without its word, or tell a link apart by color alone.
- **Don't** set Patent Yard's own copy in the serif, or the patent's words in Archivo.
- **Don't** put small uppercase tracked labels above headlines; labels are sentence case at normal tracking.
- **Don't** apply the full-bleed margin to inline or flex children, or let it cause horizontal scrolling.
- **Don't** invert drawings in dark mode by default.
