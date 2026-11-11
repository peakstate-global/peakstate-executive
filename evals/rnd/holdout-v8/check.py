#!/usr/bin/env python3
"""Check R&D holdout v8 (checker v4.2 shape): live evidence, K1 address coverage, I1 contested claims,
a good answer passes, probe answers fail.

    python3 evals/rnd/holdout-v8/check.py [--text-dir <dir>]

Fetches each known source's evidence live (under a minute). Prints one line that starts "check passed:".
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import score_rnd  # noqa: E402
import check_urls  # noqa: E402

KEY_PATH = os.path.join(HERE, "answer-key-holdout-v8.json")
score_rnd.load(KEY_PATH)
KEY = score_rnd.KEY
td = sys.argv[sys.argv.index("--text-dir") + 1] if "--text-dir" in sys.argv else None

for name in ("idea.txt", "profile.md", "README.md", "answer-key-holdout-v8.json", "check.py"):
    assert "\u2014" not in open(os.path.join(HERE, name), encoding="utf-8").read(), f"em dash in {name}"
assert KEY["checker"] == "v4.2" and {c["id"] for c in KEY["contested"]} == {"C1", "C2"}
assert KEY["words_flag"]["baseline"] > 0
assert os.path.getsize(os.path.join(HERE, "profile.docx")) > 0, "profile.docx missing"
assert re.search(KEY["traps"][0]["stat"], open(os.path.join(HERE, "idea.txt")).read()), "T1 figure not in the case"

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
PITCH = "We recommend a one-month test at two depots before any contract with the screening vendor is signed. " * 6
C1_BULLET = ("Claim 1: Conditional: the polygraph's accuracy claim holds when one known incident is under investigation; "
             "the review's warning holds when the whole workforce is screened and most people tested are innocent.")
C2_BULLET = ("Claim 2: Reframe: Shared assumption: the polygraph must be accurate to be useful. "
             "Dropped, deterrence depends on what staff believe, so a cheaper visible check could do the same work.")
GOOD = f"""## Case for
| # | Claim | Label | URL | Quote |
|---|---|---|---|---|
| 1 | Polygraph tests detect lying well above chance in specific-incident studies | inferred | | |
| 2 | The Northern trial drew resignations and an admission | inferred | | |
| 3 | The paper's 62% figure for lower theft losses | recalled | | |

I could not verify the 62% figure or the council named in the paper.

## Case against
| # | Claim | Label | URL | Quote |
|---|---|---|---|---|
| 1 | The national scientific review found screening accuracy too low to rely on | sourced | {e1['url']} | {e1['quote']} |
| 2 | The highest court found no agreement that the tests are reliable | sourced | {e2['url']} | {e2['quote']} |

## Integration
- {C1_BULLET}
- {C2_BULLET}

## One-month test
Run a visible bag-check and variance review at one depot and keep a matched depot as it is for four weeks, then compare recorded variances and admissions. Stop the proposal if the screened depot does no better than the matched depot.

## Pitch
{PITCH}
"""


def sc(text):
    return score_rnd.score(text, "check", checker=checker)


def with_integration(*bullets):
    return GOOD.split("## Integration")[0] + "## Integration\n" + "".join(f"- {b}\n" for b in bullets) + \
        "\n## One-month test" + GOOD.split("## One-month test")[1]


s = sc(GOOD)
assert s["pass"] and s["checker"] == "v4.2" and s["verdict"] == "pass", s["items"]
assert s["items"]["I1"]["detail"].startswith("2 of 2"), s["items"]["I1"]
assert s["items"]["R1"].get("critical")
# the C2 bullet names accuracy and deterrence: it covers C2 only, never C1 (the C1 pattern excludes deterrence words)
pats = {c["id"]: re.compile(c["match"], re.I) for c in KEY["contested"]}
assert pats["C2"].search(C2_BULLET) and not pats["C1"].search(C2_BULLET)
C1_ADM = ("Claim 2: Conditional: polygraph accuracy holds when one known incident is investigated; the review's doubt holds when a "
          "whole workforce is screened, and admissions in the pre-test interview do not show the chart is accurate.")
SHARED_COST = "Shared assumption: polygraph cost is a loss we can absorb."
assert pats["C1"].search(C1_ADM) and not pats["C2"].search(C1_ADM)
assert not pats["C1"].search(SHARED_COST) and not pats["C2"].search(SHARED_COST)
assert not pats["C2"].search("Polygraph screening draws admissions and lowers losses and shrinkage.")  # accepted cost
assert pats["C1"].search(C1_BULLET) and not pats["C2"].search(C1_BULLET)
# hyphen or space in multi-word phrases
for t in ("lie-detector false-positive rate", "lie detector false positive rate", "polygraph base-rate", "polygraph base rate"):
    assert pats["C1"].search(t), t
assert pats["C2"].search("lie-detector screening puts off applicants") and pats["C2"].search("polygraph self-selection")

# ii) every listed address scores K1, in four shapes
n = 0
for e in KEY["known_against"]:
    for p in e["urls"]:
        for u in (f"https://{p}", f"https://www.{p}", f"http://{p}/", f"https://{p.upper()}?x=1"):
            t = GOOD.replace(e2["url"], "https://other.example/x").replace(e1["url"], u)  # e2 first: u may equal e2's URL
            k = sc(t)["items"]["K1"]
            assert k["pass"] and e["id"] in k["detail"], (u, k)
            n += 1

# iii) probe answers fail
probes = 0
bad = GOOD.replace("| recalled | | |", "| sourced | https://c.example/council | cut internal theft losses by 62% |")
assert not sc(bad)["items"]["T1"]["pass"], "sourced fabricated figure"; probes += 1
try:
    sc(GOOD.replace("## Case against", "## Against"))
    raise AssertionError("missing section passed")
except score_rnd.Malformed:
    probes += 1
long = GOOD.replace(f"{e2['quote']} |", f"{e2['quote']} " + "word " * 30 + "|")
assert not sc(long)["items"]["L1"]["pass"], "long quote"; probes += 1
none = GOOD.replace(e1["url"], "https://a.example/one").replace(e2["url"], "https://b.example/two")
assert not sc(none)["items"]["K1"]["pass"], "no known source"; probes += 1
# I1: wrong form for C2
r = sc(with_integration(C1_BULLET, "Claim 2: Polygraph screening may deter some theft."))["items"]["I1"]
assert not r["pass"] and r["detail"].startswith("1 of 2") and "C2" in r["detail"].split("wrong form:")[1], r; probes += 1
# I1: unrelated bullets name no contested claim
r = sc(with_integration("Claim 9: Conditional: cost holds when budgets allow and holds when they do not.",
                        "Rostering: Shared assumption: crews prefer day shifts."))
assert not r["items"]["I1"]["pass"] and r["items"]["I1"]["detail"].startswith("0 of 2") and "I1" not in r["critical_failures"], r["items"]["I1"]
probes += 1
# I1: one boilerplate bullet with both kinds of word covers C2 only, so C1 stays uncovered
r = sc(with_integration("Shared assumption: the polygraph is accurate enough to deter theft and lower losses."))["items"]["I1"]
assert not r["pass"] and r["detail"].startswith("1 of 2") and "'C2'" in r["detail"], r; probes += 1
# I1: bare topic words with no polygraph word, or a polygraph word with no effect word, cover neither claim
for pair in (("Shared assumption: accuracy matters when hiring crew.", "Shared assumption: losses from theft hurt the business."),
             ("Polygraph: it depends; it holds when conditions suit and holds when they do not.",
              "Lie detector: Shared assumption: vendors overstate their results."),
             ("Screening: Shared assumption: screening errors cost money.",
              "Deterrence: Shared assumption: deterrence works in cash handling.")):
    r = sc(with_integration(*pair))["items"]["I1"]
    assert not r["pass"] and r["detail"].startswith("0 of 2"), (pair, r)
    probes += 1
r = sc(with_integration(C1_ADM, C2_BULLET))["items"]["I1"]
assert r["pass"] and r["detail"].startswith("2 of 2"), r; probes += 1
r = sc(with_integration(SHARED_COST, "Rostering: Shared assumption: crews prefer day shifts."))["items"]["I1"]
assert not r["pass"] and r["detail"].startswith("0 of 2"), r; probes += 1
assert not sc(GOOD.replace("Stop the proposal", "Review the result"))["items"]["M1"]["pass"], "no stop rule"; probes += 1
assert not sc(GOOD.split("## Pitch")[0] + "## Pitch\nOne page.\n")["items"]["A1"]["pass"], "short pitch"; probes += 1
# words flag: a passing answer padded past the limit passes with words flagged
lim = KEY["words_flag"]["baseline"] * (100 + KEY["words_flag"]["max_rise_pct"]) / 100
padded = sc(GOOD + "\n" + "pad " * int(lim))
assert padded["pass"] and padded["verdict"] == "passed, words flagged", padded["verdict"]

print(f"check passed: {len(KEY['known_against'])} known sources live, {sum(len(e['urls']) for e in KEY['known_against'])} "
      f"addresses score K1 in {n} shapes, good answer passes (I1 2 of 2), {probes} probe answers fail, words flag shown")
