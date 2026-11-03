"""The Site: every page renderer, combined. Each page lives in its own module under pages/."""
import patents as P

from .shell import Shell
from .components import Components
from .outputs import Outputs
from .pages.home import Home
from .pages.browse import Browse
from .pages.patent import PatentPage
from .pages.all_patents import AllPatents
from .pages.opportunities import Opportunities
from .pages.insights import Insights
from .pages.studio import Studio
from .pages.account import Account
from .pages.content import Content


class Site(Shell, Components, Home, Browse, PatentPage, AllPatents, Opportunities, Insights, Studio, Account, Content, Outputs):
    def __init__(self, rows, meta, dist=None):
        self.dist = dist
        self.rows, self.meta = rows, meta  # rows in catalog order: patents with a note first, easiest to build, newest freed
        self.by_field, self.doc_by_field = {}, {}
        for r in sorted(rows, key=lambda r: r["entry"]["id"]):
            self.by_field.setdefault(r["entry"]["ind"], []).append(r)
        for r in rows:
            self.doc_by_field.setdefault(r["entry"]["ind"], []).append(r)
        self.field_pos = {r["entry"]["id"]: i for lst in self.by_field.values() for i, r in enumerate(lst)}
        self.fields = {k: v[0] for k, v in P.FIELDS.items() if k in self.by_field}
        self.ids = {r["entry"]["id"]: (1 if r["fig"] else 0) + len(r["extra"]) for r in rows}  # id -> drawing sheets on the site
        self.pages = []  # (path, lastmod) for the sitemap
        self.version, self.css = "", "/assets/site.css"
        self.default_og = "/og.png"  # the share card (web/static/og.png, made by web/dev/og/); patent pages use their own drawing
