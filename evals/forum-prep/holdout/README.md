Prompt-tuning tickets must not open this folder.

# Forum holdout case

**Version:** holdout v1, 7 November 2026 (ticket 09). Written without reading any prompt or round output.
**Purpose:** a prompt tuned on tier 2 is checked on a pack its author never saw. Same shape as tier 2
but smaller (30 pages, one image-only page, printed page numbers offset from physical ones), the same
trap types each in a new form, and a different organisation, sector and attendees. Every person,
organisation and figure is invented and labelled sample.

| File | What it is |
|---|---|
| `build.py` | Builds `pack.pdf` and checks it (`--check`: page count, image-only page, every key quote on exactly its page, printed numbers). |
| `pack.pdf` | The pack. |
| `invitation.txt` | The invitation, attendee list and previous-pack extract, pasted as text. |
| `answer-key-holdout.json` | The key, in the tier-2 shape (items, attendees, fact-check salts). |
| `check.py` | Loads the key in `score_forum.py`; a good brief passes and broken briefs fail. |

## How to score a run

    python3 evals/forum-prep/holdout/build.py --check
    python3 evals/forum-prep/score_forum.py brief <output.md> --key evals/forum-prep/holdout/answer-key-holdout.json
    python3 evals/forum-prep/score_forum.py salt <output.md> --key evals/forum-prep/holdout/answer-key-holdout.json
    python3 evals/forum-prep/score_forum.py check <fact-check.md> <brief-under-test.md> --key evals/forum-prep/holdout/answer-key-holdout.json
