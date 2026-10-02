// Test stand-in for web/static/assets/js/backend.js, with the same methods and the same rules as
// web/supabase/schema.sql (5 holds, 30 days, renew in the last 7 days, one holder per patent).
// State lives in localStorage so it survives page loads. Only dev/preview.py injects this file.
(() => {
  const KEY = "pymock", DAY = 864e5;
  const load = () => JSON.parse(localStorage.getItem(KEY) || '{"users":{},"session":null,"res":{},"ideas":{},"names":{}}');
  const save = s => localStorage.setItem(KEY, JSON.stringify(s));
  const err = code => Object.assign(new Error(code), { code });
  const listeners = [];
  const emit = (ev, u) => listeners.forEach(cb => setTimeout(() => cb(ev, u), 0));
  const me = s => (s.session ? { id: s.session, email: s.users[s.session].email } : null);
  window.__mockSeed = fn => { const s = load(); fn(s); save(s); };
  window.__PY_MOCK = {
    async user() { return me(load()); },
    onAuth(cb) { listeners.push(cb); },
    async signIn(email, pw) {
      const s = load(), u = Object.entries(s.users).find(([, x]) => x.email === email);
      if (!u || u[1].pw !== pw) throw err("invalid_credentials");
      s.session = u[0]; save(s); emit("SIGNED_IN", me(s));
    },
    async signUp(email, pw, name) {
      const s = load();
      if (Object.values(s.users).some(x => x.email === email)) throw err("user_already_exists");
      const id = "u_" + Math.random().toString(36).slice(2, 10);
      s.users[id] = { email, pw }; s.names[id] = name || ""; s.session = id; save(s); emit("SIGNED_IN", me(s));
      return { confirm: false };
    },
    async signOut() { const s = load(); s.session = null; save(s); emit("SIGNED_OUT", null); },
    async providers() { return { google: true }; },
    async signInWithGoogle() {  // stands in for the round trip to Google: signs in a fixed test account and comes back
      const s = load(), email = "google.tester@example.com";
      let id = Object.keys(s.users).find(k => s.users[k].email === email);
      if (!id) { id = "u_google"; s.users[id] = { email, pw: null }; s.names[id] = "Google Tester"; }
      s.session = id; save(s);
      setTimeout(() => (location.href = "/account/"), 50);
    },
    async resendSignup() {},
    async resetPassword() {},
    async updatePassword(pw) { const s = load(); if (!s.session) throw err("not_signed_in"); s.users[s.session].pw = pw; save(s); },
    async profile() { const s = load(); return s.session ? { name: s.names[s.session] || "" } : null; },
    async setName(name) { const s = load(); if (!s.session) throw err("not_signed_in"); s.names[s.session] = name; save(s); },
    async reservations() {
      const s = load(), now = Date.now();
      return Object.entries(s.res).filter(([, r]) => Date.parse(r.expires_at) > now)
        .map(([pid, r]) => ({ patent_id: pid, holder: s.names[r.user] || "A builder", note: r.note, reserved_at: r.reserved_at, renewed_at: r.renewed_at || null, expires_at: r.expires_at, mine: r.user === s.session }));
    },
    async reserve(pid, note) {
      const s = load(), now = Date.now();
      if (!s.session) throw err("not_signed_in");
      if (!/^US-[A-Z]*\d{5,11}-[A-Z]\d?$/.test(pid)) throw err("bad_patent");
      if ((note || "").length > 140) throw err("bad_note");
      const cur = s.res[pid];
      if (cur && Date.parse(cur.expires_at) > now) throw err("taken");
      if (Object.values(s.res).filter(r => r.user === s.session && Date.parse(r.expires_at) > now).length >= 5) throw err("limit");
      s.res[pid] = { user: s.session, note: note || "", reserved_at: new Date(now).toISOString(), expires_at: new Date(now + 30 * DAY).toISOString() }; save(s);
    },
    async release(pid) { const s = load(); if (s.res[pid]?.user !== s.session) throw err("not_yours"); delete s.res[pid]; save(s); },
    async renew(pid) {
      const s = load(), r = s.res[pid], now = Date.now();
      if (!r || r.user !== s.session || Date.parse(r.expires_at) < now) throw err("not_yours");
      if (Date.parse(r.expires_at) - now > 7 * DAY) throw err("too_early");
      r.renewed_at = new Date(now).toISOString(); r.expires_at = new Date(now + 30 * DAY).toISOString(); save(s);
    },
    async ideas() { const s = load(); return Object.values(s.ideas).filter(i => i.user === s.session).map(({ user, ...i }) => i).sort((a, b) => b.updated.localeCompare(a.updated)); },
    async saveIdea(i) { const s = load(); if (!s.session) throw err("not_signed_in"); s.ideas[i.id] = { ...i, user: s.session, updated: new Date().toISOString() }; save(s); },
    async deleteIdea(id) { const s = load(); if (s.ideas[id]?.user === s.session) delete s.ideas[id]; save(s); },
    async sendMessage(m) {
      if (!["contact", "report"].includes(m.kind) || !String(m.body || "").trim() || m.body.length > 4000) throw err("bad_message");
      const s = load(); (s.messages ||= []).push({ ...m, at: new Date().toISOString() }); save(s);
    },
    async deleteAccount() {
      const s = load(), id = s.session; if (!id) throw err("not_signed_in");
      for (const [k, r] of Object.entries(s.res)) if (r.user === id) delete s.res[k];
      for (const [k, i] of Object.entries(s.ideas)) if (i.user === id) delete s.ideas[k];
      delete s.users[id]; delete s.names[id]; s.session = null; save(s); emit("SIGNED_OUT", null);
    },
  };
})();
