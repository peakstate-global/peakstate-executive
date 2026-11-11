# Practice week for the week-ahead part of Weekly radar

**Harbourview Freight Group, executive Alex Marlowe (invented). The run day is Wednesday 11 November 2026, and the week ahead is Monday 16 to Friday 20 November 2026.** Every person and organisation here is invented.

- `profile.md`, `profile.docx`: the executive's portfolio of five areas and leadership team by role.
- `week.json`: the test mailbox for the week, in `score_week.py`'s schema: 14 calendar events, 7 To Do tasks and 42 inbox emails (sender, day and time received in AEST). T01 and T02 are flagged emails with a past due date, so they sit in the mail list. Overdue means before 11 November.
- `week-key.json`: the 11 planted items. Each one lists the `week.json` ids that carry it, and citing any one of them finds it. Never put this file into a prompt.
- `checks/`: a hand-made compliant answer (scores 11 of 11), an empty answer (0 found), and `checks/probes/` (answers with known misses, listed in `expected.json`). `score_week.py --self-check` runs all of them.

To try it yourself, load the 14 events, 7 tasks and 42 emails from `week.json` into a test Microsoft 365 mailbox, run the Weekly radar prompt on 11 November (or shift the dates), paste Copilot's answer into a file, and score it:

    python3 evals/weekly-radar/score_week.py <answer.md> evals/weekly-radar/case-week/week.json evals/weekly-radar/case-week/week-key.json

## Limits

- To Do on the web refuses a past due date, so the two overdue tasks (T01, T02) are flagged emails with a past flag due date. M01, an overdue email request, reaches Copilot the same way, so a run cannot tell an overdue task from an overdue email ask.
- The test user organises every event, so "decline" can only mean "ask to be excused".
