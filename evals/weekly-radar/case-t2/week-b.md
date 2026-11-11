# Industry tier 2, week B case: how it is made

Week B has no fixed text yet, by design. Its "last week's list" is the table Copilot gave in week A,
so the two weeks test the card the way an executive uses it: one Monday's answer is the next Monday's
prior.

i) After week A is scored, take the table from week A run 1 (`rounds/t2-a1/output.md`), unedited.
ii) Write `case-t2/week-b.txt`: the "About me" paragraph from `week-a.txt`, the line
   `Last week's list (week to Monday 16 November 2026):`, then that table.
iii) Commit `week-b.txt` alone, before the week B addendum and before any week B run.

If week A run 1 failed to parse, use the first week A run that parsed, and say which in the commit
message. Never edit the rows: a wrong row in the prior list is part of the case.
