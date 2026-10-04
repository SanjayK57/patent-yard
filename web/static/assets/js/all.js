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
let meta, kidx = {}, names, fields, stop, docs = null, cut = false, pos = 0, seq = 0;  // docs: matching docs, or null for every patent; cut: a list kept only its newest docs

const gunzip = async b => new Uint8Array(await new Response(new Response(b).body.pipeThrough(new DecompressionStream("gzip"))).arrayBuffer());
// two search indexes: s/ over every patent, f/ over those past their term (in s/ a common word keeps only its newest
// docs, all recent, so "past their term" plus a common word needs f/)
const buckets = new Map();
function bucket(n, idx) {
  const key = `${idx}/${n}`;
  if (!buckets.has(key)) buckets.set(key, fetch(`${W.cards}/${key}.bin`).then(r => (r.ok ? r.arrayBuffer() : Promise.reject())).then(gunzip).then(u => {
    const len = new DataView(u.buffer, u.byteOffset).getUint32(0, true);
    return { head: JSON.parse(new TextDecoder().decode(u.subarray(4, 4 + len))), data: u.subarray(4 + len) };
  }));
  return buckets.get(key);
}
async function postings(w, idx) {  // word -> its docs, from varint steps
  const b = await bucket(crc32(w) % meta.buckets, idx), e = b.head[w];
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
// country and "past their term" filters: the newest docs of each, prepared by pipeline/world.py filters
const varints = d => { const out = []; for (let i = 0, prev = 0; i < d.length;) { let v = 0, s = 1, x; do { x = d[i++]; v += (x & 127) * s; s *= 128; } while (x & 128); out.push(prev += v); } return out; };
const filterLists = new Map();
function filterList(key) {
  if (!filterLists.has(key)) filterLists.set(key, fetch(`${W.cards}/k/${encodeURIComponent(key)}.bin`).then(r => (r.ok ? r.arrayBuffer() : Promise.reject())).then(gunzip).then(varints));
  return filterLists.get(key);
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
  const end = docs ? docs.length : meta.n, batch = docs ? docs.slice(pos, pos + 24) : Array.from({ length: Math.max(0, Math.min(24, end - pos)) }, (_, k) => pos + k);
  pos += batch.length;
  // a free Worker gets 10 ms of CPU, so each call opens at most 6 packs; the calls run side by side
  const calls = [];
  for (const d of batch) {
    const p = Math.floor(d / meta.per), last = calls[calls.length - 1];
    if (last && (last.packs.has(p) || last.packs.size < 6)) { last.packs.add(p); last.docs.push(d); } else calls.push({ packs: new Set([p]), docs: [d] });
  }
  const rows = (await Promise.all(calls.map(c => fetch(`/api/cards?d=${c.docs.join(",")}`).then(r => r.json()).catch(() => [])))).flat();
  if (my !== seq) return;
  grid.insertAdjacentHTML("beforeend", rows.map(([, line]) => cardHTML(line)).join(""));
  more.hidden = pos >= end;
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
  const key = S.cc ? (S.free ? `${S.cc}-free` : S.cc) : S.free ? "all-free" : null, k = key && kidx[key];
  if (k?.[1]) cut = true;
  const old = S.free || (S.cc && (kidx[`${S.cc}-free`]?.[0] || 0) / (kidx[S.cc]?.[0] || 1) > 0.9);  // a country of mostly old patents
  const lists = key && !k ? null : await Promise.all([...ws.map(w => postings(w, old ? "f" : "s")), ...(key ? [filterList(key)] : [])]).catch(() => null);
  if (my !== seq) return;
  if (!lists) { docs = []; count.textContent = `No patents ${[S.cc && `from ${country(S.cc)}`, S.free && "past their term"].filter(Boolean).join(", ")} in the data.`; return; }
  docs = lists.length ? intersect(lists) : null;
  const n = docs ? docs.length : meta.n, q_ = S.q.trim(), what = [S.cc && `from ${country(S.cc)}`, S.free && "past their term"].filter(Boolean).join(", ");
  const total = k ? k[0] : meta.n, newest = `newest ${meta.cap.toLocaleString("en-US")}`;
  count.textContent = (!ws.length ? (key ? `${total.toLocaleString("en-US")} patents ${what}${k[1] ? `; showing the ${newest}` : ""}, newest first.` : `${n.toLocaleString("en-US")} patents worldwide, newest first.`)
    : `${n.toLocaleString("en-US")} ${n === 1 ? "patent matches" : "patents match"} “${q_}”${what ? ` ${what}` : ""}, newest first.${cut ? ` A common word or a big filter keeps only its ${newest} patents, so older matches can be missing.` : ""}`);
  if (!n) count.textContent += " Try fewer words or filters.";
  await page(my);
}

(async () => {
  try { [meta, { names, fields }, kidx] = await Promise.all([fetch(`${W.cards}/meta.json`).then(r => r.json()), latest(), fetch(`${W.cards}/k/index.json`).then(r => (r.ok ? r.json() : {})).catch(() => ({}))]); }
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
