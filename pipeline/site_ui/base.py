"""Shared constants and small helpers for every page: escaping, dates, numbers, icons, status labels, navigation, world statistics."""

import datetime as dt
import html
import json
import re
import unicodedata
from pathlib import Path


WEB = Path(__file__).resolve().parents[2] / "web"
STATIC = WEB / "static"
CONFIG = json.loads((WEB / "config.json").read_text())
SITE = CONFIG["site_url"].rstrip("/")
STATUS = {"lapsed": "Lapsed, fee not paid", "expired": "Expired, full term", "abandoned": "Likely abandoned application"}
BUILD = ["", "Weekend", "Garage", "Workshop", "Lab", "Industrial"]
# what each level means (How it works, and the title on every build label); an editorial estimate for a first working prototype
BUILD_MEANS = ["", "a first prototype from off-the-shelf parts and hand tools, in a few days", "basic power tools, simple electronics or 3D printing, in a few weeks",
              "machining, custom circuit boards or careful assembly", "lab equipment, special materials or controlled processes", "factory equipment or large-scale processes"]
EXT = 'target="_blank" rel="noopener noreferrer"'
FIELD_NOTES = {
    "software": "Apps, web services, interfaces and business systems.",
    "ai": "Vision, speech, learning systems and the sensors that feed them.",
    "medical": "Devices for diagnosis, therapy, rehab and everyday care.",
    "electronics": "Circuits, chargers, audio, alarms and connected hardware.",
    "industrial": "Handling, fabrication, building and process equipment.",
    "consumer": "Things for the home, kitchen, pets, travel and daily life.",
    "robotics": "Arms, mobile robots, grippers and automation.",
    "tools": "Hand tools, jigs, fixtures and workshop helpers.",
    "agrifood": "Growing, gardening, animals, cooking and food handling.",
    "biotech": "Lab equipment, diagnostics, drugs and biological methods.",
    "materials": "Chemistry, coatings, composites and new materials.",
    "energy": "Solar, batteries, charging, heating and power.",
    "mobility": "Bikes, vehicles, aircraft, boats and their accessories.",
    "sports": "Training gear, games, outdoor equipment and fitness.",
    "designs": "Design patents: the shape and look of products, free to copy once their term ends.",
    "other": "Everything outside the fields above, from printing to music to packaging.",
}
BLOCK = 256    # catalog cards per file
WEIGHTS = [10, 6, 5, 4, 3, 2]  # search: name, title as filed, summary, tags, owner, first sentence of the abstract
E = lambda s: html.escape("" if s is None else str(s), quote=True)


def d(s):
    return dt.date.fromisoformat(s[:10]) if s else None


def full_date(s):
    x = d(s)
    return f"{x:%B} {x.day}, {x.year}" if x else "—"


def short_date(s):
    x = d(s)
    return f"{x:%b} {x.year}" if x else "—"


def add_years(s, y):
    x = d(s)
    months = x.month - 1 + round(y * 12)
    yy, mm = x.year + months // 12, months % 12 + 1
    day = min(x.day, [31, 29 if yy % 4 == 0 and (yy % 100 or yy % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][mm - 1])
    return dt.date(yy, mm, day).isoformat()


def big_number(n):
    return f"{n / 1e6:.1f} million" if n >= 1_000_000 else f"{n:,}"


def icon(name):
    return f'<svg class="i" aria-hidden="true"><use href="#i-{name}"/></svg>'


def meter(b):
    return '<span class="meter" aria-hidden="true">' + "".join(f'<i class="{"on" if i <= b else ""}"></i>' for i in range(1, 6)) + "</span>"


def badge(st):
    return f'<span class="badge {st}">{STATUS[st]}</span>'


def purl(pid):
    return f"/patents/{pid}/"


def freed_line(e):
    if e["st"] == "lapsed":
        return "Lapsed", short_date(e["x"])
    if e["st"] == "expired":
        return "Term ended", short_date(e.get("te"))
    return "Published", (e["p"] or "—")[:4]


# ---------------------------------------------------------------- layout

SPRITE = """<svg width="0" height="0" style="position:absolute" aria-hidden="true">
<symbol id="f-software" viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 9h18M10 12.5l-2 2 2 2M14 12.5l2 2-2 2"/></symbol><symbol id="f-ai" viewBox="0 0 24 24"><circle cx="6" cy="6" r="2"/><circle cx="18" cy="6" r="2"/><circle cx="12" cy="12" r="2.2"/><circle cx="12" cy="19" r="2"/><path d="M7.6 7.3l2.7 3.1M16.4 7.3l-2.7 3.1M12 14.2V17"/></symbol><symbol id="f-medical" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7.5v9M7.5 12h9"/></symbol><symbol id="f-electronics" viewBox="0 0 24 24"><path d="M2 12h4l1.5-4.5 3 9 3-9 3 9L18 12h4"/></symbol><symbol id="f-imaging" viewBox="0 0 24 24"><rect x="3" y="7" width="18" height="13" rx="2"/><path d="M8 7l1.5-3h5L16 7"/><circle cx="12" cy="13.5" r="3.5"/></symbol><symbol id="f-telecom" viewBox="0 0 24 24"><path d="M12 21v-9"/><circle cx="12" cy="9.5" r="1.6"/><path d="M8.3 5.8a5.3 5.3 0 0 0 0 7.4M15.7 5.8a5.3 5.3 0 0 1 0 7.4M5.6 3.2a9 9 0 0 0 0 12.6M18.4 3.2a9 9 0 0 1 0 12.6"/></symbol><symbol id="f-chips" viewBox="0 0 24 24"><rect x="6" y="6" width="12" height="12" rx="1.5"/><rect x="9.5" y="9.5" width="5" height="5"/><path d="M9 2.5v3.5M15 2.5v3.5M9 18v3.5M15 18v3.5M2.5 9H6M2.5 15H6M18 9h3.5M18 15h3.5"/></symbol><symbol id="f-industrial" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><circle cx="12" cy="12" r="7"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9 7 7M17 17l2.1 2.1M4.9 19.1 7 17M17 7l2.1-2.1"/></symbol><symbol id="f-consumer" viewBox="0 0 24 24"><path d="M5 8h14l-1.2 12H6.2z"/><path d="M9 8V6.5a3 3 0 0 1 6 0V8"/></symbol><symbol id="f-robotics" viewBox="0 0 24 24"><path d="M3 21h9M7.5 21v-4"/><circle cx="7.5" cy="15.5" r="1.6"/><circle cx="13" cy="9" r="1.6"/><path d="M8.6 14.3l3.3-4.1M14.5 8.6l4.5.6M19 9.2l2-2M19 9.2l2 2"/></symbol><symbol id="f-tools" viewBox="0 0 24 24"><path d="M14.7 6.3a4 4 0 0 0-5 5L3.5 17.5l3 3 6.2-6.2a4 4 0 0 0 5-5l-2.4 2.4-2.6-.5-.5-2.6z"/></symbol><symbol id="f-agrifood" viewBox="0 0 24 24"><path d="M12 21V11"/><path d="M12 11c0-4.2 3-7 8-7 0 5-3 7.6-8 7z"/><path d="M12 14.5c0-3-2.2-5.2-6.5-5.2 0 3.3 2.2 5.3 6.5 5.2z"/></symbol><symbol id="f-biotech" viewBox="0 0 24 24"><path d="M8 3c0 5 8 5 8 9s-8 4-8 9M16 3c0 5-8 5-8 9s8 4 8 9M9 6h6M9 18h6M10 12h4"/></symbol><symbol id="f-materials" viewBox="0 0 24 24"><path d="M12 3l7.5 4.3v8.6L12 20.2l-7.5-4.3V7.3z"/><path d="M12 3v8.6M12 11.6l7.5-4.3M12 11.6l-7.5-4.3"/></symbol><symbol id="f-energy" viewBox="0 0 24 24"><path d="M13 2L4.5 13.5H11L10 22l8.5-11.5H12z"/></symbol><symbol id="f-mobility" viewBox="0 0 24 24"><path d="M3.5 16.5V13l2.2-5h12.6l2.2 5v3.5z"/><circle cx="7.5" cy="16.5" r="2"/><circle cx="16.5" cy="16.5" r="2"/><path d="M3.5 13h17"/></symbol><symbol id="f-sports" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M5.6 5.6c3.5 3.5 3.5 9.3 0 12.8M18.4 5.6c-3.5 3.5-3.5 9.3 0 12.8"/></symbol><symbol id="f-defense" viewBox="0 0 24 24"><path d="M12 3l8 3v6c0 5-3.5 8.2-8 9-4.5-.8-8-4-8-9V6z"/></symbol><symbol id="f-designs" viewBox="0 0 24 24"><circle cx="12" cy="4.5" r="1.5"/><path d="M12 6 6.5 21M12 6l5.5 15M8 16.5h8"/></symbol><symbol id="f-other" viewBox="0 0 24 24"><path d="M9 18h6M10 21h4"/><path d="M12 3a6 6 0 0 0-3.6 10.8c.9.7 1.6 1.6 1.6 2.7v.5h4v-.5c0-1.1.7-2 1.6-2.7A6 6 0 0 0 12 3z"/></symbol>
<symbol id="i-grid" viewBox="0 0 24 24"><rect x="4" y="4" width="7" height="7" rx="1"/><rect x="13" y="4" width="7" height="7" rx="1"/><rect x="4" y="13" width="7" height="7" rx="1"/><rect x="13" y="13" width="7" height="7" rx="1"/></symbol><symbol id="i-rows" viewBox="0 0 24 24"><path d="M4 6h16M4 12h16M4 18h16"/></symbol><symbol id="i-list" viewBox="0 0 24 24"><rect x="3.5" y="5" width="6.5" height="5" rx="1"/><path d="M13 6.5h7.5M13 9h4.5"/><rect x="3.5" y="14" width="6.5" height="5" rx="1"/><path d="M13 15.5h7.5M13 18h4.5"/></symbol><symbol id="i-check" viewBox="0 0 24 24"><path d="M5 12.5l4.5 4.5L19 7.5"/></symbol>
<symbol id="i-search" viewBox="0 0 24 24"><circle cx="11" cy="11" r="6.5"/><path d="M16 16l4 4"/></symbol>
<symbol id="i-x" viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18"/></symbol>
<symbol id="i-ext" viewBox="0 0 24 24"><path d="M14 5h5v5M19 5l-8 8M18 14v4a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h4"/></symbol>
<symbol id="i-link" viewBox="0 0 24 24"><path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/></symbol>
<symbol id="i-sheet" viewBox="0 0 24 24"><rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 8h6M9 12h6M9 16h3"/></symbol>
<symbol id="i-spark" viewBox="0 0 24 24"><path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5L18 18M6 18l2.5-2.5M15.5 8.5L18 6"/></symbol>
<symbol id="i-flag" viewBox="0 0 24 24"><path d="M5 21V4M5 4h11l-2 4 2 4H5"/></symbol>
<symbol id="i-left" viewBox="0 0 24 24"><path d="M15 6l-6 6 6 6"/></symbol>
<symbol id="i-right" viewBox="0 0 24 24"><path d="M9 6l6 6-6 6"/></symbol>
<symbol id="i-shield" viewBox="0 0 24 24"><path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6z"/><path d="M9 12l2 2 4-4"/></symbol>
<symbol id="i-clock" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"/><path d="M12 8v4l3 2"/></symbol>
<symbol id="i-db" viewBox="0 0 24 24"><ellipse cx="12" cy="6" rx="7" ry="3"/><path d="M5 6v12c0 1.7 3.1 3 7 3s7-1.3 7-3V6M5 12c0 1.7 3.1 3 7 3s7-1.3 7-3"/></symbol>
<symbol id="i-file" viewBox="0 0 24 24"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h6"/></symbol>
<symbol id="i-copy" viewBox="0 0 24 24"><rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h8"/></symbol>
<symbol id="i-menu" viewBox="0 0 24 24"><path d="M4 7h16M4 12h16M4 17h16"/></symbol>
<symbol id="i-user" viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M4 20c1.5-4 4.5-6 8-6s6.5 2 8 6"/></symbol>
<symbol id="i-sun" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></symbol>
<symbol id="i-moon" viewBox="0 0 24 24"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/></symbol>
<symbol id="i-bookmark" viewBox="0 0 24 24"><path d="M7 4h10a1 1 0 0 1 1 1v15l-6-4-6 4V5a1 1 0 0 1 1-1z"/></symbol>
<symbol id="i-shuffle" viewBox="0 0 24 24"><path d="M4 7h3c4 0 6 10 10 10h3M4 17h3c1.5 0 2.7-1.4 3.7-3M14.3 10c1-1.6 2.2-3 3.7-3h2M17 4l3 3-3 3M17 14l3 3-3 3"/></symbol>
<symbol id="i-chart" viewBox="0 0 24 24"><path d="M4 20V4M4 20h16M8 16v-5M12 16V8M16 16v-8"/></symbol>
<symbol id="i-cmd" viewBox="0 0 24 24"><path d="M9 6a3 3 0 1 0-3 3h12a3 3 0 1 0-3-3v12a3 3 0 1 0 3-3H6a3 3 0 1 0 3 3z"/></symbol>
<symbol id="i-gear" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/></symbol>
</svg>"""
# All patents (pipeline/world.py) lives in its own Pages projects; web/world/live.json names them once they are deployed
WORLD = json.loads((WEB / "world" / "live.json").read_text()) if (WEB / "world" / "live.json").exists() else None
WSTATS = json.loads((WEB / "world" / "stats.json").read_text()) if WORLD and (WEB / "world" / "stats.json").exists() else None  # world.py stats
OFFICES = len(WSTATS["countries"]) if WSTATS else 106  # patent offices in the world data
WORLD_AT = dt.date.fromtimestamp((WEB / "world" / "live.json").stat().st_mtime) if WORLD else None  # when the world data was loaded
COUNTRY = dict(re.findall(r'(\b[A-Z]{2}): "([^"]+)"', (WEB / "functions" / "_world.js").read_text().split("export const COUNTRY")[1].split("};")[0]))
NAV = ([("/browse/", "Free to use"), ("/all/", "All patents"), ("/opportunities/", "Opportunities")] if WORLD else
       [("/browse/", "Browse"), ("/opportunities/", "Opportunities"), ("/fields/", "Fields")]) + [("/insights/", "Insights"), ("/studio/", "Studio"), ("/how-it-works/", "How it works")]
# card view or a dense table view of a result grid; app.js remembers the choice
VIEWTOG = ('<div class="viewtog" role="group" aria-label="View"><button type="button" data-view="list" data-for="{grid}" aria-pressed="true" title="List">'
           '<svg class="i" aria-hidden="true"><use href="#i-list"/></svg><span class="sr">List</span></button><button type="button" data-view="cards" data-for="{grid}" aria-pressed="false" title="Cards">'
           '<svg class="i" aria-hidden="true"><use href="#i-grid"/></svg><span class="sr">Cards</span></button><button type="button" data-view="table" data-for="{grid}" aria-pressed="false" title="Table">'
           '<svg class="i" aria-hidden="true"><use href="#i-rows"/></svg><span class="sr">Table</span></button></div>')
LOGO = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><circle cx="12" cy="12" r="6.2"/><path d="M12 1.5v21M1.5 12h21"/><circle cx="12" cy="12" r="1.4" fill="currentColor" stroke="none"/></svg>'
OWNER_NOISE = re.compile(r"\b(the|inc|incorporated|corp|corporation|co|company|ltd|limited|llc|l\.?l\.?c|lp|l\.?p|plc|gmbh|ag|kk|kabushiki|kaisha|sa|bv|nv|ab|oy|spa|srl)\b|[.,&']")
# Google's owner names, title-cased by world.py tidy(), with their acronyms and legal forms put back
OWNER_WORDS = {"Kk": "KK", "Ag": "AG", "Se": "SE", "Sa": "SA", "Nv": "NV", "Bv": "BV", "Ab": "AB", "Gmbh": "GmbH", "Ibm": "IBM", "Lg": "LG",
               "Nec": "NEC", "Basf": "BASF", "Zte": "ZTE", "Boe": "BOE", "Tdk": "TDK", "Ntt": "NTT", "Abb": "ABB", "Gen": "General"}


def owner_name(o):
    return " ".join(OWNER_WORDS.get(t, t) for t in o.split())


def owner_key(o):
    """A company name reduced to what identifies it, so spellings of one company count together."""
    return " ".join(OWNER_NOISE.sub(" ", o.lower()).split()) or o.lower()


def day_number(s):
    """Days since 1970-01-01, which fits two bytes until 2149; 0 when unknown."""
    return min(65535, max(1, (dt.date.fromisoformat(s[:10]) - dt.date(1970, 1, 1)).days)) if s else 0


SEARCH_STOP = set("a an and the of for to in on with by or at is it its from as be this that".split())


def search_words(text):
    """Words search can find: lower case, accents dropped, two letters or more with at least one letter.
    assets/js/catalog.js splits a query the same way."""
    t = unicodedata.normalize("NFKD", str(text or "").lower())
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    return [w for w in re.split(r"[^a-z0-9]+", t) if len(w) >= 2 and w not in SEARCH_STOP and re.search(r"[a-z]", w)]
