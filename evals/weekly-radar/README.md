# Weekly radar eval

**This eval checks the two sections of a Weekly radar answer: that the week ahead finds the planted items in a test mailbox, and that each industry or AI item quotes a real, dated page from the last seven days.** The executives, organisations and mailbox are invented. The news items in the past-week keys are real public pages.

## What it checks

Section 1, the week ahead (`score_week.py`, case `case-week/`):

- Every line's citation (a bracket, or a table row's other cells) matches a real event, task or email in `week.json`.
- No line claims the executive accepted, declined or sent anything.
- All four parts are there (priorities, prepare, decline or delegate, overdue), each with content or "Nothing this week."
- Which of the 11 planted items were found, and where. A clash between two meetings counts only in the decline or delegate part.

Section 2, the radar (`score_industry.py`, newest key `answer-key-t2-past-v11.7.json`, cards layout):

- **F1:** one card per item, with a title and its labelled lines, Type is industry or AI, and every item has a date. A type with no item has the line "Nothing material this week: <type>". A table, a missing or repeated label, or a card with no title is malformed.
- **R1 (critical):** every source page opens (no soft 404) and holds the quote, and the quote is short.
- **T1 (critical):** no stale story: the page's own publication date (not an event date, not a rolling "updated" footer) falls inside the seven-day window.
- **T2 (critical):** a press release echoed by several outlets is counted once.
- **T3 (critical):** no padding toward the cap.
- **S1:** "Why it matters" and the quote are each one sentence.
- **K1:** every must-find story for the week is reported.
- **C1:** at most five industry and three AI items.
- **PA1:** an item on a must-find story names one of that story's expected portfolio areas from the profile.
- **A2:** the Action is "None", or names who acts: a leadership team role from the profile, or "You".
- **Counter-metrics:** items per type (catches padding) and must-find stories found per type.
- A page that refuses the script and has no saved text is "awaiting route", neither pass nor fail.

## How to run it on a Copilot answer

Needs Python 3.12 or later, git, and internet access for the live quote and date checks. Standard library only.

**Week ahead.** Load `case-week/week.json` into a test mailbox (see `case-week/README.md`), run the prompt, copy the answer into `answer.md`, then from the repo root:

    python3 evals/weekly-radar/score_week.py answer.md evals/weekly-radar/case-week/week.json evals/weekly-radar/case-week/week-key.json

It scores Section 1 only. The answer must have an "Industry radar" heading to split at, or the exit code is 1.

**Radar on a past week.** Run the prompt with `case-t2/profile.docx` and the case file `case-t2/past-1.txt` (week P1) or `case-t2/past-2.txt` (week P2), then:

    python3 evals/weekly-radar/score_industry.py answer.md --key evals/weekly-radar/answer-key-t2-past-v11.7.json --week P1

Use `--week P2` for `past-2.txt`. `--text-dir <dir>` gives saved page text for pages that block a script. Exit 0 prints a score JSON with `"pass"`. Exit 2 means the answer is malformed.

The scorer loads a week's addendum and the profile fixture only if git tracks them with no edit since their last commit. This stops a key being changed after a run. Run it inside a git clone of this repo, and do not edit those files.

Self-checks: `python3 evals/weekly-radar/score_week.py --self-check` (19 probes) and `python3 evals/weekly-radar/score_industry.py --self-check` (rulers tier 1 to v11.7). In this public copy the saved past answers are not included, so the probes that replay them are skipped and only the built-in probes run.

## Folders

- `case/`, `case-t2/`: practice cases. `case-t2/` holds the profile and past weeks P1 and P2. `case-demo/` is week P1 with invented names, as the guide shows.
- `case-week/`: the practice week for Section 1. `fixtures-week/`: small hand-written answers for the self-check.
- The older `answer-key-t2-past*.json` files are earlier ruler versions, kept so earlier scores can be reproduced.

No radar holdout is published. None has been spent, so all stay sealed.

## Results

- **Radar, past weeks:** no version is proven yet. Ten restarts across prompt v6 to v10 and rulers v10 to v11.6 found real misses (missed AI stories in v6 and v7) and several faults in our own ruler: a US month-first date that crashed the scorer, a footer date that overrode a dated section, a date with spaces around the slashes, and a joined header line that made a good table unreadable. Each ruler fault was fixed in a new ruler version, and the prompt was not blamed for it.
- The latest restart (v10 on ruler v11.6) passed its first two practice runs. The third stalled because a cited government PDF refused our network, which is "awaiting route", not a fail.
- **Week ahead, prompt v13:** one run on the practice week found 8 of 11 planted items by hand check, and the scorer said 7 of 11. It missed both overdue tasks. Its two industry cards passed the hand check.

So the radar is a pilot. Most failures so far came from our own ruler, and the ruler is still moving.
