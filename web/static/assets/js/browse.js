// Browse and field pages: search, filters and sorting over the whole register, drawn from the catalog
// (catalog.js) one page of cards at a time. The server-rendered first page shows until the catalog is ready.
// State lives in the URL (?q=&field=&status=&build=&fig=1&solo=1&free=1&sort=) so filtered views can be shared.
// ?in=archive searches the archive instead: millions of US, European, Canadian and Australian patents past their term, with its own index, newest first.
import { $, $$, getSettings, reservations, markCards } from "./app.js";
import { latest, keys, search, cards, cardHTML, skeletons, patentNumber, archiveSearch, archiveTerms, archiveCards, archiveCardHTML } from "./catalog.js";

const grid = $("#grid");
const fixedField = $("[data-field]")?.dataset.field || "";
const params = new URLSearchParams(location.search);
const ARCH = !fixedField && params.get("in") === "archive";
const PAGE = ARCH ? 24 : 48;  // archive cards come from larger files, so fewer at a time
const S = {
  q: params.get("q") || "", ind: fixedField || params.get("field") || "", st: params.get("status") || "", b: params.get("build") || "",
  fig: params.get("fig") === "1", solo: params.get("solo") === "1", free: params.get("free") === "1", sort: params.get("sort") || "",
  reg: params.get("region") || "",
};
let K, L, A, scores = null, list = [], shown = 0, seq = 0, resMap = new Map();
// the archive is ordered by region (latest.json archive.spans: [name, first, end]), so a region is one index range
const span = () => (S.reg && A?.spans?.find(s => s[0] === S.reg)) || [S.reg, 0, A?.n || 0];
const total = () => (ARCH && !scores ? span()[2] - span()[1] : list.length);  // the archive without a query: every patent, newest first
const slice = (from, to) => (ARCH && !scores ? Array.from({ length: Math.max(0, Math.min(to, total()) - from) }, (_, k) => span()[1] + from + k) : list.slice(from, to));
const place = () => (!S.reg ? "the US, Europe, Canada and Australia" : S.reg === "US" ? "the US" : S.reg);
const sortBy = () => S.sort || (S.q.trim() ? "relevance" : getSettings().sort || "build");
const CMP = {
  relevance: (a, b) => scores.get(b) - scores.get(a) || a - b,
  build: (a, b) => a - b,  // catalog order is the recommended order
  recent: (a, b) => K.freed[b] - K.freed[a] || a - b,
  added: (a, b) => K.added[b] - K.added[a] || a - b,
  old: (a, b) => (K.filed[a] || 65535) - (K.filed[b] || 65535) || a - b,
};
const isDefault = () => !S.q.trim() && !S.st && !S.b && !S.fig && !S.solo && !S.free && sortBy() === "build" && (!!fixedField || !S.ind);

function compute() {
  if (ARCH) { const [, lo, hi] = span(); list = scores ? [...scores.keys()].filter(i => i >= lo && i < hi).sort((a, b) => scores.get(b) - scores.get(a) || a - b) : []; return; }
  const fi = S.ind ? L.fields.indexOf(S.ind) : -1, si = ["lapsed", "expired", "abandoned"].indexOf(S.st), bmax = +S.b || 0;
  const ok = d => (fi < 0 || K.field[d] === fi) && (si < 0 || (K.flags[d] & 3) === si) && (!bmax || (K.build[d] && K.build[d] <= bmax))
    && (!S.fig || K.flags[d] & 8) && (!S.solo || K.flags[d] & 4);
  list = scores ? [...scores.keys()].filter(ok) : [];
  if (!scores) for (let d = 0; d < K.n; d++) if (ok(d)) list.push(d);
  const by = sortBy();
  list.sort(CMP[by === "relevance" && !scores ? "build" : by]);
}

async function page(from, to, my) {
  const data = await (ARCH ? archiveCards : cards)(slice(from, to));
  if (my !== seq) return null;
  return data.filter(c => !(S.free && resMap.has(c.id)));
}

async function render() {
  const my = ++seq;
  shown = Math.min(PAGE, total());
  const n = total().toLocaleString("en-US");
  $("#count").textContent = ARCH
    ? (scores ? `${n} ${total() === 1 ? "match" : "matches"} for “${S.q.trim()}” in the archive` : `${n} patents from ${place()} past their term, newest first`)
    : S.q.trim() ? `${n} ${list.length === 1 ? "match" : "matches"} for “${S.q.trim()}”` : `${n} of ${K.n.toLocaleString("en-US")} patents`;
  $("#empty").hidden = total() > 0;
  $("#more").hidden = total() <= shown;
  const slow = setTimeout(() => my === seq && (grid.innerHTML = skeletons(Math.min(12, shown || 12))), 160);
  grid.classList.add("busy");
  const data = await page(0, shown, my).finally(() => clearTimeout(slow));
  if (!data) return;
  grid.classList.remove("busy");
  grid.innerHTML = data.map((c, i) => (ARCH ? archiveCardHTML(c, L.names) : cardHTML(c, L.names, i))).join("");
  grid.classList.remove("enter"); void grid.offsetWidth; grid.classList.add("enter");
  markCards(resMap, grid);
  moreLabel();
}

function moreLabel() {
  $("#more").hidden = total() <= shown;
  $("#more").textContent = `Show ${Math.min(PAGE, total() - shown).toLocaleString("en-US")} more`;
}

const toggle = $("#fToggle");
toggle.addEventListener("click", () => { if (wide.matches) return sidebar(!$(".workspace").classList.contains("fclosed")); const open = $("#filters").classList.toggle("open"); toggle.setAttribute("aria-expanded", String(open)); });
// wide screens: the same button folds the filter sidebar away (remembered in this browser); phones: it opens the sheet
const wide = matchMedia("(min-width: 901px)");
function sidebar(closed, keep = true) {
  $(".workspace").classList.toggle("fclosed", closed);
  toggle.setAttribute("aria-expanded", String(wide.matches ? !closed : $("#filters").classList.contains("open")));
  if (keep) try { localStorage.setItem("patentyard.filters", closed ? "closed" : "open"); } catch {}
}
try { sidebar(localStorage.getItem("patentyard.filters") === "closed", false); } catch { sidebar(false, false); }
wide.addEventListener("change", () => sidebar($(".workspace").classList.contains("fclosed"), false));
// phones: the filters open as a sheet; "Show results" closes it. "Reset" starts over with the same collection.
$("#fDone")?.addEventListener("click", () => { $("#filters").classList.remove("open"); toggle.setAttribute("aria-expanded", "false"); grid.scrollIntoView({ block: "start" }); });
$("#fReset")?.addEventListener("click", () => { location.href = location.pathname + (ARCH ? "?in=archive" : ""); });
function syncUrl() {
  const active = [!fixedField && S.ind, S.st, S.b, S.fig, S.solo, S.free].filter(Boolean).length;
  toggle.textContent = active ? `Filters · ${active}` : "Filters";
  const p = new URLSearchParams();
  if (ARCH) p.set("in", "archive");
  if (ARCH && S.reg) p.set("region", S.reg);
  if (S.q) p.set("q", S.q);
  if (S.ind && !fixedField) p.set("field", S.ind);
  if (S.st) p.set("status", S.st);
  if (S.b) p.set("build", S.b);
  if (S.fig) p.set("fig", "1");
  if (S.solo) p.set("solo", "1");
  if (S.free) p.set("free", "1");
  if (S.sort) p.set("sort", S.sort);
  history.replaceState(null, "", location.pathname + (p.size ? "?" + p : ""));
}

async function update({ research = false } = {}) {
  if (!K) return;
  if (research) {
    const num = patentNumber(S.q);
    if (num) { location.href = `/patents/${num}`; return; }
    if (ARCH) {
      const terms = S.q.trim() ? await archiveTerms(S.q) : [];
      scores = terms.length ? await archiveSearch(S.q) : null;
      if (S.q.trim() && !terms.length) { $("#count").textContent = `“${S.q.trim()}” is too common to search the archive by. Add a more specific word.`; syncUrl(); return; }
    } else scores = S.q.trim() ? await search(S.q) : null;
  }
  compute();
  syncUrl();
  await render();
  if (!ARCH) archiveHint();
}

// "Also 1,234 matches in the full-term archive"
async function archiveHint() {
  const box = $("#archHint"), q_ = S.q.trim(), my = seq;
  if (!box || !q_ || !A?.n) { if (box) box.hidden = true; return; }
  const n = (await archiveSearch(q_).catch(() => new Map())).size;
  if (my !== seq) return;
  box.hidden = !n;
  box.innerHTML = `<span>Also <b>${n.toLocaleString("en-US")}</b> ${n === 1 ? "match" : "matches"} among patents from the US, Europe, Canada and Australia in the archive.</span><a href="/browse/?in=archive&q=${encodeURIComponent(q_)}">Search the archive →</a>`;
}

// ---------------------------------------------------------------- controls
function group(sel, key) {
  for (const b of $$(sel)) {
    b.setAttribute("aria-pressed", String(b.dataset[key] === S[key]));
    b.addEventListener("click", () => {
      $$(sel).forEach(x => x.setAttribute("aria-pressed", String(x === b)));
      S[key] = b.dataset[key]; update();
    });
  }
}
group("#filters [data-ind]", "ind"); group("#filters [data-st]", "st"); group("#filters [data-b]", "b"); group("#filters [data-reg]", "reg");
for (const [id, key] of [["#fFig", "fig"], ["#fSolo", "solo"], ["#fFree", "free"]]) {
  const b = $(id); b.setAttribute("aria-pressed", String(S[key]));
  b.addEventListener("click", () => { S[key] = !S[key]; b.setAttribute("aria-pressed", String(S[key])); update(); });
}
const q = $("#q"), sort = $("#sort");
q.value = S.q; sort.value = sortBy() in CMP ? sortBy() : "build";
$("#filters").addEventListener("submit", e => { e.preventDefault(); clearTimeout(t); S.q = q.value; update({ research: true }); });
let t;
q.addEventListener("input", () => {
  clearTimeout(t);
  t = setTimeout(() => {
    S.q = q.value;
    if (!S.sort) sort.value = sortBy();
    if (!patentNumber(S.q)) update({ research: true });
  }, 180);
});
sort.addEventListener("change", () => { S.sort = sort.value; update(); });
$("#more").addEventListener("click", async e => {
  const btn = e.currentTarget, my = seq, from = shown;
  btn.disabled = true; btn.classList.add("loading");
  shown = Math.min(total(), shown + PAGE);
  const data = await page(from, shown, my);
  btn.disabled = false; btn.classList.remove("loading");
  if (!data) return;
  grid.insertAdjacentHTML("beforeend", data.map((c, i) => (ARCH ? archiveCardHTML(c, L.names) : cardHTML(c, L.names, 9 + i))).join(""));
  markCards(resMap, grid);
  moreLabel();
});
const hq = $("#hq"); if (hq) hq.value = S.q;

// collections: recently freed (the register) or the full-term archive
for (const b of $$("#filters [data-coll]")) {
  b.setAttribute("aria-pressed", String((b.dataset.coll === "archive") === ARCH));
  b.addEventListener("click", () => {
    if ((b.dataset.coll === "archive") === ARCH) return;
    const p = new URLSearchParams();
    if (b.dataset.coll) p.set("in", "archive");
    if (q.value.trim()) p.set("q", q.value.trim());
    location.href = "/browse/" + (p.size ? "?" + p : "");
  });
}
if (ARCH) { $("#filters").classList.add("archive"); q.placeholder = "Search patents from the US, Europe, Canada and Australia"; }

// ---------------------------------------------------------------- start
(async () => {
  try { [L, K] = await Promise.all([latest(), keys()]); A = L.archive; }
  catch { $("#count").textContent = "Showing the first patents. Reload to search the whole register."; return; }
  if (ARCH && !A?.n) { $("#count").textContent = "The archive is still being built. Check back soon."; return; }
  if (ARCH) { grid.innerHTML = ""; return update({ research: true }); }
  reservations.then(m => { resMap = m; if (S.free) update(); });
  if (isDefault()) {  // the server-rendered page already shows this view
    compute();
    shown = Math.min(PAGE, list.length, $$(".card", grid).length);
    $("#count").textContent = `${list.length.toLocaleString("en-US")} of ${K.n.toLocaleString("en-US")} patents`;
    moreLabel();
  } else {
    await update({ research: !!S.q.trim() });
  }
})();
// phones: a placeholder that fits the field
if (matchMedia("(max-width: 520px)").matches) q.placeholder = ARCH ? "Search the archive" : "Search patents";
