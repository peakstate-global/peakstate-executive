#!/usr/bin/env python3
"""Derive output.md from raw.html, the HTML that Copilot's Copy button puts on the clipboard.

    python3 evals/inbox-triage/derive.py rounds/rNN/raw.html > rounds/rNN/output.md
    python3 evals/inbox-triage/derive.py rounds/rNN/raw.html --after "<last line of the pasted case>" [--until "Sources"]
    python3 evals/inbox-triage/derive.py rounds/rNN/raw.html --keep-structure > rounds/rNN/output.md
    python3 evals/inbox-triage/derive.py --self-check

--after keeps only the text after the last match of the marker; an optional --until "<marker>"
after it cuts the chat chrome that follows the answer. Use it when the capture is a
select-all of the whole chat (the prompt and case included), because the answer had no Copy button.

Why HTML: the Copilot pane in Outlook on the web is a cross-origin iframe, so Chrome's page text
does not reach it. The Copy button gives two flavours. The plain-text flavour (raw.txt) loses
the table's header line break and flattens any part Copilot's renderer read as maths. The HTML
flavour keeps both, so output.md comes from it, by this script only, never by hand.
Tables become pipe rows (a pipe inside a cell is escaped), <br> and block ends become line breaks,
and every other tag is dropped. Text inside a renderer error span is kept verbatim.

--keep-structure (17 November 2026, for the R&D checker v5): an ordered-list item becomes "1. ",
"2. " and so on (from the list's start attribute), and <b> or <strong> outside a table cell and a heading becomes
** marks, so the numbered References and the bold summary labels reach the scorer. Without the flag the output is
unchanged, so every earlier output.md still derives byte for byte. Later fix: a list item whose content is a
<p> (Copilot writes "<li>\n<p>entry</p>") keeps its marker on the line of the first paragraph, not on a line of its own.
"""
import sys
from html.parser import HTMLParser

BLOCK = {"p", "h1", "h2", "h3", "h4", "li", "div", "tr", "table", "ul", "ol", "pre"}


class Md(HTMLParser):
    def __init__(self, keep_structure=False):
        super().__init__(convert_charrefs=True)
        self.out, self.row, self.cell, self.head_done, self.skip = [], None, None, False, 0
        self.keep, self.lists, self.heading = keep_structure, [], 0  # --keep-structure: list counters, heading depth
        self.marker = False  # --keep-structure: a list marker was just written, its item's text not yet reached

    def _keep_bold(self, tag):
        """--keep-structure: <b> and <strong> outside a table cell and a heading become ** marks."""
        if self.keep and tag in ("b", "strong") and self.cell is None and self.row is None and not self.skip and not self.heading:
            self.out.append("**")
            return True

    def handle_starttag(self, tag, attrs):
        if self._keep_bold(tag):
            return
        if self.keep and tag in ("ol", "ul"):
            start = dict(attrs).get("start") or "1"
            self.lists.append(int(start) if tag == "ol" and start.isdigit() else None)
        if self.keep and tag in ("h1", "h2", "h3", "h4"):
            self.heading += 1
        if tag in ("style", "head"):
            self.skip += 1
        elif tag == "tr":
            self.row = []
        elif tag in ("td", "th"):
            self.cell = []
        elif tag == "br":
            (self.cell if self.cell is not None else self.out).append("\n")
        elif tag in ("h1", "h2", "h3", "h4"):
            self.out.append("\n" + "#" * int(tag[1]) + " ")
        elif tag == "li":
            if self.keep and self.lists and self.lists[-1] is not None:
                self.out.append(f"\n{self.lists[-1]}. ")
                self.lists[-1] += 1
            else:
                self.out.append("\n- ")
            self.marker = self.keep

    def handle_endtag(self, tag):
        if self._keep_bold(tag):
            return
        if self.keep and tag in ("ol", "ul") and self.lists:
            self.lists.pop()
        if self.keep and tag in ("h1", "h2", "h3", "h4") and self.heading:
            self.heading -= 1
        if tag in ("style", "head"):
            self.skip -= 1
        elif tag in ("td", "th"):
            self.row.append(" ".join("".join(self.cell).split()).replace("|", "\\|"))
            self.cell = None
        elif tag == "tr":
            self.out.append("\n| " + " | ".join(self.row) + " |")
            if not self.head_done:
                self.out.append("\n|" + "---|" * len(self.row))
                self.head_done = True
            self.row = None
        elif tag == "table":
            self.out.append("\n\n")
            self.head_done = False
        elif tag in BLOCK:
            self.out.append("\n\n")

    def handle_data(self, data):
        if self.skip:
            return
        if self.cell is not None:
            self.cell.append(data)
        elif self.row is None:
            if self.marker:  # in "<li>\n<p>entry", the marker and the entry share one line
                data = data.lstrip()
                if not data:
                    return
                self.marker = False
            if self.out and self.out[-1] == "\n" and data.startswith("\n"):
                data = data[1:]  # "<br>\n" is one line break, not two
            self.out.append(data)

    def text(self):
        lines = [l.rstrip() for l in "".join(self.out).splitlines()]
        res = []
        for l in lines:
            if l or (res and res[-1]):
                res.append(l)
        return "\n".join(res).strip() + "\n"


def derive(html, keep_structure=False):
    p = Md(keep_structure)
    p.feed(html)
    return p.text()


def self_check():
    h = ('<html><head><style>a{}</style></head><body><p>Intro.</p><h2>A. Triage</h2>\n\n'
         '<table><thead><tr><th>Subject</th><th>Move</th><th>Why</th></tr></thead><tbody>'
         '<tr><td>S: a|b</td><td>do</td><td>Due <b>Fri</b></td></tr></tbody></table>'
         '<p>Draft: S: a<br>\nTo: Pat</p><p>Hi Pat,</p><span class="katex-error">x]  \nThanks  \nA</span></body></html>')
    got = derive(h)
    want = ("Intro.\n\n## A. Triage\n\n| Subject | Move | Why |\n|---|---|---|\n| S: a\\|b | do | Due Fri |\n\n"
            "Draft: S: a\nTo: Pat\n\nHi Pat,\n\nx]\nThanks\nA\n")
    assert got == want, repr(got)
    assert derive(h, keep_structure=True) == want  # nothing to keep: no list, no bold outside the table
    k = ('<h2><strong>References</strong></h2><p><strong>Point 1: Weak.</strong> Evidence. [1]</p>'
         '<ol><li>First, A. (2020). <em>T</em>.</li><li>Second.</li></ol><ul><li>bullet <b>bold</b></li></ul>'
         '<ol start="3"><li>Third.</li></ol><table><tr><th>A</th></tr><tr><td><b>c</b></td></tr></table>')
    assert derive(k, keep_structure=True) == (
        "## References\n\n**Point 1: Weak.** Evidence. [1]\n\n1. First, A. (2020). T.\n\n2. Second.\n\n"
        "- bullet **bold**\n\n3. Third.\n\n| A |\n|---|\n| c |\n"), repr(derive(k, keep_structure=True))
    assert derive(k) == ("## References\n\nPoint 1: Weak. Evidence. [1]\n\n- First, A. (2020). T.\n\n- Second.\n\n"
                         "- bullet bold\n\n- Third.\n\n| A |\n|---|\n| c |\n"), repr(derive(k))
    # Copilot wraps each list item in <p>; the number shares a line with the first paragraph
    lp = '<ol>\n<li>\n<p>First, A. (2020). T.</p>\n<p>More.</p>\n</li>\n<li><p>Second.</p></li>\n</ol><ul>\n<li>\n<p>b</p></li></ul>'
    assert derive(lp, keep_structure=True) == "1. First, A. (2020). T.\n\nMore.\n\n2. Second.\n\n- b\n", repr(derive(lp, True))
    assert derive(lp) == "-\nFirst, A. (2020). T.\n\nMore.\n\n- Second.\n\n-\nb\n", repr(derive(lp))  # default unchanged
    print("self-check passed (default, and --keep-structure: numbered ordered lists, bold outside tables and headings, "
          "<li><p> items on one line)")


if __name__ == "__main__":
    a = sys.argv[1:]
    keep = "--keep-structure" in a
    if keep:
        a.remove("--keep-structure")
    if a == ["--self-check"]:
        self_check()
    elif len(a) in (1, 3, 5) and a[1:2] in ([], ["--after"]):
        text = derive(open(a[0], encoding="utf-8").read(), keep)
        if len(a) >= 3:
            i = text.rfind(a[2])
            if i < 0:
                sys.exit(f"marker not found: {a[2]!r}")
            text = text[i + len(a[2]):].lstrip()
        if len(a) == 5 and a[3] == "--until":
            j = text.find(a[4])  # chat chrome after the answer (Sources, suggestion chips)
            text = text[:j].rstrip() + "\n" if j >= 0 else text
        sys.stdout.write(text)
    else:
        sys.exit(__doc__)
