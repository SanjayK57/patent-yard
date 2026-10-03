"""Canadian and Australian patents past their term, from each office's free bulk data (no account):
  Canada     CIPO patent data, open.canada.ca (Open Government Licence - Canada), raw/canada/src
  Australia  IP Australia IPGOD 2022, data.gov.au (CC BY 2.5 AU), raw/australia/src
Each becomes raw/<country>/<year>.<cc>.jsonl in the archive's record format; register.archived() lists them.

The term rules only ever let a patent in once no patent from that filing can still be in force, whatever its status:
  Canada     filed from Oct 1, 1989: 20 years from filing, 22 for drug classes (a certificate of supplementary protection
             adds at most 2). Filed earlier: 17 years from grant.
  Australia  standard: 20 years from the date of patent, which can be up to a year after the earliest filing, so 21; 26 for
             pharmaceutical classes (an extension adds at most 5). Innovation patents 8 years, petty patents 6."""
import collections, csv, datetime as dt, io, json, re, sys, zipfile
from pathlib import Path

RAW = Path(__file__).parent / "raw"
DRUGS = ("A61K", "A61P", "C07", "C12")
csv.field_size_limit(10 ** 8)


def plus(d, years):
    y, m, day = map(int, d[:10].split("-"))
    try:
        return dt.date(y + years, m, day).isoformat()
    except ValueError:  # Feb 29
        return dt.date(y + years, m, 28).isoformat()


def date(s):
    s = (s or "").strip()[:10]
    return s if re.fullmatch(r"(1[89]|20)\d\d-\d\d-\d\d", s) else ""


def name(s):
    """"ICHIKAWA CO LTD" / "ichikawa co ltd" -> "Ichikawa Co Ltd"; mixed case is kept."""
    s = " ".join((s or "").split())
    return s.title() if s and (s.isupper() or s.islower()) else s


def title(s):
    s = " ".join((s or "").split())
    return s[:1].upper() + s[1:].lower() if s.isupper() else s[:1].upper() + s[1:]


def write(country, cc, recs):
    out = RAW / country
    by_year = collections.defaultdict(list)
    for r in recs:
        by_year[r["p"][:4]].append(json.dumps(r, ensure_ascii=False))
    for f in out.glob(f"*.{cc}.jsonl"):
        f.unlink()
    for y, lines in by_year.items():
        (out / f"{y}.{cc}.jsonl").write_text("\n".join(lines) + "\n")
    print(f"{country}: {len(recs):,} records in {len(by_year)} year files", flush=True)


def rows(zips):
    for z in zips:
        with zipfile.ZipFile(z) as zf:
            with zf.open(zf.namelist()[0]) as f:
                r = csv.reader(io.TextIOWrapper(f, "utf-8-sig", errors="replace", newline=""), delimiter="|", quoting=csv.QUOTE_NONE)
                next(r)
                yield from r


# ---------------------------------------------------------------- Canada

def canada_over(f, g, ipc, today):
    if f and f >= "1989-10-01":
        return plus(f, 22 if any(c.startswith(DRUGS) for c in ipc) else 20) < today
    return bool(g) and plus(g, 17) < today


def canada(today=None):
    today = today or dt.date.today().isoformat()
    src = RAW / "canada" / "src"
    main = {}
    for x in rows(sorted(src.glob("PT_main_*.zip"))):
        if len(x) < 22 or not x[0].strip().isdigit():
            continue
        t = x[5].strip()
        if not t or t.upper() in ("N/A", "NULL"):
            continue
        main[int(x[0])] = (date(x[1]), date(x[2]), title(t), (x[21].strip() if x[21].strip() not in ("", "NULL") else x[9].strip()) or "A")
    print(f"canada: {len(main):,} titled patents and applications", flush=True)
    ipc = collections.defaultdict(list)
    for x in rows(sorted(src.glob("PT_IPC_classification_*.zip"))):
        if len(x) >= 15 and x[0].strip().isdigit() and int(x[0]) in main and len(ipc[int(x[0])]) < 6:
            main_g, sub_g = x[12].strip(), x[14].strip()  # IPC C13K 1/02: section, class, subclass, main group, subgroup
            if x[6].strip() and x[8].strip() and x[10].strip():
                ipc[int(x[0])].append(f"{x[6].strip()}{x[8].strip().zfill(2)}{x[10].strip()}" + (f"{int(main_g)}/{sub_g}" if main_g.isdigit() and sub_g else ""))
    keep = {n for n, (f, g, _, _) in main.items() if canada_over(f, g, ipc.get(n, ()), today) and (g or f)}
    owners, inventors = {}, collections.defaultdict(list)
    for x in rows(sorted(src.glob("PT_interested_party_*.zip"))):
        if len(x) < 8 or not x[0].strip().isdigit() or int(x[0]) not in keep:
            continue
        n, role, who = int(x[0]), x[3].strip(), name(x[7])
        if role in ("OWNR", "APPL") and who and (n not in owners or role == "OWNR" and owners[n][0] != "OWNR"):
            owners[n] = (role, who)
        elif role == "INVT" and who and len(inventors[n]) < 3:
            inventors[n].append(who)
    recs = []
    for n in sorted(keep):
        f, g, t, kind = main[n]
        cpcs = ipc.get(n, [])
        recs.append({"id": f"CA-{n}-{re.sub(r'[^A-Z0-9]', '', kind)[:2] or 'A'}", "t": t, "f": f, "p": g or f, "g": g,
                     "te": plus(f, 20) if f and f >= "1989-10-01" else plus(g, 17), "a": owners.get(n, ("", ""))[1],
                     "i": "; ".join(inventors.get(n, [])), "cpc": cpcs, "k": "CA"})
    write("canada", "ca", recs)


# ---------------------------------------------------------------- Australia

def australia_over(kind, f, ipc, today):
    years = {"standard_complete": 26 if any(c.startswith(DRUGS) for c in ipc) else 21, "innovation": 9, "petty": 7}.get(kind)
    return bool(years and f) and plus(f, years) < today


def australia(today=None):
    today = today or dt.date.today().isoformat()
    src = RAW / "australia" / "src"
    read = lambda n: csv.DictReader(open(src / n, encoding="utf-8-sig", errors="replace", newline=""))
    apps = {}
    for x in read("patent-application.csv"):
        if x["ip_right_sub_type"] in ("standard_complete", "innovation", "petty"):
            f = date(x["earliest_filed_date"]) or date(x["enforceable_from_date"]) or date(x["gained_registration_status_date"])
            if f:
                apps[x["application_number"]] = (x["ip_right_sub_type"], f, date(x["gained_registration_status_date"]))
    ipc = collections.defaultdict(list)
    for x in read("patent-application-classification.csv"):
        n = x["application_number"]
        if n in apps and x["classification_system"].startswith("ipc") and len(ipc[n]) < 6:
            code = x["classification"].replace(" ", "")
            if code and code not in ipc[n]:
                (ipc[n].insert(0, code) if x["classification_importance"] == "primary" else ipc[n].append(code))
    keep = {n for n, (kind, f, _) in apps.items() if australia_over(kind, f, ipc.get(n, ()), today)}
    titles = {x["application_number"]: title(x["description_value"]) for x in read("patent-application-description.csv")
              if x["application_number"] in keep and x["description_type"] == "description" and x["description_value"].strip()}
    owners = {}
    for x in read("patent-party-activity.csv"):
        n = x["application_number"]
        if (n in keep and x["party_role_category"] == "applicant" and x["party_role"] in ("applicant", "owner", "patentee") and (n not in owners or x["is_current"] == "True")
                and not re.fullmatch(r"[a-z]\d+", x["party_name"].strip(), re.I)):  # individuals' names are withheld as ids like "I570579"
            owners[n] = name(x["party_name"])
    recs = []
    for n in sorted(keep):
        if n not in titles:
            continue
        kind, f, g = apps[n]
        letter = {"innovation": "I", "petty": "P"}.get(kind) or ("B" if g else "A")
        recs.append({"id": f"AU-{n}-{letter}", "t": titles[n], "f": f, "p": g or f, "g": g, "te": plus(f, {"innovation": 9, "petty": 7}.get(kind, 21)),  # "ended by": the date of patent can be a year after f
                     "a": owners.get(n, ""), "cpc": ipc.get(n, []), "k": "AU"})
    write("australia", "au", recs)


if __name__ == "__main__":
    if sys.argv[1:] == ["test"]:
        assert canada_over("1990-01-01", "", ["F16L1/00"], "2026-10-03") and not canada_over("2006-10-04", "", [], "2026-10-03")
        assert not canada_over("2005-01-01", "", ["A61K31/00"], "2026-10-03") and canada_over("1980-01-01", "2009-01-01", [], "2026-10-03")
        assert not canada_over("1988-01-01", "2010-01-01", [], "2026-10-03") and not canada_over("", "", [], "2026-10-03")
        assert australia_over("standard_complete", "2005-10-01", [], "2026-10-03") and not australia_over("standard_complete", "2006-01-01", [], "2026-10-03")
        assert not australia_over("standard_complete", "2002-01-01", ["A61K9/00"], "2026-10-03") and australia_over("innovation", "2017-01-01", [], "2026-10-03")
        assert not australia_over("provisional", "1990-01-01", [], "2026-10-03")
        assert name("ICHIKAWA CO LTD") == "Ichikawa Co Ltd" and name("McDonald Ltd") == "McDonald Ltd" and title("A MACHINE FOR X") == "A machine for x"
        print("ok")
    else:
        {"canada": canada, "australia": australia}[sys.argv[1]]()
