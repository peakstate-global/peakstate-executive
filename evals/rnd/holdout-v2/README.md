# R&D holdout case, v2

**Version:** holdout v2, 8 November 2026. Written without reading any prompt or round output.
**Purpose:** a prompt tuned on tier 2 is checked on an idea its author never saw. Same trap types as
tier 2 and holdout v1 (a tempting fabricated statistic; one-sided sources; one idea with known strong
evidence against it), in a new form and a different industry from v1. Tier: 2.
The organisation and the note are invented and labelled sample. The known sources are real public research.

**Why v2 exists:** v1 is spent. Its key listed one known source only at an old address, and every run cited the
publisher's current address, so K1 failed. In v2 each known source is listed by every address its publisher
serves: the DOI (with and without `dx.`), each publisher article path, PubMed, PMC and Europe PMC (page and API
forms), and the open copy used as the evidence URL. K1 matches by prefix after the scheme and `www.` are removed,
so trailing slashes, query strings and `.pdf` or `.full` suffixes match too. `check.py` proves this for every
listed address.

| File | What it is |
|---|---|
| `idea.txt` | The case: one idea with known strong evidence against it. |
| `answer-key-holdout-v2.json` | The key, in the tier-2 shape (traps, known sources against by URL, rules, pass rule). |
| `check.py` | Loads the key in `score_rnd.py`, fetches each known source live, shows every listed address scores K1, and shows a good answer passes and broken answers fail. |

## How to score a run

    python3 evals/rnd/score_rnd.py <output.md> --key evals/rnd/holdout-v2/answer-key-holdout-v2.json --artefact <file> [--text-dir <dir>]

Check the key itself (fetches live, about one minute):

    python3 evals/rnd/holdout-v2/check.py

## Known sources: fetched and checked

Each of the four known sources' evidence URLs was fetched with `rnd/check_urls.py` on 8 November 2026,
between 01:05 and 01:19 AEST, and each passed: HTTP 200, no soft 404, and the page holds the quote recorded
in the key. `check.py` ran green at 01:19 AEST. The publisher pages of three sources refuse a script
(HTTP 403), so their evidence URLs are Europe PMC copies a script can fetch (the open full text for one source,
the Europe PMC record with the abstract for the other three). A run that cites a publisher page that refuses a
script needs the page text captured in Chrome and passed with `--text-dir`.

The fabricated statistic was searched for on 8 November 2026 at about 01:15 AEST (WebSearch, two queries).
Neither query found the study or the figure.
