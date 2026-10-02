// Settings page: display settings (this browser) and account settings (Supabase).
import { $, $$, toast, session, getSettings, saveSettings, applySettings } from "./app.js";

// ---------------------------------------------------------------- display settings
const DEFAULTS = { theme: "system", drawings: "inverted", text: "normal", motion: "system", sort: "build" };
function paint() {
  const s = { ...DEFAULTS, ...getSettings() };
  for (const group of $$("[data-setting]")) for (const b of $$("button", group)) b.setAttribute("aria-checked", String(b.dataset.value === s[group.dataset.setting]));
}
for (const group of $$("[data-setting]")) {
  group.addEventListener("click", e => {
    const b = e.target.closest("button[data-value]"); if (!b) return;
    saveSettings({ [group.dataset.setting]: b.dataset.value }); applySettings(); paint();
  });
  group.addEventListener("keydown", e => {  // arrow keys move between the options, like native radio buttons
    if (!["ArrowRight", "ArrowLeft"].includes(e.key)) return;
    const opts = $$("button", group), i = opts.indexOf(document.activeElement), n = opts[(i + (e.key === "ArrowRight" ? 1 : opts.length - 1)) % opts.length];
    n.focus(); n.click();
  });
}
paint();
$("#clearLocal").addEventListener("click", () => {
  try { Object.keys(localStorage).filter(k => k.startsWith("patentyard.")).forEach(k => localStorage.removeItem(k)); } catch {}
  applySettings(); paint(); toast("Settings and drafts in this browser were cleared.");
});

// ---------------------------------------------------------------- account
const st = $("#acctStatus");
const say = (msg, kind = "") => { st.className = "status " + kind; st.textContent = msg; };
(async () => {
  const { b, user } = await session;
  if (!b) { $("#acctOff").hidden = false; return; }
  if (!user) { $("#acctOut").hidden = false; return; }
  $("#acctIn").hidden = false;
  $("#setEmail").textContent = user.email;
  $("#setName").value = (await b.profile().catch(() => null))?.name || "";
  $("#nameForm").addEventListener("submit", async e => {
    e.preventDefault();
    try { await b.setName($("#setName").value.trim().slice(0, 40)); say("Display name saved.", "ok"); } catch { say("Couldn't save the name. Try again.", "err"); }
  });
  $("#pwForm").addEventListener("submit", async e => {
    e.preventDefault();
    const pw = $("#setPw").value;
    if (pw.length < 8) return say("Passwords are at least 8 characters.", "err");
    try { await b.updatePassword(pw); $("#setPw").value = ""; say("Password changed.", "ok"); } catch (err) { say(err.code === "weak_password" ? "Choose a stronger password." : "Couldn't change the password. Try again.", "err"); }
  });
  $("#setSignOut").addEventListener("click", async () => { await b.signOut(); location.href = "/"; });
  $("#setDelete").addEventListener("click", async e => {
    const btn = e.currentTarget;
    if (!btn.dataset.confirm) { btn.dataset.confirm = 1; btn.textContent = "Click again to delete everything permanently"; setTimeout(() => { delete btn.dataset.confirm; btn.textContent = "Delete my account"; }, 5000); return; }
    try { await b.deleteAccount(); location.href = "/"; } catch { say("Couldn't delete the account. Try again.", "err"); }
  });
})();
$$("form", $("#acctIn")).forEach(f => f.addEventListener("submit", e => e.preventDefault()));  // never a native submit
