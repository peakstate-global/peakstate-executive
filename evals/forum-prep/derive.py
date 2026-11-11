#!/usr/bin/env python3
"""Derive a forum run's output.md from its raw.html (ruler v3). Scorers read output.md, never raw.txt.

    python3 evals/forum-prep/derive.py <run dir | raw.html>   # writes output.md beside raw.html, prints its path
    python3 evals/forum-prep/derive.py --self-check

Method: inbox/derive.py (h1 to h4 become # marks, li becomes "- ", table rows kept), plus one change: <b> and
<strong> outside a table become ** marks, so a whole line in bold reaches the scorer as a heading candidate
(as rnd/score_rnd.py accepts). output.md is made by this script only and is never edited by hand.

Ruler v3.2 (10 November 2026, ticket 65): output.md has its curly apostrophes and quotes converted to straight ones
(straighten below; score_forum.py applies the same function to any text it scores). An output.md derived before ruler
v3.2 keeps its curly characters; it is not re-derived or re-scored, and its scores are not comparable with ruler v3.2.
"""
import importlib.util, os, sys

# Load inbox/derive.py by path: a plain "from derive import" finds this file when exec-skills/forum is on sys.path.
_spec = importlib.util.spec_from_file_location("inbox_derive", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "inbox-triage", "derive.py"))
_inbox = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_inbox)
Md = _inbox.Md

# Ruler v3.2: curly apostrophes and quotes (and their look-alikes) to straight ones.
_STRAIGHT = str.maketrans({c: "'" for c in "\u2018\u2019\u201a\u201b\u2032\u02bc\uff07"} |
                          {c: '"' for c in "\u201c\u201d\u201e\u201f\u2033\uff02"})


def straighten(text):
    """Ruler v3.2: convert curly apostrophes and quotes to straight ones, so key patterns match what Copilot writes."""
    return text.translate(_STRAIGHT)


class ForumMd(Md):
    def _bold(self, tag):
        if tag in ("b", "strong") and self.cell is None and self.row is None and not self.skip:
            self.out.append("**")
            return True

    def handle_starttag(self, tag, attrs):
        if not self._bold(tag):
            super().handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if not self._bold(tag):
            super().handle_endtag(tag)


def derive(html):
    p = ForumMd()
    p.feed(html)
    return straighten(p.text())  # ruler v3.2


def derive_run(path):
    """Write output.md beside raw.html (path is the run folder or the raw.html) and return its path."""
    raw = os.path.join(path, "raw.html") if os.path.isdir(path) else path
    out = os.path.join(os.path.dirname(raw), "output.md")
    text = derive(open(raw, encoding="utf-8").read())
    open(out, "w", encoding="utf-8").write(text)
    return out


def self_check():
    h = ("<h2>Before the meeting</h2><h3>Warnings</h3><p>None found.</p>"
         "<p><strong>Paper 1: Award</strong></p><p>Fact <b>here</b> (p. 4: \"x\").</p>"
         "<table><tr><th>A</th></tr><tr><td><b>c</b></td></tr></table>")
    want = ("## Before the meeting\n\n### Warnings\n\nNone found.\n\n**Paper 1: Award**\n\n"
            "Fact **here** (p. 4: \"x\").\n\n| A |\n|---|\n| c |\n")
    got = derive(h)
    assert got == want, repr(got)
    got = derive("<p>The regulator hasn\u2019t approved it (p. 17: \u201cnot approved\u201d).</p>")
    assert got == "The regulator hasn't approved it (p. 17: \"not approved\").\n", repr(got)
    print("derive self-check passed: h2/h3 marks, whole bold line kept as **, inline bold, table cell bold dropped; "
          "ruler v3.2: curly apostrophes and quotes straightened")


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-check"]:
        self_check()
    elif len(sys.argv) == 2:
        print(derive_run(sys.argv[1]))
    else:
        sys.exit(__doc__)
