# R&D holdout case

**Version:** holdout v1, 7 November 2026. Written without reading any prompt or round output.
**Purpose:** a prompt tuned on tier 2 is checked on an idea its author never saw. Same trap types as
tier 2 (a tempting fabricated statistic; one-sided sources), in a new form and a different industry.
The organisation and the note are invented and labelled sample. The known sources are real public research.

| File | What it is |
|---|---|
| `idea.txt` | The case: one idea with known strong evidence against it. |
| `answer-key-holdout.json` | The key, in the tier-2 shape (traps, known sources against by URL, rules, pass rule). |
| `check.py` | Loads the key in `score_rnd.py`, fetches each known source live, and shows a good answer passes and broken answers fail. |

## How to score a run

    python3 evals/rnd/score_rnd.py <output.md> --key evals/rnd/holdout/answer-key-holdout.json --artefact <file> [--text-dir <dir>]

## Known sources: fetched and checked

Each known source's evidence URL was fetched with `rnd/check_urls.py` on 7 November 2026, about
20:55 AEST, and each passed: HTTP 200, no soft 404, and the page holds the quote recorded in the key.
The publisher pages of two sources refuse a script (HTTP 403),
so the key's evidence URLs are the open copies that a script can fetch.
