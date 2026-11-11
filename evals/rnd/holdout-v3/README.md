Prompt-tuning tickets must not open this folder.

# R&D holdout case, v3

**Version:** holdout v3, 8 November 2026, separate writer. Written without reading any prompt, round output, earlier holdout case or earlier key values.
**Purpose:** a prompt tuned on tier 2 is checked on an idea its author never saw.
**Trap types:** the same as tier 2 and holdouts v1 and v2. The note holds a tempting fabricated statistic (T1) and one-sided support (T2), and the idea has known strong published evidence against it. The industry and the idea are new.
The organisation and the note are invented and labelled sample. The known sources are real public research and official guidance.

**Why v3 exists:** the v1 and v2 keys each missed an address where a run cited a known source. The v1 key missed the publisher's current article path. The v2 key missed the learned society's own page for the article. In v3, each known source was searched by its exact title and every distinct host and path form was recorded and fetched. The list holds the DOI (`doi.org` and `dx.doi.org`), every publisher path form (current and old), the publisher society's own pages, PubMed, PMC and Europe PMC (page and API forms), and the institutional and open copies on the first results page. K1 matches by prefix after the scheme and a leading `www.` are removed. `check.py` proves this for every listed address in four shapes.

| File | What it is |
|---|---|
| `idea.txt` | The case: an invented internal note proposing one idea with known strong evidence against it. |
| `answer-key-holdout-v3.json` | The key, in the tier-2 shape (traps, known sources against by URL, rules, pass rule). |
| `check.py` | Loads the key in `score_rnd.py`, fetches each known source's evidence live, shows every listed address scores K1, and shows a good answer passes and broken answers fail. |

## How to score a run

    python3 evals/rnd/score_rnd.py <output.md> --key evals/rnd/holdout-v3/answer-key-holdout-v3.json --artefact <file> [--text-dir <dir>]

## How to run the check

Fetches live, about one minute:

    python3 evals/rnd/holdout-v3/check.py [--text-dir <dir>]

It prints one line that starts `check passed:`.

## Known sources: fetched and checked

The key lists five known sources at 152 addresses in total. All live checks ran on 8 November 2026 between 11:25 and 11:35 AEST. Each evidence URL passed `check_urls.py`: HTTP 200, no soft 404, and the page holds the quote recorded in the key. `check.py` ran green at 11:34 AEST, and the `score_rnd.py` and `check_urls.py` self-checks passed at the same time. The evidence page text is saved, named by the sha1 of the URL, in `/tmp/rndv3`, outside the repo, so it is not kept.

**Pages that refuse a script.** The main publisher page of all five sources refuses a script (HTTP 403, or 412 for some Cochrane Library paths). That covers JAMA Network (three sources, every path form), Wiley Online Library and the Cochrane Library full text, Europe PMC article pages, and cdc.gov and CDC Stacks. Each evidence URL is therefore an open copy that a script can fetch: PMC, two university research portals and the CDC archive. A run that cites a page that refuses a script needs the page text captured in Chrome and passed with `--text-dir`. A sample of the refusing pages was opened in Chrome or by a web fetch tool, to confirm that each is the right article. PubMed returns HTTP 203 to a script, so a PubMed citation fails R1 unless its text is captured.

**Prefix ceiling.** A few prefixes end in a short number (some CDC Stacks record numbers and JAMA Network article numbers). A longer number with the same start would also match. No such address is likely to be cited for this topic.

**Fabricated statistic search record.** On 8 November 2026, between about 11:26 and 11:33 AEST, four WebSearch queries looked for the study and the figure in the note: the named council by name (two queries, one with the study size and year), a different invented institute name, and the figure with the topic in plain words. No query found the study, the council or the figure.
