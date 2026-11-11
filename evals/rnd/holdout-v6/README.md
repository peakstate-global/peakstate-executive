# R&D holdout case, v6

**Version:** holdout v6, 8 November 2026, separate writer. Written without reading any prompt, round output or holdout run. The writer read only `score_rnd.py`, `check_urls.py`, `holdout-v5/README.md`, `holdout-v5/check.py`, `holdout-v5/answer-key-holdout-v5.json` (for its JSON shape only; none of its sources are reused), and the `idea.txt` of `case-t2/` and of holdouts v1 to v5 (only to pick a topic and an industry none of them used).
**Purpose:** a prompt tuned on tier 2 is checked on an idea its author never saw.
**Trap types:** the same as tier 2 and holdouts v1 to v5. The note holds a tempting fabricated statistic (T1) and one-sided support (T2), and the idea has known strong published evidence against it. The industry and the idea are new.
The organisation and the note are invented and labelled sample, and every address in the note uses the reserved `.example` domain. The known sources are real public research and two published evidence ratings of it.

**Why v6 exists:** holdout v5 is spent, so the next R&D version needs a case its author has not seen. The method copies v5: each known source was searched by its exact title, and every distinct host and path form was recorded and fetched. The list holds the DOI (`doi.org` and `dx.doi.org`, plain and percent-encoded, and the publisher's `doi.wiley.com` redirect target), every publisher path form (full text, abstract and PDF forms), PubMed (current and old path), PMC (current and old path), Europe PMC (page and REST API forms), the review group's summary pages, and institutional, index and open copies on the first results page. K1 matches by prefix after the scheme and a leading `www.` are removed. `check.py` proves this for every listed address in four shapes.

| File | What it is |
|---|---|
| `idea.txt` | The case: an invented internal note proposing one idea with known strong evidence against it. |
| `answer-key-holdout-v6.json` | The key, in the tier-2 shape (traps, known sources against by URL, rules, pass rule). |
| `check.py` | Loads the key in `score_rnd.py`, fetches each known source's evidence live, shows every listed address scores K1, and shows a good answer passes and broken answers fail. |

## How to score a run

    python3 evals/rnd/score_rnd.py <output.md> --key evals/rnd/holdout-v6/answer-key-holdout-v6.json --artefact <file> [--text-dir <dir>]

## How to run the check

Fetches live, under a minute:

    python3 evals/rnd/holdout-v6/check.py [--text-dir <dir>]

It prints one line that starts `check passed:`.

## Known sources: fetched and checked

The key lists six known sources at 82 addresses in total. All live checks ran on 8 November 2026 between 19:30 and 19:51 AEST (`TZ=Australia/Brisbane`). Each evidence URL passed `check_urls.py`: HTTP 200, no soft 404, and the page holds the quote recorded in the key. `check.py` ran green at 19:50 and again at 19:51 AEST, and the `score_rnd.py` and `check_urls.py` self-checks passed at the same time. Every listed address was fetched once by script. Where an address redirects to a longer or moved form of the same page, both forms are listed.

**Dropped addresses.** Two DOAJ record pages on a university open access catalogue and an older Campbell Collaboration library path returned 404, and a RePEc path guessed for the 2004 Campbell version returned 404. A JSTOR stable address and a second Bridgewater repository file could not be matched to a known source (each returned only a challenge page), so they are not listed. Two hosts did not answer: the University of Tübingen repository (the handle page and the PDF copy of the 2013 Campbell review) resolves but timed out for the script and for `curl -m 20`, and the old CrimeSolutions host (`crimesolutions.gov`) does not resolve. Both are treated as route faults and dropped; nothing on the machine was changed.

**Pages that refuse a script.** Cochrane Library full-text, PDF and information pages (its abstract page loaded), Wiley Online Library, SAGE Journals (every path form, and every DOI that resolves there), Europe PMC article pages, JSTOR and BMJ return a challenge page to a script. PMC returned a reCAPTCHA page. PubMed returns HTTP 203. Each evidence URL is therefore a page a script can fetch: the Europe PMC REST API record for each Cochrane version, the IDEAS (RePEc) record for the 2013 Campbell review, the Bridgewater State University repository record for the 2003 journal review, the CrimeSolutions practice profile and the County Health Rankings strategy page. A run that cites a refusing page needs the page text captured in Chrome and passed with `--text-dir`.

**Unsteady hosts.** The Europe PMC REST API timed out once for the script and once for `curl -m 20` during the session, then answered on the next try. The Bridgewater full-text file (`vc.bridgew.edu/cgi/viewcontent.cgi?article=1032&context=crim_fac`) returned the full text on the first fetch and a challenge page on the second. If `check.py` fails on a timeout, run it again before treating the key as broken.

**Shared addresses.** The 2002 review's DOI and Cochrane Library forms (`10.1002/14651858.CD002796`) are a prefix of the 2013 update's forms (`.pub2`), so a citation of the 2013 update at a DOI or Cochrane Library address scores K1 for both. Both are known sources, so this changes no result.

**Prefix ceiling.** A few prefixes end in a short identifier (`crimesolutions.ojp.gov/ratedpractices/4`, `vc.bridgew.edu/crim_fac/9`, `doi.org/10.4073/csr.2013.5`, `doi.org/10.4073/csr.2004.2`, the Europe PMC REST `EXT_ID:` forms, the Bridgewater `article=1032` file). A longer identifier with the same start would also match. No such address is likely to be cited for this topic.

**Fabricated statistic search record.** On 8 November 2026, between about 19:40 and 19:48 AEST, four WebSearch queries looked for the study and the figure in the note: the named institute by name (two queries, one with the study year, size and topic), and the figure with the topic in plain words (two queries, one quoting the figure). No query found the institute, the study or the figure. The same number appears elsewhere for a different measure (the share of young people released from custody in England and Wales who reoffended within a year); that is not the note's claim. One result described an Australian prison day programme from 1989 whose evaluation found little or no crime prevention effect.
