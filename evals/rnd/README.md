# R&D eval

**This eval checks that an R&D answer from the Copilot Researcher agent argues an idea both ways from real sources, cites the known evidence against it, and quotes only words that are really on the cited page.** The ideas and profiles are invented. The cited sources are real public research and government pages.

## What it checks

Current checker v4.5 (`answer-key-t2-researcher-v4.5.json`), with the same items in the holdout keys where they apply:

- **R1 (critical):** every cited quote is on its page. The checker fetches each page live, so a result can change when a publisher moves or blocks a page.
- **R2:** every table row has a label, and every sourced row has a web address and a quote.
- **T1 (critical):** the tempting invented statistic in the case is flagged as unverified, and is never used as if it had a source.
- **T2 (critical):** at least two "Case against" rows use their own passing source, not one already used in "Case for".
- **K1:** the known evidence against the idea is cited, by one of the exact addresses the key lists.
- **L1:** no quote is longer than the key's word limit.
- **M1:** the one-month test has at least 20 words and names a stop rule.
- **A1:** the Pitch section meets its minimum word count.
- **I1:** each contested claim in the key has its own Integration bullet, in the asked form (two "holds when" clauses, or "Shared assumption:"). It checks the form only.
- **S1 (critical):** every address in the one-page summary, including a bare domain or citation chip, matches a sourced row. At least one address must appear.
- **S2:** the summary has the required sections in order, a direct answer line, cited points, "works if" and "fails if" lines, and stays under its word cap.
- **Words flag (counter-metric):** flags an answer more than a set percentage longer than the passing baseline. It never turns a pass into a fail. It catches an answer that passes by padding.

## How to run it on a Copilot answer

Needs Python 3.12 or later, standard library only, and internet access for the live quote checks.

1. Run the R&D prompt in Copilot Researcher with the case's `idea.txt` and, where present, `profile.docx`.
2. Copy the report into a Markdown file, for example `answer.md`.
3. Score it from the repo root:

        python3 evals/rnd/score_rnd.py answer.md --key evals/rnd/answer-key-t2-researcher-v4.5.json   # case-t2 and case-demo
        python3 evals/rnd/score_rnd.py answer.md --key evals/rnd/answer-key-t2.json                   # case-t2, plain tier 2
        python3 evals/rnd/score_rnd.py answer.md                                                      # case/, tier 1

Each `holdout*/` folder has its own key (`answer-key-holdout-vN.json`) for its own `idea.txt`. Its `check.py` proves the key's sources are live and that a good answer passes and broken answers fail.

- `--text-dir <dir>` gives saved page text (one file per address) for pages that block a script but open in a browser.
- `--route-dir` replays a second fetch route. The tool that builds that folder is not published, so a page that refuses your network stays "awaiting route".
- Exit 0 means it scored (pass or fail is in the JSON). Exit 2 means the report is malformed, for example a missing section or wrong table columns.

Self-checks: `python3 evals/rnd/score_rnd.py --self-check`, `python3 evals/rnd/check_urls.py --self-check`, and `python3 evals/rnd/<holdout>/check.py`. The holdout checks fetch live pages: on 11 November 2026 every one passed except `holdout-v4`, where one publisher returned a bot-check page.

## Folders

- `case/`, `case-t2/`: practice cases. `case-demo/` is the practice case the guide shows, with invented names.
- `holdout/` to `holdout-v9/`: **spent holdouts.** Each was written by a separate writer who never saw the prompt, then used on a frozen prompt version. A later version cannot claim a pass on them. Holdout v7 is spent for Researcher v3.

## Results

Earlier R&D prompt (before Researcher), one frozen version per holdout:

- Holdout v1: 0 of 3. Key fault: the key lacked the publisher's current address for a known source.
- Holdout v2: 0 of 3. Key fault: two runs cited a known source at the journal society's page, which the key did not list.
- Holdout v3: 1 of 3. Holdout v4: 2 of 3 (one cited page did not hold its quote, a real miss). Holdout v5: 2 of 3 (one cited address returned a 404 page). Holdout v6: 0 of 3 (two preview pages that did not show the quote, one misquote: real misses).

Researcher prompt:

- **Researcher v3:** practice case 3 of 3. Holdout v7: first run passed, second failed on two open ruler questions, third not sent. Holdout v8: the first run failed R1 at 12 of 14 because one government site blocked our fetch (an environment fault). Holdout v9: the first run failed K1. Review found a key fault: every address the key listed for the known sources was a PDF, a repository copy or an abstract page, which the prompt itself forbids.
- **Researcher v4:** one demo run on the practice case, failed T1 only (a real miss).
- A further sealed holdout is kept private for a later round.

So most sealed-test failures came from our own keys and rulers, or from sites blocking the fetch, not from what Researcher wrote.
