#!/usr/bin/env python3
"""Patent Yard data pipeline. Standard library only (Python 3.9+).

  python3 pipeline.py harvest [--per 6] [--only robotics,ai] [--sources lapsed,abandoned,expired] [--resume]
  python3 pipeline.py bulk [--minutes 300]  every lapsed patent that passes the checks, resumable
  python3 pipeline.py europe [--minutes N]   every European patent past its term (EPO linked open data), resumable
  python3 pipeline.py archive [--minutes N]  every US utility patent whose term has certainly ended (1976-), resumable
  python3 pipeline.py publish [--every 120]  rebuild and redeploy the website every N minutes, until stopped
  python3 pipeline.py todo [--limit 40]  the most promising patents still without a note (JSON lines)
  python3 pipeline.py notes < n.json  merge notes: {"US-...": {"name", "hook", "twist", "build", "tags", "ind"} | {"skip": true}}
  python3 pipeline.py enrich [--sheets 400]   full dossier for new patents, then up to N extra drawing sheets for the rest
  python3 pipeline.py verify          recheck every listed patent against current USPTO records
  python3 pipeline.py build           write ../site/data/ (the claude.ai version)
  python3 pipeline.py web             write ../web/dist/ (the public website)
  python3 pipeline.py test            run the checks in test_pipeline.py
"""
import argparse
import json
import os
import sys
import unittest
from pathlib import Path

import register


INDEXNOW_KEY = "b6c815479879568e2b34055b8d9df1c1"  # served at /<key>.txt (web/static) so search engines can check the pings are ours
INDEXNOW_BATCH = 2000   # pages announced per publish; Bing crawls with a 2-second delay (robots.txt), well inside the free Functions limit


def indexnow():
    """Tell Bing, DuckDuckGo and Yandex (IndexNow) about pages not announced before, a batch at a time, so the site gets
    found without an account anywhere. Google doesn't use IndexNow; it reads the sitemap."""
    import re
    import urllib.request
    here = Path(__file__).resolve().parent
    seen_file = here / "raw" / "indexnow.json"
    seen = set(json.loads(seen_file.read_text())) if seen_file.exists() else set()
    urls = []
    for m in sorted((here.parent / "web" / "dist").glob("sitemap-*.xml"), key=lambda p: int(re.sub(r"\D", "", p.name) or 0)):
        urls += [u for u in re.findall(r"<loc>([^<]+)</loc>", m.read_text()) if u not in seen]
    batch = list(dict.fromkeys(urls))[:INDEXNOW_BATCH]
    if not batch:
        return
    body = json.dumps({"host": "patentyard.pages.dev", "key": INDEXNOW_KEY, "keyLocation": f"https://patentyard.pages.dev/{INDEXNOW_KEY}.txt", "urlList": batch}).encode()
    req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body, headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            ok = r.status in (200, 202)
    except Exception as e:
        print("IndexNow ping failed:", e, flush=True)
        return
    if ok:
        seen_file.write_text(json.dumps(sorted(seen | set(batch))))
        print(f"IndexNow: announced {len(batch)} pages", flush=True)


def publish(every):
    """Rebuild and redeploy the website every `every` minutes, so new patents, text and drawings go live without
    waiting for the daily routine. Holds the build lock for build and deploy together, so nothing else rebuilds
    web/dist while it uploads. A failed build is never deployed."""
    import fcntl
    import subprocess
    import time
    here = Path(__file__).resolve().parent
    while True:
        started = time.time()
        with open(here.parent / "web" / ".build.lock", "w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            print(time.strftime("%Y-%m-%d %H:%M"), "building", flush=True)
            env = {**os.environ, "PATENTYARD_LOCK_HELD": "1"}
            if subprocess.run([sys.executable, "-u", "pipeline.py", "web"], cwd=here, env=env).returncode == 0:
                print(time.strftime("%Y-%m-%d %H:%M"), "deploying", flush=True)
                if subprocess.run(["npx", "--yes", "wrangler@4", "pages", "deploy", "dist", "--project-name", "patentyard",
                                   "--branch", "main", "--commit-dirty=true"], cwd=here.parent / "web").returncode == 0:
                    indexnow()
            else:
                print("build failed; the live site is unchanged", flush=True)
        # wait against the wall clock in short steps: time.sleep doesn't count time the Mac is asleep, so one long sleep
        # would push the next publish back by however long the lid was shut
        time.sleep(60)
        while time.time() - started < every * 60:
            time.sleep(60)


def one_copy(cmd):
    """Lets only one copy of a long job run. The daily LaunchAgent (daily.sh) and the daily Claude task both run verify,
    harvest and enrich; two copies at once split USPTO's one-request-a-second allowance (more 429s) and write the
    same files. A second copy says so and exits cleanly. The lock goes away with the process, even if it crashes."""
    import fcntl
    f = open(Path(__file__).resolve().parent / "raw" / f".{cmd}.lock", "w")
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print(f"pipeline.py {cmd} is already running; this copy exits.", flush=True)
        sys.exit(0)
    return f  # held until the process ends


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["harvest", "bulk", "archive", "europe", "publish", "todo", "notes", "enrich", "verify", "build", "web", "test"])
    ap.add_argument("--weeks", type=int, default=9, help="harvest: how many Gazette issues to sample")
    ap.add_argument("--per", type=int, default=6, help="harvest: new patents per field")
    ap.add_argument("--only", help="harvest: comma-separated fields")
    ap.add_argument("--sources", default=",".join(register.SOURCES), help="harvest: comma-separated sources")
    ap.add_argument("--resume", action="store_true", help="harvest: fetch what raw/queue.json still lacks")
    ap.add_argument("--limit", type=int, default=40, help="todo: how many patents to list")
    ap.add_argument("--every", type=int, default=120, help="publish: minutes between rebuilds")
    ap.add_argument("--minutes", type=int, help="bulk: stop after this many minutes")
    ap.add_argument("--text-only", action="store_true", help="enrich: re-read claims and description only")
    ap.add_argument("--sheets", type=int, default=400, help="enrich: most extra drawing sheets to fetch for existing patents")
    a = ap.parse_args()
    if a.cmd in ("harvest", "enrich", "verify", "bulk", "publish"):
        a.lock = one_copy(a.cmd)  # kept on the args so it stays held while the job runs

    if a.cmd == "harvest":
        sources = tuple(s for s in a.sources.split(",") if s in register.SOURCES)
        register.harvest(a.weeks, a.per, set(a.only.split(",")) if a.only else None, sources, a.resume)
    elif a.cmd == "bulk":
        register.bulk(a.minutes)
    elif a.cmd == "publish":
        publish(a.every)
    elif a.cmd == "archive":
        register.archive(a.minutes)
    elif a.cmd == "europe":
        import europe
        europe.run(a.minutes)
    elif a.cmd == "todo":
        for row in register.todo(a.limit):
            print(json.dumps(row, ensure_ascii=False))
    elif a.cmd == "notes":
        merged, total = register.merge_notes(json.load(sys.stdin))
        print(f"{merged} notes merged, {total} total")
    elif a.cmd == "enrich":
        register.enrich(a.text_only, sheet_budget=a.sheets)
    elif a.cmd == "verify":
        register.verify()
    elif a.cmd == "build":
        import build
        build.build()
    elif a.cmd == "web":
        import website
        website.build()
    elif a.cmd == "test":
        suite = unittest.defaultTestLoader.discover(str(Path(__file__).parent), pattern="test_*.py")
        sys.exit(0 if unittest.TextTestRunner(verbosity=1).run(suite).wasSuccessful() else 1)


if __name__ == "__main__":
    main()
