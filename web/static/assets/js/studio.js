// Invention studio: an idea (optionally based on a patent) -> a prompt and PDF brief for Claude, saved to the bench.
import { $, $$, esc, toast, copyText, local, session, signInUrl, reducedMotion } from "./app.js";
import { numberLabel } from "./catalog.js";
import { bestMatches } from "./app.js";
import { mountKit, loadPatent, openClaude, briefButton } from "./kit.js";

const params = new URLSearchParams(location.search);
const F = { name: $("#iName"), pitch: $("#iPitch"), desc: $("#iDesc"), change: $("#iNew") };
let patent = null, ideaId = params.get("idea") || null;

const idea = () => ({ name: F.name.value.trim(), pitch: F.pitch.value.trim(), desc: F.desc.value.trim(), change: F.change.value.trim() });
const kit = mountKit({ tasks: $("#tasks"), prompt: $("#prompt"), getPatent: () => patent, getIdea: () => { const i = idea(); return i.name || i.pitch || i.desc || i.change ? i : null; } });
Object.values(F).forEach(f => f.addEventListener("input", () => { refresh(); draft(); }));

// ---------------------------------------------------------------- how to start, where you are, and the prompt's size
const work = $("#studioWork"), stages = $$(".stagebar [data-stage]");
let opened = false;
function after() {
  const words = $("#prompt").value.trim().split(/\s+/).filter(Boolean).length;
  $("#promptSize").textContent = words ? `${words.toLocaleString("en-US")} words` : "";
  const now = opened ? 3 : patent || Object.values(idea()).some(Boolean) ? 2 : 1;
  stages.forEach(li => { const n = +li.dataset.stage; li.dataset.state = n < now ? "done" : n === now ? "on" : ""; });
}
function refresh() { kit.refresh(); after(); }
function begin(kind, focus = true) {
  $$(".intentcard").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.start === kind)));
  work.dataset.start = kind;
  if (!focus) return;
  work.scrollIntoView({ behavior: reducedMotion() ? "auto" : "smooth", block: "start" });
  (kind === "patent" ? $("#pq") : F.name).focus({ preventScroll: true });
}
$$(".intentcard").forEach(b => b.addEventListener("click", () => begin(b.dataset.start)));
$("#tasks").addEventListener("click", after);

// unsent work survives a reload
const draft = () => local("studioDraft", { ...idea(), pid: patent?.id || null, task: kit.task });

// ---------------------------------------------------------------- patent picker
const pq = $("#pq"), list = $("#pickList"), picked = $("#picked");
async function choose(id) {
  if (!id) { patent = null; picked.innerHTML = ""; refresh(); draft(); return; }
  try { patent = await loadPatent(id); }
  catch { toast("That patent didn't load."); return; }
  if (patent.armed) { patent = null; toast("The studio doesn't work with weapons patents: Claude doesn't help design weapons."); return; }
  picked.innerHTML = `<div class="srcline">${patent.sheets[0] ? `<img src="${patent.sheets[0]}" alt="">` : ""}<div><b>${esc(patent.t)}</b><div class="muted note">${esc(patent.n)} · ${esc(patent.status)}</div></div><button class="btn quiet sm push-right" type="button" id="unpick">Remove</button></div>`;
  $("#unpick").addEventListener("click", () => choose(null));
  pq.value = ""; list.hidden = true; refresh(); draft();
}
let seqP = 0;
pq.addEventListener("input", async () => {
  const q = pq.value.trim(), my = ++seqP;
  if (q.length < 2) { list.hidden = true; return; }
  const num = q.replace(/[,\s/]/g, "").match(/^(?:us)?(\d{5,11})/i)?.[1];
  const hits = await (num ? fetch(`/patents/${num}`, { method: "HEAD" }).then(r => r.ok ? [{ id: new URL(r.url).pathname.split("/")[2], t: "Patent " + numberLabel(`US-${num}-`).trim() }] : []) : bestMatches(q, 8)).catch(() => []);
  if (my !== seqP) return;
  list.innerHTML = hits.length ? hits.map(p => `<li><button type="button" data-pick="${esc(p.id)}"><span>${esc(p.t)}</span><small>${esc(numberLabel(p.id))}</small></button></li>`).join("") : `<li class="status pad-item">No matches.</li>`;
  list.hidden = false;
});
list.addEventListener("click", e => { const b = e.target.closest("[data-pick]"); if (b) choose(b.dataset.pick); });
document.addEventListener("click", e => { if (!e.target.closest(".picker")) list.hidden = true; });

// ---------------------------------------------------------------- actions
$("#openClaude").addEventListener("click", () => { opened = true; after(); openClaude($("#prompt").value); });
$("#copyPrompt").addEventListener("click", async () => toast((await copyText($("#prompt").value)) ? "Prompt copied." : "Select the prompt and copy it."));
$("#pdfBrief").addEventListener("click", e => briefButton(e.currentTarget, kit.task, patent, idea(), $("#prompt").value));
$("#saveIdea").addEventListener("click", async () => {
  const i = idea(), st = $("#studioStatus");
  if (!i.name && !patent) { st.className = "status err"; st.textContent = "Give your invention a name or pick a patent first."; return; }
  const { b, user } = await session;
  if (!b) { st.className = "status"; st.textContent = "Saved in this browser. Your account didn't load, so it isn't on your bench yet."; return; }
  if (!user) { location.href = signInUrl(); return; }
  ideaId ||= crypto.randomUUID();
  try {
    await b.saveIdea({ id: ideaId, pid: patent?.id || null, ...i, task: kit.task, ptitle: patent?.t || null });
    st.className = "status ok"; st.textContent = "Saved to your bench.";
    history.replaceState(null, "", `/studio/?idea=${ideaId}`);
  } catch { st.className = "status err"; st.textContent = "Couldn't save it. Try again."; }
});

// ---------------------------------------------------------------- start: a saved invention, a patent, or the last draft
(async () => {
  let start = null;
  if (ideaId) {
    const { b, user } = await session;
    if (b && user) start = (await b.ideas().catch(() => [])).find(x => x.id === ideaId) || null;
    if (!start) ideaId = null;
  }
  start ||= params.get("patent") ? { pid: params.get("patent") } : local("studioDraft");
  if (!start) return after();
  for (const k of Object.keys(F)) F[k].value = start[k] || "";
  if (start.task) kit.task = start.task;
  if (start.pid) await choose(start.pid);
  begin(start.pid ? "patent" : start.name || start.pitch || start.desc ? "idea" : "", false);
  refresh();
})();
