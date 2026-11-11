Prompt-tuning tickets must not open this folder.

# R&D holdout case, v7 (Researcher, checker v4)

**Version:** holdout v7, 8 November 2026, ticket 27, separate writer. Written without opening `rnd/prompts/`, any `rnd/rounds*/` folder, `results-t2.md`, any `PREREG.md` of a round, or any holdout run (`runs/`). The writer read `score_rnd.py`, `check_urls.py`, `answer-key-t2-researcher-v2.json` and `holdout-v6/` (README, key and `check.py`) for their shape only, `holdouts.md`, the ticket 26 handoff, and the `idea.txt` of `case-t2/` and of holdouts v1 to v6 (only to pick a topic and an industry none of them used). None of their sources are reused.
**Purpose:** an R&D version tuned on tier 2 for Researcher is checked on an idea its author never saw (SPEC-redesign section 5, "Holdout v7").
**Trap types:** the same as tier 2 and holdouts v1 to v6. The note holds a tempting fabricated statistic (T1) and one-sided support (T2), and the idea has known strong published evidence against it. The industry (general insurance contact centres) and the idea (blue-light filtering glasses for every consultant) are new. The key adds the checker v4 fields: the Integration and Pitch sections, the contested-claim list for I1, the stop-rule pattern for M1, and R1 as critical.
The organisation, the people, the note and the profile are invented and labelled sample, and every address in the note uses the reserved `.example` domain. The known sources are real public research and real public advice from a professional body.

| File | What it is |
|---|---|
| `idea.txt` | The case: an invented internal note proposing one idea with known strong evidence against it. |
| `profile.md`, `profile.docx` | The profile fixture, hand-written by this writer from the case; `profile.docx` built with `pandoc`. Attach it to each run as the profile. It shapes the pitch and is not scored. |
| `answer-key-holdout-v7.json` | The key, checker v4 shape: traps, known sources against by URL, contested claims C1 and C2, rules, pass rule. |
| `check.py` | Loads the key in `score_rnd.py`, fetches each known source's evidence live, shows every listed address scores K1 in four shapes, and shows a good answer passes and eleven broken answers fail (T1, missing section, L1, K1, I1 wrong form, I1 no contested claim named, three I1 pairs of bare topic bullets with no glasses word, M1 no stop rule, A1 short pitch). |

## Contested claims (I1)

- **C1:** blue-light filtering glasses reduce eye strain for consultants who work all day on screens. The pilot feedback and some small trials favour the glasses; the 2023 Cochrane review and the professional body's advice do not.
- **C2:** the glasses help consultants sleep better after evening and night shifts, so sick days fall. The Cochrane review found three of six trials with better sleep scores and three with no difference, at very low certainty.

**I1 patterns tightened after review, before any run (8 November 2026).** Each claim's pattern needs two words in the bullet together with any table rows it names: a glasses word (glasses, lenses, spectacles, eyewear, filter, blue light) and an effect word (eye strain, visual fatigue, tired eyes, asthenopia or digital eye for C1; sleep, melatonin, circadian or insomnia for C2). The first patterns took a bare topic word, so a bullet such as "Shared assumption: night shifts are hard on sleep." covered a claim; `check.py` now shows three such pairs fail I1.

The 47% figure is trap T1 (fabricated), not a contested claim. Cost is not contested by evidence.

## How to score a run

    python3 evals/rnd/score_rnd.py <output.md> --key evals/rnd/holdout-v7/answer-key-holdout-v7.json [--text-dir <dir>]

## How to run the check

Fetches live, under a minute:

    python3 evals/rnd/holdout-v7/check.py [--text-dir <dir>]

It prints one line that starts `check passed:`.

## Known sources: fetched and checked

The key lists two known sources at 57 addresses (E1 at 53, E2 at 4). All live checks ran on 8 November 2026 between about 22:15 and 22:35 AEST (`check.py` green at 22:34 AEST) (`TZ=Australia/Brisbane`). Each evidence URL passed `check_urls.py`: HTTP 200, no soft 404, and the page holds the quote recorded in the key. Every listed address was fetched once by script, except two that follow a pattern already fetched (`dx.doi.org` with a percent-encoded slash, and the Wiley `epdf` path). The probe scripts stayed in `/tmp/rndv7`, outside the repo, so they are not kept.

**E1, the Cochrane review (CD013244.pub2).** Searched by its exact title. The list holds: the Cochrane plain language summary at its current path in English and 16 other languages, and its old `CD013244/EYES_...` path in English and the 11 languages that still serve it (each of these redirects to the current page, and both slugs Cochrane has used for the current path start with the listed `CD013244_` prefix); the Cochrane Library record (the unversioned prefix covers `.pub2` and its full, abstract, PDF, media and information paths); the Cochrane Clinical Answer drawn from the review; the DOI (`doi.org` and `dx.doi.org`, plain and percent-encoded, and the `doi.wiley.com` redirect target); Wiley Online Library (plain, full, abstract, PDF and ePDF forms); PubMed (current and old path); PMC (current and old path); Europe PMC (article, abstract and PMC page forms, and the REST API search by PubMed id and by DOI); the City, University of London open access copy; and the Evidence-Based Nursing structured summary of the review.

**E2, the American Academy of Ophthalmology advice.** Two English pages that each say the Academy does not recommend special eyewear for computer use, and their two Spanish versions, which say the same. Two linked Academy pages on blue light (a smartphone news item and a night-mode page) do not hold that advice, so they are not listed.

**Dropped addresses.** The AMiner index page serves only a script shell with no text, and the Europe PMC full-text XML endpoint for the PMC id returned no response; neither is listed. The old `CD013244/EYES_...` path returned 404 in Indonesian, Japanese, Korean, Dutch and Polish, so those five are not listed (the current paths in those languages are). The unversioned DOI resolves to the 2019 protocol, which reports no results, so it is not listed.

**Pages that refuse a script.** The Cochrane Library record and full-text pages, the Cochrane Clinical Answer, Wiley Online Library and every DOI form (they resolve to Wiley), Europe PMC article pages and Evidence-Based Nursing return a challenge page to a script. PMC returns a reCAPTCHA page. PubMed returns HTTP 203. The Cochrane Library abstract page and abstract PDF did load. Each evidence URL is therefore a page a script can fetch: the English Cochrane plain language summary page for E1, and the Academy's English page for E2. A run that cites a refusing page needs the page text captured in Chrome and passed with `--text-dir`.

**Prefix ceiling.** A few prefixes end in a short identifier (`openaccess.city.ac.uk/id/eprint/31201`, `pubmed.ncbi.nlm.nih.gov/37593770`, the Europe PMC REST `EXT_ID:` form). A longer identifier with the same start would also match. No such address is likely to be cited for this topic.

**Fabricated statistic search record.** On 8 November 2026, at about 22:30 AEST, two WebSearch queries looked for the study and the figure in the note: the figure with the topic in plain words, and the named institute in quotes. No query found the institute, the study or the figure. The same number appears in a 2025 vendor survey for a different measure (the share of office workers who report regular eye strain or tired eyes); that is not the note's claim. A 2017 lab trial of 36 volunteers reported fewer eye symptoms with high-blocking lenses; that is real support for the case for, which is why C1 is contested.
