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
  const [r, g, b] = css.getPropertyValue("--ink").trim().replace("#", "").match(/../g).map(h => parseInt(h, 16));
  const d = o.getImageData(0, 0, dw, dh);
  for (let i = 0; i < d.data.length; i += 4) { const a = 255 - d.data[i]; d.data[i] = r; d.data[i + 1] = g; d.data[i + 2] = b; d.data[i + 3] = a; }
  o.putImageData(d, 0, 0);
  const C = Math.round(12 * dpr), cells = [];
  for (let y = 0, row = 0; y < dh; y += C, row++) {
    const xs = []; for (let x = 0; x < dw; x += C) xs.push(x);
    if (row % 2) xs.reverse();
    for (const x of xs) {
      let ink = 0; const w = Math.min(C, dw - x), h = Math.min(C, dh - y);
      for (let yy = y; yy < y + h && !ink; yy += 2) for (let xx = x; xx < x + w; xx += 2) if (d.data[(yy * dw + xx) * 4 + 3] > 90) { ink = 1; break; }
      if (ink) cells.push([x, y]);
    }
  }
  // paced by the clock, not by frames, so it finishes in about 2.5 seconds even when frames are slow
  const DUR = 2500, dot = css.getPropertyValue("--accent").trim(), t0 = performance.now();
  for (let i = 0; i < cells.length;) {
    await new Promise(requestAnimationFrame);
    const to = Math.max(i + 1, Math.ceil(cells.length * Math.min(1, (performance.now() - t0) / DUR)));
    for (const [x, y] of cells.slice(i, to)) ctx.drawImage(off, x, y, Math.min(C, dw - x), Math.min(C, dh - y), ox + x, oy + y, Math.min(C, dw - x), Math.min(C, dh - y));
    if (i === 0) still.style.visibility = "hidden";  // swap only once the pen is drawing
    i = Math.min(to, cells.length);
    const [x, y] = cells[i - 1], px = ox + x + C / 2, py = oy + y + C / 2;
    pc.clearRect(0, 0, W, H); pc.strokeStyle = `rgb(${r},${g},${b})`; pc.globalAlpha = .15; pc.lineWidth = dpr;
    pc.beginPath(); pc.moveTo(px, 0); pc.lineTo(px, H); pc.moveTo(0, py); pc.lineTo(W, py); pc.stroke();
    pc.globalAlpha = 1; pc.fillStyle = dot; pc.beginPath(); pc.arc(px, py, 3.5 * dpr, 0, 7); pc.fill();
  }
  pc.clearRect(0, 0, W, H);
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
