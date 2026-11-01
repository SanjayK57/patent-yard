// All patents: search every application worldwide (pipeline/world.py). The browser reads the search index straight
// from the cards project; the cards for a page come from /api/cards, which slices them out of their packs.
// Docs are numbered newest first, so matching docs in increasing order are the newest matches.
import { $, $$, esc } from "./app.js";
import { words, crc32, latest, plateHTML } from "./catalog.js";

const W = window.PY_CONFIG.world;
const grid = $("#wgrid"), count = $("#wcount"), more = $("#wmore"), q = $("#wq"), cc = $("#wcc"), free = $("#wfree"), fld = $("#wfld"), y1 = $("#wy1"), y2 = $("#wy2");
const params = new URLSearchParams(location.search);
const S = { q: params.get("q") || "", cc: params.get("cc") || "", free: params.get("free") === "1", type: params.get("type") || "", fld: params.get("field") || "",
  y1: params.get("from") || "", y2: params.get("to") || "" };
const SPECIAL = { EP: "Europe (EPO)", SU: "Soviet Union", CS: "Czechoslovakia", DD: "East Germany", YU: "Yugoslavia", EA: "Eurasian Patent Office",
  AP: "ARIPO (Africa)", OA: "OAPI (Africa)", GC: "Gulf Cooperation Council", WO: "WIPO" };
const regions = new Intl.DisplayNames(["en"], { type: "region" });
const country = c => SPECIAL[c] || (() => { try { return regions.of(c); } catch { return c; } })();
let meta, kidx = {}, years = {}, names, fields, stop, docs = null, span = null, pos = 0, seq = 0;  // docs: matching docs, or null for every doc in span (null: all)

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
  const out = new Array(e[2]), d = b.data;
  out.cut = !!e[3];
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
  if (!filterLists.has(key)) filterLists.set(key, fetch(`${W.cards}/k/${encodeURIComponent(key)}.bin`).then(r => (r.ok ? r.arrayBuffer() : Promise.reject())).then(gunzip).then(varints)
    .then(l => Object.assign(l, { cut: !!kidx[key][1] })));
  return filterLists.get(key);
}
const union = (a, b) => { const out = []; for (let i = 0, j = 0; i < a.length || j < b.length;) { const x = j >= b.length || (i < a.length && a[i] <= b[j]) ? a[i++] : b[j++]; if (out[out.length - 1] !== x) out.push(x); } return out; };
function intersect(lists) {
  lists = [...lists].sort((a, b) => a.length - b.length);
  return lists.slice(1).reduce((cur, l) => { const out = []; let j = 0; for (const d of cur) { while (l[j] < d) j++; if (l[j] === d) out.push(d); } return out; }, lists[0]);
}

const num = id => { const [c, n, k] = id.split("-"); return `${c} ${n}${k ? " " + k : ""}`; };
function cardHTML(line) {
  const [id, t, a, date, c, kind, flags, field] = line.split("\t");
  // a US grant may carry a term adjustment for USPTO delay (functions/_world.js pastTerm); within 20 years of grant it may be in force
  const past = +flags & 1 && !(c === "US" && Date.parse(`${+date.slice(0, 4) + 20}${date.slice(4)}`) > Date.now());
  // kind codes B, C, E and S are granted patents and U a registered utility model in most offices, even without the flag
  const granted = +flags & 2 || /^[BCES]/.test(kind), utility = /^U/.test(kind);
  const badge = `<span class="badge ${past ? "expired" : "plain"}">${past ? "Past its term" : utility ? "Registered" : granted ? "Granted" : "Application"}</span>`;
  return `<article class="card acard" data-id="${esc(id)}">${plateHTML(fields[+field] || "other", num(id), `${c} · ${date.slice(0, 4)}`, badge)}`
    + `<div class="cbody"><span class="fieldname">${esc(country(c))} · ${esc(names[fields[+field]] || "")}</span><h3><a href="/patents/${esc(id)}/">${esc(t)}</a></h3><span class="tstat">${badge}</span></div>`
    + `<div class="cmeta"><div><small>Published</small><span>${esc(date.slice(0, 4))}</span></div><div><small>Kind</small><span>${esc(kind)}</span></div><div><small>Assignee</small><span title="${esc(a)}">${esc(a || "—")}</span></div></div></article>`;
}

// a patent number goes straight to its page, in Google Patents' form CC-NUMBER-KIND: "CN 112345678 A", "JP2005-123456A",
// "KR 10-2020-0012345", "US 2020/0123456 A1", "DE 10 2020 123 456 A1", "USD900000S". Only for offices in the data, so a
// model name like "MP3000" stays a search.
function numberPath(s) {
  const m = s.trim().toUpperCase().replace(/[\s,./]/g, "").replace(/(\d)-(?=\d)/g, "$1").match(/^([A-Z]{2})-?([A-Z]{0,2}\d{4,})-?([A-Z]\d?)?$/);
  if (!m || !meta?.countries[m[1]]) return null;
  let [, cc, num, kind] = m;
  if (cc === "KR" && /^[12]0\d{11}$/.test(num)) num = num.slice(2);  // KIPO's 10- (patent) or 20- (utility model) prefix isn't in Google's number
  if (cc === "US" && /^(19|20)\d\d0\d{6}$/.test(num)) num = num.slice(0, 4) + num.slice(5);  // US 2026/0281245 is US-2026281245 there
  return `/patents/${cc}-${num}${kind ? "-" + kind : ""}`;
}

async function page(my) {
  const [lo, hi] = span || [0, meta.n], end = docs ? docs.length : hi - lo;
  const batch = docs ? docs.slice(pos, pos + 24) : Array.from({ length: Math.max(0, Math.min(24, end - pos)) }, (_, k) => lo + pos + k);
  pos += batch.length;
  // a free Worker gets 10 ms of CPU, so each call opens at most 4 packs (about 5 ms); the calls run side by side
  const calls = [];
  for (const d of batch) {
    const p = Math.floor(d / meta.per), last = calls[calls.length - 1];
    if (last && (last.packs.has(p) || last.packs.size < 4)) { last.packs.add(p); last.docs.push(d); } else calls.push({ packs: new Set([p]), docs: [d] });
  }
  const rows = (await Promise.all(calls.map(c => fetch(`/api/cards?d=${c.docs.join(",")}`).then(r => r.json()).catch(() => [])))).flat();
  if (my !== seq) return;
  grid.insertAdjacentHTML("beforeend", rows.map(([, line]) => cardHTML(line)).join(""));
  more.hidden = pos >= end;
}

// One list per country / past-term / type combination, because two lists cut to their newest docs can't be
// intersected exactly; a field has its own list. A year range is one exact span of docs (numbered newest first).
const mainKey = () => { const k = [S.cc || "all", S.free && "free", S.type].filter(Boolean).join("-"); return k === "all" ? null : k; };
const fieldKey = () => S.fld && `fld-${S.fld}${S.free ? "-free" : ""}`;
function yearSpan() {
  if (!S.y1 && !S.y2) return null;
  const rs = Object.entries(years).filter(([y]) => (!S.y1 || y >= S.y1) && (!S.y2 || y <= S.y2)).map(([, r]) => r);
  return rs.length ? [Math.min(...rs.map(r => r[0])), Math.max(...rs.map(r => r[1]))] : [0, 0];
}
const fmt = n => n.toLocaleString("en-US");
const noun = n => (S.type === "g" ? `granted or registered ${n === 1 ? "record" : "records"}` : S.type === "a" ? (n === 1 ? "application" : "applications") : n === 1 ? "record" : "records");
function describe() {
  const yrs = S.y1 && S.y2 ? (S.y1 === S.y2 ? `in ${S.y1}` : `${S.y1} to ${S.y2}`) : S.y1 ? `in ${S.y1} or later` : S.y2 ? `in ${S.y2} or earlier` : "";
  return [S.cc && `from ${country(S.cc)}`,
    S.fld && `in ${names[S.fld] || S.fld}`, S.free && "filed 20+ years ago", yrs && `first published ${yrs}`].filter(Boolean).join(", ");
}

async function run() {
  const my = ++seq;
  pos = 0; grid.innerHTML = ""; more.hidden = true;
  const p = new URLSearchParams();
  for (const [k, v] of [["q", S.q], ["cc", S.cc], ["free", S.free && "1"], ["type", S.type], ["field", S.fld], ["from", S.y1], ["to", S.y2]]) if (v) p.set(k, v);
  history.replaceState(null, "", location.pathname + (p.size ? "?" + p : ""));
  const ws = [...new Set(words(S.q))].filter(w => !stop.has(w));
  if (S.q.trim() && !ws.length) { count.textContent = `“${S.q.trim()}” is too common to search by. Add a more specific word.`; return; }
  count.textContent = "Searching…";
  let main = mainKey();
  const fk = fieldKey();
  if (fk && main === "all-free") main = null;  // the field's list already holds only patents past their term
  const keys = [main, fk].filter(Boolean), what = describe(), q_ = S.q.trim();
  span = yearSpan();
  if (keys.some(k => !kidx[k]) || (span && span[0] === span[1])) { docs = []; count.textContent = `No ${noun(2)} ${what} in the data.`; return; }
  // "past their term" searches the f/ index. A country of mostly old patents needs it too, since the s/ index keeps only the
  // newest docs of a common word; without the filter its few in-force patents come from s/, so each word gets both, merged
  const old = S.cc && (kidx[`${S.cc}-free`]?.[0] || 0) / (kidx[S.cc]?.[0] || 1) > 0.9;
  const word = w => (S.free ? postings(w, "f") : old ? Promise.all([postings(w, "s"), postings(w, "f")]).then(([a, b]) => Object.assign(union(a, b), { cut: a.cut && b.cut })) : postings(w, "s"));
  const lists = await Promise.all([...ws.map(word), ...keys.map(filterList)]).catch(() => null);
  if (my !== seq) return;
  if (!lists) { docs = []; count.textContent = "The search index didn't load. Try again."; return; }
  docs = lists.length ? intersect(lists) : null;
  if (docs && span) docs = docs.filter(d => d >= span[0] && d < span[1]);
  // a cut list holds only the docs newer than its last one; matches older than the newest such edge can be missing
  const edge = Math.min(...lists.filter(l => l.cut && l.length).map(l => l[l.length - 1]));
  const missing = Number.isFinite(edge) && (span ? span[1] - 1 > edge : true);
  const n = docs ? docs.length : span ? span[1] - span[0] : meta.n;
  const single = !ws.length && keys.length === 1 && !span;
  const newest = `newest ${fmt(meta.cap)}`;
  if (single) count.textContent = `${fmt(kidx[keys[0]][0])} ${noun(2)}${what ? " " + what : ""}${kidx[keys[0]][1] ? `; showing the ${newest}` : ""}, newest first.`;
  else if (!n && missing) count.textContent = `No matches in reach. A common word or a big filter keeps only its ${newest} records, and none of them are ${[S.type === "g" ? "granted" : S.type === "a" ? "applications" : "", what].filter(Boolean).join(", ") || "this old"}. Search with a more specific word, or remove a filter.`;
  else count.textContent = `${missing ? "At least " : ""}${fmt(n)} ${noun(n)}${q_ ? ` ${n === 1 ? "matches" : "match"} “${q_}”` : ""}${what ? ` ${what}` : !q_ ? " worldwide" : ""}, newest first.`
    + (missing ? ` A common word or a big filter keeps only its ${newest} records, so older matches can be missing.` : "");
  if (!n && !missing) count.textContent += " Try fewer words or filters.";
  await page(my);
}

const pressType = () => $$("[data-type]").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.type === S.type)));
(async () => {
  try {
    [meta, { names, fields }, kidx, years] = await Promise.all([fetch(`${W.cards}/meta.json`).then(r => r.json()), latest(),
      fetch(`${W.cards}/k/index.json`).then(r => (r.ok ? r.json() : {})).catch(() => ({})), fetch(`${W.cards}/k/years.json`).then(r => (r.ok ? r.json() : {})).catch(() => ({}))]);
  }
  catch { count.textContent = "All patents didn't load. Reload to try again."; return; }
  stop = new Set(meta.stop);
  cc.insertAdjacentHTML("beforeend", Object.entries(meta.countries).slice(0, 60).map(([c, n]) => `<option value="${esc(c)}">${esc(country(c))} (${n.toLocaleString("en-US")})</option>`).join(""));
  // filters the index doesn't have yet (an older cards deploy) stay hidden rather than promise what they can't do
  const flds = fields.filter(f => kidx[`fld-${f}`]);
  fld.insertAdjacentHTML("beforeend", flds.map(f => `<option value="${esc(f)}">${esc(names[f] || f)}</option>`).join(""));
  fld.closest(".frow").hidden = !flds.length;
  $("[data-type]").closest(".frow").hidden = !kidx["all-g"];
  const ys = Object.keys(years).sort().reverse(), opts = ys.map(y => `<option>${y}</option>`).join("");
  y1.insertAdjacentHTML("beforeend", opts); y2.insertAdjacentHTML("beforeend", opts);
  y1.closest(".frow").hidden = !ys.length;
  q.value = S.q; cc.value = S.cc; fld.value = S.fld; y1.value = S.y1; y2.value = S.y2; free.setAttribute("aria-pressed", String(S.free)); pressType();
  let t;
  $("#wfilters").addEventListener("submit", e => { e.preventDefault(); const path = numberPath(q.value); if (path) location.href = path; else { S.q = q.value; run(); } });
  q.addEventListener("input", () => { clearTimeout(t); t = setTimeout(() => { if (!numberPath(q.value)) { S.q = q.value; run(); } }, 250); });
  cc.addEventListener("change", () => { S.cc = cc.value; run(); });
  fld.addEventListener("change", () => { S.fld = fld.value; run(); });
  for (const [el, k] of [[y1, "y1"], [y2, "y2"]]) el.addEventListener("change", () => {
    S[k] = el.value;
    if (S.y1 && S.y2 && S.y1 > S.y2) { [S.y1, S.y2] = [S.y2, S.y1]; y1.value = S.y1; y2.value = S.y2; }  // "from 2010 to 1990" means 1990 to 2010
    run();
  });
  $("#wfilters").addEventListener("click", e => { const b = e.target.closest("[data-type]"); if (b) { S.type = b.dataset.type; pressType(); run(); } });
  const tg = $("#wToggle");
  tg.addEventListener("click", () => { const open = $("#wfilters").classList.toggle("open"); tg.setAttribute("aria-expanded", String(open)); });
  free.addEventListener("click", () => { S.free = !S.free; free.setAttribute("aria-pressed", String(S.free)); run(); });
  more.addEventListener("click", async () => { more.disabled = true; await page(seq); more.disabled = false; });
  run();
})();
