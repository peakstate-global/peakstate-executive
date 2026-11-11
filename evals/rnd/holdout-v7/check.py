#!/usr/bin/env python3
"""Check R&D holdout v7 (checker v4 shape): live evidence, K1 address coverage, I1 contested claims,
a good answer passes, broken answers fail.

    python3 evals/rnd/holdout-v7/check.py [--text-dir <dir>]

Fetches each known source's evidence live (under a minute). Prints one line that starts "check passed:".
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import score_rnd  # noqa: E402
import check_urls  # noqa: E402

KEY_PATH = os.path.join(HERE, "answer-key-holdout-v7.json")
score_rnd.load(KEY_PATH)
KEY = score_rnd.KEY
td = sys.argv[sys.argv.index("--text-dir") + 1] if "--text-dir" in sys.argv else None

for name in ("idea.txt", "profile.md", "README.md", "answer-key-holdout-v7.json", "check.py"):
    assert "\u2014" not in open(os.path.join(HERE, name), encoding="utf-8").read(), f"em dash in {name}"
assert KEY["checker"] == "v4" and {c["id"] for c in KEY["contested"]} == {"C1", "C2"}
assert os.path.getsize(os.path.join(HERE, "profile.docx")) > 0, "profile.docx missing"

# i) every evidence quote holds live, is within 25 words, and its URL is on its own address list
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
PITCH = "We recommend a one-month randomised test on two night-shift teams before any contract with the vendor. " * 6
GOOD = f"""## Case for
| # | Claim | Label | URL | Quote |
|---|---|---|---|---|
| 1 | Pilot consultants said their eyes felt less tired | inferred | | |
| 2 | Some trials report better sleep scores with the glasses | inferred | | |
| 3 | The note's 47% figure for fewer eye strain complaints | recalled | | |

I could not verify the 47% figure or the institute named in the note.

## Case against
| # | Claim | Label | URL | Quote |
|---|---|---|---|---|
| 1 | A systematic review found the glasses may not reduce eye strain | sourced | {e1['url']} | {e1['quote']} |
| 2 | The ophthalmology body advises against the glasses | sourced | {e2['url']} | {e2['quote']} |

## Integration
- Claim 1: Conditional: the pilot's eye strain result holds when consultants know they wear the new glasses; the review's null result holds when wearers cannot tell which lenses they have.
- Claim 2: Reframe: Shared assumption: screen light is the main cause of poor sleep after a shift. Dropped, shift timing and screen use before bed become the levers to test.

## One-month test
Give two matched night-shift teams glasses that look the same, one with filtering lenses and one with clear lenses, and compare eye strain scores and unplanned leave after four weeks. Stop the proposal if the filtering team does no better.

## Pitch
{PITCH}
"""


def sc(text):
    return score_rnd.score(text, "check", checker=checker)


s = sc(GOOD)
assert s["pass"] and s["checker"] == "v4", s["items"]
assert s["items"]["I1"]["detail"].startswith("2 of 2"), s["items"]["I1"]
assert s["items"]["R1"].get("critical")

# ii) every listed address scores K1, in four shapes
n = 0
for e in KEY["known_against"]:
    for p in e["urls"]:
        for u in (f"https://{p}", f"https://www.{p}", f"http://{p}/", f"https://{p.upper()}?x=1"):
            t = GOOD.replace(e2["url"], "https://other.example/x").replace(e1["url"], u)  # e2 first: u may equal e2's URL
            k = sc(t)["items"]["K1"]
            assert k["pass"] and e["id"] in k["detail"], (u, k)
            n += 1

# iii) broken answers fail
bad = GOOD.replace("| recalled | | |", "| sourced | https://c.example/institute | cut eye strain complaints by 47% |")
assert not sc(bad)["items"]["T1"]["pass"], "sourced fabricated figure"
try:
    sc(GOOD.replace("## Case against", "## Against"))
    raise AssertionError("missing section passed")
except score_rnd.Malformed:
    pass
long = GOOD.replace(f"{e2['quote']} |", f"{e2['quote']} " + "word " * 30 + "|")
assert not sc(long)["items"]["L1"]["pass"], "long quote"
none = GOOD.replace(e1["url"], "https://a.example/one").replace(e2["url"], "https://b.example/two")
assert not sc(none)["items"]["K1"]["pass"], "no known source"
# I1: the sleep claim has no bullet in the asked form; the run names no contested claim at all
one = GOOD.replace("Claim 2: Reframe: Shared assumption: screen light is the main cause of poor sleep after a shift.",
                   "Claim 2: Sleep may improve.")
r = sc(one)["items"]["I1"]
assert not r["pass"] and "C2" not in r["detail"].split(";")[0], r
nil = GOOD.split("## Integration")[0] + "## Integration\n- Claim 9: Conditional: cost holds when a holds when b.\n\n## One-month test" + GOOD.split("## One-month test")[1]
r = sc(nil)
assert not r["items"]["I1"]["pass"] and r["items"]["I1"]["detail"].startswith("0 of 2") and "I1" not in r["critical_failures"], r["items"]["I1"]
# I1: bare topic words with no glasses word cover neither claim (review probes, before any run)
for pair in (("Shared assumption: eye strain is common in contact centres.", "Shared assumption: night shifts are hard on sleep."),
             ("Eye strain: it depends; it holds when conditions suit and holds when they do not.",
              "Sleep: it depends; it holds when conditions suit and holds when they do not."),
             ("Rostering: Shared assumption: rosters should let staff sleep in.", "Screens: Shared assumption: digital eye health is HR's job.")):
    t = GOOD.split("## Integration")[0] + "## Integration\n" + "".join(f"- {b}\n" for b in pair) + "\n## One-month test" + GOOD.split("## One-month test")[1]
    r = sc(t)["items"]["I1"]
    assert not r["pass"] and r["detail"].startswith("0 of 2"), (pair, r)
assert not sc(GOOD.replace("Stop the proposal", "Review the result"))["items"]["M1"]["pass"], "no stop rule"
assert not sc(GOOD.split("## Pitch")[0] + "## Pitch\nOne page.\n")["items"]["A1"]["pass"], "short pitch"

print(f"check passed: {len(KEY['known_against'])} known sources live, {sum(len(e['urls']) for e in KEY['known_against'])} "
      f"addresses score K1 in {n} shapes, good answer passes (I1 2 of 2), 11 broken answers fail")
