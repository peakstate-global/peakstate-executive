#!/usr/bin/env python3
"""Holdout v5 heading-to-contents check on an answer document (ticket 46). Runs beside ruler v3.1; score_forum.py is
unchanged. Every `Paper <n>` heading (found the way ruler v3.1 finds headings) must name a paper on the pack's contents
page (read from pack.pdf), and any text after the number must equal that paper's contents title after case,
punctuation and whitespace are normalised. A heading with the number only passes. Exit 0 pass, 1 fail.

    python3 evals/forum-prep/holdout-v5/heading_check.py <run dir | raw.html | output.md>
"""
import importlib.util, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import score_forum as sf  # noqa: E402

sf.load(os.path.join(HERE, "answer-key-holdout-v5.json"))
_spec = importlib.util.spec_from_file_location("hv5_build", os.path.join(HERE, "build.py"))
_b = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_b)


def norm(s):
    return " ".join(re.sub(r"[^\w]+", " ", s.casefold()).split())


def contents_titles():
    """{paper number: title} from the pack's contents page (appendices and glossary are not papers)."""
    return {i: t for i, t, _ in _b.contents_rows() if isinstance(i, int)}


def problems(text, titles=None):
    titles = titles or contents_titles()
    out = []
    for line in text.splitlines():
        h = sf.heading_of(line)
        m = re.match(r"paper\s+(\d+)\b(.*)", h or "", re.I | re.S)
        if not m:
            continue
        n, rest = int(m.group(1)), norm(m.group(2))
        if n not in titles:
            out.append(f"{line.strip()!r}: Paper {n} is not on the contents page")
        elif rest and rest != norm(titles[n]):
            out.append(f"{line.strip()!r}: title differs from the contents page ({titles[n]!r})")
    return out


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    p = sys.argv[1]
    if not p.endswith(".md"):
        from derive import derive_run
        p = derive_run(p)
    bad = problems(open(p, encoding="utf-8").read())
    print("heading check FAILED:\n" + "\n".join(bad) if bad else "heading check passed")
    sys.exit(1 if bad else 0)
