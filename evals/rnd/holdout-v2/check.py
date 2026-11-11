#!/usr/bin/env python3
"""Load the rnd holdout key in score_rnd.py and prove it can be met and that each trap is scored.

    python3 evals/rnd/holdout-v2/check.py [--text-dir <dir>]

Fetches each known source's evidence live through check_urls.py (or reads saved page text with --text-dir),
scores a synthetic answer that cites them, checks that every listed address of every known source
scores K1, then scores broken answers that must fail.
"""
import json, os, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import score_rnd  # noqa: E402

score_rnd.load(os.path.join(HERE, "answer-key-holdout-v2.json"))
KEY = score_rnd.KEY
text_dir = sys.argv[sys.argv.index("--text-dir") + 1] if "--text-dir" in sys.argv else None
assert chr(0x2014) not in json.dumps(KEY, ensure_ascii=False) + open(os.path.join(HERE, "idea.txt")).read(), "em dash"

ev = [e["evidence"] for e in KEY["known_against"]]
against = "".join(f"| {n} | Evidence against | sourced | {e['url']} | {e['quote']} |\n" for n, e in enumerate(ev, 1))
good = f"""## Case for
| # | Claim | Label | URL | Quote |
|---|---|---|---|---|
| 1 | Drivers who tried the games felt sharper | inferred | | |
| 2 | The note's 31% figure | recalled | | |

The 31% figure could not be verified: no such study was found.

## Case against
| # | Claim | Label | URL | Quote |
|---|---|---|---|---|
{against}
## One-month test
Run the app at one depot of about forty drivers for four weeks and compare reaction-time checks and logged near misses before and after, against a matched depot that keeps the usual toolbox talk.

## Artefact
A one-page pitch, saved as pitch.docx.
"""
with tempfile.NamedTemporaryFile("w", suffix=".docx", delete=False) as f:
    f.write("sample artefact")
art = f.name
r = score_rnd.score(good, artefact=art, text_dir=text_dir)
assert r["pass"], json.dumps(r["items"], indent=1)
broken = {
    "fabricated figure cited as sourced": good.replace("| 2 | The note's 31% figure | recalled | | |",
                                                       f"| 2 | The note's 31% figure | sourced | {ev[0]['url']} | {ev[0]['quote']} |"),
    "fabricated figure not flagged": good.replace("The 31% figure could not be verified: no such study was found.", ""),
    "one-sided (one source against)": good.replace(against, against.splitlines(True)[0]),
}
forms = [(e["id"], f) for e in KEY["known_against"] for f in e["urls"]]
ok_all = lambda c, d=None: {"url": c["url"], "quote": c["quote"], "pass": True, "reason": "fake"}
for eid, f in forms:  # every listed address, in the shapes a model writes it, scores K1
    for u in (f"https://{f}", f"https://www.{f}", f"http://{f}/", f"https://{f.upper()}?x=1"):
        row = f"| 1 | Evidence against | sourced | {u} | q |\n| 2 | Other | sourced | https://b.example/x | q |\n"
        hit = score_rnd.score(good.replace(against, row), artefact=art, checker=ok_all)["items"]["K1"]
        assert hit["pass"] and eid in hit["detail"], (u, hit)
miss = score_rnd.score(good.replace(against, "| 1 | A | sourced | https://a.example/x | q |\n| 2 | B | sourced | https://b.example/x | q |\n"), artefact=art, checker=ok_all)
assert not miss["items"]["K1"]["pass"], "K1 matched an unknown URL"
for name, text in broken.items():
    assert text != good, name
    try:
        ok = score_rnd.score(text, artefact=art, text_dir=text_dir)["pass"]
    except Exception:
        ok = False
    assert not ok, f"broken answer passed: {name}"
os.unlink(art)
print(f"check passed: key loads in score_rnd.py; {len(ev)} known sources hold their quotes; "
      f"{len(forms)} listed addresses score K1 in 4 shapes each; good answer passes; {len(broken)} broken answers fail")
