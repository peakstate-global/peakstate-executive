#!/usr/bin/env python3
"""Plain-language ruler for any skill output (markdown). Experimental, v0.3, 17 November 2026.

    python3 evals/lib/plain_check.py <output.md> [--refs] [--summary-end "## Appendix"] [--transcript]
                                           [--source <pasted.txt>]
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

Changes from v0.2 (17 November 2026, after the Release 1.1 runs). Experimental phase: the ruler
moves on its own this round, so v0.3 results are not comparable with v0.2 results, and every run of record keeps its
v0.2 result.
  i)   --source <pasted.txt> (Inbox triage, the pasted route): the exact subject and sender-name text of each email
       in the pasted case ("Subject:" lines, and the name before the address on "From:" lines) is masked the same
       way quoted text is, wherever the output copies it. Any word Copilot adds around a copied subject or name is
       still read. Without --source nothing is masked, as in v0.2.
  ii)  A numbered bold line ("**1. Title**", or "1. **Title**") is text, not a heading, for P1 and P2. v0.2 read
       "**1. Title**" as a heading and skipped it; the section boundaries P3 and P4 use are unchanged.
  iii) P3 leaves the References section out when it looks for each listed term, so a term found only in a
       reference title counts as not used.
  iv)  Counter-metric, report only, never part of pass or fail: for each section P2 reads, the prose words (the
       words of the lines P1 and P2 read, without code and web addresses), the words P2 read, and the quoted share
       (quoted text, and with --source the copied subjects and names). A section is a heading's text ("start"
       before the first heading), or the lines that open with the same short label ("Why:", "Move:", but not a
       mail prefix such as "Re:"); the label word is not counted. A section is "empty" when P2 read fewer than half
       its prose words. The command line prints it after the items, for example
       "P2 counter-metric (report only): pass, empty in Why (1 of 484 words read)".
       Review fixes, the same day, before any document recorded a v0.3 result: straight and curly
       apostrophes in a copied name now both match, and a line's label is read after masking, so a
       copied subject such as "Save the date: offsite" is no label.
       Review fixes, 17 November 2026: a copied subject or sender value with no lower-case letter (an
       acronym alone, such as "HR" or "AGM") is not masked, so Copilot's own uses of it still count for P1.

Per skill (what each run is measured on):
  Skill               --summary-end                    Read                                  Drafts skipped
  Forum prep          default; no Appendix: all of it  output.md                             each "Draft email to your team" section
  Inbox triage        default; no Appendix: all of it  output.md, --source case pasted.txt   each "Draft to <name>:" draft
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
NUMBOLD = re.compile(r"^\*\*\d+[.)]\s+")  # v0.3 ii: "**1. Title**" is text, not a heading
# v0.3 iv: a short label such as "Why:", "**Move:**" or "Why now:", but not a mail prefix ("Re: Re: Budget")
LABEL = re.compile(r"^\**(?!(?:Re|Fw|Fwd)\W)([A-Z][a-z]*(?: [a-z]+){0,2})\**:\**\s*")
NOT_PROSE = re.compile(r"`[^`]*`|https?://\S+")  # v0.3 iv: code and web addresses are not prose words
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


def copied(pasted):
    """v0.3 i: the subjects and sender names in a pasted case, as one pattern (longest first), or None."""
    found = set()
    for line in pasted.splitlines():
        m = re.match(r"\s*(Subject|From):\s*(.+)", line)
        if m:
            t = m.group(2).strip()
            found.add(re.sub(r"\s*<[^>]*>$", "", t).strip().strip('"') if m.group(1) == "From" else t)
    # review fix: a value with no lower-case letter ("HR", "AGM") is not masked, so Copilot's own uses still count
    found = sorted((t for t in found if any(c.islower() for c in t)), key=len, reverse=True)
    # ponytail: straight and curly apostrophes count as the same character; no other normalising
    alts = [re.sub(r"['’]", "['’]", re.escape(t)) for t in found]
    return re.compile(r"(?<!\w)(?:" + "|".join(alts) + r")(?!\w)") if alts else None


def reads(lines, mask=None):
    """(section, prose, read) for each line P1 and P2 read. prose is the line without code and web addresses; read
    also has quotes and the --source text taken out (see the docstring). section is the last heading's text, or
    "start" before the first heading."""
    table = {i: (head, cells) for i, head, cells in rows(lines)}
    skip = set()
    for name in ("words used", "references"):
        r = section(lines, name)
        if r:
            skip.update(range(*r))
    draft, sect = False, "start"
    for i, line in enumerate(lines):
        s = line.strip()
        h = None if NUMBOLD.match(s) else heading(s)
        if h is not None:  # a "#" heading ends a draft; a bold line alone can start one, never end one
            draft = bool(DRAFT.match(h)) or (draft and not s.startswith("#"))
            sect = h
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
        s = NUMBOLD.sub("", MARK.sub("", s))
        if s.lstrip("*").startswith("Quote:"):
            continue
        yield sect, NOT_PROSE.sub("", s), QUOTED.sub("", mask.sub("", s) if mask else s)


def read_lines(lines, mask=None):
    """The lines P1 and P2 read, with quotes, code and web addresses taken out (see the docstring)."""
    return [r for _, _, r in reads(lines, mask)]


def summary(lines, end):
    name = end.lstrip("#").strip().lower()
    for i, line in enumerate(lines):
        h = heading(line)
        if name and h and h.lower().startswith(name):
            return lines[:i]
    return lines


def p1(md, mask=None):
    text, bad, seen = "\n".join(read_lines(md.splitlines(), mask)), [], set()
    for m in ACRO.finditer(text):
        a = m.group(1)
        if a in seen or a in CAPS_WORDS:
            continue
        seen.add(a)  # first use only: "KPIs (key ...)" or "(KPIs)"
        after, before = text[m.end():m.end() + 2], text[max(0, m.start() - 1):m.start()]
        if not (after.lstrip().startswith("(") or before == "("):
            bad.append(a)
    return not bad, f"not spelt out at first use: {', '.join(bad)}" if bad else "all spelt out"


def p2(md, end, mask=None):
    sents, words = [], 0
    for line in read_lines(summary(md.splitlines(), end), mask):
        line = re.sub(r"\*\*|\[\d+\]", "", line)
        words += len(line.split())
        sents += [s for s in re.split(r"(?<=[.!?;])\s+", line) if len(s.split()) > 2]
    long = [s for s in sents if len(s.split()) > LONG]
    share = len(long) / len(sents) if sents else 0
    return share <= SHARE, f"{len(long)} of {len(sents)} sentences over {LONG} words ({share:.0%}); summary {words} words"


def p3(md, refs=False, mask=None):
    lines = md.splitlines()
    r = section(lines, "words used")
    if r is None:
        if refs:
            return False, "no Words used section"
        defs = DEFN.findall("\n".join(read_lines(lines, mask)))
        if defs:
            return False, f"no Words used section, but {len(defs)} defined in brackets, first: ({defs[0]})"
        return True, "no Words used section, and no term defined in brackets"
    terms = re.findall(r"^\s*[-*]\s+\*\*(.+?):?\*\*", "\n".join(lines[r[0] + 1:r[1]]), flags=re.M)
    out = set(range(*r)) | set(range(*(section(lines, "references") or (0, 0))))  # v0.3 iii: not the References
    rest = "\n".join(l for i, l in enumerate(lines) if i not in out).lower()
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


def counter(md, end="## Appendix", mask=None):
    """v0.3 iv, the counter-metric, report only: {section: [prose words, words P2 read]} over the text P2 reads. A
    line that opens with a short label ("Why:") counts under the label, without the label word."""
    out, words = {}, lambda t: len(re.sub(r"\*\*|\[\d+\]", "", t).split())
    for sect, s, r in reads(summary(md.splitlines(), end), mask):
        # the label is read from the masked line, so a copied subject such as "Save the date: offsite" (--source)
        # is no label. ponytail: without --source that subject still reads as a label; a label list would fix it
        m, n = LABEL.match(r), LABEL.match(s)
        if m and n and m.group(1) == n.group(1):
            sect, s, r = m.group(1), s[n.end():], r[m.end():]
        g = out.setdefault(sect, [0, 0])
        g[0], g[1] = g[0] + words(s), g[1] + words(r)
    return out


def counter_lines(md, ok, end="## Appendix", mask=None):
    """The counter-metric as printed: one P2 line, then one line per section with prose words."""
    cm = [(k, p, r) for k, (p, r) in counter(md, end, mask).items() if p]
    empty = [f"{k} ({r} of {p} words read)" for k, p, r in cm if r < p / 2]
    head = f"P2 counter-metric (report only): {'pass' if ok else 'FAIL'}, " + (
        "empty in " + "; ".join(empty) if empty else "no section empty")
    what = "quoted or copied" if mask else "quoted"
    return [head] + [f"  {k}: {p} prose words, {r} read by P2, {(p - r) / p:.0%} {what}" + (", empty" if r < p / 2 else "")
                     for k, p, r in cm]


def check(md, refs=False, end="## Appendix", transcript=False, source=None):
    """P1 to P3 (P1 to P4 with refs). source is the pasted case's text (v0.3 i, --source), or None."""
    if transcript:
        md = copilot_turns(md)
        if not md.strip():
            err = (False, "error: no Copilot turn read; is this a transcript with **Copilot:** labels?")
            return {k: err for k in ("P1", "P2", "P3", "P4")[:4 if refs else 3]}
    mask = copied(source) if source else None
    items = {"P1": p1(md, mask), "P2": p2(md, end, mask), "P3": p3(md, refs, mask)}
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

    # v0.3 i) --source masks the exact subjects and sender names copied from the pasted case, wherever they appear,
    # straight or curly apostrophe; a word added around them, or a part of a subject, is still read
    pasted = ("--- Email 1 ---\nFrom: IT Service Desk <it@example.com>\nSubject: FY27 budget templates\n\n"
              "--- Email 2 ---\nFrom: \"Kim O'Hara\" <kim@example.com>\nSubject: Re: RSVPs for the CFO dinner\n")
    slot = ("- FY27 budget templates, from IT Service Desk, for the KPI review\n"
            "- Re: RSVPs for the CFO dinner, from Kim O’Hara\n- Why: the FY27 plan is due.\n")
    assert p1(slot) == (False, "not spelt out at first use: FY, IT, KPI, RSVP, CFO"), p1(slot)  # no --source: as v0.2
    assert check(slot, source=pasted)["P1"] == (False, "not spelt out at first use: KPI, FY"), check(slot, source=pasted)
    # review fix: the v0.3 review's seven --source probes; an acronym-only sender or subject is not masked (b, c)
    for name, src, md, want in (
            ("a", "Subject: FY27 budget templates\n", "- FY27 budget templates\n- Why: the FY27 plan is due.\n", False),
            ("b", "From: HR <hr@x>\nSubject: Leave forms\n", "- Leave forms, from HR\n- Why: HR wants the forms back.\n", False),
            ("c", "From: Kim Haddad <k@x>\nSubject: AGM\n", "- AGM, from Kim Haddad\n- Move: book the AGM venue.\n", False),
            ("d", "From: Kim <k@x>\nSubject: Roster\n\nFrom: the CEO office, a note.\n", "- Why: the CEO office wants it.\n", False),
            ("e", "Subject: Update\n", "- Update\n- Why: the ELT meets Friday. Update the ELT.\n", False),
            ("f", "Subject: Budget templates\n", "- Budget KPI templates\n", False),
            ("g", "From: IT Service Desk <it@x>\nSubject: FY27 budget templates\n",
             "- FY27 budget templates, from IT Service Desk\n", True)):
        assert check(md, source=src)["P1"][0] == want, (name, check(md, source=src)["P1"])

    # v0.3 ii) a numbered bold line is text for P1 and P2, in either form (v0.2 skipped "**1. Title**" as a heading)
    nb = "**1. The ELT met**\n\n1. **The CFO agreed**\n\n**2. " + "word " * 30 + "end**\n"
    assert p1(nb) == (False, "not spelt out at first use: ELT, CFO"), p1(nb)  # v0.2: CFO only
    assert p2(nb, "## Appendix")[1].startswith("1 of 3 sentences"), p2(nb, "## Appendix")  # v0.2: 0 of 1

    # v0.3 iii) P3 leaves References out: a term found only in a reference title is not used (v0.2: all used)
    t3 = (good.replace("- **VARK:** a model.", "- **VARK:** a model.\n- **Meta-analysis:** a study of studies.")
          .replace("Title.", "A meta-analysis of styles."))
    assert check(t3, refs=True)["P3"] == (False, "2 terms; not used in the note: Meta-analysis"), check(t3, refs=True)

    # v0.3 iv) the counter-metric, report only: prose words and words P2 read per section (a heading, or a short
    # label other than a mail prefix); "empty" under half read; never an item, so never part of pass or fail
    why = ("## Needs you today\n\n- Re: Budget, from Kim\n- Why: “Please send the budget by Friday, or the board "
           "meets without it.”\n- Move: Do, see https://example.org\n- Why: due Friday.\n")
    assert counter(why) == {"Needs you today": [4, 4], "Why": [14, 2], "Move": [2, 2]}, counter(why)
    dated = "## Can wait\n\nSave the date: offsite, from Kim O’Hara. Come back in May.\n"  # curly; the case has straight
    assert list(counter(dated)) == ["Save the date"]  # without --source a copied subject reads as a label
    assert counter(dated, mask=copied(pasted.replace("Re: RSVPs for the CFO dinner", "Save the date: offsite"))) == {
        "Can wait": [11, 7]}, counter(dated, mask=copied(pasted.replace("Re: RSVPs for the CFO dinner", "Save the date: offsite")))
    assert counter_lines(why, True)[0] == "P2 counter-metric (report only): pass, empty in Why (2 of 14 words read)"
    assert set(check(why)) == {"P1", "P2", "P3"} and set(check(why, refs=True)) == {"P1", "P2", "P3", "P4"}
    print("self-check passed")


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        self_check()
        sys.exit(0)
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__.split("\n\n")[1])
    end = args[args.index("--summary-end") + 1] if "--summary-end" in args else "## Appendix"
    src = open(args[args.index("--source") + 1], encoding="utf-8").read() if "--source" in args else None
    md = open(args[0], encoding="utf-8").read()
    items = check(md, refs="--refs" in args, end=end, transcript="--transcript" in args, source=src)
    for k, (ok, why) in items.items():
        print(f"{k} {'pass' if ok else 'FAIL'}: {why}")
    text = copilot_turns(md) if "--transcript" in args else md
    print("\n".join(counter_lines(text, items["P2"][0], end, copied(src) if src else None)))
    sys.exit(0 if all(ok for ok, _ in items.values()) else 1)
