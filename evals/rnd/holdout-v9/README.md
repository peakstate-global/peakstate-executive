Prompt-tuning tickets must not open this folder.

# R&D holdout case, v9 (Researcher, checker v4.3)

**Version:** holdout v9 key v2 (review fixes, before any run), 9 November 2026, ticket 42, separate writer. Key v1 was commit `aedf1a33`, never run; the key's `key_change` field says what v2 changed (the two contested-claim patterns only). Written without opening `rnd/prompts/`, any `rnd/rounds*/` folder, any `runs/` folder, any `results-*.md`, any `score*.json`, `output.md` or `notes.md` under `rnd/`, any round's `PREREG.md`, any other ticket's handoff, or any runner round prompt. The writer read `score_rnd.py`, `check_urls.py`, `answer-key-t2-researcher-v3.json` (for the checker v4.3 fields), `holdout-v8/` (README, key, `check.py`, `idea.txt` and `profile.md`) for their shape only, `holdouts.md`, the redesign spec section 5, ADR 0016, and the opening of the `idea.txt` of `case/`, `case-t2/` and holdouts v1 to v7 (only to pick a topic and an industry none of them used). None of their sources are reused.
**Purpose:** frozen Researcher prompt v3 is checked on an idea its author never saw, on checker v4.3 (the blocked-host route), as the owner's Q7 answer a) asks (state-of-play brief, round 4).
**Trap types:** the same as tier 2 and holdouts v1 to v8. The case holds a tempting fabricated statistic (T1) and one-sided support (T2), and the idea has known strong published evidence against it. The industry (specialty pet retail) and the idea (halving the dry food and treats range to fight choice overload) are new.

**How v9 differs in structure from case-t2, v7 and v8.** case-t2 and v7 ask whether an intervention changes a person (a learning format, a pair of glasses); v8 asks whether a screening test sorts people correctly. v9 asks about aggregate buyer behaviour in a market: whether a whole customer base buys more, and keeps coming back, after a retailer offers less. The case cites a real, famous study for the idea (the jam study), so the evidence against is a meta-analysis that finds the famous effect averages near zero, plus a field study of a real range cut. The two contested claims are about two different outcomes of one decision (purchase per visit, C1; visits per customer, C2), so one can hold while the other fails. The case is a business case in question-and-answer form, not an email or a committee paper.

The organisation, the people, the business case and the profile are invented and labelled sample, and every address in the case uses the reserved `.example` domain. The known sources are two real published academic papers; no person is named in this folder outside the papers' author lists in the key.

| File | What it is |
|---|---|
| `idea.txt` | The case: an invented business case proposing one idea with known strong evidence against it. |
| `profile.md`, `profile.docx` | The profile fixture, hand-written by this writer from the case; `profile.docx` built with `pandoc`. Attach it to each run as the profile. It shapes the pitch and is not scored. |
| `answer-key-holdout-v9.json` | The key, checker v4.3 shape: traps, known sources against by URL, contested claims C1 and C2, rules, pass rule, words flag, the blocked-host route field. |
| `check.py` | Loads the key in `score_rnd.py`, fetches each known source's evidence live, shows every listed address scores K1 in four shapes, shows a good answer passes, shows six good Integration bullets pass I1 (key v2), shows 18 probe answers fail (four of them generic bullets that key v1 passed), and shows two checker v4.3 route probes (a known source on a refusing host awaits the route; after the route it passes if the page served the quote and fails if it still refused). It also shows a padded passing answer is "passed, words flagged". |

## Contested claims (I1)

- **C1:** fewer lines on the shelf make shoppers buy more, because too much choice stops people buying. The jam study and later work on when overload occurs support it for some shoppers and shelves; the meta-analysis (E1) finds a mean effect of virtually zero with large variance and no sufficient conditions.
- **C2:** regular customers keep shopping as often after the cut. Shoppers buy from a small share of lines, so some cuts lose few sales; the online grocer study (E2) found the cut lowered shopping frequency and purchase quantity, and the lost visits cost the most.

**Patterns (key v2).** Each claim's pattern needs a range word (choice, choices, choice overload, too many, fewer choices, options, lines, products, brands or SKUs, range, assortment, SKU, jam, lines) in the bullet together with any Case for row it names, plus an outcome word: a buying word for C1 (buy, bought, purchase, sales, sell, convert, defer, satisfied, overwhelmed, paralysed), a retention word for C2 (frequency, how often, as often, visit except "per visit", retention, retain, switch, defect, churn, lapse, shop elsewhere, to or at a competitor or rival, come back, return except "return on", repeat trips, visits, customers, purchases or business, trips, keep shopping, stay with, shop less). Multi-word phrases accept a hyphen or a space, as checker v4.2 and v4.3 do. Key v1 also took the bare option, decide, decision, loyal, competitor and rival, so a generic bullet such as "Shared assumption: the range decision is the right one." covered a claim; key v2 drops those words, and `check.py` shows four such bullets now fail.

**Why C1 excludes retention words.** The natural C2 bullet says regulars keep visiting when the lines they buy stay, so it names buying too. The scorer counts a bullet that matches two claims as covering neither. C1's pattern therefore also requires that no C2 retention word appears: a bullet with both kinds of word covers C2 only. Because "per visit" and "loyal" are not retention words in key v2, a C1 bullet about buying per visit, or about loyal brand buyers, covers C1. The cost: a C1 bullet that uses a retention word covers C2, not C1. A second accepted cost: a C2 bullet that argues only basket size or sales, or says only "loyal", with no retention word, covers no claim. `check.py` shows both sides.

The 27% figure is trap T1 (fabricated), not a contested claim. The pilot's sales per line (which rise by arithmetic when lines are halved) and the consultancy's own case study are one-sided support (T2). Cost and own brand are not contested claims.

**Inherited loophole (checker v4.1).** A bullet that names "Claim <n>" is scored with the text of Case for row n added, so a generic bullet can cover a claim through the row it points at. This is checker-wide, inherited from checker v4.1, and left as is for v9.

## How to score a run

    python3 evals/rnd/score_rnd.py <output.md> --key evals/rnd/holdout-v9/answer-key-holdout-v9.json [--text-dir <dir>] [--route-dir <dir>]

If the score's verdict is "awaiting route", run `evals/rnd/blocked-host-route-wizard.sh` with that `score.json` and a route directory, then re-score with `--route-dir`. The score is final only once the wizard records that the VPN is back on.

## How to run the check

Fetches live, under a minute:

    python3 evals/rnd/holdout-v9/check.py [--text-dir <dir>]

It prints one line that starts `check passed:`.

## Known sources: fetched and checked

The key lists two known sources at 26 addresses (E1 at 14, E2 at 12). The live checks ran on 9 November 2026 between about 15:40 and 15:55 AEST (`TZ=Australia/Brisbane`), on this Mac with the VPN on (the normal route). Each evidence URL passed `check_urls.py`: HTTP 200, no soft 404, and the page holds the quote recorded in the key. Both evidence URLs are on hosts this Mac reaches without the VPN-off route.

**E1, Scheibehenne, Greifeneder and Todd (2010), Journal of Consumer Research, DOI 10.1086/651235.** Served with the quote to the script: the authors' PDF at `scheibehenne.com` (the evidence URL), the University of Geneva archive record, the EconPapers abstract (both paths) and the IDEAS abstract. Refused the script (challenge): both DOI forms (they redirect to Oxford Academic), the Oxford Academic article, abstract and lookup pages, JSTOR and the Mannheim repository record. Under checker v4.3 a run that cites one of these and has no Chrome text awaits the route.

**E2, Borle, Boatwright, Kadane, Nunes and Shmueli (2005), Marketing Science, DOI 10.1287/mksc.1050.0121.** Served with the quote to the script: the IDEAS abstract (the evidence URL) and the EconPapers abstract (both paths). Refused the script (challenge): the DOI forms and the INFORMS publisher pages. The author PDF on a University of Southern California host fails the script because its TLS certificate has expired (status None, so under checker v4.3 it awaits the route, and fails there too unless the certificate is renewed); it is listed because it is the same paper. **A run that cites only this address for E2 fails R1 unless Chrome text resolves it.**

**Needs the VPN-off route.** No address was found that fails only on this Mac's VPN exit and passes with the VPN off; this writer did not switch the VPN off. The refusing hosts above refuse any script, so a run that cites them needs Chrome text, then the route.

**Dropped addresses.** The University of Basel repository records (`edoc.unibas.ch`) refused the script and their content could not be confirmed; an Indiana University copy of E1 and of the authors' 2011 reply returned 404; a Semantic Scholar search page refused the script; a co-author's site page for E2 returned 404. None is listed.

**Prefix ceiling.** The Mannheim prefix ends in the short record number `30861`, so an address such as `.../308610` would also match. No such address is likely to be cited for this topic.

**Fabricated statistic search record.** On 9 November 2026, at about 15:50 AEST, two WebSearch queries looked for the study and the figure in the case: the named council in quotes with the topic, and the figure with the basket count in plain words. Neither found the council, the study or the figure. Real range-cut stories with rising sales exist (retailer and consultancy examples, a 1993 industry study that found no sales loss); none is the case's claim, and they are support for C1, not in the key.

## Exposure in the commit body

The body of commit `aedf1a33` names both contested claims and both known sources. History is not rewritten. For ticket 43 this is acceptable: frozen Researcher v3 (`fb6b88ed`) is not tuned, and Copilot never reads this repo. v9 is **not blind for any future tuned prompt**: a tuner can read `git log`, so a later tuned version needs a new holdout.
