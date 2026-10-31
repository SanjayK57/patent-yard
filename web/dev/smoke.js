// Click-through checks for a local copy made by dev/preview.py (with the mock backend).
// In the browser console of each page:  await runSuite("home" | "browse" | "patent" | "studio" | "account")
(() => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const q = s => document.querySelector(s), qa = s => [...document.querySelectorAll(s)];
  const errors = [];
  addEventListener("error", e => errors.push("error: " + e.message));
  addEventListener("unhandledrejection", e => errors.push("rejection: " + (e.reason?.message || e.reason)));
  // Claude hand-off and downloads are captured instead of leaving the page.
  window.__opened = []; window.open = (u) => { window.__opened.push(u); return null; };
  const until = async (fn, ms = 4000) => { const t = Date.now(); while (Date.now() - t < ms) { const v = await fn(); if (v) return v; await wait(60); } return null; };

  const suites = {
    async header(check) {
      const hq = q("#hq"); hq.value = "wrench"; hq.dispatchEvent(new Event("input"));
      check("search suggestions", !!(await until(() => !q("#hqList").hidden && q("#hqList a[href^='/patents/']"))));
      hq.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowDown", bubbles: true }));
      check("arrow keys select", q("#hqList a").getAttribute("aria-selected") === "true");
      check("see all results link", qa("#hqList li a").some(a => /\/browse\/\?q=wrench/.test(a.getAttribute("href"))));
      hq.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true })); check("escape closes", q("#hqList").hidden);
      hq.value = "US 11,112,282"; hq.dispatchEvent(new Event("input"));
      check("patent number jumps", !!(await until(() => q("#hqList a[href='/patents/11112282']"))));
      hq.value = "zzqqxx"; hq.dispatchEvent(new Event("input"));
      check("no matches says so", !!(await until(() => q("#hqList .none"))));
      hq.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
      document.dispatchEvent(new KeyboardEvent("keydown", { key: "/", bubbles: true })); check("slash focuses search", document.activeElement === hq || !hq.offsetParent, hq.offsetParent ? "" : "search box hidden at this width");
      check("footer totals", !!(await until(() => /US patents · status last checked/.test(q("#footStat").textContent))), q("#footStat").textContent);
    },
    async home(check) {
      check("today's picks", qa("#today .bento .card").length >= 6 && !!q("#today .bento .card.feat"));
      check("stat band filled", qa(".statband b").every(b => b.textContent.trim()));
      check("field chips", qa(".fchips .fchip").length >= 10);
      check("hero search goes to browse", q(".bigsearch").getAttribute("action") === "/browse/" && !!q("#heroQ"));
      await wait(3200);
      const cv = q("#plot"), px = cv.getContext("2d").getImageData(0, 0, cv.width, cv.height).data;
      let ink = 0; for (let i = 3; i < px.length; i += 400) ink += px[i] > 0;
      check("hero drawing plotted", document.hidden ? cv.width > 0 : ink > 20, document.hidden ? "tab hidden: plotting started, frames paused" : ink);
      check("every card image loads", (await until(() => qa(".card img").filter(i => i.loading !== "lazy").every(i => i.complete && i.naturalWidth > 0))) !== null);
    },
    async features(check) {  // run on the home page; then features2 on /saved/
      check("ticker of new patents", qa(".ticker .ttrack > a").length >= 10);
      await wait(1500);
      check("counters finish on the real number", qa("[data-count]").every(el => el.textContent.replace(/,/g, "") === el.dataset.count));
      document.dispatchEvent(new KeyboardEvent("keydown", { key: "k", ctrlKey: true, bubbles: true }));
      check("Ctrl+K opens the palette", !!(await until(() => q("#cmdk")?.open)));
      check("palette lists pages", qa("#cmdList [data-go]").length >= 8);
      const cq = q("#cmdQ"); cq.value = "wrench"; cq.dispatchEvent(new Event("input"));
      check("palette finds patents", !!(await until(() => qa('#cmdList [data-go^="/patents/"]').length)));
      cq.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowDown", bubbles: true }));
      check("palette arrow keys", qa("#cmdList [aria-selected=true]").length === 1);
      q("#cmdk").close();
      localStorage.removeItem("patentyard.saved");
      const card = q("#today .card"), sb = card.querySelector(".savebtn");
      check("cards carry a save button", !!sb);
      sb.click(); check("save a card", sb.getAttribute("aria-pressed") === "true" && JSON.parse(localStorage.getItem("patentyard.saved")).length === 1);
      location.href = "/saved/"; return "reload";
    },
    async features2(check) {
      check("saved page lists it", !!(await until(() => qa("#savedGrid .card").length === 1)) && q("#savedEmpty").hidden);
      q("#savedGrid .savebtn").click(); check("unsave", !!(await until(() => !q("#savedEmpty").hidden)));
      const { randomPatent } = await import("/assets/js/catalog.js");
      const p = await randomPatent(); check("surprise picks a patent with drawings", p && p.fig && !p.pending, p && p.id);
    },
    async insights(check) {
      check("charts present", !!q(".linechart .line") && qa(".hrow").length >= 10 && qa(".vcol").length === 3);
      qa(".reveal").forEach(e => { e.scrollIntoView(); if (document.hidden) e.classList.add("in"); }); await wait(1500);  // a hidden tab gets no scroll events
      check("bars animate to size", parseFloat(getComputedStyle(q(".hbar i")).width) > 20);
      check("owners listed", qa(".owners li").length >= 5);
    },
    async browse(check) {
      const n = () => +q("#count").textContent.replace(/,/g, "").split(" ")[0];
      const cards = () => qa("#grid .card:not(.skel)");
      const settle = async () => { await wait(60); await until(() => !q("#grid").classList.contains("busy")); await wait(30); };
      const total = await until(() => /of [\d,]+ patents/.test(q("#count").textContent) && +q("#count").textContent.replace(/,/g, "").split(" of ")[1].split(" ")[0]);
      check("count shown", n() === total && total > 300, q("#count").textContent);
      check("first page of 48", cards().length === 48);
      q("#more").click(); check("show more", !!(await until(() => cards().length === 96)));
      for (const st of ["lapsed", "expired", "abandoned"]) {
        q(`#filters [data-st="${st}"]`).click(); await settle();
        check("status " + st, n() > 0 && n() < total && cards().length && cards().every(c => c.querySelector(".over .badge." + st)), n());
      }
      q('#filters [data-st=""]').click(); await settle();
      q('#filters [data-b="2"]').click(); await settle(); check("build filter", cards().length && cards().every(c => /Weekend|Garage/.test(c.querySelector(".cmeta").textContent))); q('#filters [data-b=""]').click(); await settle();
      const before = location.search; cards()[0].querySelector(".cmeta").click(); await wait(30); check("clicking a card doesn't change filters", location.search === before);
      q("#fSolo").click(); await settle(); check("solo filter", cards().every(c => /None recorded/.test(c.querySelector(".cmeta").textContent))); q("#fSolo").click(); await settle();
      q("#fFig").click(); await settle(); check("with drawings", cards().every(c => c.querySelector(".fig img"))); q("#fFig").click(); await settle();
      const f = qa("#fInd [data-ind]")[2]; f.click(); await settle(); check("field filter", cards().every(c => c.querySelector(".fieldname").textContent.startsWith(f.childNodes[0].textContent.trim())) && location.search.includes("field=" + f.dataset.ind)); q('#fInd [data-ind=""]').click(); await settle();
      const box = q("#q"); box.value = "wrench"; box.dispatchEvent(new Event("input")); await wait(260); await settle();
      check("search", n() >= 1 && n() < 200 && location.search.includes("q=wrench") && /match/.test(q("#count").textContent), n());
      box.value = "wrenches"; box.dispatchEvent(new Event("input")); await wait(260); await settle(); check("plural finds the same", n() >= 1);
      box.value = "qqzzxx"; box.dispatchEvent(new Event("input")); await wait(260); await settle(); check("empty state", !q("#empty").hidden);
      box.value = ""; box.dispatchEvent(new Event("input")); await wait(260); await settle();
      const { patentNumber } = await import("/assets/js/catalog.js");
      check("patent numbers recognized", patentNumber("US 11,112,282 B2") === "11112282" && patentNumber("2015/0123456") === "20150123456" && patentNumber("wrench") === null);
      const sort = q("#sort"); sort.value = "recent"; sort.dispatchEvent(new Event("change")); await settle();
      const when = cards().map(c => Date.parse("1 " + c.querySelectorAll(".cmeta span")[1].textContent)).filter(x => !isNaN(x));
      check("most recently freed first", when.length > 10 && when.every((x, k) => !k || x <= when[k - 1]));
      sort.value = "build"; sort.dispatchEvent(new Event("change")); await settle();
      q("#fFree").click(); await settle(); check("hide reserved", !q("#grid .resmark")); q("#fFree").click();
    },
    async patent(check) {
      for (const s of ["overview", "drawings", "claims", "description", "history", "sources"]) check("section " + s, !!q("#" + s));
      check("toc", qa(".toc a").length === 6);
      check("timeline graphic", !!q("#history svg.chart"));
      check("source links", qa("#sources a.lcard").length >= 8 && qa("#sources a.lcard").every(a => a.href.startsWith("https://")));
      const sheets = +q("#patent").dataset.sheets;
      if (sheets) {
        q("[data-sheet='0']").click(); await wait(100);
        check("viewer opens", q("#viewer").open && q("#viewer img").complete !== undefined);
        if (sheets > 1) { q('#viewer [data-step="1"]').click(); await wait(50); check("viewer next", /Sheet 2/.test(q("#viewer .vbar").textContent)); }
        q("#viewer [data-zoom]").click(); check("viewer zoom", q("#vStage").classList.contains("zoom"));
        q("#viewer [data-close]").click(); check("viewer closes", !q("#viewer").open);
      }
      const more = q("#descMore"); if (more) { more.click(); check("full description", !q("#desc").classList.contains("clamped")); more.click(); }
      check("claim map", qa(".cgroup").length >= 1 && qa(".claimlist li.ind").length === qa(".cgroup").length);
      (q(".cdeps a") || q(".ci")).click(); await wait(50); check("claim map links to claim", location.hash.startsWith("#claim-"));
      check("verified date filled in", !!(await until(() => !q("#vbadge").hidden && /Verified/.test(q("#vbadge").textContent))));
      q("#copyLink").click(); await wait(150); check("copy link", /Copied/.test(q("#copyLink").textContent) || /http/.test(q("#toast").textContent));
      q('[data-kit="workshop"]').click();
      check("kit opens", !!(await until(() => qa("#kit .task").length === 7)));
      const prompt = () => q("#kPrompt").value, num = q("#patent").dataset.n;
      check("workshop prompt names the patent", prompt().includes(num) && /Step 1/.test(prompt()));
      q('#kit [data-task="novelty"]').click(); check("task switch", /prior-art check/i.test(prompt()));
      q("#kIdea").value = "Add a phone app that logs each use"; q("#kIdea").dispatchEvent(new Event("input")); check("idea in prompt", prompt().includes("logs each use"));
      q("#kOpen").click(); await wait(100); check("opens Claude", window.__opened.some(u => u.startsWith("https://claude.ai/new")), window.__opened.at(-1));
      // jsPDF saves through a temporary <a download>; capture that instead of downloading
      let saved = null, lastBlob = null;
      const origURL = URL.createObjectURL; URL.createObjectURL = b => { lastBlob = b; return origURL(b); };  // the policy blocks fetch(blob:), so keep the Blob itself
      const orig = HTMLAnchorElement.prototype.dispatchEvent, origClick = HTMLAnchorElement.prototype.click;
      const grab = function (...a) { if (this.download) { saved = { name: this.download, href: this.href }; return true; } return (a.length ? orig : origClick).apply(this, a); };
      HTMLAnchorElement.prototype.dispatchEvent = grab; HTMLAnchorElement.prototype.click = grab;
      const t0 = Date.now(); q("#kPdf").click();
      await until(() => saved, 25000);
      HTMLAnchorElement.prototype.dispatchEvent = orig; HTMLAnchorElement.prototype.click = origClick; URL.createObjectURL = origURL;
      if (saved && lastBlob) { saved.size = lastBlob.size; saved.pdf = (await lastBlob.slice(0, 5).text()) === "%PDF-"; }
      check("PDF brief made", saved?.pdf && saved.size > 20000 && /^patent-yard-brief-US-/.test(saved.name), JSON.stringify(saved && { ...saved, href: undefined }) + " " + (Date.now() - t0) + "ms");
      q("#kit [data-close]").click();
      // reservations (mock backend): sign in, reserve, release
      if (window.__PY_MOCK) {
        await window.__PY_MOCK.signOut().catch(() => {});
        try { await window.__PY_MOCK.signUp("smoke@example.test", "password123", "Smoke Tester"); } catch { await window.__PY_MOCK.signIn("smoke@example.test", "password123"); }
        location.reload(); return "reload";
      }
    },
    async contact(check) {
      await until(() => !q("#contactForm").hidden);
      q("#cBody").value = "Smoke test message"; q("#cEmail").value = "me@example.test"; q("#contactForm").requestSubmit();
      check("contact form sends", !!(await until(() => /sent/.test(q("#cStatus").textContent))) && JSON.parse(localStorage.getItem("pymock")).messages.some(m => m.body === "Smoke test message"));
      q("#cBody").value = ""; q("#contactForm").requestSubmit(); await wait(50); check("empty message refused", /first/.test(q("#cStatus").textContent));
    },
    async patent2(check) {  // after the reload above, signed in
      await until(() => !q("#reportBtn").hidden);
      q("#reportBtn").click(); await wait(50); q("#repBody").value = "Status changed"; q("#repForm").requestSubmit();
      check("report a problem", !!(await until(() => !q("#repDlg").open)) && JSON.parse(localStorage.getItem("pymock")).messages.some(m => m.kind === "report" && m.patent === q("#patent").dataset.id));
      const btn = q("#reserveBtn");
      await until(() => !btn.hidden && btn.dataset.mode);
      check("reserve button ready", btn.dataset.mode === "reserve", btn.dataset.mode);
      btn.click(); await wait(100); q("#resNote").value = "Prototype in my garage"; q("#resForm button[type=submit]").click();
      await until(() => btn.dataset.mode === "release");
      check("reserved", /Reserved by you/.test(q("#resline").textContent) && /garage/.test(q("#resline").textContent));
      btn.click(); await until(() => btn.dataset.mode === "reserve");
      check("released", btn.dataset.mode === "reserve");
    },
    async studio(check) {
      q("#pq").value = "wrench"; q("#pq").dispatchEvent(new Event("input"));
      check("picker finds patents", !!(await until(() => qa("#pickList [data-pick]").length)));
      q("#pickList [data-pick]").click(); await until(() => q("#picked .srcline"));
      check("patent picked", /US /.test(q("#picked").textContent));
      check("tasks", qa("#tasks .task").length === 7);
      q("#iName").value = "Torque-limiting smart wrench"; q("#iName").dispatchEvent(new Event("input"));
      check("prompt has idea and patent", q("#prompt").value.includes("Torque-limiting smart wrench") && q("#prompt").value.includes("SOURCE PATENT"));
      q("#unpick").click(); await wait(50); check("own idea without patent", !q("#prompt").value.includes("SOURCE PATENT") && qa("#tasks .task").length === 5);
      q("#saveIdea").click(); await wait(300);
      check("save idea", /Saved|account/i.test(q("#studioStatus").textContent) || location.pathname === "/account/", q("#studioStatus").textContent);
    },
    async settings(check) {  // run on /settings/ while signed in (after "account"), then settings2 after the reload
      const attr = n => document.documentElement.getAttribute(n);
      const pick = async (setting, value) => { q(`[data-setting="${setting}"] [data-value="${value}"]`).click(); await wait(30); };
      check("all groups shown", qa("[data-setting]").length === 5 && qa('[data-setting] [aria-checked="true"]').length === 5);
      await pick("theme", "dark"); check("dark theme applies", attr("data-theme") === "dark" && getComputedStyle(document.body).backgroundColor === "rgb(14, 15, 17)");
      await pick("theme", "light"); check("light theme applies", attr("data-theme") === "light" && getComputedStyle(document.body).backgroundColor === "rgb(246, 246, 244)");
      await pick("drawings", "original"); check("original drawings", attr("data-drawings") === "original");
      await pick("text", "large"); check("large text", attr("data-text") === "large");
      await pick("motion", "reduce"); check("reduce motion", attr("data-motion") === "reduce" && getComputedStyle(q(".btn")).transitionDuration === "0s");
      await pick("sort", "added");
      q("#themeBtn").click(); await wait(30); check("header switch flips the theme", attr("data-theme") === "dark" && /light mode/.test(q("#themeBtn").getAttribute("aria-label")));
      await until(() => !q("#acctIn").hidden);
      check("account section signed in", !q("#acctIn").hidden && /@/.test(q("#setEmail").textContent));
      q("#setName").value = "Renamed Builder"; q("#nameForm").requestSubmit(); check("display name saved", !!(await until(() => /saved/.test(q("#acctStatus").textContent))));
      q("#setPw").value = "short"; q("#pwForm").requestSubmit(); await wait(50); check("short password refused", /8 characters/.test(q("#acctStatus").textContent));
      q("#setPw").value = "longerpassword"; q("#pwForm").requestSubmit(); check("password changed", !!(await until(() => /changed/.test(q("#acctStatus").textContent))));
      location.reload(); return "reload";
    },
    async settings2(check) {
      const attr = n => document.documentElement.getAttribute(n);
      check("settings survive a reload", attr("data-theme") === "dark" && attr("data-text") === "large" && attr("data-drawings") === "original" && attr("data-motion") === "reduce");
      check("controls show saved values", q('[data-setting="sort"] [aria-checked="true"]').dataset.value === "added");
      const { getSettings } = await import("/assets/js/app.js"); check("default sort stored", getSettings().sort === "added");
      q("#clearLocal").click(); await wait(50);
      check("clear resets everything", !attr("data-theme") && !attr("data-text") && !attr("data-drawings") && !attr("data-motion") && q('[data-setting="theme"] [aria-checked="true"]').dataset.value === "system");
    },
    async redirects(check) {  // ?next= only ever leads to a page on this site
      const { safeNext } = await import("/assets/js/app.js");
      const o = "https://patentyard.pages.dev";
      check("no next stays on bench", safeNext(null, o) === "" && safeNext("", o) === "");
      check("next to a page", safeNext("/browse/?q=wrench", o) === "/browse/?q=wrench");
      check("protocol-relative refused", safeNext("//evil.example/x", o) === "");
      check("backslash trick refused", safeNext("/\\evil.example/x", o) === "");
      check("other site refused", safeNext("https://evil.example/", o) === "" && safeNext("javascript:alert(1)", o) === "");
      check("account page not a loop", safeNext("/account/", o) === "");
    },
    async account(check) {
      const m = window.__PY_MOCK;
      await until(() => q("#loadView").hidden);
      if (!q("#benchView").hidden) { check("bench shown when signed in", true); }
      else {
        q('[data-mode="up"]').click(); q("#aName").value = "Bench Tester"; q("#aEmail").value = "bench@example.test"; q("#aPw").value = "password123";
        q("#authForm").requestSubmit();
        check("sign up opens bench", !!(await until(() => !q("#benchView").hidden)));
      }
      const { cards } = await import("/assets/js/catalog.js");
      const ids = (await cards([0, 1, 2, 3, 4, 5])).map(c => c.id);
      for (const id of ids.slice(0, 5)) await m.reserve(id, "");
      let e6; try { await m.reserve(ids[5], ""); } catch (e) { e6 = e.code; } check("limit of 5", e6 === "limit");
      window.__mockSeed(s => { s.res[ids[0]].expires_at = new Date(Date.now() + 3 * 864e5).toISOString(); });
      await m.saveIdea({ id: "11111111-1111-4111-8111-111111111111", pid: ids[1], name: "Saved invention", pitch: "Pitch" });
      location.reload(); return "reload";
    },
    async google(check) {
      await until(() => q("#loadView").hidden);
      if (!q("#benchView").hidden) { await window.__PY_MOCK.signOut(); location.reload(); return "reload"; }
      check("google button shown", !!(await until(() => !q("#oauthRow").hidden)));
      q('[data-mode="up"]').click(); check("create account mode", /Create your free account/.test(q("#authTitle").textContent) && !q("#nameRow").hidden);
      q("#aPw").value = "Longer pass 123"; q("#aPw").dispatchEvent(new Event("input")); check("strength meter", parseInt(q("#pwMeter i").style.width) >= 60);
      q("#pwShow").click(); check("show password", q("#aPw").type === "text"); q("#pwShow").click();
      q("#forgotBtn").hidden || q("#forgotBtn").click();
      q('[data-mode="in"]').click(); q("#forgotBtn").click(); check("reset mode", /Reset your password/.test(q("#authTitle").textContent) && q("#pwRow").hidden);
      q("#aEmail").value = "nobody@example.test"; q("#authForm").requestSubmit();
      check("reset shows check-your-email", !!(await until(() => /Check your email/.test(q("#authDone").textContent))));
      q("#backIn").click(); check("back to sign in", !q("#authMain").hidden && /Welcome back/.test(q("#authTitle").textContent));
      q("#aEmail").value = "x@example.test"; q("#aPw").value = "wrongpassword"; q("#authForm").requestSubmit();
      check("wrong password explained", !!(await until(() => /don't match/.test(q("#authStatus").textContent))));
      q("#googleBtn").click(); return "reload";
    },
    async google2(check) {
      check("back from Google on the bench", !!(await until(() => !q("#benchView").hidden)) && /google.tester/.test(q("#benchWho").textContent));
      check("welcome shown", /Welcome, Google Tester/.test(q("#welcome").textContent));
      check("account menu in header", !!(await until(() => q(".acctmenu>button"))));
      q(".acctmenu>button").click(); check("menu opens", !q(".acctmenu .menu").hidden && document.activeElement.closest(".menu"));
      document.body.click(); check("menu closes", q(".acctmenu .menu").hidden);
    },
    async account2(check) {
      await until(() => !q("#benchView").hidden && q("#resList .rowi"));
      check("bench lists 5 holds", qa("#resList .rowi").length === 5);
      check("idea listed", /Saved invention/.test(q("#ideaList").textContent));
      const renew = q("#resList [data-renew]"); check("renew offered near expiry", !!renew);
      renew?.click(); await wait(300); check("renewed", !q("#resList [data-renew]"));
      q("#resList [data-release]").click(); await until(() => qa("#resList .rowi").length === 4); check("release from bench", qa("#resList .rowi").length === 4);
      const del = q("#ideaList [data-del]"); del.click(); del.click(); await until(() => !/Saved invention/.test(q("#ideaList").textContent)); check("delete idea", !/Saved invention/.test(q("#ideaList").textContent));
      for (const r of (await window.__PY_MOCK.reservations()).filter(r => r.mine)) await window.__PY_MOCK.release(r.patent_id);
      q("#signOut").click(); await until(() => location.pathname === "/"); check("sign out", true);
    },
  };

  window.lastSuite = name => JSON.parse(localStorage.getItem("pysmoke." + name) || "[]");
  window.runSuite = async name => {
    const results = [];
    const check = (n, ok, info = "") => { results.push({ n, ok: !!ok, info: String(info ?? "").slice(0, 200) }); localStorage.setItem("pysmoke." + name, JSON.stringify(results)); };
    let next;
    try { next = await suites[name](check); } catch (e) { check(name + " threw", false, e.stack || e.message); }
    const failed = results.filter(r => !r.ok);
    return { suite: name, passed: results.length - failed.length, total: results.length, failed, errors: [...errors], next };
  };
})();
