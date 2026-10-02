"""Checks for the parts of the pipeline that decide what the site says. Run: python3 pipeline.py test"""
import datetime as dt
import unittest

import patents as P
import uspto
from drawings import decode_gray_png, one_bit_png, shrink_sheet

TODAY = dt.date(2026, 9, 29)


class Fields(unittest.TestCase):
    def test_longest_prefix_wins(self):
        self.assertEqual(P.field_of(["H02J7/0042"]), "energy")
        self.assertEqual(P.field_of(["H01L21/02"]), "chips")  # semiconductor processes have their own field
        self.assertEqual(P.field_of(["A47J31/44"]), "agrifood")
        self.assertEqual(P.field_of(["A47G19/22"]), "consumer")
        self.assertEqual(P.field_of(["B25B13/46"]), "tools")
        self.assertEqual(P.field_of(["B25J9/16"]), "robotics")
        self.assertIsNone(P.field_of(["Z99Z1/00"]))

    def test_plain_text_from_uspto(self):
        self.assertEqual(P.plain("Schaeffler AG &amp; Co. KG"), "Schaeffler AG & Co. KG")
        self.assertEqual(P.plain("Live <i>Edwardsiella ictaluri </i>vaccine"), "Live Edwardsiella ictaluri vaccine")
        self.assertEqual(P.plain('Yang; Xiao &quot;Charles&quot;'), 'Yang; Xiao "Charles"')

    def test_term_certainly_over(self):
        import register as R
        today = dt.date(2026, 10, 2)
        self.assertTrue(R.term_certainly_over("1999-03-01", "2002-05-07", today))      # 20 years from filing, no adjustment
        self.assertFalse(R.term_certainly_over("2000-06-01", "2003-05-06", today))     # could carry a term adjustment
        self.assertTrue(R.term_certainly_over("1990-01-02", "1993-04-06", today))      # 17 years from grant also over
        self.assertFalse(R.term_certainly_over("1993-01-05", "2012-06-05", today))     # 17 years from a late grant: 2029

    def test_typo_dates_ignored(self):
        self.assertEqual(P.earliest_filing({"filed": "2012-05-01", "related": ["0204-08-18", "2010-03-02"]}), "2010-03-02")

    def test_numbers(self):
        self.assertEqual(P.pub_number({"guid": "US-8789222-B2", "type": "USPAT"}), "US 8,789,222 B2")
        self.assertEqual(P.pub_number({"guid": "US-20190258139-A1", "type": "US-PGPUB"}), "US 2019/0258139 A1")
        self.assertEqual(P.pub_number({"guid": "US-D1039700-S", "type": "USPAT"}), "US D1,039,700 S")


class Text(unittest.TestCase):
    def test_claims(self):
        self.assertEqual(P.split_claims("1. A cup comprising a lid. 2. The cup of claim 1, wherein the lid is red. 3. The cup of claim 2."),
                         [[1, "A cup comprising a lid."], [2, "The cup of claim 1, wherein the lid is red."], [3, "The cup of claim 2."]])
        self.assertEqual(P.split_claims("1 - 10 . (canceled) 11 . A robot chef. 12 . The chef of claim 11."),
                         [[11, "A robot chef."], [12, "The chef of claim 11."]])
        self.assertEqual(P.split_claims("1) A stand. 2) The stand of claim 1."), [[1, "A stand."], [2, "The stand of claim 1."]])

    def test_paragraphs(self):
        self.assertEqual(P.paragraphs("(1) FIELD (2) The cup holds tea."), (["FIELD", "The cup holds tea."], False))
        self.assertEqual(P.paragraphs("TECHNICAL FIELD [0001] It holds tea. BACKGROUND ART [0002] Cups leak."),
                         (["TECHNICAL FIELD", "It holds tea.", "BACKGROUND ART", "Cups leak."], False))
        paras, more = P.paragraphs("(1) " + "a" * 50 + " (2) " + "b" * 50, cap=60)
        self.assertTrue(more)
        self.assertEqual(len(paras), 1)

    def test_sections(self):
        desc = ["TECHNICAL FIELD", "Exoskeletons.", "BACKGROUND", "Old ones are heavy.", "They cost a lot.", "SUMMARY", "Ours is light."]
        self.assertEqual(P.section_from(desc, r"FIELD", 400), "Exoskeletons.")
        self.assertEqual(P.section_from(desc, r"BACKGROUND", 900), "Old ones are heavy. They cost a lot.")
        self.assertEqual(P.section_from(desc, r"NOTHING", 900), "")
        glued = ["Claims no benefit. BACKGROUND OF THE INVENTION 1. Field of the Invention",
                 "It relates to hand trucks. 2. Description of the Related Art", "Doors are heavy.",
                 "SUMMARY OF THE INVENTION", "A truck."]
        old = P.tidy(glued)
        self.assertEqual(old, ["Claims no benefit.", "BACKGROUND OF THE INVENTION", "1. FIELD OF THE INVENTION",
                               "It relates to hand trucks.", "2. DESCRIPTION OF THE RELATED ART", "Doors are heavy.",
                               "SUMMARY OF THE INVENTION", "A truck."])
        self.assertEqual(P.tidy(old), old)
        self.assertEqual(P.tidy(["1. Technical Field The disclosure relates to farming."]),
                         ["1. TECHNICAL FIELD", "The disclosure relates to farming."])
        self.assertEqual(P.tidy(["See FIG. 2. The arm moves."]), ["See FIG. 2. The arm moves."])
        self.assertEqual(P.tidy(["Shown in FIG. 1. Field lines bend. 2. Field The valve."]),
                         ["Shown in FIG. 1. Field lines bend.", "2. FIELD", "The valve."])
        self.assertEqual(P.field_text(old), "It relates to hand trucks.")
        self.assertEqual(P.background_text(old), "Doors are heavy.")
        self.assertEqual(P.background_text(desc), "Old ones are heavy. They cost a lot.")

    def test_figures(self):
        figs = P.figures_list("<p>FIG. 1 is a perspective view of a cup; FIG. 2 is a side view of the lid in FIG. 1.</p>")
        self.assertEqual(figs, ["FIG. 1 is a perspective view of a cup", "FIG. 2 is a side view of the lid in FIG. 1"])


class Rules(unittest.TestCase):
    me = {"guid": "US-8000001-B2", "type": "USPAT", "filed": "2012-01-01", "related": []}

    def test_dead_family(self):
        old = {"guid": "US-6000001-B1", "type": "USPAT", "filed": "2001-01-01", "related": []}
        self.assertTrue(P.family_clear([self.me, old], self.me, {"8000001"}, set(), TODAY))

    def test_live_sibling_blocks(self):
        live = {"guid": "US-9000001-B2", "type": "USPAT", "filed": "2014-01-01", "related": []}
        self.assertFalse(P.family_clear([self.me, live], self.me, {"8000001"}, set(), TODAY))
        self.assertTrue(P.family_clear([self.me, live], self.me, {"8000001", "9000001"}, set(), TODAY))

    def test_reinstated_sibling_blocks(self):
        sib = {"guid": "US-9000001-B2", "type": "USPAT", "filed": "2014-01-01", "related": []}
        self.assertFalse(P.family_clear([self.me, sib], self.me, {"9000001"}, {"9000001"}, TODAY))

    def test_continuation_inherits_old_priority(self):
        cont = {"guid": "US-7000001-B2", "type": "USPAT", "filed": "2006-01-01", "related": ["1999-05-01"]}
        self.assertTrue(P.family_clear([self.me, cont], self.me, {"8000001"}, set(), TODAY))

    def test_pending_application_blocks(self):
        app = {"guid": "US-20150000001-A1", "type": "US-PGPUB", "filed": "2014-06-01", "related": []}
        self.assertFalse(P.family_clear([self.me, app], self.me, set(), set(), TODAY))
        me_app = {"guid": "US-20150000002-A1", "type": "US-PGPUB", "filed": "2014-01-01", "related": []}
        recent = {"guid": "US-20220000003-A1", "type": "US-PGPUB", "filed": "2021-01-01", "related": []}
        self.assertFalse(P.family_clear([me_app, recent], me_app, set(), set(), TODAY))

    def test_full_term(self):
        ok = {"filed": "1998-03-01", "published": "2000-06-01", "related": []}
        slow = {"filed": "1998-03-01", "published": "2014-06-01", "related": []}
        young = {"filed": "2004-03-01", "published": "2006-06-01", "related": []}
        old_rules = {"filed": "1994-03-01", "published": "1996-06-01", "related": []}
        self.assertEqual(P.term_end({"filed": "2000-02-29"}), "2020-02-28")
        self.assertEqual(P.term_end({"filed": "1998-03-01"}), "2018-03-01")
        self.assertTrue(P.full_term_over(ok, TODAY))
        self.assertFalse(P.full_term_over(slow, TODAY))
        self.assertFalse(P.full_term_over(young, TODAY))
        self.assertFalse(P.full_term_over(old_rules, TODAY))

    def test_member_status(self):
        self.assertEqual(P.member_status({"guid": "US-8000001-B2", "type": "USPAT", "filed": "2012-01-01", "related": []}, {"8000001"}, TODAY),
                         "Patent, lapsed (fee not paid)")
        self.assertEqual(P.member_status({"guid": "US-6000001-B1", "type": "USPAT", "filed": "1999-01-01", "related": []}, set(), TODAY),
                         "Patent, expired (term ended)")


class Gazette(unittest.TestCase):
    PAGE = """<b>September 22, 2026</b>
      <a href="#ref2">Notice of Expiration of Patents Due to Failure to Pay Maintenance Fee</a>
      <a href="#ref3">Patents Reinstated Due to the Acceptance of a Late Maintenance Fee</a>
      <a name="ref2"></a> PATENTS WHICH EXPIRED ON July 29, 2026 DUE TO FAILURE TO PAY MAINTENANCE FEES
      8,789,215 13/758,555 07/29/2014 8,789,216 13/846,314 07/29/2014
      <a name="ref3"></a> 8,518,399 12/948,026 11/17/2010 08/27/2013 08/26/2026 <a name="ref4"></a>"""

    def test_parse(self):
        issued, lapsed, reinstated = uspto.parse_gazette(self.PAGE)
        self.assertEqual(issued, "2026-09-22")
        self.assertEqual([x["pn"] for x in lapsed], ["8789215", "8789216"])
        self.assertEqual(lapsed[0]["expired"], "2026-07-29")
        self.assertEqual(reinstated, ["8518399"])

    def test_issue_link_ages_out(self):
        self.assertEqual(uspto.gazette_url(38, "2026-09-22", TODAY), "https://patentsgazette.uspto.gov/week38/OG/TOC.htm")
        self.assertEqual(uspto.gazette_url(38, "2025-09-23", TODAY), uspto.GAZETTE_HOME)

    def test_old_cache_gets_week(self):
        import json, tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as d:
            Path(d, "week07.json").write_text(json.dumps({"date": "2026-02-17", "lapsed": [], "reinstated": []}))
            self.assertEqual(uspto.gazette_week(7, Path(d), dt.date(2026, 10, 1))["week"], 7)


class Drawings(unittest.TestCase):
    def test_shrink_keeps_ink_and_is_valid(self):
        out, w, h = shrink_sheet(one_bit_png(64, 160, black_rows=range(100, 104)))
        dw, dh, depth, rows = decode_gray_png(out)
        self.assertEqual((dw, dh, depth), (w, h, 2))
        self.assertTrue(any(b != 0xFF for r in rows for b in r))

    def test_blank_sheet(self):
        self.assertIsNone(shrink_sheet(one_bit_png(64, 160)))


if __name__ == "__main__":
    unittest.main()


class Classification(unittest.TestCase):
    def test_main_group_prefixes_match_whole(self):
        self.assertEqual(P.field_of(["G06F1/16"]), "electronics")
        self.assertEqual(P.field_of(["G06F12/02"]), "software")
        self.assertEqual(P.field_of(["G06T7/00"]), "ai")
        self.assertEqual(P.field_of(["G06T11/00"]), "software")

    def test_every_section_lands_somewhere_sensible(self):
        for code, field in [("H10D30/60", "chips"), ("H04L5/00", "telecom"), ("H04L67/10", "software"), ("H02M3/156", "energy"),
                            ("F41A9/83", "defense"), ("F41B5/00", "sports"), ("H04N23/00", "imaging"), ("C12M1/00", "biotech"), ("C09K8/52", "materials")]:
            self.assertEqual(P.field_of([code]), field, code)


class Website(unittest.TestCase):
    def setUp(self):
        import website
        self.W = website

    def entry(self, **k):
        e = {"id": "US-9000001-B2", "st": "lapsed", "f": "2014-03-01", "e": "2013-03-01", "p": "2017-05-02", "x": "2021-05-02", "fam": 1, "og": {"d": "2021-07-06"}}
        e.update(k)
        return e

    def test_fee_schedule(self):
        fees = self.W.fee_schedule(self.entry())
        self.assertEqual([f[2] for f in fees], ["missed", "never", "never"])  # lapsed at the 4th anniversary
        fees = self.W.fee_schedule(self.entry(x="2025-05-02"))
        self.assertEqual([f[2] for f in fees], ["paid", "missed", "never"])
        self.assertEqual(fees[0][1], "2020-11-02")
        self.assertIsNone(self.W.fee_schedule(self.entry(st="expired")))

    def test_timeline_sorted_and_labelled(self):
        ev = self.W.timeline_events(self.entry(), {"family": [{"k": "application", "f": "2014-03-01", "p": "2015-09-03"}]})
        self.assertEqual([t for _, t, _ in ev][:4], ["Earliest priority date", "Application filed", "Application published", "Patent granted"])
        self.assertEqual(ev, sorted(ev, key=lambda x: x[0]))
        svg = self.W.timeline_svg(ev)
        self.assertTrue(svg.startswith("<svg") and "Patent expired" in svg)

    def test_claims_indent_dependents_and_map_them(self):
        cl = [[1, "A cup."], [2, "The cup of claim 1, with a lid."], [3, "The cup of claim 2, red."], [4, "A method."]]
        lst, cmap = self.W.claim_list(cl), self.W.claim_map(cl)
        self.assertEqual(lst.count('class="ind"'), 2)
        self.assertIn('class="dep d2" id="claim-3"', lst)
        self.assertIn('href="#claim-3"', cmap)
        self.assertIn("2 claims build on it", cmap)

    def test_figure_list_stops_where_it_starts_over(self):
        figs = ["FIG. 1 shows a cup", "FIGS. 2-3 show a lid", "FIG. 4 is a view", "FIGS. 1 and 2 show the cup again"]
        self.assertEqual(self.W.figure_lines(figs), figs[:3])

    def test_cite_refs(self):
        self.assertEqual(self.W.cite_ref("2015/0025423")[0], "US 2015/0025423")
        self.assertEqual(self.W.cite_ref("7038588")[0], "US 7,038,588")
        self.assertIn("USD512345S", self.W.cite_ref("D512345")[1])

    def test_why_free_mentions_dates(self):
        checks, warn = self.W.why_free(self.entry())
        self.assertIn("May 2, 2021", checks[0])
        self.assertIn("July 6, 2021", checks[0])
