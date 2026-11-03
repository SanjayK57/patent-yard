"""Patent pages, their helpers (why it's free, timeline, claims, drawings) and the Claude kit data."""

import re
import struct
from urllib.parse import quote

import patents as P
from register import MAX_SHEETS, TODAY

from ..base import BUILD, BUILD_MEANS, E, EXT, SITE, STATUS, add_years, badge, d, full_date, icon, meter, purl, short_date


DEPENDENT = re.compile(r"\bclaims?\s+\d", re.I)


def png_size(path):
    b = path.read_bytes()[16:24]
    return struct.unpack(">II", b)


def links(e, d_):
    _, num, kind = e["id"].split("-")
    app = e["st"] == "abandoned"
    return {
        "pdf": f"https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/{num}",
        "ppubs": f"https://ppubs.uspto.gov/pubwebapp/external.html?q={num}.pn.&db={'US-PGPUB' if app else 'USPAT'}",
        "center": f"https://patentcenter.uspto.gov/applications/{re.sub(r'[^0-9]', '', d_.get('app') or '')}" if d_.get("app") else "https://patentcenter.uspto.gov/",
        "google": f"https://patents.google.com/patent/US{num}{kind}/en",
        "justia": f"https://patents.justia.com/patent/{num}",
        "fpo": f"https://www.freepatentsonline.com/y{num[:4]}/{num[4:]}.html" if app else f"https://www.freepatentsonline.com/{num}.html",
        "espacenet": f"https://worldwide.espacenet.com/patent/search?q=pn%3DUS{num}{kind}",
        "fees": "https://fees.uspto.gov/MaintenanceFees/",
    }


def gp(pid):
    _, num, kind = (pid.split("-") + [""])[:3]
    return f"https://patents.google.com/patent/US{num}{kind}/en"


def cite_ref(raw):
    x = str(raw).strip()
    if re.fullmatch(r"\d{4}/\d{7}", x):
        return f"US {x}", f"https://patents.google.com/patent/US{x.replace('/', '')}A1/en"
    if re.fullmatch(r"\d{5,8}", x):
        return f"US {int(x):,}", f"https://patents.google.com/patent/US{x}/en"
    if re.fullmatch(r"D\d{4,7}", x):
        return f"US {x} (design)", f"https://patents.google.com/patent/US{x}S/en"
    if re.fullmatch(r"RE\d{4,6}", x):
        return f"US {x} (reissue)", f"https://patents.google.com/patent/US{x}E/en"
    return f"US {x}", "https://patents.google.com/?q=" + quote("US" + re.sub(r"[^A-Za-z0-9]", "", x))


def why_free(e):
    fam = e["fam"]
    rel = ("Its one US relative has also lapsed, expired or never issued." if fam == 2 else f"All {fam - 1} of its US relatives have also lapsed, expired or never issued.") if fam > 1 \
        else "It has no other US patents or pending applications in its family."
    if e["st"] == "lapsed":
        og = f" of {full_date(e['og']['d'])}" if e.get("og") else ""
        recent = e["x"] and (TODAY - d(e["x"])).days < 120
        return [f"The USPTO Official Gazette{og} lists it as expired on {full_date(e['x'])} for an unpaid maintenance fee.",
                "It isn't on any reinstatement notice published since.", rel], \
            ("It lapsed only recently. Owners can still pay late and reinstate it, most often in the first months; we check every new notice. "
             if recent else "") + "We check US rights only. Check foreign counterparts before selling abroad."
    if e["st"] == "expired":
        return [f"Filed {full_date(e['f'])}. A US utility patent lasts 20 years from filing, so its base term ended {full_date(e['te'])}.",
                f"Granted {full_date(e['p'])}, within four years of filing, so any term adjustment for USPTO delay is short. The filing is over 24 years old.",
                rel, "It isn't in a drug or chemistry class, where term extensions are common."], \
            "Rarely, a term adjustment extends a patent by months or years. Confirm the expiration on Patent Center."
    return [f"Published {full_date(e['p'])}, and no patent has issued in its family since.",
            "Its family has had no new filings for more than seven years.",
            f"Filed {full_date(e['f'])}. Applications rarely stay pending this long."], \
        "This status is inferred. Confirm it on Patent Center before relying on it."


# ---------------------------------------------------------------- graphics built only from the patent's own data

def excerpt(text):
    """A stored excerpt ends where the text was cut, sometimes mid-word: end it at a sentence, or a word, and say so."""
    text = text.rstrip()
    if not text or text[-1] in '.!?)"':
        return text, False
    cut = text.rfind(". ")
    return (text[:cut + 1] if cut > len(text) * .6 else text[:text.rfind(" ")].rstrip(",;:") + "…"), True


def fee_schedule(e):
    """Fees are due 3.5, 7.5 and 11.5 years after grant; a lapse at the 4th, 8th or 12th anniversary means the fee due
    half a year earlier went unpaid and every earlier one was paid."""
    if e["st"] != "lapsed" or not e["p"] or not e["x"]:
        return None
    years = (d(e["x"]) - d(e["p"])).days / 365.25
    missed = 0 if years < 6 else 1 if years < 10 else 2
    return [(y, add_years(e["p"], y), "paid" if k < missed else "missed" if k == missed else "never") for k, y in enumerate((3.5, 7.5, 11.5))]


def timeline_events(e, doc):
    ev = []
    if e["e"] and e["e"] < e["f"]:
        ev.append((e["e"], "Earliest priority date", ""))
    ev.append((e["f"], "Application filed", ""))
    if e["st"] == "abandoned":
        ev.append((e["p"], "Application published", ""))
    else:
        pub = next((m for m in doc["family"] if m.get("k") == "application" and m.get("f") == e["f"] and m.get("p")), None)
        if pub:
            ev.append((pub["p"], "Application published", ""))
        ev.append((e["p"], "Patent granted", ""))
    fees = fee_schedule(e)
    if fees:
        ev += [(due, f"{y}-year fee {'paid' if st == 'paid' else 'not paid'}", "bad" if st == "missed" else "") for y, due, st in fees if st != "never"]
        ev.append((e["x"], "Patent expired", "bad"))
    if e["st"] == "expired" and e.get("te"):
        ev.append((e["te"], "20-year term ended", "bad"))
    return sorted((x for x in ev if x[0]), key=lambda x: x[0])


def timeline_svg(events):
    W, pad, y0 = 760, 40, 70
    t0, t1 = d(events[0][0]), d(events[-1][0])
    span = max((t1 - t0).days, 1)
    X = lambda s: pad + (d(s) - t0).days / span * (W - pad * 2)
    years = list(range(t0.year + 1, t1.year + 1))
    every = max(1, -(-len(years) // 10))
    col = lambda k: "var(--lapsed)" if k == "bad" else "var(--ink-3)" if k == "now" else "var(--accent)"
    out = [f'<svg class="chart" viewBox="0 0 {W} {y0 + 150}" role="img" aria-label="{E("Timeline: " + "; ".join(f"{t} {full_date(s)}" for s, t, _ in events))}">',
           f'<line class="axis" x1="{pad}" y1="{y0}" x2="{W - pad}" y2="{y0}" stroke-width="2"/>']
    for i, y in enumerate(years):
        if i % every == 0:
            x = X(f"{y}-01-01")
            out.append(f'<line class="tick" x1="{x:.1f}" y1="{y0 - 6}" x2="{x:.1f}" y2="{y0 + 6}"/><text class="muted" x="{x:.1f}" y="{y0 - 12}" text-anchor="middle">{y}</text>')
    last, lane = -1e9, 0
    for s, t, k in events:
        x = X(s)
        lane = (lane + 1) % 3 if x - last < 120 else 0
        last = x
        ly = y0 + 28 + lane * 38
        anchor = "start" if x < 110 else "end" if x > W - 110 else "middle"
        dash = ' stroke-dasharray="3 3"' if k == "now" else ""
        out.append(f'<line x1="{x:.1f}" y1="{y0}" x2="{x:.1f}" y2="{ly - 12}" stroke="{col(k)}" stroke-width="1"{dash}/>'
                   f'<circle cx="{x:.1f}" cy="{y0}" r="{4 if k == "now" else 6}" fill="{"var(--surface)" if k == "now" else col(k)}" stroke="{col(k)}" stroke-width="2"/>'
                   f'<text class="lbl" x="{x:.1f}" y="{ly}" text-anchor="{anchor}">{E(t)}</text>'
                   f'<text class="muted" x="{x:.1f}" y="{ly + 16}" text-anchor="{anchor}">{E(full_date(s).replace("January", "Jan").replace("February", "Feb").replace("August", "Aug").replace("September", "Sep").replace("October", "Oct").replace("November", "Nov").replace("December", "Dec"))}</text>')
    out.append("</svg>")
    return "".join(out)


def claim_parents(claims):
    """claim number -> the earlier claim it names ("as claimed in claim 2"), read from each claim's own text."""
    nums, parent = {n for n, _ in claims}, {}
    for n, t in claims:
        m = re.search(r"\bclaims?\s+(\d{1,3})", t, re.I)
        pn = int(m.group(1)) if m else None
        if pn and pn in nums and pn < n:
            parent[n] = pn
    return parent


def claim_list(claims):
    parent = claim_parents(claims)

    def depth(n):
        k = 0
        while n in parent and k < 3:
            n, k = parent[n], k + 1
        return k

    items = []
    for n, c in claims:
        dep = bool(DEPENDENT.search(c))
        d_ = max(depth(n), 1) if dep else 0
        items.append(f'<li class="{f"dep d{d_}" if dep else "ind"}" id="claim-{n}"><span class="cn">{n}</span><div>'
                     f'{"" if dep else "<em>Independent claim</em>"}{E(c)}</div></li>')
    return f'<ol class="claimlist">{"".join(items)}</ol>'


def claim_map(claims):
    """Each independent claim with the claims that build on it, as numbers, so nothing is cut off."""
    parent = claim_parents(claims)

    def root(n):
        while n in parent:
            n = parent[n]
        return n

    groups = {n: [] for n, c in claims if not DEPENDENT.search(c)}
    for n, c in claims:
        if n not in groups and root(n) in groups:
            groups[root(n)].append(n)
    rows = "".join(
        f'<div class="cgroup"><a class="ci" href="#claim-{n}">Claim {n}</a><small>{len(deps) or "No"} {"claim builds" if len(deps) == 1 else "claims build"} on it</small>'
        + ('<div class="cdeps">' + "".join(f'<a href="#claim-{k}">{k}</a>' for k in deps) + "</div>" if deps else "") + "</div>"
        for n, deps in groups.items())
    return (f'<div class="sidecard"><div class="panel"><div class="block"><h3>Claim map</h3><p class="muted note mb">'
            f'Independent claims stand on their own. The others add detail to the claim they name.</p>{rows}</div></div></div>')


def figure_lines(figs):
    """The patent's brief description of its drawings, without later mentions that start again at FIG. 1."""
    out, top = [], 0
    for f in figs:
        m = re.search(r"\d+", f)
        k = int(m.group()) if m else top
        if k < top:
            break
        top = k
        out.append(f)
    return out


# Shown instead of the Claude kit on weapons patents (patents.armed). Same text in web/functions/_archive.js.
KIT_OFF = ('<div class="panel soft kitoff"><div class="block"><h3>No Claude kit for weapons</h3><p class="prose">Claude doesn\'t help design '
           'weapons, ammunition or explosives, so this page has no Reinvent kit. To develop this one, work with a federally licensed '
           'manufacturer (many of these items are regulated) and a registered patent attorney or agent, listed on the '
           '<a href="https://oedci.uspto.gov/OEDCI/" target="_blank" rel="noopener noreferrer">USPTO roster</a>.</p></div></div>')


class PatentPage:
    def patent(self, r, detail, doc):
        """One patent's page, returned as HTML (it is packed into a shard, not written as its own file).
        Nothing on it depends on today's date, so its shard only changes when the patent's record does."""
        e, dd = r["entry"], detail
        pid, L = e["id"], links(e, dd)
        field = self.fields.get(e["ind"], e["ind"])
        sheets = ([r["fig"]] if r["fig"] else []) + r["extra"]
        checks, warn = why_free(e)
        owner = (f' · {"Applicant" if e["st"] == "abandoned" else "Assignee"}: {E(dd["asg"])}' if dd.get("asg") else "") + (f" · Inventors: {E(dd['inv'])}" if dd.get("inv") else "")
        claims = [c if isinstance(c, list) else [i + 1, c] for i, c in enumerate(doc["claims"])] or ([[1, dd["c1"]]] if dd["c1"] else [])
        ind_n = sum(1 for _, c in claims if not DEPENDENT.search(c))
        later = (f'being downloaded from USPTO and will appear here within days. Until then, read it in the <a href="{L["pdf"]}" {EXT}>USPTO PDF</a> '
                 f'or on <a href="{L["google"]}" {EXT}>Google Patents</a>.')
        status_line = {"lapsed": ("Expired (fee)", full_date(e["x"])), "expired": ("Term ended", full_date(e.get("te"))),
                       "abandoned": ("Status", "Abandoned (inferred)")}[e["st"]]
        kind = "application" if e["st"] == "abandoned" else "patent"

        # overview
        if sheets:
            w, h = png_size(sheets[0])
            fig = (f'<div class="figstick"><button class="bigfig" type="button" data-sheet="0" aria-label="Enlarge drawing sheet 1"><span class="ticks" aria-hidden="true"></span><img src="{self.img(pid)}" width="{w}" height="{h}" alt="Drawing sheet 1 of {E(e["n"])}"></button>'
                   f'<p class="cap">Sheet 1 of {e["sh"] or len(sheets)} from the published document. <a href="{L["pdf"]}" {EXT}>All sheets in the USPTO PDF</a></p></div>')
        elif e["sh"]:
            fig = (f'<div class="nofig later"><b><span class="pulse" aria-hidden="true"></span>Drawings on their way</b><p class="muted">This {kind} has {e["sh"]} drawing '
                   f'{"sheet" if e["sh"] == 1 else "sheets"}. They are being downloaded; every one is in the USPTO PDF now.</p><a class="btn secondary sm" href="{L["pdf"]}" {EXT}>{icon("file")}Open the USPTO PDF</a></div>')
        else:
            fig = ('<div class="nofig"><b>This document has no drawings.</b></div>' if e.get("arm") else
                   f'<div class="nofig"><b>This document has no drawings.</b><p class="muted">Claude can sketch it from the patent text.</p><button class="btn secondary sm" type="button" data-kit="sketch">{icon("spark")}Sketch it with Claude</button></div>')
        cpc = dd.get("cpc", [])
        cpc_html = (E(cpc[0]) + (f' <span class="muted" title="{E(", ".join(cpc))}">+{len(cpc) - 1} more</span>' if len(cpc) > 1 else "")) if cpc else "—"
        abstract = (f'<div class="block"><h3>Abstract <span class="src">Excerpt, from Google Patents</span></h3><p class="prose source">{E(dd["abs"])}</p><p class="muted note gap-top">The full abstract, claims and description are {later}</p></div>' if dd.get("abx") else
                    f'<div class="block"><h3>Abstract <span class="src">From the {kind}</span></h3><p class="prose source">{E(dd["abs"])}</p></div>' if dd["abs"] else
                    f'<div class="panel soft pendingbox"><div class="block"><h3><span class="pulse" aria-hidden="true"></span>Full text on its way</h3><p class="prose">This {kind} is listed from its USPTO record because it passed every check. Its abstract, claims and description are {later}</p></div></div>')
        plain = "" if e["auto"] else f'<div class="block pynote"><h3>In plain English <span class="src">Patent Yard summary</span></h3><p class="lead">{E(e["h"])}</p></div>'
        bg, bg_cut = excerpt(dd.get("bg") or "")
        bg_more = '<p class="muted note gap-top">It continues in the <a href="#description">description</a>.</p>' if bg_cut else ""
        overview = f"""
<section class="psec" id="overview"><h2>Overview</h2>
<div class="ov"><div>{fig}</div>
<div class="stack">
  {KIT_OFF if e.get("arm") else ""}
  {plain or abstract}
  <div class="panel soft"><div class="block"><h3>Why it's listed</h3><ul class="checks">{"".join(f"<li>{E(c)}</li>" for c in checks)}<li class="warn">{E(warn)}</li></ul></div></div>
  {f'<div class="angle"><b>Modern angle · Patent Yard idea</b>{E(e["tw"])}</div>' if e["tw"] else ""}
  <div class="facts">
    <div><small>Filed</small><b>{E(full_date(e["f"]))}</b></div>
    <div><small>{"Published" if e["st"] == "abandoned" else "Granted"}</small><b>{E(full_date(e["p"]))}</b></div>
    <div><small>{status_line[0]}</small><b>{E(status_line[1])}</b></div>
    <div><small>Application number</small><b>{E(dd.get("app") or "—")}</b></div>
    <div><small>Classification (CPC)</small><b>{cpc_html}</b></div>
    <div><small>Length</small><b>{f'{len(claims)} {"claim" if len(claims) == 1 else "claims"}' if claims else ""}{" · " if claims and dd.get("pages") else ""}{f'{dd["pages"]} pages' if dd.get("pages") else ""}{"—" if not claims and not dd.get("pages") else ""}</b></div>
  </div>
  {abstract if plain else ""}
  {f'<div class="block"><h3>Background <span class="src">From the {kind}</span></h3><p class="prose source">{E(bg)}</p>{bg_more}</div>' if dd.get("bg") else ""}
</div></div></section>"""

        # drawings
        figs = figure_lines(dd.get("figs") or [])
        if sheets or e["sh"]:
            total = max(e["sh"] or 0, len(sheets))
            gal = "".join(
                f'<figure><button type="button" data-sheet="{i}" aria-label="Enlarge sheet {i + 1}"><img src="{self.img(pid, i + 1)}" alt="Drawing sheet {i + 1} of {E(e["n"])}" loading="lazy" width="{png_size(s)[0]}" height="{png_size(s)[1]}"></button>'
                f'<figcaption><span>Sheet {i + 1} of {total}</span></figcaption></figure>'
                for i, s in enumerate(sheets))
            # sheets not downloaded yet still get their place, linked to the PDF that has them
            gal += "".join(
                f'<figure class="later"><a href="{L["pdf"]}" {EXT}><span class="pulse" aria-hidden="true"></span><b>Sheet {k}</b><span>Coming soon. Open it in the USPTO PDF</span></a>'
                f'<figcaption><span>Sheet {k} of {total}</span></figcaption></figure>'
                for k in range(len(sheets) + 1, min(total, MAX_SHEETS) + 1))
            if total > MAX_SHEETS:
                gal += (f'<figure class="later rest"><a href="{L["pdf"]}" {EXT}><b>+{total - MAX_SHEETS} more</b><span>Every sheet is in the USPTO PDF</span></a>'
                        f'<figcaption><span>Sheets {MAX_SHEETS + 1} to {total}</span></figcaption></figure>')
            more = f' <a href="{L["pdf"]}" {EXT}>Every sheet is in the USPTO PDF.</a>' if total > len(sheets) else ""
            lead = (f'All {total} drawing {"sheet" if total == 1 else "sheets"}' if len(sheets) >= total
                    else f'{len(sheets)} of {total} drawing sheets so far' if sheets else f'The {total} drawing {"sheet is" if total == 1 else "sheets are"} on the way')
            figlist = f'<div class="panel figside"><div class="block"><h3>Figures as described</h3><ul class="figlist">{"".join(f"<li>{E(x)}</li>" for x in figs)}</ul></div></div>' if figs else ""
            drawings = f"""<section class="psec" id="drawings"><h2>Drawings <small>{e["sh"] or len(sheets)}</small></h2>
<p class="muted sublead">{f"{lead} from the published document, cropped to the drawing.{more}" if sheets else f"{lead}.{more}"}</p>
<div class="drawwrap{" withlist" if figs else ""}"><div class="gallery">{gal}</div>{figlist}</div>
</section>"""
        else:
            sketch = "" if e.get("arm") else f'<p class="muted">Ask Claude for concept sketches based only on the patent\'s text. They are not part of the patent.</p><button class="btn primary sm" type="button" data-kit="sketch">{icon("spark")}Sketch it with Claude</button>'
            drawings = f"""<section class="psec" id="drawings"><h2>Drawings</h2><div class="nofig"><b>This document has no drawings.</b>{sketch}</div></section>"""

        # claims: one readable column, dependents indented under the claim they build on, and a map beside it
        gap = claims[0][0] - 1 if claims else 0
        gap_note = f'<p class="muted sublead">{"Claim 1 was" if gap == 1 else f"Claims 1 to {gap} were"} canceled before publication.</p>' if gap > 0 else ""
        claims_sec = f"""<section class="psec" id="claims"><h2>Claims <small>{len(claims)} total, {ind_n} independent</small></h2>
{gap_note}<p class="muted sublead">What the {kind} claimed, word for word. {"It was never granted, so these claims were never enforceable." if e["st"] == "abandoned" else "These claims are no longer enforceable in the US, unless the patent is reinstated." if e["st"] == "lapsed" else "These claims are no longer enforceable in the US."} Other patents and rights can still cover a product built from them.</p>
<div class="withaside">{claim_list(claims)}{claim_map(claims)}</div></section>""" if claims else f"""<section class="psec" id="claims"><h2>Claims</h2>
<div class="panel soft pendingbox"><div class="block"><h3><span class="pulse" aria-hidden="true"></span>On their way</h3><p class="prose">The claims are {later}</p></div></div></section>"""

        # description
        paras = doc["desc"]
        if paras:
            heads, parts = [], []
            for t in paras:
                if P.is_heading(t):
                    label = t.lower()[:1].upper() + t.lower()[1:] if not t[:1].isdigit() else re.sub(r"[a-z]", lambda m: m.group(0).upper(), t.lower(), count=1)
                    heads.append((f"d{len(heads) + 1}", label))
                    parts.append(f'<h3 id="d{len(heads)}">{E(label)}</h3>')
                else:
                    parts.append(f"<p>{E(t)}</p>")
            words = sum(len(t.split()) for t in paras)
            long_ = sum(len(t) for t in paras) > 6000
            jump = "".join(f'<a href="#{a}">{E(lbl)}</a>' for a, lbl in heads[:14])
            aside = ('<div class="sidecard"><div class="panel"><div class="block"><h3>In this description</h3>'
                     + (f'<nav class="jump" aria-label="Description sections">{jump}</nav>' if jump else "")
                     + f'<p class="muted note gap-top">About {words:,} words. The <a href="{L["pdf"]}" {EXT}>USPTO PDF</a> has it with every drawing.</p></div></div></div>')
            desc = f"""<section class="psec" id="description"><h2>Description</h2>
<div class="withaside"><div><div class="desc{" clamped" if long_ else ""}" id="desc">{"".join(parts)}{f'<p class="muted">The description continues in the <a href="{L["pdf"]}" {EXT}>full USPTO document</a>.</p>' if doc.get("more") else ""}</div>
{'<div class="rowbtns noprint gap-top"><button class="btn secondary" type="button" id="descMore" aria-controls="desc" aria-expanded="false">Read the full description</button></div>' if long_ else ""}</div>{aside}</div></section>"""
        else:
            desc = (f'<section class="psec" id="description"><h2>Description</h2><div class="panel soft pendingbox"><div class="block"><h3><span class="pulse" aria-hidden="true"></span>On its way</h3><p class="prose">The description is {later}</p></div></div></section>' if e["pending"] else
                    f'<section class="psec" id="description"><h2>Description</h2><p class="prose">The full description is in the <a href="{L["pdf"]}" {EXT}>USPTO document</a>.</p></section>')

        # timeline & family
        fees = fee_schedule(e)
        fee_html = ""
        if fees:
            fee_html = (f'<div class="panel"><div class="block"><h3>Maintenance fees</h3><p class="muted note mb">Fees are due 3.5, 7.5 and 11.5 years after grant. This patent expired on {E(full_date(e["x"]))}, so the fee marked "not paid" was the one that went unpaid.</p><div class="fees">'
                        + "".join(f'<div class="fee"><b>{y}-year fee</b><small>Due {E(full_date(due))}</small><span class="badge {"ok" if st == "paid" else "lapsed" if st == "missed" else "plain"}">{"Paid" if st == "paid" else "Not paid" if st == "missed" else "Never came due"}</span></div>' for y, due, st in fees)
                        + "</div></div></div>")
        me = {"n": e["n"], "id": pid, "t": e["ot"], "f": e["f"], "p": e["p"], "k": kind, "s": STATUS[e["st"]], "me": True}
        fam = sorted(doc["family"] + [me], key=lambda m: (m.get("f") or "") + (m.get("p") or ""))
        def node(m):
            kind_ = "This document" if m.get("me") else "Patent" if m.get("k") == "patent" else "Published application"
            when = (" · " + ("granted" if m.get("k") == "patent" else "published") + " " + E(short_date(m.get("p")))) if m.get("p") else ""
            cls = e["st"] if m.get("me") else "plain"
            ext = "" if m.get("me") else f'<div class="gap-top"><a href="{gp(m["id"])}" {EXT}>View on Google Patents</a></div>'
            return (f'<div class="famnode{" me" if m.get("me") else ""}" role="listitem"><small>{kind_}</small><b>{E(m["n"])}</b><p>{E(m["t"])}</p>'
                    f'<small>Filed {E(short_date(m.get("f")))}{when}</small><div class="gap-top"><span class="badge {cls}">{E(m["s"])}</span></div>{ext}</div>')
        lane = "".join(node(m) for m in fam)
        cites = doc.get("cites") or []
        cite_html = ('<div class="cites">' + "".join(f'<a class="chip" href="{h}" {EXT}>{E(lbl)}</a>' for lbl, h in map(cite_ref, cites)) + '</div><p class="muted note gap-top">Prior art cited by the examiner or applicant. Useful when you check your own idea for novelty.</p>') if cites else '<p class="muted">No US citations on record.</p>'
        history = f"""<section class="psec" id="history"><h2>Timeline &amp; family</h2><div class="stack">
<div class="panel"><div class="block"><h3>Timeline <span class="src">From USPTO dates</span></h3><div class="chartbox">{timeline_svg(timeline_events(e, doc))}</div></div></div>
{fee_html}
<div class="panel"><div class="block"><h3>US family <span class="src">{len(fam)} {"documents" if len(fam) > 1 else "document"}, by filing date</span></h3><div class="famlane" role="list">{lane}</div><p class="muted note gap-top">Earlier publications, parents and continuations. None of them can still be enforced, or this {kind} would not be listed.</p></div></div>
<div class="panel"><div class="block"><h3>US patents it cites <span class="src">{len(cites)}</span></h3>{cite_html}</div></div>
</div></section>"""

        # sources
        if e["st"] == "lapsed":
            origin = [(e.get("og", {}).get("u") or "https://www.uspto.gov/learning-and-resources/official-gazette/official-gazette-patents", "USPTO Official Gazette",
                       "Notice of Expiration of Patents Due to Failure to Pay Maintenance Fee" + (", issue of " + full_date(e["og"]["d"]) if e.get("og") else "") + ".", "Where this listing came from"),
                      (L["fees"], "Maintenance fee record", "Enter the patent number to see its fee history.", "USPTO Fees")]
        else:
            origin = [(L["ppubs"], "USPTO Patent Public Search", "The patent record, found by filing date (1996 to 2001) and classification." if e["st"] == "expired" else "The published application, found by filing date (2013 to 2017) and classification.", "Where this listing came from")]
        official = [(L["pdf"], "Full published document", "Text and every drawing sheet as a PDF.", "USPTO"), (L["center"], "File history", "Status, office actions, notices, fee records and petitions.", "USPTO Patent Center")]
        if e["st"] == "lapsed":
            official.append((L["ppubs"], "Patent Public Search record", "Searchable full text and bibliographic data.", "USPTO"))
        cross = [(L["google"], "Google Patents", "Worldwide family, citing patents and legal events.", "patents.google.com"), (L["justia"], "Justia Patents", "Full text, claims and classification.", "patents.justia.com"),
                 (L["fpo"], "FreePatentsOnline", "Full text and PDF.", "freepatentsonline.com"), (L["espacenet"], "Espacenet", "Foreign family and legal status.", "European Patent Office")]
        lc = lambda x, cls="": f'<a class="lcard {cls}" href="{x[0]}" {EXT}><b>{E(x[1])}{icon("ext")}</b><span>{E(x[2])}</span><small>{E(x[3])}</small></a>'
        confirm = {"lapsed": 'The status should read "Patent Expired Due to NonPayment of Maintenance Fees Under 37 CFR 1.362".',
                   "expired": f'Its 20-year term from filing ended {E(full_date(e.get("te")))}. Check the "Patent Term Adjustment" and "Patent Term Extension" entries, which add days to that date.',
                   "abandoned": 'The status should read "Abandoned", usually with a notice of abandonment in the documents.'}[e["st"]]
        sources = f"""<section class="psec" id="sources"><h2>Sources &amp; verification</h2><div class="stack">
<div class="cols2"><div class="panel"><div class="block"><h3>Verification</h3><ul class="checks">{"".join(f"<li>{E(c)}</li>" for c in checks)}<li><span>{"Rechecked against USPTO records for a reinstatement every day" if e["st"] == "lapsed" else "Rechecked against USPTO records with each refresh"}<span class="vdate"></span>.</span></li><li class="warn">{E(warn)}</li></ul>
<p class="muted dates">{" · ".join(x for x in [f"Added to Patent Yard {full_date(r['added'][:10])}" if r["added"] else "", f"status last checked {full_date(e['v'])}" if e["v"] else ""] if x)}</p></div></div>
<div class="panel"><div class="block"><h3>Confirm it yourself</h3><ol class="prose olist"><li>Open the <a href="{L["center"]}" {EXT}>file history on Patent Center</a>.</li><li>{confirm}</li><li>Check the documents for any later petition to revive or reinstate.</li></ol></div></div></div>
<div class="cols2 links2"><div class="block"><h3>Official USPTO records</h3><div class="linklist">{"".join(lc(x, "src" if i == 0 else "") for i, x in enumerate(origin + official))}</div></div>
<div class="block"><h3>Cross-check elsewhere</h3><div class="linklist">{"".join(lc(x) for x in cross)}</div></div></div>
<p class="muted note">{"The name, summary, modern angle and build rating are Patent Yard's notes, drafted with Claude (an AI model) from the patent's text. Everything else" if not e["auto"] else "Everything"} on this page comes from the documents linked above.</p>
<div class="rowbtns noprint"><button class="btn secondary sm" type="button" id="reportBtn" hidden>Report a problem with this listing</button></div>
</div></section>"""

        related = self.neighbors(r)
        lst, pos = self.by_field[e["ind"]], self.field_pos[pid]
        prev_, next_ = (lst[pos - 1] if pos > 0 else None), (lst[pos + 1] if pos + 1 < len(lst) else None)
        step = lambda x, lbl, cls: (f'<a class="pstep {cls}" href="{purl(x["entry"]["id"])}" rel="{"prev" if cls == "prev" else "next"}"><small>{lbl}</small><b>{E(x["entry"]["t"])}</b></a>' if x else "<span></span>")
        pnav = f'<nav class="pnav noprint" aria-label="More patents in this field">{step(prev_, "← Previous in " + field, "prev")}{step(next_, "Next in " + field + " →", "next")}</nav>' 
        rel = f'<section class="section noprint"><div class="sechead"><div><h2>More in {E(field)}</h2></div><a class="btn quiet" href="/fields/{e["ind"]}/">All {E(field)}</a></div><div class="grid">{"".join(self.card(x, 9) for x in related)}</div></section>' if related else ""
        toc = [("overview", "Overview", ""), ("drawings", "Drawings", e["sh"] or len(sheets) or ""), ("claims", "Claims", len(claims) or ""), ("description", "Description", ""), ("history", "Timeline & family", ""), ("sources", "Sources & verification", "")]
        build_badge = f'<a class="badge plain" href="/how-it-works/#build" title="Estimate: {BUILD_MEANS[e["b"]]}">{meter(e["b"])}{BUILD[e["b"]]} build</a>' if e["b"] else ""
        num = f'<span class="num">{E(e["n"])}</span>'
        asfiled = f"{num} · Title as filed: {E(e['ot'])}" if e["t"] != e["ot"] else num
        body = f"""<div class="page" id="patent" data-id="{pid}" data-n="{E(e["n"])}" data-sheets="{len(sheets)}" data-total="{e["sh"] or len(sheets)}" data-pdf="{L["pdf"]}">
<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a><span>/</span><a href="/fields/{e["ind"]}/">{E(field)}</a><span>/</span><span>{E(e["n"])}</span></nav>
<div class="phead">
  <div><div class="badges">{badge(e["st"])}{build_badge}{'<span class="badge plain">No assignee recorded</span>' if e["ia"] and e["st"] != "abandoned" else ""}<span class="badge ok" id="vbadge" hidden></span></div>
  <h1{' class="long"' if len(e["t"]) > 60 else ""}>{E(e["t"])}</h1><p class="asfiled">{asfiled}{owner}</p></div>
  <div class="pactions">
    {"" if e.get("arm") else f'<button class="btn primary" type="button" data-kit="workshop">{icon("spark")}Reinvent with Claude</button>'}
    <button class="btn quiet" type="button" id="reserveBtn">{icon("flag")}Reserve</button>
    <a class="btn quiet" href="{L["pdf"]}" {EXT}>{icon("file")}USPTO PDF</a>
    <button class="btn quiet" type="button" id="saveBtn" aria-pressed="false">{icon("bookmark")}<span>Save</span></button>
    <button class="btn quiet" type="button" id="copyLink">{icon("link")}Copy link</button>
    <div class="resline" id="resline" aria-live="polite"></div>
  </div>
</div>
<div class="playout">
  <nav class="toc" aria-label="On this page">{"".join(f'<a href="#{a}">{t}{f"<small>{n}</small>" if n else ""}</a>' for a, t, n in toc)}</nav>
  <div>{overview}{drawings}{claims_sec}{desc}{history}{sources}{pnav}</div>
</div>
{rel}
</div>
<dialog id="viewer" aria-label="Drawing viewer"></dialog>
<dialog id="kit" aria-labelledby="kitTitle"></dialog>
<dialog id="resDlg" aria-labelledby="resTitle"></dialog>
<dialog id="repDlg" aria-labelledby="repTitle"></dialog>"""
        ld = [{"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
                  {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                  {"@type": "ListItem", "position": 2, "name": field, "item": f"{SITE}/fields/{e['ind']}/"},
                  {"@type": "ListItem", "position": 3, "name": e["n"], "item": SITE + purl(pid)}]},
              {"@context": "https://schema.org", "@type": "CreativeWork", "name": e["ot"], "alternateName": e["t"], "identifier": e["n"],
               "dateCreated": e["f"], "datePublished": e["p"], "abstract": dd["abs"][:500], "url": SITE + purl(pid),
               "image": SITE + self.img(pid) if sheets else None, "isBasedOn": L["pdf"]}]
        desc_meta = f'{e["n"]}, {STATUS[e["st"]].lower()}: {e["h"] or e["ot"]}'
        return self.page(purl(pid), f'{e["t"]} ({e["n"]})', desc_meta, body, og_image=self.img(pid) if sheets else None, jsonld=ld,
                         scripts=("patent",), lastmod=e["v"] or r["added"] or None, write=False)

    def neighbors(self, r, k=4):
        """Related patents: the nearest patent numbers in the same field, so the list only changes when one is added nearby."""
        lst = self.by_field[r["entry"]["ind"]]
        i = self.field_pos[r["entry"]["id"]]
        near = lst[max(0, i - k // 2):i] + lst[i + 1:i + 1 + k]
        return near[:k]

    def kit(self, r, detail, doc):
        """What the Claude kit and the studio need about one patent (served at /data/p/<id>.json)."""
        e, dd = r["entry"], detail
        checks, warn = why_free(e)
        L = links(e, dd)
        n = (1 if r["fig"] else 0) + len(r["extra"])
        return {"id": e["id"], "n": e["n"], "t": e["t"], "ot": e["ot"], "h": e["h"], "auto": bool(e["auto"]), "tw": e["tw"], "st": e["st"], "status": STATUS[e["st"]],
                "field": self.fields.get(e["ind"], e["ind"]), "filed": e["f"], "granted": e["p"], "expired": e.get("x"), "termEnd": e.get("te"),
                "abs": dd["abs"], "claims": [c if isinstance(c, list) else [i + 1, c] for i, c in enumerate(doc["claims"])][:80], "figs": figure_lines(dd.get("figs") or []),
                "fieldText": dd.get("field") or "", "bg": dd.get("bg") or "", "inventors": dd.get("inv"), "assignee": dd.get("asg"), "cpc": dd.get("cpc") or [],
                "app": dd.get("app"), "why": checks, "warn": warn, "sheets": [self.img(e["id"], k) for k in range(1, n + 1)], "totalSheets": e["sh"],
                "url": SITE + purl(e["id"]), "pdf": L["pdf"], "google": L["google"], "armed": bool(e.get("arm"))}
