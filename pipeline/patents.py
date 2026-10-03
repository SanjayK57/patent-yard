"""Patent records: fields, parsing of USPTO text, and the rules that decide whether a patent is free to use."""
import datetime as dt
import html
import re

# Longest CPC prefix wins, so G06T7 (image analysis) lands in AI though G06T is software, and C12M (lab apparatus)
# in biotech though C is chemistry. Fields are judged by the first (main) classification of a patent.
FIELDS = {
    "software":    ("Software & Apps", "G06F G06Q G06T H04L67 H04L51 H04W4 G09B G16"),
    "ai":          ("AI & Machine Learning", "G06N G06V G06T7 G10L G06F40 G06F18"),
    "medical":     ("Medical Devices", "A61B A61M A61F A61H A61G A61N A61C A61J A61L G16H"),
    "electronics": ("Hardware & Electronics", "H01 H03 H04R H04S H04B H05 G06F1 G01 G05F G06K G07C G08 G11 H04M"),
    "imaging":     ("Cameras, Displays & Optics", "H04N G02 G03 G09G"),
    "telecom":     ("Telecom & Networks", "H04L H04W H04J H04Q H04H"),
    "chips":       ("Chips & Semiconductors", "H10 H01L B81"),
    "industrial":  ("Industrial Equipment", "B01 B02 B03 B04 B05 B06 B07 B08 B09 B21 B22 B23 B24 B26 B27 B28 B29 B30 B31 B32 B41 B65 B66 B67 B68 E01 E02 E03 E04 E05 E06 E21 F04 F15 F16 F17 F25 F26 F27 F28 G01M G01N G07D A62C D05"),
    "consumer":    ("Consumer Products", "A41 A42 A43 A44 A45 A46 A47 A24 A62B B42 B43 B44 D06F F21 F24C G04 A63H A63J G07F G09F G10 A01K"),
    "robotics":    ("Robotics & Automation", "B25J G05B G05D B23Q B23P"),
    "tools":       ("Tools & Workshop", "B25B B25C B25D B25F B25G B25H B26B B27B B27G E04F21 G01C9"),
    "agrifood":    ("Agriculture & Food Tech", "A01 A21 A22 A23 A47J C12G C12C B65B25"),
    "biotech":     ("Biotech & Lab", "C07 C12N C12P C12Q C12M A61K A61P G01N33 B01L G16B"),
    "materials":   ("Materials & Chemistry", "C D B82"),
    "energy":      ("Energy & Sustainability", "H02 F03 F22 F23 F24S F24D F24F F24H H01M Y02"),
    "mobility":    ("Vehicles & Drones", "B60 B61 B62 B63 B64 F02 F01 G08G B60L"),
    "sports":      ("Sports & Fitness", "A63B A63C A63F A63G A63K F41B F41J"),
    "defense":     ("Firearms & Defense", "F41 F42"),
    "designs":     ("Product Designs", ""),   # design patents: the look of a product, filed under this field by kind
    "other":       ("Other Inventions", ""),  # lapsed patents outside every field above
}
_PREFIXES = sorted(((p, k) for k, (_, ps) in FIELDS.items() for p in ps.split()), key=lambda t: -len(t[0]))

# CPC groups searched for applications and for expired patents, per field: inventions a small team could build.
SEARCH_GROUPS = {
    "software": "G06Q30/02 G06Q10/10 G06F3/0482 H04L67/10 G06Q50/00 G09B19/00",
    "ai": "G06N20/00 G06V40/20 G06V20/68 G10L15/26 G06F40/58 G06N3/004 G06V40/16 G06V20/10 G06N5/04",
    "medical": "A61B5/00 A61H1/00 A61M5/00 A61F5/00 A61B5/11 A61H33/00",
    "electronics": "H02J7/00 H04R1/10 G06F1/16 H05B47/19 G08B21/04 G08B13/196 H04R1/028 G06F1/1632 H01R13/66 G08B21/18",
    "industrial": "B65D81/00 B25H1/00 B65G47/00 F16M11/04 B23K37/04 E04F21/00",
    "consumer": "A47G19/00 A45C11/00 A47B81/00 A47L13/00 A45F3/00 A47C7/62 A01K15/02",
    "robotics": "B25J11/008 B25J11/0005 B25J5/007 B25J13/08 A63H11/00 G05D1/0225 A47L11/4011 B25J9/0006 A63H30/04 G05D1/0088",
    "tools": "B25B13/48 B25H3/00 B25G1/08 B26B29/00 B25F1/00",
    "agrifood": "A01G9/02 A01G25/00 A47J31/44 A23L5/00 A01K1/00 A01B1/00",
    "biotech": "C12M1/00 B01L3/00 G01N33/487 C12M1/34 A61J1/05 B01L9/00",
    "materials": "B32B27/00 C09D5/00 C04B28/00 C09K5/00 D04H1/00 B29C64/10 C08J5/00 E04B1/80",
    "energy": "H02S20/00 F03D9/00 H01M10/46 F24S20/00 H02J3/38 F03B13/00",
    "mobility": "B64C39/02 B62K3/00 B60R11/00 B62J11/00 B60L53/00 B63B35/00",
    "sports": "A63B69/00 A63B21/00 A63B71/06 A63B24/00 A63F9/00 A63B63/00",
}
# Drug and chemistry patents can carry term extensions of up to five years, so the full-term source skips them.
EXTENSION_PRONE = ("A61K", "A61P", "C07", "C12N", "A01N")


def field_of(cpcs):
    """The field of a patent's main (first) classification. A prefix longer than a subclass names a main group, which
    must match whole: G06F1 is G06F1/16, never G06F12/02."""
    for code in cpcs:
        c = code.replace(" ", "")
        for p, k in _PREFIXES:
            if c.startswith(p + "/" if len(p) > 4 else p):
                return k
    return None


# Weapons, ammunition and explosives. They stay listed (the documents are public), but get no Claude kit, notes or
# spotlight: Claude declines weapons design work, so a kit would only lead to a refusal.
ARMED = ("F41", "F42", "C06B", "C06C", "C06D", "G21J")


def armed(cpcs):
    return any(c.replace(" ", "").upper().startswith(ARMED) for c in cpcs or ())


def years_ago(today, years):
    return (today - dt.timedelta(days=int(365.25 * years))).isoformat()


# ---------------------------------------------------------------- records

def plain(s):
    """Text from a USPTO field: no markup (<i>Lactobacillus</i>), no HTML entities (&amp;), single spaces."""
    return " ".join(html.unescape(re.sub(r"</?[A-Za-z][^>]*>", "", s or "")).split())


def bib(p):
    """The fields we keep from a Patent Public Search result."""
    cpc = [c for c in (p.get("cpcInventiveFlattened") or "").split(";") if c]
    cpc += [c for c in (p.get("cpcAdditionalFlattened") or "").split(";") if c]
    return {
        "guid": p["guid"], "type": p["type"], "title": plain(p.get("inventionTitle")),
        "filed": (p.get("applicationFilingDate") or [""])[0][:10],
        "published": (p.get("datePublished") or "")[:10],
        "related": sorted(d[:10] for d in (p.get("relatedApplFilingDate") or [])),
        "app": p.get("applicationNumber"), "cpc": cpc,
        "assignee": plain((p.get("assigneeName") or [""])[0]) or None, "inventors": plain(p.get("inventorsShort")) or None,
        "family": p.get("familyIdentifierCur"), "pages": p.get("pageCount") or 0,
        "drawings": [p.get("drawingsStart") or 0, p.get("drawingsEnd") or 0],
        "imageLocation": p.get("imageLocation"), "kind": (p.get("kindCode") or [""])[0],
    }


def number(guid):
    return guid.split("-")[1]


def pub_number(c):
    kind, num = c["guid"].split("-")[-1], number(c["guid"])
    if c["guid"].startswith(("EP-", "CA-")):  # European and Canadian: EP 0500000 B1, CA 1333741 C
        return f"{c['guid'][:2]} {num} {kind}"
    if c["guid"].startswith("AU-"):  # Australian application numbers carry no kind code: AU 2002254354
        return f"AU {num}"
    if c["type"] != "USPAT":
        return f"US {num[:4]}/{num[4:]} {kind}"
    pre, digits = re.match(r"([A-Z]*)(\d*)", num).groups()  # design and reissue patents: US D1,039,700 S
    return f"US {pre}{int(digits):,} {kind}" if digits else f"US {num} {kind}"


def plausible(d):
    """USPTO records occasionally carry a typo'd year ("0204-08-18"); such dates are ignored."""
    return bool(d) and "1900" <= d[:4] <= "2100"


def earliest_filing(c):
    dates = [d for d in [c.get("filed")] + list(c.get("related") or []) if plausible(d)]
    return min(dates) if dates else ""


def appeal(b):
    """Rough buildability prior used to shortlist before a person-written note exists."""
    s = 2.0 if not b["assignee"] else 0.5 if re.search(r"\b(LLC|Inc|Ltd|Co)\b", b["assignee"] or "") and len(b["assignee"]) < 30 else 0.0
    s += 1.5 if b["drawings"][0] else -5
    s += 1 if 8 <= b["pages"] <= 30 else 0 if b["pages"] <= 45 else -1.5
    s -= 1.5 if b["type"] == "USPAT" and len(b["related"]) > 2 else 0
    return s


# ---------------------------------------------------------------- legal status rules

def full_term_over(c, today):
    """A utility patent filed after June 8, 1995 lasts 20 years from its earliest non-provisional filing, plus any term
    adjustment for USPTO delays. We measure from the patent's own filing date (a later or equal date, so the estimate
    can only be late, never early), require that date to be at least 24 years ago, and accept only patents granted
    within 4 years of filing, which keeps any adjustment small."""
    g, f = c.get("published"), c.get("filed")
    if not (g and f) or f > years_ago(today, 24) or f < "1995-06-08":
        return False
    return (dt.date.fromisoformat(g) - dt.date.fromisoformat(f)).days <= 4 * 365.25


def term_end(c):
    """20 years from the patent's own filing date (see full_term_over)."""
    f = dt.date.fromisoformat(c["filed"])
    return (f.replace(year=f.year + 20) if not (f.month == 2 and f.day == 29) else f.replace(year=f.year + 20, day=28)).isoformat()


def family_clear(members, me, lapsed, reinstated, today):
    """True when no other US family member could still be in force or pending.
    A sibling patent counts as dead if it lapsed, or if its earliest filing is over 21 years old
    (a 20-year term plus margin for term adjustments)."""
    term_over = years_ago(today, 21)
    recent = years_ago(today, 7)
    for m in members:
        if m["guid"] == me["guid"]:
            continue
        if m["type"] == "USPAT":
            pn = number(m["guid"])
            if pn in reinstated:
                return False
            if pn in lapsed:
                continue
            e = earliest_filing(m)
            if not e or e > term_over:
                return False
        elif m["type"] == "US-PGPUB":
            if me["type"] == "US-PGPUB" and m["filed"] >= recent:
                return False  # a recent continuation might still be pending
            if me["type"] == "USPAT" and m["filed"] > me["filed"] and m["filed"] > term_over:
                return False  # a later application in the family might still be pending
    return True


def member_status(m, lapsed, today):
    if m["type"] != "USPAT":
        return "Published application"
    if number(m["guid"]) in lapsed:
        return "Patent, lapsed (fee not paid)"
    e = earliest_filing(m)
    if e and e <= years_ago(today, 21):
        return "Patent, expired (term ended)"
    return "Patent"


def family_entries(members, me, lapsed, today):
    return [{"n": pub_number(m), "id": m["guid"], "t": m["title"], "f": m["filed"], "p": m["published"],
             "k": "patent" if m["type"] == "USPAT" else "application", "s": member_status(m, lapsed, today)}
            for m in sorted(members, key=lambda m: (m["filed"], m["published"])) if m["guid"] != me["guid"]][:30]


# ---------------------------------------------------------------- text

def strip(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def split_claims(claims_html):
    """[[number, text], ...] following the claim numbering; canceled claims are left out."""
    t = strip(claims_html)
    keep, expect = [], 1
    for m in re.finditer(r"(?:^|\s)(\d{1,3})(?:\s*-\s*(\d{1,3}))?\s*[.)]\s+(?=[A-Z(])", t):
        a, b = int(m.group(1)), int(m.group(2) or m.group(1))
        if a == expect:
            keep.append((m, a))
            expect = b + 1
    out = []
    for i, (m, a) in enumerate(keep):
        text = t[m.end():keep[i + 1][0].start() if i + 1 < len(keep) else len(t)].strip()
        if not re.match(r"\((?:canceled|cancelled|withdrawn)\)", text, re.I):
            out.append([a, text])
    return out or ([[1, t]] if t else [])


def paragraphs(*htmls, cap=40000):
    """Description as paragraphs. Grants number them (1), (2); applications [0001], [0002]."""
    text = " ".join(strip(h) for h in htmls if h)
    parts = tidy(re.split(r"\s*(?:\(\d{1,4}\)|\[\d{4,5}\])\s+", text))
    out, total = [], 0
    for p in parts:
        if total + len(p) > cap:
            return out, True
        out.append(p)
        total += len(p)
    return out, False


_UP = r"[A-Z][A-Z0-9 &,/()-]{3,90}"
_SUB = (r"\d\.\s*(?:(?i:fields? of (?:the )?(?:invention|disclosure)|technical field|background of the invention"
        r"|background art|prior art|related art|description of (?:the )?(?:related|prior) art(?: and problems to be solved)?)"
        r"|Field|Background)")


def tidy(parts):
    """Split headings that the source glued into paragraphs ("... filter. 2. Description of the Related Art Many ...",
    "... pending. BACKGROUND OF THE INVENTION 1. Field of the Invention") into their own entries. Known numbered
    sub-headings are upper-cased so they read as headings. Running it again changes nothing."""
    out = []
    for p in parts:
        p = p.strip()
        if re.fullmatch(_SUB, p) or re.fullmatch(_UP, p):  # already a heading on its own
            out.append(p.upper())
            continue
        pieces = re.split(rf"(?:^|(?<=[.!?:;)\]A-Z]))\s*({_SUB})(?:\s+(?=[A-Z])|$)", p)
        for i, x in enumerate(pieces):
            x = (x or "").strip()
            if i % 2:
                out.append(x.upper())
                continue
            m = re.match(rf"^(.*[.!?:;)\]])\s+({_UP})$", x)  # all-caps heading at the end of a paragraph
            out += [m.group(1), m.group(2)] if m else [x] if x else []
    return out


def figures_list(desc_html):
    """The patent's own one-line figure descriptions ("FIG. 1 is a perspective view of ...")."""
    t = strip(desc_html)
    figs = re.findall(r"(FIGS?\.\s*\d+[A-Z]?(?:\s*(?:-|and|to|through)\s*\d+[A-Z]?)?\s+(?:is|are|shows?|illustrates?|depicts?)\s(?:FIG\.|[^.;]){8,160}?)(?=[;.]\s|;|\.$|$)", t)
    seen, out = set(), []
    for f in figs:
        if f[:12] not in seen:
            seen.add(f[:12])
            out.append(f.strip())
    return out[:12]


def section_after(text, heads, n):
    for hd in heads:
        m = re.search(hd + r"[^a-z]{0,40}?\)?\s*(.{40,}?)(?=\(\d+\)\s*[A-Z][A-Z ]{6,}|\[\d{4}\]\s*[A-Z][A-Z ]{6,}|$)", text)
        if m:
            return re.sub(r"\(\d+\)\s*|\[\d{4,5}\]\s*", "", m.group(1))[:n].strip()
    return ""


def is_heading(p):
    return len(p) < 90 and p == p.upper() and len(re.findall(r"[A-Z]", p)) >= 3


def section_from(desc, pattern, cap):
    """Text under the first heading matching pattern, up to the next heading."""
    out, on = [], False
    for p in desc:
        if is_heading(p):
            if out:
                break
            on = bool(re.search(pattern, p))  # "BACKGROUND" then "1. FIELD ...": look again at the sub-heading
        elif on:
            out.append(p)
    return " ".join(out)[:cap].strip()


def field_text(desc, cap=400):
    return section_from(desc, r"FIELD", cap)


def background_text(desc, cap=900):
    return section_from(desc, r"BACKGROUND|RELATED ART|PRIOR ART", cap)


def record_text(d):
    """Everything the site shows from a full Patent Public Search document."""
    brief = strip(d.get("briefHtml")) or strip(d.get("descriptionHtml"))
    claims = split_claims(d.get("claimsHtml"))[:80]
    desc, more = paragraphs(d.get("briefHtml"), d.get("descriptionHtml"))
    return {
        "abstract": strip(d.get("abstractHtml"))[:1600],
        "claims_all": claims,
        "claim1": claims[0][1][:1400] if claims else "",
        "desc": desc, "desc_more": more,
        "figures": figures_list(d.get("descriptionHtml") or d.get("briefHtml")),
        "field": field_text(desc) or section_after(brief, ["FIELD OF THE INVENTION", "TECHNICAL FIELD", "FIELD"], 400),
        "background": background_text(desc) or section_after(brief, ["BACKGROUND OF THE INVENTION", "DESCRIPTION OF THE RELATED ART", "BACKGROUND"], 900),
        "cites": [x for x in (d.get("urpn") or []) if x][:40],
    }
