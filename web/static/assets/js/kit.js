// "Reinvent with Claude": writes a prompt and a PDF brief for the visitor's own Claude account.
// Nothing is sent anywhere; the prompt goes to the clipboard and the PDF is made in the browser.
import { $, $$, esc, toast, copyText } from "./app.js";

export const TASKS = [
  { id: "workshop", name: "Full reinvention workshop", desc: "Modern directions, then your idea, a first prior-art search and a rough provisional draft, one step at a time.", rec: true },
  { id: "explain", name: "Explain this patent", desc: "How it works part by part, and what each independent claim covers.", patent: true },
  { id: "directions", name: "Modern directions", desc: "Four new product directions using what became cheap or possible since filing.", patent: true },
  { id: "novelty", name: "Prior-art check", desc: "A first look for similar inventions, with sources and searches to run. It can't prove your idea is new." },
  { id: "provisional", name: "Provisional draft", desc: "A rough draft of a provisional application, to check and finish with a patent professional before filing." },
  { id: "sketch", name: "Concept sketches", desc: "Patent-style line drawings of the invention." },
  { id: "prototype", name: "Prototype plan", desc: "Parts list with rough costs, tools, build steps and tests." },
];

const fmt = s => { const d = new Date((s || "") + "T12:00:00"); return isNaN(d) ? "" : d.toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" }); };
const clip = (s, n) => { s = String(s || "").trim(); return s.length > n ? s.slice(0, n).replace(/\s+\S*$/, "") + " …" : s; };
const isDep = c => /\bclaims?\s+\d/i.test(c);
const hasIdea = i => !!(i && (i.name || i.pitch || i.desc || i.change));
// patents from other offices carry where/adj/office (functions/_archive.js kitOf); the rest are US patents
const where = p => p?.where || "the US", office = p => p?.office || "USPTO";

export function patentContext(p) {
  if (!p) return "";
  const ind = p.claims.filter(([, c]) => !isDep(c)).slice(0, 4);
  const dates = [`Filed: ${fmt(p.filed)}`, `${p.st === "abandoned" ? "Published" : "Granted"}: ${fmt(p.granted)}`];
  if (p.expired) dates.push(`Expired for an unpaid maintenance fee: ${fmt(p.expired)}`);
  if (p.termEnd) dates.push(`20-year term ended: ${fmt(p.termEnd)}`);
  return [
    `SOURCE PATENT (${p.st === "abandoned" ? "an abandoned application that never became an enforceable patent" : `no longer in force in ${where(p)}${p.st === "lapsed" ? ", unless the owner has it reinstated" : ""}`}; its own claims don't restrict making or using it there, but other rights may. Its published text is prior art)`,
    `Number: ${p.n}`,
    `Title as filed: ${p.ot}`,
    `Status: ${p.status}. ${p.why.join(" ")}`,
    dates.join(". ") + ".",
    p.assignee ? `Assignee: ${p.assignee}` : p.inventors ? `Inventors: ${p.inventors}` : "",
    `Field: ${p.field}${p.cpc.length ? ` (CPC ${p.cpc.slice(0, 3).join(", ")})` : ""}`,
    "",
    p.abs ? `Abstract: ${p.abs}` : `Full text: not on Patent Yard yet. Read the abstract and claims in the official PDF (${p.pdf}) and work from those.`,
    "",
    ind.length ? "Independent claims:" : "",
    ...ind.map(([n, c]) => `${n}. ${clip(c, 1500)}`),
    p.figs.length ? "\nFigures:\n" + p.figs.slice(0, 10).map(f => `- ${f}`).join("\n") : "",
    p.bg ? `\nBackground (from the patent): ${clip(p.bg, 900)}` : "",
    `\nFull record: ${p.url}  Official PDF: ${p.pdf}`,
  ].filter(x => x !== "").join("\n");
}

export function ideaBlock(i) {
  if (!hasIdea(i)) return "";
  return ["MY INVENTION", i.name && `Name: ${i.name}`, i.pitch && `Pitch: ${i.pitch}`, i.desc && `How it works: ${i.desc}`, i.change && `What's new: ${i.change}`].filter(Boolean).join("\n");
}

const ATTACH = "If I attached a Patent Yard brief (PDF), it has the patent's full claims and its original drawing sheets; use them.";
const FAITHFUL = "When you describe the original patent, stick to what its text and drawings show; don't add features it doesn't have.";
const DRAFT = `Draft a United States provisional patent application specification in Markdown with these sections: Title; Field; Background (describe the problem; cite the source patent, if any, as prior art and say what it leaves unsolved); Summary; Brief Description of the Drawings (propose FIG. 1 to FIG. 5 for me to prepare); Detailed Description (enough for a skilled person to make and use it: components with reference numerals 100, 102, 104..., how they connect, step-by-step operation, materials, ranges, and at least three alternative embodiments); Example Claims (1 independent and 6 dependent claims, optional in a provisional but useful later); Abstract (under 150 words). Write formally but plainly. Never invent test data, and put facts only I know in [square brackets]. Start the document with a note that this is an unreviewed draft: before filing, its facts, drawings and claims need checking, ideally by a registered patent attorney or agent, and it must meet the USPTO's filing requirements (cover sheet, fee, drawings).`
// what a prior-art check may and may not claim (workshop step 3 and the stand-alone task)
const NOVELTY = `This is a first look, not a search report or a legal opinion, and it can't establish that anything is new. If you can search the web or patent databases, do, and cite every result with its number or URL. Then give: (1) prior art you found, each with its source and how it overlaps; (2) things you think exist but couldn't verify, marked as unverified; (3) the new elements that look most distinct and why, and the ones most likely already known; (4) specific changes that would make it more distinct; (5) 3 to 5 searches for me to run, written as links like https://patents.google.com/?q=(your+keywords); (6) what evidence is missing. Keep three things apart: facts from the patent text, what I told you, and your own assumptions. Say plainly that you can't see everything filed recently or unpublished applications.`;

export function buildPrompt(task, p, idea) {
  const ctx = patentContext(p), mine = ideaBlock(idea), have = hasIdea(idea);
  const src = p ? "the source patent below" : "my idea below";
  const tail = [p ? ATTACH : "", p ? FAITHFUL : "", ctx, mine].filter(Boolean).join("\n\n");
  const askIdea = have ? "" : " First ask me to describe my invention (name, how it works, what's new), then continue.";
  const T = {
    workshop: `I'm an independent inventor. I want to build a new, patentable product based on ${p ? `${p.st === "abandoned" ? "an abandoned patent application, which never became an enforceable patent" : `a ${p.adj || "US"} patent whose protection has ended`}, so its own claims no longer stop anyone making, using or selling what it describes in ${where(p)} (other rights, such as newer patents, design rights, trademarks and regulations, may still apply). Its published text is prior art, so I can't patent it as it is` : "my own idea"}. Act as my product strategist and patent coach and work through these four steps with me, one at a time. After each step, stop and wait for my reply.

Step 1, modern directions. ${have ? "Start from my invention below and suggest how to strengthen it, plus three alternative directions." : `Propose four distinct product directions based on ${src}.`} Each should use something that became cheap, possible or in demand since ${p ? "the patent was filed" : "recently"} (for example low-cost sensors, phones, AI models, 3D printing, better batteries, new materials, subscriptions or new regulations) and contain a concrete new element that could be claimed, not just "add an app". For each give: a 2-4 word name, a one-sentence pitch, what is concretely new, who pays and why, what a first prototype needs, and the element that could be claimed.

Step 2, shape it. When I pick a direction or describe my own, help me write an invention name, a one-line pitch, how it works (parts, how they connect, how it is used) and what is new.

Step 3, prior-art check. ${NOVELTY}

Step 4, provisional draft. ${DRAFT}

If you can make images, SVG or artifacts, offer clean black-and-white patent-style line drawings for the figures along the way.

${tail}

Let's start with Step 1.`,
    explain: `Explain the patent below to me in plain English. Cover: the problem it solves; how it works, part by part (use the figures and reference numerals if the drawings are attached); what each independent claim covers, in simple terms; and what someone would need to build a working version today. If something is unclear from the text, say so rather than guessing.

${tail}`,
    directions: `I'm an independent inventor looking for a new, patentable product based on ${src}. Propose four distinct product directions. Each should use something that became cheap, possible or in demand since the patent was filed (for example low-cost sensors, phones, AI models, 3D printing, better batteries, new materials, subscriptions or new regulations), be buildable by a small team, and contain a concrete new element that could be claimed, not just "add an app". For each give: a 2-4 word name, a one-sentence pitch, what is concretely new versus the original, who pays and why, what a first prototype needs, and the element that could be claimed. End by asking which direction I want to develop.

${tail}`,
    novelty: `Act as a patent searcher doing a first prior-art check of my invention for me, an independent inventor.${askIdea}

${NOVELTY}${p ? " The source patent below is prior art." : ""}

${tail}`,
    provisional: `Help me draft a provisional patent application for my invention.${askIdea}

${DRAFT}

${tail}`,
    sketch: `Create clean black-and-white line drawings, in the style of US patent figures, of ${have ? "my invention" : p ? "the invention in the patent below" : "my invention"}. Make FIG. 1 a perspective view of the whole device, then add views that explain how it works (FIG. 2, FIG. 3...) as needed. Use SVG (or an image or artifact if you can make one) with a white background, black strokes, no shading or color, and reference numerals (10, 12, 14...) with leader lines. After each figure, list what each numeral labels. Show only what the text describes; don't add features.${askIdea && !p ? askIdea : ""}

${tail}`,
    prototype: `Plan a first working prototype of ${have ? "my invention" : p ? "the invention in the patent below" : "my invention"} for a small team.${!p ? askIdea : ""} Give: a bill of materials with generic part types, quantities and approximate unit costs; tools needed; step-by-step build instructions; simple tests that show it works; safety notes; and the rough total cost and build time. Prefer off-the-shelf parts, 3D printing and common hobby electronics.

${tail}`,
  };
  return (T[task] || T.workshop).trim();
}

// ---------------------------------------------------------------- Claude hand-off
export async function openClaude(prompt) {
  const copied = await copyText(prompt);
  const q = encodeURIComponent(prompt);
  window.open(q.length <= 6000 ? `https://claude.ai/new?q=${q}` : "https://claude.ai/new", "_blank", "noopener");
  toast(copied ? "Prompt copied. If Claude's message box is empty, paste it (Ctrl+V or ⌘V)." : "Claude opened. Copy the prompt from the box and paste it there.", 8000);
}

// ---------------------------------------------------------------- PDF brief
const JSPDF = "/assets/vendor/jspdf-4.2.1.umd.min.js";  // served from this site (assets/vendor/README.md)
let jspdfReady;
function loadJsPDF() {
  return jspdfReady ||= new Promise((ok, err) => {
    if (window.jspdf) return ok(window.jspdf.jsPDF);
    const s = Object.assign(document.createElement("script"), { src: JSPDF });
    s.onload = () => ok(window.jspdf.jsPDF);
    s.onerror = () => { jspdfReady = null; err(new Error("PDF tool didn't load")); };
    document.head.append(s);
  });
}
// Built-in PDF fonts cover Windows-1252 only; anything else becomes a close ASCII stand-in.
const CP1252 = new Set("€‚ƒ„…†‡ˆ‰Š‹ŒŽ‘’“”•–—˜™š›œžŸ");
const SUBS = { "≤": "<=", "≥": ">=", "≠": "!=", "→": "->", "←": "<-", "−": "-", "‐": "-", "‑": "-", "′": "'", "″": '"', "∼": "~", "≈": "~", "µ": "u", "Ω": "ohm", "α": "alpha", "β": "beta", "γ": "gamma", "δ": "delta", "θ": "theta", "λ": "lambda", "π": "pi", "σ": "sigma", "Δ": "delta", "√": "sqrt", "∞": "infinity", "⌘": "Cmd" };
export const pdfSafe = s => [...String(s ?? "").normalize("NFKC")].map(c => (c.charCodeAt(0) < 256 || CP1252.has(c) ? c : SUBS[c] ?? "?")).join("");

function sheetData(url) {
  return new Promise(ok => {
    const img = new Image();
    img.onload = () => {
      const c = document.createElement("canvas"); c.width = img.naturalWidth; c.height = img.naturalHeight;
      const x = c.getContext("2d"); x.fillStyle = "#fff"; x.fillRect(0, 0, c.width, c.height); x.drawImage(img, 0, 0);
      ok({ data: c.toDataURL("image/jpeg", 0.92), w: c.width, h: c.height });
    };
    img.onerror = () => ok(null);
    img.src = url;
  });
}

export async function downloadBrief(task, p, idea, prompt) {
  const jsPDF = await loadJsPDF();
  const doc = new jsPDF({ unit: "pt", format: "letter" });
  const W = 612, H = 792, M = 54, TW = W - 2 * M;
  let y = M;
  const ensure = h => { if (y + h > H - M - 18) { doc.addPage(); y = M; } };
  const text = (s, { size = 10.5, style = "normal", font = "helvetica", color = [22, 24, 29], after = 6, lead = 1.38 } = {}) => {
    doc.setFont(font, style); doc.setFontSize(size); doc.setTextColor(...color);
    for (const l of doc.splitTextToSize(pdfSafe(s), TW)) { ensure(size * lead); doc.text(l, M, y + size); y += size * lead; }
    y += after;
  };
  const head = s => { y += 8; ensure(40); doc.setDrawColor(207, 205, 199); doc.line(M, y, W - M, y); y += 12; text(s, { size: 13, style: "bold", after: 6 }); };
  const kicker = s => text(s.toUpperCase(), { size: 8.5, style: "bold", color: [110, 116, 130], after: 2 });
  const taskName = (TASKS.find(t => t.id === task) || TASKS[0]).name;

  kicker("Patent Yard brief · for Claude");
  text(idea?.name || p?.t || "My invention", { size: 22, style: "bold", after: 4, lead: 1.2 });
  if (p) text(`${p.n} · ${p.status} · Title as filed: ${p.ot}`, { size: 10, color: [75, 81, 96] });
  text(`Task: ${taskName} · prepared ${new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })} from Patent Yard's copy of the public record`, { size: 10, color: [179, 58, 12], style: "bold", after: 10 });
  text("How to use this brief: open Claude (claude.ai), attach this PDF to a new chat, and paste the prompt below (it is also on your clipboard if you copied it on Patent Yard). Claude will work through it with you.", { size: 10, color: [75, 81, 96] });

  head("Prompt for Claude");
  text(prompt, { size: 8.6, font: "courier", lead: 1.32, color: [40, 44, 52] });

  if (hasIdea(idea)) {
    head("My invention");
    for (const [k, v] of [["Name", idea.name], ["Pitch", idea.pitch], ["How it works", idea.desc], ["What's new", idea.change]]) if (v) { kicker(k); text(v); }
  }
  if (p) {
    head("The source patent");
    for (const [k, v] of [["Number", p.n], ["Status", p.status], ["Filed", fmt(p.filed)], [p.st === "abandoned" ? "Published" : "Granted", fmt(p.granted)],
      ["Expired (fee not paid)", fmt(p.expired)], ["20-year term ended", fmt(p.termEnd)], ["Assignee", p.assignee], ["Inventors", p.inventors],
      ["Application", p.app], ["Classification", p.cpc.slice(0, 4).join(", ")]]) if (v) text(`${k}: ${v}`, { size: 10, after: 1 });
    y += 6;
    kicker("Why it's listed"); for (const w of p.why) text("• " + w, { size: 10, after: 2 }); text("Caution: " + p.warn, { size: 10, color: [154, 75, 6] });
    kicker("Abstract"); text(p.abs);
    if (p.fieldText) { kicker("Field"); text(p.fieldText); }
    if (p.bg) { kicker("Background"); text(p.bg); }
    if (p.figs.length) { kicker("Figures"); for (const f of p.figs) text("• " + f, { size: 10, after: 2 }); y += 4; }
    head(`Claims (${p.claims.length})`);
    for (const [n, c] of p.claims) text(`${n}. ${c}`, { size: 9.6, style: isDep(c) ? "normal" : "bold", after: 5 });
    head("Sources");
    text(`Patent Yard record: ${p.url}`, { size: 10, after: 2 }); text(`Official ${office(p)} document: ${p.pdf}`, { size: 10, after: 2 }); text(`Google Patents: ${p.google}`, { size: 10 });
    head("Limits");
    text(`The abstract, claims, figure list and drawing sheets are the patent's own; the dates and status come from patent office records; the plain-English title is Patent Yard's, drafted with Claude, an AI model. A patent ending frees its own claims only; newer patents, design rights, trademarks, regulations and patents in other countries can still apply to a product. Patent Yard is not legal advice: confirm the status with the ${office(p)} before relying on it, and get a freedom-to-operate opinion before investing.`, { size: 9, color: [110, 116, 130] });
    if (p.sheets.length) {
      const imgs = await Promise.all(p.sheets.map(sheetData));
      imgs.forEach((im, i) => {
        if (!im) return;
        doc.addPage(); y = M;
        kicker(`Drawing sheet ${i + 1} of ${p.totalSheets || p.sheets.length} · from the published patent`);
        const maxH = H - y - M - 30, s = Math.min(TW / im.w, maxH / im.h);
        doc.addImage(im.data, "JPEG", M + (TW - im.w * s) / 2, y + 4, im.w * s, im.h * s);
      });
      if ((p.totalSheets || 0) > p.sheets.length) { doc.addPage(); y = M; text(`This patent has ${p.totalSheets} drawing sheets; all of them are in the official ${office(p)} document: ${p.pdf}`); }
    }
  }
  const pages = doc.getNumberOfPages();
  for (let i = 1; i <= pages; i++) {
    doc.setPage(i); doc.setFont("helvetica", "normal"); doc.setFontSize(8); doc.setTextColor(110, 116, 130);
    doc.text(pdfSafe(`Patent Yard brief${p ? " · " + p.n : ""}`), M, H - 30);
    doc.text(`${i} / ${pages}`, W - M, H - 30, { align: "right" });
  }
  const name = (p ? p.id : (idea?.name || "invention").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "invention");
  doc.save(`patent-yard-brief-${name}-${task}.pdf`);
}

// ---------------------------------------------------------------- the task picker + prompt preview, used by the patent page and the studio
export function mountKit({ tasks, prompt, getPatent, getIdea, initial = "workshop" }) {
  let task = initial;
  const avail = () => TASKS.filter(t => !t.patent || getPatent());
  const render = () => {
    if (getPatent()?.armed) {  // weapons patents get no kit (pipeline/patents.py armed)
      tasks.innerHTML = `<p class="status">Claude doesn't help design weapons, ammunition or explosives, so there is no kit for this patent. Work with a federally licensed manufacturer and a registered patent attorney or agent instead.</p>`;
      prompt.value = ""; return;
    }
    if (!avail().some(t => t.id === task)) task = "workshop";
    tasks.innerHTML = avail().map(t => `<button type="button" class="task" data-task="${t.id}" aria-pressed="${t.id === task}">${t.rec ? "<em>Recommended</em>" : ""}<b>${esc(t.name)}</b><span>${esc(t.desc)}</span></button>`).join("");
    prompt.value = buildPrompt(task, getPatent(), getIdea());
  };
  tasks.addEventListener("click", e => { const b = e.target.closest("[data-task]"); if (!b) return; task = b.dataset.task; render(); });
  render();
  return { refresh: render, get task() { return task; }, set task(v) { task = v; render(); } };
}

export async function loadPatent(id) {
  const r = await fetch(`/data/p/${encodeURIComponent(id)}.json`);
  if (!r.ok) throw new Error("Patent data didn't load");
  return r.json();
}

export async function briefButton(btn, ...args) {
  const label = btn.innerHTML;
  btn.disabled = true; btn.innerHTML = `<span class="think">Making the PDF…</span>`;
  try { await downloadBrief(...args); toast("PDF brief downloaded. Attach it to your chat with Claude."); }
  catch { toast("The PDF couldn't be made here. Use Copy prompt instead; it has the patent's key text."); }
  finally { btn.disabled = false; btn.innerHTML = label; }
}
export { $, $$ };
