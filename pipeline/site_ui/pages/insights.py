"""Insights (charts)."""

import collections

import patents as P
from register import TODAY

from ..base import COUNTRY, E, WSTATS, big_number, d, owner_key, owner_name, short_date


def line_chart(vals, labels, every, top, aria, note=""):
    """The animated line chart on Insights: vals left to right, every `every`th label under the axis, a zero line and a
    dashed line at the peak (labeled `top`), and `note` (source, period, unit) under the chart."""
    W, H, pad = 760, 220, 34
    hi = max(vals, default=1) or 1
    pts = [(pad + i / max(1, len(vals) - 1) * (W - 2 * pad), H - pad - v / hi * (H - 2 * pad)) for i, v in enumerate(vals)]
    line = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) if pts else ""
    area = f"{line} L{pts[-1][0]:.1f},{H - pad} L{pts[0][0]:.1f},{H - pad} Z" if pts else ""
    ticks = "".join(f'<text class="muted" x="{x:.1f}" y="{H - 10}" text-anchor="middle">{E(t)}</text>' for (x, _), t in list(zip(pts, labels))[::every])
    return (f'<svg class="chart linechart" viewBox="0 0 {W} {H}" role="img" aria-label="{E(aria)}">'
            f'<line class="axis" x1="{pad}" y1="{H - pad}" x2="{W - pad}" y2="{H - pad}"/><line class="peak" x1="{pad}" y1="{pad}" x2="{W - pad}" y2="{pad}"/>'
            f'<text class="muted" x="{pad}" y="{pad - 8}">Peak: {E(top)}</text><text class="muted" x="{pad - 6}" y="{H - pad + 4}" text-anchor="end">0</text>'
            f'<path class="area" d="{area}"/><path class="line" d="{line}" pathLength="1"/>{ticks}</svg>'
            + (f'<p class="chartsrc">{note}</p>' if note else ""))


class Insights:
    def insights(self, issues, recs=()):
        """The register in numbers, drawn from the same records as every page. Charts animate in as they scroll into view."""
        rows, m = self.rows, self.meta
        n, keys_ = len(rows), list(P.FIELDS)
        arch = collections.Counter(keys_[r[3]] for r in recs)
        fields = sorted(((len(self.by_field.get(k, [])) + arch.get(k, 0), k, name) for k, (name, _) in P.FIELDS.items()
                         if self.by_field.get(k) or arch.get(k)), reverse=True)
        top = fields[0][0] or 1
        field_bars = "".join(
            f'<a class="hrow" href="/fields/{k}/"><span class="hl">{E(name)}</span><span class="hbar"><i style="--w:{c / top * 100:.1f}%"></i></span><b class="num">{c:,}</b></a>'
            if k in self.fields else
            f'<div class="hrow"><span class="hl">{E(name)}</span><span class="hbar"><i style="--w:{c / top * 100:.1f}%"></i></span><b class="num">{c:,}</b></div>'
            for c, k, name in fields)
        # weekly Gazette lapses over the past year
        weeks = sorted((o["date"], len(o["lapsed"]), len(o["reinstated"])) for o in issues if (TODAY - d(o["date"])).days <= 372)
        hi = max((w[1] for w in weeks), default=1)
        chart = line_chart([w[1] for w in weeks], [short_date(w[0]) for w in weeks], max(1, len(weeks) // 6), f"{hi:,} a week",
                           f"Patents lapsed each week, past year: {min((w[1] for w in weeks), default=0):,} to {hi:,} a week",
                           f"Patents per weekly issue of the USPTO Official Gazette listed as expired for an unpaid maintenance fee, {short_date(weeks[0][0])} to {short_date(weeks[-1][0])}. Source: USPTO." if weeks else "")
        # when patents lapse: the fee missed at 3.5, 7.5 or 11.5 years
        lap = [r["entry"] for r in rows if r["entry"]["st"] == "lapsed" and r["entry"]["p"] and r["entry"]["x"]]
        at = {4: 0, 8: 0, 12: 0}
        for e in lap:
            y = (d(e["x"]) - d(e["p"])).days / 365.25
            at[4 if y < 6 else 8 if y < 10 else 12] += 1
        tl = sum(at.values()) or 1
        lapse_bars = "".join(f'<div class="vcol"><span class="vbar"><i style="--h:{v / tl * 100:.1f}%"></i></span><b class="num">{v / tl * 100:.0f}%</b><small>Year {y}</small></div>' for y, v in at.items())
        solo = sum(1 for r in rows if r["entry"]["ia"]) + sum(1 for r in recs if not r[2])
        # one company, however USPTO spelled it ("INTERNATIONAL BUSINESS MACHINES CORPORATION", "...Corporation")
        names, spell = collections.Counter(), {}
        for o in [r["entry"]["a"] for r in rows if not r["entry"]["ia"]] + [r[2] for r in recs]:
            if o:
                k = owner_key(o)
                names[k] += 1
                spell.setdefault(k, collections.Counter())[o] += 1
        def shown(k):  # the spelling used most, preferring one that isn't all capitals
            best = spell[k].most_common()
            return next((o for o, _ in best if not o.isupper()), best[0][0].title())
        own = "".join(f'<li><span>{E(shown(k))}</span><b class="num">{c:,}</b></li>' for k, c in names.most_common(10))
        rein = m["reinstatedYear"]  # the same figure as About: unique numbers in the Gazette issues of the past 365 days
        # the archive, by the decade its patents were granted
        dec = collections.Counter(r[4] // 10 * 10 for r in recs)
        kinds = collections.Counter(r[5] for r in recs)
        dtop = max(dec.values(), default=1)
        dec_bars = "".join(f'<div class="hrow"><span class="hl">{y}s</span><span class="hbar"><i style="--w:{c / dtop * 100:.1f}%"></i></span><b class="num">{c:,}</b></div>'
                           for y, c in sorted(dec.items(), reverse=True))
        archive_sec = (f'<section class="panel reveal span2"><h2>The archive, by decade</h2><p class="muted">{len(recs):,} patents and applications that can no longer be in force: '
                       f'{kinds.get("", 0):,} US utility patents past their full term, {kinds.get("S", 0):,} expired US designs, {kinds.get("A", 0):,} likely abandoned US applications, and {kinds.get("E", 0):,} European, {kinds.get("CA", 0):,} Canadian and {kinds.get("AU", 0):,} Australian patents and applications past their term, by the decade they were granted or published.</p>'
                       f'<div class="hbars">{dec_bars}</div></section>') if recs else ""
        body = f"""<div class="page">
<div class="sechead"><div><h1>Insights</h1><p>{f"Patent Yard in numbers: all {big_number(WSTATS['n'])} patent records worldwide (granted patents and published applications) by office, year, field and owner, then the free-to-use register: what lapses, when, and who used to own it." if WSTATS else "The register in numbers: what lapses, when, and who used to own it. Drawn from the same USPTO records as every patent page, updated with each refresh."}</p></div></div>
{self.world_insights()}
{'<section class="section"><div class="sechead"><div><h2>Free to use</h2><p>The register of patents whose protection has ended, drawn from the same office records as every patent page and updated with each refresh.</p></div></div>' if WSTATS else ""}
<div class="statband reveal">
  <div><b class="num" data-count="{n + len(recs)}">{n + len(recs):,}</b><span>patents listed: {n + kinds.get("", 0) + kinds.get("S", 0) + kinds.get("A", 0):,} US, {kinds.get("E", 0):,} European, {kinds.get("CA", 0):,} Canadian and {kinds.get("AU", 0):,} Australian</span></div>
  <div><b class="num" data-count="{m["lapsedYear"]}">{m["lapsedYear"]:,}</b><span>US patents the Official Gazette listed as expired for an unpaid fee in the past 365 days</span></div>
  <div><b class="num" data-count="{rein}">{rein:,}</b><span>listed as reinstated after a late payment in the same issues, and left out of the register</span></div>
  <div><b class="num" data-count="{round(solo / max(1, n + len(recs)) * 100)}">{solo / max(1, n + len(recs)) * 100:.0f}</b><span>percent granted with no assignee recorded, usually to individual inventors</span></div>
</div>
<div class="ins">
  <section class="panel reveal span2"><h2>Lapses every week</h2><p class="muted">Patents the Official Gazette listed as expired for an unpaid maintenance fee, issue by issue.</p><div class="chartbox">{chart}</div></section>
  <section class="panel reveal"><h2>By field</h2><p class="muted">All {n + len(recs):,} listed patents by the field of their main classification: recently freed and archive together.</p><div class="hbars">{field_bars}</div></section>
  <section class="panel reveal"><h2>When owners stop paying</h2><p class="muted">Maintenance fees fall due 3.5, 7.5 and 11.5 years after grant. Of the {len(lap):,} patents that lapsed in the past year, the share by the fee that went unpaid.</p><div class="vbars">{lapse_bars}</div>
    <h2 style="margin-top:26px">Most frequent former owners</h2><p class="muted">Companies with the most patents in the register, every spelling of a name counted together.</p><ol class="owners">{own}</ol></section>
  {archive_sec}
</div>
{"</section>" if WSTATS else ""}
</div>"""
        self.page("/insights/", "Insights", (f"{big_number(WSTATS['n'])} patent records worldwide by office, year, field and owner, " if WSTATS else "Patent Yard in numbers: ")
                  + "weekly USPTO lapses, fields, when owners stop paying and the companies behind them.", body, section="/insights/")

    def world_insights(self):
        """All patents in numbers (web/world/stats.json, from world.py stats), or "" before it exists."""
        if not WSTATS:
            return ""
        w = WSTATS
        short = lambda v: f"{v / 1e6:.1f}M" if v >= 1e6 else f"{v / 1e3:.0f}k" if v >= 1e3 else str(v)
        offices = list(w["countries"].items())[:12]
        top = offices[0][1][0]
        office_bars = "".join(
            f'<div class="hrow" title="{c:,} records, {f:,} past their term"><span class="hl">{E(COUNTRY.get(cc, cc))}</span>'
            f'<span class="hbar two"><i style="--w:{c / top * 100:.1f}%"></i><i style="--w:{f / top * 100:.1f}%"></i></span><b class="num">{short(c)}</b></div>'
            for cc, (c, f) in offices)
        owners = "".join(f'<li><span>{E(owner_name(o))}</span><b class="num">{c:,}</b></li>' for o, c in w["owners"][:10])
        fields = {k: c for k, c in w["fields"].items() if k != "other"}  # records with no classification, mostly
        ftop = max(fields.values())
        field_bars = "".join(f'<div class="hrow"><span class="hl">{E(P.FIELDS[k][0])}</span><span class="hbar"><i style="--w:{c / ftop * 100:.1f}%"></i></span><b class="num">{short(c)}</b></div>'
                             for k, c in fields.items())
        # from 1900 to the last full year, so the current year's partial count doesn't read as a drop
        years = [(y, c) for y, c in w["years"].items() if "1900" <= y < str(TODAY.year)]
        hi = max(c for _, c in years)
        peak = max(years, key=lambda t: t[1])[0]
        chart = line_chart([c for _, c in years], [y for y, _ in years], 20, f"{big_number(hi)} a year",
                           f"Patents and applications published each year, 1900 to {years[-1][0]}, peaking at {hi:,} in {peak}",
                           f"Patent records (granted patents and published applications) by year of publication, all offices, 1900 to {years[-1][0]}. Source: Google Patents Public Data, CC BY 4.0.")
        return f"""<section class="section"><div class="sechead"><div><h2>All patents worldwide</h2><p>Every patent and published application in <a href="/all/">All patents</a>, from Google Patents Public Data.</p></div></div>
<div class="statband reveal">
  <div><b class="num" data-count="{w["n"]}">{w["n"]:,}</b><span>patents and applications</span></div>
  <div><b class="num" data-count="{len(w["countries"])}">{len(w["countries"])}</b><span>patent offices</span></div>
  <div><b class="num" data-count="{w["granted"]}">{w["granted"]:,}</b><span>granted patents or registered utility models; the rest are applications</span></div>
  <div><b class="num" data-count="{w["free"]}">{w["free"]:,}</b><span>filed more than 20 years ago (26 for medicines), past the usual maximum term</span></div>
</div>
<div class="ins">
  <section class="panel reveal span2"><h2>Published each year</h2><p class="muted">Patents and applications by the year they were published, across every office, from 1900 to {years[-1][0]}.</p><div class="chartbox">{chart}</div></section>
  <section class="panel reveal"><h2>By office</h2><p class="muted">The 12 offices with the most records. The bright part of each bar is past its term.</p><div class="hbars">{office_bars}</div>
    <h2 style="margin-top:26px">Biggest owners</h2><p class="muted">The owners with the most records worldwide, every spelling of a name counted together.</p><ol class="owners">{owners}</ol></section>
  <section class="panel reveal"><h2>By field</h2><p class="muted">Records by the field of their main classification; {big_number(w["fields"].get("other", 0))} more have no classification or fall outside these fields.</p><div class="hbars">{field_bars}</div></section>
</div>
</section>"""
