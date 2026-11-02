// The patent card, drawn from plain fields. pipeline/site_ui/components.py card_html() draws the same markup from the
// same fields, and web/dev/test_cards.mjs renders both from web/dev/fixtures/cards.json and fails if they differ.
// To change how cards look, edit web/styles/cards.css; to change their markup, edit both renderers and run the test.
//
//   id, href, title         the patent and its page
//   number                  "US 11,117,268 B2", shown with the field and on a blank sheet
//   field                   the line above the title ("Robotics & Automation", "Germany · Robotics & Automation")
//   status                  {cls, label}: the status label (cls: lapsed, expired, abandoned or plain)
//   img, alt                the drawing; "" draws a blank sheet with the field's symbol (glyph) and the number
//   glyph                   field key for the symbol (#f-<glyph>)
//   remote                  true for a drawing from Google Patents: it may fail, so the symbol waits behind it
//   sheets                  drawing sheets on file (0 shows no count)
//   eager                   load the drawing at once (the first row of a page)
//   summary, angle          optional sentences; angle shows on the lead card only
//   meta                    up to three [label, value, title] facts; a value {build: n, name} shows the build meter
//   archive, feat           card variants: archive and worldwide records; the home page's lead card

export const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#x27;" }[c]));
export const icon = name => `<svg class="i" aria-hidden="true"><use href="#i-${name}"/></svg>`;
export const meter = b => `<span class="meter" aria-hidden="true">${[1, 2, 3, 4, 5].map(i => `<i class="${i <= b ? "on" : ""}"></i>`).join("")}</span>`;
export const badge = s => `<span class="badge ${esc(s.cls)}">${esc(s.label)}</span>`;

export function card(c) {
  const b = badge(c.status);
  const symbol = `<svg class="fglyph" aria-hidden="true"><use href="#f-${esc(c.glyph)}"/></svg><span class="numart">${esc(c.number)}</span>`;
  const n = Math.max(0, Math.floor(+c.sheets || 0));
  const sheets = n ? `<span class="sheets">${icon("sheet")}${n} ${n === 1 ? "drawing" : "drawings"}</span>` : "";
  const fig = c.img
    ? `<div class="fig${c.remote ? " gfig" : ""}"><img src="${esc(c.img)}" alt="${esc(c.alt || "Drawing from " + c.number)}" loading="${c.eager ? "eager" : "lazy"}" decoding="async"${c.remote ? ' referrerpolicy="no-referrer"' : ""}>`
      + `<span class="over">${b}</span>${sheets}${c.remote ? symbol : ""}</div>`
    : `<div class="fig plate"><span class="over">${b}</span>${symbol}</div>`;
  const body = `<div class="cbody"><span class="fieldname">${esc(c.field)} · <span class="num-id">${esc(c.number)}</span></span>`
    + `<h3><a href="${esc(c.href)}">${esc(c.title)}</a></h3>${c.summary ? `<p>${esc(c.summary)}</p>` : ""}`
    + `${c.feat && c.angle ? `<div class="angle"><b>Modern angle</b>${esc(c.angle)}</div>` : ""}<span class="tstat">${b}</span></div>`;
  const meta = c.meta?.length ? `<div class="cmeta">${c.meta.map(([label, v, title]) => `<div><small>${esc(label)}</small><span${title ? ` title="${esc(title)}"` : ""}>`
    + `${v && typeof v === "object" ? meter(v.build) + esc(v.name) : esc(v)}</span></div>`).join("")}</div>` : "";
  const cls = `card${c.archive ? " acard" : ""}${c.feat ? " feat" : ""}`;
  return `<article class="${cls}" data-id="${esc(c.id)}">${c.feat ? `${fig}<div class="side">${body}${meta}</div>` : fig + body + meta}</article>`;
}
