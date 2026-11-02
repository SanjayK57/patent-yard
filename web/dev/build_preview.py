#!/usr/bin/env python3
"""Fast local build of the website for design work: python3 web/dev/build_preview.py OUT [--live DIST] [--patents ID,ID]

Writes every static page (home, browse, studio, legal...) fresh into OUT in about a minute, from the real records in
pipeline/raw (only on the publishing Mac). Patent pages and drawings live in shard files: with --live DIST (a full
build, e.g. ~/PatentYard/web/dist) the shards are linked from it, and the shards holding --patents (plus the home
page's picks) are rendered fresh. Without real data, use web/dev/fixtures.py instead.

Serve OUT with Pages Functions: cd web && npx wrangler@4 pages dev OUT --port 8788
"""
import os
import re
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline"))
os.chdir(ROOT / "pipeline")
import website as W  # noqa: E402
from register import gazette_all  # noqa: E402

TEST = ["US-11117268-B2", "US-10008816-B2", "US-10000283-B2"]


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def main(out, live, test):
    t0 = time.time()
    rows, meta, _, _ = W.collect()
    for r in rows:
        e = r["entry"]
        r["freed"] = e.get("x") or e.get("te") or e.get("p") or ""
    rows.sort(key=lambda r: (r["entry"]["auto"], r["entry"]["b"] or 9, -W.day_number(r["freed"]), r["entry"]["id"]))
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    W.DIST = out
    s = W.Site(rows, meta, out)
    # the archive's size by region, as the last full build counted it (recounting needs the whole archive)
    n = meta["count"]
    spans = [["US", 0, 7278135 - n], ["Europe", 7278135 - n, 9106708 - n], ["Canada", 9106708 - n, 11008367 - n], ["Australia", 11008367 - n, 11822678 - n]]
    meta.update(archiveSpans=spans, archive=spans[-1][2], archiveEU=1828573, archiveRegions={"US": spans[0][2], "Europe": 1828573, "Canada": 1901659, "Australia": 814311},
                reserved=set(), archiveByField={})
    for step in ("assets", "home", "browse", "fields_index", "studio", "account", "how", "about", "contact", "settings", "legal", "not_found"):
        getattr(s, step)()
    s.insights(gazette_all(), [])
    s.opportunities()
    if W.WORLD:
        s.all_patents()
    s.saved()
    s.archive_template()
    s.feeds()
    W.function_config()
    s.catalog(None)
    if live:
        sh = out / "shard"
        sh.mkdir()
        (sh / "a").symlink_to(live / "shard" / "a")
        for kind in "pik":
            (sh / kind).mkdir()
            for f in (live / "shard" / kind).iterdir():
                (sh / kind / f.name).symlink_to(f)
        W._SITE = s
        home = (out / "index.html").read_text()
        picks = re.findall(r'data-id="(US-[^"]+)"', home)[:4] + re.findall(r'/img/p/(US-[^/]+)/', home)[:1]
        for k in sorted({W.shard_of(p) for p in test + picks}):
            for kind in "pik":
                f = sh / kind / f"{k}.bin"
                if f.is_symlink():
                    f.unlink()  # never write through a link into the live build
            W.render_shard((k, [i for i, r in enumerate(rows) if W.shard_of(r["entry"]["id"]) == k]))
    print(f"preview in {out} ({time.time() - t0:.0f}s)")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1].startswith("-"):
        raise SystemExit(__doc__)
    live = arg("--live")
    main(Path(sys.argv[1]).resolve(), Path(live).expanduser().resolve() if live else None,
         arg("--patents", ",".join(TEST)).split(","))
