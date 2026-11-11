# Forum demo case: Coralline Coast Water, Executive Leadership Team, 15 December 2026

**Demo case for the guide, not a test case.** It has no answer key and no scorer. It exists to show
what the forum prompt gives a realistic executive on a realistic pack. Built to the layout of real public board packs.
Every organisation, person and figure is invented. Addresses use `example.org` only.

## Files

- `build.py`: builds `pack.pdf` (48 pages) and `profile.docx` (pandoc from `profile.md`), then checks the pack.
  `--check` checks only: 48 pages, page 32 has no text layer, 13 key facts each on exactly their own page, no
  "Sample" or "Example" in any name, reserved domains only, every page after the cover prints "Page N of 48".
- `invitation.txt`: the invitation, attendee list and the previous-pack extract (Q4 FY2026 scorecard and ranking).
- `profile.md`, `profile.docx`: Leanne Fairbairn, Executive General Manager Network Operations. Four areas:
  Water treatment, Wastewater networks, Field services, Fleet and depots. One leadership team role owns each.

## The pack

Printed page = physical page. Order: cover, order of business (2 pages, owner, action verb, time, page), members,
apologies and the standing register of interests, minutes of 17 November 2026 (2 pages), action log, then papers in
one template (item, title, paper type, sponsor, author, record number, purpose, recommendation, background, and for
the decision paper options, strategic alignment, financial implications, a risk table with untreated and treated
ratings, policy, consultation and attachments). Then a confidential item listed by title only, a glossary and a close.

| Item | Paper | Pages |
|---|---|---|
| 4.1 | Managing Director's report (corporate scorecard, RAG) | 7 to 9 |
| 5.1 | Quarterly operational performance (scorecard, divisional ranking) | 10 to 14 |
| 5.2 | Enterprise risk report (5 by 5 heat map, register, compliance calendar) | 15 to 19 |
| 5.3 | Finance report (operating statement, capex, variances in brackets) | 20 to 24 |
| 6.1 | Northern depot consolidation and fleet electrification, Stage 1 (for decision) | 25 to 32 |
| 6.2 | People and safety report (2027 training calendar) | 33 to 37 |
| 7.1 | Customer and regulatory update (late paper) | 38 to 41 |
| 7.2 | Major projects status report (asset condition review) | 42 to 45 |
| 8.1, 8.2 | Verbal items, no paper | - |
| 9.1 | Enterprise agreement (confidential, withheld) | 46 |

## What a good brief should catch

These are the facts the demo was built around. They are not a scoring key.

| Id | What | Page |
|---|---|---|
| D1 | Decision: approve $14.8M Stage 1 of the Northern depot | 25 |
| C1 | Field jobs attended within target time 88% to 84%, still Amber | 11, previous pack |
| C2 | Scanned letter: Bellgrove site cannot be energised before March 2028 (crews move July 2027) | 32 |
| C3 | Ashby lease cannot be extended past 30 June 2027 (General Counsel) | 18 |
| Q1 | Gate 2 review by the Investment Review Panel required before ELT approval; no paper shows it done | 31, action log 6 |
| A1 to A4 | MD (supports in principle, crews never lose a base), CFO (only after Gate 2), General Counsel (no lease extension), EGM People and Safety (union consultation not started) | 9, 23, 18, 36 |
| X1 | Confined space refresher moved to July 2027; certificates expire 30 April 2027 (Wastewater networks) | 35, 19 |
| U1 | Bellcourt chlorine dosing system, condition 4, 1 year remaining life, renewal FY2029 (Water treatment) | 45 |
| R1 | Field services ranks 6 of 6, second quarter running; resolution ELT 2026/41 requires a recovery plan | 12, 5 |
| R2 | Water treatment ranks 1 of 6; same resolution asks it to share what worked | 12, 5 |
| O1 | State Water Resilience Fund, up to $2.5M, closes 26 February 2027 (Water treatment) | 40 |

No instruction aimed at an AI is planted: real packs do not carry one, so Warnings should say "None found."
