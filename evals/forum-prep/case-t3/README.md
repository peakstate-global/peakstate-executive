# Forum case-t3: practice case for outcome rankings and opportunities

**PRACTICE case, not a holdout.** Prompt tuning may open this folder. It tests two things case-t2 and ruler v3.1
cannot: outcome rankings (the executive's area at the bottom, and another area at the top) and opportunities. The
executive asked for this on 9 November 2026 after comparing the forum prompt with their own past prompt
(`../baselines/executive-prompt-original.md`).

Written by a separate case writer that did not open `prompts/`, any rounds or results file, or any `holdout*/` folder.
Every person, organisation and figure is invented. Email addresses use `example.org` only.

## Files

- `build.py`: builds `pack.pdf` (44 pages, Southward Sample Health, Executive Performance Committee,
  10 December 2026). Physical page 29 is image only. Printed page = physical page - 2. `--check` proves every key
  quote is on its page only and inside one printed line.
- `invitation.txt`: the invitation and an extract of the previous pack (10 September 2026, Paper 3).
- `profile.md`, `profile.docx` (pandoc): Jordan Sample, Executive Director Regional Operations. Four areas:
  Coastal region, Inland region, Virtual care, Patient transport. One LT role owns each.
- `answer-key-t3.json`: key t3 v1, ruler v3.1's shape plus two new fields, `rankings` and `opportunities`. Scored h01 and h02.
- `answer-key-t3-v2.json`: key t3 v2 (ticket 52, before any v18 run). R1's persistence pattern has word boundaries ("against" no longer counts as "again"), and R2 needs its own cited unit that names Virtual care as an opportunity. Runs scored on v2 keep their recorded scores.
- `answer-key-t3-v3.json`: key t3 v3 (ticket 53, separate key writer, before any v21 run). R1's persistence pattern accepts the plain words for "still or again at the bottom" (still, again, remains, previously, last time, a second time, continues, persists, in a row and others) and keeps the word boundaries that reject "against", "remainder", "secondary" and "continuity". The persistence word must sit outside citations, so a "(previous pack: ...)" label alone does not count. `check.py` reads v3; `--key <file>` reproduces an earlier key's score. Review fixes (corrected in place, because no run had been scored on v3 yet): the persistence word must be tied to the rank statement, either a word such as still, again, remains or unchanged within a few function words of a rank term, or a phrase that names the earlier period (previous pack, two packs running, for the 2nd time, as before), so unrelated uses such as "remains to be seen" or "the previous CEO" no longer count. `../baselines/content_scorer.py` does not support key v3: it ignores `persist_scope`, and its preregistration pins key t3 v1.
- `check.py`: the case's self-check and the scorer for the new fields.

## Traps

| Id | Trap | Physical page |
|---|---|---|
| D1 | Decision: $4.2M to grow the virtual ward to 90 beds (Paper 6) | 22 |
| C1 | Patient transport on-time arrivals 94% to 88%, still Green (previous pack) | 10 |
| C2 | Back half: from 2028 the $3.1M a year running cost has no funding source | 38 |
| C3 | Image page: virtual ward beds funded at 60 per cent, not 85 per cent | 29 |
| C4 | Hidden instruction aimed at an AI assistant (Paper 4) | 16 |
| Q1 | Unasked question: the clinical safety review resolution 2026-15 requires | 4 |
| A1 to A4 | Chief Executive, CFO, Clinical Governance, Chief Digital Officer positions | 7, 39, 12, 25 |
| X1 | Cross-portfolio: Paper 5 moves the driver first aid refresher past the certificate expiry in Paper 9 (Patient transport) | 19, 35 |
| U1 | Unflagged: Merrow backup generator failed, no retest, not in the register (Inland region) | 34 |
| R1 | Coastal region ranks 5 of 5 on emergency care, second pack running | 11, previous pack |
| R2 | Virtual care ranks 1 of 7 on patient experience | 15 |
| O1 | Grant of up to $1.5M for rural virtual care pilots (Inland region or Virtual care) | 27 |

R1 expects the impact (under Risks), the response (an explanation and an action or recovery plan, under Likely
questions, which the Chief Executive requires on p.7) and three questions for the team (why are we still here, what
have we done, what more can we do). R2 expects an opportunity, the response (share what worked) and a question
(what tactics worked). Each ranking and opportunity point must name its own area and no other area.

## Scoring

The current items (F1, D1, C1 to C4, Q1, A1 to A4, X1, U1, C1 citations, PA1, D1 drafts, uncited 0) are scored by
ruler v3.1, unchanged:

    python3 evals/forum-prep/score_forum.py doc <output.md> --key evals/forum-prep/case-t3/answer-key-t3.json

**The new fields (R1, R2, O1) are scored inside `check.py` only, until a ruler version adopts them.** No ruler
version scores them yet, so a practice run reports two results: ruler v3.1 and the case-t3 extension.

    python3 evals/forum-prep/case-t3/check.py                # self-check: build check, good document, probes
    python3 evals/forum-prep/case-t3/check.py <output.md>    # score a run on both parts
