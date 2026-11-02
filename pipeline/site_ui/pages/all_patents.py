"""All patents (worldwide search)."""

import struct

import patents as P
from register import TODAY

from ..components import card_html
from ..base import COUNTRY, E, OFFICES, VIEWTOG, WEB, WORLD, WORLD_AT, WSTATS, big_number


class AllPatents:
    def world_first_cards(self, k=24):
        """The newest patents worldwide as plain HTML, so the page reads without JavaScript (readers, AI tools, search
        engines); assets/js/all.js draws the same cards (cards.js) and replaces them with the live list."""
        f = WEB / "world" / "cards" / "c" / "0.bin"
        if not f.exists():
            return ""
        b = f.read_bytes()
        n = struct.unpack_from("<I", b)[0]
        offs = struct.unpack_from(f"<{min(n, k) + 1}I", b, 4)
        base, keys, out = 4 + 4 * (n + 1), list(P.FIELDS), []
        self.world_ids = set()
        for i in range(min(n, k)):
            pid, t, a, date, cc, kind, flags, field = b[base + offs[i]:base + offs[i + 1]].decode().split("\t")
            # a US grant may carry a term adjustment for USPTO delay, so within 20 years of grant it may be in force (all.js cardHTML)
            past = int(flags) & 1 and not (cc == "US" and f"{int(date[:4]) + 20}{date[4:]}" > TODAY.strftime("%Y%m%d"))
            utility = kind.startswith("U")
            granted = int(flags) & 2 or kind[:1] in "BCES"
            label = "Past its term" if past else "Registered" if utility else "Granted" if granted else "Application"
            fk = keys[int(field)] if field.isdigit() and int(field) < len(keys) else "other"
            num = " ".join(x for x in pid.split("-") if x)
            self.world_ids.add(pid)
            out.append(card_html({"id": pid, "href": f"/patents/{pid}/", "title": t, "number": num, "field": f'{COUNTRY.get(cc, cc)} · {self.fields.get(fk, "")}',
                                  "archive": True, "glyph": fk, "img": "", "status": {"cls": "expired" if past else "plain", "label": label},
                                  "meta": [["Published", date[:4]], ["Kind", kind], ["Assignee", a or "—", a]]}))
        return "".join(out)

    def all_patents(self):
        n = WORLD["n"]
        body = f"""<div class="page">
<div class="sechead"><div><h1>All patents</h1>
<p class="lede">Search {big_number(n)} records from {OFFICES} patent offices to check what already exists before you build, buy or file. About {big_number(WSTATS['granted']) if WSTATS else 'most'} are granted patents or registered utility models and the rest published applications; it is Google's public patent data as loaded in {WORLD_AT:%B %Y}, not a complete or current register of every country. Status here is only granted or not: whether a patent is still in force isn't checked, except that very old filings are marked past their term. For patents we have checked, see <a href="/browse/">Free to use</a>.</p></div></div>
<form class="filters" id="wfilters" role="search">
  <div class="frow qrow"><label class="sr" for="wq">Search all patents</label><input class="field" id="wq" type="search" placeholder="Search titles and owners, or enter a number like CN112345678A" autocomplete="off"><button class="chip ftoggle" type="button" id="wToggle" aria-expanded="false" aria-controls="wfilters">Filters</button></div>
  <div class="frow"><span class="lab">Country</span><label class="sr" for="wcc">Country</label><select class="field" id="wcc"><option value="">All countries</option></select>
    <button class="chip" type="button" id="wfree" aria-pressed="false" title="Filed more than 20 years ago (26 for medicines). US patents granted in the past 20 years can still carry a term adjustment, so their pages say may be in force">Filed 20+ years ago</button></div>
  <div class="frow" role="group" aria-label="Document type"><span class="lab" title="Granted: a grant date in the data or a grant kind code (B, C, E, S; U for utility models)">Type</span>
    <div class="seg"><button type="button" data-type="" aria-pressed="true">All</button><button type="button" data-type="g" aria-pressed="false">Granted or registered</button><button type="button" data-type="a" aria-pressed="false">Applications</button></div></div>
  <div class="frow"><span class="lab" title="Patent Yard's grouping of each record's first classification codes">Field</span><label class="sr" for="wfld">Field</label><select class="field" id="wfld"><option value="">All fields</option></select></div>
  <div class="frow"><span class="lab" title="The year the application was first published (or filed, if it never was)">Published</span><label class="sr" for="wy1">Published from</label><select class="field" id="wy1"><option value="">Any year</option></select>
    <span class="muted" aria-hidden="true">to</span><label class="sr" for="wy2">Published to</label><select class="field" id="wy2"><option value="">Any year</option></select></div>
</form>
<div class="countbar"><p class="count" id="wcount" aria-live="polite">{n:,} records worldwide, newest publication first.</p>{VIEWTOG.format(grid="wgrid")}</div>
<h2 class="sr">Patents</h2><div class="grid" id="wgrid">{self.world_first_cards()}</div>
<div class="rowbtns results-foot"><button class="btn secondary" type="button" id="wmore" hidden>Show more</button></div>
<p class="muted fine-print">Records come from Google Patents Public Data, used under CC BY 4.0, and are refreshed from time to time. Results are listed newest first by first publication date; a search matches words in titles and owner names, or a publication number. A common word or a big filter keeps only its newest 250,000 records, and the count says so when that happens. "Past its term" means filed more than 20 years ago (26 for medicines), except US patents granted within the past 20 years, which could carry a term adjustment. Every other status is as published, so confirm it with the official register before relying on it.</p>
</div>"""
        self.page("/all/", "All patents", f"Search {big_number(n)} patent records (granted patents and published applications) from {OFFICES} patent offices, with the ones past their term marked.",
                  body, section="/all/", scripts=("all",))
