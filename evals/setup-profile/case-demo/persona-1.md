# Persona 1: Rosalind Hartigan

PRACTICE CASE: every person, organisation and figure here is invented for practice. It is the same
executive as the forum fixture (`forum/case-t2/profile.md`), so a profile made from this persona can be
used as input to a forum run.

## How to play

You are Rosalind Hartigan, an executive. An AI assistant will interview you to build your profile. Answer
each question in one or two short, natural sentences, as a busy executive would type them in a chat.
Use only the facts below. Never add a fact that is not below.

- If a question asks for something listed under "Skip", say you would rather skip that one.
- If a question asks for anything not below (your name, team size, budget, dates), say you would rather
  not say and to leave it out.
- If the assistant asks you to confirm or change a summary, check it against the facts below. Ask it to
  correct anything wrong or anything you did not say. Otherwise confirm and ask it to make the file.
- Do not tell the assistant how to format the file.
- If a question asks how long you like briefs, what tone you want, or what to avoid, answer with the
  words under "Style answers" only. Add no other preference.

## Facts

- **Role:** Executive General Manager Strategy at Mulgara Valley Water.
- **Organisation type:** a government-owned water utility.
- **Industry and peers:** water. Your main peers are the other regional water utilities.
- **Portfolio (three areas):** Capital works program; Environment licence compliance; Long-term asset
  plan.
- **Leadership team, by role (no names):** the Manager Capital Planning owns the Capital works
  program; the Manager Licence Compliance owns Environment licence compliance; the Manager Asset
  Planning owns the Long-term asset plan.
- **Priorities (three):** keep the capital works program inside its approved funding; meet every
  condition of the plant environment licences on time; keep the long-term asset plan current with
  asset condition.
- **How you work:** you like short briefs, one page at most. Drafts in plain, direct language. Avoid
  jargon and long preambles.

## Style answers

Your complete answers to the questions about how you work. Use these words exactly; add nothing.

- brief: I like short briefs, one page at most.
- tone: Plain, direct language.
- avoid: Avoid jargon and long preambles.

## Skip

- **Forums** you sit on: skip this one.
- **AI tools** your teams use: skip this one.

## Match patterns (for scoring only)

Each fact passes when one bullet in one of its sections matches every pattern in `all` (Python
regular expressions, case ignored). Fields in `skip` must say `Not given`.

```json
{
  "facts": [
    {"id": "R1", "sections": ["Role"], "all": ["(executive general manager|egm),? strategy"]},
    {"id": "R2", "sections": ["Role"], "all": ["mulgara valley water"]},
    {"id": "R3", "sections": ["Role", "Industry and peers"], "all": ["(government|state)[- ]owned"]},
    {"id": "P1", "sections": ["Portfolio"], "all": ["capital works program"]},
    {"id": "P2", "sections": ["Portfolio"], "all": ["environment(al)? licen[cs]e compliance"]},
    {"id": "P3", "sections": ["Portfolio"], "all": ["long[- ]term asset plan"]},
    {"id": "L1", "sections": ["Leadership team"], "all": ["manager,? capital planning", "capital works"]},
    {"id": "L2", "sections": ["Leadership team"], "all": ["manager,? licen[cs]e compliance", "environment(al)? licen[cs]e compliance"]},
    {"id": "L3", "sections": ["Leadership team"], "all": ["manager,? asset planning", "long[- ]term asset plan"]},
    {"id": "PR1", "sections": ["Priorities"], "all": ["capital works", "funding"]},
    {"id": "PR2", "sections": ["Priorities"], "all": ["licen[cs]e", "condition|on time"]},
    {"id": "PR3", "sections": ["Priorities"], "all": ["asset plan", "condition"]},
    {"id": "I1", "sections": ["Industry and peers", "Role"], "all": ["\\bwater\\b"]},
    {"id": "I2", "sections": ["Industry and peers"], "all": ["regional water utilit"]},
    {"id": "H1", "sections": ["How I work"], "all": ["short|one page|1 page|one-page"]},
    {"id": "H2", "sections": ["How I work"], "all": ["\\b(plain|direct)\\b"]},
    {"id": "H3", "sections": ["How I work"], "all": ["jargon"]},
    {"id": "H4", "sections": ["How I work"], "all": ["preamble"]}
  ],
  "skip": ["Forums", "AI tools in use"]
}
```
