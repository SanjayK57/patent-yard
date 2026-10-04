"""All patents: every patent application worldwide from Google Patents Public Data (BigQuery
patents-public-data.patents.publications, CC BY 4.0), exported by export_world.sh to raw/world/parts/*.json.gz (query: world.sql, run into patentyard.world).

Cloudflare Pages serves only whole files (no byte ranges) and at most 20,000 files of 25 MiB per project, so the
120M+ records are numbered newest first and packed into files that a Pages Function slices without parsing:
  c/<n>.bin  card text for docs n*PER .. n*PER+PER-1      (web/world/cards: the browse and search lists)
  d/<n>.bin  full record as raw-deflated JSON, same docs (web/world/details: the patent page)
  s/<n>.bin  search: word -> docs, for the words whose crc32 % BUCKETS is n (gzip; the browser reads these); a word in
             more than CAP docs keeps only the newest CAP, which are the ones a newest-first search shows
  x/<n>.bin  id index: sha256("CC-NUMBER") -> doc, sorted, so a number finds its patent with or without a kind code
A .bin of records is: uint32 count, uint32 offsets[count + 1], then the records back to back.

  python3 world.py build       # raw/world/parts -> web/world (about 2 hours; disk-backed, so memory stays small)
  python3 world.py filters     # country / past-term filter lists from the built cards (minutes)
  python3 world.py free_index  # search index over past-term patents only, from the built cards (about 15 minutes)
  python3 world.py stats       # All patents in numbers for the Insights page -> web/world/stats.json
  python3 world.py deploy      # upload web/world/cards and web/world/details to their Pages projects, then write
                               # web/world/live.json, which turns All patents on in the next website build
"""
import array, collections, datetime as dt, gzip, hashlib, json, os, re, shutil, struct, sys, time, zlib
from pathlib import Path

import patents as P
from website import search_words

ROOT = Path(__file__).resolve().parent
PARTS, TMP = ROOT / "raw" / "world" / "parts", Path(os.environ.get("WORLD_TMP", ROOT / "raw" / "world" / "tmp"))
OUT = Path(os.environ.get("WORLD_OUT", ROOT.parent / "web" / "world"))
LIMIT = int(os.environ.get("WORLD_PARTS", 0)) or None  # a trial run on the first few export files
PER, BUCKETS, IDS, CAP = 8192, 2048, 2048, 250_000  # CAP: a common word keeps its newest matches only
FIELDS = list(P.FIELDS)
DRUGS = ("A61K", "A61P", "A01N", "A01P", "C07", "C12")
FREE, GRANTED = 1, 2  # card flags


def day(s):
    return f"{s[:4]}-{s[4:6]}-{s[6:8]}" if s and len(s) == 8 else ""


def past_term(f, cpcs, today):
    """True when no patent from a filing this old can still be in force anywhere: 20 years from filing, plus up to
    five and a half for the medicine and crop-protection classes that can get an extension."""
    if not f:
        return False
    y = int(f[:4]) + (26 if any(c.startswith(DRUGS) for c in cpcs) else 20)
    return f"{y}{f[4:]}" < today


def tidy(s, n, name=False):
    s = " ".join(str(s or "").split())
    if s.isupper() or name and s.islower():
        s = s.title() if name else s.capitalize()
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + " …"


def records():
    """Every exported record with a title, as (date, id, card fields, detail)."""
    today = dt.date.today().strftime("%Y%m%d")
    for part in sorted(PARTS.glob("*.json.gz"))[:LIMIT]:
        with gzip.open(part, "rt", encoding="utf-8") as f:
            for line in f:
                x = json.loads(line)
                t = tidy(x.get("t"), 200)
                if not t or not x.get("pn"):
                    continue
                cpcs = list(dict.fromkeys((x.get("cpc") or "").split()))[:4]
                free = past_term(x.get("f") or x.get("p"), cpcs, today)  # a publication comes after its filing
                yield {"pn": x["pn"], "t": t, "tl": x.get("tl") or "", "a": tidy(x.get("a"), 80, True), "i": tidy(x.get("i"), 60, True),
                       "f": day(x.get("f")), "p": day(x.get("p")), "g": day(x.get("g")), "pr": day(x.get("pr")),
                       "fam": x.get("fam") or "", "app": x.get("app") or "", "kind": x.get("kind") or "", "cc": x.get("cc") or "",
                       "cpc": cpcs, "ab": tidy(x.get("ab"), 330), "ind": P.field_of(cpcs) or "other", "free": free}


def split():
    """Pass 1: records into one temp file per publication month, so pass 2 can number them newest first a month at a
    time (a year of recent patents is millions of records; a month fits easily in memory)."""
    shutil.rmtree(TMP, ignore_errors=True)
    TMP.mkdir(parents=True)
    files, n, t0 = {}, 0, time.time()
    for r in records():
        y = (r["p"] or r["f"] or "0000-00").replace("-", "")[:6]
        if y not in files:
            files[y] = open(TMP / f"y{y}.jsonl", "w", encoding="utf-8")
        files[y].write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")
        n += 1
        if n % 5_000_000 == 0:
            print(f"split: {n:,} records ({time.time() - t0:.0f}s)", flush=True)
    for f in files.values():
        f.close()
    print(f"split: {n:,} records in {len(files)} months", flush=True)


def number_key(pn):
    """"CN-112345678-A" -> sha256 of "CN-112345678" as (bucket, 32-bit key)."""
    h = hashlib.sha256(pn.rsplit("-", 1)[0].encode()).digest()
    return int.from_bytes(h[:2], "big") % IDS, int.from_bytes(h[2:6], "big")


def deflate(s):
    c = zlib.compressobj(6, zlib.DEFLATED, -15)  # raw deflate: the Function inflates one record with DecompressionStream
    return c.compress(s.encode("utf-8")) + c.flush()


def pack(items):
    body = [s if isinstance(s, bytes) else s.encode("utf-8") for s in items]
    offs = [0]
    for b in body:
        offs.append(offs[-1] + len(b))
    return struct.pack(f"<{len(body) + 2}I", len(body), *offs) + b"".join(body)


def build():
    t0 = time.time()
    split()
    shutil.rmtree(OUT, ignore_errors=True)
    for d in ("cards/c", "details/d", "cards/s", "details/x"):
        (OUT / d).mkdir(parents=True)
    words = [open(TMP / f"w{k}.txt", "w", encoding="utf-8") for k in range(BUCKETS)]
    ids = [array.array("Q") for _ in range(IDS)]
    stats = collections.Counter()
    doc, cards, details = 0, [], []

    def flush():
        n = (doc - 1) // PER
        (OUT / "cards" / "c" / f"{n}.bin").write_bytes(pack(cards))
        (OUT / "details" / "d" / f"{n}.bin").write_bytes(pack(details))
        cards.clear()
        details.clear()

    for yf in sorted(TMP.glob("y*.jsonl"), reverse=True):  # newest month first
        rs = [json.loads(line) for line in open(yf, encoding="utf-8")]
        rs.sort(key=lambda r: (r["p"] or r["f"], r["pn"]), reverse=True)
        for r in rs:
            flags = (FREE if r["free"] else 0) | (GRANTED if r["g"] else 0)
            cards.append("\t".join((r["pn"], r["t"], r["a"], (r["p"] or r["f"]).replace("-", ""), r["cc"], r["kind"], str(flags), str(FIELDS.index(r["ind"])))))
            details.append(deflate(json.dumps(r, ensure_ascii=False, separators=(",", ":"))))
            for w in set(search_words(r["t"])) | set(search_words(r["a"])):
                words[zlib.crc32(w.encode()) % BUCKETS].write(f"{w} {doc}\n")
            b, key = number_key(r["pn"])
            ids[b].append(key << 32 | doc)
            stats[r["cc"]] += 1
            stats["free"] += r["free"]
            doc += 1
            if doc % PER == 0:
                flush()
        if yf.stem.endswith("01") or yf.stem == "y000000":
            print(f"pack: {yf.stem[1:5]} done, {doc:,} docs ({time.time() - t0:.0f}s)", flush=True)
    if cards:
        flush()
    for f in words:
        f.close()

    # id index: sorted (key, doc) pairs; the Function binary-searches the key and checks the record's id
    for k, a in enumerate(ids):
        (OUT / "details" / "x" / f"{k}.bin").write_bytes(array.array("Q", sorted(a)).tobytes())
    del ids

    # search: per bucket, word -> doc steps as varints, [offset, length, docs with the word, 1 if cut to the newest CAP]
    for k in range(BUCKETS):
        post = collections.defaultdict(list)
        with open(TMP / f"w{k}.txt", encoding="utf-8") as f:
            for line in f:
                w, d = line.split()
                post[w].append(int(d))
        head, blob = {}, bytearray()
        for w, df in sorted((w, len(ds)) for w, ds in post.items()):
            start, prev = len(blob), 0
            for d in post[w][:CAP]:  # docs arrive in increasing order, newest first
                v = d - prev
                prev = d
                while v >= 128:
                    blob.append(v & 127 | 128)
                    v >>= 7
                blob.append(v)
            head[w] = [start, len(blob) - start, df, int(df > CAP)]
        h = json.dumps(head, separators=(",", ":")).encode()
        (OUT / "cards" / "s" / f"{k}.bin").write_bytes(gzip.compress(struct.pack("<I", len(h)) + h + bytes(blob), 6, mtime=0))
        os.remove(TMP / f"w{k}.txt")

    meta = {"n": doc, "per": PER, "buckets": BUCKETS, "ids": IDS, "cap": CAP, "stop": [], "free": stats.pop("free"),
            "countries": dict(stats.most_common()), "built": dt.datetime.now().astimezone().isoformat(timespec="minutes")}
    for d in ("cards", "details"):
        (OUT / d / "meta.json").write_text(json.dumps(meta))
        (OUT / d / "_headers").write_text("/*\n  Access-Control-Allow-Origin: *\n  Cache-Control: public, max-age=86400\n  X-Robots-Tag: noindex\n")
    print(f"world: {doc:,} docs, {meta['free']:,} past their term ({time.time() - t0:.0f}s)", flush=True)


def filters():
    """Filter lists for All patents, read from the card packs (no export needed): for each country, every country's
    patents past their term, and all patents past their term, the newest CAP docs as gzip varint steps in
    cards/k/<key>.bin ("KR", "KR-free", "all-free"), with k/index.json {key: [docs in total, 1 if cut to CAP]}.
    The browser intersects them with search words, so a country filter works without a query too."""
    t0, lists, totals = time.time(), collections.defaultdict(lambda: array.array("I")), collections.Counter()
    packs = sorted((OUT / "cards" / "c").glob("*.bin"), key=lambda f: int(f.stem))
    for f in packs:
        b = f.read_bytes()
        n = struct.unpack_from("<I", b)[0]
        offs, base, first = struct.unpack_from(f"<{n + 1}I", b, 4), 4 + 4 * (n + 1), int(f.stem) * PER
        for i in range(n):
            parts = b[base + offs[i]:base + offs[i + 1]].split(b"\t")
            cc, free = parts[4].decode(), int(parts[6]) & FREE
            for key in ((cc, f"{cc}-free", "all-free") if free else (cc,)):
                totals[key] += 1
                if len(lists[key]) < CAP:
                    lists[key].append(first + i)
        if int(f.stem) % 1000 == 999:
            print(f"filters: {int(f.stem) + 1}/{len(packs)} packs ({time.time() - t0:.0f}s)", flush=True)
    out = OUT / "cards" / "k"
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir()
    for key, docs in lists.items():
        blob, prev = bytearray(), 0
        for d in docs:
            v, prev = d - prev, d
            while v >= 128:
                blob.append(v & 127 | 128)
                v >>= 7
            blob.append(v)
        (out / f"{key}.bin").write_bytes(gzip.compress(bytes(blob), 6, mtime=0))
    (out / "index.json").write_text(json.dumps({k: [totals[k], int(totals[k] > CAP)] for k in sorted(lists)}))
    print(f"filters: {len(lists)} lists ({time.time() - t0:.0f}s)", flush=True)


def free_index():
    """A second search index, cards/f/<bucket>.bin (same format as s/), over the patents past their term only: in s/ a
    common word keeps its newest CAP docs, all recent, so "past their term" plus a common word would find nothing.
    Built from the card packs (titles and owners), the same words world.py build indexes."""
    t0, post = time.time(), {}
    packs = sorted((OUT / "cards" / "c").glob("*.bin"), key=lambda f: int(f.stem))
    for f in packs:
        b = f.read_bytes()
        n = struct.unpack_from("<I", b)[0]
        offs, base, first = struct.unpack_from(f"<{n + 1}I", b, 4), 4 + 4 * (n + 1), int(f.stem) * PER
        for i in range(n):
            parts = b[base + offs[i]:base + offs[i + 1]].decode("utf-8").split("\t")
            if not int(parts[6]) & FREE:
                continue
            for w in set(search_words(parts[1])) | set(search_words(parts[2])):
                a = post.get(w)
                if a is None:
                    a = post[w] = [0, array.array("I")]
                a[0] += 1
                if len(a[1]) < CAP:
                    a[1].append(first + i)
        if int(f.stem) % 1000 == 999:
            print(f"free index: {int(f.stem) + 1}/{len(packs)} packs, {len(post):,} words ({time.time() - t0:.0f}s)", flush=True)
    out = OUT / "cards" / "f"
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir()
    buckets = [[] for _ in range(BUCKETS)]
    for w in post:
        buckets[zlib.crc32(w.encode()) % BUCKETS].append(w)
    for k, ws in enumerate(buckets):
        head, blob = {}, bytearray()
        for w in sorted(ws):
            df, docs = post[w]
            start, prev = len(blob), 0
            for d in docs:
                v, prev = d - prev, d
                while v >= 128:
                    blob.append(v & 127 | 128)
                    v >>= 7
                blob.append(v)
            head[w] = [start, len(blob) - start, df, int(df > CAP)]
        h = json.dumps(head, separators=(",", ":")).encode()
        (out / f"{k}.bin").write_bytes(gzip.compress(struct.pack("<I", len(h)) + h + bytes(blob), 6, mtime=0))
    print(f"free index: {len(post):,} words in {BUCKETS} files ({time.time() - t0:.0f}s)", flush=True)


HOSTS = {"cards": "patentyard-cards", "details": "patentyard-details"}


def stats():
    """All patents in numbers for the Insights page, read from the card packs: records by office (and how many are
    past their term), by year published, by field, granted, and the biggest owners. -> web/world/stats.json"""
    from website import owner_key
    t0, packs = time.time(), sorted((OUT / "cards" / "c").glob("*.bin"), key=lambda f: int(f.stem))
    cc, free, years, fields, owners = (collections.Counter() for _ in range(5))
    spell, granted = collections.defaultdict(collections.Counter), 0
    for j, f in enumerate(packs):
        b = f.read_bytes()
        n = struct.unpack_from("<I", b)[0]
        offs, base = struct.unpack_from(f"<{n + 1}I", b, 4), 4 + 4 * (n + 1)
        for i in range(n):
            pn, _, a, day_, c, _, flags, ind = b[base + offs[i]:base + offs[i + 1]].decode().split("\t")
            flags = int(flags)
            cc[c] += 1
            free[c] += flags & FREE
            granted += bool(flags & GRANTED)
            years[day_[:4]] += 1
            fields[FIELDS[int(ind)]] += 1
            if a:
                k = owner_key(a)
                owners[k] += 1
                spell[k][a] += 1
        # ponytail: lossy count, owners under 50 records are dropped every 200 packs (at most ~3,700 lost per owner,
        # against 100,000+ for the top ones); keep exact counts if a full owner table is ever needed
        if j % 200 == 199:
            for k in [k for k, v in owners.items() if v < 50]:
                del owners[k], spell[k]
            print(f"stats: {j + 1}/{len(packs)} packs ({time.time() - t0:.0f}s)", flush=True)
    top = [[next((o for o, _ in spell[k].most_common() if not o.isupper()), spell[k].most_common(1)[0][0]), v] for k, v in owners.most_common(15)]
    out = {"n": sum(cc.values()), "free": sum(free.values()), "granted": granted, "countries": {k: [v, free[k]] for k, v in cc.most_common()},
           "years": dict(sorted(years.items())), "fields": dict(fields.most_common()), "owners": top}
    (OUT / "stats.json").write_text(json.dumps(out, ensure_ascii=False))
    print(f"stats: {out['n']:,} records, {len(cc)} offices ({time.time() - t0:.0f}s)", flush=True)


def deploy():
    import subprocess
    for d, project in HOSTS.items():
        n = sum(1 for _ in (OUT / d).rglob("*"))
        assert n < 20000, f"{d}: {n} files, over the Pages limit"
        subprocess.run(["npx", "--yes", "wrangler@4", "pages", "deploy", str(OUT / d), "--project-name", project, "--branch", "main",
                        "--commit-dirty=true"], check=True, cwd=OUT)  # not web/: its functions/ would ride along
    meta = json.loads((OUT / "cards" / "meta.json").read_text())
    live = {**{d: f"https://{p}.pages.dev" for d, p in HOSTS.items()}, **{k: meta[k] for k in ("n", "per", "ids", "buckets", "free")}}
    (OUT / "live.json").write_text(json.dumps(live, indent=1))
    print("world: live", live, flush=True)


if __name__ == "__main__":
    if sys.argv[1:] == ["test"]:
        assert past_term("19990101", [], "20261003") and not past_term("20070101", [], "20261003")
        assert not past_term("20030101", ["A61K31/00"], "20261003") and past_term("19990101", ["A61K31/00"], "20261003")
        assert tidy("A VERY LOUD TITLE", 50) == "A very loud title" and tidy("x " * 200, 10).endswith("…")
        assert tidy("UNIV DALIAN MEDICAL", 80, True) == "Univ Dalian Medical" and tidy("fang linlin", 60, True) == "Fang Linlin"
        blob = pack(["ab", "", "çd"])
        n = struct.unpack_from("<I", blob)[0]
        offs = struct.unpack_from(f"<{n + 1}I", blob, 4)
        data = blob[4 + 4 * (n + 1):]
        assert [data[offs[i]:offs[i + 1]].decode() for i in range(n)] == ["ab", "", "çd"]
        assert zlib.decompress(deflate("héllo"), -15).decode() == "héllo" and number_key("CN-1-A") == number_key("CN-1-B")
        print("ok")
    else:
        {"build": build, "deploy": deploy, "filters": filters, "free_index": free_index, "stats": stats}[sys.argv[1]]()
