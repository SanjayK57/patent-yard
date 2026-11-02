#!/usr/bin/env python3
"""A representative Patent Yard built from invented sample data, for design work on any computer:

    python3 web/dev/fixtures.py OUT           build it (a few seconds)
    python3 web/dev/serve.py OUT 8000         serve it with the production headers, then open http://localhost:8000

No production data is needed (pipeline/raw holds 35 GB and only exists on the publishing Mac). Every record is
made up: titles start with "Sample", numbers sit far above any real US patent (US 98,000,001 and up), drawings
are generated line art, and every page carries a "sample data" banner. Never deploy OUT.
The production build (python3 pipeline/pipeline.py web) is untouched by this file.
"""
import datetime as dt
import math
import random
import shutil
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))
import patents as P  # noqa: E402
import website as W  # noqa: E402
from site_ui import shell  # noqa: E402

FIELDS = list(P.FIELDS)
STATUS = ["lapsed"] * 6 + ["expired", "abandoned"]
NOUNS = ["folding ladder", "bicycle brake", "solar lantern", "camera mount", "seed planter", "pet water bowl", "drone landing gear",
         "kitchen scale", "wind turbine hub", "hand drill guide", "robot gripper", "sensor glove", "battery clip", "tent pole joint",
         "door hinge", "phone stand", "garden hose reel", "shoe dryer", "camp stove", "bike lock", "light switch", "water filter",
         "desk lamp arm", "fishing reel", "ski binding", "tool holder", "car seat clip", "sewing guide", "chair caster", "plant pot tray"]


def png(path, w, h, seed):
    """Generated line art: a few parts with leader lines, black on white, written as a 1-bit PNG."""
    rnd, px = random.Random(seed), bytearray(b"\x01" * (w * h))
    def dot(x, y):
        if 0 <= x < w and 0 <= y < h:
            px[int(y) * w + int(x)] = 0
    def line(x0, y0, x1, y1):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n):
            dot(x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n)
    def rect(x, y, a, b):
        line(x, y, x + a, y); line(x + a, y, x + a, y + b); line(x + a, y + b, x, y + b); line(x, y + b, x, y)
    def circle(cx, cy, r):
        for k in range(int(r * 7)):
            t = k / (r * 7) * 2 * math.pi
            dot(cx + r * math.cos(t), cy + r * math.sin(t))
    for _ in range(rnd.randint(3, 5)):
        x, y, a, b = rnd.randint(40, w // 2), rnd.randint(40, h // 2), rnd.randint(60, w // 2), rnd.randint(40, h // 3)
        rect(x, y, a, b) if rnd.random() < .6 else circle(x + a / 2, y + b / 2, min(a, b) / 2)
        for k in range(1, rnd.randint(2, 6)):
            line(x + a * k / 6, y, x + a * k / 6 + 10, y + b)  # hatching
        line(x + a, y, x + a + 40, y - 30)  # a leader line
    rows = b"".join(b"\x00" + bytes(int("".join("1" if v else "0" for v in px[r * w + c:r * w + c + 8]).ljust(8, "1"), 2)
                                     for c in range(0, w, 8)) for r in range(h))
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 1, 0, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b""))


def sample_rows(tmp, n=36):
    rnd, today, rows = random.Random(7), dt.date.today(), []
    for i in range(n):
        st, ind = STATUS[i % len(STATUS)], FIELDS[i % len(FIELDS)]
        pid, num = f"US-{98000001 + i}-B{1 + i % 2}", 98000001 + i
        filed = today - dt.timedelta(days=4000 + 37 * i)
        figs = []
        for k in range(1 if i % 5 else 0, 1 + (i % 4) if i % 5 else 0):
            f = tmp / f"{pid}-{k + 1}.png"
            png(f, 520, 680 if k else 520, seed=i * 10 + k)
            figs.append(f)
        e = {"id": pid, "n": f"US {num:,} B{1 + i % 2}", "ind": ind, "st": st, "t": f"Sample {NOUNS[i % len(NOUNS)]}",
             "ot": f"Sample apparatus for a {NOUNS[i % len(NOUNS)]}", "h": f"A made-up {NOUNS[i % len(NOUNS)]} used to preview the design. Not a real patent.",
             "tw": "Sample modern angle: a note Patent Yard would write about why it matters now." if i % 3 == 0 else "",
             "b": 1 + i % 5, "f": filed.isoformat(), "e": filed.isoformat(), "p": (filed + dt.timedelta(days=900)).isoformat(),
             "x": (today - dt.timedelta(days=20 + 9 * i)).isoformat() if st == "lapsed" else "", "te": (filed + dt.timedelta(days=7305)).isoformat() if st == "expired" else "",
             "a": "Sample Tools Inc." if i % 2 else "", "ia": not i % 2, "fig": [520, 520] if figs else None, "fs": 0, "ns": len(figs), "sh": len(figs) + (i % 3),
             "tags": ["sample"], "cl": 12, "w1": 120, "ni": 1 + i % 3, "arm": False, "auto": i % 4 == 3, "pending": False, "fam": 1,
             "v": today.isoformat(), "og": {"d": today.isoformat(), "u": "https://www.uspto.gov/"}}
        rows.append({"entry": e, "path": None, "fig": figs[0] if figs else None, "extra": figs[1:], "added": (today - dt.timedelta(days=i)).isoformat(),
                     "freed": e["x"] or e["te"] or e["p"]})
    return rows


def dossier(r):
    e = r["entry"]
    detail = {"abs": f"{e['ot']}. This abstract is invented sample text for a design preview.", "abx": False, "c1": "", "figs": ["FIG. 1 is a sample view."],
              "field": "", "bg": "", "tw": e["tw"], "cpc": ["A01B1/00"], "app": "99/000001", "inv": "Sample Inventor", "asg": e["a"] or None, "rel": [], "pages": 6}
    claims = [[1, f"A sample {e['t'].lower()[7:]} comprising: a base; and an arm joined to the base."], [2, "The sample of claim 1, wherein the arm folds."],
              [3, "The sample of claim 2, wherein the arm locks."], [4, "A method of using a sample device, comprising: unfolding it."]]
    desc = ["SAMPLE DESCRIPTION", "Invented paragraphs that stand in for a patent's description while the design is checked."] * 4
    return detail, {"claims": claims, "desc": desc, "more": False, "family": [], "cites": ["7038588", "2015/0025423"]}


def main(out):
    tmp = out.parent / (out.name + ".drawings")
    for d in (out, tmp):
        shutil.rmtree(d, ignore_errors=True)
        d.mkdir(parents=True)
    rows = sample_rows(tmp)
    meta = {"built": dt.datetime.now().isoformat(timespec="minutes"), "verified": dt.datetime.now().isoformat(timespec="minutes"), "count": len(rows),
            "bySource": {s: sum(r["entry"]["st"] == s for r in rows) for s in ("lapsed", "expired", "abandoned")}, "lapsedYear": 0, "reinstatedYear": 0, "industries": {}, "archiveSpans": [], "archive": 0, "archiveEU": 0,
            "archiveRegions": {}, "reserved": set(), "archiveByField": {}}
    W.DIST, W.dossier = out, dossier
    shell.DEV_BANNER = "Development preview with invented sample data. None of these patents is real."
    s = W.Site(rows, meta, out)
    for step in ("assets", "home", "browse", "fields_index", "studio", "account", "how", "about", "contact", "settings", "legal", "not_found", "saved", "feeds"):
        getattr(s, step)()
    s.insights([], [])
    s.opportunities()
    s.archive_template()
    s.catalog(None)
    W._SITE = s
    for k in sorted({W.shard_of(r["entry"]["id"]) for r in rows}):
        W.render_shard((k, [i for i, r in enumerate(rows) if W.shard_of(r["entry"]["id"]) == k]))
    shutil.rmtree(tmp)
    print(f"sample site in {out}: python3 web/dev/serve.py {out} 8000")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    main(Path(sys.argv[1]).resolve())
