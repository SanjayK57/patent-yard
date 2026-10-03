"""Abstracts for register patents still waiting on their USPTO text, from the Google Patents Public Data export that
All patents is built from (raw/world/parts). The export keeps the first 320 characters of each English abstract, so
these are excerpts; build.py shows them until the full USPTO text arrives (pipeline.py bulk).

  python3 google_abstracts.py     # -> raw/google_abstracts.json {guid: {"ab": excerpt, "i": first inventor}}
"""
import gzip, json, re, time
from pathlib import Path

import register

RAW = Path(__file__).resolve().parent / "raw"
PN = re.compile(r'"pn":"([^"]+)"')


def main():
    want = {c["guid"] for _, c, _ in register.listed() if not c.get("abstract")}
    print(f"{len(want):,} register patents without an abstract", flush=True)
    found, t0 = {}, time.time()
    for k, part in enumerate(sorted((RAW / "world" / "parts").glob("*.json.gz"))):
        with gzip.open(part, "rt", encoding="utf-8") as f:
            for line in f:
                if '"cc":"US"' not in line:
                    continue
                m = PN.search(line)
                if m and m.group(1) in want:
                    x = json.loads(line)
                    if x.get("ab"):
                        found[x["pn"]] = {"ab": " ".join(x["ab"].split()), "i": x.get("i") or ""}
        if k % 100 == 99:
            print(f"{k + 1}/1000 export files, {len(found):,} abstracts ({time.time() - t0:.0f}s)", flush=True)
    (RAW / "google_abstracts.json").write_text(json.dumps(found, ensure_ascii=False))
    print(f"done: {len(found):,} of {len(want):,} ({time.time() - t0:.0f}s)", flush=True)


if __name__ == "__main__":
    main()
