"""The register: find patents from each source, download their dossiers, and recheck them against USPTO records.

Sources
  lapsed     USPTO Official Gazette notices of patents expired for an unpaid maintenance fee (issues 4-12 months old,
             minus a year of reinstatement notices)
  abandoned  published applications filed 2013-2017 whose family has no patent and no filing in 7+ years (inferred)
  expired    patents filed 1996-2001, whose 20-year term has ended (drug and chemistry classes skipped: term extensions)
Every candidate must also pass the family check: no other US family member may still be in force or pending.
"""
import datetime as dt
import json
import re
import time
import urllib.error
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import patents as P
import uspto
from drawings import shrink_sheet

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"
CURATION = ROOT / "curation.json"
TODAY = dt.date.today()
SOURCES = ("lapsed", "abandoned", "expired")
SHARE = {"lapsed": 0.45, "abandoned": 0.3, "expired": 0.25}
MAX_SHEETS = 8  # drawing sheets kept per patent; the full set is always one click away in the USPTO PDF


# ---------------------------------------------------------------- local store

def curation():
    return json.loads(CURATION.read_text()) if CURATION.exists() else {}


def save_curation(cur):
    CURATION.write_text("{\n" + ",\n".join(f"{json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}" for k, v in cur.items()) + "\n}\n")


def records():
    for p in sorted(RAW.glob("US-*.json")):
        try:
            yield p, json.loads(p.read_text())
        except ValueError:  # being rewritten by a concurrent run
            print("skipped unreadable", p.name)


def listed():
    """The register: patents with a note that is not a skip, plus patents nobody has written a note for yet (those come
    with note None and are shown with their official title and abstract, or only their USPTO record while the bulk
    download is still fetching their text: text_pending)."""
    cur = curation()
    for p, c in records():
        if c["guid"].count("-") != 2 or not c.get("published") or c.get("title", "").upper() == "TEXT NOT AVAILABLE":
            continue  # a placeholder record USPTO sometimes returns: no kind code, date or text
        note = cur.get(c["guid"])
        if note and not note.get("skip"):
            yield p, c, note
        elif note is None and (c.get("abstract") or c.get("text_pending")):
            yield p, c, None


def save(path, c):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(c, indent=1))
    tmp.replace(path)  # atomic, so a concurrent build never reads half a file


def gazette_all():
    """Every cached Gazette issue, with its week number."""
    out = []
    for f in sorted((RAW / "og").glob("week*.json")):
        o = json.loads(f.read_text())
        o.setdefault("week", int(f.stem[4:]))
        out.append(o)
    return out


def lapse_sets(issues):
    lapsed = {x["pn"]: {**x, "week": o["week"], "issue": o["date"]} for o in issues for x in o["lapsed"]}
    reinstated = {pn for o in issues for pn in o["reinstated"]}
    return lapsed, reinstated


def merge_notes(new):
    fields = set(P.FIELDS)
    for k, v in new.items():
        if not v.get("skip"):
            assert v.get("name") and v.get("hook") and 1 <= int(v.get("build", 0)) <= 5, f"incomplete note for {k}"
            assert v.get("ind") in (None, *fields), f"unknown field for {k}: {v.get('ind')}"
    cur = curation()
    cur.update(new)
    save_curation(cur)
    return len(new), len(cur)


def todo(limit=40):
    """The most promising patents still without a note. Bulk downloads list without one, so this is a daily batch."""
    cur = curation()
    rows = sorted((c for _, c in records() if c["guid"] not in cur and not P.armed(c.get("cpc"))), key=P.appeal, reverse=True)[:limit]
    for c in rows:
        yield {"id": c["guid"], "field": c["industry"], "status": c["status"], "title": c["title"], "abstract": c["abstract"][:700]}


# ---------------------------------------------------------------- harvest

def _lapsed_candidates(pp, weeks, only, ages=(120, 365), every_field=False):
    """Maintenance-fee lapses from Gazette issues 4-12 months old (ages, in days), minus every reinstatement in the past
    year. every_field keeps patents outside the named fields, filed under "other"."""
    issues = []
    for wk in range(1, 54):
        try:
            issues.append(uspto.gazette_week(wk, RAW / "og", TODAY))
        except (urllib.error.HTTPError, AttributeError):
            continue
    lapsed_all, reinstated = lapse_sets(issues)
    take = {}
    for o in issues:
        age = (TODAY - dt.date.fromisoformat(o["date"])).days
        if ages[0] <= age <= ages[1] and o["week"] % max(1, 36 // weeks) == 0:
            for x in o["lapsed"]:
                if x["pn"] not in reinstated:
                    take[x["pn"]] = lapsed_all[x["pn"]]
    print(f"{len(take)} lapsed candidates from the Gazette, {len(reinstated)} reinstatements excluded", flush=True)
    cache_f = RAW / "lapsed_meta.json"
    meta = json.loads(cache_f.read_text()) if cache_f.exists() else {}
    todo_ = sorted(pn for pn in take if pn not in meta)
    for i in range(0, len(todo_), 200):  # larger batches are refused
        try:
            for r in pp.search("(" + " ".join(todo_[i:i + 200]) + ").pn.", ["USPAT"], n=200):
                meta[P.number(r["guid"])] = P.bib(r)
        except Exception as e:
            print("metadata batch failed:", e, flush=True)
        if i % 2000 == 0:
            print(f"metadata {min(i + 200, len(todo_))}/{len(todo_)}", flush=True)
            cache_f.write_text(json.dumps(meta))
    cache_f.write_text(json.dumps(meta))
    out = []
    for pn, x in take.items():
        if pn in meta:
            b = dict(meta[pn], status="lapsed", expired=x["expired"], og_week=x["week"], og_date=x["issue"])
            b["industry"] = P.field_of(b["cpc"]) or ("other" if every_field else None)
            if b["industry"] and (not only or b["industry"] in only):
                out.append(b)
    return out, set(lapsed_all), reinstated


def _search_candidates(pp, status, only):
    """Likely-abandoned applications or expired full-term patents, by buildable CPC group."""
    out = []
    for field, groups in P.SEARCH_GROUPS.items():
        if only and field not in only:
            continue
        for g in groups.split():
            if status == "abandoned":
                q, db = f"{g}.cpc. AND @ad>=20130101<=20171231 AND @pd<=20191231", ["US-PGPUB"]
            else:
                q, db = f"{g}.cpc. AND @ad>=19960101<=20011231", ["USPAT"]
            try:
                rows = pp.search(q, db, n=120 if status == "abandoned" else 80, family=True)
            except Exception as e:  # one failed group never stops the harvest
                print("skip", g, e, flush=True)
                continue
            for r in rows:
                b = P.bib(r)
                if not b["filed"]:
                    continue
                if status == "abandoned" and b["filed"] >= "2018-01-01":
                    continue
                if status == "expired" and (not P.full_term_over(b, TODAY) or any(c.startswith(P.EXTENSION_PRONE) for c in b["cpc"])):
                    continue
                b["status"], b["industry"] = status, field
                if status == "expired":
                    b["term20"] = P.term_end(b)
                out.append(b)
        print(f"{status} {field}: {sum(1 for c in out if c['industry'] == field)}", flush=True)
    return out


def harvest(weeks=9, per=6, only=None, sources=SOURCES, resume=False):
    RAW.mkdir(exist_ok=True)
    (RAW / "figs").mkdir(exist_ok=True)
    have = {p.stem for p in RAW.glob("US-*.json")}
    pp = uspto.PatentPublicSearch()
    queue = RAW / "queue.json"
    if resume and queue.exists():
        return fetch_documents(pp, [c for c in json.loads(queue.read_text()) if c["guid"] not in have])
    cands, lapsed, reinstated = [], set(), set()
    if "lapsed" in sources:
        found, lapsed, reinstated = _lapsed_candidates(pp, weeks, only)
        cands += found
    else:
        lapsed, reinstated = (set(s) for s in lapse_sets(gazette_all()))
    for st in ("abandoned", "expired"):
        if st in sources:
            cands += _search_candidates(pp, st, only)

    total = sum(SHARE[s] for s in sources)
    chosen = []
    for field in [k for k in P.FIELDS if not only or k in only]:
        for st in sources:
            pool = sorted((c for c in cands if c["industry"] == field and c["status"] == st and c["guid"] not in have),
                          key=P.appeal, reverse=True)
            chosen += pool[:int(per * SHARE[st] / total * 1.8) + 2]
    fam = families(pp, [c["family"] for c in chosen])
    kept = {}
    for c in chosen:
        members = fam.get(c["family"], [])
        if c["status"] == "abandoned" and any(m["type"] == "USPAT" for m in members):
            continue
        if P.family_clear(members, c, lapsed, reinstated, TODAY):
            c["familySize"] = len({m["guid"] for m in members}) or 1
            c["family_members"] = P.family_entries(members, c, lapsed, TODAY)
            kept.setdefault((c["industry"], c["status"]), []).append(c)
    final = []
    for (field, st), lst in kept.items():
        final += lst[:max(1, round(per * SHARE[st] / total))]
    print(f"{len(final)} patents cleared; fetching text and drawings", flush=True)
    queue.write_text(json.dumps(final))
    fetch_documents(pp, final)


def families(pp, fids):
    out = {}
    fids = sorted({f for f in fids if f})
    for i in range(0, len(fids), 100):
        for r in pp.search("(" + " ".join(map(str, fids[i:i + 100])) + ").fmid.", ["USPAT", "US-PGPUB"], n=1000):
            out.setdefault(r.get("familyIdentifierCur"), []).append(P.bib(r))
    return out


def fetch_documents(pp, final, retry=True):
    """Text and first drawing sheet for each cleared patent. Rate-limited ones get one more try after a pause."""
    failed = []
    for n, c in enumerate(final, 1):
        try:
            c.update(P.record_text(pp.document(c["guid"], c["type"])))
            if not c["abstract"]:
                continue
            c.setdefault("harvested", TODAY.isoformat())
            fig = shrink_sheet(pp.sheet(c["imageLocation"], c["drawings"][0])) if c["drawings"][0] and c["imageLocation"] else None
            if fig:
                (RAW / "figs" / f"{c['guid']}.png").write_bytes(fig[0])
                c["fig"] = [fig[1], fig[2]]
            save(RAW / f"{c['guid']}.json", c)
            print(f"[{n}/{len(final)}] {c['guid']} {c['industry']} {c['status']} {c['title'][:50]}", flush=True)
        except Exception as e:  # one bad document never stops the run
            print(f"[{n}/{len(final)}] {c['guid']} failed: {e}", flush=True)
            failed.append(c)
    if failed and retry:
        print(f"retrying {len(failed)} after a pause", flush=True)
        time.sleep(90)
        fetch_documents(pp, failed, retry=False)


def bulk(minutes=None, workers=4):
    """Every patent the Gazette lists as lapsed in the past year, in every field, that passes the family check.
      1. family check for everything new, 100 families a request; a patent that passes is listed at once from its
         USPTO record (title, owner, dates, classification, family), marked text_pending
      2. the full text of each (claims, description, abstract), fields taken in turn, best first
      3. the first drawing sheet of each, then 4. the rest of its sheets, up to MAX_SHEETS
    A few downloads run side by side, each on its own session and still spaced out; USPTO takes seconds to assemble
    a document, so together they stay well under one request a second. Resumable at every step."""
    stop = time.time() + minutes * 60 if minutes else float("inf")
    left = lambda: time.time() < stop
    local = threading.local()

    def pp():
        if not hasattr(local, "pp"):
            local.pp = uspto.PatentPublicSearch()
        return local.pp

    cur = curation()
    found, lapsed, reinstated = _lapsed_candidates(pp(), 36, None, ages=(0, 372), every_field=True)
    have = {p.stem for p in RAW.glob("US-*.json")}
    failed_f = RAW / "family_failed.json"
    failed = set(json.loads(failed_f.read_text())) if failed_f.exists() else set()

    # 1. family checks
    todo = [c for c in found if c["guid"] not in have and c["guid"] not in cur and c["guid"] not in failed
            and c["guid"].count("-") == 2 and c.get("published")]
    print(f"{len(todo)} lapsed patents to check", flush=True)

    def check(chunk):
        if not left():
            return 0
        try:
            fam = families(pp(), [c["family"] for c in chunk])
        except Exception as e:
            print("family batch failed:", e, flush=True)
            return 0
        n = 0
        for c in chunk:
            try:
                members = fam.get(c["family"], [])
                if not P.family_clear(members, c, lapsed, reinstated, TODAY):
                    failed.add(c["guid"])
                    continue
            except Exception as e:  # one odd record never stops the run
                print(c["guid"], "family check failed:", e, flush=True)
                continue
            first, last = c["drawings"]
            c.update(familySize=len({m["guid"] for m in members}) or 1, family_members=P.family_entries(members, c, lapsed, TODAY),
                     sheet_count=last - first + 1 if first else 0, extra_sheets=0, text_pending=True,
                     harvested=TODAY.isoformat(), enriched=TODAY.isoformat())
            save(RAW / f"{c['guid']}.json", c)
            n += 1
        return n

    with ThreadPoolExecutor(workers) as ex:
        done = 0
        for k, n in enumerate(ex.map(check, [todo[i:i + 100] for i in range(0, len(todo), 100)]), 1):
            done += n
            if k % 10 == 0:
                failed_f.write_text(json.dumps(sorted(failed)))
                print(f"family checks: {k * 100}/{len(todo)}, {done} listed", flush=True)
    failed_f.write_text(json.dumps(sorted(failed)))

    # 2-4. text, first drawing, remaining sheets for every listed lapsed patent still missing them
    def pending(test):
        pools = {}
        for p, c, _ in listed():
            if c["status"] == "lapsed" and test(c):
                pools.setdefault(c["industry"], []).append((p, c))
        for lst in pools.values():
            lst.sort(key=lambda t: P.appeal(t[1]), reverse=True)
        return [lst[i] for i in range(max(map(len, pools.values()), default=0)) for lst in pools.values() if i < len(lst)]

    def text(job):
        p, c = job
        if not left():
            return 0
        try:
            c.update(P.record_text(pp().document(c["guid"], c["type"])))
            c.pop("text_pending", None)
            save(p, c)
            return 1
        except Exception as e:
            print(c["guid"], "text failed:", e, flush=True)
            return 0

    def sheets(job, upto):
        p, c = job
        first, last = c["drawings"]
        try:
            if not c.get("fig"):
                if not left():
                    return 0
                fig = shrink_sheet(pp().sheet(c["imageLocation"], first))
                if not fig:
                    return 0
                (RAW / "figs" / f"{c['guid']}.png").write_bytes(fig[0])
                c["fig"] = [fig[1], fig[2]]
                save(p, c)
                return 1
            extra, want = c.get("extra_sheets") or 0, min(last - first, upto - 1)
            for k in range(extra + 1, want + 1):
                if not left():
                    break
                out = shrink_sheet(pp().sheet(c["imageLocation"], first + k), max_w=520)
                if out:
                    (RAW / "sheets" / f"{c['guid']}-{k}.png").write_bytes(out[0])
                    c["extra_sheets"] = k
            save(p, c)
            return 1
        except Exception as e:
            print(c["guid"], "sheet failed:", e, flush=True)
            return 0

    (RAW / "sheets").mkdir(exist_ok=True)
    steps = [("texts", lambda c: c.get("text_pending"), text),
             ("first drawings", lambda c: not c.get("fig") and c["drawings"][0] and c.get("imageLocation"), lambda j: sheets(j, 1)),
             ("all drawings", lambda c: c.get("fig") and (c.get("extra_sheets") or 0) < min(c["drawings"][1] - c["drawings"][0], MAX_SHEETS - 1),
              lambda j: sheets(j, MAX_SHEETS))]
    def run(step):
        name, test, fn = step
        jobs = pending(test)
        print(f"{name}: {len(jobs)} to fetch", flush=True)
        with ThreadPoolExecutor(workers) as ex:
            for k, n in enumerate(ex.map(fn, jobs), 1):
                if k % 200 == 0:
                    print(f"{name}: {k}/{len(jobs)}", flush=True)

    # texts and first drawings side by side (cards look bare without a drawing), then the remaining sheets
    both = [threading.Thread(target=run, args=(st,)) for st in steps[:2]]
    for t in both:
        t.start()
    for t in both:
        t.join()
    if left():
        run(steps[2])
    print("bulk: done for now", flush=True)


# ---------------------------------------------------------------- archive: every US patent whose term has certainly ended

ARCHIVE = RAW / "archive"
UTILITY = re.compile(r"^US-\d{6,8}-(A|B1|B2)$")
DESIGN = re.compile(r"^US-D\d{4,7}-S\d?$")
APPLICATION = re.compile(r"^US-\d{11}-A\d$")


def term_certainly_over(filed, granted, today=None):
    """True when a US utility patent can no longer be in force, whatever extensions it had. Filed before May 29, 2000:
    no term adjustment exists, so the term ended 20 years from filing, plus at most 5 years of term guarantee or drug
    extension (2025 at the latest). Filed before June 8, 1995: the term is also at least 17 years from grant, so the
    grant must be more than 17 years ago."""
    today = today or TODAY
    if granted and granted < "1976-01-01":
        return True  # the longest term then was 17 years from grant
    if not filed or not granted or filed >= "2000-05-29":
        return False
    return filed >= "1995-06-08" or granted < P.years_ago(today, 17)


def archive(minutes=None, workers=4):
    """Every US patent and published application that can no longer be in force, as compact records in
    raw/archive/<year>.jsonl (title, dates, classification, owner, drawings), in three passes:
      utility    granted 1790-2012 with a term that has certainly ended (term_certainly_over); from 1976 the full-text
                 database one Tuesday at a time, before that the scanned one in seven-day windows (early grant days
                 varied), leaving out pages USPTO never titled ("OCR SCANNED DOCUMENT")
      designs    design patents granted more than 15 years ago (a design lasts 14 years from grant, 15 if filed from
                 May 13, 2015)
      abandoned  applications published 2001-2016 with no patent anywhere in their family and no family filing in
                 7 years: likely abandoned (inferred; every page says so)
    One search per 500 documents, plus one family lookup per 100 applications. Resumable: finished weeks are listed in
    raw/archive/done.json ("S:" and "A:" mark the design and application passes)."""
    stop = time.time() + minutes * 60 if minutes else float("inf")
    ARCHIVE.mkdir(exist_ok=True)
    done_f = ARCHIVE / "done.json"
    done = set(json.loads(done_f.read_text())) if done_f.exists() else set()
    main = {p.stem for p in RAW.glob("US-*.json")}
    lapsed, reinstated = (set(x) for x in lapse_sets(gazette_all()))

    def days(first, last, weekday):
        d = dt.date(last.year, last.month, last.day)
        d -= dt.timedelta(days=(d.weekday() - weekday) % 7)
        while d >= first:
            yield d
            d -= dt.timedelta(days=7)

    tasks = [("", d) for d in days(dt.date(1790, 1, 1), dt.date(2012, 12, 31), 1)]                                # Tuesdays
    tasks += [("S:", d) for d in days(dt.date(1842, 1, 1), dt.date.fromisoformat(P.years_ago(TODAY, 15)), 1)]
    tasks += [("A:", d) for d in days(dt.date(2001, 3, 15), dt.date(2016, 12, 31), 3)]                             # Thursdays
    order = {"": 0, "S:": 1, "A:": 2}
    tasks = [t for t in tasks if t[0] + t[1].isoformat() not in done]
    tasks.sort(key=lambda t: (order[t[0]], t[1].year < 1976, -t[1].toordinal()))
    local, lock = threading.local(), threading.Lock()

    def pp():
        if not hasattr(local, "pp"):
            local.pp = uspto.PatentPublicSearch()
        return local.pp

    def query(q, db):
        rows, total = pp().search(q, [db], n=500, total=True)
        for start in range(500, total, 500):
            rows += pp().search(q, [db], n=500, start=start)
        return rows

    def record(b, kind=""):
        first_, last_ = b["drawings"]
        x = {"id": b["guid"], "t": b["title"], "f": b["filed"], "p": b["published"], "app": b["app"], "cpc": b["cpc"][:6],
             "a": b["assignee"], "i": b["inventors"], "pg": b["pages"], "sh": last_ - first_ + 1 if first_ else 0,
             "loc": b["imageLocation"], "fam": b["family"]}
        if kind:
            x["k"] = kind
        return x

    def titled(b):
        return b["title"] and b["title"].upper() != "OCR SCANNED DOCUMENT"

    def week(task):
        pre, d = task
        if time.time() > stop:
            return 0
        ds = d.strftime("%Y%m%d")
        window = f"@pd>={(d - dt.timedelta(days=6)).strftime('%Y%m%d')}<={ds}"
        db = "USPAT" if d.year >= 1976 else "USOCR"
        out = []
        try:
            if pre == "":
                if d.year >= 1976:
                    cutoff = "@ad<=20000528" if d.isoformat() < P.years_ago(TODAY, 17) else "@ad>=19950608<=20000528"
                    rows = query(f"@pd>={ds}<={ds} AND {cutoff}", db)
                else:
                    rows = query(window, db)
                for r in rows:
                    b = P.bib(r)
                    if UTILITY.match(b["guid"]) and b["guid"] not in main and titled(b) and term_certainly_over(b["filed"], b["published"]):
                        out.append(record(b))
            elif pre == "S:":
                for r in query(f"{window if d.year < 1976 else f'@pd>={ds}<={ds}'} AND S.kd.", db):
                    b = P.bib(r)
                    if DESIGN.match(b["guid"]) and titled(b) and b["published"] and b["published"] < P.years_ago(TODAY, 15):
                        out.append(record(b, "S"))
            else:
                cands = [P.bib(r) for r in query(f"@pd>={ds}<={ds}", "US-PGPUB")]
                cands = [b for b in cands if APPLICATION.match(b["guid"]) and titled(b) and b["filed"] and b["filed"] <= "2016-12-31" and b["family"]]
                for i in range(0, len(cands), 100):
                    fam = families(pp(), [b["family"] for b in cands[i:i + 100]])
                    for b in cands[i:i + 100]:
                        members = fam.get(b["family"], [])
                        if any(m["type"] == "USPAT" for m in members) or not P.family_clear(members, b, lapsed, reinstated, TODAY):
                            continue
                        out.append(record(b, "A"))
        except Exception as e:
            print(pre + d.isoformat(), "failed:", e, flush=True)
            return 0
        with lock:
            with open(ARCHIVE / f"{d.year}.jsonl", "a") as fh:
                fh.write("".join(json.dumps(x, ensure_ascii=False, separators=(",", ":")) + "\n" for x in out))
            done.add(pre + d.isoformat())
            done_f.write_text(json.dumps(sorted(done)))
        return len(out)

    print(f"archive: {len(tasks)} weeks to read", flush=True)
    total = 0
    with ThreadPoolExecutor(workers) as ex:
        for k, n in enumerate(ex.map(week, tasks), 1):
            total += n
            if k % 10 == 0:
                print(f"archive: {k}/{len(tasks)} weeks, {total:,} added", flush=True)
    print(f"archive: {total:,} added", flush=True)


def archived():
    """Every archive record, US and from other offices (europe.py, national.py), newest year first."""
    files = list(ARCHIVE.glob("*.jsonl")) + [f for d in ("europe", "canada", "australia") for f in (RAW / d).glob("*.jsonl")]
    for f in sorted(files, key=lambda f: f.name, reverse=True):
        for line in f.read_text().splitlines():
            if line:
                yield json.loads(line)


# ---------------------------------------------------------------- dossier

def enrich(text_only=False, retry=True, sheet_budget=400):
    """Full dossier for listed patents: all claims, description, citations, family, and up to MAX_SHEETS drawing sheets.
    Patents without a dossier go first. Extra sheets for the rest are topped up at most sheet_budget per run, so the
    daily refresh fills them in gradually without hammering USPTO. text_only re-reads the text of every listed patent."""
    (RAW / "sheets").mkdir(exist_ok=True)
    lapsed, _ = lapse_sets(gazette_all())

    def missing_sheets(c):
        first, last = c["drawings"]
        want = min(max(last - first, 0), MAX_SHEETS - 1) if first else 0
        return want > (c.get("extra_sheets") or 0)

    todo_ = [(p, c, note) for p, c, note in listed() if text_only or not c.get("enriched") or missing_sheets(c)]
    todo_.sort(key=lambda t: (bool(t[1].get("enriched")), t[2] is None))  # new patents first, then ones with a note
    todo_ = [(p, c) for p, c, _ in todo_]
    if not todo_:
        print("every listed patent already has its dossier")
        return
    pp = uspto.PatentPublicSearch()
    fam = families(pp, [c["family"] for _, c in todo_ if not c.get("enriched")])
    failed = False
    for n, (p, c) in enumerate(todo_, 1):
        if sheet_budget <= 0 and c.get("enriched") and not text_only:
            break
        try:
            if text_only or not c.get("claims_all"):  # harvest already read the text of new patents
                c.update(P.record_text(pp.document(c["guid"], c["type"])))
            if c["family"] in fam:
                c["family_members"] = P.family_entries(fam[c["family"]], c, lapsed, TODAY)
            first, last = c["drawings"]
            c["sheet_count"] = last - first + 1 if first else 0
            extra = c.get("extra_sheets") or 0
            want = min(max(last - first, 0), MAX_SHEETS - 1) if first else 0
            try:
                for k in range(extra + 1, want + 1):
                    if sheet_budget <= 0 and c.get("enriched"):
                        break
                    sheet_budget -= 1
                    out = shrink_sheet(pp.sheet(c["imageLocation"], first + k), max_w=520)
                    if out:
                        extra += 1
                        (RAW / "sheets" / f"{c['guid']}-{extra}.png").write_bytes(out[0])
                c.setdefault("enriched", TODAY.isoformat())
            finally:  # keep the sheets already fetched even if a later one fails
                c["extra_sheets"] = extra
                save(p, c)
            print(f"[{n}/{len(todo_)}] {c['guid']} claims={len(c.get('claims_all') or [])} sheets={1 + extra}/{c['sheet_count']}", flush=True)
        except Exception as e:
            print(f"[{n}/{len(todo_)}] {c['guid']} failed: {e}", flush=True)
            failed = True
    if failed and retry and not text_only:
        print("retrying failed dossiers after a pause", flush=True)
        time.sleep(90)
        enrich(retry=False, sheet_budget=sheet_budget)


# ---------------------------------------------------------------- daily check

def verify(family_limit=3000):
    """Recheck the register against current USPTO records. Every listing is checked daily against the newest Gazette
    reinstatement notices and its term; family members are rechecked for family_limit listings per run, the longest
    unchecked first, so the whole register cycles through. Anything no longer clear leaves at the next build."""
    week = TODAY.isocalendar()[1]
    for wk in (week, week - 1 or 52):  # pick up the newest Gazette issue if it is out
        try:
            uspto.gazette_week(wk, RAW / "og", TODAY)
        except Exception as e:
            print(f"Gazette week {wk} unavailable: {e}")
    lapsed_map, reinstated = lapse_sets(gazette_all())
    lapsed = set(lapsed_map)
    rows = list(listed())
    due = sorted(rows, key=lambda t: t[1].get("verified") or "")[:family_limit]
    try:
        fam = families(uspto.PatentPublicSearch(), [c["family"] for _, c, _ in due])
    except Exception as e:  # e.g. Patent Public Search requires sign-in from 2026-11-07
        print(f"Patent Public Search unavailable ({e}); only the Gazette and term checks ran")
        fam = None
    due = {c["guid"] for _, c, _ in due} if fam is not None else set()
    now, bad = dt.datetime.now().astimezone().isoformat(timespec="minutes"), 0
    for p, c, _ in rows:
        why = []
        if c["status"] == "lapsed" and P.number(c["guid"]) in reinstated:
            why.append("reinstated by a late fee payment")
        if c["status"] == "expired" and not P.full_term_over(c, TODAY):
            why.append("a long examination may have extended its term")
        if c["guid"] in due:
            members = fam.get(c["family"], [])
            if c["status"] == "abandoned" and any(m["type"] == "USPAT" for m in members):
                why.append("a patent has since issued in its family")
            if members and not P.family_clear(members, c, lapsed, reinstated, TODAY):
                why.append("a family member may still be in force or pending")
            if members:
                c["family_members"] = P.family_entries(members, c, lapsed, TODAY)
            if c["status"] == "lapsed" and c["guid"].split("-")[1] in lapsed_map and not c.get("og_date"):
                x = lapsed_map[c["guid"].split("-")[1]]
                c["og_week"], c["og_date"] = x["week"], x["issue"]
            c["verified"], c["verify_ok"], c["verify_reason"] = now, not why, "; ".join(why)
        elif why:  # never clear an earlier failure from a partial check, and only rewrite files that changed
            c["verify_ok"], c["verify_reason"] = False, "; ".join(why)
        else:
            bad += c.get("verify_ok") is False
            continue
        bad += bool(why) or c.get("verify_ok") is False
        save(p, c)
    (RAW / "verify.json").write_text(json.dumps({"at": now, "checked": len(rows), "families": len(due), "failed": bad}))
    print(f"verified {len(rows)} patents at {now} ({len(due)} family rechecks); {bad} no longer clear")
