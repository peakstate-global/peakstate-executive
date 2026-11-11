# Setup profile eval

**This eval checks that the profile Copilot writes after its interview holds every fact the executive gave, in the right section, and invents nothing.** The executive is an invented persona.

## What it checks

- **F1 (critical):** the eight headings appear once each, in order: Role, Portfolio, Leadership team, Priorities, Forums, Industry and peers, AI tools in use, How I work.
- **P1:** every fact in the persona file is found in one of its allowed sections.
- **N1 (critical):** every bullet says "Not given" or matches a real persona fact, and every clause in a matched bullet matches a fact too. An invented add-on inside a true bullet fails. This is the counter-metric to P1: it catches a profile that scores on recall by padding.
- **S1:** every field the persona skipped says "Not given".
- **PN (reported, not scored):** the Portfolio is a numbered list.

## How to run it on a Copilot answer

Needs Python 3.12 or later and pandoc (`brew install pandoc` on macOS).

1. Start the profile setup prompt in Copilot. Answer its questions as the persona in `case/persona-1.md`, using only the persona's facts.
2. Download the `profile.docx` Copilot writes.
3. Score it from the repo root:

        python3 evals/setup-profile/score_profile.py profile.docx --persona evals/setup-profile/case/persona-1.md --out score.json

The score JSON has `"pass"` and the detail per item. Exit 0 means it scored.

`player.py` is optional. It plays the persona with a separate Claude (it needs the Claude Code CLI), so a practice interview can run without a person: `python3 evals/setup-profile/player.py evals/setup-profile/case/persona-1.md transcript.md` prints the persona's next reply.

Self-checks: `python3 evals/setup-profile/score_profile.py --self-check` and `python3 evals/setup-profile/player.py --self-check`.

## Results

- **Prompt v1:** 1 of 2. The failing profile added a bullet that was not a persona fact. The cause was partly the test: the player copied one of Copilot's suggested replies, and the ruler then matched only part of the bullet. Both were fixed.
- **Prompt v2:** round 3, 1 of 2, where the failure came from the player adding its own words. Round 4, 2 of 2, after the player was fixed.
- Limit: the test never covered an executive who rambles instead of answering tidily.
