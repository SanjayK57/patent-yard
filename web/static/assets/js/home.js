// Home hero: redraws today's featured drawing cell by cell, like a pen plotter. The plain image stays if anything fails.
import { $, reducedMotion, listOf, miniCard, decorateCards, local } from "./app.js";

// "Recently viewed": the last patents opened in this browser
const recent = listOf("recent").slice(0, 4);
if (recent.length && $("#recentSec")) {
  $("#recentGrid").innerHTML = recent.map(miniCard).join("");
  decorateCards($("#recentGrid"));
  $("#recentSec").hidden = false;
  $("#recentClear").addEventListener("click", () => { local("recent", []); $("#recentSec").hidden = true; });
}
const box = document.getElementById("plotbox");
const reduced = reducedMotion();

// The pen follows the linework: from each inked cell it moves to the neighbouring one that keeps its direction best,
// lifts to the nearest undrawn line when a stroke ends, and the ink settles in behind it over a fraction of a second.
function strokeOrder(ink, cols, rows) {
  const left = new Set(ink), order = [], key = (x, y) => y * cols + x;
  let cur = ink[0], dx = 1, dy = 0;
  while (left.size) {
    if (!left.has(cur)) {  // pen up: the nearest cell still to draw
      const cx = cur % cols, cy = Math.floor(cur / cols);
      let best = -1, bd = Infinity;
      for (const k of left) { const d = (k % cols - cx) ** 2 + (Math.floor(k / cols) - cy) ** 2; if (d < bd) { bd = d; best = k; if (d <= 2) break; } }
      cur = best; dx = 0; dy = 0;
    }
    left.delete(cur); order.push(cur);
    const x = cur % cols, y = Math.floor(cur / cols);
    let next = -1, score = -Infinity;
    for (let oy = -1; oy <= 1; oy++) for (let ox = -1; ox <= 1; ox++) {
      if (!ox && !oy) continue;
      const nx = x + ox, ny = y + oy, k = key(nx, ny);
      if (nx < 0 || ny < 0 || nx >= cols || ny >= rows || !left.has(k)) continue;
      const sc = (ox * dx + oy * dy) / Math.hypot(ox, oy) - (ox && oy ? .05 : 0);
      if (sc > score) { score = sc; next = k; }
    }
    if (next >= 0) { dx = next % cols - x; dy = Math.floor(next / cols) - y; cur = next; }
    else cur = -1;
    if (cur === -1 && left.size) cur = order[order.length - 1];
  }
  return order;
}

async function plot() {
  const img = new Image();
  await new Promise((ok, err) => { img.onload = ok; img.onerror = err; img.src = box.dataset.src; });
  const cv = document.getElementById("plot"), pen = document.getElementById("pen"), still = box.querySelector("img");
  const dpr = Math.min(2, devicePixelRatio || 1);
  const W = cv.width = pen.width = Math.round(box.clientWidth * dpr), H = cv.height = pen.height = Math.round(box.clientHeight * dpr);
  if (!W || !H) return;
  const ctx = cv.getContext("2d"), pc = pen.getContext("2d");
  const sc = Math.min(W / img.width, H / img.height) * .88, dw = Math.max(1, Math.round(img.width * sc)), dh = Math.max(1, Math.round(img.height * sc));
  const ox = Math.round((W - dw) / 2), oy = Math.round((H - dh) / 2);
  const off = document.createElement("canvas"); off.width = dw; off.height = dh;
  const o = off.getContext("2d"); o.drawImage(img, 0, 0, dw, dh);
  const css = getComputedStyle(document.documentElement);
  // ink: the page's ink on an inverted (dark) sheet, near-black on a white one
  const hex = css.getPropertyValue("--fig-filter").trim() === "none" ? "#161A1D" : css.getPropertyValue("--ink").trim();
  const [r, g, b] = hex.replace("#", "").match(/../g).map(h => parseInt(h, 16));
  const d = o.getImageData(0, 0, dw, dh);
  for (let i = 0; i < d.data.length; i += 4) { const a = 255 - d.data[i]; d.data[i] = r; d.data[i + 1] = g; d.data[i + 2] = b; d.data[i + 3] = a; }
  o.putImageData(d, 0, 0);
  const C = Math.max(6, Math.round(7 * dpr)), cols = Math.ceil(dw / C), rows = Math.ceil(dh / C), ink = [];
  for (let gy = 0; gy < rows; gy++) for (let gx = 0; gx < cols; gx++) {
    const x0 = gx * C, y0 = gy * C, x1 = Math.min(dw, x0 + C), y1 = Math.min(dh, y0 + C);
    find: for (let yy = y0; yy < y1; yy += 2) for (let xx = x0; xx < x1; xx += 2) if (d.data[(yy * dw + xx) * 4 + 3] > 90) { ink.push(gy * cols + gx); break find; }
  }
  if (!ink.length) return;
  const order = strokeOrder(ink, cols, rows);
  const cell = k => { const x = (k % cols) * C, y = Math.floor(k / cols) * C; return [x, y, Math.min(C, dw - x), Math.min(C, dh - y)]; };
  const stamp = (c, k) => { const [x, y, w, h] = cell(k); c.drawImage(off, x, y, w, h, ox + x, oy + y, w, h); };
  // paced by the clock, not by frames: about 3 seconds, easing in and out, whatever the frame rate
  const DUR = 3000, FADE = 220, dot = css.getPropertyValue("--accent").trim(), t0 = performance.now(), wet = [];
  const ease = t => (t < .5 ? 4 * t * t * t : 1 - (-2 * t + 2) ** 3 / 2);
  let i = 0;
  while (i < order.length || wet.length) {
    await new Promise(requestAnimationFrame);
    const now = performance.now();
    const to = Math.min(order.length, Math.max(i + 1, Math.ceil(order.length * ease(Math.min(1, (now - t0) / DUR)))));
    for (; i < to; i++) wet.push([order[i], now]);
    if (still.style.visibility !== "hidden") still.style.visibility = "hidden";  // swap only once the pen is drawing
    pc.clearRect(0, 0, W, H);
    while (wet.length && now - wet[0][1] >= FADE) stamp(ctx, wet.shift()[0]);  // dry ink joins the drawing
    for (const [k, t] of wet) { pc.globalAlpha = Math.min(1, (now - t) / FADE); stamp(pc, k); }
    if (i < order.length) {
      const [x, y, w, h] = cell(order[i - 1]), px = ox + x + w / 2, py = oy + y + h / 2;
      pc.globalAlpha = .12; pc.strokeStyle = `rgb(${r},${g},${b})`; pc.lineWidth = dpr;
      pc.beginPath(); pc.moveTo(px, 0); pc.lineTo(px, H); pc.moveTo(0, py); pc.lineTo(W, py); pc.stroke();
      pc.globalAlpha = 1; pc.fillStyle = dot; pc.beginPath(); pc.arc(px, py, 3.5 * dpr, 0, 7); pc.fill();
    }
  }
  pc.globalAlpha = 1; pc.clearRect(0, 0, W, H);
}
if (box && !reduced) plot().catch(() => {});

// the 1:1 call-out: a pinned box that magnifies the part of the plate under the pointer (a tap does the same on touch)
const loupe = box?.querySelector(".loupe"), mark = box?.querySelector(".lmark"), ZOOM = 3;
function look(e) {
  const img = box.querySelector("img"), b = box.getBoundingClientRect();
  // the drawing's drawn rectangle inside its contain-fitted box
  const ir = img.getBoundingClientRect(), s = Math.min(ir.width / img.naturalWidth, ir.height / img.naturalHeight);
  const w = img.naturalWidth * s, h = img.naturalHeight * s, x0 = ir.left + (ir.width - w) / 2, y0 = ir.top + (ir.height - h) / 2;
  const x = e.clientX - x0, y = e.clientY - y0;
  if (!w || x < 0 || y < 0 || x > w || y > h) return box.classList.remove("looking");
  const L = loupe.clientWidth;
  loupe.style.setProperty("--lz-img", `url("${box.dataset.src}")`);
  loupe.style.setProperty("--lz-size", `${w * ZOOM}px ${h * ZOOM}px`);
  loupe.style.setProperty("--lz-pos", `${L / 2 - x * ZOOM}px ${L / 2 - y * ZOOM}px`);
  mark.style.left = `${e.clientX - b.left}px`; mark.style.top = `${e.clientY - b.top}px`;
  mark.style.width = mark.style.height = `${L / ZOOM}px`;
  box.classList.add("looking");
}
if (loupe && matchMedia("(min-width: 901px)").matches) {
  box.addEventListener("pointermove", look);
  box.addEventListener("pointerdown", look);
  box.addEventListener("pointerleave", () => box.classList.remove("looking"));
}

// "Today's picks" rail: the arrows scroll it by most of a screen and grey out at the ends
for (const btn of document.querySelectorAll("[data-rail]")) {
  const rail = document.getElementById(btn.getAttribute("aria-controls"));
  btn.addEventListener("click", () => rail.scrollBy({ left: +btn.dataset.rail * rail.clientWidth * .9, behavior: reduced ? "auto" : "smooth" }));
  const ends = () => document.querySelectorAll(`[aria-controls="${rail.id}"]`).forEach(b => (b.disabled = +b.dataset.rail < 0 ? rail.scrollLeft < 8 : rail.scrollLeft + rail.clientWidth > rail.scrollWidth - 8));
  rail.addEventListener("scroll", ends, { passive: true }); ends();
}

// phones: a placeholder that fits beside the Search button
const heroQ = document.getElementById("heroQ");
if (heroQ && matchMedia("(max-width: 520px)").matches) heroQ.placeholder = "Search patents";
