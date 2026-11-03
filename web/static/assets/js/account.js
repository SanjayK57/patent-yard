// Sign in (email or Google), create an account, reset a password, and the bench (reservations, saved inventions).
import { $, $$, esc, toast, flash, fmtDate, daysLeft, session, safeNext } from "./app.js";
import { numberLabel } from "./catalog.js";

const MAX_RES = 5;
const params = new URLSearchParams(location.search);
const views = { load: $("#loadView"), auth: $("#authView"), bench: $("#benchView"), off: $("#offView"), pw: $("#newPwView") };
$("#authForm").addEventListener("submit", e => e.preventDefault());  // never a native submit, even before the account code is ready
const show = v => Object.entries(views).forEach(([k, el]) => (el.hidden = k !== v));
const store = (k, v) => { try { v === undefined ? sessionStorage.removeItem("patentyard." + k) : sessionStorage.setItem("patentyard." + k, v); } catch {} };
const stored = k => { try { return sessionStorage.getItem("patentyard." + k); } catch { return null; } };
// where to go after signing in; kept across the Google round trip
const next = safeNext(params.get("next") || stored("next"));
let mode = "in";
const say = (msg, kind = "") => { const el = $("#authStatus"); el.className = "status authstatus " + kind; el.textContent = msg; if (kind === "err") { el.style.animation = "none"; void el.offsetWidth; el.style.animation = ""; } };
const ERR = {
  invalid_credentials: "That email and password don't match.", email_not_confirmed: "Confirm your email first. The link is in your inbox.",
  user_already_exists: "There's already an account with that email. Sign in instead.", weak_password: "Choose a longer password (at least 8 characters).",
  over_email_send_rate_limit: "Too many emails sent. Wait a few minutes and try again.", over_request_rate_limit: "Too many attempts. Wait a minute and try again.",
  validation_failed: "Google sign-in isn't switched on yet. Use your email for now.", provider_disabled: "Google sign-in isn't switched on yet. Use your email for now.",
};
const busy = (btn, on) => { btn.disabled = on; btn.classList.toggle("loading", on); };

// ---------------------------------------------------------------- the sign-in card
const TEXT = {
  in: ["Welcome back", "Sign in to your bench.", "Sign in"],
  up: ["Create your free account", "Reserve patents and keep your inventions in one place.", "Create account"],
  reset: ["Reset your password", "We'll email you a link to choose a new one.", "Send reset link"],
};
function setMode(m) {
  mode = m;
  $$(".authcard .seg button").forEach(x => x.setAttribute("aria-selected", String(x.dataset.mode === m)));
  $(".authcard .seg").hidden = m === "reset";
  $("#oauthRow").hidden = m === "reset" || !$("#oauthRow").dataset.on;
  $("#nameRow").hidden = m !== "up"; $("#pwRow").hidden = m === "reset";
  $("#pwHint").hidden = $("#pwMeter").hidden = m !== "up";
  $("#aPw").autocomplete = m === "up" ? "new-password" : "current-password";
  const [title, sub, cta] = TEXT[m];
  $("#authTitle").textContent = title; $("#authSub").textContent = sub; $("#authSubmit span").textContent = cta;
  $("#forgotBtn").textContent = m === "reset" ? "Back to sign in" : "Forgot your password?";
  $("#forgotBtn").hidden = m === "up";
  say(""); slide();
}
function slide() {
  const sel = $('.authcard .seg button[aria-selected="true"]'), ind = $(".authcard .seg .ind");
  if (sel && ind) { ind.style.width = sel.offsetWidth + "px"; ind.style.transform = `translateX(${sel.offsetLeft - 4}px)`; }
}
addEventListener("resize", slide);

function strength(pw) {  // 0..4, for the bar under the password while creating an account
  let s = pw.length >= 8 ? 1 : 0;
  if (pw.length >= 12) s++;
  if (/[a-z]/.test(pw) && /[A-Z]/.test(pw)) s++;
  if (/\d/.test(pw) || /[^A-Za-z0-9]/.test(pw)) s++;
  return pw.length < 8 ? Math.min(s, 0) : s;
}
$("#aPw").addEventListener("input", () => {
  if (mode !== "up") return;
  const s = strength($("#aPw").value), bar = $("#pwMeter i");
  bar.style.width = [8, 35, 60, 80, 100][s] + "%";
  bar.style.background = s <= 1 ? "var(--lapsed)" : s === 2 ? "var(--aband)" : "var(--free)";
});
$("#pwShow").addEventListener("click", e => {
  const on = $("#aPw").type === "password";
  $("#aPw").type = on ? "text" : "password";
  e.currentTarget.textContent = on ? "Hide" : "Show";
  e.currentTarget.setAttribute("aria-pressed", String(on));
});

function doneBox(html) {
  $("#authMain").hidden = true;
  const box = $("#authDone");
  box.innerHTML = html; box.hidden = false;
  return box;
}
const mailIcon = `<svg viewBox="0 0 24 24" class="i"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3.5 6.5L12 13l8.5-6.5"/></svg>`;
function checkEmail(email, kind, b) {
  const box = doneBox(`<div class="donebox"><span class="tick mail">${mailIcon}</span><h2>Check your email</h2>
    <p>${kind === "up" ? "We sent a confirmation link to" : "If there's an account for"} <b>${esc(email)}</b>${kind === "up" ? ". Open it to finish creating your account." : ", a link to reset the password is on its way."}</p>
    <div class="rowbtns">${kind === "up" ? `<button class="btn secondary sm" type="button" id="resend">Resend the email</button>` : ""}<button class="btn quiet sm" type="button" id="backIn">Back to sign in</button></div>
    <p class="status" id="resendSt" aria-live="polite"></p></div>`);
  $("#backIn", box).addEventListener("click", () => { box.hidden = true; $("#authMain").hidden = false; setMode("in"); });
  $("#resend", box)?.addEventListener("click", async e => {
    busy(e.currentTarget, true);
    try { await b.resendSignup(email); $("#resendSt").textContent = "Sent again. It can take a minute to arrive."; }
    catch (err) { $("#resendSt").textContent = ERR[err.code] || "Couldn't resend it. Try again in a minute."; }
    busy(e.currentTarget, false);
  });
}

async function signedIn(b, user) {
  store("next");
  if (next) { flash(`Signed in as ${user.email}.`); location.href = next; return; }
  doneBox(`<div class="donebox"><span class="tick"><svg viewBox="0 0 24 24" class="i"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg></span><h2>You're in</h2><p>Opening your bench…</p></div>`);
  setTimeout(() => bench(b, user, true), 900);
}

(async () => {
  const { b, user } = await session;
  if (!b) return show("off");
  b.onAuth((event, u) => {
    if (event === "PASSWORD_RECOVERY") show("pw");
    else if (event === "SIGNED_IN" && u && !views.auth.hidden && !$("#authMain").hidden) signedIn(b, u);
    else if (event === "SIGNED_OUT") { show("auth"); setMode("in"); }
  });
  $$(".authcard .seg button").forEach(t => t.addEventListener("click", () => setMode(t.dataset.mode)));
  $("#forgotBtn").addEventListener("click", () => setMode(mode === "reset" ? "in" : "reset"));
  if (params.get("mode") === "up") setMode("up");

  // Google: shown only when it's switched on in Supabase (Authentication > Providers)
  b.providers().then(p => {
    if (!p.google) return;
    $("#oauthRow").dataset.on = "1";
    $("#oauthRow").hidden = mode === "reset";
    $("#googleBtn").addEventListener("click", async e => {
      busy(e.currentTarget, true);
      if (next) store("next", next);
      store("justSignedIn", "1");
      try { await b.signInWithGoogle(); }  // leaves the page for Google
      catch (err) { busy(e.currentTarget, false); say(ERR[err.code] || "Google sign-in didn't start. Try again.", "err"); }
    });
  }).catch(() => {});

  $("#authForm").addEventListener("submit", async e => {
    e.preventDefault();
    const email = $("#aEmail").value.trim(), pw = $("#aPw").value, btn = $("#authSubmit");
    if (!/^\S+@\S+\.\S+$/.test(email)) { $("#aEmail").focus(); return say("Enter a valid email address.", "err"); }
    if (mode !== "reset" && pw.length < 8) { $("#aPw").focus(); return say("Passwords are at least 8 characters.", "err"); }
    busy(btn, true); say("");
    try {
      if (mode === "in") { await b.signIn(email, pw); store("justSignedIn", "1"); return signedIn(b, await b.user()); }
      if (mode === "up") {
        const r = await b.signUp(email, pw, $("#aName").value.trim().slice(0, 40));
        if (r.confirm) return checkEmail(email, "up", b);
        store("justSignedIn", "1"); return signedIn(b, await b.user());
      }
      await b.resetPassword(email); checkEmail(email, "reset", b);
    } catch (err) { say(ERR[err.code] || err.message || "That didn't work. Try again.", "err"); }
    finally { busy(btn, false); }
  });
  $("#newPwForm").addEventListener("submit", async e => {
    e.preventDefault();
    const pw = $("#npw").value, st = $("#npwStatus"), btn = $("button[type=submit]", e.currentTarget);
    if (pw.length < 8) { st.className = "status err"; st.textContent = "Passwords are at least 8 characters."; return; }
    busy(btn, true);
    try { await b.updatePassword(pw); flash("Password saved."); location.replace("/account/"); }
    catch (err) { st.className = "status err"; st.textContent = ERR[err.code] || "Couldn't save it. Try again."; busy(btn, false); }
  });

  if (user) {
    if (stored("next")) { store("next"); flash(`Signed in as ${user.email}.`); location.replace(next); return; }  // back from Google
    bench(b, user, !!stored("justSignedIn"));
  } else { show("auth"); setMode(mode); }  // only now, with every handler attached
})();

// ---------------------------------------------------------------- the bench
const kit = {};
const patentInfo = id => (kit[id] ||= fetch(`/data/p/${encodeURIComponent(id)}.json`).then(r => (r.ok ? r.json() : null)).catch(() => null));

async function bench(b, user, fresh) {
  store("justSignedIn");
  show("bench");
  $("#benchWho").textContent = `Signed in as ${user.email}.`;
  if (fresh) {
    const name = (await b.profile().catch(() => null))?.name;
    $("#welcome").innerHTML = `<div class="welcome"><span class="tick"><svg viewBox="0 0 24 24" class="i"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg></span><div><b>Welcome${name ? ", " + esc(name) : ""}!</b><span>Reserve a patent or start an invention. Everything you save shows up here.</span></div></div>`;
  }
  await Promise.all([drawRes(b), drawIdeas(b)]);
  $("#signOut").onclick = async e => { e.currentTarget.classList.add("loading"); await b.signOut(); flash("Signed out. See you soon."); location.href = "/"; };
}

async function drawRes(b) {
  let mine = [];
  try { mine = (await b.reservations()).filter(r => r.mine).sort((a, z) => a.expires_at.localeCompare(z.expires_at)); } catch { toast("Your reservations didn't load.", 4600, "err"); }
  const info = await Promise.all(mine.map(r => patentInfo(r.patent_id)));
  $("#resCount").textContent = `${mine.length} of ${MAX_RES}`;
  $("#resList").innerHTML = mine.map((r, k) => {
    const p = info[k], left = daysLeft(r.expires_at);
    return `<div class="rowi"><div class="th">${p?.sheets?.[0] ? `<img src="${esc(p.sheets[0])}" alt="">` : ""}</div>
      <div><b><a href="/patents/${esc(r.patent_id)}/">${esc(p?.t || numberLabel(r.patent_id))}</a></b><small>${esc(numberLabel(r.patent_id))} · ${left} ${left === 1 ? "day" : "days"} left (until ${esc(fmtDate(r.expires_at))})${r.note ? ` · "${esc(r.note)}"` : ""}</small></div>
      <div class="ra"><a class="btn primary sm" href="/studio/?patent=${encodeURIComponent(r.patent_id)}">Reinvent</a>${left <= 7 ? `<button class="btn secondary sm" type="button" data-renew="${esc(r.patent_id)}">Renew</button>` : ""}<button class="btn quiet sm" type="button" data-release="${esc(r.patent_id)}">Release</button></div></div>`;
  }).join("") || `<div class="empty flat"><b>Nothing reserved yet</b><p>Open any patent and choose Reserve; each hold lasts 30 days.</p><p class="gap-top"><a class="btn secondary sm" href="/browse/">Browse patents</a></p></div>`;
  $("#resList").onclick = async e => {
    const rel = e.target.closest("[data-release]"), ren = e.target.closest("[data-renew]"), btn = rel || ren;
    if (!btn) return;
    btn.classList.add("loading");
    try {
      if (rel) { await b.release(rel.dataset.release); toast("Released. Other builders can reserve it now.", 4600, "ok"); }
      else { await b.renew(ren.dataset.renew); toast("Renewed for another 30 days.", 4600, "ok"); }
    } catch (err) { toast(err.code === "too_early" ? "You can renew in the last 7 days of a hold." : "That didn't work. Try again.", 4600, "err"); }
    drawRes(b);
  };
}

async function drawIdeas(b) {
  let ideas = [];
  try { ideas = await b.ideas(); } catch { toast("Your inventions didn't load.", 4600, "err"); }
  const info = await Promise.all(ideas.map(i => (i.pid ? patentInfo(i.pid) : null)));
  $("#ideaCount").textContent = ideas.length;
  $("#ideaList").innerHTML = ideas.map((i, k) => {
    const p = info[k];
    return `<div class="rowi"><div class="th">${p?.sheets?.[0] ? `<img src="${esc(p.sheets[0])}" alt="">` : "Own idea"}</div>
      <div><b><a href="/studio/?idea=${esc(i.id)}">${esc(i.name || (p ? "Based on " + p.t : i.ptitle ? "Based on " + i.ptitle : "Untitled invention"))}</a></b><small>${esc(i.pitch || (i.pid ? numberLabel(i.pid) : ""))}${i.updated ? ` · saved ${esc(fmtDate(i.updated))}` : ""}</small></div>
      <div class="ra"><a class="btn primary sm" href="/studio/?idea=${esc(i.id)}">Open</a><button class="btn quiet sm" type="button" data-del="${esc(i.id)}">Delete</button></div></div>`;
  }).join("") || `<div class="empty flat"><b>No saved inventions yet</b><p>Start one in the invention studio and save it here.</p><p class="gap-top"><a class="btn secondary sm" href="/studio/">Open the studio</a></p></div>`;
  $("#ideaList").onclick = async e => {
    const del = e.target.closest("[data-del]"); if (!del) return;
    if (!del.dataset.confirm) { del.dataset.confirm = 1; del.textContent = "Confirm delete"; setTimeout(() => { if (del.isConnected) { delete del.dataset.confirm; del.textContent = "Delete"; } }, 4000); return; }
    del.classList.add("loading");
    try { await b.deleteIdea(del.dataset.del); toast("Deleted.", 4600, "ok"); } catch { toast("Couldn't delete it.", 4600, "err"); }
    drawIdeas(b);
  };
}
