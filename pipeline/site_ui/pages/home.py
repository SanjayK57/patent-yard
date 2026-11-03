"""Home page."""

import datetime as dt
import random
from urllib.parse import quote

from register import TODAY

from ..base import E, OFFICES, SITE, STATUS, WORLD, WORLD_AT, badge, big_number, full_date, icon, purl
from .patent import png_size, why_free
from ..ranking import coolness


class Home:
    def home(self):
        """Search first, then a few hand-picked patents in a scrolling rail, the fields, and how it works."""
        rnd = random.Random(TODAY.isoformat())
        taken = self.meta.get("reserved", set())
        pools = []
        for k in self.fields:  # picks: patents with a written note and a drawing, the coolest first, varied daily
            pool = [r for r in self.doc_by_field[k] if r["entry"]["fig"] and not r["entry"]["auto"] and r["entry"]["id"] not in taken]
            pool = [(coolness(r) + rnd.random() * 1.5, r) for r in pool]
            pool = [r for c, r in sorted(pool, key=lambda t: -t[0]) if c > 1.5]
            if pool:
                pools.append(pool)
        pools.sort(key=lambda pl: -coolness(pl[0]))
        picks, k = [], 0
        while len(picks) < 12 and any(pools):
            pl = pools[k % len(pools)]
            if pl:
                picks.append(pl.pop(0))
            k += 1
        # the drawing plotted live in the hero: the coolest pick with a detailed drawing
        picks.sort(key=lambda r: -(coolness(r) + (1 if r["fig"].stat().st_size > 12000 else 0)))
        hero, hero_fig = picks[0]["entry"], picks[0]["fig"]
        seen = set()  # one card per title: the same invention is sometimes patented twice
        picks = [r for r in picks if not (r["entry"]["t"].lower() in seen or seen.add(r["entry"]["t"].lower()))]
        m = self.meta
        total = m["count"] + m.get("archive", 0)
        by_field = m.get("archiveByField", {})
        chips = "".join(f'<a class="fchip" href="/fields/{k}/"><span>{E(n)}</span><i aria-hidden="true"></i><small class="num">{len(self.by_field[k]) + by_field.get(k, 0):,}</small></a>'
                        for k, n in self.fields.items())
        tries = "".join(f'<a class="chip" href="/browse/?q={quote(t)}">{E(t)}</a>' for t in ("drone", "solar charger", "robot arm", "kitchen", "bicycle", "hearing aid"))
        span = {n: b - a for n, a, b in m.get("archiveSpans", [])}
        sources = [(m["count"] + span.get("US", 0), "United States", "USPTO", "US"), (span.get("Europe", 0), "Europe", "European Patent Office", "Europe"),
                   (span.get("Canada", 0), "Canada", "CIPO", "Canada"), (span.get("Australia", 0), "Australia", "IP Australia", "Australia")]
        week = sum(1 for r in self.rows if (r["added"] or "") >= (TODAY - dt.timedelta(days=7)).isoformat())
        he = hero
        w, h = png_size(hero_fig)
        ended = full_date(he["x"]) if he["st"] == "lapsed" else full_date(he.get("te")) if he["st"] == "expired" else ""
        ended_label = "Lapsed" if he["st"] == "lapsed" else "Term ended" if he["st"] == "expired" else "Published"
        checks, _ = why_free(he)
        free_total = m["count"] + m.get("archive", 0)
        scale = [(free_total, "patents whose protection has ended: lapsed, past their term or abandoned, in the US, Europe, Canada and Australia.", "USPTO, EPO, CIPO and IP Australia records")]
        if WORLD:
            scale.append((WORLD["n"], "patent records worldwide, in force or not, for checking what already exists. Not all of them are free to use.", f"Google Patents Public Data, {OFFICES} offices"))
        if week:
            scale.append((week, "US patents added this week. Lapsed ones are rechecked for reinstatement every day.", "USPTO Official Gazette"))
        scale_html = "".join(f'<div><b><span class="n num" data-count="{c}">{big_number(c).replace(" million", "")}</span>{"<small>million</small>" if c >= 1_000_000 else ""}</b><p>{E(t)}</p><small>{E(src)}</small></div>' for c, t, src in scale)
        offices = "".join(f'<li><a href="/browse/?in=archive&amp;region={quote(r)}"><b>{E(place)}</b><span class="n num" data-count="{c}">{c:,}</span><small>{E(office)}</small>{icon("right")}</a></li>'
                          for c, place, office, r in sources if c)
        demo_rows = "".join(f'<li><span class="pthumb">{f"""<img src="{self.img(r["entry"]["id"])}" alt="" loading="lazy" decoding="async">""" if r["entry"]["fig"] else ""}</span><span><b>{E(r["entry"]["t"])}</b><small class="st-{r["entry"]["st"]}">{STATUS[r["entry"]["st"]]}</small></span></li>' for r in picks[6:8])
        tasks = "".join(f"<li>{t}</li>" for t in ("Full reinvention workshop", "Modern directions", "Prior-art check", "Provisional draft", "Prototype plan"))
        body = f"""
<section class="hero" aria-labelledby="heroTitle">
  <div class="hcopy">
    <h1 id="heroTitle" class="rise" style="--d:0">Old inventions.<span>New possibilities.</span></h1>
    <p class="lede rise" style="--d:1">Search patents whose protection has expired, lapsed or been abandoned, each with its original drawings and claims and the official record that shows why. Then develop your own version with Claude.</p>
    <form class="bigsearch rise" style="--d:2" action="/browse/" role="search">{icon("search")}<label class="sr" for="heroQ">Search patents</label><input id="heroQ" name="q" type="search" autocomplete="off" placeholder="Search ideas, titles or patent numbers"><span class="kbd" aria-hidden="true"><kbd>⌘</kbd><kbd>K</kbd></span><button class="btn primary" type="submit">Search</button></form>
    <div class="tryrow rise" style="--d:3"><span>Try</span>{tries}<button class="chip" type="button" data-surprise>{icon("shuffle")}Surprise me</button></div>
    {f'<a class="allpat rise" style="--d:3" href="/all/">Check all <b class="num">{big_number(WORLD["n"])}</b> patent records worldwide {icon("right")}</a>' if WORLD else ""}
    <p class="rights rise" style="--d:4">A patent ending frees its own claims, not every right in a product. Every listing shows the rule that freed it, its dates and its source.</p>
  </div>
  <figure class="stage" aria-labelledby="plateTitle">
    <div class="glass ltglass">
      <div class="plotbox" id="plotbox" data-src="{self.img(he["id"])}" style="--ar:{w}/{h}"><img src="{self.img(he["id"])}" alt="Drawing from {E(he["n"])}" width="{w}" height="{h}" fetchpriority="high"><canvas id="plot" aria-hidden="true"></canvas><canvas id="pen" aria-hidden="true"></canvas>
        <span class="ticks" aria-hidden="true"></span><span class="sheetlabel num" aria-hidden="true">{E(he["n"])} · Sheet 1{f" of {he['sh']}" if he["sh"] else ""}</span>
        <div class="lmark" aria-hidden="true"></div><div class="loupe" aria-hidden="true"></div></div>
    </div>
    <figcaption class="record vellum">
      {badge(he["st"])}
      <h2 id="plateTitle"><a href="{purl(he["id"])}">{E(he["t"])}</a></h2>
      <dl><div><dt>{ended_label}</dt><dd class="num">{E(ended or full_date(he["p"]))}</dd></div><div><dt>Field</dt><dd>{E(self.fields[he["ind"]])}</dd></div><div><dt>Record</dt><dd class="num">USPTO · {E(he["n"])}</dd></div></dl>
      <div class="rowbtns"><a class="btn primary sm" href="{purl(he["id"])}">Open the record</a><a class="btn quiet sm" href="{purl(he["id"])}#kit">{icon("spark")}Reinvent with Claude</a></div>
    </figcaption>
  </figure>
</section>

<section class="section closeup reveal" id="closeup" aria-labelledby="closeTitle"><h2 class="sr" id="closeTitle">One invention, up close</h2>{self.card(picks[1], 1, feat=True)}</section>

<section class="section yard reveal" aria-labelledby="yardTitle">
  <div class="sechead"><div><h2 id="yardTitle">What's in the yard</h2><p>Every listing shows the rule that freed it, its dates and the patent office record it came from.</p></div><a class="btn quiet" href="/about/#numbers">What each number means</a></div>
  <div class="scale">{scale_html}</div>
  <ul class="ledger" aria-label="Free-to-use patents by patent office">{offices}</ul>
  <p class="note">{f"Worldwide: Google Patents Public Data as loaded in {WORLD_AT:%B %Y}. " if WORLD else ""}US, Europe, Canada and Australia: counted {full_date(TODAY.isoformat())}.</p>
</section>

<section class="section" id="recentSec" hidden><div class="sechead"><div><h2>Recently viewed</h2><p>Pick up where you left off. Kept in this browser only.</p></div><button class="btn quiet" type="button" id="recentClear">Clear</button></div><div class="rail" id="recentGrid"></div></section>
<section class="section reveal" id="today">
  <div class="sechead"><div><h2>More from today's yard</h2><p>Picked each day from US patents that have expired or lapsed. A patent ending frees its own claims, not every right in a product, so check before you build.</p></div><a class="btn secondary sm" href="/browse/">Browse all</a></div>
  <div class="bento">{"".join(self.card(r, i) for i, r in enumerate(picks[2:6], 2))}</div>
  <ol class="pickrows" aria-label="More picks">{"".join(self.pickrow(r) for r in picks[6:12])}</ol>
</section>

<section class="section fieldsec reveal" aria-labelledby="fieldTitle">
  <div class="sechead"><div><h2 id="fieldTitle">Explore by field</h2><p>Every patent is filed under the field of its main classification.</p></div><a class="btn quiet" href="/fields/">All fields</a></div>
  <nav class="fchips findex" aria-label="Fields">{chips}</nav>
</section>

<section class="section journey reveal" aria-labelledby="howTitle">
  <div class="sechead"><div><h2 id="howTitle">From an old patent to your own invention</h2></div><a class="btn quiet" href="/how-it-works/">How it works</a></div>
  <ol class="steps">
    <li><h3>Discover</h3><p>Search by idea or by number. Every result is a patent whose protection has ended, with its drawings.</p>
      <div class="demo" aria-hidden="true"><div class="dsearch">{icon("search")}<span>{E(he["t"].split()[0].lower())}</span></div><ul class="drows">{demo_rows}</ul></div></li>
    <li><h3>Investigate</h3><p>Read the claims and drawings, and see why it's listed: the rule, the dates and the record.</p>
      <div class="demo" aria-hidden="true"><b>Why it's listed</b><ul class="dchecks">{"".join(f"<li>{E(c)}</li>" for c in checks[:2])}</ul></div></li>
    <li><h3>Develop</h3><p>Pick a task and the studio writes a prompt and a PDF brief for your own Claude account.</p>
      <div class="demo" aria-hidden="true"><ul class="dtasks">{tasks}</ul></div></li>
  </ol>
</section>

<section class="section studiointro reveal" aria-labelledby="studioTitle">
  <div class="sicopy"><h2 id="studioTitle">Have your own idea?</h2><p>The invention studio turns it, or any patent here, into a prompt and a brief for Claude, with a first prior-art search and a rough provisional draft. It runs in your own Claude account, and it's free.</p>
    <div class="rowbtns"><a class="btn primary lg" href="/studio/">Open the studio</a><a class="btn link" href="/how-it-works/">How it works</a></div></div>
  <figure class="sistage"><div class="glass"><img src="{self.img(picks[2]["entry"]["id"])}" alt="" loading="lazy" decoding="async"></div>
    <blockquote class="vellum">I'm an independent inventor. I want to build a new, patentable product based on my own idea. Act as my product strategist and patent coach and work through these four steps with me, one at a time. After each step, stop and wait for my reply.<footer>The opening of the prompt the studio writes for your Claude</footer></blockquote></figure>
</section>"""
        ld = [{"@context": "https://schema.org", "@type": "WebSite", "name": "Patent Yard", "url": SITE + "/",
               "potentialAction": {"@type": "SearchAction", "target": SITE + "/browse/?q={search_term_string}", "query-input": "required name=search_term_string"}},
              {"@context": "https://schema.org", "@type": "Organization", "name": "Patent Yard", "url": SITE + "/", "logo": SITE + "/favicon.svg"}]
        self.page("/", "Patent Yard", f"Search {big_number(total)} expired, lapsed and abandoned patents from the US, Europe, Canada and Australia, each traced to its patent office record, with tools to develop new inventions from them with Claude.",
                  body, og_image=self.img(hero["id"]), jsonld=ld, scripts=("home",))
