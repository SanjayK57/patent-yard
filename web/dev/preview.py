#!/usr/bin/env python3
"""Local copy of the website for testing: python3 web/dev/preview.py OUT_DIR [--mock]

Copies web/dist to OUT_DIR. With --mock, every page also loads dev/mock-backend.js (accounts and reservations
without Supabase) and dev/smoke.js (run `await runSuite("home")` etc. in the console).
Serve OUT_DIR with any static server, e.g. python3 -m http.server 8766 --directory OUT_DIR
"""
import shutil
import sys
from pathlib import Path

WEB = Path(__file__).resolve().parent.parent


def main(out, mock):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for old in out.iterdir():  # empty it in place, so a server already running in it keeps working
        shutil.rmtree(old) if old.is_dir() else old.unlink()
    shutil.copytree(WEB / "dist", out, dirs_exist_ok=True)
    if mock:
        (out / "dev").mkdir()
        for f in ("mock-backend.js", "smoke.js"):
            shutil.copy(WEB / "dev" / f, out / "dev" / f)
        tag = '<script src="/dev/mock-backend.js"></script><script src="/dev/smoke.js"></script>'
        for page in out.rglob("*.html"):
            t = page.read_text()
            page.write_text(t.replace('<script src="/assets/js/config.js"></script>', tag + '<script src="/assets/js/config.js"></script>', 1))
    print(f"preview written to {out}{' (mock backend)' if mock else ''}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "preview", "--mock" in sys.argv)
