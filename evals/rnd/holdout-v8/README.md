Prompt-tuning tickets must not open this folder.

# R&D holdout case, v8 (Researcher, checker v4.2)

**Version:** holdout v8, 9 November 2026, ticket 34, separate writer. Written without opening `rnd/prompts/`, any `rnd/rounds*/` folder, any `results-*.md`, any `score*.json`, `output.md` or `notes.md` under `rnd/`, any `PREREG.md` of a round, any holdout run, or any other ticket's handoff. The writer read `score_rnd.py`, `check_urls.py`, `answer-key-t2-researcher-v2.json` (for the checker v4.2 fields), `holdout-v7/` (README, key, `check.py`, `idea.txt` and `profile.md`) for their shape only, `holdouts.md`, and the opening of the `idea.txt` of `case-t2/` and holdouts v1 to v6 (only to pick a topic and an industry none of them used). None of their sources are reused.
**Purpose:** Researcher prompt v3 (or a later version) is checked on an idea its author never saw (SPEC-redesign section 5; ticket 34).
**Trap types:** the same as tier 2 and holdouts v1 to v7. The paper holds a tempting fabricated statistic (T1) and one-sided support (T2), and the idea has known strong published evidence against it. The industry (cash-in-transit and cash processing) and the idea (polygraph screening of every cash crew member and vault processor) are new.

**How v8 differs in structure from case-t2 and holdout v7.** Both earlier cases ask whether an intervention changes a person (a learning format, a pair of glasses). This case asks whether a selection and screening test sorts people correctly, so the evidence against turns on accuracy at a low base rate, not on an effect size. The second contested claim (deterrence) can hold even if the first (accuracy) fails, and the key's patterns are built for that overlap (see I1 below). The case is a committee paper with numbered sections, not an email. One known source is a court judgment, not a research review or a professional body.

The organisation, the people, the paper and the profile are invented and labelled sample, and every address in the paper uses the reserved `.example` domain. The known sources are a real public scientific review and a real public court judgment; no person is named in this folder.

| File | What it is |
|---|---|
| `idea.txt` | The case: an invented committee paper proposing one idea with known strong evidence against it. |
| `profile.md`, `profile.docx` | The profile fixture, hand-written by this writer from the case; `profile.docx` built with `pandoc`. Attach it to each run as the profile. It shapes the pitch and is not scored. |
| `answer-key-holdout-v8.json` | The key, checker v4.2 shape: traps, known sources against by URL, contested claims C1 and C2, rules, pass rule, words flag. |
| `check.py` | Loads the key in `score_rnd.py`, fetches each known source's evidence live, shows every listed address scores K1 in four shapes, shows a good answer passes, and shows 14 probe answers fail (T1, missing section, L1, K1, I1 wrong form, I1 unrelated bullets, I1 one boilerplate bullet, three I1 pairs of bare topic bullets, M1 no stop rule, A1 short pitch). It also shows a padded passing answer is "passed, words flagged". |

## Contested claims (I1)

- **C1:** polygraph tests accurately pick out applicants and staff who steal. Specific-incident studies show discrimination well above chance, and the vendor claims 98%; the scientific review finds screening accuracy too low to rely on, and the court found no consensus on reliability.
- **C2:** screening deters theft and draws out admissions, so losses fall even if the test is imperfect. The review accepts that screening may help deterrence and admissions, but says this rests on a belief in accuracy, and the trial has no comparison centre.

**Patterns.** Each claim's pattern needs a polygraph word (polygraph, lie detector, lie detection) in the bullet together with any Case for row it names, plus an effect word: an accuracy word for C1 (accurate, valid, reliable, false positive, false negative, base rate, above chance, innocent, misclassified, wrongly, error rate), a deterrence word for C2 (deter, discourage, put off, self-select). Multi-word phrases accept a hyphen or a space, as checker v4.2 does.

**Why C1 excludes deterrence words.** The natural C2 bullet says deterrence works while staff believe the test is accurate, so it names accuracy too. The scorer counts a bullet that matches two claims as covering neither. C1's pattern therefore also requires that no deterrence word appears: a bullet with both kinds of word covers C2 only. The cost: a C1 bullet that uses a deterrence word covers C2, not C1. A second accepted cost: a C2 bullet that argues only admissions or losses, with no deterrence word (deter, discourage, put off, self-select), covers no claim. `check.py` shows both sides (the good C2 bullet covers C2 only; one boilerplate bullet with both kinds of word leaves C1 uncovered).

The 62% figure is trap T1 (fabricated), not a contested claim. The 98% vendor figure is one-sided support (T2). Cost and legality are not contested claims.

## How to score a run

    python3 evals/rnd/score_rnd.py <output.md> --key evals/rnd/holdout-v8/answer-key-holdout-v8.json [--text-dir <dir>]

## How to run the check

Fetches live, under a minute:

    python3 evals/rnd/holdout-v8/check.py [--text-dir <dir>]

It prints one line that starts `check passed:`.

## Known sources: fetched and checked

The key lists two known sources at 17 addresses (E1 at 12, E2 at 5). The live checks ran on 9 November 2026 between about 08:00 and 08:15 AEST (`TZ=Australia/Brisbane`). Each evidence URL passed `check_urls.py`: HTTP 200, no soft 404, and the page holds the quote recorded in the key. Every listed address was fetched once by script; the two percent-encoded DOI forms were followed with `curl`. The probe scripts stayed in `/tmp/rndv8`, outside the repo, so they are not kept.

**E1, the National Research Council review (2003), The Polygraph and Lie Detection, DOI 10.17226/10420.** The catalogue pages (`nap.edu` and `nap.nationalacademies.org`) and both DOI forms redirect to the publication page at `nationalacademies.org/publications/10420`, which describes the book but does not hold the quote. The online reader's executive summary (chapter 2) and the conclusions chapter hold it at all three hosts (each redirects to `nationalacademies.org/read/10420/`). The October 2002 news release (`polygraph-testing-too-flawed-for-security-screening`) holds only a paraphrase of the quote, so its addresses are dropped. The committee's public briefing statement (old and current path) is the same report's summary, read aloud, and is listed as the same source.

**E2, Supreme Court of the United States, 523 U.S. 303 (1998), docket 96-1133.** The Legal Information Institute opinion and syllabus pages (old `supct/html` path) and its current `supremecourt/text` page and the Court's bound volume 523 PDF all hold the quote. Justia refuses a script and is listed; a run that cites it needs the page text captured in Chrome and passed with `--text-dir`. The concurring and dissenting opinion pages are not listed: they are not the Court's finding, and the dissent argues the other way.

**Dropped addresses.** Both FindLaw addresses now return 403 or a script challenge, and the news release addresses hold only a paraphrase (see above). The National Academies download paths (`nap.edu/download/10420` and the `nap.nationalacademies.org` form) and a guessed report-brief PDF returned 404. The Library of Congress page for the judgment refused the script (403) and its PDF download was truncated, so neither is listed. The Oyez case page serves only a script template with no text.

**Pages that refuse a script.** Justia (challenge page); FindLaw (dropped). Every other listed address served text to the script.

**Prefix ceiling.** The E1 prefixes end in the short identifier `10420`, so an address such as `nap.edu/catalog/104201` would also match. No such address is likely to be cited for this topic.

**Fabricated statistic search record.** On 9 November 2026, at about 08:05 AEST, two WebSearch queries looked for the study and the figure in the paper: the named council in quotes with the topic, and the figure with the topic in plain words. Neither found the council, the study or the figure. A 1980s vendor claim of an 80% cut in employee theft exists, and one 1991 survey reports 62% of police agencies using polygraph screening; neither is the paper's claim. A field study at a convenience store chain found a written pre-employment inventory cut shrinkage more than a polygraph procedure; that is evidence against C2, not in the key.

Key amended before any run (review fixes), 2026-11-09 08:22:25 AEST, commit `77bbc555`.
