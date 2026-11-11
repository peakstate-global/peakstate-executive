# How we test the prompts

**Every skill in this repo was tuned against invented practice cases with answer keys, and scored by the scripts in this folder.** You can rerun any case in your own Copilot, paste the answer into a file, and score it the same way we did.

## What is here

| Folder | Skill | What the eval checks |
|---|---|---|
| [setup-profile](setup-profile/) | Your profile | The profile holds every fact the executive gave, in the right section, and invents nothing. |
| [forum-prep](forum-prep/) | Forum prep | The answer finds planted facts in an invented board pack, and every quote is on the page it cites. |
| [rnd](rnd/) | R&D | Researcher argues the idea both ways, cites the known evidence against it, and quotes real pages. |
| [weekly-radar](weekly-radar/) | Weekly radar | The week ahead finds planted items in a test mailbox, and each radar item quotes a real page dated in the last seven days. |
| [inbox-triage](inbox-triage/) | Inbox triage | Each email gets the right move, drafts match each sender's tone, and a hidden instruction is never obeyed. |
| [lib](lib/) | shared | `score.py`, the table scorer that Forum prep, R&D, Weekly radar and Inbox triage build on. |

Each skill folder has a README with each check in plain words, the exact commands, and the results.

## Words used here

- **Practice case:** an invented input (a board pack, an idea, a mailbox, a past news week) with an answer key. We tuned the prompts on these.
- **Answer key:** what a good answer must contain, and the traps it must avoid, as JSON. The scorer reads it.
- **Ruler:** the scorer plus its key, at one version. A changed ruler gives scores that are not comparable with the old ones, so each version is kept.
- **Holdout:** a case written by a separate writer who never saw the prompt, sealed until a frozen prompt version ran on it once. After that run it is **spent**. A spent holdout is published here, marked "spent holdout". A holdout that is not yet spent stays private, so it can still test a later version.
- **Counter-metric:** a second number that gets worse if the first is being gamed, such as words per page against items found.

## Run it

Needs Python 3.12 or later. Most scorers use the standard library only. Forum prep also needs Pillow and poppler (`pdftotext`, `pdfinfo`), Your profile needs pandoc, Weekly radar needs git, and the R&D and Weekly radar quote checks fetch live pages.

Run every self-check from the repo root:

    python3 evals/lib/score.py --self-check
    python3 evals/setup-profile/score_profile.py --self-check
    python3 evals/forum-prep/score_forum.py --self-check
    python3 evals/rnd/score_rnd.py --self-check
    python3 evals/weekly-radar/score_week.py --self-check
    python3 evals/weekly-radar/score_industry.py --self-check
    python3 evals/inbox-triage/drafts.py --self-check

A self-check proves the scorer passes a good answer and fails each broken one. It does not call Copilot.

## Results in short

- Practice cases: each skill has at least one prompt version that passed its practice case, except Weekly radar, which is still a pilot.
- Sealed holdouts: Forum prep passed one (3 of 3) and R&D passed parts of several. Most sealed-test failures came from faults in our own keys and rulers (a key that missed a valid page address, a key that asked for something the prompt forbids, a ruler that misread a date), or from a site that blocked our fetch, rather than from what Copilot wrote. We fixed each fault in a new ruler version and did not re-score the spent holdout.
- Inbox triage is proven on pasted mail only, not on a live mailbox, so it stays in beta.

Every person and organisation in the practice cases is invented. The R&D and Weekly radar keys cite real public research, government and news pages as sources.

## Licence

[CC BY 4.0](../LICENSE), like the rest of this repo. Feedback: [contact@peakstate.global](mailto:contact@peakstate.global).
