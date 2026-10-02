// Contact form. Messages go to the site's database; they're read in the Supabase dashboard.
import { $, session } from "./app.js";

const form = $("#contactForm"), st = $("#cStatus");
session.then(({ b }) => { if (!b) { form.hidden = true; $("#cOff").hidden = false; } });
form.addEventListener("submit", async e => {
  e.preventDefault();
  const { b } = await session, body = $("#cBody").value.trim(), email = $("#cEmail").value.trim();
  if (!body) { st.className = "status err"; st.textContent = "Write a message first."; return; }
  if (email && !/^\S+@\S+\.\S+$/.test(email)) { st.className = "status err"; st.textContent = "That email address doesn't look right."; return; }
  const btn = form.querySelector("button[type=submit]"); btn.disabled = true;
  try {
    if (!$("#cWebsite").value) await b.sendMessage({ kind: "contact", email, body });  // bots fill the hidden field
    form.reset(); st.className = "status ok"; st.textContent = "Thanks, your message was sent.";
  } catch (err) { st.className = "status err"; st.textContent = err.code === "limit" ? "We're getting a lot of messages right now. Try again in an hour." : "It didn't send. Try again."; }
  finally { btn.disabled = false; }
});
