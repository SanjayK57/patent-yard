// Patent page: drawing viewer, section highlighting, reservations and the Claude kit.
import { $, $$, esc, icon, toast, copyText, fmtDate, daysLeft, session, signInUrl, remember, isSaved, toggleSave, celebrate } from "./app.js";
import { mountKit, loadPatent, openClaude, briefButton } from "./kit.js";
import { latest } from "./catalog.js";

const P = $("#patent");
const id = P.dataset.id, nSheets = +P.dataset.sheets, total = +P.dataset.total, pdf = P.dataset.pdf;
const sheets = Array.from({ length: nSheets }, (_, k) => `/img/p/${id}/${k + 1}.png`);

// ---------------------------------------------------------------- drawing viewer: arrows, thumbnails, swipe, click to zoom and drag to pan
const V = { i: 0 }, viewer = $("#viewer");
function renderViewer() {
  viewer.innerHTML = `<div class="vbar"><span>${esc(P.dataset.n)} · Sheet ${V.i + 1} of ${sheets.length}${total > sheets.length ? ` (${total} in the PDF)` : ""}</span><span class="rowbtns"><a class="btn sm" href="${pdf}" target="_blank" rel="noopener noreferrer">USPTO PDF ${icon("ext")}</a><button class="x" type="button" data-close aria-label="Close viewer">${icon("x")}</button></span></div>
    <div class="stage" id="vStage"><img src="${sheets[V.i]}" alt="Drawing sheet ${V.i + 1}" data-zoom draggable="false"></div>
    <div class="vnav"><button class="btn sm" type="button" data-step="-1" ${V.i === 0 ? "disabled" : ""}>${icon("left")}Previous</button>
      <div class="vthumbs">${sheets.map((src, k) => `<button type="button" data-goto="${k}" aria-label="Sheet ${k + 1}" aria-current="${k === V.i}"><img src="${src}" alt=""></button>`).join("")}</div>
      <button class="btn sm" type="button" data-step="1" ${V.i >= sheets.length - 1 ? "disabled" : ""}>Next${icon("right")}</button></div>`;
}
const show = i => { V.i = Math.max(0, Math.min(sheets.length - 1, i)); renderViewer(); };
document.addEventListener("click", e => {
  const s = e.target.closest("[data-sheet]");
  if (s && sheets.length) { V.i = +s.dataset.sheet; renderViewer(); viewer.showModal(); }
});
let drag = null, moved = false;
viewer.addEventListener("click", e => {
  if (e.target === viewer || e.target.closest("[data-close]")) return viewer.close();
  const st = e.target.closest("[data-step]"), go = e.target.closest("[data-goto]");
  if (st) show(V.i + +st.dataset.step);
  if (go) show(+go.dataset.goto);
  if (e.target.closest("[data-zoom]") && !moved) $("#vStage").classList.toggle("zoom");
});
viewer.addEventListener("keydown", e => { if (["ArrowRight", "ArrowLeft"].includes(e.key)) show(V.i + (e.key === "ArrowRight" ? 1 : -1)); });
viewer.addEventListener("pointerdown", e => {
  const stage = e.target.closest("#vStage"); if (!stage) return;
  drag = { x: e.clientX, y: e.clientY, sl: stage.scrollLeft, st: stage.scrollTop, stage }; moved = false;
});
viewer.addEventListener("pointermove", e => {
  if (!drag) return;
  const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
  if (Math.abs(dx) + Math.abs(dy) > 6) moved = true;
  if (drag.stage.classList.contains("zoom")) { drag.stage.scrollLeft = drag.sl - dx; drag.stage.scrollTop = drag.st - dy; }
});
viewer.addEventListener("pointerup", e => {
  if (drag && !drag.stage.classList.contains("zoom") && Math.abs(e.clientX - drag.x) > 60) show(V.i + (e.clientX < drag.x ? 1 : -1));  // swipe
  drag = null; setTimeout(() => (moved = false), 0);
});

// ---------------------------------------------------------------- page furniture
const item = { id, t: $("h1").textContent.trim(), n: P.dataset.n, st: ["lapsed", "expired", "abandoned"].find(x => $(".phead .badge." + x)) || "lapsed",
  fld: $$(".crumbs a")[1]?.textContent.trim() || "", img: nSheets > 0 };
remember("recent", item);
const saveBtn = $("#saveBtn");
const paintSave = () => { const on = isSaved(id); saveBtn.setAttribute("aria-pressed", String(on)); $("span", saveBtn).textContent = on ? "Saved" : "Save"; };
saveBtn.addEventListener("click", () => { toggleSave(item); paintSave(); saveBtn.classList.remove("pop"); void saveBtn.offsetWidth; saveBtn.classList.add("pop"); });
paintSave();
const bar = Object.assign(document.createElement("div"), { className: "readbar" });
bar.setAttribute("aria-hidden", "true"); document.body.append(bar);
const readProgress = () => { const h = document.documentElement.scrollHeight - innerHeight; bar.style.transform = `scaleX(${h > 0 ? Math.min(1, scrollY / h) : 0})`; };
addEventListener("scroll", readProgress, { passive: true }); readProgress();
addEventListener("keydown", e => {  // [ and ] step through the field
  if (e.target.closest?.("input, textarea, select, [contenteditable]") || e.metaKey || e.ctrlKey || $("dialog[open]")) return;
  const a = e.key === "[" ? $(".pstep.prev") : e.key === "]" ? $(".pstep.next") : null;
  if (a) location.href = a.href;
});

// the page itself never changes from day to day; the date of the last check comes from the catalog
latest().then(L => {
  if (!L.verified || $("#patent").dataset.source) return;  // only the recently freed register is rechecked daily
  const vb = $("#vbadge");
  vb.innerHTML = `${icon("check")}Verified ${esc(fmtDate(L.verified, { month: "long", day: "numeric" }))}`; vb.hidden = false;
  $$(".vdate").forEach(el => (el.textContent = `, most recently on ${fmtDate(L.verified, { month: "long", day: "numeric", year: "numeric" })}`));
}).catch(() => {});

const unclamp = () => { const d = $("#desc"), b = $("#descMore"); if (d?.classList.contains("clamped")) { d.classList.remove("clamped"); b.textContent = "Show less"; b.setAttribute("aria-expanded", "true"); } };
document.addEventListener("click", e => { const a = e.target.closest(".jump a"); if (a) unclamp(); });
if (/^#d\d+$/.test(location.hash)) unclamp();
$("#descMore")?.addEventListener("click", e => {
  const d = $("#desc"), open = d.classList.toggle("clamped") === false;
  e.currentTarget.textContent = open ? "Show less" : "Read the full description";
  e.currentTarget.setAttribute("aria-expanded", open);
  if (!open) d.scrollIntoView({ block: "start" });
});
$("#copyLink").addEventListener("click", async e => {
  const btn = e.currentTarget, url = (window.PY_CONFIG?.siteUrl || location.origin) + location.pathname;
  if (await copyText(url)) {
    btn.innerHTML = `${icon("check")}Copied`; btn.classList.add("copied");
    setTimeout(() => { btn.innerHTML = `${icon("link")}Copy link`; btn.classList.remove("copied"); }, 1800);
  } else toast(url, 6000);
});
// "On this page": the section whose heading was passed last is the current one
const tocLinks = $$(".toc a"), secs = $$(".psec");
let ticking = false;
function spy() {
  ticking = false;
  let cur = secs[0];
  for (const s of secs) if (s.getBoundingClientRect().top <= 140) cur = s;
  if (innerHeight + scrollY >= document.documentElement.scrollHeight - 4) cur = secs[secs.length - 1];
  tocLinks.forEach(a => a.classList.toggle("on", a.getAttribute("href") === "#" + cur.id));
}
addEventListener("scroll", () => { if (!ticking) { ticking = true; requestAnimationFrame(spy); } }, { passive: true });
spy();

// ---------------------------------------------------------------- reservations
const btn = $("#reserveBtn"), line = $("#resline"), dlg = $("#resDlg");
async function refreshRes() {
  const { b, user } = await session;
  if (!b || $("#patent").dataset.noreserve) { btn.hidden = true; return; }  // nothing to reserve on a patent that may be in force
  let r;
  try { r = (await b.reservations()).find(x => x.patent_id === id); } catch { r = null; }
  btn.hidden = false; btn.disabled = false;
  btn.dataset.mode = !r ? "reserve" : r.mine ? (daysLeft(r.expires_at) <= 7 ? "renew" : "release") : "taken";
  btn.innerHTML = { reserve: `${icon("flag")}Reserve`, release: `${icon("flag")}Release`, renew: `${icon("flag")}Renew`, taken: `${icon("flag")}Reserved` }[btn.dataset.mode];
  btn.disabled = btn.dataset.mode === "taken";
  line.innerHTML = !r ? (user ? "" : `<span>Reserve it so other builders know you're on it. It doesn't stop anyone from using it.</span>`)
    : r.mine ? `<span class="badge ok">Reserved by you</span><span>until ${esc(fmtDate(r.expires_at))}${r.note ? ` · "${esc(r.note)}"` : ""}${btn.dataset.mode === "renew" ? ` · <button class="btn quiet sm" type="button" id="relNow">Release</button>` : ""}</span>`
    : `<span class="badge reserved">Reserved</span><span>by ${esc(r.holder)} until ${esc(fmtDate(r.expires_at))}${r.note ? ` · "${esc(r.note)}"` : ""}. You can still use it too.</span>`;
  $("#relNow")?.addEventListener("click", () => act("release"));
}
async function act(mode, note) {
  const { b } = await session;
  btn.disabled = true; btn.classList.add("loading");
  try {
    if (mode === "reserve") await b.reserve(id, note);
    else if (mode === "release") await b.release(id);
    else await b.renew(id);
    toast({ reserve: "Reserved for 30 days. It's on your bench. Others can still use the patent.", release: "Released. Other builders can reserve it now.", renew: "Renewed for another 30 days." }[mode], 4600, "ok");
    if (mode === "reserve") { const r = btn.getBoundingClientRect(); celebrate(r.left + r.width / 2, r.top + r.height / 2); }
  } catch (e) {
    toast({ taken: "Someone reserved it a moment before you.", limit: "You can hold 5 reservations at a time. Release one from your bench first.", not_signed_in: "Sign in to reserve.", too_early: "You can renew in the last 7 days of a hold." }[e.code] || "That didn't work. Try again.", 5200, "err");
  }
  btn.classList.remove("loading");
  await refreshRes();
}
btn.addEventListener("click", async () => {
  const { user } = await session;
  if (!user) return (location.href = signInUrl());
  if (btn.dataset.mode !== "reserve") return act(btn.dataset.mode);
  dlg.innerHTML = `<div class="dbar"><b id="resTitle">Reserve for 30 days</b><button class="x" type="button" data-close aria-label="Close">${icon("x")}</button></div>
    <form class="dbody" id="resForm"><p class="resnote"><b>A reservation doesn't stop anyone from using this patent.</b> It's only a note to other Patent Yard users that you're working on it. Anyone can still make, use and sell what it describes, and file their own improvements. It gives you no legal rights.</p>
    <p class="muted">The hold lasts 30 days. You can hold 5 at a time.</p>
    <div class="fgroup"><label for="resNote">What are you building? (optional, shown to others)</label><input class="field" id="resNote" maxlength="140"><small>Notes are public. Keep the inventive details of your own idea out of them.</small></div>
    <div class="rowbtns"><button class="btn primary" type="submit">Reserve</button><button class="btn quiet" type="button" data-close>Cancel</button></div></form>`;
  dlg.showModal();
  $("#resNote").focus();
  $("#resForm").addEventListener("submit", async e => { e.preventDefault(); const note = $("#resNote").value.trim(); dlg.close(); await act("reserve", note); });
});
dlg.addEventListener("click", e => { if (e.target === dlg || e.target.closest("[data-close]")) dlg.close(); });
refreshRes();

// ---------------------------------------------------------------- report a problem with this listing (the id goes with it)
const REPORT_KINDS = ["Wrong legal status", "Wrong expiry or lapse date", "Wrong inventor, assignee or applicant", "Missing or wrong family member",
  "Broken official link", "Drawing missing, cut off or corrupted", "Abstract, claims or description wrong", "Duplicate listing", "Something else"];
const repBtn = $("#reportBtn"), repDlg = $("#repDlg");
session.then(({ b }) => { if (b) repBtn.hidden = false; });
repBtn.addEventListener("click", () => {
  repDlg.innerHTML = `<div class="dbar"><b id="repTitle">Report a problem</b><button class="x" type="button" data-close aria-label="Close">${icon("x")}</button></div>
    <form class="dbody" id="repForm" novalidate><p class="muted">About <span class="num">${esc(P.dataset.n)}</span>. We check every report against the source record.</p>
    <div class="fgroup"><label for="repKind">What's wrong</label><select class="field" id="repKind">${REPORT_KINDS.map(k => `<option>${k}</option>`).join("")}</select></div>
    <div class="fgroup"><label for="repBody">Details <span class="opt">optional, but a link to the record that shows it helps</span></label><textarea class="field" id="repBody" maxlength="3800"></textarea></div>
    <div class="fgroup"><label for="repEmail">Your email (optional, if you'd like a reply)</label><input class="field" id="repEmail" type="email" maxlength="200" autocomplete="email"></div>
    <div class="rowbtns"><button class="btn primary" type="submit">Send report</button><button class="btn quiet" type="button" data-close>Cancel</button><span class="status" id="repStatus" aria-live="polite"></span></div></form>`;
  repDlg.showModal(); $("#repKind").focus();
  $("#repForm").addEventListener("submit", async e => {
    e.preventDefault();
    const kind = $("#repKind").value, detail = $("#repBody").value.trim(), st = $("#repStatus");
    if (kind === "Something else" && !detail) { st.className = "status err"; st.textContent = "Describe the problem first."; return; }
    const body = `[${kind}] ${detail}`.trim();
    const { b } = await session;
    try { await b.sendMessage({ kind: "report", patent: id, email: $("#repEmail").value.trim(), body }); repDlg.close(); toast("Thanks. We'll check it against the source record.", 4600, "ok"); }
    catch { st.className = "status err"; st.textContent = "It didn't send. Try again."; }
  });
});
repDlg.addEventListener("click", e => { if (e.target === repDlg || e.target.closest("[data-close]")) repDlg.close(); });

// ---------------------------------------------------------------- Claude kit
const kitDlg = $("#kit");
let patentData;
document.addEventListener("click", async e => {
  const k = e.target.closest("[data-kit]");
  if (!k) return;
  kitDlg.innerHTML = `<div class="dbar"><b id="kitTitle">Reinvent with Claude</b><button class="x" type="button" data-close aria-label="Close">${icon("x")}</button></div><div class="dbody"><span class="think">Loading the patent…</span></div>`;
  kitDlg.showModal();
  try { patentData ||= await loadPatent(id); }
  catch { $(".dbody", kitDlg).innerHTML = `<p class="status err">The patent data didn't load. Check your connection and try again.</p>`; return; }
  $(".dbody", kitDlg).innerHTML = `
    <div class="howto"><div><b>Pick a task.</b> We write the prompt for you.</div><div><b>Open Claude.</b> The prompt is copied; paste it if the box is empty.</div><div><b>Attach the brief</b> for the full claims and original drawings.</div></div>
    <div class="tasks" id="kTasks"></div>
    <div class="fgroup"><label for="kIdea">Your idea or notes (optional)</label><textarea class="field" id="kIdea" maxlength="4000" style="min-height:80px" placeholder="Anything you already have in mind. Leave it blank to let Claude propose directions."></textarea></div>
    <div class="fgroup"><label for="kPrompt">Prompt for Claude</label><textarea class="field prompt" id="kPrompt" readonly></textarea></div>
    <div class="rowbtns"><button class="btn primary" type="button" id="kOpen">${icon("spark")}Copy prompt and open Claude</button><button class="btn secondary" type="button" id="kPdf">${icon("file")}Download PDF brief</button><button class="btn quiet" type="button" id="kCopy">${icon("copy")}Copy</button><a class="btn quiet" href="/studio/?patent=${encodeURIComponent(id)}">Open in studio</a></div>
    <p class="status">Runs in your own Claude account, which has a free plan. Patent Yard sends nothing to any AI service.</p>`;
  const ideaBox = $("#kIdea");
  const kit = mountKit({ tasks: $("#kTasks"), prompt: $("#kPrompt"), getPatent: () => patentData, getIdea: () => (ideaBox.value.trim() ? { desc: ideaBox.value.trim() } : null), initial: k.dataset.kit });
  ideaBox.addEventListener("input", () => kit.refresh());
  $("#kOpen").addEventListener("click", () => openClaude($("#kPrompt").value));
  $("#kCopy").addEventListener("click", async () => toast((await copyText($("#kPrompt").value)) ? "Prompt copied." : "Select the prompt and copy it."));
  $("#kPdf").addEventListener("click", e => briefButton(e.currentTarget, kit.task, patentData, ideaBox.value.trim() ? { desc: ideaBox.value.trim() } : null, $("#kPrompt").value));
});
kitDlg.addEventListener("click", e => { if (e.target === kitDlg || e.target.closest("[data-close]")) kitDlg.close(); });

// a link ending in #kit (the home page plate) opens Reinvent with Claude straight away
if (location.hash === "#kit") $('[data-kit="workshop"]')?.click();
