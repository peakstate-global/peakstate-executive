#!/usr/bin/env python3
"""Score a profile.docx made by the profile prompt against a persona file.

    python3 evals/setup-profile/score_profile.py <profile.docx> --persona evals/setup-profile/case/persona-1.md [--out score.json]
    python3 evals/setup-profile/score_profile.py --self-check

Reads the .docx through pandoc (gfm). Checks (SPEC-redesign section 4):
  F1 (critical) the eight headings are present, once each, in order.
  P1 every persona fact is found in one of its sections (a unit matches every pattern in `all`).
  N1 (critical, ruler v2) every unit after the first fixed heading says Not given, or matches a persona fact
     listed for its section (any fact, under an extra heading) AND every clause of it holds a match of a
     pattern from a fact that matches the whole unit. So extra content in a matched bullet fails.
  S1 every skipped field says Not given.
Pass = F1, P1, N1 and S1. A heading is a Markdown heading or a whole-line bold paragraph (trailing colon
ignored). A unit is a list item, a paragraph or a table row. Text before the first fixed heading (a title)
is listed, not checked. PN (Portfolio is a numbered list) is reported, not part of pass.
"""
import json, re, subprocess, sys

HEADINGS = ["Role", "Portfolio", "Leadership team", "Priorities", "Forums",
            "Industry and peers", "AI tools in use", "How I work"]
NOT_GIVEN = re.compile(r"(?i)^([^:]{1,40}:\s*)?not given\.?$")
ITEM = re.compile(r"^\s*([-*+]|\d+[.)])\s+(.*)$")


def persona(path):
    t = open(path).read()
    return json.loads(re.search(r"```json\n(.*?)\n```", t, re.S).group(1))


def clean(s):
    s = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"\\(.)", r"\1", s)
    s = s.replace("**", "").replace("__", "")
    s = re.sub(r"(?<!\w)[*_]|[*_](?!\w)", "", s)
    return re.sub(r"\s+", " ", s).strip()


def heading(line):
    m = re.match(r"^#{1,6}\s+(.*)$", line) or re.match(r"^\*\*([^*]+)\*\*\s*:?\s*$", line.strip())
    return clean(m.group(1)).rstrip(":").strip() if m else None


def parse(md):
    """Return (pre-heading units, [(heading text, [(kind, unit)])])."""
    pre, sections, cur = [], [], None
    for line in md.splitlines():
        if not line.strip() or re.match(r"^\s*\|?\s*:?-{3,}", line):
            continue
        h = heading(line)
        if h is not None:
            cur = (h, [])
            sections.append(cur)
            continue
        m = ITEM.match(line)
        if m:
            kind, text = ("ol" if m.group(1)[0].isdigit() else "ul"), m.group(2)
        elif line.strip().startswith("|"):
            kind, text = "row", " ".join(c for c in line.strip().strip("|").split("|"))
        else:
            kind, text = "p", line
        text = clean(text)
        if text:
            (cur[1] if cur else pre).append((kind, text))
    return pre, sections


def matches(fact, text):
    return all(re.search(p, text, re.I) for p in fact["all"])


# ruler v2: a clause is a stretch between , ; . ( ) " - " or the words and, or, but, plus.
# ponytail: extra words joined without a separator ("short practical briefs") still pass; word-level check if that shows up.
CLAUSE = re.compile(r"[,;()]|\.(?=\s|$)|\s[-\u2013]\s|\s&\s|\b(?:and|or|but|plus)\b", re.I)


def uncovered(text, facts):
    """Return the first clause no match span of a fully matching fact touches, or None if every clause is covered."""
    hit = [f for f in facts if matches(f, text)]
    if not hit:
        return text
    spans = [m.span() for f in hit for p in f["all"] for m in re.finditer(p, text, re.I)]
    pos = 0
    for m in list(CLAUSE.finditer(text)) + [None]:
        a, b = pos, (m.start() if m else len(text))
        pos = m.end() if m else b
        if not text[a:b].strip(" :.'\""):
            continue
        if not any(x < b and y > a for x, y in spans):
            return text[a:b].strip(" :.")
    return None


def score(md, spec):
    pre, sections = parse(md)
    names = [h for h, _ in sections]
    norm = {h.lower(): h for h in HEADINGS}
    fixed = [norm[n.lower()] for n in names if n.lower() in norm]
    f1 = fixed == HEADINGS
    extra = [n for n in names if n.lower() not in norm]
    first = next((i for i, n in enumerate(names) if n.lower() in norm), len(sections))
    body = sections[first:]
    by = {}
    for h, units in body:
        by.setdefault(h.lower(), []).extend(units)
    facts = spec["facts"]
    found, missed = [], []
    for f in facts:
        ok = any(matches(f, u) for s in f["sections"] for _, u in by.get(s.lower(), []))
        (found if ok else missed).append(f["id"])
    def allowed(h):  # facts for this section; a unit under an extra heading may match any fact
        own = [f for f in facts if h.lower() in (s.lower() for s in f["sections"])]
        return own if h.lower() in norm else facts
    unmatched = []
    for h, units in body:
        for _, u in units:
            c = None if NOT_GIVEN.match(u) else uncovered(u, allowed(h))
            if c is not None:
                unmatched.append({"section": h, "unit": u, "clause": c})
    skip_bad = [s for s in spec["skip"] if not any(NOT_GIVEN.match(u) for _, u in by.get(s.lower(), []))]
    port = by.get("portfolio", [])
    res = {
        "F1": {"pass": f1, "headings_found": names, "extra_headings": extra},
        "P1": {"pass": not missed, "found": found, "missed": missed},
        "N1": {"pass": not unmatched, "units_checked": sum(len(u) for _, u in body), "unmatched": unmatched},
        "S1": {"pass": not skip_bad, "skipped": spec["skip"], "not_saying_not_given": skip_bad},
        "PN_diagnostic": {"numbered": bool(port) and all(k == "ol" for k, _ in port)},
        "before_first_heading": [u for _, u in pre],
    }
    res["critical_fail"] = [k for k in ("F1", "N1") if not res[k]["pass"]]
    res["pass"] = all(res[k]["pass"] for k in ("F1", "P1", "N1", "S1"))
    return res


def docx_md(path):
    return subprocess.run(["pandoc", path, "-t", "gfm", "--wrap=none"], capture_output=True, text=True, check=True).stdout


GOOD = """# Profile

# Role
- Executive General Manager Strategy, Meridian Sample Water.
- Government-owned water utility.

# Portfolio
1. Capital works program
2. Environment licence compliance
3. Long-term asset plan

# Leadership team
- Manager Capital Planning: Capital works program.
- Manager Licence Compliance: Environment licence compliance.
- Manager Asset Planning: Long-term asset plan.

# Priorities
- Keep the capital works program inside its approved funding.
- Meet every condition of the plant environment licences on time.
- Keep the long-term asset plan current with asset condition.

# Forums
- Not given

# Industry and peers
- Water.
- Peers: other regional water utilities.

# AI tools in use
- Not given

# How I work
- Short briefs, one page at most.
- Plain, direct language.
- Avoid jargon.
- Avoid long preambles.
"""


def self_check():
    import os, tempfile
    spec = persona(os.path.join(os.path.dirname(os.path.abspath(__file__)), "case", "persona-1.md"))
    with tempfile.TemporaryDirectory() as d:
        def run(md):
            src, out = os.path.join(d, "p.md"), os.path.join(d, "p.docx")
            open(src, "w").write(md)
            subprocess.run(["pandoc", src, "-o", out], check=True)
            return score(docx_md(out), spec)
        r = run(GOOD)
        assert r["pass"] and r["PN_diagnostic"]["numbered"], r
        assert r["before_first_heading"] == [] and r["F1"]["extra_headings"] == ["Profile"], r
        r = run(GOOD.replace("# Forums", "# Committees"))
        assert not r["F1"]["pass"] and not r["S1"]["pass"] and "F1" in r["critical_fail"], r
        r = run(GOOD.replace("# Role\n", "# Priorities2\n").replace("# Priorities\n", "# Role\n").replace("# Priorities2\n", "# Priorities\n"))
        assert not r["F1"]["pass"], r
        r = run(GOOD.replace("- Water.\n", "- Water.\n- Reports to the Managing Director.\n"))
        assert not r["N1"]["pass"] and r["N1"]["unmatched"][0]["unit"] == "Reports to the Managing Director.", r
        r = run(GOOD.replace("- Avoid jargon.\n", "- Avoid jargon.\n- Capital works program first.\n"))
        assert not r["N1"]["pass"], r
        r = run(GOOD.replace("# AI tools in use\n- Not given", "# AI tools in use\n- Microsoft 365 Copilot"))
        assert not r["S1"]["pass"] and not r["N1"]["pass"], r
        r = run(GOOD.replace("- Peers: other regional water utilities.\n", ""))
        assert r["P1"]["missed"] == ["I2"] and r["N1"]["pass"], r
        r = run(GOOD.replace("**", "").replace("# Leadership team\n", "**Leadership team:**\n\n"))
        assert r["pass"], r
        r = run(GOOD.replace("# Forums\n- Not given", "# Forums\n- Forums: Not given."))
        assert r["S1"]["pass"] and r["N1"]["pass"], r
        # ruler v2: N1 checks each clause of a matched bullet
        r = run(GOOD.replace("- Avoid jargon.\n", "- Drafts short and practical.\n"))
        assert not r["N1"]["pass"] and r["N1"]["unmatched"][0]["clause"] == "practical", r
        r = run(GOOD.replace("- Avoid jargon.\n", "- Avoid jargon.\n- Nothing else to avoid.\n"))
        assert not r["N1"]["pass"], r
        r = run(GOOD.replace("- Avoid jargon.\n- Avoid long preambles.\n", "- Avoid jargon and long preambles.\n- Plain, direct, no jargon.\n- No jargon or long preambles.\n"))
        assert r["pass"], r
        r = run(GOOD.replace("Executive General Manager Strategy", "Executive General Manager, Strategy"))
        assert r["pass"], r
        r = run(GOOD.replace("- Manager Capital Planning: Capital works program.", "- Manager Capital Planning: Capital works program, and Long-term asset plan."))
        assert not r["N1"]["pass"] and r["N1"]["unmatched"][0]["clause"] == "Long-term asset plan", r
        r = run(GOOD.replace("- Water.\n", "- Water; a regulated sector.\n"))
        assert not r["N1"]["pass"] and r["N1"]["unmatched"][0]["clause"] == "a regulated sector", r
        r = run(GOOD.replace("1. Capital", "- Capital").replace("2. Env", "- Env").replace("3. Long", "- Long"))
        assert r["pass"] and not r["PN_diagnostic"]["numbered"], r
    print("self-check ok")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a == ["--self-check"]:
        self_check()
        sys.exit(0)
    spec = persona(a[a.index("--persona") + 1])
    r = score(docx_md(a[0]), spec)
    s = json.dumps(r, indent=1)
    if "--out" in a:
        open(a[a.index("--out") + 1], "w").write(s + "\n")
    print(s)
    sys.exit(0 if r["pass"] else 1)
