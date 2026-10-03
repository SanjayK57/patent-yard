// The timeline chart of a patent's dates, as on recently freed patents (pipeline/website.py timeline_svg), for the
// pages rendered here: archive patents (_archive.js) and All patents (_world.js). events: [date, label, "bad"?].
const E = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
const SHORT = { January: "Jan", February: "Feb", August: "Aug", September: "Sep", October: "Oct", November: "Nov", December: "Dec" };
const full = s => { const [y, m, d] = s.split("-").map(Number); return `${MONTHS[m - 1]} ${d}, ${y}`; };
const day = s => Date.UTC(+s.slice(0, 4), +s.slice(5, 7) - 1, +s.slice(8, 10)) / 864e5;
const col = k => (k === "bad" ? "var(--lapsed)" : "var(--accent)");

export function timelineSvg(events) {
  const W = 760, pad = 40, y0 = 70, t0 = day(events[0][0]), t1 = day(events[events.length - 1][0]), span = Math.max(t1 - t0, 1);
  const X = s => pad + (day(s) - t0) / span * (W - pad * 2);
  const y1 = +events[0][0].slice(0, 4), y2 = +events[events.length - 1][0].slice(0, 4), years = [];
  for (let y = y1 + 1; y <= y2; y++) years.push(y);
  const every = Math.max(1, Math.ceil(years.length / 10));
  const out = [`<svg class="chart" viewBox="0 0 ${W} ${y0 + 150}" role="img" aria-label="${E("Timeline: " + events.map(([s, t]) => `${t} ${full(s)}`).join("; "))}">`,
    `<line class="axis" x1="${pad}" y1="${y0}" x2="${W - pad}" y2="${y0}" stroke-width="2"/>`];
  years.forEach((y, i) => {
    if (i % every) return;
    const x = X(`${y}-01-01`).toFixed(1);
    out.push(`<line class="tick" x1="${x}" y1="${y0 - 6}" x2="${x}" y2="${y0 + 6}"/><text class="muted" x="${x}" y="${y0 - 12}" text-anchor="middle">${y}</text>`);
  });
  let last = -1e9, lane = 0;
  for (const [s, t, k] of events) {
    const x = X(s);
    lane = x - last < 120 ? (lane + 1) % 3 : 0;
    last = x;
    const ly = y0 + 28 + lane * 38, a = x < 110 ? "start" : x > W - 110 ? "end" : "middle", xs = x.toFixed(1);
    out.push(`<line x1="${xs}" y1="${y0}" x2="${xs}" y2="${ly - 12}" stroke="${col(k)}" stroke-width="1"/>`
      + `<circle cx="${xs}" cy="${y0}" r="6" fill="${col(k)}" stroke="${col(k)}" stroke-width="2"/>`
      + `<text class="lbl" x="${xs}" y="${ly}" text-anchor="${a}">${E(t)}</text>`
      + `<text class="muted" x="${xs}" y="${ly + 16}" text-anchor="${a}">${E(full(s).replace(/^(\w+)/, m => SHORT[m] || m))}</text>`);
  }
  out.push("</svg>");
  return out.join("");
}

// the Timeline section, or "" when there are fewer than two dated events
export function timelineSection(events, source) {
  const ev = events.filter(e => e && /^\d{4}-\d\d-\d\d$/.test(e[0] || "")).sort((a, b) => (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0))
    .filter((e, i, all) => !i || e[0] !== all[i - 1][0] || e[1] !== all[i - 1][1]);
  return ev.length < 2 ? "" : `<section class="psec" id="history"><h2>Timeline</h2><div class="panel"><div class="block"><h3>Timeline <span class="src">From ${E(source)} dates</span></h3><div class="chartbox">${timelineSvg(ev)}</div></div></div></section>`;
}
