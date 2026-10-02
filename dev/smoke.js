// End-to-end smoke test for test.html (the page plus dev/mock-runtime.js). Run in the page: await runSmoke()
// Returns {passed, failed: [...], errors: [...]} and clicks every kind of button the site has.
window.runSmoke = async function runSmoke() {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const q = s => document.querySelector(s), qa = s => [...document.querySelectorAll(s)];
  const results = [], errors = [];
  addEventListener("unhandledrejection", e => errors.push("rejection: " + (e.reason?.message || JSON.stringify(e.reason))));
  addEventListener("error", e => errors.push("error: " + e.message));
  const check = (name, ok, info = "") => results.push({ name, ok: !!ok, info: String(info).slice(0, 160) });
  const click = async (sel, ms = 250) => { const el = typeof sel === "string" ? q(sel) : sel; if (!el) throw new Error("missing " + sel); el.click(); await wait(ms); return el; };
  const step = async (name, fn) => { try { await fn(); } catch (e) { check(name, false, e.message); } };

  await wait(1200);
  await step("boot", async () => {
    check("patents loaded", S.patents.length > 300, S.patents.length);
    check("wall has 15 cards with one featured", qa("#wall .card").length === 15 && qa("#wall .card.feat").length === 1);
    check("stats filled", q("#stPool").textContent !== "—" && q("#stLapsed").textContent !== "—");
    check("verified pill", /Verified/.test(q("#vpill").textContent), q("#vpill").textContent);
    check("signed in", !!q("#who img"));
    check("every card image resolved", (await wait(900), qa("#wall .fig img").every(i => i.src || i.closest(".fig").querySelector(".nofig"))));
  });

  await step("navigation", async () => {
    for (const v of ["browse", "bench", "how", "legal", "today"]) { await click(`.tab[data-go="${v}"], footer [data-go="${v}"]`, 200); check("nav " + v, !q(`[data-view="${v}"]`).hidden); }
    await click('footer [data-anchor="privacy"]', 300); check("footer legal anchor", !q('[data-view="legal"]').hidden);
    await click(".brand", 200); check("brand goes home", !q('[data-view="today"]').hidden);
    await click('[data-scroll="wallTop"]', 200); check("hero scroll button", true);
    q("#hq").value = "wrench"; q("#hq").dispatchEvent(new KeyboardEvent("keydown", { key: "Enter" })); await wait(300);
    check("header search goes to browse", !q('[data-view="browse"]').hidden && /of/.test(q("#count").textContent), q("#count").textContent);
    q("#q").value = ""; q("#q").dispatchEvent(new Event("input")); await wait(300); await click('.tab[data-go="today"]', 200);
  });

  await step("fields", async () => {
    await click("#editFields", 150); check("picker opens", !q("#picker").hidden);
    const chips = qa("[data-pick]"); check("picker lists fields", chips.length >= 10, chips.length);
    chips[0].click(); await wait(50); const f = chips[0].dataset.pick;
    await click("#savePicker", 300);
    check("wall follows chosen field", S.wall.length > 0 && S.wall.every(p => p.ind === f), f);
    await click("#editFields", 150); qa("[data-pick]").forEach(b => b.setAttribute("aria-pressed", "false")); await click("#savePicker", 300);
    check("back to all fields", new Set(S.wall.map(p => p.ind)).size > 3);
  });

  await step("dossier", async () => {
    const p = S.patents.find(x => x.st === "lapsed" && x.ns > 1) || S.patents[0];
    await openSheet(p.id); await wait(500);
    check("dossier opens", q("#dlg").open && q("#dlgTitle").textContent === p.t);
    for (const t of ["overview", "drawings", "claims", "desc", "history", "sources"]) { await click(`.dtab[data-tab="${t}"]`, 450); check("tab " + t, q("#dpanel").textContent.trim().length > 40 && q(`.dtab[data-tab="${t}"]`).getAttribute("aria-selected") === "true"); }
    await click('.dtab[data-tab="history"]', 450);
    check("timeline graphic", !!q("#dpanel svg.chart"));
    check("fee schedule for lapsed patent", qa("#dpanel .fee").length === 3 && !!q("#dpanel .fee .badge.lapsed"));
    check("family lane", qa("#dpanel .famnode").length >= 1 && !!q("#dpanel .famnode.me"));
    await click('.dtab[data-tab="sources"]', 450);
    const hrefs = qa("#dpanel a.lcard").map(a => a.href);
    check("source and cross-check links", hrefs.length >= 8 && hrefs.every(h => /^https:\/\//.test(h)), hrefs.length);
    check("gazette source link for lapsed", !!q("#dpanel a.lcard.src") && /uspto\.gov/.test(q("#dpanel a.lcard.src").href));
    await click('.dtab[data-tab="claims"]', 450);
    const tb = q("#dpanel .tree button"); check("claim tree", !!tb);
    if (tb) { await click(tb, 300); check("claim tree jumps to claim", !!q(".claimlist li.hl")); }
    await click('.dtab[data-tab="overview"]', 500);
    const th = q("#dpanel .strip button") || q('#dpanel [data-view-sheet="0"]');
    await click(th, 400); check("viewer opens", q("#viewer").open && !!q("#viewer img").src);
    if (p.ns > 1) { await click('[data-vstep="1"]', 150); check("viewer next", /Sheet 2/.test(q("#viewer .vbar").textContent)); await click('[data-vstep="-1"]', 150); }
    document.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowRight" })); await wait(100);
    await click("#viewer [data-zoomtoggle]", 100); check("viewer zoom", q("#vStage").classList.contains("zoom"));
    await click("#viewer [data-close]", 150); check("viewer closes, dossier stays", !q("#viewer").open && q("#dlg").open);
    await click('#dlg [data-act="copylink"]', 200); check("copy link", /claude\.ai\/artifact\/.+#US-/.test(q("#toast").textContent) || /copied/i.test(q("#toast").textContent), q("#toast").textContent);
    await click('#dActs [data-act="reserveform"]', 150); q("#resNote").value = "Prototype v1";
    await click('#resForm button[type="submit"]', 500);
    check("reserve with note", claimOf(p.id)?.uid === S.me.id && claimOf(p.id)?.note === "Prototype v1");
    await click('#dActs [data-act="release"]', 500); check("release from dossier", !claimOf(p.id));
    q("#dlg").close();
  });

  await step("all statuses render", async () => {
    for (const st of ["lapsed", "expired", "abandoned"]) {
      const p = S.patents.find(x => x.st === st); if (!p) { check("status present: " + st, false); continue; }
      await openSheet(p.id, "history"); await wait(600);
      check(`timeline for ${st}`, !!q("#dpanel svg.chart"));
      await renderTab("sources"); await wait(300);
      check(`sources for ${st}`, qa("#dpanel a.lcard").length >= 7);
      q("#dlg").close();
    }
  });

  await step("reservations", async () => {
    const now = Date.now(), iso = t => new Date(t).toISOString();
    const other = S.wall[2].id, tampered = S.wall[3].id, spoofed = S.wall[4].id;
    __seed("claims/u_other00000000000000000", { items: { [other]: { at: iso(now - 864e5), until: iso(now + 29 * 864e5), note: "In my garage" } } });
    __seed("claims/u_evil000000000000000000", { items: { [tampered]: { at: iso(now), until: iso(now + 3650 * 864e5) } } });
    __seed("claims/u_spoof00000000000000000", { uid: S.me.id, items: { [spoofed]: { at: iso(now), until: iso(now + 20 * 864e5) } } });
    await wait(400);
    check("other builder's hold shown", claimOf(other)?.uid === "u_other00000000000000000");
    check("uid inside a document can't impersonate me", claimOf(spoofed)?.uid === "u_spoof00000000000000000");
    check("held patent leaves my daily set", !S.wall.some(p => p.id === other));
    check("tampered hold ignored", !claimOf(tampered));
    const card = q("#wall .card:not(.feat)"), id = card.dataset.id;
    await click(card.querySelector('[data-act="reserve"]'), 500);
    check("reserve from card", claimOf(id)?.uid === S.me.id && !!q(`.card[data-id="${id}"] .resmark.mine`));
    const free = S.patents.filter(p => !claimOf(p.id)).slice(0, 5).map(p => p.id);
    for (const f of free.slice(0, 4)) { await reserve(f); await wait(80); }
    await reserve(free[4]); await wait(150);
    check("limit of 5", mine().length === 5 && !claimOf(free[4]), q("#toast").textContent);
    try { await S.db.doc("claims/u_other00000000000000000").set({ items: {} }); check("others' holds are protected", false); } catch { check("others' holds are protected", true); }
    // make one of mine expire soon so Renew shows on the bench
    const items = myItems(); items[free[0]].until = iso(now + 5 * 864e5); await writeMyClaims(items); await wait(200);
    await click('.tab[data-go="bench"]', 400);
    check("bench lists holds", qa("#resList .rowi").length === 5);
    const renewBtn = q('#resList [data-act="renew"]'); check("renew offered near expiry", !!renewBtn);
    if (renewBtn) { await click(renewBtn, 400); check("renew", daysLeft(claimOf(free[0])) >= 29); }
    await click('#resList [data-open]', 400); check("open from bench", q("#dlg").open); q("#dlg").close();
    for (const r of mine()) { await release(r.id); await wait(60); }
    check("release all", mine().length === 0);
  });

  await step("browse", async () => {
    await click('.tab[data-go="browse"]', 300);
    const total = S.patents.length;
    for (const sel of ['[data-st="lapsed"]', '[data-st="expired"]', '[data-st="abandoned"]']) { await click(sel, 200); const n = +q("#count").textContent.split(" ")[0]; check("status filter " + sel, n > 0 && n < total, n); }
    await click('[data-st=""]', 150);
    await click('[data-b="2"]', 150); check("build filter", filtered().every(p => p.b <= 2)); await click('[data-b=""]', 150);
    await click("#fSolo", 150); check("solo filter", filtered().every(p => p.ia)); await click("#fSolo", 150);
    await click("#fFree", 150); await click("#fFree", 150);
    const fb = qa("#fInd [data-ind]")[1]; await click(fb, 150); check("field filter", filtered().every(p => p.ind === fb.dataset.ind)); await click('#fInd [data-ind=""]', 150);
    for (const v of ["recent", "old", "az", "build"]) { q("#sort").value = v; q("#sort").dispatchEvent(new Event("change")); await wait(120); }
    check("sorting", qa("#grid .card").length === 24);
    await click("#more", 300); check("show more", qa("#grid .card").length === 48);
    q("#q").value = S.patents[0].n; q("#q").dispatchEvent(new Event("input")); await wait(400);
    check("search by number", qa("#grid .card").length >= 1); q("#q").value = ""; q("#q").dispatchEvent(new Event("input")); await wait(300);
  });

  await step("studio", async () => {
    await click('.tab[data-go="today"]', 300);
    await click('#wall .card:not(.feat) [data-act="reinvent"]', 300);
    check("studio opens on directions", q("#studio").open && /Directions/.test(q('.step[aria-current="step"]').textContent));
    await click("#genDirs", 400); check("directions generated", qa(".dir").length === 4);
    await click(qa(".dir")[1], 100); await click("#toShape", 200); check("shape step", q("#iName").value === "Direction 2");
    for (const k of ["improve", "concise", "detail"]) { await click(`[data-rw="${k}"]`, 300); check("rewrite " + k, q("#iDesc").value === "Rewritten description."); }
    await click("#sketchIdea", 500);
    const img = q("#ideaSketch img"), svg = img ? decodeURIComponent(img.src.split(",")[1]) : "";
    check("sketch my idea", !!img);
    check("sketch is sanitized", svg && !/script|onload|foreignObject|evil\.example/i.test(svg), svg.slice(0, 120));
    q("#iPitch").value = "Edited pitch"; await click('[data-step="0"]', 100); await click('[data-step="1"]', 100);
    check("edits kept across steps", q("#iPitch").value === "Edited pitch");
    await click("#saveShape", 300); check("save idea", S.ideas.some(i => i.name === "Direction 2"));
    await click("#toNovelty", 300); await click("#runNov", 400); check("novelty verdict", /promising/i.test(q(".verdict")?.textContent || ""));
    await click("#toDraft", 200); await click("#runDraft", 600); check("draft streamed", /Test Title/.test(q("#draft").value));
    await click("#saveDraft", 200); await click("#copyDraft", 200);
    await click("#dlDraft", 200); check("download", /provisional-draft\.md$/.test(window.__saved?.filename || ""));
    check("all four steps done", qa(".step.done").length >= 3);
    q("#studio").close(); await click('.tab[data-go="bench"]', 400);
    const cont = q('#ideaList [data-act="studio"]'); check("idea on bench", !!cont);
    await click(cont, 300); check("continue resumes at draft", /Provisional/.test(q('.step[aria-current="step"]').textContent)); q("#studio").close();
    await click("#ownIdea", 300); check("own idea starts at shape", /Shape/.test(q('.step[aria-current="step"]').textContent) && q('[data-step="0"]').disabled); q("#studio").close();
    const del = q('#ideaList [data-act="delidea"]'); await click(del, 100); check("delete asks to confirm", del.textContent === "Confirm delete");
    await click(del, 300);
  });

  await step("sketch for a patent without drawings", async () => {
    const p = S.patents[5], saved = { fig: p.fig, ns: p.ns, sh: p.sh };
    Object.assign(p, { fig: null, ns: 0, sh: 0 });
    await openSheet(p.id, "drawings"); await wait(500);
    const b = q('[data-act="sketchpatent"]'); check("generate offered when no drawings", !!b);
    if (b) { await click(b, 600); check("AI sketch shown and labeled", !!q("#skOut img") && /AI-generated/.test(q("#skOut").textContent)); }
    Object.assign(p, saved); q("#dlg").close();
  });

  const failed = results.filter(r => !r.ok);
  return { passed: results.length - failed.length, total: results.length, failed, errors };
};
