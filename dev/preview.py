#!/usr/bin/env python3
"""Build a local preview of the site: python3 dev/preview.py OUT_DIR

  OUT_DIR/index.html   the page wrapped in the same skeleton claude.ai adds (no runtime: capabilities stay off)
  OUT_DIR/test.html    the page plus dev/mock-runtime.js (signed-in user, database, canned AI) and dev/smoke.js;
                       run `await runSmoke()` in its console to click through every feature
  OUT_DIR/data/        copied from site/data

Serve OUT_DIR with any static server, e.g. python3 -m http.server 8765 --directory OUT_DIR
"""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEAD = ('<!doctype html><html><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '<style>:root{color-scheme:light}img{max-width:100%}[hidden]{display:none!important}</style>{extra}</head><body>')


def main(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    data = out / "data"
    if data.exists():
        shutil.rmtree(data)
    shutil.copytree(ROOT / "site" / "data", data)
    page = (ROOT / "site" / "index.html").read_text()
    mock = (ROOT / "dev" / "mock-runtime.js").read_text()
    shutil.copy(ROOT / "dev" / "smoke.js", out / "smoke.js")
    (out / "index.html").write_text(HEAD.replace("{extra}", "") + page + "</body></html>")
    (out / "test.html").write_text(HEAD.replace("{extra}", f'<script>{mock}</script><script src="smoke.js"></script>') + page + "</body></html>")
    print(f"preview written to {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "preview")
