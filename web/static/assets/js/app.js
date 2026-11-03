// Runs on every page: menu, account button, reservation marks on patent cards, and shared helpers.
import { backend } from "./backend.js";
import { card, esc, icon } from "./cards.js";
import { latest, topMatches, patentNumber, numberLabel, numLabel, randomPatent, STATUS, archiveSearch, archiveCards } from "./catalog.js";

// Best matches across both collections: the recently freed register first, then the archive fills up to n.
export async function bestMatches(q, n) {
  const hits = await topMatches(q, n).catch(() => []);
  if (hits.length >= n) return hits;
  const sc = await archiveSearch(q).catch(() => new Map());
  const top = [...sc].sort((a, b) => b[1] - a[1] || a[0] - b[0]).slice(0, n - hits.length).map(([d]) => d);
  const more = top.length ? (await archiveCards(top).catch(() => [])).map(c => ({ ...c, archive: true })) : [];
  return [...hits, ...more];
}
const label = p => numberLabel(p.id);
export { esc, icon };

export const $ = (s, el = document) => el.querySelector(s);
export const $$ = (s, el = document) => [...el.querySelectorAll(s)];
export const DAY = 864e5;
export const fmtDate = (s, o = { month: "short", day: "numeric", year: "numeric" }) => { const d = new Date(s); return isNaN(d) ? "" : d.toLocaleDateString("en-US", o); };
export const daysLeft = until => Math.max(0, Math.ceil((Date.parse(until) - Date.now()) / DAY));
// Small notices at the bottom of the screen. kind: "ok", "err" or "" (neutral); the icon follows the kind.
export function toast(msg, ms = 4600, kind) {
  const box = $("#toast"); if (!box) return;
  kind ??= /n't|not |couldn|error|try again|fail/i.test(msg) ? "err" : /^(saved|reserved|released|renewed|copied|sent|thanks|deleted|signed|welcome|link|prompt)/i.test(msg) ? "ok" : "";
  const el = document.createElement("div");
  el.className = "toast " + kind;
  el.innerHTML = `<span class="ti">${icon(kind === "err" ? "x" : kind === "ok" ? "check" : "spark")}</span><span></span>`;
  el.lastChild.textContent = msg;
  box.append(el);
  while (box.children.length > 3) box.firstChild.remove();
  setTimeout(() => { el.classList.add("out"); setTimeout(() => el.remove(), 260); }, ms);
}
// A notice to show on the next page (after a redirect), e.g. "Signed in".
export const flash = (msg, kind = "ok") => { try { sessionStorage.setItem("patentyard.flash", JSON.stringify([msg, kind])); } catch {} };
try {
  const f = JSON.parse(sessionStorage.getItem("patentyard.flash") || "null");
  if (f) { sessionStorage.removeItem("patentyard.flash"); setTimeout(() => toast(f[0], 4600, f[1]), 350); }
} catch {}
export async function copyText(text) {
  try { await navigator.clipboard.writeText(text); return true; }
  catch {
    const ta = Object.assign(document.createElement("textarea"), { value: text });
    ta.style.cssText = "position:fixed;opacity:0"; document.body.append(ta); ta.select();
    const ok = document.execCommand?.("copy"); ta.remove(); return !!ok;
  }
}
export const local = (k, v) => {
  try {
    if (v === undefined) return JSON.parse(localStorage.getItem("patentyard." + k) || "null");
    localStorage.setItem("patentyard." + k, JSON.stringify(v));
  } catch { return null; }
};
export const signInUrl = () => "/account/?next=" + encodeURIComponent(location.pathname + location.search);
// Where to go after signing in: only ever a page on this site (never "//x", "/\\x" or another origin).
export function safeNext(n, origin = location.origin) {
  if (!n) return "";
  try { const u = new URL(n, origin); return u.origin === origin && u.pathname !== "/account/" ? u.pathname + u.search + u.hash : ""; }
  catch { return ""; }
}

// ---------------------------------------------------------------- display settings (theme.js applies them before paint)
const SETTINGS = "settings";
export const getSettings = () => local(SETTINGS) || {};
export const saveSettings = patch => local(SETTINGS, { ...getSettings(), ...patch });
export function applySettings() {
  const s = getSettings(), d = document.documentElement;
  const set = (attr, on, v) => (on ? d.setAttribute(attr, v) : d.removeAttribute(attr));
  set("data-theme", s.theme === "light" || s.theme === "dark", s.theme);
  set("data-motion", s.motion === "reduce", "reduce");
  set("data-text", s.text === "large", "large");
  set("data-drawings", s.drawings === "inverted", "inverted");
}
export const isDark = () => { const t = document.documentElement.getAttribute("data-theme"); return t ? t === "dark" : matchMedia("(prefers-color-scheme: dark)").matches; };
export const reducedMotion = () => document.documentElement.getAttribute("data-motion") === "reduce" || matchMedia("(prefers-reduced-motion: reduce)").matches;
const themeBtn = $("#themeBtn");
const labelTheme = () => themeBtn?.setAttribute("aria-label", isDark() ? "Switch to light mode" : "Switch to dark mode");
// the switch cross-fades the whole page where the browser can (a view transition), and simply swaps where it can't
themeBtn?.addEventListener("click", () => {
  const flip = () => { saveSettings({ theme: isDark() ? "light" : "dark" }); applySettings(); labelTheme(); };
  if (!document.startViewTransition || reducedMotion()) return flip();
  const root = document.documentElement;
  root.classList.add("theming");
  document.startViewTransition(flip).finished.finally(() => root.classList.remove("theming"));
});
labelTheme();
matchMedia("(prefers-color-scheme: dark)").addEventListener?.("change", labelTheme);
addEventListener("storage", e => { if (e.key === "patentyard." + SETTINGS) { applySettings(); labelTheme(); } });  // other open tabs follow

// ---------------------------------------------------------------- a card drawing from Google Patents that doesn't load falls back to its field symbol (catalog.js)
addEventListener("error", e => { const f = e.target.closest?.(".gfig"); if (f) f.classList.add("failed"); }, true);

// ---------------------------------------------------------------- register totals in the footer (pages stay the same from day to day)
latest().then(L => {
  const el = $("#footStat");
  if (el && L.verified) el.textContent = `${L.count.toLocaleString("en-US")} recently lapsed or expired US patents · status last checked ${fmtDate(L.verified, { month: "long", day: "numeric", year: "numeric" })}`;
}).catch(() => {});

// ---------------------------------------------------------------- header shadow once the page scrolls, and sections that slide in
const top = $(".top");
const onScroll = () => top?.classList.toggle("scrolled", scrollY > 8);
addEventListener("scroll", onScroll, { passive: true }); onScroll();
const reveal = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { e.target.classList.add("in"); reveal.unobserve(e.target); } }), { rootMargin: "0px 0px -8% 0px" });
$$(".reveal").forEach(el => reveal.observe(el));
addEventListener("beforeprint", () => $$(".reveal").forEach(el => el.classList.add("in")));

// ---------------------------------------------------------------- menu
const menu = $("#menuBtn"), nav = $("#mainnav");
// the phone menu: opening moves focus to its first link, Escape or a click outside closes it and returns focus to the button
const setMenu = open => { nav.classList.toggle("open", open); menu.setAttribute("aria-expanded", open); if (open) $("a", nav)?.focus(); };
menu?.addEventListener("click", () => setMenu(!nav.classList.contains("open")));
addEventListener("keydown", e => { if (e.key === "Escape" && nav?.classList.contains("open")) { setMenu(false); menu.focus(); } });
addEventListener("click", e => { if (nav?.classList.contains("open") && !nav.contains(e.target) && !menu.contains(e.target)) setMenu(false); });

// ---------------------------------------------------------------- header search suggestions (Enter still opens the full results)
const hq = $("#hq");
if (hq) {
  const list = Object.assign(document.createElement("ul"), { className: "sugg", id: "hqList", hidden: true });
  list.setAttribute("role", "listbox");
  hq.closest("form").append(list);
  hq.setAttribute("aria-controls", "hqList"); hq.setAttribute("aria-autocomplete", "list"); hq.setAttribute("autocomplete", "off");
  let sel = -1;
  const items = () => $$("a", list);
  const mark = i => { sel = i; items().forEach((a, k) => a.setAttribute("aria-selected", String(k === i))); };
  let seqQ = 0, wait;
  hq.addEventListener("input", () => { clearTimeout(wait); wait = setTimeout(suggest, 140); });
  async function suggest() {
    const q = hq.value.trim(), my = ++seqQ;
    if (q.length < 2) { list.hidden = true; return; }
    const num = patentNumber(q);
    const all = `<li><a role="option" href="/browse/?q=${encodeURIComponent(q)}"><span>See all results</span>${icon("right")}</a></li>`
      + `<li><a role="option" href="/browse/?in=archive&q=${encodeURIComponent(q)}"><span>Search the archive: US, Europe, Canada, Australia</span>${icon("right")}</a></li>`
      + (window.PY_CONFIG?.world ? `<li><a role="option" href="/all/?q=${encodeURIComponent(q)}"><span>Search all patents worldwide</span>${icon("right")}</a></li>` : "");
    if (num) {
      list.innerHTML = `<li><a role="option" href="/patents/${num}"><span>Go to ${esc(numLabel(num))}</span>${icon("right")}</a></li>`;
      list.hidden = false; mark(-1); return;
    }
    list.classList.add("busy");
    const hits = await bestMatches(q, 6);
    if (my !== seqQ) return;
    list.classList.remove("busy");
    list.innerHTML = (hits.length ? hits.map(p => `<li><a role="option" href="/patents/${encodeURIComponent(p.id)}/"><span>${esc(p.t)}</span><small>${esc(label(p))}${p.archive ? ` · ${p.year}` : ""}</small></a></li>`).join("")
      : `<li class="none">No patents match “${esc(q)}”.</li>`) + all;
    list.hidden = false; mark(-1);
  }
  addEventListener("keydown", e => {  // "/" jumps to search, like most sites
    if (e.key === "/" && !(e.target instanceof Element && e.target.closest("input, textarea, select, [contenteditable]"))) { e.preventDefault(); ($("#heroQ") || $("#q") || $("#wq") || hq).focus(); }
  });
  hq.addEventListener("keydown", e => {
    const n = items().length;
    if (list.hidden || !n) return;
    if (e.key === "ArrowDown" || e.key === "ArrowUp") { e.preventDefault(); mark((sel + (e.key === "ArrowDown" ? 1 : n - 1)) % n); }
    else if (e.key === "Enter" && sel >= 0) { e.preventDefault(); location.href = items()[sel].href; }
    else if (e.key === "Escape") list.hidden = true;
  });
  document.addEventListener("click", e => { if (!e.target.closest(".hsearch")) list.hidden = true; });
}

// ---------------------------------------------------------------- account button: "Sign in", or a menu once signed in
export const session = (async () => {
  const b = await backend();
  if (!b) return { b: null, user: null };
  const user = await b.user().catch(() => null);
  const acct = $("#acct");
  if (acct && user) {
    const initial = (user.email || "?").trim().charAt(0).toUpperCase();
    acct.innerHTML = `<div class="acctmenu"><button type="button" aria-haspopup="menu" aria-expanded="false" aria-label="My bench, signed in as ${esc(user.email)}" title="${esc(user.email)}"><span class="avatar" aria-hidden="true">${esc(initial)}</span><span>My bench</span></button>
      <div class="menu" role="menu" hidden><div class="who"><b>Signed in</b><small>${esc(user.email)}</small></div>
      <a role="menuitem" href="/account/">${icon("flag")}My bench</a><a role="menuitem" href="/saved/">${icon("bookmark")}Saved patents</a><a role="menuitem" href="/studio/">${icon("spark")}Invention studio</a><a role="menuitem" href="/settings/">${icon("gear")}Settings</a>
      <button role="menuitem" type="button" data-signout>${icon("left")}Sign out</button></div></div>`;
    const btn = $(".acctmenu>button", acct), menu = $(".menu", acct);
    const open = v => { menu.hidden = !v; btn.setAttribute("aria-expanded", String(v)); if (v) $("a", menu).focus(); };
    btn.addEventListener("click", () => open(menu.hidden));
    document.addEventListener("click", e => { if (!e.target.closest(".acctmenu")) open(false); });
    menu.addEventListener("keydown", e => {
      const items = $$("[role=menuitem]", menu), i = items.indexOf(document.activeElement);
      if (e.key === "Escape") { open(false); btn.focus(); }
      if (e.key === "ArrowDown" || e.key === "ArrowUp") { e.preventDefault(); items[(i + (e.key === "ArrowDown" ? 1 : items.length - 1)) % items.length].focus(); }
    });
    $("[data-signout]", menu).addEventListener("click", async () => { await b.signOut(); flash("Signed out. See you soon."); location.href = "/"; });
  }
  return { b, user };
})();

// ---------------------------------------------------------------- reservations shown on cards
export const reservations = (async () => {
  const { b } = await session;
  if (!b) return new Map();
  try { return new Map((await b.reservations()).map(r => [r.patent_id, r])); }
  catch { return new Map(); }
})();

export function markCards(map, root = document) {
  decorateCards(root);
  for (const card of $$(".card[data-id]", root)) {
    card.querySelector(".resmark")?.remove();
    const r = map.get(card.dataset.id);
    card.dataset.res = r ? (r.mine ? "mine" : "other") : "";
    if (r) card.insertAdjacentHTML("beforeend", `<span class="resmark ${r.mine ? "mine" : ""}" role="img" aria-label="Reserved by ${esc(r.mine ? "you" : r.holder)}">${icon("flag")}Reserved${r.mine ? " by you" : ""}</span>`);
  }
  document.dispatchEvent(new CustomEvent("py:reservations"));
}
reservations.then(map => { if (map.size) markCards(map); });

// ---------------------------------------------------------------- saved patents and recently viewed (this browser only)
const LIST_MAX = { saved: 200, recent: 12 };
export const listOf = k => (local(k) || []).filter(x => x && x.id);
export const isSaved = id => listOf("saved").some(x => x.id === id);
export function remember(k, item) {  // newest first, no duplicates
  local(k, [item, ...listOf(k).filter(x => x.id !== item.id)].slice(0, LIST_MAX[k]));
}
export function toggleSave(item) {
  const on = !isSaved(item.id);
  if (on) remember("saved", { ...item, at: Date.now() }); else local("saved", listOf("saved").filter(x => x.id !== item.id));
  document.dispatchEvent(new CustomEvent("py:saved", { detail: { id: item.id, on } }));
  toast(on ? "Saved. Find it under Saved patents." : "Removed from your saved patents.", 3200, on ? "ok" : "");
  return on;
}
// what a card shows, read from the card itself
export function cardItem(card) {
  const img = card.querySelector(".fig img");
  return { id: card.dataset.id, t: card.querySelector("h3")?.textContent.trim(), n: card.querySelector(".num-id")?.textContent.trim(),
    st: ["lapsed", "expired", "abandoned"].find(x => card.querySelector(".over .badge." + x)) || "lapsed",
    fld: card.querySelector(".fieldname")?.firstChild?.textContent.replace(/·\s*$/, "").trim() || "", img: !!img };
}
export function miniCard(x) {
  return card({ id: x.id, href: `/patents/${x.id}/`, title: x.t, number: x.n, field: x.fld, status: { cls: x.st, label: STATUS[x.st] || "" },
    img: x.img ? `/img/p/${x.id}/1.png` : "", glyph: "other" });
}
// a bookmark on every card
export function decorateCards(root = document) {
  for (const card of $$(".card[data-id]:not(.skel)", root)) {
    if (card.querySelector(".savebtn")) continue;
    const on = isSaved(card.dataset.id);
    card.insertAdjacentHTML("beforeend", `<button class="savebtn" type="button" aria-pressed="${on}" aria-label="${on ? "Remove from saved" : "Save"}" title="${on ? "Saved" : "Save for later"}">${icon("bookmark")}</button>`);
  }
}
document.addEventListener("click", e => {
  const b = e.target.closest(".savebtn"); if (!b) return;
  e.preventDefault(); e.stopPropagation();
  const on = toggleSave(cardItem(b.closest(".card")));
  b.setAttribute("aria-pressed", String(on)); b.setAttribute("aria-label", on ? "Remove from saved" : "Save"); b.title = on ? "Saved" : "Save for later";
  b.classList.remove("pop"); void b.offsetWidth; b.classList.add("pop");
});
decorateCards();

// ---------------------------------------------------------------- "Surprise me"
export async function surprise(btn) {
  btn?.classList.add("loading");
  try { const p = await randomPatent(); location.href = `/patents/${p.id}/`; }
  catch { btn?.classList.remove("loading"); toast("Couldn't pick one just now. Try again.", 4000, "err"); }
}
document.addEventListener("click", e => { const b = e.target.closest("[data-surprise]"); if (b) surprise(b); });

// ---------------------------------------------------------------- numbers that strike into place digit by digit, never tweened
const counter = new IntersectionObserver(es => es.forEach(en => {
  if (!en.isIntersecting) return;
  counter.unobserve(en.target);
  const el = en.target, text = el.textContent;
  if (reducedMotion() || !/\d/.test(text)) return;
  el.classList.add("strike");
  el.innerHTML = [...text].map(c => (/\d/.test(c) ? `<i class="off">${c}</i>` : c)).join("");
  const digits = [...el.querySelectorAll("i")];
  digits.forEach((d, k) => setTimeout(() => d.classList.remove("off"), 90 + k * 55));
  setTimeout(() => { el.textContent = text; el.classList.remove("strike"); }, 160 + digits.length * 55);
}), { threshold: .4 });
$$("[data-count]").forEach(el => counter.observe(el));

// ---------------------------------------------------------------- a burst of confetti for good news (reserving a patent)
export function celebrate(x = innerWidth / 2, y = innerHeight / 3) {
  if (reducedMotion()) return;
  const cv = Object.assign(document.createElement("canvas"), { className: "confetti" });
  const dpr = Math.min(2, devicePixelRatio || 1);
  cv.width = innerWidth * dpr; cv.height = innerHeight * dpr; document.body.append(cv);
  const ctx = cv.getContext("2d"), css = getComputedStyle(document.documentElement);
  const colors = ["--mark", "--ink", "--line-strong", "--mark"].map(v => css.getPropertyValue(v).trim());
  const bits = Array.from({ length: 90 }, () => ({ x: x * dpr, y: y * dpr, vx: (Math.random() - .5) * 16 * dpr, vy: (-Math.random() * 13 - 4) * dpr,
    r: (3 + Math.random() * 4) * dpr, a: Math.random() * 6, va: (Math.random() - .5) * .4, c: colors[Math.floor(Math.random() * colors.length)] }));
  const t0 = performance.now();
  const frame = now => {
    const t = (now - t0) / 1400;
    ctx.clearRect(0, 0, cv.width, cv.height);
    for (const b of bits) {
      b.vy += .45 * dpr; b.x += b.vx; b.y += b.vy; b.vx *= .985; b.a += b.va;
      ctx.save(); ctx.globalAlpha = Math.max(0, 1 - t); ctx.translate(b.x, b.y); ctx.rotate(b.a); ctx.fillStyle = b.c; ctx.fillRect(-b.r, -b.r / 2, b.r * 2, b.r); ctx.restore();
    }
    if (t < 1) requestAnimationFrame(frame); else cv.remove();
  };
  requestAnimationFrame(frame);
}

// ---------------------------------------------------------------- command palette: ⌘K or Ctrl+K, or the search button on small screens
const PAGES = [["Browse the register", "/browse/", "search"], ...(window.PY_CONFIG?.world ? [["All patents worldwide", "/all/", "db"]] : []), ["Opportunities", "/opportunities/", "spark"], ["Fields", "/fields/", "sheet"], ["Insights", "/insights/", "chart"], ["Invention studio", "/studio/", "spark"],
  ["Saved patents", "/saved/", "bookmark"], ["My bench", "/account/", "flag"], ["Settings", "/settings/", "gear"], ["How it works", "/how-it-works/", "shield"], ["About", "/about/", "db"], ["Contact", "/contact/", "file"]];
let pal;
function palette() {
  if (pal) return pal;
  pal = Object.assign(document.createElement("dialog"), { id: "cmdk", className: "cmdk" });
  pal.setAttribute("aria-label", "Search and jump");
  pal.innerHTML = `<div class="cmdin">${icon("search")}<input id="cmdQ" type="search" autocomplete="off" placeholder="Search patents, or jump to a page" aria-label="Search patents, or jump to a page" aria-controls="cmdList"><kbd class="hk">esc</kbd></div><div id="cmdList" role="listbox" aria-label="Results"></div><div class="cmdfoot"><span><kbd class="hk">↑</kbd><kbd class="hk">↓</kbd> to move</span><span><kbd class="hk">↵</kbd> to open</span></div>`;
  document.body.append(pal);
  const q = $("#cmdQ", pal), list = $("#cmdList", pal);
  let sel = 0, seq = 0;
  const items = () => $$("[data-go], [data-act]", list);
  const mark = i => { const it = items(); if (!it.length) return; sel = (i + it.length) % it.length; it.forEach((x, k) => x.setAttribute("aria-selected", String(k === sel))); it[sel].scrollIntoView({ block: "nearest" }); };
  const row = (label, sub, ic, attr) => `<button type="button" role="option" ${attr}>${icon(ic)}<span>${esc(label)}</span>${sub ? `<small>${esc(sub)}</small>` : ""}</button>`;
  const group = (t, inner) => `<div role="group" aria-label="${esc(t)}"><div class="cmdh" aria-hidden="true">${esc(t)}</div>${inner}</div>`;
  async function draw() {
    const v = q.value.trim(), my = ++seq, lv = v.toLowerCase();
    const pages = PAGES.filter(([l]) => !lv || l.toLowerCase().includes(lv));
    const acts = [["Surprise me with a random patent", "act=surprise", "shuffle"], [`Switch to ${isDark() ? "light" : "dark"} mode`, "act=theme", isDark() ? "sun" : "moon"]].filter(([l]) => !lv || l.toLowerCase().includes(lv));
    let html = "";
    const num = patentNumber(v);
    if (num) html += group("Patent number", row(`Go to ${numLabel(num)}`, "", "right", `data-go="/patents/${num}"`));
    else if (v.length >= 2) html += group("Patents", `<div class="cmdh muted" aria-hidden="true" id="cmdBusy">Searching…</div>` + row(`Search the register for “${v}”`, "", "search", `data-go="/browse/?q=${encodeURIComponent(v)}"`)
      + row(`Search the archive for “${v}”`, "4 patent offices", "db", `data-go="/browse/?in=archive&q=${encodeURIComponent(v)}"`)
      + (window.PY_CONFIG?.world ? row(`Search all patents for “${v}”`, "worldwide, in force or not", "db", `data-go="/all/?q=${encodeURIComponent(v)}"`) : ""));
    if (pages.length) html += group("Pages", pages.map(([l, href, ic]) => row(l, "", ic, `data-go="${href}"`)).join(""));
    if (acts.length) html += group("Actions", acts.map(([l, a, ic]) => row(l, "", ic, `data-act="${a.split("=")[1]}"`)).join(""));
    list.innerHTML = html; mark(0);
    if (!num && v.length >= 2) {
      const hits = await bestMatches(v, 6);
      if (my !== seq) return;
      const busy = $("#cmdBusy", list);
      if (busy) busy.outerHTML = hits.length ? hits.map(p => row(p.t, label(p) + (p.archive ? ` · ${p.year}` : ""), "file", `data-go="/patents/${esc(p.id)}/"`)).join("") : `<div class="cmdh muted" aria-hidden="true">No patents match.</div>`;
      mark(0);
    }
  }
  function go(el) {
    if (!el) return;
    if (el.dataset.go) location.href = el.dataset.go;
    else if (el.dataset.act === "surprise") { pal.close(); surprise(); }
    else if (el.dataset.act === "theme") { saveSettings({ theme: isDark() ? "light" : "dark" }); applySettings(); labelTheme(); pal.close(); }
  }
  let t;
  q.addEventListener("input", () => { clearTimeout(t); t = setTimeout(draw, 120); });
  q.addEventListener("keydown", e => {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") { e.preventDefault(); mark(sel + (e.key === "ArrowDown" ? 1 : -1)); }
    else if (e.key === "Enter") { e.preventDefault(); go(items()[sel]); }
  });
  list.addEventListener("click", e => go(e.target.closest("[data-go], [data-act]")));
  list.addEventListener("pointermove", e => { const b = e.target.closest("[data-go], [data-act]"); if (b) mark(items().indexOf(b)); });
  pal.addEventListener("click", e => { if (e.target === pal) pal.close(); });
  pal.draw = draw;
  return pal;
}
export function openPalette() { const p = palette(); p.showModal(); $("#cmdQ", p).value = ""; p.draw(); $("#cmdQ", p).focus(); }
addEventListener("keydown", e => { if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") { e.preventDefault(); pal?.open ? pal.close() : openPalette(); } });
$("#cmdBtn")?.addEventListener("click", openPalette);

// ---------------------------------------------------------------- list, card or table view for result grids (site_ui/base.py VIEWTOG)
function setView(id, view) {
  const grid = document.getElementById(id);
  if (!grid) return;
  grid.classList.toggle("as-list", view === "list");
  grid.classList.toggle("as-table", view === "table");
  $$(`[data-for="${id}"]`).forEach(b => b.setAttribute("aria-pressed", String(b.dataset.view === view)));
}
$$(".viewtog").forEach(t => { const b = t.querySelector("[data-for]"); try { setView(b.dataset.for, localStorage.getItem("patentyard.view." + b.dataset.for) || b.closest(".viewtog").dataset.default || "list"); } catch {} });
document.addEventListener("click", e => {
  const b = e.target.closest("[data-view][data-for]");
  if (!b) return;
  setView(b.dataset.for, b.dataset.view);
  try { localStorage.setItem("patentyard.view." + b.dataset.for, b.dataset.view); } catch {}
});
