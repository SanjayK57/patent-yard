// All patents: every application worldwide (pipeline/world.py), kept in two separate Pages projects because one
// project holds at most 20,000 files. Pages serves whole files only, so the Function fetches a pack and slices out
// the records it needs: uint32 count, uint32 offsets[count + 1], then the records.
import SITE from "./site.json";

const W = SITE.world || {};
const E = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const icon = n => `<svg class="i" aria-hidden="true"><use href="#i-${n}"/></svg>`;
const EXT = 'target="_blank" rel="noopener noreferrer"';
const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
const full = s => { if (!s) return "—"; const [y, m, d] = s.split("-").map(Number); return `${MONTHS[m - 1]} ${d}, ${y}`; };
const fieldName = k => SITE.fields[k] || "Other Inventions";

export const COUNTRY = { US: "United States", CN: "China", JP: "Japan", KR: "South Korea", DE: "Germany", EP: "Europe (EPO)", GB: "United Kingdom",
  FR: "France", CA: "Canada", AU: "Australia", TW: "Taiwan", ES: "Spain", RU: "Russia", SU: "Soviet Union", AT: "Austria", BR: "Brazil", IT: "Italy",
  CH: "Switzerland", BE: "Belgium", NL: "Netherlands", SE: "Sweden", DK: "Denmark", PL: "Poland", MX: "Mexico", ZA: "South Africa", UA: "Ukraine",
  IL: "Israel", FI: "Finland", DD: "East Germany", NO: "Norway", AR: "Argentina", HU: "Hungary", HK: "Hong Kong", PT: "Portugal", SG: "Singapore",
  TR: "Turkey", NZ: "New Zealand", CS: "Czechoslovakia", MY: "Malaysia", GR: "Greece", IN: "India", CZ: "Czechia", IE: "Ireland", RO: "Romania",
  BG: "Bulgaria", YU: "Yugoslavia", PH: "Philippines", SI: "Slovenia", SK: "Slovakia", EA: "Eurasian Patent Office", EG: "Egypt", HR: "Croatia",
  LU: "Luxembourg", CL: "Chile", CO: "Colombia", PE: "Peru", ID: "Indonesia", TH: "Thailand", VN: "Vietnam", SA: "Saudi Arabia", AE: "UAE",
  MA: "Morocco", TN: "Tunisia", GE: "Georgia", MD: "Moldova", RS: "Serbia", LT: "Lithuania", LV: "Latvia", EE: "Estonia", CY: "Cyprus",
  MC: "Monaco", AP: "ARIPO", OA: "OAPI", GC: "Gulf Cooperation Council", CU: "Cuba", UY: "Uruguay", EC: "Ecuador", CR: "Costa Rica" };
export const countryName = cc => COUNTRY[cc] || cc;

const get = async path => {
  const host = path.startsWith("c/") ? W.cards : W.details;
  const res = await fetch(`${host}/${path}`, { cf: { cacheTtl: 86400, cacheEverything: true } });
  return res.ok ? new Uint8Array(await res.arrayBuffer()) : null;
};
function slice(buf, i) {
  const dv = new DataView(buf.buffer, buf.byteOffset, buf.byteLength), n = dv.getUint32(0, true);
  if (i >= n) return null;
  const base = 4 + 4 * (n + 1);
  return buf.subarray(base + dv.getUint32(4 + 4 * i, true), base + dv.getUint32(8 + 4 * i, true));
}
const inflate = bytes => new Response(new Response(bytes).body.pipeThrough(new DecompressionStream("deflate-raw"))).text();

// [[doc, "id\ttitle\towner\tyyyymmdd\tcc\tkind\tflags\tfield"], ...]; at most 40 pack files per call (subrequest limit)
export async function cards(docs) {
  const files = [...new Set(docs.map(d => Math.floor(d / W.per)))].slice(0, 40);
  const packs = Object.fromEntries(await Promise.all(files.map(async f => [f, await get(`c/${f}.bin`)])));
  const dec = new TextDecoder();
  return docs.filter(d => packs[Math.floor(d / W.per)]).map(d => { const b = slice(packs[Math.floor(d / W.per)], d % W.per); return b && [d, dec.decode(b)]; }).filter(Boolean);
}

// "CN-112345678-A" or "CN-112345678" -> the full record, or null
export async function worldRecord(id) {
  if (!W.details) return null;
  const key = id.split("-").slice(0, 2).join("-");
  const h = new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(key)));
  const x = await get(`x/${((h[0] << 8) | h[1]) % W.ids}.bin`);
  if (!x) return null;
  const k = ((h[2] << 24) | (h[3] << 16) | (h[4] << 8) | h[5]) >>> 0, dv = new DataView(x.buffer, x.byteOffset, x.byteLength);
  let lo = 0, hi = x.byteLength / 8;  // entries are uint64 (key << 32 | doc), little-endian, sorted
  while (lo < hi) { const mid = (lo + hi) >> 1; if (dv.getUint32(mid * 8 + 4, true) < k) lo = mid + 1; else hi = mid; }
  for (let i = lo; i < x.byteLength / 8 && dv.getUint32(i * 8 + 4, true) === k; i++) {
    const doc = dv.getUint32(i * 8, true), pack = await get(`d/${Math.floor(doc / W.per)}.bin`);
    const b = pack && slice(pack, doc % W.per);
    const r = b && JSON.parse(await inflate(b));
    if (r && r.pn.split("-").slice(0, 2).join("-") === key) return r;
  }
  return null;
}

export const label = r => { const [cc, num, kind] = r.pn.split("-"); return `${cc} ${num}${kind ? " " + kind : ""}`; };
export function status(r) {
  if (r.free) return ["Past its term", "expired", [`Filed ${full(r.f)}. A patent lasts at most 20 years from filing, so no patent from this filing can still be in force${r.cpc.some(c => /^(A61K|A61P|A01N|A01P|C07|C12)/.test(c)) ? ", even with the up to six-year extensions medicine and crop-protection patents can get" : ""}.`]];
  if (r.g) return ["Granted, may be in force", "plain", [`Granted ${full(r.g)}. It may still be in force: owners keep patents alive by paying renewal fees, and many stop.`, "Check its status in the official register of its country before relying on it."]];
  return ["Published application", "plain", ["This application was published, but its outcome is not recorded here: it may have been granted, refused or withdrawn.", "Check the official register of its country for its status."]];
}

export function worldKit(r) {
  const [st] = status(r), g = google(r);
  return { id: r.pn, n: label(r), t: r.t, ot: r.t, h: "", tw: "", st: "expired", status: st, field: fieldName(r.ind), filed: r.f, granted: r.g || r.p,
    where: countryName(r.cc), adj: countryName(r.cc), office: "official", expired: null, termEnd: null, abs: r.ab || "", claims: [], figs: [], fieldText: "",
    bg: "", inventors: r.i || null, assignee: r.a || null, cpc: r.cpc, app: r.app, why: status(r)[2], warn: "", sheets: [], totalSheets: 0,
    url: `${SITE.site}/patents/${r.pn}/`, pdf: g, google: g, armed: false };
}
const google = r => `https://patents.google.com/patent/${r.pn.replace(/-/g, "")}/en`;

export function renderWorld(tpl, r) {
  const [st, cls, checks] = status(r), n = label(r), g = google(r), country = countryName(r.cc);
  const esp = `https://worldwide.espacenet.com/patent/search?q=pn%3D${r.pn.replace(/-/g, "")}`;
  const lc = x => `<a class="lcard" href="${x[0]}" ${EXT}><b>${E(x[1])}${icon("ext")}</b><span>${E(x[2])}</span><small>${E(x[3])}</small></a>`;
  const owner = (r.a ? ` · Owner: ${E(r.a)}` : "") + (r.i ? ` · Inventor: ${E(r.i)}` : "");
  const facts = [["Country", country], ["Filed", full(r.f)], ["Published", full(r.p)], ["Granted", r.g ? full(r.g) : "Not recorded"], ["Priority", full(r.pr)],
    ["Application", r.app || "—"], ["Classification (CPC)", r.cpc.join(", ") || "—"], ["Family", r.fam ? `Google family ${r.fam}` : "—"]];
  const body = `<div class="page" id="patent" data-id="${E(r.pn)}" data-n="${E(n)}" data-sheets="0" data-total="0" data-pdf="${g}">
<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a><span>/</span><a href="/all/">All patents</a><span>/</span><span>${E(n)}</span></nav>
<div class="phead">
  <div><div class="badges"><span class="badge ${cls}">${st}</span><span class="badge plain">${E(country)}</span><span class="badge ok" id="vbadge" hidden></span></div>
  <h1>${E(r.t)}</h1><p class="asfiled">${E(n)}${owner}</p></div>
  <div class="pactions">
    ${r.free ? `<button class="btn primary" type="button" data-kit="workshop">${icon("spark")}Reinvent with Claude</button>` : ""}
    <button class="btn secondary" type="button" id="reserveBtn"${r.free ? "" : " hidden"}>${icon("flag")}Reserve</button>
    <a class="btn secondary" href="${g}" ${EXT}>${icon("file")}Full text</a>
    <button class="btn quiet" type="button" id="saveBtn" aria-pressed="false">${icon("bookmark")}<span>Save</span></button>
    <button class="btn quiet" type="button" id="copyLink">${icon("link")}Copy link</button>
    <div class="resline" id="resline" aria-live="polite"></div>
  </div>
</div>
<div class="playout">
  <nav class="toc" aria-label="On this page"><a href="#overview">Overview</a><a href="#sources">Sources</a></nav>
  <div>
  <section class="psec" id="overview"><h2>Overview</h2>
  <div class="ov"><div><div class="nofig later"><b>Full text and drawings</b><p class="muted">The claims, description and drawings are on Google Patents${r.tl && r.tl !== "en" ? ", with a machine translation" : ""}.</p><a class="btn secondary sm" href="${g}" ${EXT}>${icon("file")}Open on Google Patents</a></div></div>
  <div class="stack">
    ${r.ab ? `<div class="block"><h3>Abstract</h3><p class="prose">${E(r.ab)}</p></div>` : ""}
    <div class="panel soft"><div class="block"><h3>Is it free to use?</h3><ul class="checks">${checks.map((c, i) => `<li${!r.free && i === checks.length - 1 ? ' class="warn"' : ""}>${E(c)}</li>`).join("")}</ul>
      ${r.free ? "" : `<p class="muted" style="margin-top:8px">Looking for inventions you can use now? <a href="/browse/">Browse the free-to-use register</a>.</p>`}</div></div>
    <div class="facts">${facts.map(([k, v]) => `<div><small>${k}</small><b>${E(v)}</b></div>`).join("")}</div>
  </div></div></section>
  <section class="psec" id="sources"><h2>Sources</h2><div class="stack">
    <div class="cols2 links2"><div class="block"><h3>Read it</h3><div class="linklist">${lc([g, "Google Patents", "Full text, drawings, family and legal events.", "patents.google.com"])}${lc([esp, "Espacenet", "The European Patent Office's worldwide search, with legal status.", "European Patent Office"])}</div></div>
    <div class="block"><h3>Where this record comes from</h3><p class="prose">Google Patents Public Data, used under CC BY 4.0. Field: ${E(fieldName(r.ind))}.</p></div></div>
    <div class="rowbtns noprint"><button class="btn secondary sm" type="button" id="reportBtn" hidden>Report a problem with this listing</button></div>
  </div></section>
  </div>
</div>
</div>
<dialog id="viewer" aria-label="Drawing viewer"></dialog>
<dialog id="kit" aria-labelledby="kitTitle"></dialog>
<dialog id="resDlg" aria-labelledby="resTitle"></dialog>
<dialog id="repDlg" aria-labelledby="repTitle"></dialog>`;
  return tpl.replaceAll("%%TITLE%%", () => E(`${r.t} (${n})`)).replaceAll("%%DESC%%", () => E(`${n}, ${country}: ${r.t}`))
    .replaceAll("%%PATH%%", () => `/patents/${r.pn}/`).replace("%%BODY%%", () => body);
}
