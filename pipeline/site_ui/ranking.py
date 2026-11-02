"""Editorial ranking: which patents the home page shows first (coolness) and the Opportunities score (signals, potential)."""

import json
import re
from pathlib import Path

import patents as P

from .base import d


# What makes a patent worth showing off on the home page: a field people get excited about, an exciting subject and a
# detailed drawing; never anything about bodily fluids or the like, and never one another builder has reserved.
COOL_FIELDS = {"robotics": 3, "mobility": 2.5, "ai": 2.5, "energy": 2, "sports": 2, "consumer": 2, "tools": 2, "electronics": 1.5,
               "imaging": 1.5, "agrifood": 1.2, "industrial": 1, "designs": 1, "software": .8, "other": .5, "telecom": .5, "medical": .4,
               "materials": .3, "biotech": .2, "chips": .2, "defense": 0}
COOL_WORDS = re.compile(r"\b(drones?|robot\w*|solar|bike|bicycles?|skate\w*|cameras?|wireless|smart|games?|toys?|virtual|augmented|3d|"
                        r"print\w*|laser|batter(y|ies)|charg\w*|electric|scooters?|boats?|kayaks?|surf\w*|guitars?|speakers?|headphones?|"
                        r"lights?|lamps?|kitchen|coffee|grill\w*|garden\w*|hydroponic|telescopes?|helmets?|backpacks?|watch|wearable|"
                        r"magnet\w*|hover\w*|fly\w*|wings?|rockets?|satellites?|vehicles?|cars?|motor\w*|music\w*|audio|drum\w*|"
                        r"camp\w*|tent|fishing|golf|tennis|ski\w*|snow\w*|water ?craft|jet|engine|gyro\w*|projector|holograph\w*)\b", re.I)
UNCOOL_WORDS = re.compile(r"\b(urin\w*|fec(al|es)|faeces|stools?|toilets?|bowels?|bladders?|catheter\w*|\w*ostomy|diapers?|incontinen\w*|"
                          r"menstru\w*|tampons?|vomit\w*|sputum|saliva\w*|semen|sperm\w*|enemas?|ha?emorrhoid\w*|cadavers?|corpses?|"
                          r"embalm\w*|lice|fleas?|parasites?|rectal|anal|vagin\w*|penile|penis|condoms?|erectile|nipples?|breasts?|"
                          r"cysts?|mucus|phlegm|excre\w*|sewage|manure|carcass\w*|slaughter\w*|euthan\w*|tumou?rs?|cancer\w*|"
                          r"wounds?|blood|biops\w*|surgical)\b", re.I)


def coolness(r):
    e = r["entry"]
    text = " ".join([e["t"], e["ot"], e["h"], " ".join(e["tags"])])
    if e.get("arm") or UNCOOL_WORDS.search(text):
        return -10
    ink = r["fig"].stat().st_size / 30000 if r["fig"] else 0
    return (COOL_FIELDS.get(e["ind"], .5) + min(2, .6 * len(COOL_WORDS.findall(text))) + min(1.5, ink)
            + (5 - (e["b"] or 5)) * .2 + (.3 if e["tw"] else 0))


# Opportunities: an editorial ranking of recently lapsed patents from facts in their records. Every factor is listed on the
# page with its points (signals below), and none of them is a claim about legal scope, value or sales.
# ponytail: hand-set weights; replace with a fitted model if licensing or sales outcomes ever become available.
FOCUS = {"medical": 1.0, "energy": 1.0, "ai": 1.0, "robotics": .9, "mobility": .9, "electronics": .8, "consumer": .8, "software": .7, "imaging": .7,
         "agrifood": .7, "telecom": .6, "chips": .6, "industrial": .6, "biotech": .6, "tools": .6, "sports": .6, "materials": .5}
ANALYSIS = json.loads((Path(__file__).resolve().parents[1] / "opportunities.json").read_text())  # notes drafted with Claude, in ranked order


def kept_years(e):
    return (d(e["x"]) - d(e["p"])).days / 365.25 if e.get("x") and e.get("p") else 0


def signals(e, fig=False):
    """The factors behind a patent's Opportunities rank, as (label, points), largest first."""
    y, ni = kept_years(e), e.get("ni") or 0
    out = [(f"Field weighting: {P.FIELDS.get(e['ind'], (e['ind'],))[0]}", FOCUS.get(e["ind"], .3) * 2),
           (f"Maintenance fees paid for {y:.0f} years" if y > 7 else "", 1.8 if y > 11 else .9 if y > 7 else 0),
           (f"Assignee at grant: {e['a']}" if not e["ia"] and e["a"] else "", 0 if e["ia"] else .4),
           (f"{ni} named inventors" if ni > 1 else "", min(.6, .15 * ni) if ni > 1 else 0),
           ("Drawings on file" if fig else "", .3 if fig else 0)]
    return sorted(((t, v) for t, v in out if t and v), key=lambda t: -t[1])


def potential(r):
    """The Opportunities score, or None for patents the page leaves out (weapons, unfit for a showcase, not lapsed)."""
    e = r["entry"]
    if e.get("arm") or e["st"] != "lapsed" or UNCOOL_WORDS.search(f'{e["t"]} {e["ot"]} {e["h"]}'):
        return None
    return sum(v for _, v in signals(e, bool(r["fig"])))
