// All patents: search every application worldwide (pipeline/world.py). The browser reads the search index straight
// from the cards project; the cards for a page come from /api/cards, which slices them out of their packs.
// Docs are numbered newest first, so matching docs in increasing order are the newest matches.
import { $, esc } from "./app.js";
import { words, crc32, latest } from "./catalog.js";

const W = window.PY_CONFIG.world;
const grid = $("#wgrid"), count = $("#wcount"), more = $("#wmore"), q = $("#wq"), cc = $("#wcc"), free = $("#wfree");
const params = new URLSearchParams(location.search);
const S = { q: params.get("q") || "", cc: params.get("cc") || "", free: params.get("free") === "1" };
const SPECIAL = { EP: "Europe (EPO)", SU: "Soviet Union", CS: "Czechoslovakia", DD: "East Germany", YU: "Yugoslavia", EA: "Eurasian Patent Office",
  AP: "ARIPO (Africa)", OA: "OAPI (Africa)", GC: "Gulf Cooperation Council", WO: "WIPO" };
const regions = new Intl.DisplayNames(["en"], { type: "region" });
const country = c => SPECIAL[c] || (() => { try { return regions.of(c); } catch { return c; } })();
let meta, names, fields, stop, docs = null, cut = false, pos = 0, seq = 0;  // docs: matching docs, or null for every patent; cut: a word kept only its newest matches

const gunzip = async b => new Uint8Array(await new Response(new Response(b).body.pipeThrough(new DecompressionStream("gzip"))).arrayBuffer());
const buckets = new Map();
function bucket(n) {
  if (!buckets.has(n)) buckets.set(n, fetch(`${W.cards}/s/${n}.bin`).then(r => r.arrayBuffer()).then(gunzip).then(u => {
    const len = new DataView(u.buffer, u.byteOffset).getUint32(0, true);
    return { head: JSON.parse(new TextDecoder().decode(u.subarray(4, 4 + len))), data: u.subarray(4 + len) };
  }));
  return buckets.get(n);
}
async function postings(w) {  // word -> its docs, from varint steps
  const b = await bucket(crc32(w) % meta.buckets), e = b.head[w];
  if (!e) return [];
  if (e[3]) cut = true;
  const out = new Array(e[2]), d = b.data;
  for (let i = e[0], end = e[0] + e[1], prev = 0, k = 0; i < end; k++) {
    let v = 0, s = 1, x;
    do { x = d[i++]; v += (x & 127) * s; s *= 128; } while (x & 128);
    out[k] = prev += v;
  }
  return out;
}
function intersect(lists) {
  lists.sort((a, b) => a.length - b.length);
  return lists.slice(1).reduce((cur, l) => { const out = []; let j = 0; for (const d of cur) { while (l[j] < d) j++; if (l[j] === d) out.push(d); } return out; }, lists[0]);
}

const num = id => { const [c, n, k] = id.split("-"); return `${c} ${n}${k ? " " + k : ""}`; };
function cardHTML(line) {
  const [id, t, a, date, c, kind, flags, field] = line.split("\t"), past = +flags & 1, granted = +flags & 2;
  return `<article class="card acard" data-id="${esc(id)}"><div class="ahead"><span class="badge ${past ? "expired" : "plain"}">${past ? "Past its term" : granted ? "Granted" : "Application"}</span><span class="num-id">${esc(num(id))}</span></div>`
    + `<div class="cbody"><span class="fieldname">${esc(country(c))} · ${esc(names[fields[+field]] || "")}</span><h3><a href="/patents/${esc(id)}/">${esc(t)}</a></h3></div>`
    + `<div class="cmeta"><div><small>Published</small><span>${esc(date.slice(0, 4))}</span></div><div><small>Kind</small><span>${esc(kind)}</span></div><div><small>Owner</small><span title="${esc(a)}">${esc(a || "—")}</span></div></div></article>`;
}

// a patent number goes straight to its page: "CN 112345678 A", "JP2005-123456", "US 10,000,000 B2"
function numberPath(s) {
  const m = s.trim().toUpperCase().replace(/[\s,./]/g, "").match(/^([A-Z]{2})-?([A-Z]?\d{4,}[A-Z]?)-?([A-Z]\d?)?$/);
  return m ? `/patents/${m[1]}-${m[2].replace(/-/g, "")}${m[3] ? "-" + m[3] : ""}` : null;
}

async function page(my) {
  const shown = [], filtered = S.cc || S.free, step = filtered ? 40 : 24;
  for (let tries = 0; shown.length < 24 && tries < (filtered ? 10 : 1); tries++) {
    const end = docs ? docs.length : meta.n, batch = docs ? docs.slice(pos, pos + step) : Array.from({ length: Math.max(0, Math.min(step, end - pos)) }, (_, k) => pos + k);
    if (!batch.length) break;
    pos += batch.length;
    const rows = await fetch(`/api/cards?d=${batch.join(",")}`).then(r => r.json()).catch(() => []);
    if (my !== seq) return;
    for (const [, line] of rows) { const f = line.split("\t"); if ((!S.cc || f[4] === S.cc) && (!S.free || +f[6] & 1)) shown.push(line); }
  }
  grid.insertAdjacentHTML("beforeend", shown.map(cardHTML).join(""));
  more.hidden = pos >= (docs ? docs.length : meta.n);
  if (!grid.children.length) count.textContent += filtered ? " None of the newest matches fit the filters; try fewer filters." : "";
}

async function run() {
  const my = ++seq;
  pos = 0; grid.innerHTML = ""; more.hidden = true;
  const p = new URLSearchParams();
  if (S.q) p.set("q", S.q);
  if (S.cc) p.set("cc", S.cc);
  if (S.free) p.set("free", "1");
  history.replaceState(null, "", location.pathname + (p.size ? "?" + p : ""));
  const ws = [...new Set(words(S.q))].filter(w => !stop.has(w));
  if (S.q.trim() && !ws.length) { count.textContent = `“${S.q.trim()}” is too common to search by. Add a more specific word.`; return; }
  count.textContent = "Searching…";
  cut = false;
  docs = ws.length ? intersect(await Promise.all(ws.map(postings))) : null;
  if (my !== seq) return;
  const n = docs ? docs.length : meta.n, q_ = S.q.trim();
  const head = !docs ? `${n.toLocaleString("en-US")} patents worldwide, newest first`
    : cut ? `The newest matches for “${q_}”. A word in it is very common, so its newest ${meta.cap.toLocaleString("en-US")} patents are searched`
    : `${n.toLocaleString("en-US")} ${n === 1 ? "patent matches" : "patents match"} “${q_}”, newest first`;
  const only = [S.cc && `from ${country(S.cc)}`, S.free && "past their term"].filter(Boolean).join(", ");
  count.textContent = `${head}${only ? `. Showing those ${only}` : ""}.`;
  await page(my);
}

(async () => {
  try { [meta, { names, fields }] = await Promise.all([fetch(`${W.cards}/meta.json`).then(r => r.json()), latest()]); }
  catch { count.textContent = "All patents didn't load. Reload to try again."; return; }
  stop = new Set(meta.stop);
  cc.insertAdjacentHTML("beforeend", Object.entries(meta.countries).slice(0, 60).map(([c, n]) => `<option value="${esc(c)}">${esc(country(c))} (${n.toLocaleString("en-US")})</option>`).join(""));
  q.value = S.q; cc.value = S.cc; free.setAttribute("aria-pressed", String(S.free));
  let t;
  $("#wfilters").addEventListener("submit", e => { e.preventDefault(); const path = numberPath(q.value); if (path) location.href = path; else { S.q = q.value; run(); } });
  q.addEventListener("input", () => { clearTimeout(t); t = setTimeout(() => { if (!numberPath(q.value)) { S.q = q.value; run(); } }, 250); });
  cc.addEventListener("change", () => { S.cc = cc.value; run(); });
  free.addEventListener("click", () => { S.free = !S.free; free.setAttribute("aria-pressed", String(S.free)); run(); });
  more.addEventListener("click", async () => { more.disabled = true; await page(seq); more.disabled = false; });
  run();
})();
