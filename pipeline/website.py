"""The public website: web/dist, a static site for Cloudflare Pages (or any static host).

Every page is plain HTML, so it loads fast, works without JavaScript and can be indexed. JavaScript in
web/static/assets/js adds search and filters, the drawing viewer, accounts and reservations (Supabase) and the
"Reinvent with Claude" kit, which writes a prompt and a PDF brief for the visitor's own Claude.

  python3 pipeline.py web     builds web/dist from the same records as the claude.ai build
"""
import array
import collections
import datetime as dt
import fcntl
import gzip
import html
import itertools
import json
import multiprocessing
import os
import random
import re
import shutil
import struct
import time
import unicodedata
import urllib.request
import zlib
from pathlib import Path
from urllib.parse import quote

import patents as P
from build import collect, dossier
from register import MAX_SHEETS, TODAY, archived, gazette_all

WEB = Path(__file__).resolve().parent.parent / "web"
DIST = WEB / "dist"
STATIC = WEB / "static"
CONFIG = json.loads((WEB / "config.json").read_text())
SITE = CONFIG["site_url"].rstrip("/")
STATUS = {"lapsed": "Lapsed, fee not paid", "expired": "Expired, full term", "abandoned": "Likely abandoned"}
BUILD = ["", "Weekend", "Garage", "Workshop", "Lab", "Industrial"]
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

SHARDS = 1024  # patent pages, drawings, kit data and archive records are packed into this many files each (web/functions/_lib.js); fewer files keeps the site under Cloudflare Pages' 20,000
BLOCK = 256    # catalog cards per file
WEIGHTS = [10, 6, 5, 4, 3, 2]  # search: name, title as filed, summary, tags, owner, first sentence of the abstract
ARCH_BLOCK, ARCH_BUCKETS = 1536, 1024  # the archive: card text per file, search index files (a free site holds 20,000 files)
ARCH_KEYS = ("id", "n", "t", "f", "p", "te", "a", "i", "ind", "cpc", "app", "pg", "sh", "k", "g", "ab")  # k: "" utility, S design, A application, E/CA/AU other offices
REGIONS = {"E": "Europe", "CA": "Canada", "AU": "Australia"}  # archive kinds from other offices (functions/_archive.js REGIONS)
SPAN_ORDER = ["US", "Europe", "Canada", "Australia"]  # the archive is ordered by region, so browse filters one by its index range

E = lambda s: html.escape("" if s is None else str(s), quote=True)
DEPENDENT = re.compile(r"\bclaims?\s+\d", re.I)


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


def png_size(path):
    b = path.read_bytes()[16:24]
    return struct.unpack(">II", b)


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


def links(e, d_):
    _, num, kind = e["id"].split("-")
    app = e["st"] == "abandoned"
    return {
        "pdf": f"https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/{num}",
        "ppubs": f"https://ppubs.uspto.gov/pubwebapp/external.html?q={num}.pn.&db={'US-PGPUB' if app else 'USPAT'}",
        "center": f"https://patentcenter.uspto.gov/applications/{re.sub(r'[^0-9]', '', d_.get('app') or '')}" if d_.get("app") else "https://patentcenter.uspto.gov/",
        "google": f"https://patents.google.com/patent/US{num}{kind}/en",
        "justia": f"https://patents.justia.com/patent/{num}",
        "fpo": f"https://www.freepatentsonline.com/y{num[:4]}/{num[4:]}.html" if app else f"https://www.freepatentsonline.com/{num}.html",
        "espacenet": f"https://worldwide.espacenet.com/patent/search?q=pn%3DUS{num}{kind}",
        "fees": "https://fees.uspto.gov/MaintenanceFees/",
    }


def gp(pid):
    _, num, kind = (pid.split("-") + [""])[:3]
    return f"https://patents.google.com/patent/US{num}{kind}/en"


def cite_ref(raw):
    x = str(raw).strip()
    if re.fullmatch(r"\d{4}/\d{7}", x):
        return f"US {x}", f"https://patents.google.com/patent/US{x.replace('/', '')}A1/en"
    if re.fullmatch(r"\d{5,8}", x):
        return f"US {int(x):,}", f"https://patents.google.com/patent/US{x}/en"
    if re.fullmatch(r"D\d{4,7}", x):
        return f"US {x} (design)", f"https://patents.google.com/patent/US{x}S/en"
    if re.fullmatch(r"RE\d{4,6}", x):
        return f"US {x} (reissue)", f"https://patents.google.com/patent/US{x}E/en"
    return f"US {x}", "https://patents.google.com/?q=" + quote("US" + re.sub(r"[^A-Za-z0-9]", "", x))


def why_free(e):
    fam = e["fam"]
    rel = f"Its {fam - 1} US {'relative has' if fam - 1 == 1 else 'relatives have'} also lapsed, expired or never issued." if fam > 1 \
        else "It has no other US patents or pending applications in its family."
    if e["st"] == "lapsed":
        og = f" of {full_date(e['og']['d'])}" if e.get("og") else ""
        recent = e["x"] and (TODAY - d(e["x"])).days < 120
        return [f"The USPTO Official Gazette{og} lists it as expired on {full_date(e['x'])} for an unpaid maintenance fee.",
                "It isn't on any reinstatement notice published since.", rel], \
            ("It lapsed only recently. Owners can still pay late and reinstate it, most often in the first months; we check every new notice. "
             if recent else "") + "We check US rights only. Check foreign counterparts before selling abroad."
    if e["st"] == "expired":
        return [f"Filed {full_date(e['f'])}. A US utility patent lasts 20 years from filing, so its base term ended {full_date(e['te'])}.",
                f"Granted {full_date(e['p'])}, within four years of filing, so any term adjustment for USPTO delay is short. The filing is over 24 years old.",
                rel, "It isn't in a drug or chemistry class, where term extensions are common."], \
            "Rarely, a term adjustment extends a patent by months or years. Confirm the expiration on Patent Center."
    return [f"Published {full_date(e['p'])}, and no patent has issued in its family since.",
            "Its family has had no new filings for more than seven years.",
            f"Filed {full_date(e['f'])}. Applications rarely stay pending this long."], \
        "This status is inferred. Confirm it on Patent Center before relying on it."


# ---------------------------------------------------------------- graphics built only from the patent's own data

def fee_schedule(e):
    """Fees are due 3.5, 7.5 and 11.5 years after grant; a lapse at the 4th, 8th or 12th anniversary means the fee due
    half a year earlier went unpaid and every earlier one was paid."""
    if e["st"] != "lapsed" or not e["p"] or not e["x"]:
        return None
    years = (d(e["x"]) - d(e["p"])).days / 365.25
    missed = 0 if years < 6 else 1 if years < 10 else 2
    return [(y, add_years(e["p"], y), "paid" if k < missed else "missed" if k == missed else "never") for k, y in enumerate((3.5, 7.5, 11.5))]


def timeline_events(e, doc):
    ev = []
    if e["e"] and e["e"] < e["f"]:
        ev.append((e["e"], "Earliest priority date", ""))
    ev.append((e["f"], "Application filed", ""))
    if e["st"] == "abandoned":
        ev.append((e["p"], "Application published", ""))
    else:
        pub = next((m for m in doc["family"] if m.get("k") == "application" and m.get("f") == e["f"] and m.get("p")), None)
        if pub:
            ev.append((pub["p"], "Application published", ""))
        ev.append((e["p"], "Patent granted", ""))
    fees = fee_schedule(e)
    if fees:
        ev += [(due, f"{y}-year fee {'paid' if st == 'paid' else 'not paid'}", "bad" if st == "missed" else "") for y, due, st in fees if st != "never"]
        ev.append((e["x"], "Patent expired", "bad"))
    if e["st"] == "expired" and e.get("te"):
        ev.append((e["te"], "20-year term ended", "bad"))
    return sorted((x for x in ev if x[0]), key=lambda x: x[0])


def timeline_svg(events):
    W, pad, y0 = 760, 40, 70
    t0, t1 = d(events[0][0]), d(events[-1][0])
    span = max((t1 - t0).days, 1)
    X = lambda s: pad + (d(s) - t0).days / span * (W - pad * 2)
    years = list(range(t0.year + 1, t1.year + 1))
    every = max(1, -(-len(years) // 10))
    col = lambda k: "var(--lapsed)" if k == "bad" else "var(--ink-3)" if k == "now" else "var(--accent)"
    out = [f'<svg class="chart" viewBox="0 0 {W} {y0 + 150}" role="img" aria-label="{E("Timeline: " + "; ".join(f"{t} {full_date(s)}" for s, t, _ in events))}">',
           f'<line class="axis" x1="{pad}" y1="{y0}" x2="{W - pad}" y2="{y0}" stroke-width="2"/>']
    for i, y in enumerate(years):
        if i % every == 0:
            x = X(f"{y}-01-01")
            out.append(f'<line class="tick" x1="{x:.1f}" y1="{y0 - 6}" x2="{x:.1f}" y2="{y0 + 6}"/><text class="muted" x="{x:.1f}" y="{y0 - 12}" text-anchor="middle">{y}</text>')
    last, lane = -1e9, 0
    for s, t, k in events:
        x = X(s)
        lane = (lane + 1) % 3 if x - last < 120 else 0
        last = x
        ly = y0 + 28 + lane * 38
        anchor = "start" if x < 110 else "end" if x > W - 110 else "middle"
        dash = ' stroke-dasharray="3 3"' if k == "now" else ""
        out.append(f'<line x1="{x:.1f}" y1="{y0}" x2="{x:.1f}" y2="{ly - 12}" stroke="{col(k)}" stroke-width="1"{dash}/>'
                   f'<circle cx="{x:.1f}" cy="{y0}" r="{4 if k == "now" else 6}" fill="{"var(--surface)" if k == "now" else col(k)}" stroke="{col(k)}" stroke-width="2"/>'
                   f'<text class="lbl" x="{x:.1f}" y="{ly}" text-anchor="{anchor}">{E(t)}</text>'
                   f'<text class="muted" x="{x:.1f}" y="{ly + 16}" text-anchor="{anchor}">{E(full_date(s).replace("January", "Jan").replace("February", "Feb").replace("August", "Aug").replace("September", "Sep").replace("October", "Oct").replace("November", "Nov").replace("December", "Dec"))}</text>')
    out.append("</svg>")
    return "".join(out)


def claim_parents(claims):
    """claim number -> the earlier claim it names ("as claimed in claim 2"), read from each claim's own text."""
    nums, parent = {n for n, _ in claims}, {}
    for n, t in claims:
        m = re.search(r"\bclaims?\s+(\d{1,3})", t, re.I)
        pn = int(m.group(1)) if m else None
        if pn and pn in nums and pn < n:
            parent[n] = pn
    return parent


def claim_list(claims):
    parent = claim_parents(claims)

    def depth(n):
        k = 0
        while n in parent and k < 3:
            n, k = parent[n], k + 1
        return k

    items = []
    for n, c in claims:
        dep = bool(DEPENDENT.search(c))
        d_ = max(depth(n), 1) if dep else 0
        items.append(f'<li class="{f"dep d{d_}" if dep else "ind"}" id="claim-{n}"><span class="cn">{n}</span><div>'
                     f'{"" if dep else "<em>Independent claim</em>"}{E(c)}</div></li>')
    return f'<ol class="claimlist">{"".join(items)}</ol>'


def claim_map(claims):
    """Each independent claim with the claims that build on it, as numbers, so nothing is cut off."""
    parent = claim_parents(claims)

    def root(n):
        while n in parent:
            n = parent[n]
        return n

    groups = {n: [] for n, c in claims if not DEPENDENT.search(c)}
    for n, c in claims:
        if n not in groups and root(n) in groups:
            groups[root(n)].append(n)
    rows = "".join(
        f'<div class="cgroup"><a class="ci" href="#claim-{n}">Claim {n}</a><small>{len(deps) or "No"} {"claim builds" if len(deps) == 1 else "claims build"} on it</small>'
        + ('<div class="cdeps">' + "".join(f'<a href="#claim-{k}">{k}</a>' for k in deps) + "</div>" if deps else "") + "</div>"
        for n, deps in groups.items())
    return (f'<div class="sidecard"><div class="panel"><div class="block"><h3>Claim map</h3><p class="muted" style="font-size:13px;margin-bottom:12px">'
            f'Independent claims stand on their own. The others add detail to the claim they name.</p>{rows}</div></div></div>')


def figure_lines(figs):
    """The patent's brief description of its drawings, without later mentions that start again at FIG. 1."""
    out, top = [], 0
    for f in figs:
        m = re.search(r"\d+", f)
        k = int(m.group()) if m else top
        if k < top:
            break
        top = k
        out.append(f)
    return out


# ---------------------------------------------------------------- layout

SPRITE = """<svg width="0" height="0" style="position:absolute" aria-hidden="true">
<symbol id="i-check" viewBox="0 0 24 24"><path d="M5 12.5l4.5 4.5L19 7.5"/></symbol>
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
COUNTRY = dict(re.findall(r'(\b[A-Z]{2}): "([^"]+)"', (WEB / "functions" / "_world.js").read_text().split("export const COUNTRY")[1].split("};")[0]))
NAV = ([("/browse/", "Free to use"), ("/all/", "All patents"), ("/opportunities/", "Opportunities")] if WORLD else
       [("/browse/", "Browse"), ("/opportunities/", "Opportunities"), ("/fields/", "Fields")]) + [("/insights/", "Insights"), ("/studio/", "Studio"), ("/how-it-works/", "How it works")]
LOGO = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M4 20V9l8-5 8 5v11"/><path d="M9 20v-6h6v6"/></svg>'


class Site:
    def __init__(self, rows, meta):
        self.rows, self.meta = rows, meta  # rows in catalog order: patents with a note first, easiest to build, newest freed
        self.by_field, self.doc_by_field = {}, {}
        for r in sorted(rows, key=lambda r: r["entry"]["id"]):
            self.by_field.setdefault(r["entry"]["ind"], []).append(r)
        for r in rows:
            self.doc_by_field.setdefault(r["entry"]["ind"], []).append(r)
        self.field_pos = {r["entry"]["id"]: i for lst in self.by_field.values() for i, r in enumerate(lst)}
        self.fields = {k: v[0] for k, v in P.FIELDS.items() if k in self.by_field}
        self.ids = {r["entry"]["id"]: (1 if r["fig"] else 0) + len(r["extra"]) for r in rows}  # id -> drawing sheets on the site
        self.pages = []  # (path, lastmod) for the sitemap
        self.version, self.css = "", "/assets/site.css"
        self.default_og = next((self.img(r["entry"]["id"]) for r in rows if r["entry"]["fig"]), "/favicon.svg")

    # -------------------------------------------------------- shell
    def page(self, path, title, desc, body, *, section="", og_image=None, jsonld=None, scripts=(), lastmod=None, index=True, write=True):
        full_title = f"{title} · Patent Yard" if title != "Patent Yard" else ("Patent Yard: search 122.8 million patents, and the free ones" if WORLD else "Patent Yard: free-to-use patents from four patent offices")
        cur = ' aria-current="page"'
        nav = "".join(f'<a href="{href}"{cur if section == href else ""}>{label}</a>' for href, label in NAV)
        og = og_image or self.default_og
        ld_json = json.dumps(jsonld, separators=(",", ":")).replace("</", "<\\/") if jsonld else ""
        ld = f'<script type="application/ld+json">{ld_json}</script>' if jsonld else ""
        js = "".join(f'<script type="module" src="/assets/js/{s}.js"></script>' for s in ("app",) + tuple(scripts))  # unversioned: modules import each other by plain path
        fields_nav = "".join(f'<a href="/fields/{k}/">{E(n)}</a>' for k, n in self.fields.items())
        doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<script src="/assets/js/theme.js"></script>
<title>{E(full_title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{SITE}{path}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Patent Yard">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{SITE}{path}">
<meta property="og:image" content="{SITE}{og}">
<meta name="twitter:card" content="summary_large_image">
{'' if index else '<meta name="robots" content="noindex">'}
<meta name="theme-color" content="#F6F6F4" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0E0F11" media="(prefers-color-scheme: dark)">
<link rel="icon" href="/favicon.ico" sizes="32x32">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<link rel="alternate" type="application/atom+xml" title="New on Patent Yard" href="/feed.xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Schibsted+Grotesk:wght@600;700;800&family=Public+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&family=IBM+Plex+Mono:wght@400;500;600&display=swap">
<link rel="stylesheet" href="{self.css}">
{ld}
</head>
<body>
{SPRITE}
<a class="skip" href="#main">Skip to content</a>
<header class="top">
  <div class="wrap">
    <a class="brand" href="/" aria-label="Patent Yard home"><span class="mark">{LOGO}</span><b>Patent Yard</b></a>
    <nav class="mainnav" id="mainnav" aria-label="Main">{nav}</nav>
    <form class="hsearch" action="/browse/" role="search"><svg class="i" aria-hidden="true"><use href="#i-search"/></svg><label class="sr" for="hq">Search patents</label><input id="hq" name="q" type="search" placeholder="Search patents"><kbd class="hk" aria-hidden="true">/</kbd></form>
    <button class="iconbtn cmdbtn" type="button" id="cmdBtn" aria-label="Search and jump (Ctrl K)" title="Search and jump (⌘K)">{icon("search")}</button>
    <button class="iconbtn" type="button" id="themeBtn" aria-label="Switch between light and dark mode" title="Light or dark mode">{icon("sun").replace('class="i"', 'class="i sun"')}{icon("moon").replace('class="i"', 'class="i moon"')}</button>
    <span class="acct" id="acct"><a class="btn secondary sm" href="/account/">{icon("user")}<span>Sign in</span></a></span>
    <button class="menu-btn" id="menuBtn" aria-controls="mainnav" aria-expanded="false" aria-label="Menu">{icon("menu")}</button>
  </div>
</header>
<main id="main" class="wrap" tabindex="-1">
{body}
</main>
<footer class="foot">
  <div class="wrap">
    <div><b>Patent Yard</b><p style="margin-top:10px;max-width:44ch">A free register of patents from the US, Europe, Canada and Australia whose protection has ended, traced to official records, with tools to turn them into new inventions.</p><p class="num" id="footStat" style="margin-top:10px">Rechecked against USPTO records every day</p></div>
    <nav aria-label="Explore"><span class="kicker">Explore</span><a href="/browse/">Browse all</a><a href="/opportunities/">Opportunities</a><a href="/fields/">Fields</a><a href="/studio/">Invention studio</a><a href="/insights/">Insights</a><a href="/saved/">Saved patents</a><a href="/account/">My bench</a><a href="/feed.xml">New patents feed</a></nav>
    <nav aria-label="Fields"><span class="kicker">Fields</span>{fields_nav}</nav>
    <nav aria-label="Sources"><span class="kicker">Sources</span><a href="https://www.uspto.gov/learning-and-resources/official-gazette/official-gazette-patents" {EXT}>USPTO Official Gazette</a><a href="https://ppubs.uspto.gov/pubwebapp/" {EXT}>Patent Public Search</a><a href="https://patentcenter.uspto.gov/" {EXT}>Patent Center</a><a href="https://data.epo.org/linked-data/" {EXT}>EPO linked open data</a></nav>
    <nav aria-label="Company"><span class="kicker">Patent Yard</span><a href="/about/">About</a><a href="/how-it-works/">How it works</a><a href="/how-it-works/#faq">FAQ</a><a href="/contact/">Contact</a><a href="/settings/">Settings</a><a href="/legal/terms/">Terms</a><a href="/legal/privacy/">Privacy</a><a href="/legal/disclaimer/">Disclaimer</a><a href="/legal/copyright/">Copyright</a><a href="/legal/accessibility/">Accessibility</a></nav>
    <p class="fine">Patent data comes from the United States Patent and Trademark Office; the European Patent Office's Linked open EP data, used under <a href="https://creativecommons.org/licenses/by/4.0/" {EXT}>CC BY 4.0</a>; the Canadian Intellectual Property Office, and contains information licensed under the <a href="https://open.canada.ca/en/open-government-licence-canada" {EXT}>Open Government Licence – Canada</a>; and IP Australia's IPGOD, used under <a href="https://creativecommons.org/licenses/by/2.5/au/" {EXT}>CC BY 2.5 AU</a>.{" All patents uses Google Patents Public Data, under CC BY 4.0." if WORLD else ""} Patent Yard is not affiliated with any of these offices and does not give legal advice. Plain-English names, summaries and modern angles are Patent Yard's editorial notes.</p>
  </div>
</footer>
<div id="toast" role="status" aria-live="polite"></div>
<script src="/assets/js/config.js"></script>
{js}
</body>
</html>
"""
        if write:
            out = DIST / path.strip("/") / "index.html" if path.endswith("/") else DIST / path.lstrip("/")
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(doc)
            if index:
                self.pages.append((path, lastmod or TODAY.isoformat()))
        return doc

    # -------------------------------------------------------- pieces
    def img(self, pid, k=1):
        return f"/img/p/{pid}/{k}.png"

    def card(self, r, i=0, feat=False):
        """A patent card. assets/js/catalog.js draws the same markup from the catalog data; keep them in step."""
        e = r["entry"]
        owner = "Solo inventor" if e["ia"] else (e["a"] or "—")
        lab, val = freed_line(e)
        fig = (f'<div class="fig"><img src="{self.img(e["id"])}" alt="Drawing from {E(e["n"])}" loading="{"eager" if i < 4 else "lazy"}" decoding="async">'
               f'<span class="over">{badge(e["st"])}</span>'
               + (f'<span class="sheets">{icon("sheet")}{e["sh"]} {"drawing" if e["sh"] == 1 else "drawings"}</span>' if e["sh"] else "") + "</div>") \
            if e["fig"] else f'<div class="fig blank"><span class="over">{badge(e["st"])}</span><span class="numart">{E(e["n"])}</span></div>'
        body = (f'<div class="cbody"><span class="fieldname">{E(self.fields.get(e["ind"], e["ind"]))} · <span class="num-id">{E(e["n"])}</span></span>'
                f'<h3><a href="{purl(e["id"])}">{E(e["t"])}</a></h3><p>{E(e["h"])}</p>'
                + (f'<div class="angle"><b>Modern angle</b>{E(e["tw"])}</div>' if feat and e["tw"] else "") + "</div>")
        first = (f'<div><small>Build</small><span>{meter(e["b"])}{BUILD[e["b"]]}</span></div>' if e["b"]
                 else f'<div><small>Filed</small><span>{E((e["e"] or e["f"] or "—")[:4])}</span></div>')
        meta = (f'<div class="cmeta">{first}<div><small>{lab}</small><span>{E(val)}</span></div>'
                f'<div><small>{"Applicant" if e["st"] == "abandoned" else "Owner"}</small><span title="{E(owner)}">{E(owner)}</span></div></div>')
        inner = f'{fig}<div class="side">{body}{meta}</div>' if feat else f"{fig}{body}{meta}"
        return f'<article class="card{" feat" if feat else ""}" data-id="{e["id"]}">{inner}</article>'

    # -------------------------------------------------------- pages
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
        m = self.meta
        total = m["count"] + m.get("archive", 0)
        by_field = m.get("archiveByField", {})
        chips = "".join(f'<a class="fchip" href="/fields/{k}/"><span>{E(n)}</span><small class="num">{len(self.by_field[k]) + by_field.get(k, 0):,}</small></a>'
                        for k, n in self.fields.items())
        tries = "".join(f'<a class="chip" href="/browse/?q={quote(t)}">{E(t)}</a>' for t in ("drone", "solar charger", "robot arm", "kitchen", "bicycle", "hearing aid"))
        span = {n: b - a for n, a, b in m.get("archiveSpans", [])}
        sources = [(m["count"] + span.get("US", 0), "United States", "USPTO", "US"), (span.get("Europe", 0), "Europe", "European Patent Office", "Europe"),
                   (span.get("Canada", 0), "Canada", "CIPO", "Canada"), (span.get("Australia", 0), "Australia", "IP Australia", "Australia")]
        statband = (f'<a href="/all/"><b class="num" data-count="{WORLD["n"]}">{WORLD["n"]:,}</b><span>All patents worldwide · 100+ offices</span></a>' if WORLD else "") + "".join(
            f'<a href="/browse/?in=archive&amp;region={quote(r)}"><b class="num" data-count="{c}">{c:,}</b><span>{E(place)} · free to use</span></a>'
            for c, place, office, r in sources if c)
        body = f"""
<section class="hero">
  <div>
    <div class="kicker rise" style="--d:0">The search engine for free-to-use patents</div>
    <h1 class="rise" style="--d:1">Build on inventions <em>nobody owns</em> anymore.</h1>
    <p class="lede rise" style="--d:2">{f'Search {big_number(WORLD["n"])} patents worldwide, and find the {big_number(total)} you can use for free, from the US, Europe, Canada and Australia.' if WORLD else f'{big_number(total)} patents from the US, Europe, Canada and Australia whose protection has ended, each traced to its official record.'} Find one, then turn it into your own invention with Claude.</p>
    <form class="bigsearch rise" style="--d:3" action="/browse/" role="search">{icon("search")}<label class="sr" for="heroQ">Search patents</label><input id="heroQ" name="q" type="search" autocomplete="off" placeholder="Search by idea, title, owner or patent number"><button class="btn primary" type="submit">Search</button></form>
    <div class="tryrow rise" style="--d:4"><span>Try</span>{tries}<button class="chip" type="button" data-surprise>{icon("shuffle")}Surprise me</button></div>
    {f'<p class="allline rise" style="--d:5">Searching for ideas you can use? The box above searches the free-to-use register. Checking what already exists? <a href="/all/">Search all {big_number(WORLD["n"])} patents worldwide</a>, including ones still in force.</p>' if WORLD else ""}
  </div>
  <figure class="plotter rise" style="--d:2">
    <div class="phead"><span>{E(hero["n"])}</span><span>Original drawing, plotted live</span></div>
    <div class="plotbox" id="plotbox" data-src="{self.img(hero["id"])}"><img src="{self.img(hero["id"])}" alt="Drawing from {E(hero["n"])}"><canvas id="plot" aria-hidden="true"></canvas><canvas id="pen" aria-hidden="true"></canvas></div>
    <figcaption><div><b>{E(hero["t"])}</b><small>{E(self.fields[hero["ind"]])} · {E(" ".join(freed_line(hero)))}</small></div><a class="btn secondary sm" href="{purl(hero["id"])}">Open patent</a></figcaption>
  </figure>
</section>
<nav class="statband{" five" if WORLD else ""}" aria-label="Patents by collection and office">{statband}</nav>
{self.ticker()}
<section class="section" id="recentSec" hidden><div class="sechead"><div><h2>Recently viewed</h2><p>Pick up where you left off. Kept in this browser only.</p></div><button class="btn quiet" type="button" id="recentClear">Clear</button></div><div class="rail" id="recentGrid"></div></section>
<section class="section reveal" id="today">
  <div class="sechead"><div><h2>Today's picks</h2><p>Twelve patents worth a look, refreshed every day. Each one is free to make, use and sell in the US.</p></div>
    <div class="railnav"><button class="iconbtn" type="button" data-rail="-1" aria-controls="todayRail" aria-label="Scroll back">{icon("left")}</button><button class="iconbtn" type="button" data-rail="1" aria-controls="todayRail" aria-label="Scroll forward">{icon("right")}</button></div></div>
  <div class="rail" id="todayRail">{"".join(self.card(r, i) for i, r in enumerate(picks))}</div>
</section>
<section class="section reveal">
  <div class="sechead"><div><h2>Explore by field</h2><p>Every patent is filed under the field of its main classification.</p></div><a class="btn quiet" href="/fields/">All fields</a></div>
  <div class="fchips">{chips}</div>
</section>
<section class="section reveal">
  <div class="sechead"><div><h2>How it works</h2></div><a class="btn quiet" href="/how-it-works/">The details</a></div>
  <div class="steps3">
    <div><span class="n">1</span><h3>Find</h3><p>Search millions of patents whose protection has ended. Each one links to the official USPTO record it came from.</p></div>
    <div><span class="n">2</span><h3>Reinvent with Claude</h3><p>One click writes a prompt and a PDF brief for your own Claude: modern directions, a novelty screen and a provisional draft.</p></div>
    <div><span class="n">3</span><h3>Reserve and build</h3><p>Reserve a patent for 30 days so other builders know you're on it, then build and file your own improvement. Reserving doesn't stop anyone else from using it.</p></div>
  </div>
</section>
<section class="section reveal">
  <div class="ctaband"><div><h2>Have your own idea?</h2><p>The invention studio turns it into a prompt and brief for Claude, with a novelty screen and a provisional patent draft. Free.</p></div><div class="rowbtns"><a class="btn primary lg" href="/studio/">Open the studio</a><a class="btn secondary lg" href="/how-it-works/">How it works</a></div></div>
</section>"""
        ld = [{"@context": "https://schema.org", "@type": "WebSite", "name": "Patent Yard", "url": SITE + "/",
               "potentialAction": {"@type": "SearchAction", "target": SITE + "/browse/?q={search_term_string}", "query-input": "required name=search_term_string"}},
              {"@context": "https://schema.org", "@type": "Organization", "name": "Patent Yard", "url": SITE + "/", "logo": SITE + "/favicon.svg"}]
        self.page("/", "Patent Yard", f"Search {big_number(total)} patents from the US, Europe, Canada and Australia whose protection has ended, each traced to its official record, with tools to reinvent them with Claude.",
                  body, og_image=self.img(hero["id"]), jsonld=ld, scripts=("home",))

    def ticker(self):
        newest = sorted(self.rows, key=lambda r: (r["added"], r["freed"], r["entry"]["id"]), reverse=True)[:400]
        newest = sorted((r for r in newest if coolness(r) > 0), key=coolness, reverse=True)[:24]  # the most interesting of the newest
        items = "".join(f'<a href="{purl(r["entry"]["id"])}"><span class="badge {r["entry"]["st"]}"></span>{E(r["entry"]["t"][:70])}<small>{E(self.fields.get(r["entry"]["ind"], ""))}</small></a>' for r in newest)
        return (f'<div class="ticker" aria-label="Newly added patents"><span class="tlabel"><span class="pulse" aria-hidden="true"></span>Just added</span>'
                f'<div class="tmask"><div class="ttrack">{items}<span aria-hidden="true" class="tdup">{items}</span></div></div></div>')

    def field_thumb(self, k):
        r = next((r for r in self.doc_by_field.get(k, []) if r["entry"]["fig"] and coolness(r) > 0), None)
        return f'<img src="{self.img(r["entry"]["id"])}" alt="" loading="lazy">' if r else icon("sheet")

    def filters(self, field=None):
        fields = "".join(f'<button class="chip" type="button" data-ind="{k}" aria-pressed="false">{E(n)}</button>' for k, n in self.fields.items())
        return f"""
<form class="filters" id="filters" role="search">
  {'' if field else f'<div class="frow colrow"><span class="lab">Collection</span><button class="chip" type="button" data-coll="" aria-pressed="true">Recently freed, US <small class="num">{self.meta["count"]:,}</small></button><button class="chip" type="button" data-coll="archive" aria-pressed="false">Archive, 4 offices <small class="num">{self.meta.get("archive", 0):,}</small></button></div>'}
  <div class="frow qrow"><label class="sr" for="q">Search</label><input class="field" id="q" name="q" type="search" placeholder="Search names, titles, owners or patent numbers" autocomplete="off"><button class="chip ftoggle" type="button" id="fToggle" aria-expanded="false" aria-controls="filters">Filters</button></div>
  {'' if field or len(self.meta.get("archiveSpans", [])) < 2 else '<div class="frow regrow"><span class="lab">From</span><button class="chip" type="button" data-reg="" aria-pressed="true">All</button>' + "".join(f'<button class="chip" type="button" data-reg="{n}" aria-pressed="false">{n} <small class="num">{b - a:,}</small></button>' for n, a, b in self.meta["archiveSpans"]) + '</div>'}
  {'' if field else f'<div class="frow scrollrow" id="fInd"><span class="lab">Field</span><button class="chip" type="button" data-ind="" aria-pressed="true">All</button>{fields}</div>'}
  <div class="frow"><span class="lab">Status</span>
    <button class="chip" type="button" data-st="" aria-pressed="true">All</button>
    <button class="chip" type="button" data-st="lapsed" aria-pressed="false">Lapsed</button>
    <button class="chip" type="button" data-st="expired" aria-pressed="false">Expired, full term</button>
    <button class="chip" type="button" data-st="abandoned" aria-pressed="false">Likely abandoned</button></div>
  <div class="frow"><span class="lab">Build</span>
    <button class="chip" type="button" data-b="" aria-pressed="true">Any</button>
    <button class="chip" type="button" data-b="2" aria-pressed="false">Weekend or garage</button>
    <button class="chip" type="button" data-b="3" aria-pressed="false">Up to workshop</button></div>
  <div class="frow"><span class="lab">Options</span>
    <button class="chip" type="button" id="fFig" aria-pressed="false">With drawings</button>
    <button class="chip" type="button" id="fSolo" aria-pressed="false">Solo inventors</button>
    <button class="chip" type="button" id="fFree" aria-pressed="false">Hide reserved</button>
    <label class="sr" for="sort">Sort</label>
    <select class="field" id="sort" style="width:auto">
      <option value="relevance">Best match</option>
      <option value="build">Recommended</option>
      <option value="recent">Most recently freed</option>
      <option value="added">Newly added</option>
      <option value="old">Oldest filing first</option>
    </select></div>
</form>
<div class="count" id="count" aria-live="polite"></div><div class="archhint" id="archHint" hidden></div>"""

    def listing(self, rows):
        """The first page of a list as plain HTML, for visitors without JavaScript and for search engines.
        browse.js replaces it with the live catalog."""
        return (f'<h2 class="sr">Patents</h2><div class="grid" id="grid">{"".join(self.card(r, i) for i, r in enumerate(rows[:48]))}</div>'
                '<div class="empty" id="empty" hidden><b>Nothing matches.</b><p>Loosen a filter or try a different word.</p></div>'
                '<div class="more"><button class="btn secondary" id="more" hidden>Show more</button></div>')

    def browse(self):
        n = len(self.rows)
        body = f"""<div class="page">
<div class="sechead"><div><h1>Browse the register</h1><p>{n:,} US patents whose protection has ended. Every one passed the same checks: officially lapsed, past its full term, or long abandoned, with no live relative in its US family. Each is rechecked daily.</p></div></div>
{self.filters()}
{self.listing(self.rows)}
</div>"""
        self.page("/browse/", "Browse free-to-use patents", f"Search and filter {n:,} US patents whose protection has ended, by field, status and how hard they are to build.",
                  body, section="/browse/", scripts=("browse",))

    def fields_index(self):
        tiles = "".join(
            f'<a class="tile" href="/fields/{k}/"><span class="th">{self.field_thumb(k)}</span><span><b>{E(n)}</b><small>{E(FIELD_NOTES.get(k, ""))} {len(self.by_field[k]) + self.meta.get("archiveByField", {}).get(k, 0):,} patents.</small></span></a>'
            for k, n in self.fields.items())
        body = f"""<div class="page"><div class="sechead"><div><h1>Fields</h1><p>Patents are filed under the field their classification points to. Pick one to see everything in it.</p></div></div><div class="tiles">{tiles}</div></div>"""
        self.page("/fields/", "Fields", "Free-to-use patents from the US, Europe, Canada and Australia, grouped by field, from software and AI to tools, energy and sports.", body, section="/fields/")
        for k, n in self.fields.items():
            rows = self.doc_by_field[k]
            counts = {s: sum(1 for r in rows if r["entry"]["st"] == s) for s in STATUS}
            arch = self.meta.get("archiveByField", {}).get(k, 0)
            parts = [f"{counts['lapsed']:,} lapsed", f"{counts['expired']:,} expired at full term", f"{counts['abandoned']:,} likely abandoned"]
            body = f"""<div class="page" data-field="{k}">
<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a><span>/</span><a href="/fields/">Fields</a><span>/</span><span>{E(n)}</span></nav>
<div class="sechead"><div><h1>{E(n)}</h1><p>{E(FIELD_NOTES.get(k, ""))} {len(rows) + arch:,} patents: {len(rows):,} freed in the past year ({", ".join(p for p in parts if not p.startswith("0 "))}){f", and {arch:,} more in the archive, from the US, Europe, Canada and Australia" if arch else ""}.</p></div><div class="rowbtns"><a class="btn secondary" href="/browse/?field={k}">Open in browse</a>{f'<a class="btn quiet" href="/browse/?in=archive">Search the archive</a>' if arch else ""}</div></div>
{self.filters(field=k)}
{self.listing(rows)}
</div>"""
            self.page(f"/fields/{k}/", f"{n} patents", f"{len(rows) + arch:,} free-to-use patents in {n.lower()}: {FIELD_NOTES.get(k, '')}",
                      body, section="/fields/", scripts=("browse",))

    def patent(self, r, detail, doc):
        """One patent's page, returned as HTML (it is packed into a shard, not written as its own file).
        Nothing on it depends on today's date, so its shard only changes when the patent's record does."""
        e, dd = r["entry"], detail
        pid, L = e["id"], links(e, dd)
        field = self.fields.get(e["ind"], e["ind"])
        sheets = ([r["fig"]] if r["fig"] else []) + r["extra"]
        checks, warn = why_free(e)
        owner = (f' · {"Applicant" if e["st"] == "abandoned" else "Assignee"}: {E(dd["asg"])}' if dd.get("asg") else "") + (f" · Inventors: {E(dd['inv'])}" if dd.get("inv") else "")
        claims = [c if isinstance(c, list) else [i + 1, c] for i, c in enumerate(doc["claims"])] or ([[1, dd["c1"]]] if dd["c1"] else [])
        ind_n = sum(1 for _, c in claims if not DEPENDENT.search(c))
        later = (f'being downloaded from USPTO and will appear here within days. Until then, read it in the <a href="{L["pdf"]}" {EXT}>USPTO PDF</a> '
                 f'or on <a href="{L["google"]}" {EXT}>Google Patents</a>.')
        status_line = {"lapsed": ("Expired (fee)", full_date(e["x"])), "expired": ("Term ended", full_date(e.get("te"))),
                       "abandoned": ("Status", "Abandoned (inferred)")}[e["st"]]
        kind = "application" if e["st"] == "abandoned" else "patent"

        # overview
        if sheets:
            w, h = png_size(sheets[0])
            fig = (f'<div class="figstick"><button class="bigfig" type="button" data-sheet="0" aria-label="Enlarge drawing sheet 1"><img src="{self.img(pid)}" width="{w}" height="{h}" alt="Drawing sheet 1 of {E(e["n"])}"></button>'
                   f'<p class="cap">Sheet 1 of {e["sh"] or len(sheets)} from the published document. <a href="{L["pdf"]}" {EXT}>All sheets in the USPTO PDF</a></p></div>')
        elif e["sh"]:
            fig = (f'<div class="nofig later"><b><span class="pulse" aria-hidden="true"></span>Drawings on their way</b><p class="muted">This {kind} has {e["sh"]} drawing '
                   f'{"sheet" if e["sh"] == 1 else "sheets"}. They are being downloaded; every one is in the USPTO PDF now.</p><a class="btn secondary sm" href="{L["pdf"]}" {EXT}>{icon("file")}Open the USPTO PDF</a></div>')
        else:
            fig = ('<div class="nofig"><b>This document has no drawings.</b></div>' if e.get("arm") else
                   f'<div class="nofig"><b>This document has no drawings.</b><p class="muted">Claude can sketch it from the patent text.</p><button class="btn secondary sm" type="button" data-kit="sketch">{icon("spark")}Sketch it with Claude</button></div>')
        cpc = dd.get("cpc", [])
        cpc_html = (E(cpc[0]) + (f' <span class="muted" title="{E(", ".join(cpc))}">+{len(cpc) - 1} more</span>' if len(cpc) > 1 else "")) if cpc else "—"
        abstract = (f'<div class="block"><h3>Abstract <span class="src">Excerpt, from Google Patents</span></h3><p class="prose">{E(dd["abs"])}</p><p class="muted" style="margin-top:8px;font-size:13.5px">The full abstract, claims and description are {later}</p></div>' if dd.get("abx") else
                    f'<div class="block"><h3>Abstract <span class="src">From the {kind}</span></h3><p class="prose">{E(dd["abs"])}</p></div>' if dd["abs"] else
                    f'<div class="panel soft pendingbox"><div class="block"><h3><span class="pulse" aria-hidden="true"></span>Full text on its way</h3><p class="prose">This {kind} is listed from its USPTO record because it passed every check. Its abstract, claims and description are {later}</p></div></div>')
        plain = "" if e["auto"] else f'<div class="block"><h3>In plain English <span class="src">Patent Yard summary</span></h3><p class="lead">{E(e["h"])}</p></div>'
        overview = f"""
<section class="psec" id="overview"><h2>Overview</h2>
<div class="ov"><div>{fig}</div>
<div class="stack">
  {KIT_OFF if e.get("arm") else ""}
  {plain or abstract}
  <div class="panel soft"><div class="block"><h3>Why it's free to use</h3><ul class="checks">{"".join(f"<li>{E(c)}</li>" for c in checks)}<li class="warn">{E(warn)}</li></ul></div></div>
  {f'<div class="angle"><b>Modern angle · Patent Yard idea</b>{E(e["tw"])}</div>' if e["tw"] else ""}
  <div class="facts">
    <div><small>Filed</small><b>{E(full_date(e["f"]))}</b></div>
    <div><small>{"Published" if e["st"] == "abandoned" else "Granted"}</small><b>{E(full_date(e["p"]))}</b></div>
    <div><small>{status_line[0]}</small><b>{E(status_line[1])}</b></div>
    <div><small>Application number</small><b>{E(dd.get("app") or "—")}</b></div>
    <div><small>Classification (CPC)</small><b>{cpc_html}</b></div>
    <div><small>Length</small><b>{f'{len(claims)} {"claim" if len(claims) == 1 else "claims"}' if claims else ""}{" · " if claims and dd.get("pages") else ""}{f'{dd["pages"]} pages' if dd.get("pages") else ""}{"—" if not claims and not dd.get("pages") else ""}</b></div>
  </div>
  {abstract if plain else ""}
  {f'<div class="block"><h3>Background <span class="src">From the {kind}</span></h3><p class="prose">{E(dd["bg"])}</p></div>' if dd.get("bg") else ""}
</div></div></section>"""

        # drawings
        figs = figure_lines(dd.get("figs") or [])
        if sheets or e["sh"]:
            total = max(e["sh"] or 0, len(sheets))
            gal = "".join(
                f'<figure><button type="button" data-sheet="{i}" aria-label="Enlarge sheet {i + 1}"><img src="{self.img(pid, i + 1)}" alt="Drawing sheet {i + 1} of {E(e["n"])}" loading="lazy" width="{png_size(s)[0]}" height="{png_size(s)[1]}"></button>'
                f'<figcaption><span>Sheet {i + 1} of {total}</span></figcaption></figure>'
                for i, s in enumerate(sheets))
            # sheets not downloaded yet still get their place, linked to the PDF that has them
            gal += "".join(
                f'<figure class="later"><a href="{L["pdf"]}" {EXT}><span class="pulse" aria-hidden="true"></span><b>Sheet {k}</b><span>Coming soon. Open it in the USPTO PDF</span></a>'
                f'<figcaption><span>Sheet {k} of {total}</span></figcaption></figure>'
                for k in range(len(sheets) + 1, min(total, MAX_SHEETS) + 1))
            if total > MAX_SHEETS:
                gal += (f'<figure class="later rest"><a href="{L["pdf"]}" {EXT}><b>+{total - MAX_SHEETS} more</b><span>Every sheet is in the USPTO PDF</span></a>'
                        f'<figcaption><span>Sheets {MAX_SHEETS + 1} to {total}</span></figcaption></figure>')
            more = f' <a href="{L["pdf"]}" {EXT}>Every sheet is in the USPTO PDF.</a>' if total > len(sheets) else ""
            lead = (f'All {total} drawing {"sheet" if total == 1 else "sheets"}' if len(sheets) >= total
                    else f'{len(sheets)} of {total} drawing sheets so far' if sheets else f'The {total} drawing {"sheet is" if total == 1 else "sheets are"} on the way')
            figlist = f'<div class="panel figside"><div class="block"><h3>Figures as described</h3><ul class="figlist">{"".join(f"<li>{E(x)}</li>" for x in figs)}</ul></div></div>' if figs else ""
            drawings = f"""<section class="psec" id="drawings"><h2>Drawings <small>{e["sh"] or len(sheets)}</small></h2>
<p class="muted sublead">{f"{lead} from the published document, cropped to the drawing.{more}" if sheets else f"{lead}.{more}"}</p>
<div class="drawwrap{" withlist" if figs else ""}"><div class="gallery">{gal}</div>{figlist}</div>
</section>"""
        else:
            sketch = "" if e.get("arm") else f'<p class="muted">Ask Claude for concept sketches based only on the patent\'s text. They are not part of the patent.</p><button class="btn primary sm" type="button" data-kit="sketch">{icon("spark")}Sketch it with Claude</button>'
            drawings = f"""<section class="psec" id="drawings"><h2>Drawings</h2><div class="nofig"><b>This document has no drawings.</b>{sketch}</div></section>"""

        # claims: one readable column, dependents indented under the claim they build on, and a map beside it
        gap = claims[0][0] - 1 if claims else 0
        gap_note = f'<p class="muted sublead">{"Claim 1 was" if gap == 1 else f"Claims 1 to {gap} were"} canceled before publication.</p>' if gap > 0 else ""
        claims_sec = f"""<section class="psec" id="claims"><h2>Claims <small>{len(claims)} total, {ind_n} independent</small></h2>
{gap_note}<p class="muted sublead">What the {kind} claimed, word for word. All of it is now free to use.</p>
<div class="withaside">{claim_list(claims)}{claim_map(claims)}</div></section>""" if claims else f"""<section class="psec" id="claims"><h2>Claims</h2>
<div class="panel soft pendingbox"><div class="block"><h3><span class="pulse" aria-hidden="true"></span>On their way</h3><p class="prose">The claims are {later}</p></div></div></section>"""

        # description
        paras = doc["desc"]
        if paras:
            heads, parts = [], []
            for t in paras:
                if P.is_heading(t):
                    label = t.lower()[:1].upper() + t.lower()[1:] if not t[:1].isdigit() else re.sub(r"[a-z]", lambda m: m.group(0).upper(), t.lower(), count=1)
                    heads.append((f"d{len(heads) + 1}", label))
                    parts.append(f'<h3 id="d{len(heads)}">{E(label)}</h3>')
                else:
                    parts.append(f"<p>{E(t)}</p>")
            words = sum(len(t.split()) for t in paras)
            long_ = sum(len(t) for t in paras) > 6000
            jump = "".join(f'<a href="#{a}">{E(lbl)}</a>' for a, lbl in heads[:14])
            aside = (f'<div class="sidecard"><div class="panel"><div class="block"><h3>In this description</h3>'
                     + (f'<nav class="jump" aria-label="Description sections">{jump}</nav>' if jump else "")
                     + f'<p class="muted" style="font-size:13px;margin-top:10px">About {words:,} words. The <a href="{L["pdf"]}" {EXT}>USPTO PDF</a> has it with every drawing.</p></div></div></div>')
            desc = f"""<section class="psec" id="description"><h2>Description</h2>
<div class="withaside"><div><div class="desc{" clamped" if long_ else ""}" id="desc">{"".join(parts)}{f'<p class="muted">The description continues in the <a href="{L["pdf"]}" {EXT}>full USPTO document</a>.</p>' if doc.get("more") else ""}</div>
{'<div class="rowbtns noprint" style="margin-top:14px"><button class="btn secondary" type="button" id="descMore" aria-controls="desc" aria-expanded="false">Read the full description</button></div>' if long_ else ""}</div>{aside}</div></section>"""
        else:
            desc = (f'<section class="psec" id="description"><h2>Description</h2><div class="panel soft pendingbox"><div class="block"><h3><span class="pulse" aria-hidden="true"></span>On its way</h3><p class="prose">The description is {later}</p></div></div></section>' if e["pending"] else
                    f'<section class="psec" id="description"><h2>Description</h2><p class="prose">The full description is in the <a href="{L["pdf"]}" {EXT}>USPTO document</a>.</p></section>')

        # timeline & family
        fees = fee_schedule(e)
        fee_html = ""
        if fees:
            fee_html = (f'<div class="panel"><div class="block"><h3>Maintenance fees</h3><p class="muted" style="font-size:14px;margin-bottom:12px">Fees are due 3.5, 7.5 and 11.5 years after grant. This patent expired on {E(full_date(e["x"]))}, so the fee marked "not paid" was the one that went unpaid.</p><div class="fees">'
                        + "".join(f'<div class="fee"><b>{y}-year fee</b><small>Due {E(full_date(due))}</small><span class="badge {"ok" if st == "paid" else "lapsed" if st == "missed" else "plain"}">{"Paid" if st == "paid" else "Not paid" if st == "missed" else "Never came due"}</span></div>' for y, due, st in fees)
                        + "</div></div></div>")
        me = {"n": e["n"], "id": pid, "t": e["ot"], "f": e["f"], "p": e["p"], "k": kind, "s": STATUS[e["st"]], "me": True}
        fam = sorted(doc["family"] + [me], key=lambda m: (m.get("f") or "") + (m.get("p") or ""))
        def node(m):
            kind_ = "This document" if m.get("me") else "Patent" if m.get("k") == "patent" else "Published application"
            when = (" · " + ("granted" if m.get("k") == "patent" else "published") + " " + E(short_date(m.get("p")))) if m.get("p") else ""
            cls = e["st"] if m.get("me") else "plain"
            ext = "" if m.get("me") else f'<div style="margin-top:8px"><a href="{gp(m["id"])}" {EXT}>View on Google Patents</a></div>'
            return (f'<div class="famnode{" me" if m.get("me") else ""}" role="listitem"><small>{kind_}</small><b>{E(m["n"])}</b><p>{E(m["t"])}</p>'
                    f'<small>Filed {E(short_date(m.get("f")))}{when}</small><div style="margin-top:8px"><span class="badge {cls}">{E(m["s"])}</span></div>{ext}</div>')
        lane = "".join(node(m) for m in fam)
        cites = doc.get("cites") or []
        cite_html = ('<div class="cites">' + "".join(f'<a class="chip" href="{h}" {EXT}>{E(lbl)}</a>' for lbl, h in map(cite_ref, cites)) + '</div><p class="muted" style="margin-top:10px;font-size:13px">Prior art cited by the examiner or applicant. Useful when you check your own idea for novelty.</p>') if cites else '<p class="muted">No US citations on record.</p>'
        history = f"""<section class="psec" id="history"><h2>Timeline &amp; family</h2><div class="stack">
<div class="panel"><div class="block"><h3>Timeline <span class="src">From USPTO dates</span></h3><div class="chartbox">{timeline_svg(timeline_events(e, doc))}</div></div></div>
{fee_html}
<div class="panel"><div class="block"><h3>US family <span class="src">{len(fam)} {"documents" if len(fam) > 1 else "document"}, by filing date</span></h3><div class="famlane" role="list">{lane}</div><p class="muted" style="margin-top:10px;font-size:13px">Earlier publications, parents and continuations. None of them can still be enforced, or this {kind} would not be listed.</p></div></div>
<div class="panel"><div class="block"><h3>US patents it cites <span class="src">{len(cites)}</span></h3>{cite_html}</div></div>
</div></section>"""

        # sources
        if e["st"] == "lapsed":
            origin = [(e.get("og", {}).get("u") or "https://www.uspto.gov/learning-and-resources/official-gazette/official-gazette-patents", "USPTO Official Gazette",
                       "Notice of Expiration of Patents Due to Failure to Pay Maintenance Fee" + (", issue of " + full_date(e["og"]["d"]) if e.get("og") else "") + ".", "Where this listing came from"),
                      (L["fees"], "Maintenance fee record", "Enter the patent number to see its fee history.", "USPTO Fees")]
        else:
            origin = [(L["ppubs"], "USPTO Patent Public Search", "The patent record, found by filing date (1996 to 2001) and classification." if e["st"] == "expired" else "The published application, found by filing date (2013 to 2017) and classification.", "Where this listing came from")]
        official = [(L["pdf"], "Full published document", "Text and every drawing sheet as a PDF.", "USPTO"), (L["center"], "File history", "Status, office actions, notices, fee records and petitions.", "USPTO Patent Center")]
        if e["st"] == "lapsed":
            official.append((L["ppubs"], "Patent Public Search record", "Searchable full text and bibliographic data.", "USPTO"))
        cross = [(L["google"], "Google Patents", "Worldwide family, citing patents and legal events.", "patents.google.com"), (L["justia"], "Justia Patents", "Full text, claims and classification.", "patents.justia.com"),
                 (L["fpo"], "FreePatentsOnline", "Full text and PDF.", "freepatentsonline.com"), (L["espacenet"], "Espacenet", "Foreign family and legal status.", "European Patent Office")]
        lc = lambda x, cls="": f'<a class="lcard {cls}" href="{x[0]}" {EXT}><b>{E(x[1])}{icon("ext")}</b><span>{E(x[2])}</span><small>{E(x[3])}</small></a>'
        confirm = {"lapsed": 'The status should read "Patent Expired Due to NonPayment of Maintenance Fees Under 37 CFR 1.362".',
                   "expired": f'Its 20-year term from filing ended {E(full_date(e.get("te")))}. Check the "Patent Term Adjustment" and "Patent Term Extension" entries, which add days to that date.',
                   "abandoned": 'The status should read "Abandoned", usually with a notice of abandonment in the documents.'}[e["st"]]
        sources = f"""<section class="psec" id="sources"><h2>Sources &amp; verification</h2><div class="stack">
<div class="cols2"><div class="panel"><div class="block"><h3>Verification</h3><ul class="checks">{"".join(f"<li>{E(c)}</li>" for c in checks)}<li><span>Rechecked against USPTO records every day<span class="vdate"></span>.</span></li><li class="warn">{E(warn)}</li></ul></div></div>
<div class="panel"><div class="block"><h3>Confirm it yourself</h3><ol class="prose" style="padding-left:18px;margin:0;font-size:14.5px"><li>Open the <a href="{L["center"]}" {EXT}>file history on Patent Center</a>.</li><li>{confirm}</li><li>Check the documents for any later petition to revive or reinstate.</li></ol></div></div></div>
<div class="cols2 links2"><div class="block"><h3>Official USPTO records</h3><div class="linklist">{"".join(lc(x, "src" if i == 0 else "") for i, x in enumerate(origin + official))}</div></div>
<div class="block"><h3>Cross-check elsewhere</h3><div class="linklist">{"".join(lc(x) for x in cross)}</div></div></div>
<p class="muted" style="font-size:13px">{"Names, summaries, modern angles and build ratings are Patent Yard's editorial notes. Everything else" if not e["auto"] else "Everything"} on this page comes from the documents linked above.</p>
<div class="rowbtns noprint"><button class="btn secondary sm" type="button" id="reportBtn" hidden>Report a problem with this listing</button></div>
</div></section>"""

        related = self.neighbors(r)
        lst, pos = self.by_field[e["ind"]], self.field_pos[pid]
        prev_, next_ = (lst[pos - 1] if pos > 0 else None), (lst[pos + 1] if pos + 1 < len(lst) else None)
        step = lambda x, lbl, cls: (f'<a class="pstep {cls}" href="{purl(x["entry"]["id"])}" rel="{"prev" if cls == "prev" else "next"}"><small>{lbl}</small><b>{E(x["entry"]["t"])}</b></a>' if x else "<span></span>")
        pnav = f'<nav class="pnav noprint" aria-label="More patents in this field">{step(prev_, "← Previous in " + field, "prev")}{step(next_, "Next in " + field + " →", "next")}</nav>' 
        rel = f'<section class="section noprint"><div class="sechead"><div><h2>More in {E(field)}</h2></div><a class="btn quiet" href="/fields/{e["ind"]}/">All {E(field)}</a></div><div class="grid">{"".join(self.card(x, 9) for x in related)}</div></section>' if related else ""
        toc = [("overview", "Overview", ""), ("drawings", "Drawings", e["sh"] or len(sheets) or ""), ("claims", "Claims", len(claims) or ""), ("description", "Description", ""), ("history", "Timeline & family", ""), ("sources", "Sources & verification", "")]
        build_badge = f'<span class="badge plain">{meter(e["b"])}{BUILD[e["b"]]} build</span>' if e["b"] else ""
        asfiled = f"{E(e['n'])} · Title as filed: {E(e['ot'])}" if e["t"] != e["ot"] else E(e["n"])
        body = f"""<div class="page" id="patent" data-id="{pid}" data-n="{E(e["n"])}" data-sheets="{len(sheets)}" data-total="{e["sh"] or len(sheets)}" data-pdf="{L["pdf"]}">
<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a><span>/</span><a href="/fields/{e["ind"]}/">{E(field)}</a><span>/</span><span>{E(e["n"])}</span></nav>
<div class="phead">
  <div><div class="badges">{badge(e["st"])}{build_badge}{'<span class="badge plain">Solo inventor</span>' if e["ia"] else ""}<span class="badge ok" id="vbadge" hidden></span></div>
  <h1>{E(e["t"])}</h1><p class="asfiled">{asfiled}{owner}</p></div>
  <div class="pactions">
    {"" if e.get("arm") else f'<button class="btn primary" type="button" data-kit="workshop">{icon("spark")}Reinvent with Claude</button>'}
    <button class="btn secondary" type="button" id="reserveBtn">{icon("flag")}Reserve</button>
    <a class="btn secondary" href="{L["pdf"]}" {EXT}>{icon("file")}USPTO PDF</a>
    <button class="btn quiet" type="button" id="saveBtn" aria-pressed="false">{icon("bookmark")}<span>Save</span></button>
    <button class="btn quiet" type="button" id="copyLink">{icon("link")}Copy link</button>
    <div class="resline" id="resline" aria-live="polite"></div>
  </div>
</div>
<div class="playout">
  <nav class="toc" aria-label="On this page">{"".join(f'<a href="#{a}">{t}{f"<small>{n}</small>" if n else ""}</a>' for a, t, n in toc)}</nav>
  <div>{overview}{drawings}{claims_sec}{desc}{history}{sources}{pnav}</div>
</div>
{rel}
</div>
<dialog id="viewer" aria-label="Drawing viewer"></dialog>
<dialog id="kit" aria-labelledby="kitTitle"></dialog>
<dialog id="resDlg" aria-labelledby="resTitle"></dialog>
<dialog id="repDlg" aria-labelledby="repTitle"></dialog>"""
        ld = [{"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
                  {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                  {"@type": "ListItem", "position": 2, "name": field, "item": f"{SITE}/fields/{e['ind']}/"},
                  {"@type": "ListItem", "position": 3, "name": e["n"], "item": SITE + purl(pid)}]},
              {"@context": "https://schema.org", "@type": "CreativeWork", "name": e["ot"], "alternateName": e["t"], "identifier": e["n"],
               "dateCreated": e["f"], "datePublished": e["p"], "abstract": dd["abs"][:500], "url": SITE + purl(pid),
               "image": SITE + self.img(pid) if sheets else None, "isBasedOn": L["pdf"]}]
        desc_meta = f'{e["n"]}, {STATUS[e["st"]].lower()}: {e["h"] or e["ot"]}'
        return self.page(purl(pid), f'{e["t"]} ({e["n"]})', desc_meta, body, og_image=self.img(pid) if sheets else None, jsonld=ld,
                         scripts=("patent",), lastmod=e["v"] or r["added"] or None, write=False)

    def neighbors(self, r, k=4):
        """Related patents: the nearest patent numbers in the same field, so the list only changes when one is added nearby."""
        lst = self.by_field[r["entry"]["ind"]]
        i = self.field_pos[r["entry"]["id"]]
        near = lst[max(0, i - k // 2):i] + lst[i + 1:i + 1 + k]
        return near[:k]

    def all_patents(self):
        n = WORLD["n"]
        body = f"""<div class="page">
<div class="sechead"><div><div class="kicker">All patents</div><h1>Search {big_number(n)} patents worldwide</h1>
<p class="lede">Every patent and published application in Google's public patent data, from more than 100 patent offices: check what already exists before you build, buy or file. Patents that may still be in force are marked; for inventions you can use freely, see <a href="/browse/">Free to use</a>.</p></div></div>
<form class="filters" id="wfilters" role="search">
  <div class="frow qrow"><label class="sr" for="wq">Search all patents</label><input class="field" id="wq" type="search" placeholder="Search titles and owners, or enter a number like CN112345678A" autocomplete="off"></div>
  <div class="frow"><span class="lab">Country</span><label class="sr" for="wcc">Country</label><select class="field" id="wcc" style="width:auto"><option value="">All countries</option></select>
    <button class="chip" type="button" id="wfree" aria-pressed="false">Past their term only</button></div>
</form>
<p class="muted" id="wcount" aria-live="polite">Loading…</p>
<div class="grid" id="wgrid"></div>
<div class="rowbtns" style="justify-content:center;margin-top:18px"><button class="btn secondary" type="button" id="wmore" hidden>Show more</button></div>
<p class="muted fine-print">Records come from Google Patents Public Data, used under CC BY 4.0, and are refreshed from time to time. "Past its term" means filed long enough ago that no patent from it can still be in force; every other status is as published, so confirm it with the official register before relying on it.</p>
</div>"""
        self.page("/all/", "All patents", f"Search {big_number(n)} patents and applications from more than 100 patent offices, with the ones past their term marked.",
                  body, section="/all/", scripts=("all",))

    def opportunities(self):
        # ties: the broader first claim, then more claims
        scored = sorted(((p, r) for r in self.rows if (p := potential(r)) is not None),
                        key=lambda t: (-t[0], t[1]["entry"].get("w1") or 999, -(t[1]["entry"].get("cl") or 0), t[1]["entry"]["id"]))
        by_id = {r["entry"]["id"]: r for _, r in scored}
        picks = [(by_id[k], v) for k, v in ANALYSIS.items() if k in by_id]
        top = [r for _, r in scored if r["entry"]["id"] not in ANALYSIS][:96]
        chips = lambda e: "".join(f'<span class="chip sm">{E(x)}</span>' for x in signals(e))
        pick_html = "".join(f"""<article class="oppick reveal" data-of="{r["entry"]["ind"]}">
  <a class="ofig" href="{purl(r["entry"]["id"])}">{f'<img src="{self.img(r["entry"]["id"])}" alt="Drawing from {E(r["entry"]["n"])}" loading="lazy">' if r["fig"] else ""}<span class="rank">{i}</span></a>
  <div class="otext"><span class="fieldname">{E(self.fields.get(r["entry"]["ind"], r["entry"]["ind"]))} · <span class="num-id">{E(r["entry"]["n"])}</span></span>
    <h3><a href="{purl(r["entry"]["id"])}">{E(r["entry"]["t"])}</a></h3>
    <dl><div><dt>Now free to use</dt><dd>{E(a["open"])}</dd></div><div><dt>Who would buy it</dt><dd>{E(a["buyers"])}</dd></div>
    <div><dt>Why now</dt><dd>{E(a["now"])}</dd></div><div><dt>Check first</dt><dd>{E(a["watch"])}</dd></div></dl>
    <div class="chips">{chips(r["entry"])}</div>
    <div class="rowbtns"><a class="btn primary sm" href="{purl(r["entry"]["id"])}">Open patent</a><a class="btn secondary sm" href="/studio/?patent={quote(r["entry"]["id"])}">{icon("spark")}Reinvent with Claude</a></div></div>
</article>""" for i, (r, a) in enumerate(picks, 1))
        top_html = "".join(f'<div class="opp" data-of="{r["entry"]["ind"]}"><span class="rank">{i}</span>{self.card(r, i)}<div class="chips">{chips(r["entry"])}</div></div>'
                           for i, r in enumerate(top, len(picks) + 1))
        fields = sorted({r["entry"]["ind"] for r, _ in picks} | {r["entry"]["ind"] for r in top}, key=lambda k: list(self.fields).index(k) if k in self.fields else 99)
        filt = '<button class="chip" type="button" data-of="" aria-pressed="true">All</button>' + "".join(
            f'<button class="chip" type="button" data-of="{k}" aria-pressed="false">{E(self.fields.get(k, k))}</button>' for k in fields)
        body = f"""<div class="page">
<div class="sechead"><div><div class="kicker">Opportunities</div><h1>The biggest openings in the register</h1>
<p class="lede">Recently freed patents ranked by the signals that track commercial value: how long the owner kept paying to protect it, how broad its claims are, who owned it and the size of the market it sells into. The top {len(picks)} come with Claude's analysis of what is now free, who would buy it and why now.</p></div></div>
<ul class="omethod"><li><b>Kept up for years</b><span>An owner paying maintenance fees for 8 to 12 years thought it was worth protecting.</span></li><li><b>Broad claims</b><span>A short independent claim covered more ground, and all of it is free now.</span></li><li><b>Company-owned</b><span>A business filed and paid for it, usually for a product.</span></li><li><b>Large market</b><span>Its field sells into a big market: medical, energy, AI, robotics, vehicles.</span></li></ul>
<div class="frow ofilter" role="group" aria-label="Filter by field"><span class="lab">Field</span>{filt}</div>
<section class="section"><div class="sechead"><div><h2>Claude's analysis</h2><p>Read from each patent's abstract and claims. Market notes are general, with no figures we can't source.</p></div></div>
<div class="opicks">{pick_html}</div></section>
<section class="section"><div class="sechead"><div><h2>Next {len(top)} by score</h2><p>Ranked by the same signals. Open any one for its claims, drawings and the Claude kit.</p></div></div>
<div class="grid ogrid">{top_html}</div></section>
<p class="muted fine-print">Rankings are estimates from public patent records, not a valuation, investment advice or a promise of sales. A lapsed patent's own claims are free to use in the US, but newer patents, regulations and other rights can still apply. Check before you build, and see the <a href="/legal/disclaimer/">disclaimer</a>.</p>
</div>"""
        self.page("/opportunities/", "Opportunities", f"The {len(picks) + len(top)} recently freed patents with the most commercial potential, ranked by owner investment, claim breadth and market, with Claude's analysis of the top {len(picks)}.",
                  body, section="/opportunities/", scripts=("opps",))

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
                           f"Patents lapsed each week, past year: {min((w[1] for w in weeks), default=0):,} to {hi:,} a week")
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
        rein = sum(w[2] for w in weeks)
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
<div class="sechead"><div><h1>Insights</h1><p>{f"Patent Yard in numbers: all {big_number(WSTATS['n'])} patents worldwide by office, year, field and owner, then the free-to-use register: what lapses, when, and who used to own it." if WSTATS else "The register in numbers: what lapses, when, and who used to own it. Drawn from the same USPTO records as every patent page, updated with each refresh."}</p></div></div>
{self.world_insights()}
{'<section class="section"><div class="sechead"><div><h2>Free to use</h2><p>The register of patents whose protection has ended, drawn from the same office records as every patent page and updated with each refresh.</p></div></div>' if WSTATS else ""}
<div class="statband reveal">
  <div><b class="num" data-count="{n + len(recs)}">{n + len(recs):,}</b><span>patents listed: {n + kinds.get("", 0) + kinds.get("S", 0) + kinds.get("A", 0):,} US, {kinds.get("E", 0):,} European, {kinds.get("CA", 0):,} Canadian and {kinds.get("AU", 0):,} Australian</span></div>
  <div><b class="num" data-count="{m["lapsedYear"]}">{m["lapsedYear"]:,}</b><span>US patents lapsed in the past year</span></div>
  <div><b class="num" data-count="{rein}">{rein:,}</b><span>reinstated after a late payment, and left out</span></div>
  <div><b class="num" data-count="{round(solo / max(1, n + len(recs)) * 100)}">{solo / max(1, n + len(recs)) * 100:.0f}</b><span>percent from solo inventors, with no company named</span></div>
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
        self.page("/insights/", "Insights", (f"{big_number(WSTATS['n'])} patents worldwide by office, year, field and owner, " if WSTATS else "Patent Yard in numbers: ")
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
                           f"Patents and applications published each year, 1900 to {years[-1][0]}, peaking at {hi:,} in {peak}")
        return f"""<section class="section"><div class="sechead"><div><h2>All patents worldwide</h2><p>Every patent and published application in <a href="/all/">All patents</a>, from Google Patents Public Data.</p></div></div>
<div class="statband reveal">
  <div><b class="num" data-count="{w["n"]}">{w["n"]:,}</b><span>patents and applications</span></div>
  <div><b class="num" data-count="{len(w["countries"])}">{len(w["countries"])}</b><span>patent offices</span></div>
  <div><b class="num" data-count="{w["granted"]}">{w["granted"]:,}</b><span>granted patents; the rest are applications</span></div>
  <div><b class="num" data-count="{w["free"]}">{w["free"]:,}</b><span>past their term, so no patent from them can still be in force</span></div>
</div>
<div class="ins">
  <section class="panel reveal span2"><h2>Published each year</h2><p class="muted">Patents and applications by the year they were published, across every office, from 1900 to {years[-1][0]}.</p><div class="chartbox">{chart}</div></section>
  <section class="panel reveal"><h2>By office</h2><p class="muted">The 12 offices with the most records. The bright part of each bar is past its term.</p><div class="hbars">{office_bars}</div>
    <h2 style="margin-top:26px">Biggest owners</h2><p class="muted">The owners with the most records worldwide, every spelling of a name counted together.</p><ol class="owners">{owners}</ol></section>
  <section class="panel reveal"><h2>By field</h2><p class="muted">Records by the field of their main classification; {big_number(w["fields"].get("other", 0))} more have no classification or fall outside these fields.</p><div class="hbars">{field_bars}</div></section>
</div>
</section>"""

    def archive_template(self):
        """The page shell for archive patents. functions/_archive.js fills in %%TITLE%%, %%DESC%%, %%PATH%% and %%BODY%%."""
        doc = self.page("%%PATH%%", "%%TITLE%%", "%%DESC%%", "%%BODY%%", scripts=("patent",), write=False)
        out = DIST / "tpl" / "archive" / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(doc)

    def saved(self):
        body = f"""<div class="page">
<div class="sechead"><div><h1>Saved patents</h1><p>Patents you saved with the {icon("bookmark")} button. They're kept in this browser, so no account is needed.</p></div><a class="btn secondary" href="/browse/">Browse patents</a></div>
<div class="grid" id="savedGrid"></div>
<div class="empty" id="savedEmpty" hidden><b>Nothing saved yet</b><p>Tap Save on any patent, or the bookmark on a card, and it shows up here.</p></div>
</div>"""
        self.page("/saved/", "Saved patents", "Patents you saved on Patent Yard.", body, scripts=("saved",), index=False)

    def studio(self):
        body = f"""<div class="page">
<div class="sechead"><div><h1>Invention studio</h1><p>Turn a patent, or your own idea, into a ready-made prompt and a PDF brief for Claude. Claude then works with you on modern directions, a novelty screen, a provisional patent draft, sketches or a prototype plan. It runs on your own Claude account, free on Patent Yard.</p></div></div>
<div class="howto" style="margin-bottom:22px"><div><b>Describe it.</b> Start from a patent here or from your own idea.</div><div><b>Pick a task.</b> We write the prompt and a PDF brief with the patent's claims and drawings.</div><div><b>Open Claude.</b> Paste the prompt, attach the brief, and work through it together.</div></div>
<div class="studio">
  <div class="panel"><div class="stack" id="studioForm">
    <div class="fgroup picker"><label for="pq">Start from a patent (optional)</label><input class="field" id="pq" type="search" autocomplete="off" placeholder="Search by name or patent number"><ul id="pickList" role="listbox" hidden></ul><div id="picked"></div></div>
    <div class="fgroup"><label for="iName">Invention name</label><input class="field" id="iName" maxlength="120" placeholder="Self-leveling camp stove"></div>
    <div class="fgroup"><label for="iPitch">One-line pitch</label><input class="field" id="iPitch" maxlength="300" placeholder="What it does, for whom, in one sentence"></div>
    <div class="fgroup"><label for="iDesc">How it works</label><textarea class="field" id="iDesc" maxlength="8000" placeholder="Parts, how they connect, how someone uses it. Rough notes are fine."></textarea></div>
    <div class="fgroup"><label for="iNew">What's new</label><textarea class="field" id="iNew" maxlength="3000" style="min-height:80px" placeholder="The part nobody has done before."></textarea><small>Leave these blank to let Claude propose directions first.</small></div>
  </div></div>
  <div class="stack">
    <div class="block"><h2>Task</h2><div class="tasks" id="tasks"></div></div>
    <div class="fgroup"><label for="prompt">Prompt for Claude</label><textarea class="field prompt" id="prompt" readonly></textarea></div>
    <div class="rowbtns"><button class="btn primary" type="button" id="openClaude">{icon("spark")}Copy prompt and open Claude</button><button class="btn secondary" type="button" id="pdfBrief">{icon("file")}Download PDF brief</button><button class="btn quiet" type="button" id="copyPrompt">{icon("copy")}Copy</button></div>
    <div class="rowbtns"><button class="btn secondary sm" type="button" id="saveIdea">Save to my bench</button><span class="status" id="studioStatus" aria-live="polite"></span></div>
  </div>
</div></div>"""
        self.page("/studio/", "Invention studio", "Turn a free-to-use patent or your own idea into a ready-made prompt and PDF brief for Claude: modern directions, a novelty screen and a provisional patent draft.",
                  body, section="/studio/", scripts=("studio",))

    def account(self):
        g = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="#4285F4" d="M22.6 12.3c0-.8-.1-1.6-.2-2.3H12v4.4h5.9a5 5 0 0 1-2.2 3.3v2.7h3.6c2.1-1.9 3.3-4.8 3.3-8.1z"/><path fill="#34A853" d="M12 23c3 0 5.5-1 7.3-2.7l-3.6-2.7c-1 .7-2.2 1.1-3.7 1.1-2.9 0-5.3-1.9-6.2-4.5H2.1v2.8A11 11 0 0 0 12 23z"/><path fill="#FBBC05" d="M5.8 14.2a6.6 6.6 0 0 1 0-4.3V7.1H2.1a11 11 0 0 0 0 9.9l3.7-2.8z"/><path fill="#EA4335" d="M12 5.4c1.6 0 3.1.6 4.2 1.7l3.2-3.2A11 11 0 0 0 2.1 7.1l3.7 2.8C6.7 7.3 9.1 5.4 12 5.4z"/></svg>'
        body = f"""<div class="page">
<div id="loadView"><p class="muted" style="text-align:center;padding:48px 0"><span class="think">Loading your account…</span></p><noscript><p class="empty">Accounts need JavaScript turned on.</p></noscript></div>
<div id="authView" hidden>
  <div class="authwrap">
    <div class="authpitch">
      <div class="kicker">Free account</div>
      <h1>Claim your spot on <em>the yard.</em></h1>
      <p>An account is free and takes a minute. Browsing and the patent files never need one.</p>
      <ul class="perks">
        <li><span class="pi">{icon("flag")}</span><div><b>Reserve patents</b><span>Hold up to 5 for 30 days so other builders know you're on them.</span></div></li>
        <li><span class="pi">{icon("spark")}</span><div><b>Keep your inventions</b><span>Save ideas from the studio to your bench and pick them up anywhere.</span></div></li>
        <li><span class="pi">{icon("shield")}</span><div><b>Private by default</b><span>No ads, no tracking. Only your display name shows next to what you reserve.</span></div></li>
      </ul>
    </div>
    <div class="authcard" id="authCard">
      <div id="authMain">
        <h2 id="authTitle">Welcome back</h2><p class="sub" id="authSub">Sign in to your bench.</p>
        <div class="seg" role="tablist" aria-label="Account"><span class="ind" aria-hidden="true"></span><button type="button" role="tab" data-mode="in" aria-selected="true">Sign in</button><button type="button" role="tab" data-mode="up" aria-selected="false">Create account</button></div>
        <div id="oauthRow" hidden><button class="gbtn" type="button" id="googleBtn">{g}<span>Continue with Google</span></button><div class="ordiv">or with email</div></div>
        <form id="authForm" class="authform" novalidate>
          <div class="fgroup" id="nameRow" hidden><label for="aName">Display name</label><input class="field" id="aName" maxlength="40" autocomplete="nickname" placeholder="Shown next to your reservations"></div>
          <div class="fgroup"><label for="aEmail">Email</label><input class="field" id="aEmail" type="email" required autocomplete="email" placeholder="you@example.com"></div>
          <div class="fgroup" id="pwRow"><label for="aPw">Password</label><div class="pwbox"><input class="field" id="aPw" type="password" minlength="8" required autocomplete="current-password"><button type="button" id="pwShow" aria-pressed="false">Show</button></div>
            <div class="meterbar" id="pwMeter" hidden><i></i></div><small id="pwHint" hidden>At least 8 characters. A short phrase is easiest to remember.</small></div>
          <button class="btn primary lg" type="submit" id="authSubmit"><span>Sign in</span></button>
          <p class="status authstatus" id="authStatus" aria-live="polite"></p>
          <button class="btn quiet sm" type="button" id="forgotBtn" style="justify-self:center">Forgot your password?</button>
        </form>
      </div>
      <div id="authDone" hidden></div>
      <p class="fine2">By continuing you agree to the <a href="/legal/terms/">terms</a> and <a href="/legal/privacy/">privacy notice</a>.</p>
    </div>
  </div>
</div>
<div id="newPwView" hidden>
  <div class="authcard" style="max-width:440px;margin:32px auto 0"><h2>Set a new password</h2><p class="sub">Choose a new password for your account.</p><form id="newPwForm" class="authform"><div class="fgroup"><label for="npw">New password</label><input class="field" id="npw" type="password" minlength="8" required autocomplete="new-password"></div><button class="btn primary lg" type="submit"><span>Save password</span></button><p class="status" id="npwStatus" aria-live="polite"></p></form></div>
</div>
<div id="benchView" hidden>
  <div id="welcome"></div>
  <div class="sechead"><div><h1>My bench</h1><p id="benchWho"></p></div><div class="rowbtns"><a class="btn primary" href="/studio/">{icon("spark")}New invention</a><a class="btn secondary" href="/settings/">{icon("gear")}Settings</a><button class="btn quiet" type="button" id="signOut">Sign out</button></div></div>
  <div class="explain"><span class="badge reserved">Reserved</span><p><b>What reserving does.</b> A reservation holds a patent for you on Patent Yard for 30 days. Other builders see it's taken, with your optional note, so nobody here duplicates your work. You can hold 5 at a time and renew in the last week. <b>It doesn't stop anyone from using the patent.</b> It gives you no legal rights: the invention stays free for everyone, including other builders.</p></div>
  <div class="bench">
    <div class="list"><header><h2>Reserved</h2><span class="badge plain" id="resCount">0 of 5</span></header><div id="resList"></div></div>
    <div class="list"><header><h2>Inventions</h2><span class="badge plain" id="ideaCount">0</span></header><div id="ideaList"></div></div>
  </div>
</div>
<div id="offView" hidden><div class="empty">Accounts are being set up. Browsing, the patent files and the invention studio work without one.</div></div>
</div>"""
        self.page("/account/", "My account", "Sign in to reserve patents and keep your inventions on your Patent Yard bench.", body, section="/account/", scripts=("account",), index=False)

    def how(self):
        body = f"""<div class="page narrow" style="margin-inline:auto">
<div class="sechead"><div><h1>How a patent gets here</h1><p>Every patent comes from an official patent office source (the USPTO, the EPO, the Canadian Intellectual Property Office or IP Australia) and links back to it. Recently freed patents are rechecked daily, and new ones are added every week.</p></div></div>
<ol class="pipe">
  <li><span class="n">1</span><b>Recently lapsed</b><p>Every patent the USPTO's weekly Official Gazette listed in the past year as expired for an unpaid maintenance fee, minus any reinstated since. These get their full file: claims, description and drawings.</p><a href="https://www.uspto.gov/learning-and-resources/official-gazette/official-gazette-patents" {EXT}>Official Gazette for Patents</a></li>
  <li><span class="n">2</span><b>Family clearance</b><p>For recently lapsed patents, every US relative is checked. If a sibling patent could still be in force, or a continuation could still be pending, the patent is left out.</p></li>
  <li><span class="n">3</span><b>Full-term archive</b><p>Every US utility patent whose term has certainly ended: filed before May 29, 2000 (no term adjustments, extensions capped at five years), or granted before 1976. Listed from its USPTO record, with links to the full text.</p><a href="https://ppubs.uspto.gov/pubwebapp/" {EXT}>Patent Public Search</a></li>
  <li><span class="n">4</span><b>Design patents</b><p>Design patents granted more than 15 years ago. A design lasts 14 years from grant (15 if filed from May 13, 2015), and covers only how a product looks.</p><a href="https://ppubs.uspto.gov/pubwebapp/" {EXT}>Patent Public Search</a></li>
  <li><span class="n">5</span><b>Abandoned applications</b><p>Applications published 2001 to 2016 with no patent anywhere in their family and no family filing in seven years. Labeled "likely abandoned" because the status is inferred.</p><a href="https://ppubs.uspto.gov/pubwebapp/" {EXT}>Patent Public Search</a></li>
  <li><span class="n">6</span><b>European patents</b><p>Every European patent and application filed more than 20 years ago, so no European patent from it can still be in force; 25 and a half for medicines and crop protection, which a supplementary protection certificate can extend. From the EPO's linked open data (CC BY 4.0).</p><a href="https://data.epo.org/linked-data/" {EXT}>Linked open EP data</a></li>
  <li><span class="n">7</span><b>Canadian patents</b><p>Every Canadian patent and application whose term has certainly ended: filed from October 1, 1989 and more than 20 years ago (22 for drugs, which a certificate of supplementary protection can extend), or granted under the old law more than 17 years ago. From CIPO's patent data, under the Open Government Licence – Canada.</p><a href="https://open.canada.ca/data/en/dataset/fe1dfbb9-0fc3-42ca-b2a9-6ca4c05dbac9" {EXT}>CIPO patent data</a></li>
  <li><span class="n">8</span><b>Australian patents</b><p>Every Australian standard patent filed more than 21 years ago (26 for pharmaceuticals, which can get an extension), and every innovation and petty patent past its short term. From IP Australia's IPGOD (CC BY 2.5 AU).</p><a href="https://data.gov.au/data/dataset/ipgod2022" {EXT}>IPGOD</a></li>
  {f'<li><span class="n">9</span><b>All patents</b><p>Every patent and published application in Google Patents Public Data, from more than 100 offices ({big_number(WORLD["n"])} records), searchable in <a href="/all/">All patents</a>. Ones filed long enough ago that no patent from them can still be in force are marked past their term; every other status is shown as published, unchecked.</p><a href="https://console.cloud.google.com/marketplace/product/google_patents_public_datasets/google-patents-public-data" {EXT}>Google Patents Public Data</a></li>' if WORLD else ""}
  <li><span class="n">{10 if WORLD else 9}</span><b>Rechecked and growing</b><p>Each day recently lapsed patents are checked against the newest Gazette, and their families in rotation. New lapses join every week, and the site republishes every two hours.</p></li>
</ol>
<div class="section"><div class="sechead"><div><h2>Reinventing with Claude</h2></div></div>
<div class="prose"><p>Patent Yard doesn't run AI on its servers, so it stays free. Instead, every patent page and the <a href="/studio/">invention studio</a> write a careful prompt for your own Claude account, plus a PDF brief with the patent's claims, figures and original drawings. Paste the prompt into Claude, attach the brief, and Claude works through it with you: modern directions, a novelty screen, a provisional patent draft, concept sketches or a prototype plan.</p><p>Claude can't see patents filed after its training, so treat its novelty screen as a starting point and run the searches it suggests.</p></div></div>
<div class="section"><div class="law">
  <div class="panel"><h3>What you can do</h3><ul><li>Make, use and sell what an expired or abandoned US patent describes. Nobody can enforce it against you in the US. The same goes for an expired European, Canadian or Australian patent where it was granted.</li><li>Check the other places: a patent from one office says nothing about rights anywhere else. Each page says which office it comes from.</li><li>Improve on it and patent the improvement, if the improvement is new and not obvious.</li><li>File a provisional application yourself to lock in a filing date for 12 months.</li></ul></div>
  <div class="panel"><h3>What you can't do</h3><ul><li>Patent the same invention. The published document is prior art against everyone, you included.</li><li>Assume the whole product is free. A newer patent on some other part could still apply; we only check this patent's own family.</li><li>Assume foreign rights are gone. We check US rights only.</li></ul></div>
  <div class="panel"><h3>Fine print</h3><ul><li><b>Lapsed</b> patents can be reinstated if the owner shows the missed payment was unintentional. Anyone who started using the invention during the lapse keeps limited "intervening rights" under 35 U.S.C. 41(c)(2).</li><li><b>Likely abandoned</b> status is inferred from USPTO records. Confirm it on Patent Center before relying on it.</li><li>Patent Yard is not legal advice. For anything with real money behind it, talk to a registered patent attorney or agent.</li></ul></div>
</div></div>
<div class="section" id="faq"><div class="sechead"><div><h2>Questions</h2></div></div><div class="faq">
  <details><summary>What is a lapsed patent?</summary><p>US patents need maintenance fees 3.5, 7.5 and 11.5 years after grant, with a six-month grace period. If the owner doesn't pay, the patent expires at the 4th, 8th or 12th anniversary of its grant, and the USPTO lists it in the Official Gazette. From then on nobody can enforce it.</p></details>
  <details><summary>What does "expired, full term" mean?</summary><p>A US utility patent filed after June 8, 1995 lasts 20 years from its earliest non-provisional filing date. Patents filed before May 29, 2000 can't receive a term adjustment for USPTO delays, and other extensions are capped at five years, so all of them have ended. Patents filed before June 8, 1995 lasted 17 years from grant or 20 from filing, whichever was longer; those are listed once both have passed. Everything granted before 1976 has long expired.</p></details>
  <details><summary>Can I really build and sell these?</summary><p>In the US, yes: an expired or abandoned patent gives no one the right to stop you. Two cautions. Other, newer patents might cover parts of a product you build, and foreign patents in the same family might still be alive. Check both before you invest serious money.</p></details>
  <details><summary>Can I patent one of these?</summary><p>Not as it is. The published document is prior art. You can patent a genuine improvement that is new and not obvious, which is what the invention studio helps you find.</p></details>
  <details><summary>What does reserving do?</summary><p>It holds a patent for you on Patent Yard for 30 days so other builders here can see someone is working on it. It is a courtesy between users, not a legal right: it doesn't stop anyone, on Patent Yard or anywhere else, from using the patent. You can hold 5 at a time and renew in the last week.</p></details>
  <details><summary>Where do the drawings come from?</summary><p>Every drawing is a page of the patent's own published document, cropped to the drawing and scaled down. We never add to them. If a patent has no drawings, Claude can sketch it from the text, clearly marked as not part of the patent.</p></details>
  <details><summary>How current is the data?</summary><p>New lapses are added every week after the Official Gazette publishes, and the site republishes every two hours. Recently freed patents are rechecked against USPTO records daily; the date of the last check is on each patent's page. Patents in the archive, from every office, can't come back to life, so they don't need rechecking.</p></details>
  <details><summary>Is it really free?</summary><p>Yes. Browsing, reserving and the invention studio are free. The AI work happens in your own Claude account, which has a free plan, and the USPTO charges its own filing fee (from $65 for a micro entity provisional).</p></details>
</div></div></div>"""
        self.page("/how-it-works/", "How it works", "Where Patent Yard's patents come from, how they are checked every day, and what you can legally do with them.", body, section="/how-it-works/")

    def about(self):
        m = self.meta
        body = f"""<div class="page narrow" style="margin-inline:auto">
<div class="sechead"><div><h1>About Patent Yard</h1><p>A free register of inventions that anyone in the US may now build.</p></div></div>
<div class="prose">
<p>Every week, thousands of US patents stop being enforceable: owners stop paying maintenance fees, terms run out, and applications are quietly abandoned. The inventions in them become free for anyone to make, use and sell in the US. The same happens in Europe, Canada, Australia and everywhere else. Most are never looked at again.</p>
<p>Patent Yard collects them into one searchable register, traces each to its official USPTO record, shows the full file of recently freed ones with their original drawings, and explains the best of them in plain English. Builders can reserve a patent so others know it's taken, and take it to Claude to turn it into a new, patentable invention.</p>
<h2>What we promise</h2>
<ul><li><b>Sources first.</b> Every status comes from an official USPTO record, and every patent page links to it and to independent places to cross-check.</li><li><b>Nothing invented.</b> Drawings, claims and descriptions are the patent's own. Our names, summaries and modern angles are labeled as ours.</li><li><b>Free.</b> No ads, no paywall, no tracking. AI work runs in your own Claude account.</li></ul>
<h2>Today</h2>
<p>{m["count"] + m.get("archive", 0):,} free-to-use patents and applications from the US, Europe, Canada and Australia, across {len(self.fields)} fields: {m["count"]:,} US patents freed in the past year with their full files ({m["bySource"]["lapsed"]:,} lapsed for an unpaid fee), and {m.get("archive", 0):,} in the archive: US patents past their full term, expired designs, likely abandoned applications, and {", ".join(f"{c:,} from {k}" for k, c in m.get("archiveRegions", {}).items())} past their term. In the past year the Official Gazette recorded {m["lapsedYear"]:,} fee lapses and {m["reinstatedYear"]:,} reinstatements.</p>
<h2>Not legal advice</h2>
<p>Patent Yard is not a law firm and is not affiliated with the United States Patent and Trademark Office. Read the <a href="/legal/disclaimer/">disclaimer</a> before relying on anything here.</p>
</div></div>"""
        self.page("/about/", "About", "Why Patent Yard exists, where its data comes from, and what it promises.", body, section="/about/")

    def settings(self):
        def seg(name, opts):
            return (f'<div class="seg inline" role="radiogroup" aria-label="{E(name)}" data-setting="{name}">'
                    + "".join(f'<button type="button" role="radio" aria-checked="false" data-value="{v}">{E(t)}</button>' for v, t in opts) + "</div>")
        body = f"""<div class="page">
<div class="settings">
  <div class="sechead"><div><h1>Settings</h1><p>Display settings are saved in this browser. Account settings follow your account everywhere.</p></div></div>
  <section class="panel" aria-labelledby="sAppear"><h2 id="sAppear">Appearance</h2>
    <div class="setrow"><div><b>Theme</b><p>System follows your device's light or dark setting.</p></div>{seg("theme", [("system", "System"), ("light", "Light"), ("dark", "Dark")])}</div>
    <div class="setrow"><div><b>Drawings in dark mode</b><p>Inverted drawings match the dark page; original keeps black lines on white paper.</p></div>{seg("drawings", [("inverted", "Inverted"), ("original", "Original")])}</div>
    <div class="setrow"><div><b>Text size</b><p>Makes everything on the site a little larger.</p></div>{seg("text", [("normal", "Normal"), ("large", "Large")])}</div>
    <div class="setrow"><div><b>Motion</b><p>Turns off animations, including the drawing plotter on the home page.</p></div>{seg("motion", [("system", "System"), ("reduce", "Reduce")])}</div>
  </section>
  <section class="panel" aria-labelledby="sBrowse"><h2 id="sBrowse">Browsing</h2>
    <div class="setrow"><div><b>Default order</b><p>How the register is sorted when you aren't searching. Recommended puts patents with a written summary and an easy build first.</p></div>{seg("sort", [("build", "Recommended"), ("recent", "Recently freed"), ("added", "Newly added")])}</div>
  </section>
  <section class="panel" aria-labelledby="sAcct"><h2 id="sAcct">Account</h2>
    <div id="acctOff" hidden><p class="muted" style="padding:6px 0">Accounts are being set up.</p></div>
    <div id="acctOut" hidden><div class="setrow"><div><b>Not signed in</b><p>Sign in to reserve patents and keep inventions on your bench.</p></div><a class="btn primary" href="/account/?next=/settings/">Sign in</a></div></div>
    <div id="acctIn" hidden>
      <div class="setrow"><div><b>Email</b><p id="setEmail"></p></div></div>
      <form class="setrow" id="nameForm"><div><b><label for="setName">Display name</label></b><p>Shown next to the patents you reserve. Leave it blank to appear as "A builder".</p><input class="field" id="setName" maxlength="40" style="max-width:320px;margin-top:8px"></div><div class="rowbtns"><button class="btn secondary" type="submit">Save name</button></div></form>
      <form class="setrow" id="pwForm"><div><b><label for="setPw">New password</label></b><p>At least 8 characters.</p><input class="field" id="setPw" type="password" minlength="8" autocomplete="new-password" style="max-width:320px;margin-top:8px"></div><div class="rowbtns"><button class="btn secondary" type="submit">Change password</button></div></form>
      <div class="setrow"><div><b>Sign out</b><p>Signs you out in this browser.</p></div><button class="btn secondary" type="button" id="setSignOut">Sign out</button></div>
      <div class="setrow"><div><b>Delete account</b><p>Permanently removes your account, reservations and saved inventions.</p></div><button class="btn quiet" type="button" id="setDelete">Delete my account</button></div>
    </div>
    <p class="status" id="acctStatus" aria-live="polite"></p>
  </section>
  <section class="panel" aria-labelledby="sData"><h2 id="sData">Data in this browser</h2>
    <div class="setrow"><div><b>Clear saved settings and drafts</b><p>Resets the settings above and removes your unsent studio draft from this browser. Your account isn't affected.</p></div><button class="btn secondary" type="button" id="clearLocal">Clear</button></div>
  </section>
  <p class="muted" style="font-size:13px">Data checked against USPTO records {E(full_date(self.meta.get("verified") or self.meta["built"]))} · site version {self.version}</p>
</div></div>"""
        self.page("/settings/", "Settings", "Appearance, browsing and account settings for Patent Yard.", body, scripts=("settings",), index=False)

    def contact(self):
        body = f"""<div class="page narrow" style="margin-inline:auto">
<div class="sechead"><div><h1>Contact</h1><p>Questions, corrections or ideas for Patent Yard. To report a problem with a particular patent, use "Report a problem" on its page so we know which one.</p></div></div>
<div class="panel"><form id="contactForm" class="stack" novalidate>
  <div class="fgroup"><label for="cEmail">Your email (optional, if you'd like a reply)</label><input class="field" id="cEmail" type="email" maxlength="200" autocomplete="email"></div>
  <div class="fgroup"><label for="cBody">Message</label><textarea class="field" id="cBody" maxlength="4000" required style="min-height:160px"></textarea></div>
  <div class="sr" aria-hidden="true"><label for="cWebsite">Leave this empty</label><input id="cWebsite" tabindex="-1" autocomplete="off"></div>
  <div class="rowbtns"><button class="btn primary" type="submit">Send message</button><span class="status" id="cStatus" aria-live="polite"></span></div>
</form><p id="cOff" class="muted" hidden>The contact form is being set up. Please check back soon.</p></div>
<p class="muted" style="margin-top:14px;font-size:14px">We read every message. Patent Yard can't give legal advice; for that, talk to a registered patent attorney or agent. Please don't send confidential details of your own inventions. Messages are handled as described in our <a href="/legal/privacy/">Privacy Policy</a>.</p>
</div>"""
        self.page("/contact/", "Contact", "Get in touch with Patent Yard: questions, corrections and ideas.", body, scripts=("contact",))

    def legal(self):
        """Terms, privacy, disclaimer, copyright and accessibility, written for a free informational service. Each page
        lists its sections at the top and carries its effective date."""
        eff = "October 2, 2026"
        terms = [
            ("agreement", "Agreement", f"""<p>These Terms of Use govern your use of Patent Yard, the website at {SITE.replace("https://", "")} and its related services ("Patent Yard", "we", "us"). By using Patent Yard you agree to these Terms, to our <a href="/legal/privacy/">Privacy Policy</a> and to our <a href="/legal/disclaimer/">Disclaimer</a>, which are part of these Terms. If you don't agree, please don't use Patent Yard.</p>"""),
            ("eligibility", "Who may use Patent Yard", """<p>You must be at least 13 years old. If you are under 18, use Patent Yard only with a parent's or guardian's permission. An account is for one person. Keep your sign-in details to yourself; you are responsible for what happens under your account.</p>"""),
            ("service", "What Patent Yard is, and isn't", """<p>Patent Yard is a free, informational register of patents and published applications from the US, Europe, Canada and Australia whose protection appears to have ended, drawn from public records of the United States Patent and Trademark Office (USPTO), the European Patent Office (EPO), the Canadian Intellectual Property Office (CIPO) and IP Australia, with tools that write prompts and briefs for an AI assistant of your choosing.</p><p><b>Patent Yard is not a law firm and does not give legal advice.</b> Nothing on the site creates an attorney-client relationship. Patent Yard is not affiliated with, endorsed by or connected to the USPTO, the EPO, CIPO, IP Australia or any government agency.</p>"""),
            ("accuracy", "Accuracy, and no guarantee you are free to make anything", """<p>Statuses on Patent Yard come from public records and from rules we apply to them. Records can be wrong, incomplete or out of date, and our rules and inferences can be wrong. "Likely abandoned" is an inference. A patent listed here may have been reinstated, extended or corrected after we checked. Records in All patents come from Google Patents Public Data as published; apart from marking those past their term, we don't check whether they are in force. We check each patent only where it was granted: US rights for a US patent, European rights for a European patent, and so on.</p><p>Even when a patent has expired, other patents, design patents, trademarks, trade dress, copyrights, regulations or contracts may still apply to a product you make, use or sell. <b>You are solely responsible for confirming a patent's status and your freedom to operate</b> before you rely on anything here. For anything that matters, consult a registered patent attorney or agent.</p>"""),
            ("use", "Your use of patents and information", """<p>Patent documents are public records. Patent Yard grants no license to any patent or invention; whatever right you have to use an invention comes from the law, not from us. You are solely responsible for anything you build, sell, publish or file, including its safety, its compliance with law and any claims made against you.</p>"""),
            ("reservations", "Reservations", """<p>A reservation is a courtesy between users of Patent Yard. It gives you no legal right, exclusivity or priority of any kind: anyone may still make, use or sell what an expired patent describes, and anyone may file on their own improvements. We may limit, change, release or remove reservations and notes at any time.</p>"""),
            ("ai", "AI-assisted tools", """<p>The Reinvent with Claude kit and the invention studio create prompts and PDF briefs in your browser. If you paste them into Claude or another AI service, that service's own terms and privacy policy apply. AI output can be inaccurate, incomplete, unoriginal or unsuitable for filing, and it may describe things that infringe others' rights. Review everything yourself. We are not responsible for any AI service or its output.</p>"""),
            ("content", "Your content", """<p>You keep ownership of what you submit: display names, reservation notes, saved inventions and messages. You give us a limited, non-exclusive, royalty-free license to store, process and display it as needed to run Patent Yard. Display names and reservation notes are public; saved inventions are private to your account. You confirm you have the right to submit your content and that it doesn't break any law or anyone's rights.</p><p><b>Protect your own inventions.</b> Publicly describing an invention can limit or end your ability to patent it. Don't put inventive details in public reservation notes or messages; keep them in your private saved inventions, and talk to a patent professional about filing.</p>"""),
            ("conduct", "Acceptable use", """<p>Don't use Patent Yard to break the law; harass, threaten or impersonate anyone; post other people's personal information; send spam; upload malware; interfere with or overload the service; probe or bypass its security; create accounts automatically; or suggest that you, or Patent Yard, are connected to the USPTO. Reasonable, rate-limited automated access to public pages is fine; heavy scraping is not.</p>"""),
            ("ip", "Our content", """<p>Patent documents and USPTO data are public. Patent Yard's own work, including its plain-English summaries, design, software, compilation and arrangement, belongs to Patent Yard. You may link to any page and quote reasonably with attribution. The Patent Yard name and logo are ours; don't use them in a way that suggests we endorse you.</p>"""),
            ("third", "Other services and links", """<p>Patent Yard links to and relies on other services, including the USPTO, Google Patents, Justia, FreePatentsOnline, Espacenet, Google sign-in, Supabase and Cloudflare. We don't control them and aren't responsible for their content, availability or practices.</p>"""),
            ("copyright", "Copyright complaints", """<p>If you believe something on Patent Yard infringes your copyright, follow the steps on our <a href="/legal/copyright/">Copyright and takedown</a> page.</p>"""),
            ("warranty", "No warranties", """<p>PATENT YARD IS PROVIDED "AS IS" AND "AS AVAILABLE", WITHOUT WARRANTIES OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING WARRANTIES OF ACCURACY, COMPLETENESS, MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, TITLE AND NON-INFRINGEMENT, TO THE FULLEST EXTENT THE LAW ALLOWS. WE DON'T PROMISE THAT THE SERVICE WILL BE UNINTERRUPTED, SECURE OR ERROR-FREE, OR THAT ANY INFORMATION IS CORRECT OR CURRENT.</p>"""),
            ("liability", "Limitation of liability", """<p>TO THE FULLEST EXTENT THE LAW ALLOWS, PATENT YARD AND THE PEOPLE WHO RUN IT WILL NOT BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, EXEMPLARY OR PUNITIVE DAMAGES, OR FOR LOST PROFITS, REVENUE, DATA, GOODWILL OR BUSINESS OPPORTUNITIES, OR FOR ANY COSTS OF INFRINGEMENT CLAIMS OR LITIGATION, ARISING FROM OR RELATED TO YOUR USE OF, OR INABILITY TO USE, PATENT YARD, EVEN IF ADVISED OF THEIR POSSIBILITY. OUR TOTAL LIABILITY FOR ALL CLAIMS RELATED TO PATENT YARD IS LIMITED TO FIFTY US DOLLARS (US$50). Some places don't allow some of these limits, so they may not all apply to you.</p>"""),
            ("indemnity", "Indemnity", """<p>To the extent the law allows, you agree to defend, indemnify and hold harmless Patent Yard and the people who run it from any claims, losses, damages and costs (including reasonable legal fees) arising from your use of Patent Yard, your content, anything you make, sell or file, or your breach of these Terms or anyone's rights.</p>"""),
            ("termination", "Suspension and termination", """<p>We may suspend or end your access, or remove your content, at any time, including for a breach of these Terms. You may stop using Patent Yard and delete your account at any time from <a href="/settings/">Settings</a>. Sections that by their nature should survive (including ownership, disclaimers, limits of liability and indemnity) survive termination.</p>"""),
            ("changes", "Changes", """<p>We may change Patent Yard or these Terms. Changed Terms take effect when posted here with a new effective date; we'll point out material changes on the site. If you keep using Patent Yard after a change, you accept the new Terms.</p>"""),
            ("law", "Governing law and disputes", """<p>These Terms are governed by the laws of the United States and of the US state in which Patent Yard's operator resides, without regard to conflict-of-law rules. Before filing any claim, please contact us so we can try to resolve it informally. Any claim must be brought in the state or federal courts located in that state, and, where the law allows, within one year after it arose.</p>"""),
            ("general", "General", """<p>These Terms, with the Privacy Policy and Disclaimer, are the whole agreement between you and Patent Yard about the service. If any part is unenforceable, the rest stays in effect. Not enforcing a term isn't a waiver. You may not transfer these Terms; we may, together with the service. Nothing here creates a partnership, employment or agency relationship.</p>"""),
            ("contact", "Contact", """<p>Questions about these Terms: use the <a href="/contact/">contact form</a>.</p>"""),
        ]
        privacy = [
            ("summary", "In short", """<ul><li>No ads, no analytics, no tracking cookies, and we never sell or share your personal information for advertising.</li><li>You can browse and search everything without an account.</li><li>An account stores your email, your optional display name, your reservations and your saved inventions. You can delete all of it at any time.</li><li>Patent Yard doesn't send your data to any AI service.</li></ul>"""),
            ("collect", "What we collect", """<p><b>Account.</b> Your email address and a password, which our authentication provider (Supabase) stores only as a secure hash. If you choose "Continue with Google", Google shares your name, email address and profile picture with us; we use the email and name.</p><p><b>Display name and reservations.</b> The patents you reserve, when, and your optional note. Your display name and notes are shown publicly next to what you reserved.</p><p><b>Saved inventions.</b> The names, descriptions and tasks you save from the studio, private to your account.</p><p><b>Messages.</b> What you send through the contact form or "Report a problem", the optional email address you give us, and the patent concerned.</p><p><b>Technical data.</b> Our hosting provider (Cloudflare) and database provider (Supabase) process your IP address and basic request information to deliver the site and keep it secure. Fonts load from Google Fonts and some code libraries from jsDelivr and cdnjs, which receive your IP address when they serve those files.</p><p><b>On your device.</b> Your browser keeps your sign-in session, display settings, saved patents, recently viewed patents and your unsent studio draft in local storage. We don't read these unless you use the feature, and you can clear them in <a href="/settings/">Settings</a>.</p>"""),
            ("use", "How we use it", """<p>To run your account and its features, show reservations, keep your saved inventions, answer your messages, check reported problems, keep the service secure and prevent abuse. We don't build profiles of you, show ads, or sell or share personal information for cross-context behavioral advertising.</p>"""),
            ("ai", "AI", """<p>Prompts and PDF briefs are created in your browser. Nothing is sent to an AI service unless you paste it there yourself, and then that service's privacy policy applies (for Claude, Anthropic's).</p>"""),
            ("providers", "Service providers", """<p>Supabase (accounts and database), Cloudflare (hosting and delivery), Google (sign-in if you choose it, and fonts), and jsDelivr and cdnjs (code libraries). They process data for us or under their own policies. We share personal information otherwise only when the law requires it, to protect people's rights or safety, or as part of a transfer of the service, in which case this policy continues to apply to it.</p>"""),
            ("retention", "How long we keep it", """<p>Account data, reservations and saved inventions stay until you delete them or your account. Messages are kept as long as we need them to handle what you asked, then deleted. Providers keep server logs for their usual short periods.</p>"""),
            ("rights", "Your choices and rights", """<p>You can change your display name and password and delete your account in <a href="/settings/">Settings</a>; deleting it removes your account, reservations and saved inventions. Depending on where you live, including California and the EU or UK, you may have rights to access, correct, delete or export your personal information and to object to some uses. Ask through the <a href="/contact/">contact form</a>; we'll respond within the time the law requires and won't treat you differently for asking.</p>"""),
            ("children", "Children", """<p>Patent Yard isn't directed to children under 13, and we don't knowingly collect their personal information. If you believe a child under 13 has given us information, contact us and we'll delete it.</p>"""),
            ("security", "Security", """<p>The site uses encrypted connections, the database only lets each person reach their own private data, and passwords are never stored in plain text. No system is perfectly secure, so please use a unique password.</p>"""),
            ("international", "Where data is processed", """<p>Patent Yard is run from the United States. Our providers may process data in the United States and other countries.</p>"""),
            ("changes", "Changes and contact", """<p>We'll post any changes here with a new effective date. Questions or requests: the <a href="/contact/">contact form</a>.</p>"""),
        ]
        disclaimer = [
            ("advice", "Not legal advice", """<p>Patent Yard is an informational tool. It is not a law firm, it doesn't give legal advice, and using it doesn't create an attorney-client relationship. Before you invest significant money, sell a product or file a patent application, talk to a registered patent attorney or agent. The USPTO keeps a <a href="https://oedci.uspto.gov/OEDCI/" target="_blank" rel="noopener noreferrer">directory of registered practitioners</a>.</p>"""),
            ("affiliation", "Not affiliated with the USPTO", """<p>Patent Yard is independent. It is not affiliated with, endorsed by or connected to the United States Patent and Trademark Office or any government agency. Patent data comes from public USPTO records, which themselves can contain errors, including scanning errors in older documents.</p>"""),
            ("status", "What our statuses mean", """<ul><li><b>Lapsed, fee not paid.</b> The USPTO's Official Gazette published an expiration notice because a maintenance fee went unpaid. A lapsed patent can be reinstated if the owner later shows the late payment was unintentional; people who began using the invention during the lapse keep limited "intervening rights" under 35 U.S.C. 41(c). Recent lapses carry the most risk.</li><li><b>Expired, full term.</b> The patent's maximum term has ended under the rules described on <a href="/how-it-works/">How it works</a>. In the archive, we have not checked the patent's family.</li><li><b>Expired design patent.</b> A design patent's 14- or 15-year term from grant has ended. It covered only the product's appearance.</li><li><b>Likely abandoned.</b> Our inference from USPTO records: no patent issued in the application's family and nothing was filed in it for years. Confirm it on Patent Center.</li></ul>"""),
            ("free", 'What "free to use" does and doesn\'t mean', """<p>When a patent's protection has ended, that patent can no longer be enforced where it was granted: the United States for a US patent, the countries a European patent covered, Canada or Australia. That does not mean a product is free of every right: other patents (including newer patents on improvements), design patents, trademarks, trade dress, copyrights, regulations and contracts may still apply, and the same invention may still be protected in other countries. We check only the patent shown, and only where it was granted.</p>"""),
            ("content", "Our notes and tools", """<p>Plain-English names, summaries, modern angles and build ratings are Patent Yard's editorial opinions, not part of any patent, and may be wrong. Drawings and text are reproduced from public patent documents. Prompts, briefs and anything an AI produces from them can be inaccurate or unoriginal; review all of it before you rely on it.</p>"""),
            ("patenting", "Patenting your own improvements", """<p>The published text of any patent here is prior art: you can't patent the same invention. You may be able to patent a genuine improvement that is new and not obvious. Public disclosure, sales and offers can start deadlines or end your chance to patent, and US and foreign rules differ. Get professional advice before you disclose or file.</p>"""),
            ("risk", "Use at your own risk", """<p>All information is provided as is, without warranty, and may be incomplete, out of date or wrong. You are responsible for your decisions and for verifying anything important with the USPTO and a qualified professional. See our <a href="/legal/terms/">Terms of Use</a> for the full disclaimer of warranties and limitation of liability.</p>"""),
        ]
        copyright_ = [
            ("public", "Patent documents", """<p>USPTO patent documents are generally free of copyright restrictions. A few carry a copyright or mask work notice placed by the applicant; we reproduce such documents as public records, and rights holders can contact us as described below.</p>"""),
            ("notice", "Reporting infringement", """<p>If you believe material on Patent Yard infringes your copyright, send a notice through the <a href="/contact/">contact form</a> that includes:</p><ol><li>the copyrighted work you believe is infringed;</li><li>the address of the page and the material on it;</li><li>your name and contact details;</li><li>a statement that you believe in good faith the use isn't authorized by the owner, its agent or the law;</li><li>a statement, under penalty of perjury, that your notice is accurate and that you are the owner or authorized to act for the owner;</li><li>your physical or electronic signature.</li></ol><p>We'll review notices promptly and remove or disable material where appropriate.</p>"""),
            ("counter", "Counter-notices", """<p>If your content was removed and you believe that was a mistake, send a counter-notice through the contact form identifying the material, stating under penalty of perjury that you believe in good faith it was removed by mistake, consenting to the jurisdiction of the federal courts where you live (or where Patent Yard's operator resides, if you live outside the US), and including your name, contact details and signature.</p>"""),
            ("repeat", "Repeat infringers", """<p>We disable the accounts of people who repeatedly infringe others' rights.</p>"""),
            ("errors", "Wrong or outdated listings", """<p>For a wrong status, a missing drawing or any other error in a listing, use "Report a problem" on the patent's page.</p>"""),
        ]
        access = [
            ("commitment", "Our commitment", """<p>We want Patent Yard to work for everyone. We aim to meet the Web Content Accessibility Guidelines (WCAG) 2.1 at level AA, and we test pages with automated accessibility checks, keyboard-only use and both light and dark modes.</p>"""),
            ("features", "What helps", """<ul><li>Every page works with a keyboard, with visible focus and a "skip to content" link.</li><li>Settings let you choose light or dark mode, larger text, reduced motion, and original black-on-white drawings.</li><li>Patent drawings have text alternatives, and every patent's full text is linked.</li></ul>"""),
            ("limits", "Known limits", """<p>Older patents come from scanned documents, and some of their text and drawings are hard to read. Content on linked third-party sites isn't under our control.</p>"""),
            ("feedback", "Feedback", """<p>If something doesn't work for you, tell us through the <a href="/contact/">contact form</a> and we'll fix it or find another way to get you the information.</p>"""),
        ]
        pages = {"terms": ("Terms of Use", terms), "privacy": ("Privacy Policy", privacy), "disclaimer": ("Disclaimer", disclaimer),
                 "copyright": ("Copyright and takedown", copyright_), "accessibility": ("Accessibility", access)}
        for slug, (title, sections) in pages.items():
            cur = ' aria-current="page"'
            nav = "".join(f'<a href="/legal/{s}/"{cur if s == slug else ""}>{t}</a>' for s, (t, _) in pages.items())
            toc = "".join(f'<li><a href="#{a}">{E(h)}</a></li>' for a, h, _ in sections)
            text = "".join(f'<section id="{a}"><h2>{E(h)}</h2>{t}</section>' for a, h, t in sections)
            body = f"""<div class="page legal">
<nav class="legalnav" aria-label="Legal">{nav}</nav>
<div class="sechead"><div><h1>{title}</h1><p>Effective {eff}. Written in plain language; the headings are a guide, not limits on what a section says.</p></div></div>
<div class="legalgrid"><nav class="legaltoc" aria-label="On this page"><b>On this page</b><ol>{toc}</ol></nav><div class="panel prose legaltext">{text}</div></div>
</div>"""
            self.page(f"/legal/{slug}/", title, f"Patent Yard {title.lower()}: how the free patent register works and what it promises.", body)

    def not_found(self):
        body = '<div class="notfound"><p class="kicker">Error 404</p><h1>Not here</h1><p class="muted" style="margin:14px 0 24px">That page doesn\'t exist, or the patent has left the register after a daily check.</p><div class="rowbtns" style="justify-content:center"><a class="btn primary" href="/browse/">Browse patents</a><a class="btn secondary" href="/">Home</a></div></div>'
        self.page("/404.html", "Page not found", "This page doesn't exist.", body, index=False)

    # -------------------------------------------------------- data, images, feeds
    # -------------------------------------------------------- static files, catalog data, feeds
    def assets(self):
        shutil.copytree(STATIC, DIST, dirs_exist_ok=True)
        stamp = zlib.crc32(b"".join(p.read_bytes() for p in sorted((STATIC / "assets").rglob("*")) if p.is_file()))
        self.version = f"{stamp:08x}"
        # the stylesheet is cached for a year, so its name carries its content hash: a page can never get an old copy
        css = (DIST / "assets" / "site.css").read_bytes()
        self.css = f"/assets/site.{zlib.crc32(css):08x}.css"
        (DIST / "assets" / "site.css").rename(DIST / self.css.lstrip("/"))
        cfg = {"siteUrl": SITE, "supabaseUrl": CONFIG.get("supabase_url", ""), "supabaseAnonKey": CONFIG.get("supabase_anon_key", ""), "version": self.version,
               **({"world": {"cards": WORLD["cards"]}} if WORLD else {})}
        (DIST / "assets" / "js" / "config.js").write_text(f"window.PY_CONFIG = {json.dumps(cfg)};\n")

    def kit(self, r, detail, doc):
        """What the Claude kit and the studio need about one patent (served at /data/p/<id>.json)."""
        e, dd = r["entry"], detail
        checks, warn = why_free(e)
        L = links(e, dd)
        n = (1 if r["fig"] else 0) + len(r["extra"])
        return {"id": e["id"], "n": e["n"], "t": e["t"], "ot": e["ot"], "h": e["h"], "tw": e["tw"], "st": e["st"], "status": STATUS[e["st"]],
                "field": self.fields.get(e["ind"], e["ind"]), "filed": e["f"], "granted": e["p"], "expired": e.get("x"), "termEnd": e.get("te"),
                "abs": dd["abs"], "claims": [c if isinstance(c, list) else [i + 1, c] for i, c in enumerate(doc["claims"])][:80], "figs": figure_lines(dd.get("figs") or []),
                "fieldText": dd.get("field") or "", "bg": dd.get("bg") or "", "inventors": dd.get("inv"), "assignee": dd.get("asg"), "cpc": dd.get("cpc") or [],
                "app": dd.get("app"), "why": checks, "warn": warn, "sheets": [self.img(e["id"], k) for k in range(1, n + 1)], "totalSheets": e["sh"],
                "url": SITE + purl(e["id"]), "pdf": L["pdf"], "google": L["google"], "armed": bool(e.get("arm"))}

    def catalog(self, archive=None):
        """The data browse and search run on, so no page ever downloads the whole register:
          keys.bin      per patent, in catalog order: field, flags, build, freed/added/filed day (filter and sort)
          c/<n>.json    card text for patents n*BLOCK .. n*BLOCK+BLOCK-1
          s/<ab>.json   search index: word -> patents it appears in, for words starting with "ab"
        Files live under /v/<content hash>/ and never change; /data/latest.json names the current set."""
        fields = list(P.FIELDS)
        n = len(self.rows)
        cols = [bytearray(n), bytearray(n), bytearray(n)]
        dates = [array.array("H", bytes(2 * n)) for _ in range(3)]
        blocks, index = [], {}
        for i, r in enumerate(self.rows):
            e = r["entry"]
            cols[0][i] = fields.index(e["ind"])
            cols[1][i] = ("lapsed", "expired", "abandoned").index(e["st"]) | e["ia"] << 2 | bool(r["fig"]) << 3 | (not e["auto"]) << 4 | e["pending"] << 5
            cols[2][i] = e["b"]
            for k, s in enumerate((r["freed"], r["added"], e["e"] or e["f"])):
                dates[k][i] = day_number(s)
            if i % BLOCK == 0:
                blocks.append([])
            blocks[-1].append([e["id"], e["t"], e["h"], "" if e["ia"] else (e["a"] or ""), e["sh"] if r["fig"] else 0])
            texts = [(0, e["t"]), (1, e["ot"] if e["ot"].lower() != e["t"].lower() else ""), (2 if not e["auto"] else 5, e["h"]),
                     (3, " ".join(e["tags"])), (4, e["a"] or "")]
            for wi, text in texts:
                for w in set(search_words(text)):
                    post = index.setdefault(w, {})
                    if post.get(i, 9) > wi:
                        post[i] = wi
        keys = struct.pack("<I", n) + b"".join(bytes(c) for c in cols) + (b"\0" if n % 2 else b"") + b"".join(d.tobytes() for d in dates)
        shards = {}
        for w, post in index.items():
            prev, enc = 0, []
            for doc in sorted(post):
                enc.append((doc - prev) * 8 + post[doc])
                prev = doc
            shards.setdefault(w[:2], {})[w] = enc
        files = {"keys.bin": keys}
        files.update({f"c/{k}.json": json.dumps(b, separators=(",", ":"), ensure_ascii=False).encode() for k, b in enumerate(blocks)})
        files.update({f"s/{p}.json": json.dumps(d, separators=(",", ":"), sort_keys=True).encode() for p, d in shards.items()})
        ver = f"{zlib.crc32(b''.join(k.encode() + v for k, v in sorted(files.items()))):08x}"
        for name, data in files.items():
            out = DIST / "v" / ver / name
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(data)
        m = self.meta
        latest = {"v": ver, "n": n, "block": BLOCK, "weights": WEIGHTS, "fields": fields, "names": {k: v[0] for k, v in P.FIELDS.items()},
                  "count": m["count"], "verified": m.get("verified"), "built": m["built"], "bySource": m["bySource"], "archive": archive}
        (DIST / "data").mkdir(exist_ok=True)
        (DIST / "data" / "latest.json").write_text(json.dumps(latest, separators=(",", ":")))
        return len(files), sum(len(v) for v in files.values())

    def feeds(self):
        newest = sorted(self.rows, key=lambda r: (r["added"], r["freed"]), reverse=True)[:50]
        updated = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        entries = "".join(
            f"""<entry><title>{E(r["entry"]["t"])} ({E(r["entry"]["n"])})</title><link href="{SITE}{purl(r["entry"]["id"])}"/><id>{SITE}{purl(r["entry"]["id"])}</id>"""
            f"""<updated>{(r["added"] or TODAY.isoformat())[:10]}T00:00:00Z</updated><summary>{E(STATUS[r["entry"]["st"]] + ". " + r["entry"]["h"])}</summary></entry>"""
            for r in newest)
        (DIST / "feed.xml").write_text(f'<?xml version="1.0" encoding="utf-8"?>\n<feed xmlns="http://www.w3.org/2005/Atom"><title>New on Patent Yard</title><link href="{SITE}/"/><link rel="self" href="{SITE}/feed.xml"/><id>{SITE}/</id><updated>{updated}</updated>{entries}</feed>\n')

    def sitemaps(self):
        # a sitemap holds at most 50,000 addresses, so the pages and the register are split and indexed. The 11.7M archive
        # pages are left out, and robots.txt keeps all but the main search engines off patent pages: every patent page,
        # drawing and kit file runs a Function, a free site gets 100,000 a day, and until 2026-10-25 a crawler working
        # through the archive used them up by 03:00 UTC each day, so patent pages failed for everyone until midnight.
        everything, maps = iter(self.pages), 0
        while chunk := list(itertools.islice(everything, 40000)):
            maps += 1
            k = maps
            urls = "".join(f"<url><loc>{SITE}{p}</loc>{f'<lastmod>{m}</lastmod>' if m else ''}</url>" for p, m in chunk)
            (DIST / f"sitemap-{k}.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
        items = "".join(f"<sitemap><loc>{SITE}/sitemap-{k}.xml</loc></sitemap>" for k in range(1, maps + 1))
        (DIST / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{items}</sitemapindex>\n')
        never = "".join(f"Disallow: {p}\n" for p in ("/account/", "/shard/", "/v/", "/tpl/", "/img/p/", "/data/p/", "/api/"))
        engines = "".join(f"User-agent: {b}\n" for b in ("Googlebot", "Bingbot", "Applebot", "DuckDuckBot"))
        (DIST / "robots.txt").write_text(f"{engines}Crawl-delay: 2\n{never}\nUser-agent: *\nCrawl-delay: 10\n{never}Disallow: /patents/\n\nSitemap: {SITE}/sitemap.xml\n")

    # -------------------------------------------------------- links
    def resolves(self, u):
        """True when an internal address exists: a file in dist, a patent page, a drawing or a patent's kit data."""
        p = html.unescape(u).split("#")[0].split("?")[0]
        m = re.fullmatch(r"/patents/([^/]+)/", p)
        if m:
            return m.group(1) in self.ids
        m = re.fullmatch(r"/img/p/([^/]+)/(\d+)\.png", p)
        if m:
            return 1 <= int(m.group(2)) <= self.ids.get(m.group(1), 0)
        m = re.fullmatch(r"/data/p/([^/]+)\.json", p)
        if m:
            return m.group(1) in self.ids
        return (DIST / p.lstrip("/") / ("index.html" if p.endswith("/") else "")).exists()

    def bad_links(self, page):
        ids = set(re.findall(r'\bid="([^"]+)"', page))
        bad = []
        for u in re.findall(r'\b(?:href|src)="([^"]+)"', page):
            if u.startswith("#"):
                if len(u) > 1 and u[1:] not in ids:
                    bad.append(u)
            elif u.startswith("/") and not u.startswith("//") and not self.resolves(u):
                bad.append(u)
        return bad


OWNER_NOISE = re.compile(r"\b(the|inc|incorporated|corp|corporation|co|company|ltd|limited|llc|l\.?l\.?c|lp|l\.?p|plc|gmbh|ag|kk|kabushiki|kaisha|sa|bv|nv|ab|oy|spa|srl)\b|[.,&']")


def line_chart(vals, labels, every, top, aria):
    """The animated line chart on Insights: vals left to right, every `every`th label under the axis."""
    W, H, pad = 760, 220, 34
    hi = max(vals, default=1) or 1
    pts = [(pad + i / max(1, len(vals) - 1) * (W - 2 * pad), H - pad - v / hi * (H - 2 * pad)) for i, v in enumerate(vals)]
    line = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) if pts else ""
    area = f"{line} L{pts[-1][0]:.1f},{H - pad} L{pts[0][0]:.1f},{H - pad} Z" if pts else ""
    ticks = "".join(f'<text class="muted" x="{x:.1f}" y="{H - 10}" text-anchor="middle">{E(t)}</text>' for (x, _), t in list(zip(pts, labels))[::every])
    return (f'<svg class="chart linechart" viewBox="0 0 {W} {H}" role="img" aria-label="{E(aria)}">'
            f'<line class="axis" x1="{pad}" y1="{H - pad}" x2="{W - pad}" y2="{H - pad}"/><text class="muted" x="{pad}" y="{pad - 12}">{E(top)}</text>'
            f'<path class="area" d="{area}"/><path class="line" d="{line}" pathLength="1"/>{ticks}</svg>')


# Google's owner names, title-cased by world.py tidy(), with their acronyms and legal forms put back
OWNER_WORDS = {"Kk": "KK", "Ag": "AG", "Se": "SE", "Sa": "SA", "Nv": "NV", "Bv": "BV", "Ab": "AB", "Gmbh": "GmbH", "Ibm": "IBM", "Lg": "LG",
               "Nec": "NEC", "Basf": "BASF", "Zte": "ZTE", "Boe": "BOE", "Tdk": "TDK", "Ntt": "NTT", "Abb": "ABB", "Gen": "General"}


def owner_name(o):
    return " ".join(OWNER_WORDS.get(t, t) for t in o.split())


def owner_key(o):
    """A company name reduced to what identifies it, so spellings of one company count together."""
    return " ".join(OWNER_NOISE.sub(" ", o.lower()).split()) or o.lower()


# Shown instead of the Claude kit on weapons patents (patents.armed). Same text in web/functions/_archive.js.
KIT_OFF = ('<div class="panel soft kitoff"><div class="block"><h3>No Claude kit for weapons</h3><p class="prose">Claude doesn\'t help design '
           'weapons, ammunition or explosives, so this page has no Reinvent kit. To develop this one, work with a federally licensed '
           'manufacturer (many of these items are regulated) and a registered patent attorney or agent, listed on the '
           '<a href="https://oedci.uspto.gov/OEDCI/" target="_blank" rel="noopener noreferrer">USPTO roster</a>.</p></div></div>')


# What makes a patent worth showing off on the home page: a field people get excited about, an exciting subject and a
# detailed drawing; never anything about bodily fluids or the like, and never one another builder has reserved.
COOL_FIELDS = {"robotics": 3, "mobility": 2.5, "ai": 2.5, "energy": 2, "sports": 2, "consumer": 2, "tools": 2, "electronics": 1.5,
               "imaging": 1.5, "agrifood": 1.2, "industrial": 1, "designs": 1, "software": .8, "other": .5, "telecom": .5, "medical": .4,
               "materials": .3, "biotech": .2, "chips": .2, "defense": 0}
COOL_WORDS = re.compile(r"\b(drones?|robot\w*|solar|bike|bicycles?|skate\w*|cameras?|wireless|smart|games?|toys?|virtual|augmented|3d|"
                        r"print\w*|laser|batter(y|ies)|charg\w*|electric|scooters?|boats?|kayaks?|surf\w*|guitars?|speakers?|headphones?|"
                        r"lights?|lamps?|kitchen|coffee|grill\w*|garden\w*|hydroponic|telescopes?|helmets?|backpacks?|watch|wearable|"
                        r"magnet\w*|hover\w*|fly\w*|wings?|rockets?|satellites?|vehicles?|cars?|motor\w*|music\w*|audio|drum\w*|"
                        r"camp\w*|tent|fishing|golf|tennis|ski\w*|snow\w*|water ?craft|jet|engine|gyro\w*|projector|holograph\w*)\b", re.I)
UNCOOL_WORDS = re.compile(r"\b(urin\w*|fec(al|es)|faeces|stools?|toilets?|bowels?|bladders?|catheter\w*|\w*ostomy|diapers?|incontinen\w*|"
                          r"menstru\w*|tampons?|vomit\w*|sputum|saliva\w*|semen|sperm\w*|enemas?|ha?emorrhoid\w*|cadavers?|corpses?|"
                          r"embalm\w*|lice|fleas?|parasites?|rectal|anal|vagin\w*|penile|penis|condoms?|erectile|nipples?|breasts?|"
                          r"cysts?|mucus|phlegm|excre\w*|sewage|manure|carcass\w*|slaughter\w*|euthan\w*|tumou?rs?|cancer\w*|"
                          r"wounds?|blood|biops\w*|surgical)\b", re.I)


def coolness(r):
    e = r["entry"]
    text = " ".join([e["t"], e["ot"], e["h"], " ".join(e["tags"])])
    if e.get("arm") or UNCOOL_WORDS.search(text):
        return -10
    ink = r["fig"].stat().st_size / 30000 if r["fig"] else 0
    return (COOL_FIELDS.get(e["ind"], .5) + min(2, .6 * len(COOL_WORDS.findall(text))) + min(1.5, ink)
            + (5 - (e["b"] or 5)) * .2 + (.3 if e["tw"] else 0))


# Opportunities: how much commercial ground a recently freed patent opened, from signals patent-value research relies on:
# how long the owner kept paying to protect it, how broad its claims are, who owned it, and the market its field sells into.
MARKET = {"medical": 1.0, "energy": 1.0, "ai": 1.0, "robotics": .9, "mobility": .9, "electronics": .8, "consumer": .8, "software": .7, "imaging": .7,
          "agrifood": .7, "telecom": .6, "chips": .6, "industrial": .6, "biotech": .6, "tools": .6, "sports": .6, "materials": .5}
ANALYSIS = json.loads((Path(__file__).parent / "opportunities.json").read_text())  # Claude's write-ups, in ranked order


def kept_years(e):
    return (d(e["x"]) - d(e["p"])).days / 365.25 if e.get("x") and e.get("p") else 0


def potential(r):
    """A score for the Opportunities page, or None for patents it leaves out (weapons, unfit for a showcase, not lapsed).
    ponytail: hand-set weights; replace with a fitted model if licensing or sales outcomes ever become available."""
    e = r["entry"]
    if e.get("arm") or e["st"] != "lapsed" or UNCOOL_WORDS.search(f'{e["t"]} {e["ot"]} {e["h"]}'):
        return None
    y, w1 = kept_years(e), e.get("w1") or 0
    return (MARKET.get(e["ind"], .3) * 2 + (1.8 if y > 11 else .9 if y > 7 else 0) + (.8 if 0 < w1 <= 60 else .5 if 0 < w1 <= 100 else .2 if 0 < w1 <= 150 else 0)
            + min(.6, .15 * (e.get("ni") or 0)) + (0 if e["ia"] else .4) + (.3 if r["fig"] else 0))


def signals(e):
    """The reasons a patent ranks, in plain words."""
    y = kept_years(e)
    out = [f"Owner paid to keep it {y:.0f} years" if y > 7 else ""]
    out.append(f'Broad claim, {e["w1"]} words' if 0 < (e.get("w1") or 0) <= 100 else "")
    out.append(f'{e["cl"]} claims' if e.get("cl") else "")
    out.append("Solo inventor" if e["ia"] else f'Owned by {e["a"]}' if e["a"] else "")
    return [x for x in out if x]


def reserved_ids():
    """Patents builders have reserved on the site (Supabase list_reservations, readable by anyone); none of them is
    featured on the home page."""
    try:
        req = urllib.request.Request(CONFIG["supabase_url"].rstrip("/") + "/rest/v1/rpc/list_reservations", data=b"{}", method="POST",
                                     headers={"apikey": CONFIG["supabase_anon_key"], "Authorization": "Bearer " + CONFIG["supabase_anon_key"],
                                              "Content-Type": "application/json"})
        return {x["patent_id"] for x in json.loads(urllib.request.urlopen(req, timeout=20).read())}
    except Exception as e:
        print("reservations unavailable:", e)
        return set()


def archive_term_end(f, p, kind=""):
    """When an archive patent's term ended: 20 years from filing, or for a filing before June 8, 1995 the later of that
    and 17 years from grant. A design: 14 years from grant (15 if filed from May 13, 2015). An abandoned application: ""."""
    if kind == "A":
        return ""
    if kind == "E":  # European: 20 years from filing (europe.py waits longer for classes a certificate can extend)
        return add_years(f, 20)
    if kind == "S":
        return add_years(p, 15 if f and f >= "2015-05-13" else 14)
    if not f or p < "1976-01-01":
        return add_years(p, 17)
    end = add_years(f, 20)
    return end if f >= "1995-06-08" else max(end, add_years(p, 17))


ARCH_TMP = WEB / "archive.tmp"  # full archive records, one file per shard, while the build runs


def archive_records(skip):
    """Archive patents not already in the register, newest first, as light (id, title, owner, field index, year, kind)
    tuples. The full records (ARCH_KEYS) go straight to ARCH_TMP for write_archive, so millions of them never sit in
    memory at once (a build of 11M+ archive patents fits in a few GB)."""
    fields, out, seen = list(P.FIELDS), [], set(skip)
    shutil.rmtree(ARCH_TMP, ignore_errors=True)
    ARCH_TMP.mkdir()
    tmp = [open(ARCH_TMP / f"{k}.bin", "wb") for k in range(SHARDS)]
    for x in archived():
        pid, k = x["id"], x.get("k", "")
        if pid in seen or not x.get("p") or (not x.get("f") and x["p"] >= "1976-01-01" and k in ("", "A")):  # a US record missing its filing date
            continue
        seen.add(pid)
        field = "designs" if k == "S" else P.field_of(x["cpc"]) or "other"
        t = P.plain(x["t"]) or "Untitled"
        t = t.capitalize() if t.isupper() else t  # SHOUTED TITLES from old records read better as sentences
        a = P.plain(x.get("a"))
        full = (pid, P.pub_number({"guid": pid, "type": "US-PGPUB" if k == "A" else "USPAT"}), t, x.get("f") or "", x["p"],
                x.get("te") or archive_term_end(x.get("f"), x["p"], k), a, P.plain(x.get("i")), fields.index(field), x["cpc"][:3],
                x.get("app") or "", x.get("pg") or 0, x.get("sh") or 0, k, x.get("g") or "", x.get("ab") or "")
        key, gz = pid.encode(), gzip.compress(json.dumps(dict(zip(ARCH_KEYS, full)), separators=(",", ":"), ensure_ascii=False).encode(), 6, mtime=0)
        tmp[shard_of(pid)].write(struct.pack("<HI", len(key), len(gz)) + key + gz)
        out.append((pid, t, a, fields.index(field), int(x["p"][:4]), k))
    for f in tmp:
        f.close()
    return out


def write_archive():
    """One small gzipped JSON record per archive patent, packed in shards like the pages (functions/_archive.js reads
    them), a shard at a time from the files archive_records wrote."""
    for k in range(SHARDS):
        b, items, i = (ARCH_TMP / f"{k}.bin").read_bytes(), {}, 0
        while i < len(b):
            kl, gl = struct.unpack_from("<HI", b, i)
            items[b[i + 6:i + 6 + kl].decode()] = b[i + 6 + kl:i + 6 + kl + gl]
            i += 6 + kl + gl
        if items:
            write_shard(DIST / "shard" / "a" / f"{k}.bin", items)
    shutil.rmtree(ARCH_TMP)


def archive_catalog(recs):
    """Search for the archive, in files that stay small however large it grows:
      c/<n>.json  card text for archive patents n*ARCH_BLOCK onward (newest grant first)
      s/<n>.json  word -> patents, for the words whose crc32 % ARCH_BUCKETS is n (exact words; the commonest are left out)"""
    df = collections.Counter()
    for r in recs:
        df.update(set(search_words(r[1])) | set(search_words(r[2])))
    stop = sorted(w for w, c in df.items() if c > max(2000, len(recs) * 0.015))
    stopset, buckets = set(stop), [{} for _ in range(ARCH_BUCKETS)]
    for i, r in enumerate(recs):
        tw = set(search_words(r[1])) - stopset
        for wi, ws in ((0, tw), (1, set(search_words(r[2])) - stopset - tw)):
            for w in ws:
                b = buckets[zlib.crc32(w.encode()) % ARCH_BUCKETS]
                (b.get(w) or b.setdefault(w, array.array("I"))).append(i * 2 + wi)  # compact: 4 bytes a posting
    files = {}
    for k in range(0, len(recs), ARCH_BLOCK):
        files[f"c/{k // ARCH_BLOCK}.json"] = json.dumps([list(r) for r in recs[k:k + ARCH_BLOCK]],
                                                       separators=(",", ":"), ensure_ascii=False).encode()
    for k, b in enumerate(buckets):
        enc = {}
        for w, post in b.items():
            prev, out = 0, []
            for v in post:  # doc*2 + where it matched; docs only increase, so store the steps
                out.append((v >> 1) - prev << 1 | v & 1)
                prev = v >> 1
            enc[w] = out
        files[f"s/{k}.json"] = json.dumps(enc, separators=(",", ":"), sort_keys=True).encode()
    ver = f"x{zlib.crc32(b''.join(k.encode() + v for k, v in sorted(files.items()))):08x}"
    for name, data in files.items():
        out = DIST / "v" / ver / name
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
    return {"v": ver, "n": len(recs), "block": ARCH_BLOCK, "buckets": ARCH_BUCKETS, "stop": stop}


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


def shard_of(pid):
    return int(re.sub(r"\D", "", pid.split("-")[1])) % SHARDS


def write_shard(path, items):
    """One shard file, read by web/functions/_lib.js without parsing anything (a free Worker gets 10 ms of CPU):
      "PYS2", uint32 n, then n entries (uint32 crc32(key), uint32 offset, uint32 length) sorted, then the items,
      each stored as uint16 key length, key, payload. Patent ids also get an entry under "CC-NUMBER" (no kind code)
      pointing at the same item, so a bare number finds its patent. Deterministic, so unchanged shards skip upload."""
    entries, blob = [], bytearray()
    for k in sorted(items):
        kb, off = k.encode(), len(blob)
        blob += struct.pack("<H", len(kb)) + kb + items[k]
        entries.append((zlib.crc32(kb), off, len(blob) - off))
        if "/" not in k and k.count("-") == 2:
            entries.append((zlib.crc32(k.rsplit("-", 1)[0].encode()), off, len(blob) - off))
    entries.sort()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"PYS2" + struct.pack("<I", len(entries)) + b"".join(struct.pack("<III", *e) for e in entries) + bytes(blob))


_SITE = None  # the Site being built, shared with forked workers


def render_shard(job):
    """Pages, drawings and kit data for every patent in one shard. Runs in a worker process."""
    k, idx = job
    s, pages, imgs, kits, smap, bad = _SITE, {}, {}, {}, [], []
    for i in idx:
        r = s.rows[i]
        e = r["entry"]
        detail, doc = dossier(r)
        page = s.patent(r, detail, doc)
        bad += [f"{e['id']}: {u}" for u in s.bad_links(page)]
        pages[e["id"]] = gzip.compress(page.encode(), 6, mtime=0)
        for n, f in enumerate(([r["fig"]] if r["fig"] else []) + r["extra"], 1):
            imgs[f"{e['id']}/{n}"] = f.read_bytes()
        kits[e["id"]] = gzip.compress(json.dumps(s.kit(r, detail, doc), separators=(",", ":")).encode(), 6, mtime=0)
        smap.append((purl(e["id"]), (e["v"] or r["added"] or TODAY.isoformat())[:10]))
    for kind, items in (("p", pages), ("i", imgs), ("k", kits)):
        if items:
            write_shard(DIST / "shard" / kind / f"{k}.bin", items)
    return smap, bad


def function_config():
    """web/functions/site.json: the shard count and the security headers from _headers ("/*"), which Cloudflare
    does not add to responses from Functions."""
    block = (STATIC / "_headers").read_text().split("\n\n")[0].splitlines()[1:]
    headers = dict(x.strip().split(": ", 1) for x in block if ": " in x)
    fields = {k: v[0] for k, v in P.FIELDS.items()}
    world = {k: WORLD[k] for k in ("cards", "details", "per", "ids")} if WORLD else None
    (WEB / "functions" / "site.json").write_text(json.dumps({"shards": SHARDS, "headers": headers, "site": SITE, "fieldKeys": list(P.FIELDS), "fields": fields,
                                                             **({"world": world} if world else {})}, indent=1) + "\n")


def build():
    """Builds into web/dist.new and swaps it in at the end, so web/dist is always a complete site for a deploy."""
    global _SITE, DIST
    lock = open(WEB / ".build.lock", "w")
    if not os.environ.get("PATENTYARD_LOCK_HELD"):  # the publisher holds it already for its own builds
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit("another build or deploy is using web/dist; try again when it finishes")
    final, DIST = DIST, WEB / "dist.new"
    try:
        s = _build()
    except BaseException:
        DIST = final
        raise
    old = WEB / "dist.old"
    if old.exists():
        shutil.rmtree(old)
    if final.exists():
        final.rename(old)
    DIST.rename(final)
    DIST = final
    shutil.rmtree(old, ignore_errors=True)
    return s


def _build():
    global _SITE
    t0 = time.time()
    rows, meta, dropped, _ = collect()
    for r in rows:
        e = r["entry"]
        r["freed"] = e.get("x") or e.get("te") or e.get("p") or ""
    # catalog order: patents with a written note first, easiest to build first, then the most recently freed
    rows.sort(key=lambda r: (r["entry"]["auto"], r["entry"]["b"] or 9, -day_number(r["freed"]), r["entry"]["id"]))
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    s = Site(rows, meta)
    recs = archive_records({r["entry"]["id"] for r in rows})
    recs.sort(key=lambda r: SPAN_ORDER.index(REGIONS.get(r[5], "US")))  # stable: newest first within each region
    spans, at = [], 0
    for name, c in sorted(collections.Counter(REGIONS.get(r[5], "US") for r in recs).items(), key=lambda x: SPAN_ORDER.index(x[0])):
        spans.append([name, at, at + c])
        at += c
    meta["archiveSpans"] = spans
    meta["archive"] = len(recs)
    by_kind = collections.Counter(r[5] for r in recs)
    meta["archiveEU"] = by_kind["E"]
    meta["archiveRegions"] = {REGIONS[k]: by_kind[k] for k in REGIONS if by_kind[k]}
    meta["reserved"] = reserved_ids()
    keys_ = list(P.FIELDS)
    meta["archiveByField"] = {keys_[i]: c for i, c in collections.Counter(r[3] for r in recs).items()}
    s.assets()
    s.home()
    s.browse()
    s.fields_index()
    s.studio()
    s.account()
    s.how()
    s.about()
    s.contact()
    s.settings()
    s.legal()
    s.not_found()
    s.insights(gazette_all(), recs)
    s.opportunities()
    if WORLD:
        s.all_patents()
    s.saved()
    s.archive_template()
    s.feeds()
    arch = archive_catalog(recs)
    arch["spans"] = spans
    write_archive()
    nfiles, nbytes = s.catalog(arch)
    function_config()
    bad = [f"{p.relative_to(DIST)}: {u}" for p in DIST.rglob("*.html") for u in s.bad_links(p.read_text())]
    jobs = {}
    for i, r in enumerate(rows):
        jobs.setdefault(shard_of(r["entry"]["id"]), []).append(i)
    _SITE = s
    with multiprocessing.get_context("fork").Pool(max(1, (os.cpu_count() or 2) - 2)) as pool:
        for smap, b in pool.imap_unordered(render_shard, sorted(jobs.items()), chunksize=4):
            s.pages += smap
            bad += b
    s.pages.sort()
    s.sitemaps()
    assert not bad, "broken links: " + "; ".join(bad[:10])
    files = [p for p in DIST.rglob("*") if p.is_file()]
    size = sum(p.stat().st_size for p in files)
    assert len(files) < 20000 and max(p.stat().st_size for p in files) < 25 * 2**20, "over Cloudflare Pages limits"
    print(f"website: {len(rows):,} patents in {len(jobs)} shards and {len(recs):,} in the archive, catalog {nfiles} files {nbytes / 1e6:.1f} MB, {len(files):,} files, "
          f"{size / 1e6:.1f} MB -> {DIST} ({time.time() - t0:.0f}s)")
    return s
