// Local stand-in for the claude.ai artifact runtime, for testing only. Never published.
// Provides window.claude.use("db" | "user" | "sample" | "downloads") with the same call shapes as the real runtime,
// an in-memory database that enforces the page's rule (each viewer writes only claims/<their id>), a signed-in
// test user, and canned AI answers.
(() => {
  const ME = "u_me000000000000000000000";
  const store = new Map(), subs = new Set();
  const clone = v => JSON.parse(JSON.stringify(v));
  const notify = () => subs.forEach(fn => fn());
  const snap = path => ({ id: path.split("/").pop(), exists: store.has(path), data: () => store.has(path) ? clone(store.get(path)) : undefined, metadata: {} });
  const doc = path => ({
    id: path.split("/").pop(), path,
    get: async () => snap(path),
    set: async data => {
      if (path.startsWith("claims/") && path !== "claims/" + ME) throw { code: "invalid_argument" };
      if (JSON.stringify(data).length > 256 * 1024) throw { code: "invalid_argument" };
      store.set(path, clone(data)); window.__writes.push(path); setTimeout(notify, 20);
    },
    delete: async () => { store.delete(path); setTimeout(notify, 20); },
    collection: name => col(path + "/" + name),
    onSnapshot(next) { const fn = () => next(snap(path)); subs.add(fn); setTimeout(fn, 10); return () => subs.delete(fn); },
  });
  const col = path => ({
    path, doc: id => doc(path + "/" + id),
    onSnapshot(next) {
      const fn = () => { const docs = [...store.keys()].filter(k => k.startsWith(path + "/") && k.split("/").length === path.split("/").length + 1).map(snap); next({ docs, size: docs.length, empty: !docs.length, docChanges: () => [] }); };
      subs.add(fn); setTimeout(fn, 10); return () => subs.delete(fn);
    },
  });
  const user = {
    me: async () => ({ id: ME, name: "Test Builder", avatarUrl: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='30' height='30'%3E%3Crect width='30' height='30' fill='%230F6B4F'/%3E%3C/svg%3E", color: "#0F6B4F", email: null, isOwner: true, canEdit: true }),
    can: async () => true,
    profiles: async ids => Object.fromEntries([].concat(ids).map(id => [id, { id, name: id === ME ? "Test Builder" : "Other Builder", avatarUrl: "", color: "#888", isMe: id === ME, guest: false }])),
  };
  const SVG = `<svg viewBox="0 0 640 480" onload="alert(1)"><scr` + `ipt>alert(1)</scr` + `ipt><rect width="640" height="480" fill="white"/><circle cx="320" cy="240" r="120" fill="none" stroke="black" stroke-width="2"/><a href="https://evil.example"><text x="330" y="100">10</text></a><foreignObject><div>x</div></foreignObject></svg>`;
  const dirs = [1, 2, 3, 4].map(k => ({ name: `Direction ${k}`, pitch: `Pitch ${k}`, change: `Change ${k}`, buyer: `Buyer ${k}`, build: `Build ${k}`, novelty: `Novelty ${k}` }));
  const novelty = { verdict: "promising", score: 7, summary: "Looks new.", overlaps: [{ what: "Thing", why: "Similar" }], differentiators: ["Add a sensor"], queries: ["test query"] };
  window.__writes = []; window.__prompts = []; window.__store = store;
  window.__seed = (path, data) => { store.set(path, clone(data)); notify(); };
  const sample = async (input, opts = {}) => {
    window.__prompts.push(String(input).slice(0, 60));
    const text = /SVG/.test(input) ? SVG : /provisional/i.test(input) ? "# Test Title\n\n## Field\nTest field." : "Rewritten description.";
    let acc = "";
    for (const w of text.split(" ")) { if (opts.signal?.aborted) throw { code: "cancelled", text: acc }; acc += (acc ? " " : "") + w; opts.onText?.({ text: acc, delta: w }); await new Promise(r => setTimeout(r, 2)); }
    return { text, truncated: false, modelTierApplied: "default" };
  };
  sample.json = async input => { window.__prompts.push(String(input).slice(0, 60)); await new Promise(r => setTimeout(r, 30)); return /novelty screen/.test(input) ? novelty : dirs; };
  const downloads = { save: async req => { window.__saved = req; return { status: "saved" }; } };
  window.claude = { use: async n => ({ db: { doc, collection: col }, user, sample, downloads })[n] || null };
})();
