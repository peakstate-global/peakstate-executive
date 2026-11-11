# Forum prep eval

**This eval checks that a Forum prep answer finds the planted facts in an invented board pack and that every quote it cites is really on the page it names.** The packs, people and organisations are invented.

## What it checks

Document layout (ruler v3.1 and v3.2, keys `answer-key-t2-v2.json`, `case-t3/` and `holdout-v4/` to `holdout-v6/`):

- **F1 (critical):** the fixed headings appear in order, one "Paper n" heading per paper, and no text comes before the first heading.
- **Planted items:** each planted fact or risk appears under an allowed heading, with a citation that holds. Some sit on an image-only page, in the back half of the pack, or in a pasted invitation.
- **C1:** every quoted citation, such as `(p. 12: "...")`, `(previous pack: "...")` or `(invitation: "...")`, has its exact quoted words on that page or in that pasted text.
- **PA1:** each risk names its own expected portfolio area from the profile, and no other area.
- **D1:** each paper's draft email starts "Draft, not sent.", names a leadership team role from the profile, cites a pack page, and avoids banned phrases.
- **Counter-metrics:** words per pack page (flagged above about 1.5 times a passing answer) and uncited sentences in Background and Risks (must be zero). These catch an answer that passes by pasting the whole pack.
- **Heading check (holdout v5 on):** each item's paper heading matches the pack's own contents page.
- **Rankings (`case-t3/`, holdout v6):** the bottom-ranking response with its questions, and the top ranking named as an opportunity, each in its own cited bullet.

Table layout (tier 1, `answer-key.json` and `answer-key-t2.json`): the table is well formed, each key item is found in the right row type and cites an allowed page, the quote holds on that page, each attendee's position is found and cited, and no row lacks a page.

## How to run it on a Copilot answer

Needs Python 3.12 or later, Pillow (`pip install pillow`), and `pdftotext` and `pdfinfo` from poppler (`brew install poppler` on macOS). Rebuilding a pack (not needed to score) also needs Google Chrome and pandoc.

1. Run the Forum prep prompt in Copilot with the case's `pack.pdf`, `invitation.txt` and, where present, `profile.docx`.
2. Copy Copilot's answer into a Markdown file, for example `answer.md`. If you save the page as HTML instead, `python3 evals/forum-prep/derive.py <raw.html>` writes `output.md` beside it.
3. Score it from the repo root:

        python3 evals/forum-prep/score_forum.py doc answer.md --key evals/forum-prep/answer-key-t2-v2.json   # case-t2
        python3 evals/forum-prep/case-t3/check.py answer.md                                               # case-t3
        python3 evals/forum-prep/holdout-v6/check.py answer.md                                            # spent holdout v6
        python3 evals/forum-prep/score_forum.py brief answer.md                                           # tier 1 table, case/

The scorer prints one JSON object with `"pass"` and the detail (missed items, bad citations, word counts). Exit 0 means it scored (pass or fail is in the JSON). Exit 2 means the answer is malformed, for example a missing heading.

Self-checks: `python3 evals/forum-prep/score_forum.py --self-check`, `python3 evals/forum-prep/case-t3/check.py`, and for each holdout `python3 evals/forum-prep/<holdout>/build.py --check` then `python3 evals/forum-prep/<holdout>/check.py`.

## Folders

- `case/`, `case-t2/`, `case-t3/`: practice cases (15, 60 and 44 pages).
- `case-demo/`: the 48-page demo pack the guide shows. It has no key.
- `holdout/` to `holdout-v6/`: **spent holdouts.** Each was written by a separate writer who never saw the prompt, then used once on a frozen prompt version. They are spent, so a new prompt version cannot claim a pass on them.
- `fixtures/`: a passing and a failing answer for the ruler v3 self-check.

## Results

- **Table layout, prompt v11:** practice case 3 of 3, spent holdout v3 3 of 3. This is the only forum version that passed a sealed holdout.
- **Earlier table versions:** v7 failed holdout v1 (it missed the fact on the image-only page). v8 passed 1 of 3 on holdout v2. One failing run missed an attendee's view on a page our key did not list, which was a key fault.
- **Document layout, v12 to v16:** each failed practice (layout, draft citation form, or a quote cited to the wrong page).
- **v17:** practice 3 of 3. Holdout v4 failed on a key fault: the key mapped a risk to Paper 6, but the pack's contents page puts that page in Paper 5, where the answer filed it. Holdout v5 failed on a real miss: one quote joined a table header to a cell two rows down.
- **v18 to v21:** each failed its first practice run on real misses (wrong page, split response, missing items).
- **v22:** practice 6 of 6. Holdout v6 failed on a key fault: the key needed one risk cited to two pages in one bullet, which the prompt's own one-citation rule forbids.

So the sealed tests mostly failed on faults in our own keys and rulers, not on the content Copilot wrote. Treat a holdout result as evidence about the key as well as the prompt.
