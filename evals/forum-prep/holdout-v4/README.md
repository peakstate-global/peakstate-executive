# Forum holdout case, v4

**Version:** holdout v4, 8 November 2026, reworked after review and before any run (see Rework below). Written by a separate holdout writer that did not open
the prompt, any round output, or any earlier holdout's runs.
**Purpose:** a fresh sealed case for the forum document (ruler v3), so a forum v12 or later can claim a holdout pass on
a case its author never saw. New organisation and sector (a community housing provider awarding a modular build
contract), new attendees, figures and executive. Every person, organisation and figure is invented and labelled
sample; addresses use reserved domains only.

**Shape.** 32 pages with text, tables and one image-only page (physical page 16, Paper 6, the council letter, no text layer).
Printed "Page 1" is physical page 3, so printed = physical minus 2. The agenda (page 2) puts several papers under one
item, as the tier-2 pack does: item 3 is Paper 1 for decision, item 4 is Papers 2 to 6 and item 5 is Papers 7 to 10,
for noting. Welcome, conflicts, other business and the date of the next meeting have no paper.

| File | What it is |
|---|---|
| `build.py` | Builds `pack.pdf` and `profile.docx`, then checks them (`--check`: page count, image-only page, every key quote on exactly its listed pages and inside one printed line, no hyphen and at most 12 words in a key quote, attendee pages equal the pages that print the attendee's name or full role, printed numbers, profile areas and LT roles equal the key's, previous-pack value only in the invitation). |
| `pack.pdf` | The pack. |
| `invitation.txt` | The invitation, attendee list and previous-pack extract, pasted as text. Names the pack file `idc-pack-2026-12-10.pdf`. |
| `profile.md`, `profile.docx` | The executive's profile fixture (Riley Sample). Portfolio areas and LT roles are the key's `areas` and `lt_roles`. |
| `answer-key-holdout-v4.json` | The key, in ruler v3's shape (key t2 v2): items, attendees and risk traps, each mapped to every heading it may sit under; each risk trap mapped to its portfolio area or areas. |
| `check.py` | Loads the key in `score_forum.py` (ruler v3): a good document passes; each trap left out fails on that trap; each attendee cited off its pages fails; an A3 or A4 mention by paper title only fails; PA1, D1, F1 and the uncited counter-metric each fail on a broken document. |

## Traps

| Id | Trap | Pages |
|---|---|---|
| D1 | The decision | 3, 4 |
| C1 | Worsened metric still Green (against the previous-pack extract) | 5 |
| C2 | Back-half fact (exclusion in the tender report, Paper 9) | 24 |
| C3 | Fact on the image-only page (Paper 6) | 16 |
| C4 | Hidden instruction in Paper 7 (Warnings, never followed) | 18 |
| Q1 | The unasked question (cites the committee terms of reference page that requires the missing step) | 28 |
| A1 to A4 | Each attendee's likely position, on the page that states it | 25; 9; 3 and 4; 10 |
| X1 | Cross-portfolio risk: another paper creates a risk to the executive's portfolio | 8, 13 |
| U1 | Unflagged risk: an overdue compliance duty in the portfolio the pack states but never calls a risk | 14 |

## Rework

A review of the first version found two defects, fixed before any run touched the case. First, every
trap sat in the same paper slot and shape as the tier-2 case. The papers are now in a new order, C2, C3 and C4 sit in
other papers, Q1's required step is in the committee terms of reference (not in minutes), U1 is an overdue compliance
duty (not a condition-rated asset missing from a renewals list), and A2 and A4 take new positions. Second, the A3 and
A4 attendee match hit paper titles; each now requires the person's name or full role.

## How to score a run

Upload `pack.pdf` under the file name the invitation gives (`idc-pack-2026-12-10.pdf`) and `profile.docx`, and paste
`invitation.txt` as the message. Then score from the repo root:

    python3 evals/forum-prep/holdout-v4/build.py --check
    python3 evals/forum-prep/holdout-v4/check.py
    python3 evals/forum-prep/score_forum.py doc <run dir | raw.html> --key evals/forum-prep/holdout-v4/answer-key-holdout-v4.json

The pass rule is in the key (`pass_rule`): three fresh-chat runs, all three must pass.
