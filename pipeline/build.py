"""Package the register for the site: site/data/*.json.

  index.json        every listed patent's card data plus totals
  detail-<field>    abstract, first claim, figure descriptions, background, filing facts   (opened patent)
  fig-<n>           first drawing sheet for each patent in bundle n                        (cards)
  doc-<n>           all claims, description, family, citations                            (dossier tabs)
  sheets-<n>        further drawing sheets                                                  (Drawings tab)

Bundles are keyed by a stable hash of the patent number, so a wall of 15 cards loads at most 15 small files.
The artifact accepts 255 files and 64 MB per version; the build stays under both, retiring the longest-free
patents first when the size budget is reached.
"""
import base64
import datetime as dt
import functools
import json
import re
import zlib

import patents as P
import uspto
from register import RAW, TODAY, gazette_all, lapse_sets, listed

SITE_DATA = RAW.parent.parent / "site" / "data"
SHARDS = 70         # 3 bundle kinds x 70 + 14 detail files + index = 225 files
BUDGET = 55_000_000  # bytes


def _b64(path):
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()


def freed_on(c):
    return c.get("expired") or (P.term_end(c) if c["status"] == "expired" else c.get("published")) or ""


def clean(c):
    """USPTO search results carry markup and escapes (Xiao &quot;Charles&quot;, <i>Lactobacillus</i>); older records still do."""
    for k in ("title", "assignee", "inventors"):
        if c.get(k):
            c[k] = P.plain(c[k])
    for m in c.get("family_members") or []:
        if m.get("t"):
            m["t"] = P.plain(m["t"])
    return c


def auto_note(c):
    """For a patent nobody has written a note for: its own title and the first sentence of its abstract."""
    t = " ".join(c["title"].split())
    if t.isupper():
        t = t.capitalize()
    first = re.split(r"(?<=[a-z0-9)][.;])\s+(?=[A-Z])", (c.get("abstract") or "").strip(), 1)[0]
    hook = first if len(first) <= 220 else first[:220].rsplit(" ", 1)[0] + "…"
    return {"name": t, "hook": hook, "build": 0, "tags": [], "twist": "", "auto": True}


@functools.lru_cache(maxsize=1)
def google_abstracts():
    """guid -> {"ab", "i"}: abstract excerpts from Google Patents Public Data (google_abstracts.py) for patents still
    waiting on their USPTO text."""
    f = RAW / "google_abstracts.json"
    return json.loads(f.read_text()) if f.exists() else {}


def excerpt(c):
    """Fill a waiting patent's abstract (and inventor) from the Google excerpt; True when it did."""
    g = None if c.get("abstract") else google_abstracts().get(c["guid"])
    if not g:
        return False
    ab = g["ab"]
    c["abstract"] = ab if len(ab) < 315 or ab.endswith(".") else ab.rsplit(" ", 1)[0] + " …"  # the export cut it at 320
    c["inventors"] = c.get("inventors") or g.get("i") or ""
    return True


def dossier(r):
    """Detail and full document for one row, read from its record when a page needs them."""
    c = clean(json.loads(r["path"].read_text()))
    abx = excerpt(c)
    desc = P.tidy(c.get("desc") or [])
    doc = {"claims": c.get("claims_all") or ([[1, c["claim1"]]] if c.get("claim1") else []), "desc": desc, "more": c.get("desc_more", False),
           "family": c.get("family_members") or [], "cites": c.get("cites") or []}
    detail = {
        "abs": c.get("abstract") or "", "abx": abx, "c1": c.get("claim1") or "", "figs": c.get("figures") or [],
        "field": P.field_text(desc) if desc else c.get("field", ""),
        "bg": P.background_text(desc) if desc else c.get("background", ""), "tw": r["entry"]["tw"], "cpc": c["cpc"][:8], "app": c["app"],
        "inv": c["inventors"], "asg": c["assignee"], "rel": c.get("related") or [], "pages": c["pages"],
    }
    return detail, doc


def collect(budget=None):
    """Every listed patent that is still clear, newest-freed first, as dicts with the card entry, the record's path and
    its drawing files; dossier(row) reads the full text. Shared by the claude.ai build below and the website."""
    issues = gazette_all()
    _, reinstated = lapse_sets(issues)
    vfile = RAW / "verify.json"
    verified = json.loads(vfile.read_text()) if vfile.exists() else {}
    rows, used, dropped, over = [], 0, [], []
    for p, c, note in sorted(listed(), key=lambda t: freed_on(t[1]), reverse=True):
        pn = P.number(c["guid"])
        if c.get("verify_ok") is False or (c["status"] == "lapsed" and pn in reinstated):
            dropped.append(c["guid"])
            continue
        if budget and (note is None or P.armed(c["cpc"])):  # the claude.ai version: written notes only, no weapons
            continue
        clean(c)
        excerpt(c)
        note = note or auto_note(c)
        fig = RAW / "figs" / f"{c['guid']}.png"
        fig = fig if fig.exists() else None
        extra = [RAW / "sheets" / f"{c['guid']}-{k}.png" for k in range(1, (c.get("extra_sheets") or 0) + 1)]
        extra = [f for f in extra if f.exists()]
        if budget:
            size = len(json.dumps([c.get("claims_all"), c.get("desc"), c.get("family_members"), c.get("cites")]))
            size += sum(f.stat().st_size * 4 // 3 + 40 for f in ([fig] if fig else []) + extra) + 3500
            if used + size > budget:
                over.append(c["guid"])
                continue
            used += size
        # a written note may set the field; otherwise it follows the patent's main classification
        field = note.get("ind") or (P.field_of(c["cpc"]) or "other" if note.get("auto") else c["industry"])
        w1, ni = P.breadth(c.get("claims_all"))
        n = zlib.crc32(c["guid"].encode()) % SHARDS
        entry = {
            "id": c["guid"], "n": P.pub_number(c), "ind": field, "st": c["status"],
            "t": note["name"], "ot": c["title"], "h": note["hook"], "tw": note.get("twist", ""), "b": note["build"],
            "f": c["filed"], "e": P.earliest_filing(c), "p": c["published"], "x": c.get("expired"),
            "a": c["assignee"] or c["inventors"], "ia": not c["assignee"],
            "fig": c.get("fig") if fig else None, "fs": n, "ns": (1 if fig else 0) + len(extra),
            "sh": c.get("sheet_count") or (1 if fig else 0), "tags": note.get("tags", []),
            "cl": len(c.get("claims_all") or []), "w1": w1, "ni": ni, "arm": P.armed(c["cpc"]), "auto": bool(note.get("auto")), "pending": bool(c.get("text_pending")),
            "fam": len(c["family_members"]) + 1 if "family_members" in c else c.get("familySize", 1), "v": (c.get("verified") or "")[:10],
        }
        if c["status"] == "lapsed" and c.get("og_date"):
            entry["og"] = {"d": c["og_date"], "u": uspto.gazette_url(c.get("og_week"), c["og_date"], TODAY)}
        if c["status"] == "expired":
            entry["te"] = P.term_end(c)
        rows.append({"entry": entry, "path": p, "fig": fig, "extra": extra, "added": c.get("harvested") or c.get("enriched") or ""})

    lapsed_year, rein_year = set(), set()
    for o in issues:
        if (TODAY - dt.date.fromisoformat(o["date"])).days <= 365:
            lapsed_year |= {x["pn"] for x in o["lapsed"]}
            rein_year |= set(o["reinstated"])
    counts = {s: sum(1 for r in rows if r["entry"]["st"] == s) for s in ("lapsed", "abandoned", "expired")}
    meta = {"built": dt.datetime.now().astimezone().isoformat(timespec="minutes"), "verified": verified.get("at"),
            "count": len(rows), "bySource": counts, "lapsedYear": len(lapsed_year), "reinstatedYear": len(rein_year),
            "industries": {k: v[0] for k, v in P.FIELDS.items()}}
    return rows, meta, dropped, over


def build():
    SITE_DATA.mkdir(parents=True, exist_ok=True)
    rows, meta, dropped, over = collect(BUDGET)
    index, detail, figs, docs, sheets = [], {}, {}, {}, {}
    for r in rows:
        e, n = r["entry"], r["entry"]["fs"]
        r["detail"], r["doc"] = dossier(r)
        index.append(e)
        detail.setdefault(e["ind"], {})[e["id"]] = r["detail"]
        if r["fig"]:
            figs.setdefault(n, {})[e["id"]] = _b64(r["fig"])
        docs.setdefault(n, {})[e["id"]] = r["doc"]
        if r["extra"]:
            sheets.setdefault(n, {})[e["id"]] = [_b64(f) for f in r["extra"]]

    for old in SITE_DATA.glob("*.json"):
        old.unlink()
    dump = lambda name, obj: (SITE_DATA / name).write_text(json.dumps(obj, separators=(",", ":")))
    dump("index.json", {"meta": meta, "patents": index})
    for kind, bundle in (("detail", detail), ("fig", figs), ("doc", docs), ("sheets", sheets)):
        for key, d in bundle.items():
            dump(f"{kind}-{key}.json", d)
    files = list(SITE_DATA.glob("*.json"))
    total = sum(f.stat().st_size for f in files)
    assert len(files) <= 250 and total <= 62_000_000, f"over the artifact limits: {len(files)} files, {total} bytes"
    print(f"built {len(index)} patents ({meta['bySource']}); {len(dropped)} dropped as no longer clear, {len(over)} left out for size; "
          f"{len(files)} files, {total / 1e6:.1f} MB")
    return len(index)
