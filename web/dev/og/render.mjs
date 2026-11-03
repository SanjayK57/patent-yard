// The share card (Open Graph image) for links to Patent Yard: node web/dev/og/render.mjs web/dev/og/card.html web/static/og.png
// The drawing is US 11,154,768 B2, sheet 1, as published. Needs Playwright (PLAYWRIGHT_DIR and CHROME, see check.mjs).
import { createRequire } from "node:module";
const { chromium } = createRequire((process.env.PLAYWRIGHT_DIR || ".") + "/")("playwright");
const b = await chromium.launch({ headless: true, ...(process.env.CHROME ? { executablePath: process.env.CHROME } : {}) });
const p = await b.newPage({ viewport: { width: 1200, height: 630 }, deviceScaleFactor: 1 });
await p.goto(new URL(process.argv[2], "file://" + process.cwd() + "/").href); await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(300);
await p.screenshot({ path: process.argv[3] }); await b.close();
