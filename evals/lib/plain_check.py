#!/usr/bin/env python3
"""Plain-language ruler for any skill output (markdown). Experimental, v0.2, 17 November 2026.

    python3 evals/lib/plain_check.py <output.md> [--refs] [--summary-end "## Appendix"] [--transcript]
    python3 evals/lib/plain_check.py --self-check

P1  every acronym (2+ capitals) is spelt out at its first use: "VARK (a model ...)" or "... (VARK)".
P2  at most 10% of summary sentences run over 25 words (summary = start to the --summary-end heading).
P3  a "Words used in this note" list exists and every term in it appears in the rest of the note.
    Without --refs, a note with no word list passes when it defines no term in brackets.
P4  (--refs) a numbered "References" list, alphabetical, each entry with a year and a web address;
    every [n] in the summary, the reconcile lines ("Claim <n>: ...") and the Source cells points at
    an entry, every entry is cited there, and every sourced table row cites one.

Not read for P1 and P2: headings, drafts, text in quotation marks, Quote cells and "Quote:" lines,
code in backticks, web addresses, the word list and the reference list. Quotes keep their source's
words (block rule iv); drafts write acronyms the way the team does (block rule v). The block is
the PLAIN ENGLISH section of each prompt in prompts/. Counter-metric: the skill's own evidence scorer must still pass,
so plain wording never buys its way past a missing quote, source, fact or item.

Changed from v0.1. Experimental phase: the ruler and the prompts move together, so v0.2 results
are not comparable with v0.1 results.
  i)   P2 splits at line ends, bullets and table rows as well as at . ! ? ; and no heading line is
       read for P1 or P2. v0.1 read a whole table, or "Move: ... Link: ... Draft to ...", as one
       sentence.
  ii)  Drafts are skipped. A draft starts at a "Draft to <name>:" line (Inbox triage), or at a
       "Draft email to your team" heading or a "Draft, not sent." line (Forum prep). It ends only at
       a "#" heading, a numbered line that opens with a bold title ("7. **Title**, from Kim"), or
       the title line of the next item (the line before its "Why:" line). A numbered list or a
       bold line alone inside a draft is part of the draft.
  iii) Text in quotation marks, code in backticks and "Quote:" lines are not read, and all-capital
       ordinary words (URGENT, OR, CONFIDENTIAL, FW) are not acronyms. An acronym followed by a
       plural s or digits (KPIs, RSVPs, FY27) is read as its stem (KPI, RSVP, FY). The Quote column
       is found by its header name: v0.1 dropped the last cell of every row, which in Weekly radar
       holds Copilot's own words.
  iv)  P4 reads [n] only from the summary, the reconcile lines and the Source cells, never from a
       quote: a source's own "[1]" is not a citation.
  v)   The word-list, References and --summary-end headings are found at any heading level, or as
       a bold line on its own ("**References**", "**References:**" or "**References**:"), because
       Copilot's clipboard markdown varies.
  vi)  P3 without --refs: a note with no word list passes when it defines no term in brackets. A
       bracket that opens "see", "for example", "e.g.", "such as" or "including" is a note, not a
       definition; a bracket with a digit ("injuries per 1 million hours") can be a definition.
  vii) --transcript reads only Copilot's turns, without the transcriber's lines that sit wholly in
       brackets (suggested replies, file notes). A speaker label on the same line as text
       ("**Executive:** text") starts that speaker's turn; "**Copilot:** text" keeps the text. A
       transcript with no Copilot text fails every item with an error.

v0.2 review fixes (17 November 2026, before any run): acronym stems with a plural s or digits
(iii), more all-capital ordinary words (iii), drafts end only at the markers in ii, a colon
outside the bold on a heading line (v), definitions with digits and note brackets (vi), inline
speaker labels and an empty transcript (vii). No run used v0.2 before these fixes.

Per skill (what each run is measured on):
  Skill               --summary-end                    Read                                  Drafts skipped
  Forum prep          default; no Appendix: all of it  output.md                             each "Draft email to your team" section
  Inbox triage        default; no Appendix: all of it  output.md                             each "Draft to <name>:" draft
  R&D                 "## Appendix" (default), --refs  output.md                             none
  Weekly radar        default; no Appendix: all of it  output.md, "Quote:" lines skipped     none
  Your profile setup  default; no Appendix: all of it  Copilot's turns in transcript.md       none
                                                       (--transcript); never profile.docx
Exit 0 when every item passes, 1 otherwise.
"""
import re, sys

LONG, SHARE = 25, 0.10
# ponytail: a fixed list of ordinary words seen in capitals (mail subjects, Outlook search); add one when a baseline flags it
CAPS_WORDS = {"URGENT", "IMPORTANT", "ACTION", "REQUIRED", "REMINDER", "FINAL", "NOTE", "OR", "AND", "NOT",
              "CONFIDENTIAL", "PRIVATE", "PLEASE", "READ", "FW", "FWD", "RE", "UPDATE", "NEW", "DUE", "OVERDUE"}
ACRO = re.compile(r"\b([A-Z]{2,})(?:s\b|\d\w*|\b)")  # the stem of KPIs, RSVPs, FY27, FY2029
HEAD = re.compile(r"^\s*(?:#{1,6}\s+(.+?)|\*\*([^*]+)\*\*:?)\s*$")
DRAFT = re.compile(r"^(?:#{1,6}\s+|[-*+]\s+|\d+[.)]\s+)?\**\s*Draft(?: to \S| email to your team|, not sent)")
WHY = re.compile(r"^(?:[-*+]\s+)?\**Why\**:")
TITLE = re.compile(r"^\d+[.)]\s+\*\*")  # a numbered item that opens with a bold title, as in Inbox s01
MARK = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
CLAIM = re.compile(r"^\s*(?:[-*+]\s+)?\**Claim \d+\**:")
QUOTED = re.compile(r"`[^`]*`|https?://\S+|\"[^\"\n]*\"|“[^”\n]*”")
SPEAKER = re.compile(r"\*\*(\w[\w ]*):\*\*\s*(.*)")
# ponytail: a definition is a bracket straight after a word that opens lower-case, holds 2+ words and no colon, and
# does not open with a note word (see, for example). Ceiling: other note brackets ("(due 1 December)", "(in
# Brisbane)") read as definitions; no ruler can tell every definition from every bracket (ADR 0018 vi). Add an
# opening word to the list when a baseline flags one.
DEFN = re.compile(r"[A-Za-z][\w-]*\s+\((?!see\b|for example\b|e\.g\.|such as\b|including\b|p\.|pp\.)"
                  r"([a-z][^():]*\s[^():]*)\)")


def heading(line):
    """The heading text of a markdown heading at any level or a bold line on its own, else None."""
    m = HEAD.match(line)
    return (m.group(1) or m.group(2)).strip().strip("*").strip().rstrip(":").strip() if m else None


def section(lines, name):
    """(heading index, end index) of the first section whose heading starts with name, else None."""
    for i, line in enumerate(lines):
        h = heading(line)
        if h and h.lower().startswith(name):
            return i, next((k for k in range(i + 1, len(lines)) if heading(lines[k]) is not None), len(lines))
    return None


def rows(lines):
    """(index, header, cells) for each table data row; header names in lower case."""
    head = None
    for i, line in enumerate(lines):
        if not line.lstrip().startswith("|"):
            head = None
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-+:?", c) for c in cells):
            continue
        if head is None:
            head = [c.lower() for c in cells]
            continue
        yield i, head, cells


def next_text(lines, i):
    return next((l.strip() for l in lines[i + 1:] if l.strip()), "")


def read_lines(lines):
    """The lines P1 and P2 read, with quotes, code and web addresses taken out (see the docstring)."""
    table = {i: (head, cells) for i, head, cells in rows(lines)}
    skip = set()
    for name in ("words used", "references"):
        r = section(lines, name)
        if r:
            skip.update(range(*r))
    out, draft = [], False
    for i, line in enumerate(lines):
        s = line.strip()
        h = heading(s)
        if h is not None:  # a "#" heading ends a draft; a bold line alone can start one, never end one
            draft = bool(DRAFT.match(h)) or (draft and not s.startswith("#"))
            continue
        if draft and (TITLE.match(s) or WHY.match(next_text(lines, i))):
            draft = False
        if DRAFT.match(s):
            draft = True
        if draft or i in skip or not s:
            continue
        if s.startswith("|"):
            if i not in table:
                continue  # header or separator row
            head, cells = table[i]
            s = " ".join(c for c, h in zip(cells, head) if h != "quote")
        s = MARK.sub("", s)
        if s.lstrip("*").startswith("Quote:"):
            continue
        out.append(QUOTED.sub("", s))
    return out


def summary(lines, end):
    name = end.lstrip("#").strip().lower()
    for i, line in enumerate(lines):
        h = heading(line)
        if name and h and h.lower().startswith(name):
            return lines[:i]
    return lines


def p1(md):
    text, bad, seen = "\n".join(read_lines(md.splitlines())), [], set()
    for m in ACRO.finditer(text):
        a = m.group(1)
        if a in seen or a in CAPS_WORDS:
            continue
        seen.add(a)  # first use only: "KPIs (key ...)" or "(KPIs)"
        after, before = text[m.end():m.end() + 2], text[max(0, m.start() - 1):m.start()]
        if not (after.lstrip().startswith("(") or before == "("):
            bad.append(a)
    return not bad, f"not spelt out at first use: {', '.join(bad)}" if bad else "all spelt out"


def p2(md, end):
    sents, words = [], 0
    for line in read_lines(summary(md.splitlines(), end)):
        line = re.sub(r"\*\*|\[\d+\]", "", line)
        words += len(line.split())
        sents += [s for s in re.split(r"(?<=[.!?;])\s+", line) if len(s.split()) > 2]
    long = [s for s in sents if len(s.split()) > LONG]
    share = len(long) / len(sents) if sents else 0
    return share <= SHARE, f"{len(long)} of {len(sents)} sentences over {LONG} words ({share:.0%}); summary {words} words"


def p3(md, refs=False):
    lines = md.splitlines()
    r = section(lines, "words used")
    if r is None:
        if refs:
            return False, "no Words used section"
        defs = DEFN.findall("\n".join(read_lines(lines)))
        if defs:
            return False, f"no Words used section, but {len(defs)} defined in brackets, first: ({defs[0]})"
        return True, "no Words used section, and no term defined in brackets"
    terms = re.findall(r"^\s*[-*]\s+\*\*(.+?):?\*\*", "\n".join(lines[r[0] + 1:r[1]]), flags=re.M)
    rest = "\n".join(lines[:r[0]] + lines[r[1]:]).lower()
    dead = [t for t in terms if t.lower() not in rest]
    if not terms:
        return False, "Words used section is empty"
    return not dead, f"{len(terms)} terms; not used in the note: {', '.join(dead)}" if dead else f"{len(terms)} terms, all used"


def p4(md, end="## Appendix"):
    lines = md.splitlines()
    r = section(lines, "references")
    if r is None:
        return False, "no References section"
    refs = re.findall(r"^\s*(\d+)\.\s+(.+)$", "\n".join(lines[r[0] + 1:r[1]]), flags=re.M)
    nums, faults = [int(n) for n, _ in refs], []
    if nums != list(range(1, len(nums) + 1)):
        faults.append("not numbered 1..n")
    texts = [t for _, t in refs]
    if [t.lower() for t in texts] != sorted(t.lower() for t in texts):
        faults.append("not alphabetical")
    faults += [f"entry {n} lacks a year or web address" for n, t in refs
               if not re.search(r"\(\d{4}", t) or "http" not in t]
    # [n] only from the summary, the reconcile lines and the Source cells; never from a quote
    where = [QUOTED.sub("", l) for l in summary(lines, end) if not l.lstrip().startswith("|")]
    where += [QUOTED.sub("", l) for l in lines if CLAIM.match(l)]
    uncited = []
    for _, head, cells in rows(lines):
        row = dict(zip(head, cells))
        src = row.get("source", "")
        where.append(src)
        if row.get("label", "").lower() == "sourced" and not re.fullmatch(r"\[\d+\]", src):
            uncited.append(f"sourced row {cells[0]} cites no reference")
    cited = {int(n) for n in re.findall(r"\[(\d+)\]", "\n".join(where))}
    faults += [f"[{n}] has no entry" for n in sorted(cited - set(nums))]
    faults += [f"entry {n} never cited" for n in sorted(set(nums) - cited)] + uncited
    return not faults, "; ".join(faults) if faults else f"{len(nums)} references, all cited, alphabetical"


def copilot_turns(md):
    """Copilot's turns of a transcript ("**Copilot:**" to the next "**<speaker>:**"), without
    lines wholly in brackets (the transcriber's notes: suggested replies, files made). A label with
    text after it on the same line counts only for the two lab speakers, so a "**Role:** text" line
    inside Copilot's turn stays in it."""
    keep, on = [], False
    for line in md.splitlines():
        m = SPEAKER.fullmatch(line.strip())
        if m and (not m.group(2) or m.group(1) in ("Copilot", "Executive")):
            on, line = m.group(1) == "Copilot", m.group(2)
            if not line:
                continue
        if on and not re.fullmatch(r"\(.*\)", line.strip()):
            keep.append(line)
    return "\n".join(keep)


def check(md, refs=False, end="## Appendix", transcript=False):
    if transcript:
        md = copilot_turns(md)
        if not md.strip():
            err = (False, "error: no Copilot turn read; is this a transcript with **Copilot:** labels?")
            return {k: err for k in ("P1", "P2", "P3", "P4")[:4 if refs else 3]}
    items = {"P1": p1(md), "P2": p2(md, end), "P3": p3(md, refs)}
    if refs:
        items["P4"] = p4(md, end)
    return items


def self_check():
    # v0.1 probes: the known-good note passes, the known-bad one fails P1 and P4
    good = ("## Executive summary\n\nUse VARK (a model of learning styles) with care [1].\n\n## Appendix\n\n"
            "| # | Claim | Label | Source | Quote |\n|---|---|---|---|---|\n| 1 | A claim. | sourced | [1] | THE QUOTE. |\n\n"
            "## Words used in this note\n\n- **VARK:** a model.\n\n## References\n\n1. Smith, J. (2024). Title. https://example.org\n")
    bad = good.replace("VARK (a model of learning styles)", "VARK").replace("| [1] |", "| x |", 1)
    assert all(ok for ok, _ in check(good, refs=True).values()), check(good, refs=True)
    r = check(bad, refs=True)
    assert not r["P1"][0] and not r["P4"][0], r
    assert r["P3"][0]  # the term is still used

    # i) P2 splits at line ends, bullets and table rows; headings are not read
    rowtext = "check the dispatch numbers and the overtime figures with the site team before the meeting starts"
    t = ("## " + "word " * 30 + "\n\n| When | Prepare |\n|---|---|\n"
         + "".join(f"| Monday {k} am | {rowtext} |\n" for k in range(3))
         + "| Friday | Ask the GM for the plan |\n\n- Move: Do\n- Link: none\n- Draft to Sam:\n")
    ok, why = p2(t, "## Appendix")
    assert ok and why.startswith("0 of 4"), why  # v0.1 read the table and the bullets as one sentence
    assert p1(t) == (False, "not spelt out at first use: GM"), p1(t)  # the last column is read: it is no Quote column

    # ii) drafts are skipped, from their marker to a "#" heading, a bold-titled numbered item or the line
    # before a "Why:" line. A numbered list or a bold line alone inside a draft does not end it. Item 3
    # has no "Why:" line: its bold title ends the draft before it (the Inbox s01 shape).
    inbox = ("## Needs you today\n\n- Budget, from Kim\n\n- Why: due Friday.\n\n- Move: Do\n\n- Draft to Kim:\n\n"
             "Kim, the ELT wants " + "a very long line of words " * 6 + "today.\n\n- October numbers: [figure]\n\n"
             "1. the LTIFR trend\n2. the OTIF report\n\n**[approve the RFQ / do not approve]**\n\n"
             "Thanks, Alex\n\n- Roster, from Sam\n\n- Why: due Monday for the CFO.\n\n"
             "2. **Lease**, from Jo\n* Draft to Jo:\n\nJo, the MVA is fine.\n\n3. **Lights**, from the KPI desk\n")
    assert p1(inbox) == (False, "not spelt out at first use: CFO, KPI"), p1(inbox)
    assert p2(inbox, "## Appendix")[0], p2(inbox, "## Appendix")
    forum = ("### Draft email to your team\n\nDraft, not sent.\nTo: Manager Field Services\n"
             "Please send me:\n\n1. the plan from the ELT\n\n**Thanks**\n\n## Paper 2\n\nThe WTP rose.\n")
    assert p1(forum) == (False, "not spelt out at first use: WTP"), p1(forum)

    # iii) quoted text, code, Quote: lines and all-capital ordinary words are not read as acronyms
    q = ('URGENT: inputs from Pat. Search `from:a OR from:b`, then pick one OR the other. '
         'He wrote "the ELT met" and “the CEO agreed”.\nQuote: The ABS said so.\nThe WTP rose.\n')
    assert p1(q) == (False, "not spelt out at first use: WTP"), p1(q)
    caps = "CONFIDENTIAL: board pack, from Kim.\nPLEASE READ: new roster.\nFW: roster, from Sam.\n"
    assert p1(caps)[0], p1(caps)
    # an acronym with a plural s or digits is read as its stem, and first use is checked on the stem
    stems = "FY27 budget templates, from Kim.\nChristmas party RSVPs open.\nThe KPIs are on track.\n"
    assert p1(stems) == (False, "not spelt out at first use: FY, RSVP, KPI"), p1(stems)
    assert p1("Financial year (FY) 2027 is set. The key performance indicators (KPIs) and KPIs (key "
              "performance indicators) hold. The FY2029 plan is due.\n")[0]

    # iv) P4 reads [n] from the summary, reconcile lines and Source cells, never from a quote
    quoted6 = good.replace("THE QUOTE.", "As shown before [6].")
    assert check(quoted6, refs=True)["P4"][0], check(quoted6, refs=True)  # v0.1: "[6] has no entry"
    two = (good.replace("| THE QUOTE. |", "| See [2]. |")
           .replace("https://example.org\n", "https://example.org\n2. Zed, A. (2023). Other. https://example.net\n"))
    assert check(two, refs=True)["P4"] == (False, "entry 2 never cited"), check(two, refs=True)
    claim = two + "\n## Where both sides are right\n\n- Claim 1: Both sides assume the test is fair [2].\n"
    assert check(claim, refs=True)["P4"][0], check(claim, refs=True)

    # v) headings at any level or as a bold line on its own
    styled = (good.replace("## Words used in this note", "### Words used in this note")
              .replace("## References", "**References**").replace("## Appendix", "**Appendix: the evidence**"))
    assert all(ok for ok, _ in check(styled, refs=True).values()), check(styled, refs=True)
    colon = good.replace("## Words used in this note", "**Words used in this note**:").replace("## References", "**References**:")
    assert all(ok for ok, _ in check(colon, refs=True).values()), check(colon, refs=True)

    # vi) P3 without --refs: no word list passes only when no term is defined in brackets
    assert p3("The plan is simple and the team agrees.\n")[0]
    assert p3("The plan is simple (see the table below for dates).\n")[0]  # a note bracket, not a definition
    assert not p3("The plan uses a meta-analysis (a study that combines many studies).\n")[0]
    assert not p3("The plan tracks the injury rate (injuries per 1 million hours worked).\n")[0]
    assert not p3("The plan is simple.\n", refs=True)[0]

    # vii) --transcript reads only Copilot's turns, without bracketed transcriber lines; a label with text
    # on the same line starts that speaker's turn, and a transcript with no Copilot text fails with an error
    tr = ("# Transcript\n\n**Executive:**\n\nThe ELT agreed.\n\n**Copilot:**\n\nWhat does the CFO want?\n\n"
          "(Suggested replies shown: the KPI list)\n\n**Executive:**\n\nThe MVA.\n")
    assert check(tr, transcript=True)["P1"] == (False, "not spelt out at first use: CFO"), check(tr, transcript=True)
    inline = ("**Copilot:**\n\nWhat is your role?\n\n**Executive:** I run the ELT.\n\n**Copilot:** Which AI tools "
              "do you use?\n\n**Role:** the COO\n")
    assert check(inline, transcript=True)["P1"] == (False, "not spelt out at first use: AI, COO"), check(inline, transcript=True)
    none = check("**Executive:** hello.\n", transcript=True)
    assert all(not ok and why.startswith("error:") for ok, why in none.values()), none
    print("self-check passed")


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        self_check()
        sys.exit(0)
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__.split("\n\n")[1])
    end = args[args.index("--summary-end") + 1] if "--summary-end" in args else "## Appendix"
    items = check(open(args[0], encoding="utf-8").read(), refs="--refs" in args, end=end,
                  transcript="--transcript" in args)
    for k, (ok, why) in items.items():
        print(f"{k} {'pass' if ok else 'FAIL'}: {why}")
    sys.exit(0 if all(ok for ok, _ in items.values()) else 1)
