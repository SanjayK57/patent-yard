// Browser checks against a running preview: the smoke suites (smoke.js, with the mock backend standing in for
// Supabase, so no real account is touched) and a no-sideways-scroll check at phone and tablet widths.
//
//   node web/dev/check.mjs http://localhost:8000
//
// Needs Playwright with Chromium: cd web/dev && npm install --no-save playwright && npx playwright install chromium
// (or point PLAYWRIGHT_DIR at an existing install and CHROME at a Chromium binary).
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";

const base = (process.argv[2] || "http://localhost:8000").replace(/\/$/, "");
const load = async () => { try { return await import("playwright"); } catch { return createRequire((process.env.PLAYWRIGHT_DIR || ".") + "/")("playwright"); } };
const { chromium } = await load();
const here = new URL(".", import.meta.url);
const inject = readFileSync(new URL("smoke.js", here), "utf8") + "\n" + readFileSync(new URL("mock-backend.js", here), "utf8");
const browser = await chromium.launch({ headless: true, ...(process.env.CHROME ? { executablePath: process.env.CHROME } : {}) });
let failed = 0;

const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
await ctx.addInitScript(inject);
const first = await ctx.newPage();
await first.goto(base + "/browse/", { waitUntil: "load", timeout: 30000 });
await first.waitForSelector(".card h3 a", { timeout: 15000 });
const patent = process.env.PATENT || await first.$eval(".card h3 a", a => a.getAttribute("href"));
// the suites expect the real register (its words, numbers and page sizes); on the sample site (fixtures.py) only
// the ones that hold for any data run, plus the layout checks below
const sample = !!(await first.$(".devbanner"));
await first.close();
const suites = [["/", "header"], ["/", "home"], ["/browse/", "browse"], [patent, "patent"], ["/studio/", "studio"], ["/account/", "account"]];
if (sample) console.log("sample data: running the data-independent checks only");
for (const [path, suite] of sample ? suites.filter(([, s]) => s === "account") : suites) {
  const p = await ctx.newPage();
  await p.goto(base + path, { waitUntil: "load", timeout: 30000 });
  await p.waitForTimeout(1200);
  const r = await p.evaluate(s => window.runSuite(s), suite).catch(e => ({ suite, passed: 0, total: 1, failed: [{ n: "runner", info: e.message }] }));
  failed += r.total - r.passed;
  console.log(`${r.suite}: ${r.passed}/${r.total}`, r.failed.map(f => `FAIL ${f.n} ${f.info ?? ""}`).join(" | "));
  await p.close();
}
// a fresh browser for the layout pass: the account suite can leave this one busy
await browser.close();
const browser2 = await chromium.launch({ headless: true, ...(process.env.CHROME ? { executablePath: process.env.CHROME } : {}) });

for (const width of [320, 390, 768]) {
  console.log(`layout at ${width}px`);
  const p = await browser2.newPage({ viewport: { width, height: 800 } });
  const errors = [];
  p.on("pageerror", e => errors.push(e.message));
  for (const path of ["/", "/browse/", patent, "/studio/", "/account/", "/settings/", "/how-it-works/"]) {
    await p.goto(base + path, { waitUntil: "load", timeout: 30000 });
    await p.waitForTimeout(400);
    if (errors.length) { failed++; console.log(`FAIL ${path} script error: ${errors.splice(0).join("; ")}`); }
    const w = await p.evaluate(() => document.documentElement.scrollWidth);
    if (w > width) { failed++; console.log(`FAIL ${path} at ${width}px scrolls sideways (${w}px wide)`); }
  }
  await p.close();
}
console.log(failed ? `${failed} checks failed` : "all checks passed");
await browser2.close();
process.exit(failed ? 1 : 0);
