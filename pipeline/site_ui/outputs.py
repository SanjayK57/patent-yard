"""Files that are not pages: assets, the browse catalog, feeds, sitemaps, and the link checker."""

import array
import datetime as dt
import html
import itertools
import json
import re
import shutil
import struct
import zlib

import patents as P
from register import TODAY

from .base import BLOCK, CONFIG, E, SITE, STATIC, STATUS, WEIGHTS, WORLD, day_number, purl, search_words


class Outputs:
    def assets(self):
        shutil.copytree(STATIC, self.dist, dirs_exist_ok=True)
        stamp = zlib.crc32(b"".join(p.read_bytes() for p in sorted((STATIC / "assets").rglob("*")) if p.is_file()))
        self.version = f"{stamp:08x}"
        # the stylesheet is cached for a year, so its name carries its content hash: a page can never get an old copy
        css = (self.dist / "assets" / "site.css").read_bytes()
        self.css = f"/assets/site.{zlib.crc32(css):08x}.css"
        (self.dist / "assets" / "site.css").rename(self.dist / self.css.lstrip("/"))
        cfg = {"siteUrl": SITE, "supabaseUrl": CONFIG.get("supabase_url", ""), "supabaseAnonKey": CONFIG.get("supabase_anon_key", ""), "version": self.version,
               **({"world": {"cards": WORLD["cards"]}} if WORLD else {})}
        (self.dist / "assets" / "js" / "config.js").write_text(f"window.PY_CONFIG = {json.dumps(cfg)};\n")

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
            out = self.dist / "v" / ver / name
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(data)
        m = self.meta
        latest = {"v": ver, "n": n, "block": BLOCK, "weights": WEIGHTS, "fields": fields, "names": {k: v[0] for k, v in P.FIELDS.items()},
                  "count": m["count"], "verified": m.get("verified"), "built": m["built"], "bySource": m["bySource"], "archive": archive}
        (self.dist / "data").mkdir(exist_ok=True)
        (self.dist / "data" / "latest.json").write_text(json.dumps(latest, separators=(",", ":")))
        return len(files), sum(len(v) for v in files.values())

    def feeds(self):
        newest = sorted(self.rows, key=lambda r: (r["added"], r["freed"]), reverse=True)[:50]
        updated = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        entries = "".join(
            f"""<entry><title>{E(r["entry"]["t"])} ({E(r["entry"]["n"])})</title><link href="{SITE}{purl(r["entry"]["id"])}"/><id>{SITE}{purl(r["entry"]["id"])}</id>"""
            f"""<updated>{(r["added"] or TODAY.isoformat())[:10]}T00:00:00Z</updated><summary>{E(STATUS[r["entry"]["st"]] + ". " + r["entry"]["h"])}</summary></entry>"""
            for r in newest)
        (self.dist / "feed.xml").write_text(f'<?xml version="1.0" encoding="utf-8"?>\n<feed xmlns="http://www.w3.org/2005/Atom"><title>New on Patent Yard</title><link href="{SITE}/"/><link rel="self" href="{SITE}/feed.xml"/><id>{SITE}/</id><updated>{updated}</updated>{entries}</feed>\n')

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
            (self.dist / f"sitemap-{k}.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
        items = "".join(f"<sitemap><loc>{SITE}/sitemap-{k}.xml</loc></sitemap>" for k in range(1, maps + 1))
        (self.dist / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{items}</sitemapindex>\n')
        never = "".join(f"Disallow: {p}\n" for p in ("/account/", "/shard/", "/v/", "/tpl/", "/img/p/", "/data/p/", "/api/"))
        engines = "".join(f"User-agent: {b}\n" for b in ("Googlebot", "Bingbot", "Applebot", "DuckDuckBot",  # search engines
                                                          "Google-Extended", "ChatGPT-User", "Claude-User", "Perplexity-User"))  # AI tools reading a page for a person
        (self.dist / "robots.txt").write_text(f"{engines}Crawl-delay: 2\n{never}\nUser-agent: *\nCrawl-delay: 10\n{never}Disallow: /patents/\n\nSitemap: {SITE}/sitemap.xml\n")

    def resolves(self, u):
        """True when an internal address exists: a file in dist, a patent page, a drawing or a patent's kit data."""
        p = html.unescape(u).split("#")[0].split("?")[0]
        m = re.fullmatch(r"/patents/([^/]+)/", p)
        if m:
            return m.group(1) in self.ids or m.group(1) in getattr(self, "world_ids", ())  # All patents pages come from functions/_world.js
        m = re.fullmatch(r"/img/p/([^/]+)/(\d+)\.png", p)
        if m:
            return 1 <= int(m.group(2)) <= self.ids.get(m.group(1), 0)
        m = re.fullmatch(r"/data/p/([^/]+)\.json", p)
        if m:
            return m.group(1) in self.ids
        return (self.dist / p.lstrip("/") / ("index.html" if p.endswith("/") else "")).exists()

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
