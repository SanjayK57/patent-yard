// Visual regression: full-page screenshots of the main pages at desktop and phone widths, light and dark, with motion
// settled, and an optional comparison against an earlier set.
//
//   node web/dev/visual.mjs http://localhost:8000 OUT                 # capture OUT/<page>-<width>-<theme>.png
//   node web/dev/visual.mjs http://localhost:8000 OUT --against GOLD  # capture, then compare with GOLD
//
// Use the sample site (web/dev/fixtures.py) for goldens: its data never changes, and it holds no real account.
// The comparison ignores anti-aliasing: a pixel counts as changed only when a channel moves by more than 48 of 255,
// and a page fails when its height changes or more than 0.5% of its pixels change. A failing page writes
// OUT/<name>.diff.png with the changed pixels in red. Needs Playwright (see check.mjs).
import { existsSync, readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { createRequire } from "node:module";

const [base0, out, flag, gold] = process.argv.slice(2);
if (!base0 || !out) { console.log("usage: node web/dev/visual.mjs BASE OUT [--against GOLD]"); process.exit(2); }
const base = base0.replace(/\/$/, "");
const load = async () => { try { return await import("playwright"); } catch { return createRequire((process.env.PLAYWRIGHT_DIR || ".") + "/")("playwright"); } };
const { chromium } = await load();
const browser = await chromium.launch({ headless: true, ...(process.env.CHROME ? { executablePath: process.env.CHROME } : {}) });
mkdirSync(out, { recursive: true });

// the patent page is the first card on the register unless PATENT names one
const PAGES = [["home", "/"], ["register", "/browse/"], ["patent", process.env.PATENT || ""], ["opportunities", "/opportunities/"],
  ["studio", "/studio/"], ["account", "/account/"], ["settings", "/settings/"], ["all", "/all/"], ["insights", "/insights/"]];
const SIZES = [[1440, 900], [390, 844]];
let failed = 0;

if (!PAGES[2][1]) {
  const p = await browser.newPage();
  await p.goto(base + "/browse/", { waitUntil: "load", timeout: 30000 });
  PAGES[2][1] = await p.$eval(".card h3 a, .row h3 a, [data-id] h3 a", a => a.getAttribute("href")).catch(() => "");
  await p.close();
}

for (const theme of ["light", "dark"])
  for (const [width, height] of SIZES) {
    const ctx = await browser.newContext({ viewport: { width, height }, colorScheme: theme, reducedMotion: "reduce", deviceScaleFactor: 1 });
    await ctx.addInitScript(t => { try { localStorage.setItem("patentyard.settings", JSON.stringify({ theme: t, motion: "reduce" })); } catch {} }, theme);
    for (const [name, path] of PAGES) {
      if (!path) continue;
      const page = await ctx.newPage();
      const res = await page.goto(base + path, { waitUntil: "load", timeout: 30000 }).catch(() => null);
      if (!res || res.status() >= 400) { await page.close(); continue; }  // e.g. All patents on a build without web/world
      await page.evaluate(() => document.fonts.ready);
      await page.waitForTimeout(900);
      const file = `${out}/${name}-${width}-${theme}.png`;
      await page.screenshot({ path: file, fullPage: true, animations: "disabled", caret: "hide" });
      await page.close();
      if (flag === "--against" && gold) failed += await compare(file, `${gold}/${name}-${width}-${theme}.png`);
    }
    await ctx.close();
  }

// pixel comparison in the browser: decode both PNGs on a canvas and count channels that moved past the threshold
async function compare(now, then) {
  const tag = now.split("/").pop();
  if (!existsSync(then)) { console.log(`new   ${tag} (no golden)`); return 0; }
  const page = await browser.newPage();
  const r = await page.evaluate(async ([a, b]) => {
    const img = async src => { const i = new Image(); i.src = "data:image/png;base64," + src; await i.decode(); return i; };
    const [x, y] = [await img(a), await img(b)];
    if (x.width !== y.width || x.height !== y.height) return { size: `${y.width}x${y.height} -> ${x.width}x${x.height}` };
    const c = new OffscreenCanvas(x.width, x.height), g = c.getContext("2d");
    g.drawImage(x, 0, 0); const p = g.getImageData(0, 0, x.width, x.height);
    g.drawImage(y, 0, 0); const q = g.getImageData(0, 0, x.width, x.height);
    let n = 0;
    for (let i = 0; i < p.data.length; i += 4) {
      const moved = Math.abs(p.data[i] - q.data[i]) > 48 || Math.abs(p.data[i + 1] - q.data[i + 1]) > 48 || Math.abs(p.data[i + 2] - q.data[i + 2]) > 48;
      if (moved) { n++; p.data[i] = 255; p.data[i + 1] = 0; p.data[i + 2] = 0; } else p.data[i + 3] = 40;
    }
    g.clearRect(0, 0, x.width, x.height); g.putImageData(p, 0, 0);
    const blob = await c.convertToBlob();
    const diff = await new Promise(ok => { const f = new FileReader(); f.onload = () => ok(f.result.split(",")[1]); f.readAsDataURL(blob); });
    return { share: n / (x.width * x.height), diff };
  }, [readFileSync(now).toString("base64"), readFileSync(then).toString("base64")]);
  await page.close();
  if (r.size) { console.log(`FAIL  ${tag} height changed ${r.size}`); return 1; }
  if (r.share > 0.005) { writeFileSync(now.replace(/\.png$/, ".diff.png"), Buffer.from(r.diff, "base64")); console.log(`FAIL  ${tag} ${(r.share * 100).toFixed(2)}% changed`); return 1; }
  console.log(`same  ${tag}`);
  return 0;
}

await browser.close();
if (flag === "--against") console.log(failed ? `${failed} pages changed` : "no visual changes");
process.exit(failed ? 1 : 0);
