#!/usr/bin/env python3
"""Derive output.md from raw.html, the HTML that Copilot's Copy button puts on the clipboard.

    python3 evals/inbox-triage/derive.py rounds/rNN/raw.html > rounds/rNN/output.md
    python3 evals/inbox-triage/derive.py rounds/rNN/raw.html --after "<last line of the pasted case>" [--until "Sources"]
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
"""
import sys
from html.parser import HTMLParser

BLOCK = {"p", "h1", "h2", "h3", "h4", "li", "div", "tr", "table", "ul", "ol", "pre"}


class Md(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.row, self.cell, self.head_done, self.skip = [], None, None, False, 0

    def handle_starttag(self, tag, attrs):
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
            self.out.append("\n- ")

    def handle_endtag(self, tag):
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


def derive(html):
    p = Md()
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
    print("self-check passed")


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-check"]:
        self_check()
    elif len(sys.argv) in (2, 4, 6) and sys.argv[2:3] in ([], ["--after"]):
        text = derive(open(sys.argv[1], encoding="utf-8").read())
        if len(sys.argv) >= 4:
            i = text.rfind(sys.argv[3])
            if i < 0:
                sys.exit(f"marker not found: {sys.argv[3]!r}")
            text = text[i + len(sys.argv[3]):].lstrip()
        if len(sys.argv) == 6 and sys.argv[4] == "--until":
            j = text.find(sys.argv[5])  # chat chrome after the answer (Sources, suggestion chips)
            text = text[:j].rstrip() + "\n" if j >= 0 else text
        sys.stdout.write(text)
    else:
        sys.exit(__doc__)
