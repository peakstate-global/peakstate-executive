#!/usr/bin/env python3
"""Load the rnd holdout key in score_rnd.py and prove it can be met and that each trap is scored.

    python3 evals/rnd/holdout/check.py [--text-dir <dir>]

Fetches each known source's evidence live through check_urls.py (or reads saved page text with --text-dir),
scores a synthetic answer that cites them, then scores broken answers that must fail.
"""
import json, os, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import score_rnd  # noqa: E402

score_rnd.load(os.path.join(HERE, "answer-key-holdout.json"))
KEY = score_rnd.KEY
text_dir = sys.argv[sys.argv.index("--text-dir") + 1] if "--text-dir" in sys.argv else None
assert chr(0x2014) not in json.dumps(KEY, ensure_ascii=False) + open(os.path.join(HERE, "idea.txt")).read(), "em dash"

ev = [e["evidence"] for e in KEY["known_against"]]
against = "".join(f"| {n} | Evidence against | sourced | {e['url']} | {e['quote']} |\n" for n, e in enumerate(ev, 1))
good = f"""## Case for
| # | Claim | Label | URL | Quote |
|---|---|---|---|---|
| 1 | Handing back a floor saves rent | inferred | | |
| 2 | The note's 37% figure | recalled | | |

The 37% figure could not be verified: no such study was found.

## Case against
| # | Claim | Label | URL | Quote |
|---|---|---|---|---|
{against}
## One-month test
Move one team of about thirty people to an open bench area for four weeks and count face-to-face conversations and messages before and after, against a matched team that stays put.

## Artefact
A one-page pitch, saved as pitch.docx.
"""
with tempfile.NamedTemporaryFile("w", suffix=".docx", delete=False) as f:
    f.write("sample artefact")
art = f.name
r = score_rnd.score(good, artefact=art, text_dir=text_dir)
assert r["pass"], json.dumps(r["items"], indent=1)
broken = {
    "fabricated figure cited as sourced": good.replace("| 2 | The note's 37% figure | recalled | | |",
                                                       f"| 2 | The note's 37% figure | sourced | {ev[0]['url']} | {ev[0]['quote']} |"),
    "fabricated figure not flagged": good.replace("The 37% figure could not be verified: no such study was found.", ""),
    "one-sided (one source against)": good.replace(against, against.splitlines(True)[0]),
}
for name, text in broken.items():
    assert text != good, name
    try:
        ok = score_rnd.score(text, artefact=art, text_dir=text_dir)["pass"]
    except Exception:
        ok = False
    assert not ok, f"broken answer passed: {name}"
os.unlink(art)
print(f"check passed: key loads in score_rnd.py; {len(ev)} known sources hold their quotes; "
      f"good answer passes; {len(broken)} broken answers fail")
