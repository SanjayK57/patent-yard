"""Official USPTO sources. None of them needs an account or a key (until Patent Public Search requires sign-in).

  Official Gazette      weekly notices: patents expired for unpaid maintenance fees, and patents reinstated
  Patent Public Search  bibliographic data, family members, full text and drawing sheets (anonymous session)
"""
import datetime as dt
import html
import json
import re
import socket
import time
import urllib.error
import urllib.request
from pathlib import Path

UA = "PatentYard/1.0 (free public patent register; about one request a second)"
GAZETTE_ISSUE = "https://patentsgazette.uspto.gov/week{week:02d}/OG/TOC.htm"
GAZETTE_HOME = "https://www.uspto.gov/learning-and-resources/official-gazette/official-gazette-patents"


def fetch(url, data=None, headers=None, tries=4):
    """GET or POST with backoff. A 429 means USPTO wants us slower, so those waits are long."""
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, **(headers or {})})
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.read(), r.headers
        except urllib.error.HTTPError as e:
            if e.code in (401, 403) and "ppubs" in url:
                raise  # session problem; the caller reopens it
            if e.code not in (429, 500, 502, 503, 504) or i == tries - 1:
                raise
            time.sleep((20 if e.code == 429 else 3) * 2 ** i)
            continue
        except (urllib.error.URLError, TimeoutError, socket.timeout, ConnectionError):  # socket.timeout isn't a TimeoutError before 3.10
            if i == tries - 1:
                raise
        time.sleep(3 * 2 ** i)


SIGN_IN_FLAG = Path(__file__).resolve().parent / "raw" / "ppubs_signin_required"


class SignInRequired(SystemExit):
    """Patent Public Search asked for a USPTO.gov sign-in (required from 2026-11-07). A SystemExit, so the long-running
    jobs (bulk, enrich, harvest) stop instead of retrying every document; daily.sh starts them again twice a day and
    they ask once more only after 24 hours (SIGN_IN_FLAG). verify catches it and keeps its Gazette and term checks."""


def _signed_out(note):
    SIGN_IN_FLAG.write_text(time.strftime("%Y-%m-%d %H:%M ") + note)
    raise SignInRequired(f"Patent Public Search needs a USPTO.gov sign-in (HTTP Error 401/403: {note}); "
                         "the pipeline needs a USPTO Open Data Portal API key. Asking again in 24 hours.")


class PatentPublicSearch:
    """Client for ppubs.uspto.gov. It opens an anonymous session the way the public web app does.
    The access token is kept in memory only, never written to disk."""
    BASE = "https://ppubs.uspto.gov/api/"

    def __init__(self):
        self.token = self.case = None
        self.opened = 0.0
        self.delay = 1.1  # seconds between calls; grows after rate-limit replies, shrinks back when calls succeed

    def _open(self):
        if SIGN_IN_FLAG.exists() and time.time() - SIGN_IN_FLAG.stat().st_mtime < 86400:
            raise SignInRequired("Patent Public Search needs a USPTO.gov sign-in (HTTP Error 401, seen in the last 24 hours)")
        try:
            body, hdrs = fetch(self.BASE + "users/me/session", b"-1", {"Content-Type": "application/json"})
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                _signed_out(f"session refused, HTTP {e.code}")
            raise
        self.token = hdrs.get("x-access-token")
        self.case = json.loads(body)["userCase"]["caseId"]
        self.opened = time.time()

    def _call(self, path, payload=None):
        if not self.token or time.time() - self.opened > 20 * 60:  # sessions time out after 30 minutes
            self._open()
        time.sleep(self.delay)
        started = time.time()
        hdr = {"x-access-token": self.token}
        data = None
        if payload is not None:
            hdr["Content-Type"] = "application/json"
            data = json.dumps(payload).encode()
        try:
            body = fetch(self.BASE + path, data, hdr)[0]
        except urllib.error.HTTPError as e:
            if e.code == 429:
                self.delay = min(self.delay * 2, 12)
            if e.code not in (401, 403):
                raise
            self._open()
            hdr["x-access-token"] = self.token
            try:
                body = fetch(self.BASE + path, data, hdr)[0]
            except urllib.error.HTTPError as e2:
                if e2.code in (401, 403):  # refused even with a fresh session: sign-in is required now
                    _signed_out(f"call refused with a fresh session, HTTP {e2.code}")
                raise
        if SIGN_IN_FLAG.exists():
            SIGN_IN_FLAG.unlink()  # working again
        # a slow answer means fetch() waited out rate limits: space calls further apart for a while
        self.delay = min(self.delay * 1.5, 12) if time.time() - started > 15 else max(1.1, self.delay * 0.95)
        return body

    def search(self, q, dbs, n=500, family=False, start=0, total=False):
        """Run a search in the ppubs query language. Batches over ~200 patent numbers are refused.
        start pages through larger results; total=True also returns how many there are."""
        if self.case is None:
            self._open()
        payload = {
            "start": start, "pageCount": n, "sort": "date_publ desc",
            "docFamilyFiltering": "familyIdFiltering" if family else "noFiltering",
            "searchType": 1, "familyIdEnglishOnly": True, "familyIdFirstPreferred": "US-PGPUB",
            "familyIdSecondPreferred": "USPAT", "familyIdThirdPreferred": "FPRS",
            "showDocPerFamilyPref": "showEnglish", "queryId": 0, "tagDocSearch": False,
            "query": {"caseId": self.case, "hl_snippets": "2", "op": "OR", "q": q, "queryName": q,
                      "highlights": "0", "qt": "brs", "spellCheck": False, "viewName": "tile",
                      "plurals": True, "britishEquivalents": True,
                      "databaseFilters": [{"databaseName": d, "countryCodes": []} for d in dbs],
                      "searchType": 1, "ignorePersist": True, "userEnteredQuery": q},
        }
        r = json.loads(self._call("searches/searchWithBeFamily", payload))
        if r.get("error"):
            raise RuntimeError(f"Patent Public Search refused {q!r}: {r['error']}")
        return (r.get("patents") or [], r.get("numFound") or 0) if total else r.get("patents") or []

    def document(self, guid, source):
        """Full record: abstract, claims, description and citations."""
        return json.loads(self._call(f"patents/highlight/{guid}?queryId=1&source={source}&includeSections=true&uniqueId="))

    def sheet(self, location, page):
        """One page of the published document as a 1-bit PNG."""
        return self._call(f"image/convert?url={location}/{page:08d}.tif")


def parse_gazette(page):
    """Issue date, expired patents and reinstated patents from one Official Gazette table of contents."""
    h = page
    issued = dt.datetime.strptime(re.search(r"(\w+ \d{1,2}, 20\d\d)", h).group(1), "%B %d, %Y").date().isoformat()
    toc = {html.unescape(re.sub(r"\s+", " ", t)).strip(): ref for ref, t in re.findall(r'<a href="#(ref\d+)">([^<]{8,})<', h)}

    def section(title_start):
        ref = next((r for t, r in toc.items() if t.startswith(title_start)), None)
        if not ref:
            return ""
        i = h.find(f'name="{ref}"')
        j = h.find('name="ref', i + 10)
        return html.unescape(re.sub(r"<[^>]+>", " ", h[i:j if j > 0 else None]))

    lapsed = []
    for block in re.split(r"PATENTS WHICH EXPIRED ON ", section("Notice of Expiration of Patents Due to Failure to Pay"))[1:]:
        m = re.match(r"(\w+ \d{1,2}, \d{4})", block)
        expired = dt.datetime.strptime(m.group(1), "%B %d, %Y").date().isoformat() if m else None
        for pn, app, _ in re.findall(r"(\d{1,2},\d{3},\d{3}|RE\d{2},\d{3})\s+(\d{2}/\d{3},\d{3})\s+(\d{2}/\d{2}/\d{4})", block):
            lapsed.append({"pn": pn.replace(",", ""), "app": app.replace(",", ""), "expired": expired})
    reinstated = sorted({p.replace(",", "") for p in re.findall(r"(\d{1,2},\d{3},\d{3})\s+\d{2}/\d{3},\d{3}", section("Patents Reinstated"))})
    return issued, lapsed, reinstated


def gazette_week(week, cache_dir: Path, today: dt.date):
    """One weekly issue, cached. The URL always holds the latest issue with that week number, so a cached
    issue older than ~51 weeks is refetched."""
    cache = cache_dir / f"week{week:02d}.json"
    if cache.exists():
        c = json.loads(cache.read_text())
        c.setdefault("week", week)  # caches written before the field existed
        if (today - dt.date.fromisoformat(c["date"])).days < 358:
            return c
    body, _ = fetch(GAZETTE_ISSUE.format(week=week))
    issued, lapsed, reinstated = parse_gazette(body.decode("utf-8", "replace"))
    c = {"date": issued, "week": week, "lapsed": lapsed, "reinstated": reinstated}
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(c))
    return c


def gazette_url(week, issued, today: dt.date):
    """Link to the issue that listed a patent while it is still online at its weekly address."""
    if week and issued and (today - dt.date.fromisoformat(issued)).days < 358:
        return GAZETTE_ISSUE.format(week=week)
    return GAZETTE_HOME
