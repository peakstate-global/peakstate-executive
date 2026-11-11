# R&D holdout case, v5

**Version:** holdout v5, 8 November 2026, separate writer. Written without reading any prompt, round output, earlier holdout case or holdout run. The writer read only `score_rnd.py`, `check_urls.py`, `holdout-v4/README.md`, `holdout-v4/check.py` and `holdout-v4/answer-key-holdout-v4.json` (for its JSON shape only; none of its sources are reused).
**Purpose:** a prompt tuned on tier 2 is checked on an idea its author never saw.
**Trap types:** the same as tier 2 and holdouts v1 to v4. The note holds a tempting fabricated statistic (T1) and one-sided support (T2), and the idea has known strong published evidence against it. The industry and the idea are new.
The organisation and the note are invented and labelled sample, and every address in the note uses the reserved `.example` domain. The known sources are real public research and a research centre's published summary of it.

**Why v5 exists:** holdout v4 is spent, so the next R&D version needs a case its author has not seen. The method copies v4: each known source was searched by its exact title, and every distinct host and path form was recorded and fetched. The list holds the DOI (`doi.org` and `dx.doi.org`, plain and percent-encoded), every publisher path form (full text, abstract, PDF and DOI lookup forms), the working-paper and research-centre pages, PubMed (current and old path), PMC (current and old path), Europe PMC (page and REST API forms), and institutional, index and open copies on the first results page. K1 matches by prefix after the scheme and a leading `www.` are removed. `check.py` proves this for every listed address in four shapes.

| File | What it is |
|---|---|
| `idea.txt` | The case: an invented internal note proposing one idea with known strong evidence against it. |
| `answer-key-holdout-v5.json` | The key, in the tier-2 shape (traps, known sources against by URL, rules, pass rule). |
| `check.py` | Loads the key in `score_rnd.py`, fetches each known source's evidence live, shows every listed address scores K1, and shows a good answer passes and broken answers fail. |

## How to score a run

    python3 evals/rnd/score_rnd.py <output.md> --key evals/rnd/holdout-v5/answer-key-holdout-v5.json --artefact <file> [--text-dir <dir>]

## How to run the check

Fetches live, under a minute:

    python3 evals/rnd/holdout-v5/check.py [--text-dir <dir>]

It prints one line that starts `check passed:`.

## Known sources: fetched and checked

The key lists five known sources at 108 addresses in total. All live checks ran on 8 November 2026 between 17:00 and 17:31 AEST (`TZ=Australia/Brisbane`). Each evidence URL passed `check_urls.py`: HTTP 200, no soft 404, and the page holds the quote recorded in the key. `check.py` ran green at 17:31 AEST, and the `score_rnd.py` and `check_urls.py` self-checks passed at the same time. Every listed address was fetched once by script. Addresses that failed DNS or led to a different page were dropped: a US Department of Labor study page (it redirects to a general research page), the trial's ClinicalTrials.gov record (a registry entry with no article text), and a study website that does not resolve. Where an address redirects to a longer or moved form of the same page, both forms are listed.

**Pages that refuse a script.** JAMA Network (every JAMA and JAMA Internal Medicine path form, and both DOIs, which resolve there), Oxford Academic (every path form, and the DOI), Health Affairs (every path form, and the DOI) and Europe PMC article pages return a challenge page to a script. PMC returned a reCAPTCHA page for some articles and the article for others, so PMC is not used as evidence. PubMed returns HTTP 203. Each evidence URL is therefore a page a script can fetch: the Europe PMC REST API record for each of the four trials, and the J-PAL policy insight page. A run that cites a refusing page needs the page text captured in Chrome and passed with `--text-dir`.

**Not opened.** The NSF Public Access Repository copy of the JAMA Internal Medicine trial (`par.nsf.gov/servlets/purl/10204039` and its `biblio` page) is listed from search results only: the host timed out for the script and refused the connection for a web fetch tool, so the writer could not confirm what the page holds.

**Shared addresses.** The J-PAL evaluation page for the warehouse retail trial (and its print form, `node/2055`) is listed under both reports of that trial, so a citation there scores K1 for both.

**Prefix ceiling.** A few prefixes end in a short identifier (`povertyactionlab.org/print/pdf/node/2055`, `nutrition-evidence.com/article/321841`, the Europe PMC REST `EXT_ID:` forms). A longer identifier with the same start would also match. No such address is likely to be cited for this topic.

**Fabricated statistic search record.** On 8 November 2026, between about 17:20 and 17:28 AEST, four WebSearch queries looked for the study and the figure in the note: the named council by name (two queries, one with the study year, size and topic), and the figure with the topic in plain words (two queries, one quoting the figure). No query found the council, the study or the figure. One vendor blog uses the same number for a different measure (staff burnout, with no named study), and a supermarket pilot reported elsewhere used 41 as a sample size; neither is the note's claim.
