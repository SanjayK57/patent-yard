// Archive patents (US patents past their full term, pipeline/register.py archive, and other offices', REGIONS) have no pre-built page: their small
// record is read from shard/a and poured into the page shell /tpl/archive/ that the build writes. Millions of pages
// this way cost one small record each instead of a page each.
import SITE from "./site.json";
import { timelineSection } from "./_timeline.js";

// a page of a US patent on Google Patents' image store: "US-6046565-A", 1 -> .../pages/US6046565-1.png (page 0 is the front page)
export const gpage = (id, k) => `https://patentimages.storage.googleapis.com/pages/${id.split("-").slice(0, 2).join("")}${k === "" ? "" : `-${k}.png`}`;

const E = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const icon = n => `<svg class="i" aria-hidden="true"><use href="#i-${n}"/></svg>`;
const EXT = 'target="_blank" rel="noopener noreferrer"';
const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
const full = s => { if (!s) return "—"; const [y, m, d] = s.split("-").map(Number); return `${MONTHS[m - 1]} ${d}, ${y}`; };
const fieldOf = r => [SITE.fieldKeys[r.ind] || "other", SITE.fields[SITE.fieldKeys[r.ind]] || "Other Inventions"];

// what kind of document an archive record is: "S" design patent, "A" published application, "" utility patent,
// or a patent office outside the US (REGIONS)
const KIND = { S: ["Expired design patent", "expired"], A: ["Likely abandoned application", "abandoned"], "": ["Expired, full term", "expired"] };
const addYears = (s, y) => { const d = new Date(s + "T12:00:00Z"); d.setUTCMonth(d.getUTCMonth() + Math.round(y * 12)); return d.toISOString().slice(0, 10); };
const passed = (s, y) => addYears(s, y) < new Date().toISOString().slice(0, 10);
const GOOGLE = "Full text, worldwide family, citing patents and legal events.";

// Patents from other offices, by record kind: pipeline/europe.py (E) and pipeline/national.py (CA, AU). Each "why" follows
// the term rule its importer applied, so it only says what that rule made certain.
const REGIONS = {
  E: {
    name: "Europe", adj: "European", office: "EPO", party: "Applicant", ipc: "CPC", credit: "EPO data used under CC BY 4.0.",
    granted: r => /-B\d$/.test(r.id),
    links: (num, kind, r) => {
      const pdf = `https://data.epo.org/linked-data/representation/publication/EP/${num}/NW${kind}.pdf`, google = `https://patents.google.com/patent/EP${num}${kind}/en`;
      return { doc: pdf, embed: pdf, docLabel: "EPO PDF", docNote: "The claims, description and any drawings are in the published document.", google,
        official: [[pdf, "Full published document", "Claims, description and drawings as a PDF.", "EPO"],
          [`https://register.epo.org/application?number=EP${r.app}`, "European Patent Register", "Procedure, status, file inspection and legal events.", "EPO"],
          [`https://data.epo.org/linked-data/data/publication/EP/${num}/${kind}/-`, "Linked open EP data record", "The bibliographic record this page is built from.", "EPO"]],
        cross: [[google, "Google Patents", GOOGLE, "patents.google.com"],
          [`https://worldwide.espacenet.com/patent/search?q=pn%3DEP${num}${kind}`, "Espacenet", "National family members and their legal status.", "European Patent Office"]] };
    },
    why: (r, g) => [[g ? `Filed ${full(r.f)}${r.g ? ` and granted ${full(r.g)}` : ""}. A European patent lasts at most 20 years from filing, so its term ended ${full(r.te)}.`
        : `Filed ${full(r.f)} and never granted as a European patent. Had it been granted, its 20-year term would have ended ${full(r.te)}.`,
      passed(r.f, 25.5) ? `A supplementary protection certificate, which can extend a medicine or crop-protection patent, adds at most five and a half years, so even that would have ended by ${full(addYears(r.f, 25.5))}.`
        : "Supplementary protection certificates extend only medicine and crop-protection patents, and it isn't classified as either."],
      "We check European rights only. A US or other national patent in its family could still be in force: check its family on Espacenet or Google Patents."],
    facts: r => [["Filed", full(r.f)], ["Published", full(r.p)], ["Granted", r.g ? full(r.g) : "Never granted"], ["Term ended", full(r.te)], ["Application number", `EP ${r.app || "—"}`]],
  },
  CA: {
    name: "Canada", adj: "Canadian", office: "CIPO", party: "Owner on the CIPO record", ipc: "IPC", credit: "Contains information licensed under the Open Government Licence – Canada.",
    granted: r => !!r.g,
    links: (num, kind) => {
      const rec = `https://brevets-patents.ic.gc.ca/opic-cipo/cpd/eng/patent/${num}/summary.html`, google = `https://patents.google.com/patent/CA${num}${kind}/en`;
      return { doc: rec, docLabel: "CIPO record", docNote: "Its claims, description and drawings are in the Canadian Patents Database.", google,
        official: [[rec, "Canadian Patents Database", "Claims, description, documents and status.", "CIPO"]],
        cross: [[google, "Google Patents", GOOGLE, "patents.google.com"]] };
    },
    why: (r, g) => {
      const now = r.f && r.f >= "1989-10-01";
      return [[!g ? `Filed ${full(r.f)}. No grant is recorded for it in Canada; had it been granted, its 20-year term would have ended ${full(r.te)}.`
          : now ? `Filed ${full(r.f)} and granted ${full(r.g)}. A Canadian patent filed from October 1, 1989 lasts 20 years from filing, so its term ended ${full(r.te)}.`
          : `Granted ${full(r.g)}. A Canadian patent filed before October 1, 1989 lasted 17 years from grant, so its term ended ${full(r.te)}.`,
        ...(!now ? [] : passed(r.f, 22) ? [`A certificate of supplementary protection adds at most two years for a drug, so even that would have ended by ${full(addYears(r.f, 22))}.`]
          : ["Certificates of supplementary protection extend only drug patents, and it isn't classified as one."])],
        "We check Canadian rights only. A patent in its family in another country could still be in force: check its family on Google Patents."];
    },
    facts: r => [["Filed", full(r.f)], ["Granted", r.g ? full(r.g) : "No grant recorded"], ["Term ended", full(r.te)], ["Patent number", r.n]],
  },
  AU: {
    name: "Australia", adj: "Australian", office: "IP Australia", party: "Applicant", ipc: "IPC", credit: "Data from IP Australia's IPGOD, licensed under CC BY 2.5 AU.",
    granted: r => !!r.g || /-[IP]$/.test(r.id),
    links: num => {
      const rec = `https://ipsearch.ipaustralia.gov.au/patents/${num}`, google = `https://patents.google.com/?q=AU${num}`;
      return { doc: rec, docLabel: "AusPat record", docNote: "Its specification, documents and status are on IP Australia's AusPat.", google,
        official: [[rec, "AusPat", "Specification, documents, status and events.", "IP Australia"]],
        cross: [[google, "Google Patents", GOOGLE, "patents.google.com"]] };
    },
    why: (r, g) => {
      const type = { I: "innovation patent lasts at most 8 years", P: "petty patent lasted at most 6 years" }[r.id.slice(-1)];
      if (type) return [[`Filed ${full(r.f)}. An Australian ${type} from its date of patent, at most a year after this filing, so it ended by ${full(r.te)}.`],
        "We check Australian rights only. A patent in its family in another country could still be in force."];
      return [[g ? `Filed ${full(r.f)} and granted ${full(r.g)}. An Australian standard patent lasts 20 years from its date of patent, which is at most a year after this filing, so its term ended by ${full(r.te)}.`
          : `Filed ${full(r.f)}. Even if it was granted, its term would have ended by ${full(r.te)}.`,
        passed(r.f, 26) ? `A pharmaceutical extension adds at most five years, so even that would have ended by ${full(addYears(r.f, 26))}.`
          : "Term extensions apply only to pharmaceutical patents, and it isn't classified as one."],
        "We check Australian rights only. A patent in its family in another country could still be in force: check its family on Google Patents."];
    },
    facts: r => [["Filed", full(r.f)], ["Granted", r.g ? full(r.g) : "No grant recorded"], ["Term ended by", full(r.te)], ["Application number", r.n]],
  },
};
const kindOf = r => { const R = REGIONS[r.k]; return R ? (R.granted(r) ? [`Expired ${R.adj} patent`, "expired"] : [`${R.adj} application, no grant`, "abandoned"]) : KIND[r.k || ""] || KIND[""]; };

// Weapons, ammunition and explosives (pipeline/patents.py armed): listed, but no Claude kit. Same note as pipeline/website.py KIT_OFF.
const armed = r => (r.cpc || []).some(c => /^(F41|F42|C06[BCD]|G21J)/i.test(c.replace(/\s/g, "")));
const KIT_OFF = `<div class="panel soft kitoff"><div class="block"><h3>No Claude kit for weapons</h3><p class="prose">Claude doesn't help design weapons, ammunition or explosives, so this page has no Reinvent kit. To develop this one, work with a federally licensed manufacturer (many of these items are regulated) and a registered patent attorney or agent, listed on the <a href="https://oedci.uspto.gov/OEDCI/" ${EXT}>USPTO roster</a>.</p></div></div>`;

export function links(r) {
  const [, num, kind] = r.id.split("-"), app = r.k === "A";
  if (REGIONS[r.k]) return REGIONS[r.k].links(num, kind, r);
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
  const R = REGIONS[r.k];
  if (R) return R.why(r, R.granted(r));
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
  return { id: r.id, n: r.n, t: r.t, ot: r.t, h: "", tw: "", st: kindOf(r)[1], status: kindOf(r)[0], field: fieldOf(r)[1], filed: r.f, granted: REGIONS[r.k] ? r.g || r.p : r.p, where: REGIONS[r.k]?.name, adj: REGIONS[r.k]?.adj, office: REGIONS[r.k]?.office,
    expired: null, termEnd: r.te, abs: r.ab || "", claims: [], figs: [], fieldText: "", bg: "", inventors: r.i || null, assignee: r.a || null, cpc: r.cpc || [],
    app: r.app, why: checks, warn, sheets: [], totalSheets: r.sh, url: `${SITE.site}/patents/${r.id}/`, pdf: L.doc || L.pdf, google: L.google, armed: armed(r) };
}

export function renderArchive(tpl, r) {
  const [fk, field] = fieldOf(r), L = links(r), [checks, warn] = why(r), arm = armed(r), K = kindOf(r), R = REGIONS[r.k], office = R ? R.office : "USPTO", doc = L.doc || L.pdf;
  const owner = (r.a ? ` · ${R ? R.party : "Assignee"}: ${E(r.a)}` : "") + (r.i ? ` · Inventors: ${E(r.i)}` : "");
  const lc = (x, cls = "") => `<a class="lcard ${cls}" href="${x[0]}" ${EXT}><b>${E(x[1])}${icon("ext")}</b><span>${E(x[2])}</span><small>${E(x[3])}</small></a>`;
  const official = R ? L.official : [[L.pdf, "Full published document", "Text and every drawing sheet as a PDF.", "USPTO"],
    [L.center, "File history", "Status, office actions, notices, fee records and petitions.", "USPTO Patent Center"],
    [L.ppubs, "Patent Public Search record", "Searchable full text and bibliographic data.", "USPTO"]];
  const cross = R ? L.cross : [[L.google, "Google Patents", "Full text, worldwide family, citing patents and legal events.", "patents.google.com"],
    [L.justia, "Justia Patents", "Full text, claims and classification.", "patents.justia.com"], [L.fpo, "FreePatentsOnline", "Full text and PDF.", "freepatentsonline.com"],
    [L.espacenet, "Espacenet", "Foreign family and legal status.", "European Patent Office"]];
  // the published document itself, inline: its first page has the abstract and main drawing (US and EPO PDFs allow framing)
  const embed = R ? L.embed : L.pdf;
  // US patents granted up to about 2014 have every page as an image on Google Patents' image store, so their drawing sheets
  // show here; patent.js swaps in the PDF view below if the first sheet doesn't load (newer numbers aren't there)
  const gsheets = !R && r.k !== "A" && r.sh ? Math.min(r.sh, 40) : 0;
  const gallery = gsheets ? `<link rel="preconnect" href="https://patentimages.storage.googleapis.com"><div class="gsheets"><div class="gallery">${Array.from({ length: gsheets }, (_, k) =>
    `<figure><button type="button" data-sheet="${k}" aria-label="Enlarge sheet ${k + 1}"><img src="${gpage(r.id, k + 1)}" alt="Drawing sheet ${k + 1} of ${E(r.n)}" ${k === 0 ? 'fetchpriority="high"' : 'loading="lazy"'} decoding="async" referrerpolicy="no-referrer"></button>`
    + `<figcaption><span>Sheet ${k + 1} of ${r.sh}</span></figcaption></figure>`).join("")}</div>
    <p class="cap">${r.sh} drawing ${r.sh === 1 ? "sheet" : "sheets"} from the published patent, as page images from Google Patents. <a href="${L.pdf}" ${EXT}>Open the USPTO PDF</a></p></div>` : "";
  const draw = gallery ? gallery + `<div class="gfail" hidden>${drawFallback()}</div>` : drawFallback();
  function drawFallback() { return embed
    ? `<div class="docview"><iframe src="${embed}#view=FitH" title="Published document ${E(r.n)}" loading="lazy"></iframe><p class="cap">The published document from the ${office}: abstract, claims, description${r.k === "S" ? "" : " and drawings"}. <a href="${embed}" ${EXT}>Open it full size</a></p></div>`
    : R
    ? `<div class="nofig later"><b>Drawings and full text</b><p class="muted">${L.docNote}</p><a class="btn secondary sm" href="${doc}" ${EXT}>${icon("file")}Open the ${L.docLabel}</a></div>`
    : r.sh
    ? `<div class="nofig later"><b>${r.sh} drawing ${r.sh === 1 ? "sheet" : "sheets"}</b><p class="muted">Every sheet is in the USPTO PDF.</p><a class="btn secondary sm" href="${L.pdf}" ${EXT}>${icon("file")}Open the USPTO PDF</a></div>`
    : arm ? `<div class="nofig"><b>This document has no drawings.</b></div>`
    : `<div class="nofig"><b>This document has no drawings.</b><p class="muted">Claude can sketch it from the patent text.</p><button class="btn secondary sm" type="button" data-kit="sketch">${icon("spark")}Sketch it with Claude</button></div>`; }
  const events = r.k === "S" ? [[r.p, "Design granted"], [r.te, "Term ended", "bad"]]
    : r.k === "A" ? [[r.f, "Application filed"], [r.p, "Application published"]]
    : r.k === "E" ? [[r.f, "Application filed"], [r.p, "Published"], [r.g, "Patent granted"], [r.te, "Term ended", "bad"]]
    : R ? [[r.f, "Application filed"], [r.g, "Patent granted"], [r.te, r.k === "AU" ? "Term ended by" : "Term ended", "bad"]]
    : [[r.f, "Application filed"], [r.p, "Patent granted"], [r.te, "Term ended", "bad"]];
  const timeline = timelineSection(events, office);
  const cpc = (r.cpc || []).length ? E(r.cpc[0]) + (r.cpc.length > 1 ? ` <span class="muted" title="${E(r.cpc.join(", "))}">+${r.cpc.length - 1} more</span>` : "") : "—";
  const body = `<div class="page" id="patent" data-source="archive" data-id="${E(r.id)}" data-n="${E(r.n)}" data-sheets="${gsheets}" data-total="${r.sh || 0}"${gsheets ? ` data-sheetbase="${gpage(r.id, "")}"` : ""} data-pdf="${doc}">
<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a><span>/</span><a href="/fields/${fk}/">${E(field)}</a><span>/</span><span>${E(r.n)}</span></nav>
<div class="phead">
  <div><div class="badges"><span class="badge ${K[1]}">${K[0]}</span><span class="badge plain">${R ? R.name : "Archive"}</span>${r.a || r.k === "A" ? "" : '<span class="badge plain">No assignee recorded</span>'}<span class="badge ok" id="vbadge" hidden></span></div>
  <h1>${E(r.t)}</h1><p class="asfiled"><span class="num">${E(r.n)}</span>${owner}</p></div>
  <div class="pactions">
    ${arm ? "" : `<button class="btn primary" type="button" data-kit="workshop">${icon("spark")}Reinvent with Claude</button>`}
    <button class="btn quiet" type="button" id="reserveBtn">${icon("flag")}Reserve</button>
    <a class="btn quiet" href="${doc}" ${EXT}>${icon("file")}${R ? L.docLabel : "USPTO PDF"}</a>
    <button class="btn quiet" type="button" id="saveBtn" aria-pressed="false">${icon("bookmark")}<span>Save</span></button>
    <button class="btn quiet" type="button" id="copyLink">${icon("link")}Copy link</button>
    <div class="resline" id="resline" aria-live="polite"></div>
  </div>
</div>
<div class="playout">
  <nav class="toc" aria-label="On this page"><a href="#overview">Overview</a>${timeline ? '<a href="#history">Timeline</a>' : ""}<a href="#sources">Sources &amp; verification</a></nav>
  <div>
  <section class="psec" id="overview"><h2>Overview</h2>
  <div class="ov"><div>${draw}</div>
  <div class="stack">${arm ? KIT_OFF : ""}
    ${r.ab ? `<div class="block"><h3>Abstract <span class="src">From the ${R ? R.adj + " " : ""}patent</span></h3><p class="prose source">${E(r.ab)}</p></div>` : ""}
    <div class="panel soft"><div class="block"><h3>Read the whole patent</h3><p class="prose">Listed from its ${office} record in Patent Yard's ${R ? `archive of ${R.adj} patents past their term` : "full-term archive"}. Its claims, description and drawings are in the <a href="${doc}" ${EXT}>${R ? L.docLabel : "USPTO PDF"}</a> and on <a href="${L.google}" ${EXT}>Google Patents</a>${arm ? "" : ", and the Claude kit works from them"}.</p>
      <div class="rowbtns" style="margin-top:12px"><a class="btn secondary sm" href="${L.google}" ${EXT}>Google Patents${icon("ext")}</a><a class="btn secondary sm" href="${doc}" ${EXT}>${icon("file")}${R ? L.docLabel : "USPTO PDF"}</a></div></div></div>
    <div class="panel soft"><div class="block"><h3>Why it's listed</h3><ul class="checks">${checks.map(c => `<li>${E(c)}</li>`).join("")}<li class="warn">${E(warn)}</li></ul></div></div>
    <div class="facts">
      ${R ? R.facts(r).map(([k, v]) => `<div><small>${k}</small><b>${E(v)}</b></div>`).join("") + `<div><small>Classification (${R.ipc})</small><b>${cpc}</b></div>`
      : `<div><small>Filed</small><b>${E(full(r.f))}</b></div><div><small>${r.k === "A" ? "Published" : "Granted"}</small><b>${E(full(r.p))}</b></div><div><small>${r.k === "A" ? "Status" : "Term ended"}</small><b>${r.k === "A" ? "Abandoned (inferred)" : E(full(r.te))}</b></div>
      <div><small>Application number</small><b>${E(r.app || "—")}</b></div><div><small>Classification (CPC)</small><b>${cpc}</b></div><div><small>Length</small><b>${r.pg ? `${r.pg} pages` : "—"}</b></div>`}
    </div>
  </div></div></section>
  ${timeline}
  <section class="psec" id="sources"><h2>Sources &amp; verification</h2><div class="stack">
    <div class="cols2 links2"><div class="block"><h3>Official ${office} records</h3><div class="linklist">${official.map(x => lc(x)).join("")}</div></div>
    <div class="block"><h3>Cross-check elsewhere</h3><div class="linklist">${cross.map(x => lc(x)).join("")}</div></div></div>
    <p class="muted" style="font-size:13px">Everything on this page comes from the ${office} record linked above.${R ? " " + R.credit : ""}</p>
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
  return tpl.replaceAll("%%TITLE%%", () => E(`${r.t} (${r.n})`)).replaceAll("%%DESC%%", () => E(`${r.n}, ${K[0].toLowerCase()}: ${r.t}`))
    .replaceAll("%%PATH%%", () => `/patents/${r.id}/`).replace("%%BODY%%", () => body);
}
