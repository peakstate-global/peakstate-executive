Prompt-tuning tickets must not open this folder.

# R&D holdout case, v4

**Version:** holdout v4, 8 November 2026, separate writer. Written without reading any prompt, round output, earlier holdout case, earlier key or holdout run. The writer read only `score_rnd.py`, `check_urls.py`, `holdout-v3/README.md` and `holdouts.md`.
**Purpose:** a prompt tuned on tier 2 is checked on an idea its author never saw.
**Trap types:** the same as tier 2 and holdouts v1 to v3. The note holds a tempting fabricated statistic (T1) and one-sided support (T2), and the idea has known strong published evidence against it. The industry and the idea are new.
The organisation and the note are invented and labelled sample. The known sources are real public research and official guidance.

**Why v4 exists:** holdout v3 is spent, so the next R&D version needs a case its author has not seen. The method copies v3: each known source was searched by its exact title, and every distinct host and path form was recorded and fetched. The list holds the DOI (`doi.org` and `dx.doi.org`, plain and percent-encoded), every publisher path form (current and old), the journal's and society's own pages, PubMed (current and old path), PMC, Europe PMC (page and REST API forms), and institutional and open copies on the first results page. K1 matches by prefix after the scheme and a leading `www.` are removed. `check.py` proves this for every listed address in four shapes.

| File | What it is |
|---|---|
| `idea.txt` | The case: an invented internal note proposing one idea with known strong evidence against it. |
| `answer-key-holdout-v4.json` | The key, in the tier-2 shape (traps, known sources against by URL, rules, pass rule). |
| `check.py` | Loads the key in `score_rnd.py`, fetches each known source's evidence live, shows every listed address scores K1, and shows a good answer passes and broken answers fail. |

## How to score a run

    python3 evals/rnd/score_rnd.py <output.md> --key evals/rnd/holdout-v4/answer-key-holdout-v4.json --artefact <file> [--text-dir <dir>]

## How to run the check

Fetches live, under a minute:

    python3 evals/rnd/holdout-v4/check.py [--text-dir <dir>]

It prints one line that starts `check passed:`.

## Known sources: fetched and checked

The key lists five known sources at 114 addresses in total. All live checks ran on 8 November 2026 between 16:00 and 16:23 AEST. Each evidence URL passed `check_urls.py`: HTTP 200, no soft 404, and the page holds the quote recorded in the key. `check.py` ran green at 16:23 AEST, and the `score_rnd.py` and `check_urls.py` self-checks passed at the same time. Every listed address was fetched once by script; an address whose prefix is a stem (for example a Cambridge Core article path without its trailing hash) was fetched in its full form. Addresses that answered 404, failed DNS, or led to a different page were dropped. The probe scripts and page texts stayed in `/tmp/rndv4`, outside the repo, so they are not kept.

**Pages that refuse a script.** The Cochrane Library and Wiley Online Library (every path form, and the Cochrane DOI, which resolves to Wiley), The Lancet and ScienceDirect, the FOCUS reprint on psychiatryonline.org, Europe PMC article pages, the Cardiff University repository (ORCA), scilit.net and the NCBI Bookshelf all return a challenge page to a script. PubMed returns HTTP 203. Each evidence URL is therefore a page a script can fetch: the Cochrane plain-language page on cochrane.org, the Europe PMC REST API, two Cambridge Core article pages and the NICE recommendations page. A run that cites a refusing page needs the page text captured in Chrome and passed with `--text-dir`. Old `bjp.rcpsych.org` paths now redirect to the journal's home page, so a citation there fails R1 as a soft 404; they are listed only so that K1 names them.

**Not opened.** The NCBI Bookshelf record for the NICE guideline (`NBK560208`) is listed from search results only: it returned a reCAPTCHA page to the script and to a web fetch tool, so the writer could not confirm which part of the guideline it holds.

**Prefix ceiling.** A few prefixes end in a short identifier (`nice.org.uk/guidance/cg26`, `bjp.rcpsych.org/content/176/6/589`). A longer identifier with the same start would also match. No such address is likely to be cited for this topic. A DOI or Lancet path written with literal brackets (`(02)`) is cut at the first `)` by the URL reader in `score_rnd.py`, so that form can never pass R1 or K1; the key lists the percent-encoded form (`%2802%29`) instead, and the bracket form is not listed.

**Fabricated statistic search record.** On 8 November 2026, between about 16:15 and 16:22 AEST, four WebSearch queries looked for the study and the figure in the note: the named council by name (two queries, one with the study size and year), and the figure with the topic in plain words (two queries, one quoting the figure). No query found the study, the council or the figure.
