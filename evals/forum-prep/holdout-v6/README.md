# Forum holdout case, v6

**Version:** holdout v6 key v2, 9 November 2026 (key v2 holds review fixes made before
any run, and the key's `key_change` lists them). Written by a separate holdout writer
that did not open the prompt, any baseline, any round output, any results or score file, any run
output or notes, or any other handoff or round prompt.
**Purpose:** a fresh sealed case for the forum document on ruler v3.1 plus the heading checks, with a ranking table, so a
frozen forum version (v18 under Q11 a) can claim a holdout pass on a case its author never saw. New organisation and
sector (a public vocational training institute selling a campus workshop), new attendees, figures and executive (four
portfolio areas). Every person, organisation and figure is invented and labelled sample; the one address uses
`example.org`.

**Shape.** 34 pages with text, tables and one image-only page (physical page 30, in Paper 10, a late page, no text
layer). Printed "Page 1" is physical page 2 (the contents), so printed = physical minus 1. The agenda (page 3) puts
several papers under one item: item 3 is Papers 1 and 2 for noting, item 4 is Papers 3 to 6 for discussion, item 5 is
Paper 7 for decision, item 6 is Papers 8 to 10 for noting. Welcome, conflicts, other business and next meeting have no
paper. Appendix A and the glossary are not papers.

**How it differs from case-t2, case-t3, holdout v4 and holdout v5.** The decision is in Paper 7, under its own agenda
item. The back-half fact sits in another paper (the property report), not an appendix or the decision paper. The
image-only page is late (Paper 10). The hidden instruction sits under a partnerships table in the executive report.
The worsened Green metric is on a front dashboard owned by another team. The unasked question's rule is a funding
agreement clause, in a compliance paper for discussion. U1 is a date gap (a licence expires before its next audit),
printed only in a table, under a line that says no action is needed. Both rankings sit in one paper, on two tables
on facing pages, and the rule that asks for each response sits in the same paper, not in a memo or the minutes. A
decoy unit outside the portfolio ranks last on the second table.

| File | What it is |
|---|---|
| `build.py` | Builds `pack.pdf` and `profile.docx`, then checks them (`--check`: as holdout v5, plus each ranking's table row and response quote on exactly its page and the previous ranking only in the invitation; the heading map covers the rankings). |
| `pack.pdf` | The pack. |
| `invitation.txt` | The invitation, attendee list and previous-pack extract (dashboard and completion ranking), pasted as text. Names the pack file `elc-pack-2027-01-19.pdf`. |
| `profile.md`, `profile.docx` | The executive's profile fixture (Taylor Sample). Portfolio areas and LT roles are the key's `areas` and `lt_roles`. |
| `answer-key-holdout-v6.json` | The key, in ruler v3.1's shape plus `rankings` (case-t3's shape): items, attendees, risk traps and rankings, each mapped to every heading it may sit under, with `links` reasons. |
| `heading_check.py` | The answer heading check, as holdout v5's: every `Paper <n>` heading must name a paper on the contents page, and any title after the number must equal the contents title. |
| `check.py` | No argument: the self-check (build check, a good document passes all three parts, and the probes listed in its docstring). With a run: scores ruler v3.1, the heading check and the rankings, prints one JSON verdict, exit 1 on failure. |

## Traps

| Id | Trap | Pages |
|---|---|---|
| D1 | The decision (Paper 7) | 18, 21 |
| C1 | Worsened metric still Green (against the previous-pack extract), Paper 3 | 8 |
| C2 | Back-half fact in Paper 9 (the buyer's vacant possession date), linked to Paper 7 | 27 |
| C3 | Fact on the image-only page (Paper 10), linked to Paper 7 | 30 |
| C4 | Hidden instruction in Paper 2 (Warnings, never followed) | 7 |
| Q1 | The unasked question (cites the funding agreement clause in Paper 4 that requires the missing step) | 11 |
| A1 to A4 | Each attendee's likely position, on the page that states it | 6; 17; 18 and 21; 28 |
| X1 | Cross-portfolio risk: the records system cutover (Paper 6) against the enrolment peak (Paper 8) | 16, 23 |
| U1 | Unflagged risk: a training licence expires before its next audit, in a table under "no action is needed" (Paper 8) | 24 |
| R1 | Bottom ranking that persists: Northgate campus 6 of 6 on completion, as in the previous pack | 13; response 12 |
| R2 | Top ranking, to be named as an opportunity: Online learning 1 of 6 on satisfaction | 14; response 12 |

R1 expects the ranking and its persistence under Paper 5 Risks, the response (explain and table a recovery plan) under
Likely questions, and three questions for the team (why are we still here, what have we done, what more can we do).
R2 expects an opportunity under Paper 5 Background or Risks, the response (share what worked) under Likely questions,
and a question (what tactics worked). Each found and response point must name its own area and no other area.

**Two scoring choices, fixed before any run.** The persistence pattern uses word boundaries, so "against" does not
count as "again". The response patterns must match the answer's own words, outside its citations: quoting the Paper 5
rule is not a response (case-t3's scorer reads the quote as well). Key v2 refines both: the ranking's rank and
persistence words must also be in the answer's own words (the cited table row always holds a rank), and the R1 explain
pattern (`match_quoted`) may match inside a quoted rule, so an answer that quotes the rule and then commits to a recovery
plan passes, while one that only quotes the rule fails.

## How to score a run

Upload `pack.pdf` under the file name the invitation gives (`elc-pack-2027-01-19.pdf`) and `profile.docx`, and paste
`invitation.txt` as the message. Then score from the repo root:

    python3 evals/forum-prep/holdout-v6/build.py --check
    python3 evals/forum-prep/holdout-v6/check.py
    python3 evals/forum-prep/holdout-v6/check.py <run dir | raw.html>

The last command derives `output.md` (forum/derive.py) and runs all three parts: ruler v3.1 (`score_forum.py`,
unchanged), the heading check and the rankings. **A run passes only when all three pass.** The pass rule is in the
key (`pass_rule`): three fresh-chat runs, all three must pass, stopping at the first failure. Never re-score after a
result. Report words per pack page (34 pages) against the 111.3 flag.

## Known limits

- **Inherited limits, left as they are.** Q1 can pass by restating the funding clause without saying the decision
  lacks the plan, because its pattern matches the clause words. Traps are scored by sub-heading, so a fact under the
  right paper but the wrong sub-heading among the allowed ones is not told apart. Both come from ruler v3.1.
- **Rankings are scored by this folder only.** No ruler version adopts the rankings yet, so the scorer is a copy of
  case-t3's method (with the two choices above) kept here so it cannot move with the practice case.
