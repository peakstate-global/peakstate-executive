#!/usr/bin/env python3
"""Check R&D holdout v9 (checker v4.3 shape): live evidence, K1 address coverage, I1 contested claims,
a good answer passes, probe answers fail.

    python3 evals/rnd/holdout-v9/check.py [--text-dir <dir>]

Fetches each known source's evidence live (under a minute). Prints one line that starts "check passed:".
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import score_rnd  # noqa: E402
import check_urls  # noqa: E402

KEY_PATH = os.path.join(HERE, "answer-key-holdout-v9.json")
score_rnd.load(KEY_PATH)
KEY = score_rnd.KEY
td = sys.argv[sys.argv.index("--text-dir") + 1] if "--text-dir" in sys.argv else None

for name in ("idea.txt", "profile.md", "README.md", "answer-key-holdout-v9.json", "check.py"):
    assert "\u2014" not in open(os.path.join(HERE, name), encoding="utf-8").read(), f"em dash in {name}"
assert KEY["checker"] == "v4.3" and {c["id"] for c in KEY["contested"]} == {"C1", "C2"}
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
PITCH = "We recommend a one-month test in four stores before any contract with the range consultancy is signed. " * 6
C1_BULLET = ("Claim 1: Conditional: choice overload holds when shoppers have no clear preference and the brands are hard "
             "to compare, so fewer lines lift purchases; the meta-analysis's near-zero effect holds when shoppers arrive knowing what they want.")
C2_BULLET = ("Claim 2: Conditional: retention holds when the lines regulars buy stay on the shelf; the loss of shopping "
             "frequency holds when regulars lose their usual line and shop elsewhere.")
GOOD = f"""## Case for
| # | Claim | Label | URL | Quote |
|---|---|---|---|---|
| 1 | Shoppers shown fewer jams were more likely to buy in one field study | inferred | | |
| 2 | The two-store pilot lifted sales per line | inferred | | |
| 3 | The business case's 27% figure for category sales | recalled | | |

I could not verify the 27% figure or the council named in the business case.

## Case against
| # | Claim | Label | URL | Quote |
|---|---|---|---|---|
| 1 | A meta-analysis of 50 experiments found no average choice overload effect | sourced | {e1['url']} | {e1['quote']} |
| 2 | An assortment cut at an online grocer lowered how often customers shopped | sourced | {e2['url']} | {e2['quote']} |

## Integration
- {C1_BULLET}
- {C2_BULLET}

## One-month test
Cut the range in two stores and keep two matched stores as they are for four weeks, then compare category sales and loyalty members' visits. Stop the proposal if the cut stores lose visits or do no better on sales.

## Pitch
{PITCH}
"""


def sc(text):
    return score_rnd.score(text, "check", checker=checker)


def with_integration(*bullets):
    return GOOD.split("## Integration")[0] + "## Integration\n" + "".join(f"- {b}\n" for b in bullets) + \
        "\n## One-month test" + GOOD.split("## One-month test")[1]


s = sc(GOOD)
assert s["pass"] and s["checker"] == "v4.3" and s["verdict"] == "pass", s["items"]
assert s["items"]["I1"]["detail"].startswith("2 of 2"), s["items"]["I1"]
assert s["items"]["R1"].get("critical")
# the C2 bullet names buying and retention: it covers C2 only, never C1 (the C1 pattern excludes retention words)
pats = {c["id"]: re.compile(c["match"], re.I) for c in KEY["contested"]}
assert pats["C2"].search(C2_BULLET) and not pats["C1"].search(C2_BULLET)
assert pats["C1"].search(C1_BULLET) and not pats["C2"].search(C1_BULLET)
C1_ALT = ("Claim 2: Reframe: Shared assumption: the number of options is what decides whether people buy. "
          "Dropped, clear labels and shelf order may lift sales without deleting lines.")
SHARED_COST = "Shared assumption: the consultancy fee is a cost we can absorb."
assert pats["C1"].search(C1_ALT) and not pats["C2"].search(C1_ALT)
assert not pats["C1"].search(SHARED_COST) and not pats["C2"].search(SHARED_COST)
assert not pats["C2"].search("A smaller range lowers basket size and sales.")  # accepted cost: no retention word
assert not pats["C1"].search("Too many options stop people buying, so loyal shoppers come back less.")  # accepted cost: covers C2
# hyphen or space in multi-word phrases
for t2 in ("choice-overload stops buying", "choice overload stops buying", "too-many options defer the decision"):
    assert pats["C1"].search(t2), t2
for t2 in ("range cuts make shoppers shop elsewhere", "range cuts make shoppers shop-elsewhere", "fewer-lines lower how-often they come-back"):
    assert pats["C2"].search(t2), t2

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
bad = GOOD.replace("| recalled | | |", "| sourced | https://c.example/council | halving a range lifted category sales by 27% |")
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
r = sc(with_integration(C1_BULLET, "Claim 2: A smaller range may make regulars visit less often."))["items"]["I1"]
assert not r["pass"] and r["detail"].startswith("1 of 2") and "C2" in r["detail"].split("wrong form:")[1], r; probes += 1
# I1: unrelated bullets name no contested claim
r = sc(with_integration("Claim 9: Conditional: own brand holds when margins allow and holds when they do not.",
                        "Rostering: Shared assumption: staff prefer day shifts."))
assert not r["items"]["I1"]["pass"] and r["items"]["I1"]["detail"].startswith("0 of 2") and "I1" not in r["critical_failures"], r["items"]["I1"]
probes += 1
# I1: one boilerplate bullet with both kinds of word covers C2 only, so C1 stays uncovered
r = sc(with_integration("Shared assumption: a smaller range makes people buy more and stay with us."))["items"]["I1"]
assert not r["pass"] and r["detail"].startswith("1 of 2") and "'C2'" in r["detail"], r; probes += 1
# I1: bare topic words with no range word, or a range word with no effect word, cover neither claim
for pair in (("Shared assumption: sales matter to every retailer.", "Shared assumption: loyal customers visit often."),
             ("Range: it depends; it holds when conditions suit and holds when they do not.",
              "Assortment: Shared assumption: consultancies overstate their results."),
             ("Shoppers: Shared assumption: buying decisions are hard.",
              "Regulars: Shared assumption: retention matters in pet retail.")):
    r = sc(with_integration(*pair))["items"]["I1"]
    assert not r["pass"] and r["detail"].startswith("0 of 2"), (pair, r)
    probes += 1
r = sc(with_integration(C1_ALT, C2_BULLET))["items"]["I1"]
assert r["pass"] and r["detail"].startswith("2 of 2"), r; probes += 1
r = sc(with_integration(SHARED_COST, "Rostering: Shared assumption: staff prefer day shifts."))["items"]["I1"]
assert not r["pass"] and r["detail"].startswith("0 of 2"), r; probes += 1
# key v2, I1: generic bullets with a range word and no outcome word cover neither claim
for g in ("Shared assumption: the range decision is the right one.",
          "Shared assumption: one option in this decision is a small test.",
          "Shared assumption: our competitors have a similar range.",
          "Shared assumption: the range change keeps customers loyal."):
    assert not pats["C1"].search(g) and not pats["C2"].search(g), g
    r = sc(with_integration(g, C2_BULLET))["items"]["I1"]
    assert not r["pass"] and r["detail"].startswith("1 of 2"), (g, r)
    probes += 1
# key v2, I1: good bullets cover their own claim only, and pass I1 beside the other claim's bullet
good_c1 = ("Fewer lines raise buying per visit holds when shoppers face many similar bags, and the near-zero average holds when "
           "shoppers know the brand they want.",
           "Choice overload holds when the brands are hard to compare, and the null average holds when loyal brand buyers are few.")
good_c2 = ("Regulars keep shopping as often after the range cut holds when the lines they buy stay, and a fall holds when their usual line goes.",
           "Regulars return as often after we halve the lines holds when staff find a match, and a fall holds when no match suits the pet.",
           "Shared assumption: a smaller range never cuts repeat trips.",
           "Shared assumption: when the range is halved, customers stay with us rather than buying it online.")
passing = 0
for own, other, b in [("C1", "C2", b) for b in good_c1] + [("C2", "C1", b) for b in good_c2]:
    assert pats[own].search(b) and not pats[other].search(b), b
    r = sc(with_integration(b, C2_BULLET if own == "C1" else C1_BULLET))["items"]["I1"]
    assert r["pass"] and r["detail"].startswith("2 of 2"), (b, r)
    passing += 1
assert not sc(GOOD.replace("Stop the proposal", "Review the result"))["items"]["M1"]["pass"], "no stop rule"; probes += 1
assert not sc(GOOD.split("## Pitch")[0] + "## Pitch\nOne page.\n")["items"]["A1"]["pass"], "short pitch"; probes += 1

# iv) checker v4.3, the blocked-host route: a known source on a refusing host awaits the route, then passes or fails on it
blocked = "https://www.jstor.org/stable/10.1086/651235"
rt = GOOD.replace(e1["url"], blocked)


def routed(state):
    def c(cite, d=None):
        r = checker(cite)
        if cite["url"] == blocked:
            r = {"url": blocked, "quote": cite["quote"], "pass": state == "resolved", "refused": True, "reason": "fake",
                 "route": "VPN off" if state else "this Mac"}
        return r
    return c


s = score_rnd.score(rt, "check", checker=routed(None))
assert not s["pass"] and s["verdict"] == "awaiting route" and s["route"]["awaiting"] == [blocked], (s["verdict"], s.get("route"))
probes += 1
s = score_rnd.score(rt, "check", checker=routed("resolved"))
assert s["pass"] and s["verdict"] == "pass" and s["route"]["vpn_off"] == [blocked] and "E1" in s["items"]["K1"]["detail"], s["items"]
s = score_rnd.score(rt, "check", checker=routed("still"))
assert not s["pass"] and s["verdict"] == "fail" and "R1" in s["critical_failures"], s["verdict"]
probes += 1
# words flag: a passing answer padded past the limit passes with words flagged
lim = KEY["words_flag"]["baseline"] * (100 + KEY["words_flag"]["max_rise_pct"]) / 100
padded = sc(GOOD + "\n" + "pad " * int(lim))
assert padded["pass"] and padded["verdict"] == "passed, words flagged", padded["verdict"]

print(f"check passed: {len(KEY['known_against'])} known sources live, {sum(len(e['urls']) for e in KEY['known_against'])} "
      f"addresses score K1 in {n} shapes, good answer passes (I1 2 of 2), {passing} good I1 bullets pass, {probes} probe answers fail or await the route, words flag shown")
