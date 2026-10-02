#!/usr/bin/env python3
"""Serve a preview folder with caching off and the site's production security headers:
python3 web/dev/serve.py DIR [PORT]

Headers come from DIR/_headers (the "/*" block), so local tests run under the same Content-Security-Policy.
Patent pages, drawings and kit data are read from DIR/shard/ the way web/functions does it on Cloudflare; in a
preview made with --mock (DIR/dev exists) patent pages also get the mock backend and the smoke tests."""
import functools
import gzip
import http.server
import json
import re
import struct
import sys
from pathlib import Path

SHARDS = 2048
ROUTES = [(re.compile(r"^/patents/(US-[A-Z]*(\d{5,11})-[A-Z]\d?)/$"), "p", "text/html; charset=utf-8"),
          (re.compile(r"^/img/p/(US-[A-Z]*(\d{5,11})-[A-Z]\d?)/(\d+)\.png$"), "i", "image/png"),
          (re.compile(r"^/data/p/(US-[A-Z]*(\d{5,11})-[A-Z]\d?)\.json$"), "k", "application/json")]
MOCK = '<script src="/dev/mock-backend.js"></script><script src="/dev/smoke.js"></script>'


def shard_item(root, kind, num, key):
    f = Path(root) / "shard" / kind / f"{int(num) % SHARDS}.bin"
    if not f.exists():
        return None
    b = f.read_bytes()
    n = struct.unpack(">I", b[:4])[0]
    at = json.loads(b[4:4 + n]).get(key)
    return b[4 + n + at[0]:4 + n + at[0] + at[1]] if at else None


def security_headers(root):
    f = Path(root) / "_headers"
    if not f.exists():
        return []
    block = f.read_text().split("\n\n")[0].splitlines()[1:]
    return [tuple(x.strip().split(": ", 1)) for x in block if ": " in x]


class Handler(http.server.SimpleHTTPRequestHandler):
    headers_extra = []

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        for k, v in self.headers_extra:
            self.send_header(k, v)
        super().end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]
        for rx, kind, ctype in ROUTES:
            m = rx.match(path)
            if m:
                key = f"{m.group(1)}/{m.group(3)}" if kind == "i" else m.group(1)
                body = shard_item(self.directory, kind, m.group(2), key)
                if body is None:
                    self.path = "/404.html"
                    return super().do_GET()
                if kind != "i":
                    body = gzip.decompress(body)
                if kind == "p" and (Path(self.directory) / "dev").exists():
                    body = body.replace(b'<script src="/assets/js/config.js"></script>', MOCK.encode() + b'<script src="/assets/js/config.js"></script>', 1)
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
        return super().do_GET()

    def do_PUT(self):  # test hook: the browser can hand a generated file back, e.g. PUT /_out/brief.pdf
        name = self.path.rsplit("/", 1)[-1]
        if not self.path.startswith("/_out/") or not name or "/" in name or name.startswith("."):
            return self.send_error(400)
        out = Path(self.directory) / "_out"
        out.mkdir(exist_ok=True)
        (out / name).write_bytes(self.rfile.read(int(self.headers["Content-Length"])))
        self.send_response(204)
        self.end_headers()


if __name__ == "__main__":
    root = sys.argv[1]
    Handler.headers_extra = security_headers(root)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", int(sys.argv[2]) if len(sys.argv) > 2 else 8766), functools.partial(Handler, directory=root))
    print(f"serving {root} with {len(Handler.headers_extra)} security headers")
    server.serve_forever()
