"""Free to use (browse), the fields index and the archive page shell."""

from ..base import E, FIELD_NOTES, STATUS


class Browse:
    def browse(self):
        n = len(self.rows)
        body = f"""<div class="page browse">
<div class="sechead"><div><h1>Browse the register</h1><p>{n:,} recent US patents and applications that are no longer in force: lapsed for an unpaid fee, past their full term, or likely abandoned. Each passed the same checks, including no live relative in its US family, and lapsed ones are rechecked for reinstatement daily. The archive adds {self.meta.get('archive', 0):,} older records from four offices.</p></div></div>
<div class="workspace">{self.filters()}<div class="results">{self.toolbar()}{self.listing(self.rows)}</div></div>
</div>"""
        self.page("/browse/", "Browse free-to-use patents", f"Search and filter {n:,} US patents whose protection has ended, by field, status and how hard they are to build.",
                  body, section="/browse/", scripts=("browse",))

    def fields_index(self):
        tiles = "".join(
            f'<a class="tile" href="/fields/{k}/"><span class="th">{self.field_thumb(k)}</span><span><b>{E(n)}</b><small>{E(FIELD_NOTES.get(k, ""))} {len(self.by_field[k]) + self.meta.get("archiveByField", {}).get(k, 0):,} patents.</small></span></a>'
            for k, n in self.fields.items())
        body = f"""<div class="page"><div class="sechead"><div><h1>Fields</h1><p>Patents are filed under the field their classification points to. Pick one to see everything in it.</p></div></div><div class="tiles">{tiles}</div></div>"""
        self.page("/fields/", "Fields", "Free-to-use patents from the US, Europe, Canada and Australia, grouped by field, from software and AI to tools, energy and sports.", body, section="/fields/")
        for k, n in self.fields.items():
            rows = self.doc_by_field[k]
            counts = {s: sum(1 for r in rows if r["entry"]["st"] == s) for s in STATUS}
            arch = self.meta.get("archiveByField", {}).get(k, 0)
            parts = [f"{counts['lapsed']:,} lapsed", f"{counts['expired']:,} expired at full term", f"{counts['abandoned']:,} likely abandoned"]
            body = f"""<div class="page browse" data-field="{k}">
<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a><span>/</span><a href="/fields/">Fields</a><span>/</span><span>{E(n)}</span></nav>
<div class="sechead"><div><h1>{E(n)}</h1><p>{E(FIELD_NOTES.get(k, ""))} {len(rows) + arch:,} patents: {len(rows):,} freed in the past year ({", ".join(p for p in parts if not p.startswith("0 "))}){f", and {arch:,} more in the archive, from the US, Europe, Canada and Australia" if arch else ""}.</p></div><div class="rowbtns"><a class="btn secondary" href="/browse/?field={k}">Open in browse</a>{f'<a class="btn quiet" href="/browse/?in=archive">Search the archive</a>' if arch else ""}</div></div>
<div class="workspace">{self.filters(field=k)}<div class="results">{self.toolbar()}{self.listing(rows)}</div></div>
</div>"""
            self.page(f"/fields/{k}/", f"{n} patents", f"{len(rows) + arch:,} free-to-use patents in {n.lower()}: {FIELD_NOTES.get(k, '')}",
                      body, section="/fields/", scripts=("browse",))

    def archive_template(self):
        """The page shell for archive patents. functions/_archive.js fills in %%TITLE%%, %%DESC%%, %%PATH%% and %%BODY%%."""
        doc = self.page("%%PATH%%", "%%TITLE%%", "%%DESC%%", "%%BODY%%", scripts=("patent",), write=False)
        out = self.dist / "tpl" / "archive" / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(doc)
