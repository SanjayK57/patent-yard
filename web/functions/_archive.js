// Archive patents (US patents past their full term, pipeline/register.py archive) have no pre-built page: their small
// record is read from shard/a and poured into the page shell /tpl/archive/ that the build writes. Millions of pages
// this way cost one small record each instead of a page each.
import SITE from "./site.json";

const E = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const icon = n => `<svg class="i" aria-hidden="true"><use href="#i-${n}"/></svg>`;
const EXT = 'target="_blank" rel="noopener noreferrer"';
const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
const full = s => { if (!s) return "—"; const [y, m, d] = s.split("-").map(Number); return `${MONTHS[m - 1]} ${d}, ${y}`; };
const fieldOf = r => [SITE.fieldKeys[r.ind] || "other", SITE.fields[SITE.fieldKeys[r.ind]] || "Other Inventions"];

// what kind of document an archive record is: "S" design patent, "A" published application, "" utility patent
const KIND = { S: ["Expired design patent", "expired"], A: ["Likely abandoned", "abandoned"], "": ["Expired, full term", "expired"] };

export function links(r) {
  const [, num, kind] = r.id.split("-"), app = r.k === "A";
  return {
    pdf: `https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/${num}`,
    ppubs: `https://ppubs.uspto.gov/pubwebapp/external.html?q=${num}.pn.&db=${app ? "US-PGPUB" : "USPAT"}`,
    center: r.app ? `https://patentcenter.uspto.gov/applications/${String(r.app).replace(/\D/g, "")}` : "https://patentcenter.uspto.gov/",
    google: `https://patents.google.com/patent/US${num}${kind}/en`, justia: `https://patents.justia.com/patent/${num}`,
    fpo: app ? `https://www.freepatentsonline.com/y${num.slice(0, 4)}/${num.slice(4)}.html` : `https://www.freepatentsonline.com/${num}.html`,
    espacenet: `https://worldwide.espacenet.com/patent/search?q=pn%3DUS${num}${kind}`,
  };
}

// The same reasoning as pipeline/register.py term_certainly_over
export function why(r) {
  if (r.k === "S") return [[`Granted ${full(r.p)}. A US design patent lasts 14 years from grant (15 if filed from May 13, 2015), so this one ended ${full(r.te)}.`],
    "A design patent protects only how a product looks. We check US rights only."];
  if (r.k === "A") return [[`Published ${full(r.p)}, and no patent has issued anywhere in its US family since.`, "Nothing has been filed in its family for more than seven years, so it is very unlikely to still be pending."],
    "This status is inferred from USPTO records. Confirm it on Patent Center before relying on it."];
  if (!r.f || r.p < "1976-01-01") return [[`Granted ${full(r.p)}. A patent granted before 1976 lasted at most 17 years from grant, so its term ended by ${full(r.te)}.`],
    "We check US rights only. Old patents can still inspire new ones: improvements may be patentable."];
  const checks = r.f >= "1995-06-08"
    ? [`Filed ${full(r.f)}. A US utility patent lasts 20 years from filing, so its term ended ${full(r.te)}.`,
       "Patents filed before May 29, 2000 can't get a term adjustment for USPTO delays, and any other extension is capped at five years, so it can't still be in force."]
    : [`Filed ${full(r.f)} and granted ${full(r.p)}. A patent filed before June 8, 1995 lasts 17 years from grant or 20 from filing, whichever is longer, so its term ended ${full(r.te)}.`,
       "Any extension is capped at five years, so it can't still be in force."];
  return [checks, "We haven't checked its US family, and a later related patent could still be in force. We check US rights only."];
}

export function kitOf(r) {
  const L = links(r), [checks, warn] = why(r);
  return { id: r.id, n: r.n, t: r.t, ot: r.t, h: "", tw: "", st: KIND[r.k || ""][1], status: KIND[r.k || ""][0], field: fieldOf(r)[1], filed: r.f, granted: r.p,
    expired: null, termEnd: r.te, abs: "", claims: [], figs: [], fieldText: "", bg: "", inventors: r.i || null, assignee: r.a || null, cpc: r.cpc || [],
    app: r.app, why: checks, warn, sheets: [], totalSheets: r.sh, url: `${SITE.site}/patents/${r.id}/`, pdf: L.pdf, google: L.google };
}

export function renderArchive(tpl, r) {
  const [fk, field] = fieldOf(r), L = links(r), [checks, warn] = why(r);
  const owner = (r.a ? ` · Assignee: ${E(r.a)}` : "") + (r.i ? ` · Inventors: ${E(r.i)}` : "");
  const lc = (x, cls = "") => `<a class="lcard ${cls}" href="${x[0]}" ${EXT}><b>${E(x[1])}${icon("ext")}</b><span>${E(x[2])}</span><small>${E(x[3])}</small></a>`;
  const official = [[L.pdf, "Full published document", "Text and every drawing sheet as a PDF.", "USPTO"],
    [L.center, "File history", "Status, office actions, notices, fee records and petitions.", "USPTO Patent Center"],
    [L.ppubs, "Patent Public Search record", "Searchable full text and bibliographic data.", "USPTO"]];
  const cross = [[L.google, "Google Patents", "Full text, worldwide family, citing patents and legal events.", "patents.google.com"],
    [L.justia, "Justia Patents", "Full text, claims and classification.", "patents.justia.com"], [L.fpo, "FreePatentsOnline", "Full text and PDF.", "freepatentsonline.com"],
    [L.espacenet, "Espacenet", "Foreign family and legal status.", "European Patent Office"]];
  const draw = r.sh
    ? `<div class="nofig later"><b>${r.sh} drawing ${r.sh === 1 ? "sheet" : "sheets"}</b><p class="muted">Every sheet is in the USPTO PDF.</p><a class="btn secondary sm" href="${L.pdf}" ${EXT}>${icon("file")}Open the USPTO PDF</a></div>`
    : `<div class="nofig"><b>This document has no drawings.</b><p class="muted">Claude can sketch it from the patent text.</p><button class="btn secondary sm" type="button" data-kit="sketch">${icon("spark")}Sketch it with Claude</button></div>`;
  const cpc = (r.cpc || []).length ? E(r.cpc[0]) + (r.cpc.length > 1 ? ` <span class="muted" title="${E(r.cpc.join(", "))}">+${r.cpc.length - 1} more</span>` : "") : "—";
  const body = `<div class="page" id="patent" data-id="${E(r.id)}" data-n="${E(r.n)}" data-sheets="0" data-total="${r.sh || 0}" data-pdf="${L.pdf}">
<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a><span>/</span><a href="/fields/${fk}/">${E(field)}</a><span>/</span><span>${E(r.n)}</span></nav>
<div class="phead">
  <div><div class="badges"><span class="badge ${KIND[r.k || ""][1]}">${KIND[r.k || ""][0]}</span><span class="badge plain">Archive</span>${r.a ? "" : '<span class="badge plain">Solo inventor</span>'}<span class="badge ok" id="vbadge" hidden></span></div>
  <h1>${E(r.t)}</h1><p class="asfiled">${E(r.n)}${owner}</p></div>
  <div class="pactions">
    <button class="btn primary" type="button" data-kit="workshop">${icon("spark")}Reinvent with Claude</button>
    <button class="btn secondary" type="button" id="reserveBtn">${icon("flag")}Reserve</button>
    <a class="btn secondary" href="${L.pdf}" ${EXT}>${icon("file")}USPTO PDF</a>
    <button class="btn quiet" type="button" id="saveBtn" aria-pressed="false">${icon("bookmark")}<span>Save</span></button>
    <button class="btn quiet" type="button" id="copyLink">${icon("link")}Copy link</button>
    <div class="resline" id="resline" aria-live="polite"></div>
  </div>
</div>
<div class="playout">
  <nav class="toc" aria-label="On this page"><a href="#overview">Overview</a><a href="#sources">Sources &amp; verification</a></nav>
  <div>
  <section class="psec" id="overview"><h2>Overview</h2>
  <div class="ov"><div>${draw}</div>
  <div class="stack">
    <div class="panel soft"><div class="block"><h3>Read the whole patent</h3><p class="prose">Listed from its USPTO record in Patent Yard's full-term archive. Its claims, description and drawings are in the <a href="${L.pdf}" ${EXT}>USPTO PDF</a> and on <a href="${L.google}" ${EXT}>Google Patents</a>, and the Claude kit works from them.</p>
      <div class="rowbtns" style="margin-top:12px"><a class="btn secondary sm" href="${L.google}" ${EXT}>Google Patents${icon("ext")}</a><a class="btn secondary sm" href="${L.pdf}" ${EXT}>${icon("file")}USPTO PDF</a></div></div></div>
    <div class="panel soft"><div class="block"><h3>Why it's free to use</h3><ul class="checks">${checks.map(c => `<li>${E(c)}</li>`).join("")}<li class="warn">${E(warn)}</li></ul></div></div>
    <div class="facts">
      <div><small>Filed</small><b>${E(full(r.f))}</b></div><div><small>${r.k === "A" ? "Published" : "Granted"}</small><b>${E(full(r.p))}</b></div><div><small>${r.k === "A" ? "Status" : "Term ended"}</small><b>${r.k === "A" ? "Abandoned (inferred)" : E(full(r.te))}</b></div>
      <div><small>Application number</small><b>${E(r.app || "—")}</b></div><div><small>Classification (CPC)</small><b>${cpc}</b></div><div><small>Length</small><b>${r.pg ? `${r.pg} pages` : "—"}</b></div>
    </div>
  </div></div></section>
  <section class="psec" id="sources"><h2>Sources &amp; verification</h2><div class="stack">
    <div class="cols2 links2"><div class="block"><h3>Official USPTO records</h3><div class="linklist">${official.map(x => lc(x)).join("")}</div></div>
    <div class="block"><h3>Cross-check elsewhere</h3><div class="linklist">${cross.map(x => lc(x)).join("")}</div></div></div>
    <p class="muted" style="font-size:13px">Everything on this page comes from the USPTO record linked above.</p>
    <div class="rowbtns noprint"><button class="btn secondary sm" type="button" id="reportBtn" hidden>Report a problem with this listing</button></div>
  </div></section>
  </div>
</div>
</div>
<dialog id="viewer" aria-label="Drawing viewer"></dialog>
<dialog id="kit" aria-labelledby="kitTitle"></dialog>
<dialog id="resDlg" aria-labelledby="resTitle"></dialog>
<dialog id="repDlg" aria-labelledby="repTitle"></dialog>`;
  // replacer functions, so a "$" in a title is never read as a replacement pattern
  return tpl.replaceAll("%%TITLE%%", () => E(`${r.t} (${r.n})`)).replaceAll("%%DESC%%", () => E(`${r.n}, ${KIND[r.k || ""][0].toLowerCase()}: ${r.t}`))
    .replaceAll("%%PATH%%", () => `/patents/${r.id}/`).replace("%%BODY%%", () => body);
}
