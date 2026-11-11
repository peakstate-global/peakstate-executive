#!/usr/bin/env python3
"""Check R&D holdout v5: live evidence, K1 address coverage, good answer passes, broken answers fail.

    python3 evals/rnd/holdout-v5/check.py [--text-dir <dir>]

Fetches each known source's evidence live (about one minute). Prints one line that starts "check passed:".
"""
import os, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import score_rnd  # noqa: E402
import check_urls  # noqa: E402

KEY_PATH = os.path.join(HERE, "answer-key-holdout-v5.json")
score_rnd.load(KEY_PATH)
KEY = score_rnd.KEY
td = sys.argv[sys.argv.index("--text-dir") + 1] if "--text-dir" in sys.argv else None

for name in ("idea.txt", "answer-key-holdout-v5.json"):
    assert "\u2014" not in open(os.path.join(HERE, name), encoding="utf-8").read(), f"em dash in {name}"

# i) every evidence quote holds live, and is within the quote limit
live = {}
for e in KEY["known_against"]:
    ev = e["evidence"]
    assert len(ev["quote"].split()) <= 25, e["id"]
    r = check_urls.check(ev, td)
    assert r["pass"], (e["id"], r)
    live[(ev["url"], ev["quote"])] = r
    assert any(ev["url"].split("://")[1].removeprefix("www.").casefold().startswith(p.casefold()) for p in e["urls"]), e["id"]

def checker(c, d=None):  # known evidence was checked live above; every other address is treated as passing
    return live.get((c["url"], c["quote"])) or {"url": c["url"], "quote": c["quote"], "pass": True, "reason": "fake"}

e1, e2 = KEY["known_against"][0]["evidence"], KEY["known_against"][1]["evidence"]
GOOD = f"""## Case for
| # | Claim | Label | URL | Quote |
|---|---|---|---|---|
| 1 | Staff at the taster store liked the programme | inferred | | |
| 2 | The note's 41% sick leave figure | recalled | | |

I could not verify the 41% figure or the council named in the note.

## Case against
| # | Claim | Label | URL | Quote |
|---|---|---|---|---|
| 1 | A retail wellness trial found no effect on absenteeism | sourced | {e1['url']} | {e1['quote']} |
| 2 | A second trial found no effect on spending or productivity | sourced | {e2['url']} | {e2['quote']} |

## One-month test
Offer the health check at four matched stores only, keep four similar stores as a comparison, and compare unplanned sick leave and turnover across the eight stores before signing any contract.

## Artefact
Attached: proposal-review.docx
"""

with tempfile.NamedTemporaryFile(suffix=".docx") as f:
    f.write(b"x"); f.flush()
    s = score_rnd.score(GOOD, "check", f.name, checker=checker)
    assert s["pass"], s["items"]

    # ii) every listed address scores K1, in four shapes
    n = 0
    for e in KEY["known_against"]:
        for p in e["urls"]:
            for u in (f"https://{p}", f"https://www.{p}", f"http://{p}/", f"https://{p.upper()}?x=1"):
                t = GOOD.replace(e1["url"], u).replace(e2["url"], "https://other.example/x")
                k = score_rnd.score(t, "check", f.name, checker=checker)["items"]["K1"]
                assert k["pass"] and e["id"] in k["detail"], (u, k)
                n += 1

    # iii) broken answers fail
    bad = GOOD.replace("| recalled | | |", "| sourced | https://c.example/council | cut unplanned sick leave by 41% |")
    assert not score_rnd.score(bad, "check", f.name, checker=checker)["items"]["T1"]["pass"], "sourced fabricated figure"
    try:
        score_rnd.score(GOOD.replace("## Case against", "## Against"), checker=checker)
        raise AssertionError("missing section passed")
    except score_rnd.Malformed:
        pass
    long = GOOD.replace(f"{e2['quote']} |", f"{e2['quote']} " + "word " * 30 + "|")
    assert not score_rnd.score(long, "check", f.name, checker=checker)["items"]["L1"]["pass"], "long quote"
    none = GOOD.replace(e1["url"], "https://a.example/one").replace(e2["url"], "https://b.example/two")
    assert not score_rnd.score(none, "check", f.name, checker=checker)["items"]["K1"]["pass"], "no known source"

print(f"check passed: {len(KEY['known_against'])} known sources live, {sum(len(e['urls']) for e in KEY['known_against'])} "
      f"addresses score K1 in {n} shapes, good answer passes, 4 broken answers fail")
