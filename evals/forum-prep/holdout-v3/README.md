Prompt-tuning tickets must not open this folder.

# Forum holdout case, v3

**Version:** holdout v3, 8 November 2026. Written by a separate holdout writer that read no prompt, no round
output, no holdout run, and no earlier holdout file other than `holdout-v2/README.md`.
**Purpose:** a fresh sealed pack for the forum skill, so a prompt can claim a holdout pass on a case its author
never saw. Same shape as v2 (30 pages, one image-only page with no text layer, printed page numbers offset from
physical ones) and the same six trap types in new forms. New organisation, sector (a public passenger ferry
operator buying battery electric ferries), attendees and figures. Every person, organisation and figure is
invented and labelled sample; addresses use reserved domains only.

| File | What it is |
|---|---|
| `build.py` | Builds `pack.pdf` and checks it (`--check`: page count, image-only page, no hyphen in a key quote, every key quote on exactly its listed pages, attendee pages equal the pages that print the attendee's name or full role, salted quotes do not hold, printed numbers). |
| `pack.pdf` | The pack. Printed "Page 1" is physical page 3, so printed = physical minus 2. |
| `invitation.txt` | The invitation, attendee list and previous-pack extract, pasted as text. Names the pack file `harbourline-fac-pack-2026-12-03.pdf`. |
| `answer-key-holdout-v3.json` | The key, in the tier-2 shape (items, attendees with `pages`, fact-check salts). |
| `check.py` | Loads the key in `score_forum.py`; a good brief passes, one broken brief per trap fails, an attendee cited off every listed page fails, salt adds 2 rows. |

## How to score a run

Attach `pack.pdf` to the run under the file name the invitation gives (`harbourline-fac-pack-2026-12-03.pdf`),
and paste `invitation.txt` as the message. Then score from the repo root:

    python3 evals/forum-prep/holdout-v3/build.py --check
    python3 evals/forum-prep/holdout-v3/check.py
    python3 evals/forum-prep/score_forum.py brief <output.md> --key evals/forum-prep/holdout-v3/answer-key-holdout-v3.json
    python3 evals/forum-prep/score_forum.py salt <output.md> --key evals/forum-prep/holdout-v3/answer-key-holdout-v3.json
    python3 evals/forum-prep/score_forum.py check <fact-check.md> <brief-under-test.md> --key evals/forum-prep/holdout-v3/answer-key-holdout-v3.json

The pass rule is in the key (`pass_rule`): three fresh-chat runs, all three must pass.

## Fairness rules (new for v3)

i) **Q1 has exactly one undelivered step.** The policy extract (physical page 23) lists four things the
   committee must see before it approves a vessel purchase. Three are met by papers in the pack: (a) the
   approved business case, page 24 (resolution 2026/31); (b) the probity adviser's report, page 15; (c) the
   outcome of crew consultation, page 16. Only (d), the independent marine survey, is in no paper. The previous
   minute's condition (page 25, written confirmation of the charging connection dates) is met by the letter on
   page 19. The action log (page 26) holds three actions, each closed and met: action 31 by paper 5 (pages 12
   to 15), action 32 by paper 6 (page 16), action 33 by paper 8 (page 19).
ii) **Every attendee's `pages` lists every page that states or shows the attendee's view.** Each attendee's
   name or full role is printed only on the pages that state the view, and `build.py --check` proves the set
   of pages naming each attendee equals the key's `pages`. Paper 1 (pages 3 and 4) is prepared by the
   programme office with the operations general manager as sponsor; the sponsor's view is on both pages and
   both are listed. Pages 5 and 6 (paper 2) carry background figures and no recommendation. The finance and
   customer papers are one page each; their attachments are prepared by other teams and state no view.
iii) **No key quote holds a hyphen or a word split across a line end, and each key quote is on exactly its
   listed pages.** `build.py --check` proves this from the built PDF text (pdftotext, the same extraction
   `score_forum.py` uses).
