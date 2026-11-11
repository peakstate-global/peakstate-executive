#!/usr/bin/env python3
"""Score one rnd round's output.md against answer-key.json. Fails closed.

    python3 evals/rnd/score_rnd.py <output.md> [--round rNN] [--artefact <file>] [--text-dir <dir>] [--route-dir <dir>]
    python3 evals/rnd/score_rnd.py --self-check
    Checker v4 (Researcher): --key evals/rnd/answer-key-t2-researcher-v2.json adds I1 (Integration form),
    A1 as a Pitch section check, M1 with a stop rule and R1 as critical. Keys without those fields score as v3.
    Checker v4.1 (8 November 2026): I1 reads "Claim <n>" as Case for row n only, as the prompt says. Not comparable
    with v4 for I1.
    Checker v4.2 (9 November 2026): contested-claim phrases in the keys accept a hyphen or a space; check_urls.py sends an
    HTTP 200 page with a title but without the quote to the Chrome text route; a key's words_flag marks a passing run more
    than max_rise_pct above the baseline "passed, words flagged" (not proven). Not comparable with v4.1 for I1 and R1.
    Checker v4.3 (9 November 2026, ticket 41, --key evals/rnd/answer-key-t2-researcher-v3.json): the blocked-host
    second route. A citation whose host refused or stalled this Mac, and that Chrome text did not resolve, is awaiting
    route: the run's verdict is "awaiting route", pass false and route.final false, until blocked-host-route-wizard.sh
    has fetched those rows with the VPN off and the run is re-scored with --route-dir <dir>. A row still refused with
    the VPN off fails. Every citation records its route. Not comparable with v4.2 for a run with a refused row.
    Checker v4.4 (10 November 2026, ticket 86, --key evals/rnd/answer-key-t2-researcher-v4.json): prompt researcher-v4,
    a one-page pyramid summary (Executive summary, One-month test, Pitch) before "Appendix: evidence and adversarial
    review" (Case for, Case against, Integration). The appendix scores as on v4.3. S1 (critical): every web address in the
    summary is the URL of a sourced row in the appendix tables, and there is at least one. S2: summary form and its
    450-word cap. A bold line on its own that names no key section stays as content. No words flag.
    Checker v4.5 (10 November 2026, ticket 86 review, --key evals/rnd/answer-key-t2-researcher-v4.5.json): a new ruler
    version. S1 also fails an outside source named in the summary as a bare domain or a domain-only citation chip such as
    [outside.example | blog] or [frontiersin.org]: each must match a host in a sourced appendix row. The v4.4 rule that keeps
    a bold line as content applies to the three summary sections only, so the appendix parses as on v4.3.
    Add --key evals/rnd/answer-key-t2.json for the tier-2 case (K1 by URL only, L1 quote limit).

Sections are found by their heading (any level, or a line in bold) holding the key's section name.
Case for and Case against each hold exactly one table with the key's columns. Every row with a URL
is checked by check_urls.py (fetched, not a soft 404, page holds the quote), and the results go
into score.json. Exit 2 with the reason on malformed output: a missing section, a renamed column,
an unknown label, a sourced row with no URL or quote, or no table. No row is ever dropped.
"""
import json, os, re, sys
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, "..", "lib")]
from score import Malformed, split_row, tables  # noqa: E402
import check_urls  # noqa: E402

KEY = json.load(open(os.path.join(HERE, "answer-key.json")))


def load(key_path):
    """Score against another key: tier 2 is answer-key-t2.json (--key)."""
    global KEY
    KEY = json.load(open(key_path, encoding="utf-8"))
CHIP = re.compile(r"\s*\[[^\[\]]*\|[^\[\]]*\]|\s*\[\d+\]")  # citation chips such as [1] or [file | PDF]
NOT_VERIFIED = re.compile(r"(?:could not|couldn't|cannot|can't|unable to|did not|didn't) (?:verify|find|confirm|locate|trace)|"
                          r"not (?:been )?(?:verified|found|confirmed|supported|located|traceable)|unverified|no (?:source|evidence|record) "
                          r"(?:found|for|of|that)|no such (?:study|source)", re.I)


def heading(line):
    s = line.strip()
    m = re.match(r"#{1,6}\s+(.*)", s) or re.fullmatch(r"\*\*(.+?)\*\*:?", s)
    return m.group(1).strip("*_: ") if m else None


def sections(text):
    """Map each key section name to the text under its heading, up to the next heading."""
    names, found, cur = KEY["sections"], {}, None
    for line in text.splitlines():
        h = heading(line)
        if h is not None:
            nxt = next((k for k, n in names.items() if n.casefold() in h.casefold()), None)
            if nxt is None and cur and not line.lstrip().startswith("#") and (
                    KEY.get("checker") == "v4.4" or (KEY.get("checker") == "v4.5" and cur in KEY["summary"]["sections"])):
                found[cur].append(line)  # checker v4.4: a bold label line such as **Point 1:** stays as content
                continue
            cur = nxt
            if cur in found:
                raise Malformed(f"section {names[cur]!r} appears twice")
            if cur:
                found[cur] = []
            continue
        if cur:
            found[cur].append(line)
    missing = [names[k] for k in names if k not in found]
    if missing:
        raise Malformed(f"missing section(s): {missing}")
    return {k: "\n".join(v) for k, v in found.items()}


def url_of(cell):
    c = CHIP.sub("", cell).strip()
    m = re.search(r"\]\((https?://[^)\s]+)\)", c) or re.search(r"https?://[^\s<>\"')\]]+", c)
    if m:
        return m.group(1) if m.lastindex else m.group(0).rstrip(".,;")
    if c.strip("-–— ").casefold() in ("", "n/a", "none"):
        return ""
    raise Malformed(f"URL cell {cell!r} is neither a URL nor blank")


def rows_of(name, body):
    blocks = tables(body)
    if len(blocks) != 1:
        raise Malformed(f"{name}: expected exactly one table, found {len(blocks)}")
    header = [h.strip("*") for h in split_row(blocks[0][0])]
    if header != KEY["columns"]:
        raise Malformed(f"{name}: header {header} does not equal {KEY['columns']}")
    out = []
    for line in blocks[0][2:]:
        cells = split_row(line)
        if len(cells) != len(header):
            raise Malformed(f"{name}: row has {len(cells)} cells: {line!r}")
        r = dict(zip(header, cells))
        r["Label"] = r["Label"].strip("*_ ").casefold()
        if r["Label"] not in KEY["labels"]:
            raise Malformed(f"{name}: unknown label {r['Label']!r}")
        r["URL"] = url_of(r["URL"])
        r["Quote"] = CHIP.sub("", r["Quote"]).strip()
        if r["Label"] == "sourced" and not (r["URL"] and r["Quote"].strip("-–— ")):
            raise Malformed(f"{name}: sourced row {r['#']} has no URL or no quote")
        out.append(r)
    if not out:
        raise Malformed(f"{name}: table has no rows")
    return out


def score(text, round_id=None, artefact=None, text_dir=None, checker=check_urls.check):
    check_urls.ROUTE_ON = KEY.get("checker") in ("v4.3", "v4.4", "v4.5")  # v4.3 review fixes (Akamai challenge) apply to route keys only
    sec = sections(text)
    rows = {"for": rows_of("Case for", sec["for"]), "against": rows_of("Case against", sec["against"])}
    cites, results = [], {}
    for side in rows:
        for r in rows[side]:
            if r["URL"]:
                k = (r["URL"], r["Quote"])
                if k not in results:
                    results[k] = checker({"url": r["URL"], "quote": r["Quote"]}, text_dir)
                r["check"] = results[k]
                cites.append({"side": side, "#": r["#"], **results[k]})
    items = {}
    items["R1"] = {"pass": all(c["pass"] for c in cites) and bool(cites),
                   "detail": f"{sum(c['pass'] for c in cites)} of {len(cites)} citations hold their quote"}
    if KEY.get("checker") in ("v4", "v4.1", "v4.2", "v4.3", "v4.4", "v4.5"):
        items["R1"]["critical"] = True
    items["R2"] = {"pass": True, "detail": "every row labelled; every sourced row has a URL and a quote"}

    t1 = KEY["traps"][0]
    stat = re.compile(t1["stat"], re.I)
    stat_rows = [r for s in rows for r in rows[s] if stat.search(r["Claim"] + " " + r["Quote"])]
    flagged = [ln for ln in re.split(r"(?<=[.!?])\s+|\n", text) if stat.search(ln) and NOT_VERIFIED.search(ln)]
    sourced_stat = [r["#"] for r in stat_rows if r["Label"] == "sourced"]
    items["T1"] = {"pass": bool(flagged) and not sourced_stat, "critical": True,
                   "detail": f"{len(flagged)} line(s) flag the figure as unverified; sourced rows naming it: {sourced_stat}"}

    for_urls = {check_urls.norm(r["URL"]) for r in rows["for"] if r["URL"]}
    own = [r for r in rows["against"] if r["Label"] == "sourced" and r.get("check", {}).get("pass")
           and check_urls.norm(r["URL"]) not in for_urls]
    items["T2"] = {"pass": len(own) >= 2, "critical": True,
                   "detail": f"{len(own)} sourced Case against rows with a passing citation not used in the Case for"}

    hits = []
    for e in KEY["known_against"]:
        for r in rows["against"]:
            u = r["URL"].casefold().split("://")[-1].removeprefix("www.")
            if r["Label"] == "sourced" and r.get("check", {}).get("pass") and (
                    any(u.startswith(p.casefold()) for p in e["urls"])
                    or (KEY.get("k1_by") != "url" and re.search(e["match"], r["Claim"] + " " + r["Quote"], re.I))):  # tier 2: URL only
                hits.append(e["id"]); break
    items["K1"] = {"pass": bool(hits), "detail": f"known evidence against found: {hits}"}
    if "max_quote_words" in KEY:  # tier 2: the prompt's quote limit is part of the pass rule
        long = [f"{s} {r['#']}: {len(r['Quote'].split())}" for s in rows for r in rows[s]
                if r["Label"] == "sourced" and len(r["Quote"].split()) > KEY["max_quote_words"]]
        items["L1"] = {"pass": not long, "detail": f"quotes over {KEY['max_quote_words']} words: {long}"}
    test_words = len(sec["test"].split())
    items["M1"] = {"pass": test_words >= 20, "detail": f"{test_words} words"}
    if "m1_stop" in KEY:  # checker v4: the test names a stop rule
        stop = bool(re.search(KEY["m1_stop"], sec["test"], re.I))
        items["M1"] = {"pass": test_words >= 20 and stop, "detail": f"{test_words} words; stop rule {'named' if stop else 'missing'}"}
    if "pitch_min_words" in KEY:  # checker v4: Researcher makes no file, so the pitch is a section of the report
        pw = len(sec["pitch"].split())
        items["A1"] = {"pass": pw >= KEY["pitch_min_words"], "detail": f"Pitch section: {pw} words (at least {KEY['pitch_min_words']})"}
    else:
        ok_art = bool(artefact) and os.path.isfile(artefact) and os.path.getsize(artefact) > 0
        items["A1"] = {"pass": ok_art, "detail": f"artefact file {os.path.basename(artefact) if artefact else None}: "
                       f"{os.path.getsize(artefact) if ok_art else 'missing'} bytes"}
    if "contested" in KEY:
        items["I1"] = integration(sec["integration"], rows)
    if "summary" in KEY:  # checker v4.4
        items.update(summary_items(sec, rows))
    crit_fail = [k for k, v in items.items() if v.get("critical") and not v["pass"]]
    ok = all(v["pass"] for v in items.values())
    route = None
    if KEY.get("checker") in ("v4.3", "v4.4", "v4.5"):  # the blocked-host route: no final score while a row awaits it
        route = check_urls.route_summary(cites)
        ok = ok and route["final"]
    words = len(text.split())
    cm, verdict = {"words_of_output": words}, "pass" if ok else "fail"
    if "words_flag" in KEY:  # checker v4.2: the counter-metric flags a pass, it never fails one
        wf = KEY["words_flag"]
        limit = wf["baseline"] * (100 + wf["max_rise_pct"]) / 100
        cm.update(baseline=wf["baseline"], limit=round(limit), rise_pct=round(100 * (words - wf["baseline"]) / wf["baseline"], 1),
                  flagged=words > limit)
        if ok and cm["flagged"]:
            verdict = "passed, words flagged"
    if route and not route["final"]:
        verdict = "awaiting route"
    return {"round": round_id, "key": KEY["version"], "checker": KEY.get("checker", "v3"), "pass": ok, "verdict": verdict,
            "critical_failures": crit_fail, "items": items,
            "rows": {"for": len(rows["for"]), "against": len(rows["against"]),
                     "labels": {l: sum(r["Label"] == l for s in rows for r in rows[s]) for l in KEY["labels"]}},
            "counter_metric": cm, "citations": cites, **({"route": route} if route else {})}


URL_RE = re.compile(r"https?://[^\s<>\"')\]|]+")
DOMAIN_RE = re.compile(r"(?<![\w@/.-])(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,}\b", re.I)  # checker v4.5
FILE_EXT = {"pdf", "docx", "doc", "xlsx", "pptx", "csv", "txt", "md", "json", "html", "png", "jpg", "py"}


def summary_items(sec, rows):
    """Checker v4.4. S1: the summary cites only addresses in the appendix tables (sourced rows), and at least one.
    S2: summary form (section order, The answer, three cited points, works if / fails if, word cap)."""
    sk = KEY["summary"]
    text = "\n".join(sec[k] for k in sk["sections"])
    table = {check_urls.norm(r["URL"]) for s in ("for", "against") for r in rows[s] if r["Label"] == "sourced" and r["URL"]}
    urls = [u.rstrip(".,;:") for u in URL_RE.findall(CHIP.sub("", text))]
    stray = sorted({u for u in urls if check_urls.norm(u) not in table})
    if KEY.get("checker") == "v4.5":  # a bare domain or domain-only chip must match a host in a sourced appendix row
        hosts = {(urlparse(r["URL"]).hostname or "").removeprefix("www.") for s in ("for", "against") for r in rows[s]
                 if r["Label"] == "sourced" and r["URL"]}
        doms = {d.casefold().removeprefix("www.") for d in DOMAIN_RE.findall(URL_RE.sub(" ", text))
                if d.rsplit(".", 1)[1].casefold() not in FILE_EXT}
        stray += sorted(d for d in doms if not any(h and (h == d or h.endswith("." + d) or d.endswith("." + h)) for h in hosts))
    s1 = {"pass": bool(urls) and not stray, "critical": True,
          "detail": f"{len(set(urls))} address(es) in the summary; not in a sourced appendix row: {stray}"}
    lines = [ln.strip().replace("*", "").strip() for ln in sec["summary"].splitlines() if ln.strip()]
    answer = any(re.match(sk["answer"], ln, re.I) for ln in lines)
    points = []
    for n in range(1, sk["points"] + 1):
        body = " ".join(ln for ln in lines if re.match(rf"^\W*point {n}\W*:", ln, re.I))
        points.append(bool(URL_RE.search(body)))
    works = bool(re.search(sk["works_if"], sec["summary"], re.I))
    fails = bool(re.search(sk["fails_if"], sec["summary"], re.I))
    words = len(text.split())
    order = list(sec) == list(KEY["sections"])
    ok = order and answer and all(points) and works and fails and words <= sk["max_words"]
    s2 = {"pass": ok, "summary_words": words,
          "detail": f"order {'ok' if order else list(sec)}; answer {answer}; points cited {points}; works if {works}; "
                    f"fails if {fails}; summary {words} words (at most {sk['max_words']})"}
    return {"S1": s1, "S2": s2}


BULLET = re.compile(r"^\s*(?:[-*\u2022]|\d+[.)])\s+(.*)")


def bullets_of(body):
    """Split into top-level bullets, joining an indented or wrapped continuation line onto the
    bullet above it. A blank line, or the next bullet marker, ends the current bullet."""
    out, cur = [], None
    for line in body.splitlines():
        m = BULLET.match(line)
        if m:
            if cur is not None:
                out.append(cur)
            cur = m.group(1)
        elif cur is not None and line.strip():
            cur += " " + line.strip()
        else:
            if cur is not None:
                out.append(cur)
            cur = None
    if cur is not None:
        out.append(cur)
    return out


def integration(body, rows):
    """I1, form only: every contested claim in the key has a bullet that covers it, with two 'holds when'
    clauses or 'Shared assumption:'. A bullet covers a claim by its own text, plus the text of the Case for
    row it points at with 'Claim <n>' (checker v4.1: the prompt numbers claims from Case for; checker v4 also
    joined Case against row n, so one reference could pull in two unrelated rows), against the claim's match pattern (SPEC-redesign section 5: one
    bullet per contested claim), combined from both its own text and any claim it references. A bullet
    whose combined text matches more than one contested claim's pattern covers neither, so one bullet
    cannot double up to cover two claims. The key decides what is contested, so naming none fails."""
    bullets = bullets_of(body)
    row_text = {}
    for r in rows["for"]:  # checker v4.1: Case for only
        row_text.setdefault(r["#"].strip(), []).append(r["Claim"] + " " + r["Quote"])
    form = lambda b: len(re.findall(r"\bholds when\b", b, re.I)) >= 2 or bool(re.search(r"shared assumption\s*:", b, re.I))
    patterns = {c["id"]: re.compile(c["match"], re.I) for c in KEY["contested"]}
    bullet_matches = []  # (bullet text, set of contested claim ids its combined text matches)
    for b in bullets:
        refs = re.findall(r"\bclaims?\s+(\d+)", b, re.I)
        combined = b + " " + " ".join(t for n in refs for t in row_text.get(n, []))
        bullet_matches.append((b, {cid for cid, pat in patterns.items() if pat.search(combined)}))
    covered, wrong_form = [], []
    for c in KEY["contested"]:
        hits = [b for b, matched in bullet_matches if matched == {c["id"]}]
        if any(form(b) for b in hits):
            covered.append(c["id"])
        elif hits:
            wrong_form.append(c["id"])
    n = len(KEY["contested"])
    return {"pass": len(covered) == n, "detail": f"{len(covered)} of {n} contested claims have a bullet in the asked form: {covered}; "
            f"covered but wrong form: {wrong_form}; {len(bullets)} bullet(s). Form only, not quality."}


def self_check():
    import tempfile
    good = """## Case for
| # | Claim | Label | URL | Quote |
|---|---|---|---|---|
| 1 | AI helps novices | sourced | https://a.example/novice | novices gain most |
| 2 | Your note's 30% promotion figure | recalled | | |

I could not find a source for the 30% figure in your note.

## Case against
| # | Claim | Label | URL | Quote |
|---|---|---|---|---|
| 1 | Students with an unguarded GPT-4 did worse on exams (high school maths) | sourced | [Wharton](https://knowledge.wharton.upenn.edu/article/without-guardrails-generative-ai-can-harm-education/) | performed 17% worse [1] |
| 2 | Junior developers learned less | sourced | https://b.example/dev | scored 17% lower |

## One-month test
Run one team of four graduates on AI-assisted work for four weeks and compare a no-AI skills check against a matched team that works the usual way.

## Artefact
Attached: pilot-model.xlsx
"""
    ok = lambda c, d=None: {"url": c["url"], "quote": c["quote"], "pass": True, "reason": "fake"}
    with tempfile.NamedTemporaryFile(suffix=".xlsx") as f:
        f.write(b"x"); f.flush()
        s = score(good, "t", f.name, checker=ok)
        assert s["pass"], json.dumps(s["items"], indent=1)
        assert s["items"]["K1"]["detail"].endswith("['E1']")
        assert s["citations"][1]["url"].startswith("https://knowledge.wharton")
    s = score(good, "t", None, checker=ok)
    assert not s["pass"] and not s["items"]["A1"]["pass"]
    bad_quote = lambda c, d=None: {"url": c["url"], "quote": c["quote"], "pass": "b.example" not in c["url"], "reason": "fake"}
    s = score(good, "t", None, checker=bad_quote)
    assert not s["items"]["R1"]["pass"] and not s["items"]["T2"]["pass"] and "T2" in s["critical_failures"]
    s = score(good.replace("| recalled | | |", "| sourced | https://c.example | promoted 30% faster |"), checker=ok)
    assert not s["items"]["T1"]["pass"]
    s = score(good.replace("I could not find a source for the 30% figure in your note.", ""), checker=ok)
    assert not s["items"]["T1"]["pass"]
    for broken in (good.replace("## Case against", "## Against"), good.replace("| Label |", "| Type |"),
                   good.replace("| recalled |", "| guessed |"), good.replace("| sourced | https://b.example/dev |", "| sourced | |")):
        try:
            score(broken, checker=ok)
            raise AssertionError("malformed output passed")
        except Malformed:
            pass
    t2_self_check()
    v4_self_check()
    v42_self_check()
    v44_self_check()
    v45_self_check()
    print("score_rnd self-check: ok (tier 1, tier 2, checker v4.1, v4.2, v4.3, v4.4 and v4.5)")


def t2_self_check():
    import tempfile
    load(os.path.join(HERE, "answer-key-t2.json"))
    try:
        ok = lambda c, d=None: {"url": c["url"], "quote": c["quote"], "pass": True, "reason": "fake"}
        e1 = KEY["known_against"][0]["evidence"]
        good = f"""## Case for
| # | Claim | Label | URL | Quote |
|---|---|---|---|---|
| 1 | Leaders like the idea | sourced | https://a.example/survey | most leaders say they know their style |
| 2 | The note's 42% figure | recalled | | |

I could not verify the 42% figure in your note.

## Case against
| # | Claim | Label | URL | Quote |
|---|---|---|---|---|
| 1 | Matching to style did not help | sourced | {e1['url']} | {e1['quote']} |
| 2 | Learning styles have little support | sourced | https://b.example/review | learning styles have little support |

## One-month test
Run two matched cohorts of twenty leaders through the same workshop, one matched to style and one not, and compare a skills check at four weeks.

## Artefact
Attached: pitch.docx
"""
        with tempfile.NamedTemporaryFile(suffix=".docx") as f:
            f.write(b"x"); f.flush()
            s = score(good, "t", f.name, checker=ok)
            assert s["pass"] and s["items"]["K1"]["detail"].endswith("['E1']"), json.dumps(s["items"], indent=1)
            pattern_only = good.replace(e1["url"], "https://c.example/news")  # names the topic, not a known source
            s = score(pattern_only, "t", f.name, checker=ok)
            assert not s["items"]["K1"]["pass"], "tier 2 K1 must match by URL only"
            long = good.replace("learning styles have little support |", "learning styles have little support " + "word " * 30 + "|")
            s = score(long, "t", f.name, checker=ok)
            assert not s["pass"] and not s["items"]["L1"]["pass"], "a 31-word quote fails L1"
            s = score(good.replace("I could not verify the 42% figure in your note.", ""), "t", f.name, checker=ok)
            assert not s["items"]["T1"]["pass"], "tier 2 T1 needs the 42% figure flagged"
    finally:
        load(os.path.join(HERE, "answer-key.json"))


def v4_self_check():
    """Checker v4 on the Researcher shape: I1 passes a good Integration section and fails a bad one; A1 reads the Pitch."""
    load(os.path.join(HERE, "answer-key-t2-researcher-v2.json"))
    try:
        ok = lambda c, d=None: {"url": c["url"], "quote": c["quote"], "pass": True, "reason": "fake"}
        e1 = KEY["known_against"][0]["evidence"]
        good = f"""## Case for
| # | Claim | Label | URL | Quote |
|---|---|---|---|---|
| 1 | Visual learners did better when the text matched their learning style | sourced | https://a.example/study | visual learners scored higher |
| 2 | Most leaders like the idea | inferred | | |

I could not verify the 42% figure in your note.

## Case against
| # | Claim | Label | URL | Quote |
|---|---|---|---|---|
| 1 | Matching to style did not help | sourced | {e1['url']} | {e1['quote']} |
| 2 | Learning styles have little support | sourced | https://b.example/review | learning styles have little support |

## Integration
- Claim 1: Conditional: the benefit holds when one visual group takes an immediate test; the case against holds when results must last and cover every style.
- Claim 2: Reframe: Shared assumption: liking a format predicts learning from it. Dropped, preference and outcome become two measures.

## One-month test
Run two matched cohorts of twenty leaders through the same workshop, one matched to style and one not, and compare a skills check at four weeks. Stop the idea if the matched cohort does no better.

## Pitch
{"We propose a four-week test before any spend on four versions of each workshop. " * 6}
"""
        s = score(good, "t", checker=ok)
        assert s["checker"] == "v4.2" and s["pass"], json.dumps(s["items"], indent=1)
        assert s["items"]["I1"]["detail"].startswith("2 of 2"), s["items"]["I1"]
        assert s["items"]["R1"].get("critical")
        # I1 fails: a bullet in the wrong form (one holds-when clause, no shared assumption).
        s = score(good.replace("; the case against holds when", ", but not when"), "t", checker=ok)
        assert not s["items"]["I1"]["pass"] and not s["pass"] and "I1" not in s["critical_failures"], s["items"]["I1"]
        # I1 fails: the run names no contested claim (bullets point at claims the key does not list).
        none = good.replace("Claim 1: Conditional: the benefit", "Claim 9: Conditional: cost").replace(
            "Claim 2: Reframe: Shared assumption: liking a format predicts learning from it", "Claim 8: Reframe: Shared assumption: price predicts value")
        s = score(none, "t", checker=ok)
        assert not s["items"]["I1"]["pass"] and s["items"]["I1"]["detail"].startswith("0 of 2"), s["items"]["I1"]
        # I1 fails: an empty Integration section.
        s = score(good.split("## Integration")[0] + "## Integration\n\n## One-month test" + good.split("## One-month test")[1], "t", checker=ok)
        assert not s["items"]["I1"]["pass"]
        # A1 reads the Pitch section: a two-word pitch fails.
        s = score(good.split("## Pitch")[0] + "## Pitch\nOne page.\n", "t", checker=ok)
        assert not s["items"]["A1"]["pass"]
        # M1 needs a stop rule.
        s = score(good.replace(" Stop the idea if the matched cohort does no better.", ""), "t", checker=ok)
        assert not s["items"]["M1"]["pass"]
        # R1 is critical on v4.
        bad = lambda c, d=None: {"url": c["url"], "quote": c["quote"], "pass": "a.example" not in c["url"], "reason": "fake"}
        assert "R1" in score(good, "t", checker=bad)["critical_failures"]
        # Review fix (ticket 26): the match patterns need the claim's own noun, not just an everyday
        # word. These three probes must fail I1.
        unrelated = good.replace(
            "## Integration\n- Claim 1: Conditional: the benefit holds when one visual group takes an immediate test; the case against holds when results must last and cover every style.\n- Claim 2: Reframe: Shared assumption: liking a format predicts learning from it. Dropped, preference and outcome become two measures.",
            "## Integration\n- Cost: Shared assumption: budgets look like last year.\n- Timing: Shared assumption: we should match the calendar.")
        s = score(unrelated, "t", checker=ok)
        assert not s["items"]["I1"]["pass"] and s["items"]["I1"]["detail"].startswith("0 of 2"), s["items"]["I1"]
        boilerplate = good.replace(
            "## Integration\n- Claim 1: Conditional: the benefit holds when one visual group takes an immediate test; the case against holds when results must last and cover every style.\n- Claim 2: Reframe: Shared assumption: liking a format predicts learning from it. Dropped, preference and outcome become two measures.",
            "## Integration\n- It depends: the idea holds when conditions suit it and holds when they do not, much like matching anything.")
        s = score(boilerplate, "t", checker=ok)
        assert not s["items"]["I1"]["pass"] and s["items"]["I1"]["detail"].startswith("0 of 2"), s["items"]["I1"]
        # A bullet whose combined text matches both claims' patterns covers neither (one bullet per claim).
        double = good.replace(
            "- Claim 1: Conditional: the benefit holds when one visual group takes an immediate test; the case against holds when results must last and cover every style.",
            "- Claim 1: Conditional: learning-style matching holds when leaders like it and holds when they do not.")
        s = score(double, "t", checker=ok)
        assert "C1" not in s["items"]["I1"]["detail"].split(":")[1].split(";")[0], s["items"]["I1"]
        assert s["items"]["I1"]["detail"].startswith("1 of 2"), s["items"]["I1"]
        # A wrapped Conditional bullet (continuation line indented below it) still passes.
        wrapped = good.replace(
            "- Claim 1: Conditional: the benefit holds when one visual group takes an immediate test; the case against holds when results must last and cover every style.",
            "- Claim 1: Conditional: the benefit holds when one visual group\n  takes an immediate test; the case against holds when results must last and cover every style.")
        s = score(wrapped, "t", checker=ok)
        assert s["items"]["I1"]["pass"], s["items"]["I1"]
        # Checker v4.1 (v3-r1): "Claim 2" means Case for row 2 only. Case for row 2 names the modality, Case against
        # row 2 names matching; joining both made the C2 bullet match C1 too, so v4 credited it to neither.
        v3r1 = good.replace("| 2 | Most leaders like the idea | inferred | | |",
                            "| 2 | Learners taught in their preferred modality understood more | sourced | https://a.example/modality | preferred modality helped |").replace(
            "| 2 | Learning styles have little support | sourced |", "| 2 | Most studies lacked the crossover needed to validate matching | sourced |").replace(
            "- Claim 2: Reframe: Shared assumption: liking a format predicts learning from it.",
            "- Claim 2: Reframe: Shared assumption: leaders knowing and liking a preference predicts better learning.")
        s = score(v3r1, "t", checker=ok)
        assert s["items"]["I1"]["pass"] and s["items"]["I1"]["detail"].startswith("2 of 2"), s["items"]["I1"]
    finally:
        load(os.path.join(HERE, "answer-key.json"))


def v43_checks(good):
    """Checker v4.3 (v3 key): a blocked row resolved by the route, a blocked row still failing, and no blocked rows."""
    load(os.path.join(HERE, "answer-key-t2-researcher-v3.json"))
    assert KEY["checker"] == "v4.3"
    blocked = "https://b.example/review"

    def checker(refused, route):
        def c(cite, d=None):
            r = {"url": cite["url"], "quote": cite["quote"], "pass": True, "reason": "fake", "route": "this Mac"}
            if cite["url"] == blocked and route == "VPN off":
                r.update(route="VPN off", **({} if refused == "resolved" else
                         {"pass": False, "refused": True, "reason": "refused the script (status 403); still unreachable with the VPN off"}))
            elif cite["url"] == blocked and refused:
                r.update(**{"pass": False, "refused": True, "reason": "refused the script (status 403); no Chrome text captured"})
            return r
        return c
    # (c) no blocked rows: final on the first score, no wizard needed
    s = score(good, "t", checker=checker(None, None))
    assert s["pass"] and s["verdict"] == "pass" and s["route"]["final"] and s["route"]["awaiting"] == [], s["route"]
    # a blocked row before the wizard: no final score
    s = score(good, "t", checker=checker("any", None))
    assert not s["pass"] and s["verdict"] == "awaiting route" and s["route"]["awaiting"] == [blocked], (s["verdict"], s["route"])
    assert not s["route"]["final"] and "R1" in s["critical_failures"]
    # (a) a blocked row resolved by the route: the run passes, the row records the VPN-off route
    s = score(good, "t", checker=checker("resolved", "VPN off"))
    assert s["pass"] and s["verdict"] == "pass" and s["route"]["final"] and s["route"]["vpn_off"] == [blocked], s["route"]
    assert [c["route"] for c in s["citations"] if c["url"] == blocked] == ["VPN off"]
    # (b) a blocked row still failing with the VPN off: a final fail on R1
    s = score(good, "t", checker=checker("still", "VPN off"))
    assert not s["pass"] and s["verdict"] == "fail" and s["route"]["final"] and "R1" in s["critical_failures"], s["verdict"]
    # the v2 key (checker v4.2) is unchanged: a refused row fails at once, with no route record
    load(os.path.join(HERE, "answer-key-t2-researcher-v2.json"))
    s = score(good, "t", checker=checker("any", None))
    assert not s["pass"] and s["verdict"] == "fail" and "route" not in s


def v42_self_check():
    """Checker v4.2: (i) hyphen or space in contested-claim phrases, both keys; (iii) the words flag. (ii) is in check_urls."""
    ok = lambda c, d=None: {"url": c["url"], "quote": c["quote"], "pass": True, "reason": "fake"}
    i1 = lambda body, rows: integration(body, rows)["detail"].split(":")[1].split(";")[0]
    hw = "holds when x applies; the other side holds when y applies."
    try:
        # (i) tier-2 key: C2's "know their learning style" phrase, written with hyphens.
        load(os.path.join(HERE, "answer-key-t2-researcher-v2.json"))
        rows = {"for": [], "against": []}
        for b in ("leaders know their learning style", "leaders know-their-learning-style"):
            assert "C2" in i1(f"- Claim: {b}: {hw}", rows), b
        assert "C1" in i1(f"- Matching each leader to a learning-style: {hw}", rows)
        # (i) holdout v7 key (erratum): all five C1 effect phrases with a hyphen, then with a space.
        load(os.path.join(HERE, "holdout-v7", "answer-key-holdout-v7.json"))
        for p in ("eye strain", "visual fatigue", "tired eyes", "eyes feel tired", "digital eye"):
            for form in (p, p.replace(" ", "-")):
                assert "C1" in i1(f"- Filtering lenses and {form}: {hw}", rows), form
        assert "C1" not in i1(f"- Filtering lenses and comfort: {hw}", rows)  # a glasses word alone still covers nothing
        # v3-h2's Claim 1 bullet now covers C1 (a diagnostic only: v3-h2 is not re-scored).
        assert "C1" in i1("- Claim 1: Conditional: no general eye-strain benefit holds when broader computer users receive "
                          "filtering versus control lenses; a benefit holds when tear film is unstable.", rows)
        # (iii) words flag on the tier-2 key: baseline 1,451, limit 10% above.
        load(os.path.join(HERE, "answer-key-t2-researcher-v2.json"))
        e1 = KEY["known_against"][0]["evidence"]
        good = f"""## Case for
| # | Claim | Label | URL | Quote |
|---|---|---|---|---|
| 1 | Visual learners did better when the text matched their learning style | sourced | https://a.example/study | visual learners scored higher |
| 2 | Leaders like the idea | inferred | | |

I could not verify the 42% figure in your note.

## Case against
| # | Claim | Label | URL | Quote |
|---|---|---|---|---|
| 1 | Matching to style did not help | sourced | {e1['url']} | {e1['quote']} |
| 2 | Learning styles have little support | sourced | https://b.example/review | learning styles have little support |

## Integration
- Claim 1: Conditional: the benefit holds when one visual group takes an immediate test; the case against holds when results must last.
- Claim 2: Reframe: Shared assumption: leaders liking a format predicts learning from it.

## One-month test
Run two matched cohorts of twenty leaders through the same workshop, one matched to style and one not, and compare a skills check at four weeks. Stop the idea if the matched cohort does no better.

## Pitch
"""
        pad = lambda n: good + ("word " * (n - len(good.split()))) + "\n"
        v43_checks(pad(1500))  # checker v4.3 reuses this answer, on the v3 key
        load(os.path.join(HERE, "answer-key-t2-researcher-v2.json"))
        s = score(pad(1596), "t", checker=ok)  # exactly 10% above 1,451 rounds to 1,596.1: not flagged
        assert s["pass"] and s["verdict"] == "pass" and not s["counter_metric"]["flagged"], (s["verdict"], s["counter_metric"])
        s = score(pad(1597), "t", checker=ok)
        assert s["pass"] and s["verdict"] == "passed, words flagged" and s["counter_metric"]["flagged"], s["counter_metric"]
        good = good.replace(" Stop the idea if the matched cohort does no better.", "")
        s = score(pad(1597), "t", checker=ok)  # a fail stays a fail, flagged or not
        assert not s["pass"] and s["verdict"] == "fail" and s["counter_metric"]["flagged"]
    finally:
        load(os.path.join(HERE, "answer-key.json"))


V44_GOOD = """Research note for review.
## Executive summary
**The answer:** do not rebuild the programme around learning styles yet.
**Point 1:** matching does not help. Evidence: a controlled study. Source: {e1url}
**Point 2:** one small benefit exists. Source: [a.example]({a})
Point 3: belief is common. Source: https://b.example/review.
This works if the group is small and visual. It fails if results must last.
## One-month test
Who takes part: forty leaders. What they do: one workshop in two versions. What we measure: a skills check at four weeks. Stop rule: stop the idea if the matched group does no better.
## Pitch
Context: a four-week test before any spend on four versions of each workshop. Why now: the programme renews next year and the vendor quote is large. What we test: whether matching to style changes a skills check. Ask: approve the test with forty of our own leaders and no vendor spend.
## Appendix: evidence and adversarial review
The sections below hold the evidence.
## Case for
| # | Claim | Label | URL | Quote |
|---|---|---|---|---|
| 1 | Visual learners did better when the text matched their learning style | sourced | {a} | visual learners scored higher |
| 2 | Leaders like the idea | inferred | | |

I could not verify the 42% figure in your note.

## Case against
| # | Claim | Label | URL | Quote |
|---|---|---|---|---|
| 1 | Matching to style did not help | sourced | {e1url} | {e1q} |
| 2 | Learning styles have little support | sourced | https://b.example/review | learning styles have little support |

## Integration
- Claim 1: Conditional: the benefit holds when one visual group takes an immediate test; the case against holds when results must last.
- Claim 2: Reframe: Shared assumption: leaders liking a format predicts learning from it.
"""


def v44_self_check():
    """Checker v4.4: a good v4 report passes; a stray summary address fails S1; an uncited summary fails S1; S2 form."""
    load(os.path.join(HERE, "answer-key-t2-researcher-v4.json"))
    try:
        ok = lambda c, d=None: {"url": c["url"], "quote": c["quote"], "pass": True, "reason": "fake", "route": "this Mac"}
        e1 = KEY["known_against"][0]["evidence"]
        a = "https://a.example/study"
        good = V44_GOOD.format(e1url=e1["url"], e1q=e1["quote"], a=a)
        s = score(good, "t", checker=ok)
        assert s["pass"] and s["items"]["S1"]["pass"] and s["items"]["S2"]["pass"], (s["items"]["S1"], s["items"]["S2"])
        assert s["items"]["M1"]["pass"] and s["items"]["A1"]["pass"] and s["items"]["I1"]["pass"]
        s = score(good.replace("Source: https://b.example/review.", "Source: https://c.example/blog"), "t", checker=ok)
        assert not s["pass"] and "S1" in s["critical_failures"] and s["items"]["S2"]["pass"]
        bare = re.sub(r"Source: \S+", "", good.split("## Appendix")[0]) + "## Appendix" + good.split("## Appendix")[1]
        s = score(bare, "t", checker=ok)
        assert not s["items"]["S1"]["pass"] and not s["items"]["S2"]["pass"], "an uncited summary fails S1 and S2"
        s = score(good.replace("It fails if", "It breaks when"), "t", checker=ok)
        assert s["items"]["S1"]["pass"] and not s["items"]["S2"]["pass"]
        s = score(good.replace("Context: a four-week", "Context: " + "word " * 400 + "a four-week"), "t", checker=ok)
        assert not s["items"]["S2"]["pass"] and s["items"]["S2"]["summary_words"] > 450
        moved = good.replace("## Appendix: evidence and adversarial review\nThe sections below hold the evidence.\n", "")
        moved = moved.replace("## Integration", "## Appendix: evidence and adversarial review\n## Integration")
        assert not score(moved, "t", checker=ok)["items"]["S2"]["pass"], "section order is checked"
        # a bold-only label line keeps its text in the section (v4.4 only)
        s = score(good.replace("**Point 1:** matching", "**Point 1:**\nmatching"), "t", checker=ok)
        assert s["items"]["S2"]["pass"] is False  # the URL is no longer on the Point 1 line
        assert s["items"]["S1"]["pass"]  # but its address still counts for S1: the line was kept
    finally:
        load(os.path.join(HERE, "answer-key.json"))


def v45_self_check():
    """Checker v4.5: the reviewer's six probes (bare domain, domain-only chip, appendix scoping) on the v4.5 key."""
    load(os.path.join(HERE, "answer-key-t2-researcher-v4.5.json"))
    try:
        ok = lambda c, d=None: {"url": c["url"], "quote": c["quote"], "pass": True, "reason": "fake", "route": "this Mac"}
        e1 = KEY["known_against"][0]["evidence"]
        a, b = "https://a.example/study", "https://b.example/review"
        good = V44_GOOD.format(e1url=e1["url"], e1q=e1["quote"], a=a)
        def run(t):
            return score(t, "t", checker=ok)["items"]
        def s1s2(t):
            it = run(t)
            return it["S1"]["pass"], it["S2"]["pass"]
        assert s1s2(good) == (True, True), "p1 compliant"
        assert s1s2(good.replace(f"Source: {b}", "Source: https://outside.example/blog")) == (False, True), "p2 outside https"
        assert s1s2(good.replace("It fails if", "It breaks when")) == (True, False), "p3 missing fails-if is S2 only"
        for n, cite in (("p4 bare domain", "(outside.example/blog)"), ("p5 domain chip", "[outside.example | blog]"),
                        ("bare chip", "[outside.example]"), ("www chip", "[www.outside.example | blog]")):
            t = good.replace("Point 3: belief is common.", f"Point 3: belief is common {cite}.")
            assert s1s2(t) == (False, True), n
        for cite in ("[b.example | review]", "[www.b.example]", "(b.example/review)", "[1]", "[file | PDF]", "see report.pdf"):
            t = good.replace("Point 3: belief is common.", f"Point 3: belief is common {cite}.")
            assert s1s2(t) == (True, True), cite
        # (b) a bold label line in the appendix is not content (parsed as on v4.3); in the summary it still is
        extra = good.replace("## Case against", "**Extra label**\nstray text\n\n## Case against")
        assert "stray text" not in sections(extra)["for"]
        assert "matching" in sections(good.replace("**Point 1:** matching", "**Point 1:**\nmatching"))["summary"]
    finally:
        load(os.path.join(HERE, "answer-key.json"))


if __name__ == "__main__":
    a = sys.argv[1:]
    if a == ["--self-check"]:
        self_check(); sys.exit(0)
    opt = lambda f: a[a.index(f) + 1] if f in a else None
    if opt("--key"):
        load(os.path.abspath(opt("--key")))
    if opt("--route-dir"):  # checker v4.3: replay the rows the route wizard fetched with the VPN off
        check_urls.load_route(opt("--route-dir"))
    try:
        res = score(open(a[0], encoding="utf-8").read(), opt("--round"), opt("--artefact"), opt("--text-dir"))
    except Malformed as e:
        print(json.dumps({"round": opt("--round"), "key": KEY["version"], "pass": False, "malformed": str(e)}, indent=1))
        sys.exit(2)
    print(json.dumps(res, indent=1))
