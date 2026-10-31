// Accounts, reservations and saved inventions.
// Production: Supabase (web/supabase/schema.sql), loaded only when a page needs it.
// Tests: dev/mock-backend.js sets window.__PY_MOCK with the same methods.
// Resolves to null when accounts aren't configured; every caller hides its account features then.
const cfg = window.PY_CONFIG || {};
let ready;

export function backend() {
  return ready ||= (async () => {
    if (window.__PY_MOCK) return window.__PY_MOCK;
    if (!cfg.supabaseUrl || !cfg.supabaseAnonKey) return null;
    try {  // a stalled download counts as no accounts after 10 s, so no page waits on it forever
      const { createClient } = await Promise.race([import("/assets/vendor/supabase-js-2.117.3.min.js"),
        new Promise((_, no) => setTimeout(() => no(new Error("timeout")), 10000))]);
      return wrap(createClient(cfg.supabaseUrl, cfg.supabaseAnonKey, { auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true } }));
    } catch {
      return null;
    }
  })();
}

// Errors raised by the database functions carry a short code in their message (see schema.sql).
const CODES = ["not_signed_in", "taken", "limit", "not_yours", "too_early", "bad_patent", "bad_note"];
function fail(error) {
  if (!error) return;
  const code = CODES.find(c => String(error.message || "").includes(c)) || error.code || "error";
  throw Object.assign(new Error(error.message || "Request failed"), { code });
}
const me = u => (u ? { id: u.id, email: u.email } : null);

function wrap(sb) {
  return {
    async user() { const { data } = await sb.auth.getSession(); return me(data.session?.user); },
    onAuth(cb) { sb.auth.onAuthStateChange((event, session) => setTimeout(() => cb(event, me(session?.user)), 0)); },
    async signIn(email, password) { const { error } = await sb.auth.signInWithPassword({ email, password }); fail(error); },
    async signUp(email, password, name) {
      const { data, error } = await sb.auth.signUp({ email, password, options: { data: { display_name: name }, emailRedirectTo: cfg.siteUrl + "/account/" } });
      fail(error);
      return { confirm: !data.session };
    },
    async signOut() { await sb.auth.signOut(); },
    // which sign-in providers are switched on in Supabase (Authentication > Providers)
    async providers() {
      const r = await fetch(cfg.supabaseUrl + "/auth/v1/settings", { headers: { apikey: cfg.supabaseAnonKey } });
      const ext = r.ok ? (await r.json()).external || {} : {};
      return { google: !!ext.google };
    },
    async signInWithGoogle() {  // leaves for Google and comes back to /account/, where the session is picked up
      const { error } = await sb.auth.signInWithOAuth({ provider: "google", options: { redirectTo: cfg.siteUrl + "/account/" } });
      fail(error);
    },
    async resendSignup(email) { const { error } = await sb.auth.resend({ type: "signup", email, options: { emailRedirectTo: cfg.siteUrl + "/account/" } }); fail(error); },
    async resetPassword(email) { const { error } = await sb.auth.resetPasswordForEmail(email, { redirectTo: cfg.siteUrl + "/account/" }); fail(error); },
    async updatePassword(password) { const { error } = await sb.auth.updateUser({ password }); fail(error); },
    async profile() {
      const u = await this.user(); if (!u) return null;
      const { data, error } = await sb.from("profiles").select("display_name").eq("id", u.id).maybeSingle(); fail(error);
      return { name: data?.display_name || "" };
    },
    async setName(name) { const { error } = await sb.rpc("set_display_name", { p_name: name }); fail(error); },
    // Active reservations: patent_id, holder (display name), note, reserved_at, renewed_at, expires_at, mine.
    async reservations() { const { data, error } = await sb.rpc("list_reservations"); fail(error); return data || []; },
    async reserve(patent, note) { const { error } = await sb.rpc("reserve_patent", { p_patent: patent, p_note: note || "" }); fail(error); },
    async release(patent) { const { error } = await sb.rpc("release_patent", { p_patent: patent }); fail(error); },
    async renew(patent) { const { error } = await sb.rpc("renew_patent", { p_patent: patent }); fail(error); },
    async ideas() {
      const { data, error } = await sb.from("ideas").select("id,patent_id,data,updated_at").order("updated_at", { ascending: false }); fail(error);
      return (data || []).map(r => ({ ...r.data, id: r.id, pid: r.patent_id, updated: r.updated_at }));
    },
    async saveIdea(idea) {
      const u = await this.user();
      const { id, pid, updated, ...data } = idea;
      const { error } = await sb.from("ideas").upsert({ id, user_id: u.id, patent_id: pid || null, data, updated_at: new Date().toISOString() }); fail(error);
    },
    async deleteIdea(id) { const { error } = await sb.from("ideas").delete().eq("id", id); fail(error); },
    async sendMessage({ kind, patent, email, body }) {
      const { error } = await sb.from("messages").insert({ kind, patent_id: patent || null, email: (email || "").slice(0, 200), body: String(body).slice(0, 4000) }); fail(error);
    },
    async deleteAccount() { const { error } = await sb.rpc("delete_my_account"); fail(error); await sb.auth.signOut(); },
  };
}
