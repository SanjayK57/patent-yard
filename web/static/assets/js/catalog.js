// The register's catalog, loaded in small pieces so no page downloads all of it (written by pipeline/website.py
// Site.catalog):
//   /data/latest.json   the current catalog version, totals and field names
//   /v/<v>/keys.bin     per patent, in catalog order: field, flags, build, and freed/added/filed days (filter, sort)
//   /v/<v>/c/<n>.json   card text for patents n*block .. n*block+block-1
//   /v/<v>/s/<ab>.json  search index: word -> patents it appears in, for words starting with "ab"
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
// a patent with no drawing on file: its field's line symbol and its number in a blueprint frame (site.css .fig.plate)
export const plateHTML = (field, n, tag, over = "") => `<div class="fig plate" data-tag="${esc(tag)}">${over ? `<span class="over">${over}</span>` : ""}<svg class="fglyph" aria-hidden="true"><use href="#f-${esc(field || "other")}"/></svg><span class="numart">${esc(n)}</span></div>`;
const icon = name => `<svg class="i" aria-hidden="true"><use href="#i-${name}"/></svg>`;
export const STATUS = { lapsed: "Lapsed, fee not paid", expired: "Expired, full term", abandoned: "Likely abandoned" };
const ST = ["lapsed", "expired", "abandoned"];
const BUILD = ["", "Weekend", "Garage", "Workshop", "Lab", "Industrial"];

let latestP;
export const latest = () => (latestP ||= fetch("/data/latest.json", { cache: "no-cache" })
  .then(r => { if (!r.ok) throw new Error("catalog"); return r.json(); })
  .catch(e => { latestP = null; throw e; }));

const memo = new Map();
function get(path, bin) {
  if (!memo.has(path)) memo.set(path, fetch(path).then(r => { if (!r.ok) throw new Error(path); return bin ? r.arrayBuffer() : r.json(); })
    .catch(e => { memo.delete(path); throw e; }));
  return memo.get(path);
}

let keysP;
export function keys() {
  return (keysP ||= (async () => {
    const L = await latest(), buf = await get(`/v/${L.v}/keys.bin`, true);
    const n = new DataView(buf).getUint32(0, true);
    let o = 4;
    const col = () => { const a = new Uint8Array(buf, o, n); o += n; return a; };
    const field = col(), flags = col(), build = col();
    if (o % 2) o++;
    const day = () => { const a = new Uint16Array(buf, o, n); o += 2 * n; return a; };
    return { n, field, flags, build, freed: day(), added: day(), filed: day() };
  })().catch(e => { keysP = null; throw e; }));
}

// Card data for catalog positions, in the order given
export async function cards(docs) {
  const L = await latest(), K = await keys();
  const blocks = await Promise.all([...new Set(docs.map(d => Math.floor(d / L.block)))].map(async b => [b, await get(`/v/${L.v}/c/${b}.json`)]));
  const data = Object.fromEntries(blocks);
  return docs.map(d => {
    const [id, t, h, a, sh] = data[Math.floor(d / L.block)][d % L.block], f = K.flags[d];
    return { doc: d, id, t, h, a, sh, ind: L.fields[K.field[d]], st: ST[f & 3], ia: !!(f & 4), fig: !!(f & 8), noted: !!(f & 16), pending: !!(f & 32), b: K.build[d], freed: K.freed[d], filed: K.filed[d] };
  });
}

// "Surprise me": a random patent with its drawings and full text in
let complete;
export async function randomPatent() {
  const K = await keys();
  if (!complete) { complete = []; for (let d = 0; d < K.n; d++) if ((K.flags[d] & 8) && !(K.flags[d] & 32)) complete.push(d); }
  const pool = complete.length ? complete : [...Array(K.n).keys()];
  return (await cards([pool[Math.floor(Math.random() * pool.length)]]))[0];
}

// ---------------------------------------------------------------- search
// Whole words ("arm" finds arm, arms, armrest; never farm or alarm); every word must match; ranked by where it
// matched: the name, the title as filed, the summary, tags, the owner, then the first sentence of the abstract.
const STOP = new Set("a an and the of for to in on with by or at is it its from as be this that".split(" "));
export const words = s => String(s ?? "").toLowerCase().normalize("NFKD").replace(/[̀-ͯ]/g, "")
  .split(/[^a-z0-9]+/).filter(w => w.length >= 2 && !STOP.has(w) && /[a-z]/.test(w));

// "US 11,112,282 B2", "11112282" or "2015/0123456" -> the number, so the search can jump straight to it
// "US 11,112,282 B2" -> "11112282", "EP 0500272 B1" -> "EP0500272": the address /patents/<it> redirects to the patent
export function patentNumber(q) {
  const s = String(q).replace(/[,\s/.]/g, ""), ep = s.match(/^ep(\d{1,7})(?:[ab]\d)?$/i), other = s.match(/^(ca\d{1,7}|au\d{10})(?:[a-z]\d?)?$/i);
  if (ep) return "EP" + ep[1].padStart(7, "0");
  if (other) return other[1].toUpperCase();
  const m = s.match(/^(?:us)?(\d{5,11})(?:[a-z]\d?)?$/i);
  return m ? m[1] : null;
}

export async function search(q) {  // -> Map(catalog position -> score) of the patents that match every word
  const L = await latest(), terms = [...new Set(words(q))];
  let out = null;
  for (const term of terms) {
    const shard = await get(`/v/${L.v}/s/${term.slice(0, 2)}.json`).catch(() => ({}));
    const stems = [term];
    if (term.length > 3 && term.endsWith("s")) stems.push(term.slice(0, -1));
    if (term.length > 4 && term.endsWith("es")) stems.push(term.slice(0, -2));
    const sc = new Map();
    for (const word in shard) {
      let f = 0;
      for (const st of stems) {
        if (word === st) f = Math.max(f, 1.3);
        else if (word.startsWith(st)) f = Math.max(f, st.length / word.length >= .6 ? 1 : .7);
      }
      if (!f) continue;
      let doc = 0;
      for (const v of shard[word]) {
        doc += v >>> 3;
        const s = L.weights[v & 7] * f;
        if (s > (sc.get(doc) || 0)) sc.set(doc, s);
      }
    }
    if (!out) out = sc;
    else for (const [d, s] of out) { const t = sc.get(d); if (t) out.set(d, s + t); else out.delete(d); }
    if (!out.size) break;
  }
  return out || new Map();
}

// Best matches first, with their card data
export async function topMatches(q, n) {
  const sc = await search(q);
  const top = [...sc].sort((a, b) => b[1] - a[1] || a[0] - b[0]).slice(0, n).map(([d]) => d);
  return top.length ? cards(top) : [];
}

// ---------------------------------------------------------------- cards (pipeline/website.py Site.card draws the same)
// what patentNumber() returned, for display: "11112282" -> "US 11,112,282", "EP0500272" -> "EP 0500272"
export const numLabel = num => (/^(EP|CA|AU)/.test(num) ? `${num.slice(0, 2)} ${num.slice(2)}` : numberLabel(`US-${num}-`).trim());

export function numberLabel(id) {
  const [cc, num, kind] = id.split("-");
  if (cc === "EP" || cc === "CA") return `${cc} ${num} ${kind}`;
  if (cc === "AU") return `AU ${num}`;
  if (/\D/.test(num)) return `US ${num} ${kind}`.trim();  // designs and reissues: US D500000 S
  return num.length > 8 ? `US ${num.slice(0, 4)}/${num.slice(4)} ${kind}` : `US ${Number(num).toLocaleString("en-US")} ${kind}`;
}
const fmtDay = (n, o) => (n ? new Date(n * 864e5).toLocaleDateString("en-US", { timeZone: "UTC", ...o }) : "—");
const meter = b => `<span class="meter" aria-hidden="true">${[1, 2, 3, 4, 5].map(i => `<i class="${i <= b ? "on" : ""}"></i>`).join("")}</span>`;

export function cardHTML(c, names, i = 9) {
  const n = numberLabel(c.id), owner = c.ia ? "Solo inventor" : c.a || "—";
  const badge = `<span class="badge ${c.st}">${STATUS[c.st]}</span>`;
  const fig = c.fig
    ? `<div class="fig"><img src="/img/p/${c.id}/1.png" alt="Drawing from ${esc(n)}" loading="${i < 4 ? "eager" : "lazy"}" decoding="async"><span class="over">${badge}</span>${c.sh ? `<span class="sheets">${icon("sheet")}${c.sh} ${c.sh === 1 ? "drawing" : "drawings"}</span>` : ""}</div>`
    : plateHTML(c.ind, n, "No drawing", badge);
  const freed = c.st === "abandoned" ? ["Published", fmtDay(c.freed, { year: "numeric" })] : [c.st === "lapsed" ? "Lapsed" : "Term ended", fmtDay(c.freed, { month: "short", year: "numeric" })];
  const first = c.b ? `<div><small>Build</small><span>${meter(c.b)}${BUILD[c.b]}</span></div>` : `<div><small>Filed</small><span>${fmtDay(c.filed, { year: "numeric" })}</span></div>`;
  return `<article class="card" data-id="${esc(c.id)}">${fig}<div class="cbody"><span class="fieldname">${esc(names[c.ind] || c.ind)} · <span class="num-id">${esc(n)}</span></span>`
    + `<h3><a href="/patents/${esc(c.id)}/">${esc(c.t)}</a></h3><p>${esc(c.h)}</p></div>`
    + `<div class="cmeta">${first}<div><small>${freed[0]}</small><span>${freed[1]}</span></div><div><small>${c.st === "abandoned" ? "Applicant" : "Owner"}</small><span title="${esc(owner)}">${esc(owner)}</span></div></div></article>`;
}

export const skeletons = n => Array.from({ length: n }, () => `<div class="card skel" aria-hidden="true"><div class="fig"></div><div class="cbody"><i></i><i></i><i></i></div></div>`).join("");

// ---------------------------------------------------------------- the full-term archive (latest.json "archive")
//   /v/<av>/s/<n>.json  word -> archive patents, for words whose crc32 % buckets is n (exact words, the commonest left out)
//   /v/<av>/c/<n>.json  [id, title, owner, field index, grant year] for archive patents n*block onward, newest first
const CRC = Array.from({ length: 256 }, (_, n) => { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1; return c >>> 0; });
export const crc32 = s => { let c = 0xFFFFFFFF; for (const b of new TextEncoder().encode(s)) c = CRC[(c ^ b) & 255] ^ (c >>> 8); return (c ^ 0xFFFFFFFF) >>> 0; };

export async function archiveInfo() { return (await latest()).archive; }

// The words of a query the archive can look up: common words ("method", "system") are not indexed and are skipped.
export async function archiveTerms(q) {
  const A = await archiveInfo(), stop = new Set(A?.stop || []);
  return [...new Set(words(q))].filter(t => !stop.has(t));
}

export async function archiveSearch(q) {  // -> Map(archive position -> score), patents matching every looked-up word
  const A = await archiveInfo();
  if (!A?.n) return new Map();
  let out = null;
  for (const term of await archiveTerms(q)) {
    const forms = new Set([term, term + "s"]);
    if (term.length > 3 && term.endsWith("s")) forms.add(term.slice(0, -1));
    if (term.length > 4 && term.endsWith("es")) forms.add(term.slice(0, -2));
    const sc = new Map();
    for (const w of forms) {
      const bucket = await get(`/v/${A.v}/s/${crc32(w) % A.buckets}.json`).catch(() => ({}));
      const post = bucket[w];
      if (!post) continue;
      let doc = 0;
      for (const v of post) {
        doc += v >>> 1;
        const s = (v & 1 ? 3 : 10) * (w === term ? 1.3 : 1);
        if (s > (sc.get(doc) || 0)) sc.set(doc, s);
      }
    }
    if (!out) out = sc;
    else for (const [d, s] of out) { const t = sc.get(d); if (t) out.set(d, s + t); else out.delete(d); }
    if (!out.size) break;
  }
  return out || new Map();
}

export async function archiveCards(docs) {
  const A = await archiveInfo(), L = await latest();
  const blocks = Object.fromEntries(await Promise.all([...new Set(docs.map(d => Math.floor(d / A.block)))].map(async b => [b, await get(`/v/${A.v}/c/${b}.json`)])));
  return docs.map(d => { const [id, t, a, ind, year, k] = blocks[Math.floor(d / A.block)][d % A.block]; return { doc: d, id, t, a, ind: L.fields[ind], year, k: k || "" }; });
}

const AKIND = { S: ["Expired design", "expired", "Granted", "Design"], A: ["Likely abandoned", "abandoned", "Published", "Application"], "": ["Expired, full term", "expired", "Granted", "Full term"],
  E: ["Expired, Europe", "expired", "Published", "European"], CA: ["Expired, Canada", "expired", "Year", "Canadian"],
  AU: ["Expired, Australia", "expired", "Year", "Australian"] };
export function archiveCardHTML(c, names) {
  const n = numberLabel(c.id), owner = c.a || (c.k === "A" ? "Inventors" : "Solo inventor"), K = AKIND[c.k] || AKIND[""];
  // archive patents have no drawing on file, so their cards show their field's symbol in a blueprint frame
  return `<article class="card acard" data-id="${esc(c.id)}">${plateHTML(c.ind, n, `${c.id.slice(0, 2)} · no drawing`, `<span class="badge ${K[1]}">${K[0]}</span>`)}`
    + `<div class="cbody"><span class="fieldname">${esc(names[c.ind] || c.ind)} · <span class="num-id">${esc(n)}</span></span><h3><a href="/patents/${esc(c.id)}/">${esc(c.t)}</a></h3></div>`
    + `<div class="cmeta"><div><small>${K[2]}</small><span>${c.year}</span></div><div><small>Kind</small><span>${K[3]}</span></div><div><small>Owner</small><span title="${esc(owner)}">${esc(owner)}</span></div></div></article>`;
}
