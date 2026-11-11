# Forum holdout case, v2

**Version:** holdout v2, 8 November 2026. Written without reading any prompt, round output or holdout run.
**Purpose:** holdout v1 is spent, so a forum prompt needs a fresh pack its author never
saw before it can claim a holdout pass. Same shape as v1 (30 pages, one image-only page, printed page numbers offset
from physical ones), the same trap types each in a new form, and a different organisation, sector and attendees. The
image-only page holds a different kind of content from v1's. Every person, organisation and figure is invented and
labelled sample; addresses use reserved domains only.

| File | What it is |
|---|---|
| `build.py` | Builds `pack.pdf` and checks it (`--check`: page count, image-only page, every key quote on exactly its page, no hyphen in a key quote, printed numbers). |
| `pack.pdf` | The pack. |
| `invitation.txt` | The invitation, attendee list and previous-pack extract, pasted as text. |
| `answer-key-holdout-v2.json` | The key, in the tier-2 and v1 shape (items, attendees, fact-check salts). |
| `check.py` | Loads the key in `score_forum.py`; a good brief passes and broken briefs fail. |

## How to score a run

Attach `pack.pdf` to the run under the file name the invitation gives, and paste `invitation.txt` as the message.
Then score from the repo root:

    python3 evals/forum-prep/holdout-v2/build.py --check
    python3 evals/forum-prep/holdout-v2/check.py
    python3 evals/forum-prep/score_forum.py brief <output.md> --key evals/forum-prep/holdout-v2/answer-key-holdout-v2.json
    python3 evals/forum-prep/score_forum.py salt <output.md> --key evals/forum-prep/holdout-v2/answer-key-holdout-v2.json
    python3 evals/forum-prep/score_forum.py check <fact-check.md> <brief-under-test.md> --key evals/forum-prep/holdout-v2/answer-key-holdout-v2.json

The pass rule is in the key (`pass_rule`): three fresh-chat runs, all three must pass.
