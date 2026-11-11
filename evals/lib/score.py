#!/usr/bin/env python3
"""Score one round's output.md against an answer key. Fails closed.

    python3 evals/lib/score.py <output.md> <answer-key.json> [--round rNN]
    python3 evals/lib/score.py --self-check

Answer key shape:
    {"match_column": "Subject",
     "columns": ["Subject", "Move", "Why"],          # exact header, in order
     "values": {"Move": ["delete", "delegate", "defer", "do"]},   # allowed values (case-insensitive)
     "items": [{"key": "Sample: ...", "expect": {"Move": "do"}, "critical": true}]}
    Optional (tier 2): "nonempty": ["Why"] fails the round on an empty cell in those columns;
    "min_precision_recall": 0.8 makes pass = no critical error and every value's precision and recall
    at least 0.8 (a value with no key item and no row is skipped; a value with key items
    and no row has recall 0, and a value with rows and no key item has precision 0). Without it, pass = every row right.

Exit 0 with score JSON on stdout when the table parses cleanly (the JSON says pass or fail on content).
Exit 2 with the reason when the table is malformed: missing, duplicate or unknown row, renamed
column, unexpected value, wrong cell count, no table or more than one table. No row is ever dropped.
"""
import json, re, sys


class Malformed(Exception):
    pass


def split_row(line):
    """Split a markdown table row on pipes, ignoring pipes inside backticks or escaped as \\|."""
    s = line.strip()
    if not (s.startswith("|") and s.endswith("|")) or len(s) < 2:
        raise Malformed(f"row does not start and end with a pipe: {line!r}")
    cells, cur, tick, i = [], "", False, 1
    while i < len(s) - 1:
        c = s[i]
        if c == "\\" and i + 1 < len(s) - 1:
            cur += s[i:i + 2]; i += 2; continue
        if c == "`":
            tick = not tick
        if c == "|" and not tick:
            cells.append(cur); cur = ""
        else:
            cur += c
        i += 1
    if tick:
        raise Malformed(f"unclosed backtick in row: {line!r}")
    cells.append(cur)
    return [clean(x) for x in cells]


def clean(cell):
    cell = re.sub(r"<br\s*/?>", " ", cell, flags=re.I)
    cell = re.sub(r"\\([\\`*_{}\[\]()#+\-.!|<>~])", r"\1", cell)
    return " ".join(cell.split())


def norm(v):
    return v.strip("`*_ ").casefold()


def tables(text):
    blocks, cur = [], []
    for line in text.splitlines():
        if line.strip().startswith("|"):
            cur.append(line)
        elif cur:
            blocks.append(cur); cur = []
    if cur:
        blocks.append(cur)
    return blocks


def parse(text, key):
    blocks = tables(text)
    if len(blocks) != 1:
        raise Malformed(f"expected exactly one table, found {len(blocks)}")
    lines = blocks[0]
    if len(lines) < 2:
        raise Malformed("table has no separator row")
    header = split_row(lines[0])
    if header != key["columns"]:
        raise Malformed(f"header {header} does not equal key columns {key['columns']}")
    sep = split_row(lines[1])
    if len(sep) != len(header) or not all(re.fullmatch(r":?-{3,}:?", c) for c in sep):
        raise Malformed(f"bad separator row: {lines[1]!r}")
    rows = []
    for line in lines[2:]:
        cells = split_row(line)
        if len(cells) != len(header):
            raise Malformed(f"row has {len(cells)} cells, header has {len(header)}: {line!r}")
        rows.append(dict(zip(header, cells)))
    return rows


def validate_key(key):
    """Every column the answer key references must be in key['columns'] (and so in the header)."""
    cols = set(key["columns"])
    refs = {key["match_column"]} | set(key.get("values", {})) | \
        {c for item in key["items"] for c in item["expect"]}
    unknown = refs - cols
    if unknown:
        raise Malformed(f"answer key references column(s) not in columns: {sorted(unknown)}")


def score(text, key):
    validate_key(key)
    rows = parse(text, key)
    mc = key["match_column"]
    items = {k["key"]: k for k in key["items"]}
    seen = {}
    for r in rows:
        k = r[mc]
        if k in seen:
            raise Malformed(f"duplicate row: {k!r}")
        if k not in items:
            raise Malformed(f"unknown row: {k!r}")
        for col, allowed in key.get("values", {}).items():
            if norm(r[col]) not in {a.casefold() for a in allowed}:
                raise Malformed(f"unexpected {col} value {r[col]!r} in row {k!r}")
        for col in key.get("nonempty", []):  # tier 2: every item keeps its move and why line
            if not r[col].strip("*_` "):
                raise Malformed(f"empty {col} cell in row {k!r}")
        seen[k] = r
    missing = [k for k in items if k not in seen]
    if missing:
        raise Malformed(f"missing row(s): {missing}")

    wrong, critical = [], []
    for k, item in items.items():
        bad = {c: {"want": v, "got": seen[k][c]} for c, v in item["expect"].items() if norm(seen[k][c]) != v.casefold()}
        if bad:
            wrong.append({"key": k, "errors": bad})
            if item.get("critical"):
                critical.append(k)

    pr = {}  # per-value precision and recall for each constrained column
    for col, allowed in key.get("values", {}).items():
        for v in allowed:
            want = {k for k, i in items.items() if i["expect"].get(col, "").casefold() == v.casefold()}
            got = {k for k in items if norm(seen[k][col]) == v.casefold()}
            tp = len(want & got)
            pr[f"{col}={v}"] = {"precision": round(tp / len(got), 3) if got else None,
                                "recall": round(tp / len(want), 3) if want else None}
    if "min_precision_recall" in key:  # tier 2 pass rule: no critical error and every move's P and R >= threshold
        m = key["min_precision_recall"]
        ok = not critical and all(v is None or v >= m for d in pr.values() for v in d.values())
    else:  # tier 1: every row right
        ok = not wrong and not critical
    return {"rows": len(rows), "correct": len(items) - len(wrong), "wrong": wrong,
            "critical_errors": critical, "pass": ok, "precision_recall": pr}


def self_check():
    key = {"match_column": "Subject", "columns": ["Subject", "Move", "Why"],
           "values": {"Move": ["delete", "delegate", "defer", "do"]},
           "items": [{"key": "Sample: deposit", "expect": {"Move": "do"}, "critical": True},
                     {"key": "Sample: `a|b` notes", "expect": {"Move": "defer"}},
                     {"key": "Sample: newsletter", "expect": {"Move": "delete"}}]}
    head = "Intro text.\n\n| Subject | Move | Why |\n|---|:---:|---|\n"
    good = head + ("| Sample: deposit | **Do** | Money<br>due 14 Nov |\n"
                   "| Sample: `a|b` notes | defer | Pipe \\| inside, escaped \\* star |\n"
                   "| Sample: newsletter | delete | Not needed |\n")
    r = score(good, key)
    assert r["pass"] and r["correct"] == 3, r
    assert r["precision_recall"]["Move=do"] == {"precision": 1.0, "recall": 1.0}, r
    assert split_row("| a `x|y` | b\\|c | d<br/>e |") == ["a `x|y`", "b|c", "d e"]

    wrong = good.replace("| **Do** |", "| defer |")
    r = score(wrong, key)
    assert not r["pass"] and r["critical_errors"] == ["Sample: deposit"], r

    bad = {
        "missing row": head + "| Sample: deposit | do | x |\n| Sample: newsletter | delete | x |\n",
        "duplicate row": good + "| Sample: newsletter | delete | again |\n",
        "unknown row": good + "| Sample: other | delete | x |\n",
        "renamed column": good.replace("| Subject | Move | Why |", "| Subject | Action | Why |"),
        "unexpected value": good.replace("| delete | Not", "| archive | Not"),
        "cell count": good.replace("| Not needed |", "| Not | needed |"),
        "no table": "No table here.",
        "two tables": good + "\nMore text.\n\n" + head,
        "unclosed backtick": good.replace("| Sample: newsletter |", "| Sample: `newsletter |"),
        "bad separator": good.replace("|---|:---:|---|", "|---|xx|---|"),
    }
    for name, text in bad.items():
        try:
            score(text, key)
        except Malformed:
            continue
        raise AssertionError(f"self-check: {name} was not rejected")

    # tier 2 key fields: nonempty columns (the counter-metric floor) and a precision/recall pass rule
    k2 = dict(key, nonempty=["Why"], min_precision_recall=0.8)
    assert score(good, k2)["pass"], "tier 2: a perfect table passes"
    try:
        score(good.replace("| Not needed |", "|  |"), k2)
    except Malformed:
        pass
    else:
        raise AssertionError("self-check: an empty Why cell was not rejected under nonempty")
    many = {"match_column": "Subject", "columns": ["Subject", "Move", "Why"], "values": {"Move": ["do", "defer"]},
            "min_precision_recall": 0.8,
            "items": [{"key": f"S{i}", "expect": {"Move": "do" if i < 5 else "defer"}} for i in range(10)]}
    tbl = "| Subject | Move | Why |\n|---|---|---|\n" + "".join(
        f"| S{i} | {'do' if i < 5 else 'defer'} | x |\n" for i in range(10))
    one_off = tbl.replace("| S9 | defer |", "| S9 | do |")  # do precision 5/6 = 0.83, defer recall 4/5 = 0.8
    r = score(one_off, many)
    assert r["pass"] and r["wrong"], f"tier 2: P/R >= 0.8 with one non-critical error passes: {r}"
    two_off = one_off.replace("| S8 | defer |", "| S8 | do |")  # defer recall 3/5 = 0.6
    assert not score(two_off, many)["pass"], "tier 2: a move below 0.8 recall fails"
    crit = dict(many, items=[dict(i, critical=(i["key"] == "S9")) for i in many["items"]])
    assert not score(one_off, crit)["pass"], "tier 2: a critical error fails whatever P/R says"

    bad_key = dict(key, match_column="Status")  # column absent from key["columns"]
    try:
        score(good, bad_key)
    except Malformed:
        pass
    else:
        raise AssertionError("self-check: answer key with unknown match_column was not rejected")

    print(f"self-check passed: 1 good table, 1 critical error, {len(bad)} malformed cases rejected, "
          "1 bad answer-key case rejected")


def main(argv):
    if argv == ["--self-check"]:
        return self_check()
    if len(argv) < 2:
        sys.exit(__doc__)
    rnd = argv[argv.index("--round") + 1] if "--round" in argv else None
    text = open(argv[0], encoding="utf-8").read()
    key = json.load(open(argv[1], encoding="utf-8"))
    try:
        r = score(text, key)
    except Malformed as e:
        print(f"ROUND FAILED (malformed output): {e}", file=sys.stderr)
        sys.exit(2)
    if rnd:
        r["round"] = rnd
    print(json.dumps(r, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
