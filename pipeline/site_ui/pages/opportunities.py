"""Opportunities."""

from urllib.parse import quote

from ..base import E, icon, purl, short_date
from ..ranking import ANALYSIS, potential, signals


class Opportunities:
    def opportunities(self):
        scored = sorted(((p, r) for r in self.rows if (p := potential(r)) is not None),
                        key=lambda t: (-t[0], -(t[1]["entry"].get("cl") or 0), t[1]["entry"]["id"]))  # ties: more claims, then number
        by_id = {r["entry"]["id"]: r for _, r in scored}
        picks = [(by_id[k], v) for k, v in ANALYSIS.items() if k in by_id]
        top = [r for _, r in scored if r["entry"]["id"] not in ANALYSIS][:96]

        def why(r):  # every factor and its points, so the order can be checked by hand
            sig = signals(r["entry"], bool(r["fig"]))
            rows_ = "".join(f"<li><span>{E(t)}</span><b class=\"num\">+{v:.1f}</b></li>" for t, v in sig)
            return (f'<details class="why"><summary>Why it ranks here <span class="num">{sum(v for _, v in sig):.1f} points</span></summary>'
                    f'<ul>{rows_}</ul></details>')
        pick_html = "".join(f"""<article class="oppick reveal" data-of="{r["entry"]["ind"]}">
  <a class="ofig" href="{purl(r["entry"]["id"])}">{f'<img src="{self.img(r["entry"]["id"])}" alt="Drawing from {E(r["entry"]["n"])}" loading="lazy">' if r["fig"] else ""}<span class="rank">{i}</span></a>
  <div class="otext"><span class="fieldname">{E(self.fields.get(r["entry"]["ind"], r["entry"]["ind"]))} · <span class="num-id">{E(r["entry"]["n"])}</span> · lapsed {E(short_date(r["entry"]["x"]))}</span>
    <h3><a href="{purl(r["entry"]["id"])}">{E(r["entry"]["t"])}</a></h3>
    <dl><div><dt>What lapsed</dt><dd>{E(a["open"])}</dd></div><div><dt>Who might be interested</dt><dd>{E(a["buyers"])}</dd></div>
    <div><dt>Why it could matter now</dt><dd>{E(a["now"])}</dd></div><div><dt>Check before building</dt><dd>{E(a["watch"])}</dd></div></dl>
    {why(r)}
    <div class="rowbtns"><a class="btn primary sm" href="{purl(r["entry"]["id"])}">Open patent</a><a class="btn secondary sm" href="/studio/?patent={quote(r["entry"]["id"])}">{icon("spark")}Reinvent with Claude</a></div></div>
</article>""" for i, (r, a) in enumerate(picks, 1))
        top_html = "".join(f'<div class="opp" data-of="{r["entry"]["ind"]}"><span class="rank">{i}</span>{self.card(r, i)}{why(r)}</div>'
                           for i, r in enumerate(top, len(picks) + 1))
        fields = sorted({r["entry"]["ind"] for r, _ in picks} | {r["entry"]["ind"] for r in top}, key=lambda k: list(self.fields).index(k) if k in self.fields else 99)
        filt = '<button class="chip" type="button" data-of="" aria-pressed="true">All</button>' + "".join(
            f'<button class="chip" type="button" data-of="{k}" aria-pressed="false">{E(self.fields.get(k, k))}</button>' for k in fields)
        body = f"""<div class="page">
<div class="sechead"><div><h1>Opportunities</h1>
<p class="lede">US patents that lapsed for an unpaid maintenance fee in the past year, ordered by a few facts from their records that suggest someone once invested in them. It's a starting point for research, not a valuation: nothing here measures the legal scope of the claims or predicts sales.</p></div></div>
<ul class="omethod">
<li><b>Fees paid for years</b><span>The owner paid maintenance fees for 7.5 or 11.5 years before letting the patent lapse. They thought it worth paying for; that says nothing about sales.</span></li>
<li><b>A company assignee</b><span>A company was the assignee when it was granted. Companies usually file for products they mean to make, but not always, and today's owner may differ.</span></li>
<li><b>Field weighting</b><span>Our judgment of where product development is busiest now (medical, energy, AI, robotics, vehicles weigh most). It is not market data.</span></li>
<li><b>Inventors and drawings</b><span>Several named inventors, and drawings on file to work from.</span></li>
</ul>
<p class="muted fine-print">Each patent's factors and points are under "Why it ranks here". Claim length is not used: a short claim isn't necessarily a broad one.</p>
<div class="frow ofilter" role="group" aria-label="Filter by field"><span class="lab">Field</span>{filt}</div>
<section class="section"><div class="sechead"><div><h2>Researched notes on the top {len(picks)}</h2><p>Drafted with Claude (an AI model) from each patent's abstract and claims while the register was prepared, not reviewed by a patent professional. Who might be interested and why now are leads to check, not findings. No market figures are given because we can't source them.</p></div></div>
<div class="opicks">{pick_html}</div></section>
<section class="section"><div class="sechead"><div><h2>The next {len(top)}</h2><p>Same factors, without written notes. Open any one for its claims, drawings and the Claude kit.</p></div></div>
<div class="grid ogrid">{top_html}</div></section>
<p class="muted fine-print">A lapsed US patent can be reinstated if the owner later shows the missed payment was unintentional, and its own claims are only one of the rights a product can touch: newer patents, design patents, trademarks, regulations and patents in other countries can still apply. See the <a href="/legal/disclaimer/">disclaimer</a>.</p>
</div>"""
        self.page("/opportunities/", "Opportunities", f"{len(picks) + len(top)} recently lapsed US patents in an explainable research order, with notes on the top {len(picks)} drafted with Claude.",
                  body, section="/opportunities/", scripts=("opps",))
