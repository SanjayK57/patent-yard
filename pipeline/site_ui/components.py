"""Shared UI pieces: patent cards (assets/js/cards.js draws the same markup), compact pick rows, browse filters."""

import collections

from .base import BUILD, BUILD_MEANS, E, STATUS, VIEWTOG, badge, freed_line, icon, meter, purl
from .ranking import coolness


def card_html(c):
    """The patent card. assets/js/cards.js card() draws the same markup from the same fields (documented there);
    web/dev/test_cards.mjs renders both from web/dev/fixtures/cards.json and fails if they differ."""
    b = f'<span class="badge {E(c["status"]["cls"])}">{E(c["status"]["label"])}</span>'
    symbol = f'<svg class="fglyph" aria-hidden="true"><use href="#f-{E(c.get("glyph"))}"/></svg><span class="numart">{E(c["number"])}</span>'
    n = c.get("sheets") or 0
    sheets = f'<span class="sheets">{icon("sheet")}{n} {"drawing" if n == 1 else "drawings"}</span>' if n else ""
    remote = bool(c.get("remote"))
    if c.get("img"):
        alt = c.get("alt") or "Drawing from " + c["number"]
        loading = "eager" if c.get("eager") else "lazy"
        referrer = ' referrerpolicy="no-referrer"' if remote else ""
        fig = (f'<div class="fig{" gfig" if remote else ""}"><img src="{E(c["img"])}" alt="{E(alt)}" loading="{loading}" decoding="async"{referrer}>'
               f'<span class="over">{b}</span>{sheets}{symbol if remote else ""}</div>')
    else:
        fig = f'<div class="fig plate"><span class="over">{b}</span>{symbol}</div>'
    summary = f'<p>{E(c["summary"])}</p>' if c.get("summary") else ""
    angle = f'<div class="angle"><b>Modern angle</b>{E(c["angle"])}</div>' if c.get("feat") and c.get("angle") else ""
    body = (f'<div class="cbody"><span class="fieldname">{E(c["field"])} · <span class="num-id">{E(c["number"])}</span></span>'
            f'<h3><a href="{E(c["href"])}">{E(c["title"])}</a></h3>{summary}{angle}<span class="tstat">{b}</span></div>')

    def fact(m):
        label, v, title = (list(m) + [None])[:3]
        value = meter(v["build"]) + E(v["name"]) if isinstance(v, dict) else E(v)
        tip = f' title="{E(title)}"' if title else ""
        return f'<div><small>{E(label)}</small><span{tip}>{value}</span></div>'
    meta = f'<div class="cmeta">{"".join(fact(m) for m in c["meta"])}</div>' if c.get("meta") else ""
    cls = "card" + (" acard" if c.get("archive") else "") + (" feat" if c.get("feat") else "")
    inner = f'{fig}<div class="side">{body}{meta}</div>' if c.get("feat") else fig + body + meta
    return f'<article class="{cls}" data-id="{E(c["id"])}">{inner}</article>'


class Components:
    def img(self, pid, k=1):
        return f"/img/p/{pid}/{k}.png"

    def card(self, r, i=0, feat=False):
        """A register patent as a card (card_html below draws it)."""
        e = r["entry"]
        owner = (e["a"] if e["st"] == "abandoned" or not e["ia"] else "None recorded") or "Not recorded"
        lab, val = freed_line(e)
        first = ["Build", {"build": e["b"], "name": BUILD[e["b"]]}, f"Estimate: {BUILD_MEANS[e['b']]}"] if e["b"] else ["Filed", (e["e"] or e["f"] or "—")[:4]]
        return card_html({"id": e["id"], "href": purl(e["id"]), "title": e["t"], "number": e["n"], "field": self.fields.get(e["ind"], e["ind"]),
                          "status": {"cls": e["st"], "label": STATUS[e["st"]]}, "img": self.img(e["id"]) if e["fig"] else "", "glyph": e["ind"],
                          "sheets": e["sh"], "eager": i < 4, "summary": e["h"], "angle": e["tw"], "feat": feat,
                          "meta": [first, [lab, val], ["Applicant" if e["st"] == "abandoned" else "Assignee", owner, owner]]})

    def pickrow(self, r):
        """A compact line for the home page's further picks: drawing thumbnail, name, field, number and status."""
        e = r["entry"]
        thumb = f'<img src="{self.img(e["id"])}" alt="" loading="lazy" decoding="async">' if e["fig"] else f'<svg class="fglyph" aria-hidden="true"><use href="#f-{e["ind"]}"/></svg>'
        return (f'<li><a href="{purl(e["id"])}"><span class="pthumb">{thumb}</span><span class="ptext"><b>{E(e["t"])}</b>'
                f'<small>{E(self.fields.get(e["ind"], e["ind"]))} · <span class="num">{E(e["n"])}</span> · <span class="st-{e["st"]}">{STATUS[e["st"]]}</span></small></span></a></li>')

    def field_thumb(self, k):
        r = next((r for r in self.doc_by_field.get(k, []) if r["entry"]["fig"] and coolness(r) > 0), None)
        return f'<img src="{self.img(r["entry"]["id"])}" alt="" loading="lazy">' if r else icon("sheet")

    def filters(self, field=None):
        fields = "".join(f'<button class="chip" type="button" data-ind="{k}" aria-pressed="false">{E(n)} <small>{len(self.by_field.get(k, [])):,}</small></button>' for k, n in self.fields.items())
        st = collections.Counter(r["entry"]["st"] for r in self.rows)
        return f"""
<form class="filters" id="filters" role="search">
  {'' if field else f'<div class="frow colrow"><span class="lab">Collection</span><div class="seg" role="group" aria-label="Collection"><button type="button" data-coll="" aria-pressed="true">Recent, US <small class="num">{self.meta["count"]:,}</small></button><button type="button" data-coll="archive" aria-pressed="false">Archive, 4 offices <small class="num">{self.meta.get("archive", 0):,}</small></button></div></div>'}
  <div class="frow qrow"><label class="sr" for="q">Search</label><input class="field" id="q" name="q" type="search" placeholder="Search names, titles, owners or patent numbers" autocomplete="off"><button class="chip ftoggle" type="button" id="fToggle" aria-expanded="false" aria-controls="filters">Filters</button></div>
  {'' if field or len(self.meta.get("archiveSpans", [])) < 2 else '<div class="frow regrow"><span class="lab">From</span><button class="chip" type="button" data-reg="" aria-pressed="true">All</button>' + "".join(f'<button class="chip" type="button" data-reg="{n}" aria-pressed="false">{n} <small class="num">{b - a:,}</small></button>' for n, a, b in self.meta["archiveSpans"]) + '</div>'}
  {'' if field else f'<div class="frow" id="fInd"><span class="lab">Field</span><div class="frow scrollrow"><button class="chip" type="button" data-ind="" aria-pressed="true">All</button>{fields}</div></div>'}
  <div class="frow"><span class="lab">Status</span>
    <button class="chip" type="button" data-st="" aria-pressed="true">All</button>
    <button class="chip" type="button" data-st="lapsed" aria-pressed="false">Lapsed <small>{st["lapsed"]:,}</small></button>
    <button class="chip" type="button" data-st="expired" aria-pressed="false">Expired, full term <small>{st["expired"]:,}</small></button>
    <button class="chip" type="button" data-st="abandoned" aria-pressed="false">Likely abandoned applications <small>{st["abandoned"]:,}</small></button></div>
  <div class="frow"><span class="lab" title="Our estimate of the effort for a first working prototype, not for production">Build</span>
    <button class="chip" type="button" data-b="" aria-pressed="true">Any</button>
    <button class="chip" type="button" data-b="2" aria-pressed="false">Weekend or garage</button>
    <button class="chip" type="button" data-b="3" aria-pressed="false">Up to workshop</button></div>
  <div class="frow"><span class="lab">Options</span>
    <button class="chip" type="button" id="fFig" aria-pressed="false">With drawings</button>
    <button class="chip" type="button" id="fSolo" aria-pressed="false" title="Granted with no assignee recorded, usually to individual inventors">No assignee</button>
    <button class="chip" type="button" id="fFree" aria-pressed="false">Hide reserved</button>
    <label class="sr" for="sort">Sort</label>
    <select class="field" id="sort">
      <option value="relevance">Best match</option>
      <option value="build">Recommended</option>
      <option value="recent">Most recently freed</option>
      <option value="added">Newly added</option>
      <option value="old">Oldest filing first</option>
    </select></div>
</form>
<div class="countbar"><div class="count" id="count" aria-live="polite"></div>{VIEWTOG.format(grid="grid")}</div><div class="archhint" id="archHint" hidden></div>"""

    def listing(self, rows):
        """The first page of a list as plain HTML, for visitors without JavaScript and for search engines.
        browse.js replaces it with the live catalog."""
        return (f'<h2 class="sr">Patents</h2><div class="grid" id="grid">{"".join(self.card(r, i) for i, r in enumerate(rows[:48]))}</div>'
                '<div class="empty" id="empty" hidden><b>Nothing matches.</b><p>Loosen a filter or try a different word.</p></div>'
                '<div class="more"><button class="btn secondary" id="more" hidden>Show more</button></div>')
