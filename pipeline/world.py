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
    """Pass 1: records into one temp file per publication year, so pass 2 can number them newest first."""
    shutil.rmtree(TMP, ignore_errors=True)
    TMP.mkdir(parents=True)
    files, n, t0 = {}, 0, time.time()
    for r in records():
        y = (r["p"] or r["f"] or "0000")[:4]
        if y not in files:
            files[y] = open(TMP / f"y{y}.jsonl", "w", encoding="utf-8")
        files[y].write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")
        n += 1
        if n % 5_000_000 == 0:
            print(f"split: {n:,} records ({time.time() - t0:.0f}s)", flush=True)
    for f in files.values():
        f.close()
    print(f"split: {n:,} records in {len(files)} years", flush=True)


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

    for yf in sorted(TMP.glob("y*.jsonl"), reverse=True):  # newest year first
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
        print(f"pack: {yf.stem[1:]} done, {doc:,} docs ({time.time() - t0:.0f}s)", flush=True)
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
        build()
