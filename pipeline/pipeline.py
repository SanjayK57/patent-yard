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
                subprocess.run(["npx", "--yes", "wrangler@4", "pages", "deploy", "dist", "--project-name", "patentyard",
                                "--branch", "main", "--commit-dirty=true"], cwd=here.parent / "web")
            else:
                print("build failed; the live site is unchanged", flush=True)
        time.sleep(max(60, every * 60 - (time.time() - started)))


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
