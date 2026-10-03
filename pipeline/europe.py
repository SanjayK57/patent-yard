"""European patents past their term, from the EPO's Linked open EP data (data.epo.org/linked-data): free, no account,
Creative Commons Attribution 4.0, under the EPO's fair use policy, so at most two queries run at a time.

An EP patent lasts at most 20 years from filing (EPC Art. 63). A supplementary protection certificate can extend one
for a medicine or plant protection product by up to five years and six months more, so patents in those classes wait
25.5 years. Applications filed that long ago are free whether or not they were ever granted.

Records go into raw/europe/<first publication year>.ep.jsonl and are listed the same way
(kind "E"). Progress (batches of publication numbers done) is in raw/europe/done.json."""
import calendar, collections, datetime as dt, json, threading, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ENDPOINT = "https://data.epo.org/linked-data/query"
ARCHIVE = Path(__file__).parent / "raw" / "europe"  # register.archived() reads it with the US archive
DONE = ARCHIVE / "done.json"
BATCH, END = 500, 3_300_000  # past every publication of a 2006 filing, late divisionals and Euro-PCT entries included
SPC = ("A61K", "A61P", "A01N", "A01P", "C07", "C12")  # classes a certificate can extend

QUERY = """PREFIX p: <http://data.epo.org/linked-data/def/patent/>
PREFIX v: <http://www.w3.org/2006/vcard/ns#>
SELECT ?num (SAMPLE(?no) AS ?app) (MIN(?fd) AS ?filed) (MIN(?pd) AS ?published) (SAMPLE(?gd) AS ?granted)
  (GROUP_CONCAT(DISTINCT STRAFTER(STR(?k), "Kind_"); separator=" ") AS ?kinds) (SAMPLE(?t) AS ?title)
  (SAMPLE(?who) AS ?applicant) (GROUP_CONCAT(DISTINCT STRAFTER(STR(?c), "cpc/"); separator=" ") AS ?cpcs) WHERE {
 VALUES ?num { %s }
 ?pub p:publicationNumber ?num ; p:publicationAuthority <http://data.epo.org/linked-data/id/st3/EP> ;
      p:publicationKind ?k ; p:publicationDate ?pd ; p:application ?a .
 ?a p:filingDate ?fd ; p:applicationNumber ?no . OPTIONAL { ?a p:grantDate ?gd }
 OPTIONAL { ?pub p:titleOfInvention ?t FILTER(langMatches(lang(?t), "en")) }
 OPTIONAL { ?pub p:applicantVC/v:fn ?who }
 OPTIONAL { ?a p:classificationCPCInventive ?c }
} GROUP BY ?num"""


def years_after(d, years):
    y, m, day = map(int, d.split("-"))
    whole, months = int(years), round((years % 1) * 12)
    y, m = y + whole + (m - 1 + months) // 12, (m - 1 + months) % 12 + 1
    return dt.date(y, m, min(day, calendar.monthrange(y, m)[1])).isoformat()


def term_over(filed, cpcs, today):
    """True once no EP patent from this filing can still be in force."""
    return years_after(filed, 25.5 if any(c.startswith(SPC) for c in cpcs) else 20) < today


def main_first(cpcs):
    """CPC codes with the patent's dominant subclass first, so field_of reads its main subject."""
    top = collections.Counter(c[:4] for c in cpcs).most_common(1)
    return sorted(cpcs, key=lambda c: c[:4] != top[0][0]) if top else cpcs


def record(b, today):
    """One archive record from a query row, or None when the patent may still be in force or has no usable title."""
    g = lambda k: b.get(k, {}).get("value", "")
    cpcs = main_first([c.replace("-", "/", 1) for c in g("cpcs").split()])
    filed, kinds, title = g("filed"), g("kinds").split(), " ".join(g("title").split())
    if not filed or not title or not term_over(filed, cpcs, today):
        return None
    kind = next((k for k in ("B1", "B2", "B3", "A1", "A2", "A3", "A4") if k in kinds), kinds[0] if kinds else "A1")
    return {"id": f"EP-{g('num')}-{kind}", "t": title, "f": filed, "p": g("published"), "g": g("granted"),
            "a": " ".join(g("applicant").split()), "cpc": cpcs[:6], "app": g("app"), "k": "E"}


def query(start):
    nums = " ".join(f'"{n:07d}"' for n in range(start, start + BATCH))
    body = urllib.parse.urlencode({"query": QUERY % nums}).encode()
    req = urllib.request.Request(ENDPOINT, body, {"Accept": "application/sparql-results+json", "User-Agent": "PatentYard/1.0 (patentyard.pages.dev)"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.load(r)["results"]["bindings"]
        except Exception as e:  # busy or timed out: back off, then try again
            print(f"  {start}: {e}; retrying", flush=True)
            time.sleep(20 * (attempt + 1))
    raise RuntimeError(f"batch {start} kept failing")


def run(minutes=None, workers=2):
    """Download every EP publication number up to END in batches, skipping batches already done."""
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    done = set(json.loads(DONE.read_text())) if DONE.exists() else set()
    todo = [s for s in range(1, END, BATCH) if s not in done]
    today, lock, stop = dt.date.today().isoformat(), threading.Lock(), time.time() + minutes * 60 if minutes else None
    kept = [0]
    print(f"EP: {len(todo)} batches of {BATCH} to go", flush=True)

    def one(start):
        if stop and time.time() > stop:
            return
        rows = query(start)
        recs = [r for r in (record(b, today) for b in rows) if r]
        with lock:
            by_year = collections.defaultdict(list)
            for r in recs:
                by_year[r["p"][:4]].append(json.dumps(r, ensure_ascii=False))
            for y, lines in by_year.items():
                with open(ARCHIVE / f"{y}.ep.jsonl", "a") as f:
                    f.write("\n".join(lines) + "\n")
            done.add(start)
            kept[0] += len(recs)
            if len(done) % 20 == 0:
                DONE.write_text(json.dumps(sorted(done)))
                print(f"EP: {len(done)} batches done, up to {start:,}; {kept[0]:,} kept this run", flush=True)
        time.sleep(1)  # fair use

    try:
        with ThreadPoolExecutor(workers) as pool:
            list(pool.map(one, todo))
    finally:
        DONE.write_text(json.dumps(sorted(done)))
        print(f"EP: done for now; {kept[0]:,} kept this run", flush=True)


if __name__ == "__main__":
    today = "2026-10-02"
    assert years_after("2006-10-01", 20) == "2026-10-01" and years_after("2001-03-31", 25.5) == "2026-09-30"
    assert term_over("2006-10-01", ["F16L1/00"], today) and not term_over("2006-10-03", ["F16L1/00"], today)
    assert not term_over("2003-01-01", ["A61K31/00"], today) and term_over("2001-01-01", ["A61K31/00"], today)
    r = record({"num": {"value": "0500000"}, "filed": {"value": "1992-02-14"}, "published": {"value": "1992-08-26"},
                "kinds": {"value": "A1 B1"}, "title": {"value": "Spray  gun"}, "cpcs": {"value": "B05B7-12 B29B7-74 B29B7-32"}}, today)
    assert r["id"] == "EP-0500000-B1" and r["t"] == "Spray gun" and r["cpc"][0].startswith("B29B7/"), r
    print("ok")
