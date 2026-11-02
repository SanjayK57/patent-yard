"""The public website: web/dist, a static site for Cloudflare Pages (or any static host).

Every page is plain HTML, so it loads fast, works without JavaScript and can be indexed. JavaScript in
web/static/assets/js adds search and filters, the drawing viewer, accounts and reservations (Supabase) and the
"Reinvent with Claude" kit, which writes a prompt and a PDF brief for the visitor's own Claude.

This module collects the data and runs the build: the archive, the shard files and the swap into web/dist.
What the pages look like lives in site_ui/ (one module per page); see docs/DEVELOPING.md.

  python3 pipeline.py web     builds web/dist from the same records as the claude.ai build
"""
import array
import collections
import fcntl
import gzip
import json
import multiprocessing
import os
import re
import shutil
import struct
import time
import urllib.request
import zlib

import patents as P
from build import collect, dossier
from register import TODAY, archived, gazette_all
from site_ui import Site
from site_ui.base import CONFIG, SITE, STATIC, WEB, WORLD, add_years, day_number, owner_key, purl, search_words  # noqa: F401  (owner_key, search_words: world.py)

DIST = WEB / "dist"
SHARDS = 1024  # patent pages, drawings, kit data and archive records are packed into this many files each (web/functions/_lib.js); fewer files keeps the site under Cloudflare Pages' 20,000
ARCH_BLOCK, ARCH_BUCKETS = 1536, 1024  # the archive: card text per file, search index files (a free site holds 20,000 files)
ARCH_KEYS = ("id", "n", "t", "f", "p", "te", "a", "i", "ind", "cpc", "app", "pg", "sh", "k", "g", "ab")  # k: "" utility, S design, A application, E/CA/AU other offices
REGIONS = {"E": "Europe", "CA": "Canada", "AU": "Australia"}  # archive kinds from other offices (functions/_archive.js REGIONS)
SPAN_ORDER = ["US", "Europe", "Canada", "Australia"]  # the archive is ordered by region, so browse filters one by its index range


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
    """Archive patents not already in the register, newest first, as light (id, title, owner, field index, year, kind,
    drawing sheets) tuples. The full records (ARCH_KEYS) go straight to ARCH_TMP for write_archive, so millions of them never sit in
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
        out.append((pid, t, a, fields.index(field), int(x["p"][:4]), k, x.get("sh") or 0))
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
    global DIST
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
    s = Site(rows, meta, DIST)
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
