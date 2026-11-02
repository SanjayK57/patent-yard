"""Home page."""

import datetime as dt
import random
from urllib.parse import quote

from register import TODAY

from ..base import E, OFFICES, SITE, WORLD, WORLD_AT, badge, big_number, full_date, icon, purl
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
        hero = picks[0]["entry"]
        seen = set()  # one card per title: the same invention is sometimes patented twice
        picks = [r for r in picks if not (r["entry"]["t"].lower() in seen or seen.add(r["entry"]["t"].lower()))]
        m = self.meta
        total = m["count"] + m.get("archive", 0)
        by_field = m.get("archiveByField", {})
        chips = "".join(f'<a class="fchip" href="/fields/{k}/"><svg class="fglyph" aria-hidden="true"><use href="#f-{k}"/></svg><span>{E(n)}</span><small class="num">{len(self.by_field[k]) + by_field.get(k, 0):,}</small></a>'
                        for k, n in self.fields.items())
        tries = "".join(f'<a class="chip" href="/browse/?q={quote(t)}">{E(t)}</a>' for t in ("drone", "solar charger", "robot arm", "kitchen", "bicycle", "hearing aid"))
        span = {n: b - a for n, a, b in m.get("archiveSpans", [])}
        sources = [(m["count"] + span.get("US", 0), "United States", "USPTO", "US"), (span.get("Europe", 0), "Europe", "European Patent Office", "Europe"),
                   (span.get("Canada", 0), "Canada", "CIPO", "Canada"), (span.get("Australia", 0), "Australia", "IP Australia", "Australia")]
        week = sum(1 for r in self.rows if (r["added"] or "") >= (TODAY - dt.timedelta(days=7)).isoformat())
        statband = (f'<a href="/all/"><em>{OFFICES} offices</em><b class="num" data-count="{WORLD["n"]}">{big_number(WORLD["n"])}</b><span>patent records worldwide, granted and published applications</span></a>' if WORLD else "") + "".join(
            f'<a href="/browse/?in=archive&amp;region={quote(r)}">{f"<em class=up>+{week:,} added this week</em>" if place == "United States" and week else ""}<b class="num" data-count="{c}">{big_number(c)}</b><span>{E(place)}: {"expired, lapsed or abandoned" if place == "United States" else "past their term"}</span></a>'
            for c, place, office, r in sources if c)
        he = hero
        ended = full_date(he["x"]) if he["st"] == "lapsed" else full_date(he.get("te")) if he["st"] == "expired" else ""
        body = f"""
<div class="homelead">
<section class="ahero">
  <h1 class="rise" style="--d:0">Build on inventions whose patents have ended.</h1>
  <p class="lede rise" style="--d:1">Search expired, lapsed and abandoned patents from the US, Europe, Canada and Australia, with their original drawings and claims. Check what else exists among {big_number(WORLD['n']) if WORLD else 'millions of'} records worldwide, then develop your own version with Claude.</p>
  <form class="bigsearch rise" style="--d:2" action="/browse/" role="search">{icon("search")}<label class="sr" for="heroQ">Search patents</label><input id="heroQ" name="q" type="search" autocomplete="off" placeholder="Search ideas, titles or numbers"><span class="kbd" aria-hidden="true"><kbd>⌘</kbd><kbd>K</kbd></span><button class="btn primary" type="submit">Search</button></form>
  <div class="tryrow rise" style="--d:3"><span>Try</span>{tries}<button class="chip" type="button" data-surprise>{icon("shuffle")}Surprise me</button>{'<a class="allpat" href="/all/">Or search all patents worldwide ›</a>' if WORLD else ""}</div>
</section>
<section class="specimen rise" style="--d:2" aria-labelledby="plateTitle">
  <figure class="plotter">
    <div class="plotbox" id="plotbox" data-src="{self.img(he["id"])}"><span class="figbar" aria-hidden="true"><b>FIG. 1 · {E(he["n"])}</b></span><img src="{self.img(he["id"])}" alt="Drawing from {E(he["n"])}"><canvas id="plot" aria-hidden="true"></canvas><canvas id="pen" aria-hidden="true"></canvas>
      <div class="lmark" aria-hidden="true"></div><div class="loupe" aria-hidden="true"></div></div>
  </figure>
  <div class="platefacts">
    <div class="badges">{badge(he["st"])}<span class="badge plain">{E(self.fields[he["ind"]])}</span></div>
    <h2 id="plateTitle"><a href="{purl(he["id"])}">{E(he["t"])}</a></h2>
    <p><span class="num">{E(he["n"])}</span>{f" · {'lapsed' if he['st'] == 'lapsed' else 'term ended'} {ended}" if ended else ""}</p>
    <div class="rowbtns"><a class="btn secondary sm" href="{purl(he["id"])}">Open the patent</a><a class="btn link sm" href="{purl(he["id"])}#kit">Reinvent with Claude ›</a></div>
  </div>
</section>
</div>
<nav class="statband{" five" if WORLD else ""}" aria-label="Patents by collection and office">{statband}</nav>
<p class="statnote">{f"Worldwide: Google Patents Public Data as loaded in {WORLD_AT:%B %Y}, granted patents and published applications together. " if WORLD else ""}US, Europe, Canada and Australia: patents and applications no longer in force, from USPTO, EPO, CIPO and IP Australia records, counted {full_date(TODAY.isoformat())}. <a href="/about/#numbers">What each number means</a></p>

<section class="section" id="recentSec" hidden><div class="sechead"><div><h2>Recently viewed</h2><p>Pick up where you left off. Kept in this browser only.</p></div><button class="btn quiet" type="button" id="recentClear">Clear</button></div><div class="rail" id="recentGrid"></div></section>
<section class="section reveal" id="today">
  <div class="sechead"><div><h2>Worth a look today</h2><p>Picked each day from US patents that have expired or lapsed. A patent ending frees its own claims, not every right in a product, so check before you build.</p></div><a class="btn secondary sm" href="/browse/">Browse all</a></div>
  <div class="bento">{self.card(picks[1], 1, feat=True)}{"".join(self.card(r, i) for i, r in enumerate(picks[2:6], 2))}</div>
  <ol class="pickrows" aria-label="More picks">{"".join(self.pickrow(r) for r in picks[6:12])}</ol>
</section>
<section class="section reveal">
  <div class="sechead"><div><h2>Explore by field</h2><p>Every patent is filed under the field of its main classification.</p></div><a class="btn quiet" href="/fields/">All fields</a></div>
  <div class="fchips">{chips}</div>
</section>
<section class="section reveal">
  <div class="sechead"><div><h2>How it works</h2></div><a class="btn quiet" href="/how-it-works/">The details</a></div>
  <div class="steps3">
    <div><span class="n">01</span><h3>Find</h3><p>Search patents that have expired, lapsed or been abandoned. Each one links to the patent office record it came from.</p></div>
    <div><span class="n">02</span><h3>Reinvent with Claude</h3><p>The studio writes a prompt and a PDF brief for your own Claude account: modern directions, a first prior-art search and a rough provisional draft to review with a professional.</p></div>
    <div><span class="n">03</span><h3>Reserve and build</h3><p>Reserve a patent for 30 days so other builders know you're on it, then build it, and file on your improvement if it's new. Reserving doesn't stop anyone else from using it.</p></div>
  </div>
</section>
<section class="section reveal">
  <div class="ctaband"><div><h2>Have your own idea?</h2><p>The invention studio turns it into a prompt and brief for Claude, with a first prior-art search and a rough provisional draft. Free.</p></div>
    <figure class="promptcard"><span class="figbar" aria-hidden="true"><b>Invention studio · prompt</b></span><blockquote>I'm an independent inventor. I want to build a new, patentable product based on my own idea. Act as my product strategist and patent coach and work through these four steps with me, one at a time. After each step, stop and wait for my reply.</blockquote><figcaption>The opening of the prompt the studio writes for your Claude</figcaption></figure><div class="rowbtns"><a class="btn primary lg" href="/studio/">Open the studio</a><a class="btn link lg" href="/how-it-works/">How it works ›</a></div></div>
</section>"""
        ld = [{"@context": "https://schema.org", "@type": "WebSite", "name": "Patent Yard", "url": SITE + "/",
               "potentialAction": {"@type": "SearchAction", "target": SITE + "/browse/?q={search_term_string}", "query-input": "required name=search_term_string"}},
              {"@context": "https://schema.org", "@type": "Organization", "name": "Patent Yard", "url": SITE + "/", "logo": SITE + "/favicon.svg"}]
        self.page("/", "Patent Yard", f"Search {big_number(total)} expired, lapsed and abandoned patents from the US, Europe, Canada and Australia, each traced to its patent office record, with tools to develop new inventions from them with Claude.",
                  body, og_image=self.img(hero["id"]), jsonld=ld, scripts=("home",))

    def ticker(self):
        newest = sorted(self.rows, key=lambda r: (r["added"], r["freed"], r["entry"]["id"]), reverse=True)[:400]
        newest = sorted((r for r in newest if coolness(r) > 0), key=coolness, reverse=True)[:24]  # the most interesting of the newest
        items = "".join(f'<a href="{purl(r["entry"]["id"])}"><span class="badge {r["entry"]["st"]}"></span>{E(r["entry"]["t"][:70])}<small>{E(self.fields.get(r["entry"]["ind"], ""))}</small></a>' for r in newest)
        return (f'<div class="ticker" aria-label="Newly added patents"><span class="tlabel"><span class="pulse" aria-hidden="true"></span>Just added</span>'
                f'<div class="tmask"><div class="ttrack">{items}<span aria-hidden="true" class="tdup">{items}</span></div></div></div>')
