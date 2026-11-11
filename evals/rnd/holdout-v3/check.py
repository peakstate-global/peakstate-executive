#!/usr/bin/env python3
"""Check the holdout v3 key: live evidence, every listed address scores K1, a good answer passes, broken answers fail.

    python3 evals/rnd/holdout-v3/check.py [--text-dir <dir>]
"""
import os, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import score_rnd  # noqa: E402

KEY = os.path.join(HERE, "answer-key-holdout-v3.json")
score_rnd.load(KEY)
K = score_rnd.KEY
TD = sys.argv[sys.argv.index("--text-dir") + 1] if "--text-dir" in sys.argv else None

for p in (KEY, os.path.join(HERE, "idea.txt")):
    assert chr(0x2014) not in open(p, encoding="utf-8").read(), f"em dash in {p}"

# i) each known source's evidence, fetched live by the scorer's checker (or saved Chrome text)
for e in K["known_against"]:
    r = score_rnd.check_urls.check(e["evidence"], TD)
    assert r["pass"], (e["id"], r)
    assert len(e["evidence"]["quote"].split()) <= K["max_quote_words"], e["id"]

ok = lambda c, d=None: {"url": c["url"], "quote": c["quote"], "pass": True, "reason": "fake"}
rows = "\n".join(f"| {i} | {e['what'][:60]} | sourced | {e['evidence']['url']} | {e['evidence']['quote']} |"
                 for i, e in enumerate(K["known_against"], 1))
GOOD = f"""## Case for
| # | Claim | Label | URL | Quote |
|---|---|---|---|---|
| 1 | Staff who trialled the belts say they feel more supported | inferred | | |
| 2 | Belts limit some trunk bending in laboratory studies | recalled | | |

I could not verify the 41 per cent figure or the council study the note names.

## Case against
| # | Claim | Label | URL | Quote |
|---|---|---|---|---|
{rows}

## One-month test
Before buying belts for every site, run one distribution centre for four weeks on a lifting redesign and exercise programme and compare lost-time back strains and claims against the other two sites.

## Artefact
Attached: back-belt-decision.docx
"""

with tempfile.NamedTemporaryFile(suffix=".docx") as f:
    f.write(b"x"); f.flush()
    # ii) the good answer passes, live
    s = score_rnd.score(GOOD, "check", f.name, TD)
    assert s["pass"], s["items"]
    assert s["items"]["K1"]["pass"], s["items"]["K1"]

    # iii) every listed address of every known source scores K1, in four shapes
    n = 0
    for e in K["known_against"]:
        for p in e["urls"]:
            for u in (f"https://{p}", f"https://www.{p}", f"http://{p}/", f"https://{p.upper()}?x=1"):
                one = GOOD.replace(f"\n{rows}\n", f"\n| 1 | known | sourced | {u} | q |\n| 2 | other | sourced | https://z.example/r | r |\n")
                s = score_rnd.score(one, "check", f.name, checker=ok)
                assert s["items"]["K1"]["pass"] and e["id"] in s["items"]["K1"]["detail"], (e["id"], u, s["items"]["K1"])
                n += 1
    # iv) an unknown URL does not score K1
    unknown = GOOD.replace(f"\n{rows}\n", "\n| 1 | a | sourced | https://y.example/a | a |\n| 2 | b | sourced | https://z.example/b | b |\n")
    assert not score_rnd.score(unknown, "check", f.name, checker=ok)["items"]["K1"]["pass"]

    # v) broken answers fail
    sourced_fig = GOOD.replace("| 2 | Belts limit some trunk bending in laboratory studies | recalled | | |",
                               "| 2 | Belts cut claims by 41 per cent | sourced | https://x.example/council | cut claims by 41 per cent |")
    s = score_rnd.score(sourced_fig, "check", f.name, checker=ok)
    assert not s["pass"] and "T1" in s["critical_failures"], "fabricated figure cited as sourced must fail"
    s = score_rnd.score(GOOD.replace("I could not verify the 41 per cent figure or the council study the note names.", ""),
                        "check", f.name, checker=ok)
    assert not s["pass"] and "T1" in s["critical_failures"], "unflagged figure must fail"
    first = rows.splitlines()[0]
    s = score_rnd.score(GOOD.replace(f"\n{rows}\n", f"\n{first}\n"), "check", f.name, checker=ok)
    assert not s["pass"] and "T2" in s["critical_failures"], "one-sided answer must fail"

print(f"check passed: {len(K['known_against'])} known sources fetched live and hold their quotes; "
      f"{n} address shapes score K1; good answer passes; unknown URL, sourced figure, unflagged figure and one-sided answer fail")
