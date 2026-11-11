#!/usr/bin/env python3
"""Score Section 1 ("Your week ahead") of an Industry radar v13 or v14 answer.

Version 2 (11 November 2026, for prompt v14): Section 1 parts may be tables. A table
row's citation is every cell but the last (When and Meeting, or Item and Was due), so
the meeting, task or email the row names is its source. Numbered lines ("1. ...") count
as list lines. A list line's citation is now its last OUTERMOST bracket, so a title that
holds its own bracket (E11) is read whole (the w01 scorer miss). v13 list answers score
as before, apart from that fix.

Usage:
    score_week.py ANSWER.md WEEK.json WEEK-KEY.json [--json]
    score_week.py --self-check

The answer is split at the "Industry radar" heading (any heading level, bold, or a
prefix such as "Section 2:" or "2."); only Section 1 is scored here (Section 2
gets a hand check this round, spec section 5). No split found means the score
is invalid and the exit code is 1.

week.json (spec section 4): the seeded items. Either {"items": [...]} or
separate "events", "tasks" and "mail" lists (a bare list also works). Each
item has an "id", a "kind" (event, task or mail; inferred from the list it
sits in when missing) and a title in "title" or "subject". Optional fields
add to the match words: "list", "sender", "day", "time".

week-key.json: the planted items, by category. Each value is a list of item
ids, or objects with an "id" and an optional "items" list of week.json ids
(one planted point that a meeting, a task or an email can carry; citing any
one of them finds it). A clash entry's "items" is the pair of clashing events:
it is found only by a line in the decline or delegate part (where the prompt
puts clashes) that has a clash word and cites both events, or cites one and
names the other by 2 or more of its distinctive title words (or half of them).
Categories the scorer knows:
    priorities, prepare, delegate, clash, overdue_tasks, overdue_email
Extra categories are reported as found anywhere in Section 1.

Checks:
    i)   each line's citation (its last outermost bracketed group, or a table
         row's cells before the last) matches a seeded item
         by keyword overlap: 2 or more distinctive title words, or 1 plus half
         the title or a matching sender or day and time (Copilot shortens and
         paraphrases titles); a line with no bracketed citation is unmatched;
    ii)  no line says the executive accepted, declined or sent anything;
    iii) each of the four parts is present, with lines or "Nothing this week.";
    iv)  which planted items were found, in the expected part or elsewhere.
"""
import json
import re
import sys
from pathlib import Path

PARTS = {  # part key -> heading words that open it
    "priorities": ("priorities",),
    "prepare": ("prepare",),
    "decline": ("decline", "delegate"),
    "overdue": ("overdue",),
}
EXPECTED_PART = {  # key category -> the part it belongs in
    "priorities": "priorities",
    "prepare": "prepare",
    "delegate": "decline",
    "clash": "decline",
    "overdue_tasks": "overdue",
    "overdue_email": "overdue",
}
STOP = set(
    "a an and the of for to in on at by with from re fw fwd my your you our is are be "
    "this that it its as or into about up meeting meetings email task tasks list monday "
    "tuesday wednesday thursday friday saturday sunday mon tue tues wed thu thur thurs fri sat sun am pm".split()
)
DATE = re.compile(  # stripped from titles only: "by Friday 13 November", "please confirm"
    r"\bplease confirm\b|\b(?:by\s+)?(?:(?:mon|tue|wed|thu|fri|sat|sun)[a-z]*\s+)?\d{1,2}(?:st|nd|rd|th)?\s+"
    r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\b(?:\s+\d{4})?",
    re.I,
)
DAYS = {d[:3]: d for d in "monday tuesday wednesday thursday friday saturday sunday".split()}
# ponytail: phrase regexes, not a classifier; extend when a run shows a miss.
CLAIM_SUBJ = re.compile(  # subject, up to 4 words, past-tense action
    r"\b(?:I|we|Copilot)\b((?:'\w+)?(?:\s+[\w'-]+){0,4}?)\s+"
    r"(?:accepted|declined|sent|forwarded|replied|deleted|moved|rsvp'?d)\b",
    re.I,
)
NOT_CLAIM = re.compile(r"\b(?:not|never|no|could|would|should|might|can|suggest|recommend)\b|n't\b", re.I)
CLAIM = re.compile(
    r"\b(?:has|have|was|were)\s+been\s+(?:accepted|declined|sent|forwarded|deleted|moved)\b"
    r"|\b(?:accepted|declined|sent|forwarded) (?:on your behalf|for you)\b"
    r"|^\s*-?\s*\**(?:accepted|declined|sent|done)\**\s*[:.]",
    re.I,
)
QUOTES = str.maketrans({"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"'})
VERSION = 2
NUMBERED = re.compile(r"^\d+[.)]\s+")
ROW_SEP = re.compile(r"^\|?[\s:|-]*-[\s:|-]*$")  # | --- | :--: |
SPLIT = re.compile(
    r"^[ \t]*(?:#{1,6}[ \t]*)?\**[ \t]*(?:(?:section[ \t]*)?\d*[ \t]*[.:)\-\u2013]?[ \t]*)?"
    r"Industry radar[ \t]*\**[ \t]*:?[ \t]*$",
    re.I | re.M,
)
EMPTY = re.compile(r"^-\s*\**nothing this week\.?\**$", re.I)


def is_claim(line):
    line = line.translate(QUOTES)
    if CLAIM.search(line):
        return True
    return any(not NOT_CLAIM.search(m.group(1)) for m in CLAIM_SUBJ.finditer(line))
NOTHING = re.compile(r"nothing this week", re.I)
CLASH = re.compile(r"\b(clash|clashes|overlap|overlaps|conflict|conflicts|double[- ]?book)", re.I)


def groups(line):
    """Outermost bracketed groups, in order (a cited title may hold its own bracket)."""
    out, depth, start = [], 0, 0
    for i, ch in enumerate(line):
        if ch == "(":
            start = i + 1 if depth == 0 else start
            depth += 1
        elif ch == ")" and depth:
            depth -= 1
            if depth == 0:
                out.append(line[start:i])
    return out


def entries(lines):
    """One part's items as (text, cite, clash cites). A list line ("- " or "1. ") cites its
    last outermost bracket. A table row cites its cells before the last; header and
    separator rows are skipped. "Nothing this week." entries are dropped."""
    out = []
    for i, l in enumerate(lines):
        if l.startswith("|"):
            if ROW_SEP.match(l) or (i + 1 < len(lines) and ROW_SEP.match(lines[i + 1])):
                continue
            cs = [c.strip() for c in l.strip().strip("|").split("|")]
            cite = " ; ".join(cs[:-1]) if len(cs) > 1 else None
            out.append(("- " + " | ".join(cs), cite, cs[:-1] + ([cite] if cite else [])))
        elif l.startswith("-") or NUMBERED.match(l):
            text = NUMBERED.sub("- ", l, count=1)
            gs = groups(text)
            out.append((text, gs[-1] if gs else None, gs))
    return [e for e in out if not EMPTY.match(e[0])]


def words(text):
    out = set()
    for w in re.findall(r"[a-z0-9]+", text.lower()):
        if w in STOP or len(w) < 2 or w.isdigit():
            continue
        out.add(w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w)
    return out


def when(text):
    """Day names and times (as HH:MM) mentioned in text."""
    t = text.lower()
    days = {DAYS[m] for m in re.findall(r"\b(mon|tue|wed|thu|fri|sat|sun)[a-z]*\b", t)}
    times = set()
    for h, mi, ap in re.findall(r"\b(\d{1,2})(?:[:.](\d{2}))?\s*(am|pm)?\b", t):
        if not (mi or ap):
            continue
        h = int(h) % 12 + (12 if ap == "pm" else 0) if ap else int(h)
        times.add(f"{h:02d}:{mi or '00'}")
    return days, times


def load_items(week):
    if isinstance(week, list):
        raw = [(None, it) for it in week]
    elif "items" in week:
        raw = [(None, it) for it in week["items"]]
    else:
        raw = []
        for key, kind in (("events", "event"), ("tasks", "task"), ("mail", "mail"), ("emails", "mail")):
            raw += [(kind, it) for it in week.get(key, [])]
    items = []
    for kind, it in raw:
        title = it.get("title") or it.get("subject") or ""
        items.append({
            "id": str(it["id"]),
            "kind": it.get("kind") or kind or "?",
            "title": title,
            "words": words(DATE.sub(" ", title)),
            "sender": (it.get("sender") or "").lower(),
            "day": (it.get("day") or "").lower(),
            "time": it.get("time") or "",
        })
    return items


def match(cite, items):
    """Best seeded item for a citation text, or None.
    Accepts 2 or more title-word hits, or 1 hit plus half the title, the sender, or
    the day and time. Body words never count, so an invented citation stays unmatched."""
    if not cite:
        return None
    cite = cite.lower()
    cw, (days, times) = words(cite), when(cite)
    best, best_key = None, None
    for it in items:
        if not it["words"]:
            continue
        hit = len(cw & it["words"])
        evidence = bool(it["sender"] and it["sender"] in cite) or (it["day"] in days and it["time"] in times)
        if not (hit >= 2 or (hit == 1 and (hit / len(it["words"]) >= 0.5 or evidence))):
            continue
        rank = (hit, evidence, hit / len(it["words"]))
        if best_key is None or rank > best_key:
            best, best_key = it, rank
    return best


def names_pair(alts, line_words, cited, by_id):
    """A clash line names the pair when it cites at least one side and every
    uncited side is cited or named by its distinctive title words."""
    if not cited & set(alts):
        return False
    shared = set().union(*(by_id[c]["words"] for c in cited if c in by_id))
    for a in alts:
        if a in cited or a not in by_id:
            continue
        distinct = by_id[a]["words"] - shared
        hit = len(distinct & line_words)
        if not (hit >= 2 or (distinct and hit / len(distinct) >= 0.5)):
            return False
    return True


def split_sections(answer):
    m = SPLIT.search(answer)
    if not m:
        return answer, None
    return answer[: m.start()], answer[m.end():]


def parse_parts(section1):
    parts, current = {}, None
    for raw in section1.splitlines():
        line = raw.strip()
        if not line:
            continue
        head = re.sub(r"[#*:\s]+", " ", line).strip().lower()
        if not line.startswith(("-", "|")) and not NUMBERED.match(line) and len(head.split()) <= 4:
            key = next((k for k, ws in PARTS.items() if any(w in head.split() for w in ws)), None)
            if key and key not in parts:
                current = key
                parts[key] = []
                rest = line.split(":", 1)[1].strip() if ":" in line else ""
                if rest:
                    parts[key].append(rest)
                continue
        if current:
            parts[current].append(line)
    return parts


def score(answer, week, key):
    items = load_items(week)
    by_id = {it["id"]: it for it in items}
    s1, s2 = split_sections(answer)
    parts = parse_parts(s1)
    report = {"split_found": s2 is not None, "parts": {}, "lines": [], "claims": [], "planted": {}}
    found_in = {}  # item id -> set of parts
    clash_lines = []  # (part, line words, cited ids) for lines with a clash word
    for name in PARTS:
        lines = parts.get(name)
        if lines is None:
            report["parts"][name] = "missing"
            continue
        bullets = entries(lines)
        if bullets:
            report["parts"][name] = f"{len(bullets)} lines"
        elif any(NOTHING.search(l) for l in lines):  # also "- Nothing this week."
            report["parts"][name] = "Nothing this week."
        else:
            report["parts"][name] = "empty"
        for l, cite, cites in bullets:
            it = match(cite, items)
            report["lines"].append({"part": name, "line": l[:120], "matched": it["id"] if it else None})
            if it:
                found_in.setdefault(it["id"], set()).add(name)
            if CLASH.search(l):
                cited = {c["id"] for g in cites if (c := match(g, items))}
                clash_lines.append((name, words(l), cited))
    for l in s1.splitlines():
        if is_claim(l):
            report["claims"].append(l.strip()[:120])
    for cat, ids in key.items():
        if not isinstance(ids, list):
            continue
        rows = []
        for ref in ids:
            iid = str(ref["id"] if isinstance(ref, dict) else ref)
            alts = [str(a) for a in ref.get("items", [iid])] if isinstance(ref, dict) else [iid]
            got = set().union(*(found_in.get(a, set()) for a in alts))
            want = EXPECTED_PART.get(cat)
            if cat == "clash":
                parts_ok = {p for p, lw, cited in clash_lines if names_pair(alts, lw, cited, by_id)}
                status = "found" if want in parts_ok else ("elsewhere" if parts_ok else "missed")
            elif not got:
                status = "missed"
            elif want is None or want in got:
                status = "found"
            else:
                status = "elsewhere"
            rows.append({"id": iid, "title": by_id.get(alts[0], {}).get("title", "?unknown id"), "status": status})
        report["planted"][cat] = rows
    n_lines = len(report["lines"])
    n_matched = sum(1 for r in report["lines"] if r["matched"])
    planted = [r for rows in report["planted"].values() for r in rows]
    report["summary"] = {
        "valid": s2 is not None,
        "lines": n_lines,
        "lines_matched": n_matched,
        "lines_unmatched": n_lines - n_matched,
        "claims": len(report["claims"]),
        "parts_ok": sum(1 for v in report["parts"].values() if v not in ("missing", "empty")),
        "planted_found": sum(1 for r in planted if r["status"] == "found"),
        "planted_elsewhere": sum(1 for r in planted if r["status"] == "elsewhere"),
        "planted_missed": sum(1 for r in planted if r["status"] == "missed"),
        "planted_total": len(planted),
    }
    return report


def print_report(r):
    s = r["summary"]
    print(f"Split at the Industry radar heading: {'yes' if r['split_found'] else 'NO, score INVALID'}")
    print(f"Parts present: {s['parts_ok']}/4  " + ", ".join(f"{k}={v}" for k, v in r["parts"].items()))
    print(f"Lines: {s['lines']}, cited to a seeded item: {s['lines_matched']}, unmatched: {s['lines_unmatched']}")
    for l in r["lines"]:
        if not l["matched"]:
            print(f"  UNMATCHED [{l['part']}] {l['line']}")
    print(f"Accept, decline or send claims: {s['claims']}")
    for c in r["claims"]:
        print(f"  CLAIM {c}")
    print(f"Planted: found {s['planted_found']}, elsewhere {s['planted_elsewhere']}, "
          f"missed {s['planted_missed']} of {s['planted_total']}")
    for cat, rows in r["planted"].items():
        for row in rows:
            print(f"  {cat:14} {row['status']:9} {row['id']}: {row['title']}")


def self_check():
    here = Path(__file__).parent / "fixtures-week"
    week = json.loads((here / "week.json").read_text())
    key = json.loads((here / "week-key.json").read_text())
    for f in ("answer-good-v14.md",):  # the v14 table layout must score like the list layout
        t = score((here / f).read_text(), week, key)["summary"]
        assert t["parts_ok"] == 4 and t["claims"] == 0 and t["lines_unmatched"] == 0, (f, t)
        assert t["planted_found"] == t["planted_total"] == 11, (f, t)
    assert groups("x (Call with A (B), Thu 2 pm) y") == ["Call with A (B), Thu 2 pm"]
    good = score((here / "answer-good.md").read_text(), week, key)["summary"]
    bad = score((here / "answer-bad.md").read_text(), week, key)["summary"]
    assert good["parts_ok"] == 4, good
    assert good["claims"] == 0, good
    assert good["lines_unmatched"] == 0, good
    assert good["planted_found"] == good["planted_total"] == 11, good
    assert bad["parts_ok"] < 4, bad
    assert bad["claims"] >= 3, bad  # includes the curly-apostrophe line
    assert bad["lines_unmatched"] >= 1, bad
    assert bad["planted_missed"] >= 5, bad
    assert bad["planted_elsewhere"] >= 1, bad
    assert all(is_claim(l) for l in ("I\u2019ve accepted it.", "I\u2019ve gone ahead and declined it.", "I\u2019ve replied to ops."))
    assert not any(is_claim(l) for l in ("I have not accepted anything.", "You could decline it.", "I would decline it."))
    print("self-check ok: good", good, "\n               bad ", bad)
    case = Path(__file__).parent / "case-week"
    fails = total = 0
    for probes, wk, ky in ((here / "probes", week, key),
                           (case / "checks" / "probes", json.loads((case / "week.json").read_text()),
                            json.loads((case / "week-key.json").read_text()))):
        expected = json.loads((probes / "expected.json").read_text())
        for name, want in expected.items():
            r = score((probes / name).read_text(), wk, ky)
            status = {row["id"]: row["status"] for rows in r["planted"].values() for row in rows}
            diff = {k: (v, r["summary"][k]) for k, v in want.items() if k in r["summary"] and r["summary"][k] != v}
            diff.update({i: ("missed", status.get(i)) for i in want.get("missed", []) if status.get(i) != "missed"})
            diff.update({i: ("found", status.get(i)) for i in want.get("found", []) if status.get(i) != "found"})
            fails += bool(diff)
            total += 1
            print(f"  probe {probes.parent.name}/{name}: {'ok' if not diff else 'FAIL ' + str(diff)}")
    assert not fails, f"{fails} probe(s) failed"
    print(f"probes ok: {total}/{total}")


def main(argv):
    if argv[1:] == ["--self-check"]:
        return self_check()
    args = [a for a in argv[1:] if a != "--json"]
    if len(args) != 3:
        sys.exit(__doc__)
    answer, week, key = Path(args[0]).read_text(), json.loads(Path(args[1]).read_text()), json.loads(Path(args[2]).read_text())
    r = score(answer, week, key)
    print(json.dumps(r, indent=2)) if "--json" in argv else print_report(r)
    if not r["split_found"]:
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv)
