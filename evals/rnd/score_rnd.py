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
    Checker v4.3 (9 November 2026, --key evals/rnd/answer-key-t2-researcher-v3.json): the blocked-host
    second route. A citation whose host refused or stalled this Mac, and that Chrome text did not resolve, is awaiting
    route: the run's verdict is "awaiting route", pass false and route.final false, until blocked-host-route-wizard.sh
    has fetched those rows with the VPN off and the run is re-scored with --route-dir <dir>. A row still refused with
    the VPN off fails. Every citation records its route. Not comparable with v4.2 for a run with a refused row.
    Checker v4.4 (10 November 2026, --key evals/rnd/answer-key-t2-researcher-v4.json): prompt researcher-v4,
    a one-page pyramid summary (Executive summary, One-month test, Pitch) before "Appendix: evidence and adversarial
    review" (Case for, Case against, Integration). The appendix scores as on v4.3. S1 (critical): every web address in the
    summary is the URL of a sourced row in the appendix tables, and there is at least one. S2: summary form and its
    450-word cap. A bold line on its own that names no key section stays as content. No words flag.
    Checker v4.5 (10 November 2026, --key evals/rnd/answer-key-t2-researcher-v4.5.json): a new ruler
    version. S1 also fails an outside source named in the summary as a bare domain or a domain-only citation chip such as
    [outside.example | blog] or [frontiersin.org]: each must match a host in a sourced appendix row. The v4.4 rule that keeps
    a bold line as content applies to the three summary sections only, so the appendix parses as on v4.3.
    Checker v5 (17 November 2026, --key evals/rnd/answer-key-t2-researcher-v5.json): prompt researcher-v5,
    plain English with numbered APA 7 references. The appendix is "Appendix: the evidence", "Evidence for the idea",
    "Evidence against the idea" and "Where both sides are right", then "Words used in this note" and "References" (last).
    "## References" is parsed into a map of number to entry and address. Each row's Source cell (the column the key names)
    holds one [n], resolved to its entry's address before any chip step; a bare [n] is no longer a chip on this key, so
    quotes keep their source's own bracketed numbers. Several rows may cite one [n]; each row's quote is checked on that
    page with the v4.5 routes. S1: every summary [n] resolves to a reference a sourced row cites, and a bare domain or
    domain-only chip must match a cited reference's host or the final host check_urls reached for it. S2: each Point
    cites an [n]; caps 300 / 180 / 150 words and 600 together. I1: the two reconcile forms in the key only. R5 (new):
    each DOI entry matches its Crossref record on title, first author's family name, year, volume and issue, and the
    result lists every element that differs; an entry with no DOI needs its title on its page. plain_check.py --refs
    (P1 to P4) is reported beside the items under "plain" and does not change the checker's pass. Experimental phase:
    not comparable with v4.5. A v4 note is malformed on this key (no v5 appendix sections, no References).
    Checker v5 review fixes (17 November 2026, before any real v5 run): a bold line is a section heading only when its
    text equals a section name, and any other bold line is content in every section; a Point runs from its "Point n:"
    line to the next blank line, point, or bold works-if or fails-if label; References with no numbers ("- " entries,
    from derive.py without --keep-structure) are numbered by position; R5 reads "13(6), 3341" as volume 13 and issue 6;
    S1 also accepts the host a Chrome-captured address redirected to (check_urls "reached"; "final" is unchanged).
    Derive a v5 run with inbox-triage/derive.py --keep-structure, so the numbered References and bold labels reach P3 and P4.
    Checker v5 fix (17 November 2026, after v5-d01): a reference number alone on its line ("1.", then the
    entry on the next line, as derive.py --keep-structure wrote Copilot's <li><p> items before its own fix) is read as
    that numbered entry. Only a note that was malformed before can score differently.
    Checker v5.1 (17 November 2026, after the Release 1.1 runs, --key evals/rnd/answer-key-t2-researcher-v5.1.json):
    checker v5 with two I1 changes. The tie rule: a reconcile bullet whose text, with the rows it names, matches two
    contested claims is credited to the one claim its named row ("Claim <n>", a row in Evidence for the idea) matches
    on that row's own text; with no row named, or a row that matches both claims or neither, it still covers neither.
    The key's C1 pattern accepts plurals ("styles", "modalities"). Every other item scores as on v5. Experimental
    phase: not comparable with v5 for I1.
    Add --key evals/rnd/answer-key-t2.json for the tier-2 case (K1 by URL only, L1 quote limit).

Sections are found by their heading (any level, or a line in bold) holding the key's section name.
Case for and Case against each hold exactly one table with the key's columns. Every row with a URL
is checked by check_urls.py (fetched, not a soft 404, page holds the quote), and the results go
into score.json. Exit 2 with the reason on malformed output: a missing section, a renamed column,
an unknown label, a sourced row with no URL or quote, or no table. No row is ever dropped.
"""
import json, os, re, sys, unicodedata, urllib.error, urllib.request
from urllib.parse import quote as urlquote, urlparse

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
CHIP_V5 = re.compile(r"\s*\[[^\[\]]*\|[^\[\]]*\]")  # checker v5: [n] is the citation, so only [file | PDF] chips go
CITE = re.compile(r"\[(\d+)\]")  # checker v5: a numbered citation
ROUTE_CHECKERS = ("v4.3", "v4.4", "v4.5", "v5", "v5.1")  # keys with the blocked-host route and R1 as critical
V5 = ("v5", "v5.1")  # checker v5.1 scores as v5 except the I1 tie rule


def chip():
    return CHIP_V5 if KEY.get("checker") in V5 else CHIP


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
            bold, v5 = not line.lstrip().startswith("#"), KEY.get("checker") in V5
            # checker v5 (review): the prompt allows its nine headings only, so a bold line is a heading only
            # when its text equals a section name, and any other bold line is content in every section. A bold finding
            # such as **Point 3: A one-month test is the cheap way to find out.** no longer opens One-month test.
            nxt = next((k for k, n in names.items() if (n.casefold() == h.casefold() if v5 and bold else n.casefold() in h.casefold())), None)
            if nxt is None and cur and bold and (
                    KEY.get("checker") == "v4.4" or v5 or (KEY.get("checker") == "v4.5" and cur in KEY["summary"]["sections"])):
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


def url_of(cell, refs=None):
    if refs is not None:  # checker v5: the Source cell's one [n] names a reference entry; read it before any chip step
        nums = CITE.findall(cell)
        if len(nums) > 1:
            raise Malformed(f"Source cell {cell!r} holds more than one [n]")
        if nums:
            if nums[0] not in refs:
                raise Malformed(f"Source cell {cell!r} cites [{nums[0]}], which has no entry in References")
            return refs[nums[0]]["url"]
    c = chip().sub("", cell).strip()
    m = re.search(r"\]\((https?://[^)\s]+)\)", c) or re.search(r"https?://[^\s<>\"')\]]+", c)
    if m:
        return m.group(1) if m.lastindex else m.group(0).rstrip(".,;")
    if c.strip("-–— ").casefold() in ("", "n/a", "none"):
        return ""
    raise Malformed(f"URL cell {cell!r} is neither a URL nor blank")


REF_LINE = re.compile(r"^\s*\[?(\d+)(?:\\?[.)]|\])\s+(.+)")  # "1. Entry", "1) Entry", "[1] Entry", "1\. Entry"
REF_BULLET = re.compile(r"^[-*\u2022]\s+(.+)")  # derive.py without --keep-structure writes <ol> items as "- "
REF_LONE = re.compile(r"^\s*\[?\d+(?:\\?[.)]|\])\s*$")  # "1." on its own line, the entry on the next line


def references(body):
    """Checker v5: the References section as {n: {"entry": text, "url": its first web address}}. An indented line
    continues the entry above it. When no entry carries a number (Copilot's numbered list derived without
    --keep-structure), each top-level "- " entry is numbered by its position, 1 to n. A number alone on its
    line ("1.", from <li><p> derived before the derive.py fix) joins the next non-blank line as its entry. Called on v5
    keys only (a key with a References section)."""
    lines = []
    for line in body.splitlines():
        if lines and REF_LONE.match(lines[-1]) and not REF_LONE.match(line):
            if line.strip():
                lines[-1] = lines[-1].rstrip() + " " + line.strip()
            continue
        lines.append(line)
    out, last = {}, None
    numbered = any(REF_LINE.match(line) for line in lines)
    for line in lines:
        m = REF_LINE.match(line) if numbered else REF_BULLET.match(line)
        if m:
            n = m.group(1) if numbered else str(len(out) + 1)
            if n in out:
                raise Malformed(f"References: entry {n} appears twice")
            last = n
            out[last] = {"entry": m.groups()[-1].strip()}
        elif last and line.strip() and line[:1] in (" ", "\t"):
            out[last]["entry"] += " " + line.strip()
    for e in out.values():
        urls = URL_RE.findall(e["entry"])
        e["url"] = urls[0].rstrip(".,;:") if urls else ""  # ponytail: first address; an entry naming two pages uses the first
    return out


def rows_of(name, body, refs=None):
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
        col = KEY.get("source_column", "URL")  # checker v5: the key names the column (Source)
        nums = CITE.findall(r[col]) if refs is not None else []
        r["ref"] = nums[0] if nums else None
        r["URL"] = url_of(r[col], refs)
        r["Quote"] = chip().sub("", r["Quote"]).strip()
        if r["Label"] == "sourced" and not (r["URL"] and r["Quote"].strip("-–— ")):
            raise Malformed(f"{name}: sourced row {r['#']} has no {'URL' if col == 'URL' else col + ' address'} or no quote")
        out.append(r)
    if not out:
        raise Malformed(f"{name}: table has no rows")
    return out


def score(text, round_id=None, artefact=None, text_dir=None, checker=check_urls.check, crossref=None):
    check_urls.ROUTE_ON = KEY.get("checker") in ROUTE_CHECKERS  # v4.3 review fixes (Akamai challenge) apply to route keys only
    sec = sections(text)
    refs = references(sec["references"]) if "references" in KEY["sections"] else None  # checker v5
    names = KEY["sections"]
    rows = {"for": rows_of(names["for"], sec["for"], refs), "against": rows_of(names["against"], sec["against"], refs)}
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
    if KEY.get("checker") in ("v4", "v4.1", "v4.2") + ROUTE_CHECKERS:
        items["R1"]["critical"] = True
    items["R2"] = {"pass": True, "detail": "every row labelled; every sourced row has a URL and a quote" if refs is None else
                   "every row labelled; every sourced row has a quote and a Source [n] that resolves to a reference with an address"}

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
                   "detail": f"{len(own)} sourced {names['against']} rows with a passing citation not used in the {names['for']}"}

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
    pages = []
    if "crossref" in KEY:  # checker v5
        items["R5"], pages = reference_check(refs, text_dir, checker, crossref or crossref_record)
    crit_fail = [k for k, v in items.items() if v.get("critical") and not v["pass"]]
    ok = all(v["pass"] for v in items.values())
    route = None
    if KEY.get("checker") in ROUTE_CHECKERS:  # the blocked-host route: no final score while a row awaits it
        route = check_urls.route_summary(cites + pages)  # checker v5: a refused R5 title page awaits the route too
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
            "counter_metric": cm, "citations": cites, **({"route": route} if route else {}),
            **({"references": {n: {"url": e["url"], **e.get("r5", {})} for n, e in refs.items()}} if refs is not None else {}),
            **plain_items(text)}


def plain_items(text):
    """Checker v5: plain_check.py --refs (P1 to P4), reported beside the checker's items. Not part of the checker's pass."""
    if "plain" not in KEY:
        return {}
    import plain_check
    p = {k: {"pass": ok, "detail": why} for k, (ok, why) in
         plain_check.check(text, refs=KEY["plain"].get("refs", True), end=KEY["plain"].get("summary_end", "## Appendix")).items()}
    return {"plain": {"pass": all(v["pass"] for v in p.values()), "ruler": "plain_check.py --refs", "items": p}}


DOI_RE = re.compile(r"(?:doi\.org/|\bdoi:\s*)(10\.\d{4,9}/[^\s<>\"|\]]+)", re.I)
VOL_RE = re.compile(r",\s*\*?(\d{1,5})\*?\s*(?:\((\d[^)]*)\))?\s*(?=,|\.(?:\s|$)|$)")  # ", *8*," or ", *20*(4),"


def fold(s):
    """Case, accents, tags and punctuation off, for comparing a reference element with Crossref."""
    s = unicodedata.normalize("NFKD", re.sub(r"<[^>]+>", "", s or ""))
    return check_urls.norm("".join(c for c in s if not unicodedata.combining(c)))


def crossref_record(doi):
    """Checker v5: the Crossref record for a DOI, or None when Crossref has no such DOI (404). Other errors raise."""
    req = urllib.request.Request("https://api.crossref.org/works/" + urlquote(doi, safe="/:;()<>"),
                                 headers={"User-Agent": "peakstate-executive-score_rnd/5"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)["message"]
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def entry_elements(entry):
    """The elements an APA 7 entry gives: first author's family name, year, volume, issue. None for one it leaves out."""
    plain = re.sub(r"^[*_\s]+", "", entry)
    year = re.search(r"\((\d{4})", plain)
    # ponytail: the last ", <vol>(<issue>)," before the address; a title holding ", 12," could be read as a volume
    vols = list(VOL_RE.finditer(URL_RE.sub(" ", plain)))
    # in "*13*(6), 3341." the last match is the article number. A last match with no issue that
    # follows straight on from another match is an article or page number, so the match before it is the volume.
    if len(vols) > 1 and not vols[-1].group(2) and vols[-2].end() == vols[-1].start():
        vols.pop()
    vol, issue = vols[-1].groups() if vols else (None, None)
    return {"family": plain.split(",")[0].strip("*_ "), "year": year.group(1) if year else None,
            "volume": vol or None, "issue": issue or None}


def entry_title(entry):
    """Checker v5, entries with no DOI: the title after the date, in italics or up to the first full stop."""
    rest = re.split(r"\(\d{4}[^)]*\)\.?\s*", entry, maxsplit=1)[-1]
    m = re.match(r"\*([^*]+)\*", rest) or re.match(r"(.+?)\.(?:\s|$)", rest)
    return (m.group(1) if m else rest).strip().rstrip(".")


def reference_check(refs, text_dir, checker, crossref):
    """R5. Each DOI entry against its Crossref record (title, first author's family name, year, volume, issue): every
    element the entry gives that differs, or that Crossref lacks, is listed. A DOI-less entry needs its title on its page.
    Returns (item, page checks for the route summary)."""
    faults, pages = [], []
    for n, e in sorted(refs.items(), key=lambda kv: int(kv[0])):
        m = DOI_RE.search(e["entry"])
        if not m:
            title = entry_title(e["entry"])
            if not e["url"]:
                e["r5"] = {"pass": False, "reason": "no DOI and no address"}
            else:
                c = checker({"url": e["url"], "quote": title}, text_dir)
                pages.append(c)
                e["r5"] = {"pass": c["pass"], "title": title, "reason": "title on its page" if c["pass"] else
                           f"title not found on its page ({c.get('reason')})"}
            if not e["r5"]["pass"]:
                faults.append(f"[{n}] {e['r5']['reason']}")
            continue
        doi = m.group(1).rstrip(".,;")
        if doi.endswith(")") and doi.count("(") < doi.count(")"):
            doi = doi[:-1]
        try:
            rec = crossref(doi)
        except Exception as x:  # fails closed: no record, no pass
            rec, err = None, f"Crossref unreachable ({type(x).__name__}: {x})"
        else:
            err = None if rec is not None else "DOI not in Crossref"
        if rec is None:
            e["r5"] = {"pass": False, "doi": doi, "reason": err}
            faults.append(f"[{n}] {err}")
            continue
        got, diff = entry_elements(e["entry"]), []
        titles = [t for t in rec.get("title") or [] if t]
        # ponytail: containment, so a Crossref title found inside the entry passes even with words added around it
        if not titles or fold(titles[0]) not in fold(e["entry"]):
            diff.append(f"title (Crossref {titles[0] if titles else 'has none'!r})")
        authors = rec.get("author") or []
        first = next((a for a in authors if a.get("sequence") == "first"), authors[0] if authors else {})
        fam = first.get("family") or first.get("name")
        if fold(got["family"]) != fold(fam):
            diff.append(f"first author (entry {got['family']!r}, Crossref {fam!r})")
        years = sorted({str(rec[k]["date-parts"][0][0]) for k in ("issued", "published", "published-print", "published-online")
                        if (rec.get(k) or {}).get("date-parts") and rec[k]["date-parts"][0] and rec[k]["date-parts"][0][0]})
        if got["year"] and got["year"] not in years:
            diff.append(f"year (entry {got['year']}, Crossref {', '.join(years) or 'none'})")
        for el in ("volume", "issue"):
            if got[el] and fold(got[el]) != fold(rec.get(el)):
                diff.append(f"{el} (entry {got[el]}, Crossref {rec.get(el) or 'none'})")
        e["r5"] = {"pass": not diff, "doi": doi, "differs": diff}
        faults += [f"[{n}] {d}" for d in diff]
    ok = bool(refs) and not faults
    return {"pass": ok, "detail": f"{len(refs)} reference(s) checked; " + ("every element matches Crossref or the page" if ok
            else "no references" if not refs else "differs or not found: " + "; ".join(faults))}, pages


URL_RE = re.compile(r"https?://[^\s<>\"')\]|]+")
DOMAIN_RE = re.compile(r"(?<![\w@/.-])(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,}\b", re.I)  # checker v4.5
FILE_EXT = {"pdf", "docx", "doc", "xlsx", "pptx", "csv", "txt", "md", "json", "html", "png", "jpg", "py"}


def summary_items(sec, rows):
    """Checker v4.4. S1: the summary cites only addresses in the appendix tables (sourced rows), and at least one.
    S2: summary form (section order, The answer, three cited points, works if / fails if, word cap)."""
    sk = KEY["summary"]
    v5 = KEY.get("checker") in V5
    text = "\n".join(sec[k] for k in sk["sections"])
    sourced = [r for s in ("for", "against") for r in rows[s] if r["Label"] == "sourced" and r["URL"]]
    table = {check_urls.norm(r["URL"]) for r in sourced}
    urls = [u.rstrip(".,;:") for u in URL_RE.findall(chip().sub("", text))]
    stray = sorted({u for u in urls if check_urls.norm(u) not in table})
    if KEY.get("checker") in ("v4.5",) + V5:  # a bare domain or domain-only chip must match a host in a sourced appendix row
        chk = lambda r: r.get("check") or {}  # v5: and the final host reached, or the redirect target behind a Chrome capture
        hosts = {(urlparse(u).hostname or "").removeprefix("www.") for r in sourced
                 for u in ((r["URL"], chk(r).get("final"), chk(r).get("reached")) if v5 else (r["URL"],)) if u}
        doms = {d.casefold().removeprefix("www.") for d in DOMAIN_RE.findall(URL_RE.sub(" ", text))
                if d.rsplit(".", 1)[1].casefold() not in FILE_EXT}
        stray += sorted(d for d in doms if not any(h and (h == d or h.endswith("." + d) or d.endswith("." + h)) for h in hosts))
    if v5:  # every summary [n] names a reference that a sourced row cites, and there is at least one
        nums = CITE.findall(text)
        cited = {r["ref"] for r in sourced if r.get("ref")}
        loose = sorted({n for n in nums if n not in cited}, key=int)
        s1 = {"pass": bool(nums) and not loose and not stray, "critical": True,
              "detail": f"{len(set(nums))} reference number(s) in the summary; not cited by a sourced row: {loose}; "
                        f"addresses or domains not in a sourced row: {stray}"}
    else:
        s1 = {"pass": bool(urls) and not stray, "critical": True,
              "detail": f"{len(set(urls))} address(es) in the summary; not in a sourced appendix row: {stray}"}
    lines = [ln.strip().replace("*", "").strip() for ln in sec["summary"].splitlines() if ln.strip()]
    answer = any(re.match(sk["answer"], ln, re.I) for ln in lines)
    cite = re.compile(sk["cite"]) if "cite" in sk else URL_RE  # checker v5: a point is cited by [n]
    points = []
    for n in range(1, sk["points"] + 1):
        body = " ".join(ln for ln in lines if re.match(rf"^\W*point {n}\W*:", ln, re.I))
        if v5:  # a point runs from its "Point n:" line to the next blank line, the next point, or a
            run, on = [], False  # bold "works if" or "fails if" label line (a bold "Strongest evidence:" line stays in)
            for ln in sec["summary"].splitlines():
                plain, lab = ln.strip().replace("*", "").strip(), heading(ln)
                if on and (not plain or re.match(r"^\W*point \d+\W*:", plain, re.I) or (
                        lab is not None and re.search(f"{sk['works_if']}|{sk['fails_if']}", lab, re.I))):
                    on = False
                on = on or bool(re.match(rf"^\W*point {n}\W*:", plain, re.I))
                if on:
                    run.append(plain)
            body = " ".join(run)
        points.append(bool(cite.search(body)))
    works = bool(re.search(sk["works_if"], sec["summary"], re.I))
    fails = bool(re.search(sk["fails_if"], sec["summary"], re.I))
    words = len(text.split())
    each = {k: len(sec[k].split()) for k in sk.get("max_words_each", {})}
    over = [k for k, w in each.items() if w > sk["max_words_each"][k]]
    order = list(sec) == list(KEY["sections"])
    ok = order and answer and all(points) and works and fails and words <= sk["max_words"] and not over
    caps = "".join(f"; {KEY['sections'][k]} {w} words (at most {sk['max_words_each'][k]})" for k, w in each.items())
    s2 = {"pass": ok, "summary_words": words, **({"section_words": each} if each else {}),
          "detail": f"order {'ok' if order else list(sec)}; answer {answer}; points cited {points}; works if {works}; "
                    f"fails if {fails}{caps}; summary {words} words (at most {sk['max_words']})"}
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
    cannot double up to cover two claims. The key decides what is contested, so naming none fails.
    Checker v5.1: a tie is settled by the named row's own claim, unless the bullet's own text (without
    the row) matches a different single claim than the row, in which case the tie stands unsettled.
    Known limit: this only catches a bullet whose own text names a claim outright; a bullet whose own
    text is off-topic for both claims still settles by the named row alone (review,
    17 November 2026)."""
    bullets = bullets_of(body)
    row_text = {}
    for r in rows["for"]:  # checker v4.1: Case for only
        row_text.setdefault(r["#"].strip(), []).append(r["Claim"] + " " + r["Quote"])
    form = lambda b: len(re.findall(r"\bholds when\b", b, re.I)) >= 2 or bool(re.search(r"shared assumption\s*:", b, re.I))
    if "reconcile" in KEY:  # checker v5: the two reconcile forms only
        cond, refr = (re.compile(KEY["reconcile"][f], re.I | re.S) for f in ("conditional", "reframe"))
        form = lambda b: bool(cond.search(b) or refr.search(b))
    patterns = {c["id"]: re.compile(c["match"], re.I) for c in KEY["contested"]}
    bullet_matches, settled = [], []  # (bullet text, set of contested claim ids its combined text matches)
    for b in bullets:
        refs = re.findall(r"\bclaims?\s+(\d+)", b, re.I)
        combined = b + " " + " ".join(t for n in refs for t in row_text.get(n, []))
        matched = {cid for cid, pat in patterns.items() if pat.search(combined)}
        if KEY.get("checker") == "v5.1" and len(matched) > 1:  # checker v5.1: the named row's own claim wins a tie
            own = {cid for cid in matched if any(patterns[cid].search(t) for n in refs for t in row_text.get(n, []))}
            bullet_own = {cid for cid in matched if patterns[cid].search(b)}  # the bullet's own text alone
            if len(own) == 1 and not (bullet_own and bullet_own.isdisjoint(own)):
                matched = own
                settled.append(f"Claim {', '.join(refs)} to {next(iter(own))}")
        bullet_matches.append((b, matched))
    covered, wrong_form = [], []
    for c in KEY["contested"]:
        hits = [b for b, matched in bullet_matches if matched == {c["id"]}]
        if any(form(b) for b in hits):
            covered.append(c["id"])
        elif hits:
            wrong_form.append(c["id"])
    n = len(KEY["contested"])
    tie = f" Ties settled by the named row: {settled}." if KEY.get("checker") == "v5.1" else ""
    return {"pass": len(covered) == n, "detail": f"{len(covered)} of {n} contested claims have a bullet in the asked form: {covered}; "
            f"covered but wrong form: {wrong_form}; {len(bullets)} bullet(s). Form only, not quality.{tie}"}


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
    pair = v5_self_check()
    print("score_rnd self-check: ok (tier 1, tier 2, checker v4.1, v4.2, v4.3, v4.4, v4.5 and v5, "
          + ("with the known pair)" if pair else "known pair skipped)"))
    pair = v51_self_check()
    print("score_rnd self-check: ok (checker v5.1: the v5 fixture and probes, the tie rule, C1 plurals, "
          + ("v5-d01 Claim 6, with the known pair)" if pair else "known pair or v5-d01 skipped)"))


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
        # Review fix: the match patterns need the claim's own noun, not just an everyday
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


V5_GOOD = """Research note for review.
## Executive summary
**The answer:** do not rebuild the programme around learning styles yet.
**Point 1: Matching does not help.** A controlled study found no gain. [1]
**Point 2: One small benefit exists.** It came from one visual group. [2]
**Point 3: Belief is common.** Many staff like the idea. [3]
**This works if:**
- the group is small and visual.
**It fails if:**
- results must last.
## One-month test
Who takes part: forty leaders. What they do: one workshop in two versions. What we measure: a skills check at four weeks. Stop rule: stop the idea if the matched group does no better.
## Pitch
Context: a four-week test before any spend on four versions of each workshop. Why now: the programme renews next year and the vendor quote is large. What we test: whether matching to style changes a skills check. Ask: approve the test with forty of our own leaders and no vendor spend.
## Appendix: the evidence
The tables below hold the evidence.
## Evidence for the idea
| # | Claim | Label | Source | Quote |
|---|---|---|---|---|
| 1 | Visual learners did better when the text matched their learning style | sourced | [2] | visual learners scored higher |
| 2 | Leaders like the idea | inferred | | |

I could not verify the 42% figure in your note.

## Evidence against the idea
| # | Claim | Label | Source | Quote |
|---|---|---|---|---|
| 1 | Matching to style did not help | sourced | [1] | {e1q} |
| 2 | Learning styles have little support | sourced | [3] | learning styles have little support |
| 3 | Belief in styles is common | sourced | [3] | belief in styles is common [15] |

## Where both sides are right
- Claim 1: Matching to style helps when one visual group takes an immediate test. The case against holds when results must last.
- Claim 2: Both sides assume leaders liking a format predicts learning from it. If that is not true, measure learning, not liking.
## Words used in this note
- **Learning style:** the way a person says they like to learn.
## References
1. Example, A. (2020). Matching instruction to style does not improve learning. *Journal of Examples*, *11*, Article 164. https://doi.org/10.3389/fpsyg.2020.00164
2. Sample, B., & Test, C. (2019). Text modality and learner preference. *Journal of Samples*, *10*(2), 45–67. https://doi.org/10.5555/sample.2019.2
3. Trial, D. (2021, May 3). *Why learning styles persist*. Example Review. https://a.example/review
"""
V5_CROSSREF = {  # stubbed Crossref records for V5_GOOD (invented; 10.5555 is Crossref's test prefix)
    "10.3389/fpsyg.2020.00164": {"title": ["Matching Instruction to Style Does Not Improve Learning"],
                                 "author": [{"family": "Example", "sequence": "first"}],
                                 "issued": {"date-parts": [[2020, 2, 14]]}, "volume": "11"},
    "10.5555/sample.2019.2": {"title": ["Text modality and learner preference"], "author": [{"family": "Sample"}, {"family": "Test"}],
                              "issued": {"date-parts": [[2020, 1, 9]]}, "published-print": {"date-parts": [[2019, 12]]},
                              "volume": "10", "issue": "2"}}
# Crossref's records for the prototype's six DOIs, read 17 November 2026: title, first author's family name, year, volume, issue.
PROTO_CROSSREF = {
    "10.3389/feduc.2023.1147498": ("The persistence of matching teaching and learning styles: A review of the ubiquity of this "
                                   "neuromyth, predictors of its endorsement, and recommendations to end it", "Brown", 2023, "8", None),
    "10.3389/fpsyg.2024.1428732": ("Is it really a neuromyth? A meta-analysis of the learning styles matching hypothesis",
                                   "Clinton-Lisell", 2024, "15", None),
    "10.1371/journal.pone.0320131": ("Recognizing employees’ contribution to effectiveness and values: A randomized "
                                     "waitlist-controlled trial of operant-based leadership training", "Grill", 2025, "20", "4"),
    "10.3389/fpsyg.2019.02820": ("The Interaction Between Text Modality and the Learner’s Modality Preference Influences "
                                 "Comprehension and Cognitive Load", "Lehmann", 2020, "10", None),
    "10.3390/su13063341": ("The Relationship between Learning Styles and Academic Performance: Consistency among Multiple "
                           "Assessment Methods in Psychology and Education Students", "Maya", 2021, "13", "6"),
    "10.3389/fpsyg.2020.00164": ("Providing Instruction Based on Students’ Learning Style Preferences Does Not Improve Learning",
                                 "Rogowsky", 2020, "11", None)}


def v5_self_check():
    """Checker v5: one probe per trap, then the known pair (v4-d01 and the prototype) with stubbed fetches."""
    load(os.path.join(HERE, "answer-key-t2-researcher-v5.json"))
    try:
        assert KEY["checker"] == "v5"
        e1 = KEY["known_against"][0]["evidence"]
        good = V5_GOOD.replace("{e1q}", e1["quote"])
        seen = []

        def ok(c, d=None):
            seen.append(c)
            final = "https://www.frontiersin.org/x" if "doi.org/10.3389" in c["url"] else c["url"]
            return {"url": c["url"], "quote": c["quote"], "pass": True, "reason": "fake", "route": "this Mac", "final": final}
        cr = lambda recs: (lambda doi: recs.get(doi))
        run = lambda t, chk=ok, recs=V5_CROSSREF: score(t, "t", checker=chk, crossref=cr(recs))
        s = run(good)
        assert s["pass"] and s["verdict"] == "pass" and s["checker"] == "v5", json.dumps(s["items"], indent=1)
        # (a) Source [n] resolves before any chip step, so the row is checked at its reference's address
        assert {c["url"] for c in s["citations"]} == {"https://doi.org/10.3389/fpsyg.2020.00164",
                                                      "https://doi.org/10.5555/sample.2019.2", "https://a.example/review"}
        # (b) several rows cite [3]: each row's quote is checked on that one page; a quote keeps its own [15]
        assert sorted(c["quote"] for c in s["citations"] if c["url"].endswith("/review")) == [
            "belief in styles is common [15]", "learning styles have little support"]
        # (c) every version check: R1 critical, the route record, the bold-line rule (S2 needs "works if" kept)
        bad = lambda c, d=None: {**ok(c), "pass": "a.example" not in c["url"]}
        assert "R1" in run(good, bad)["critical_failures"] and "route" in s
        refused = lambda c, d=None: {**ok(c), **({"pass": False, "refused": True} if "a.example" in c["url"] else {})}
        assert run(good, refused)["verdict"] == "awaiting route"
        assert s["items"]["S2"]["pass"] and "works if True" in s["items"]["S2"]["detail"]
        # (d) S1: a domain chip passes for the cited reference's final host, fails for an outside host and a loose [n]
        chipped = lambda c: good.replace("found no gain. [1]", f"found no gain. [1] {c}")
        assert run(chipped("[frontiersin.org]"))["items"]["S1"]["pass"]
        no_final = lambda c, d=None: {**ok(c), "final": c["url"]}
        assert not run(chipped("[frontiersin.org]"), no_final)["items"]["S1"]["pass"]
        assert not run(chipped("[outside.example]"))["items"]["S1"]["pass"]
        assert not run(good.replace("like the idea. [3]", "like the idea. [4]"))["items"]["S1"]["pass"]
        assert not run(re.sub(r" \[\d\]\n", "\n", good))["items"]["S1"]["pass"], "a summary with no [n] fails S1"
        # (e) S2: a point is cited by [n], and each section has its own cap
        s = run(good.replace("like the idea. [3]", "like the idea."))
        assert not s["items"]["S2"]["pass"] and s["items"]["S1"]["pass"]
        s = run(good.replace("Context: a four-week", "Context: " + "word " * 140 + "a four-week"))
        assert not s["items"]["S2"]["pass"] and s["items"]["S2"]["section_words"]["pitch"] > 150
        # (f) I1: the two reconcile forms; the v4 forms do not count on v5
        assert s["items"]["I1"]["pass"]
        old = good.replace("helps when one visual group takes an immediate test. The case against holds when",
                           "holds when one visual group takes an immediate test; the case against holds when").replace(
            "Both sides assume leaders liking a format predicts learning from it. If that is not true, measure learning, not liking.",
            "Shared assumption: leaders liking a format predicts learning from it.")
        assert run(old)["items"]["I1"]["detail"].startswith("0 of 2")
        # (g) malformed: an [n] with no entry, two [n] in one Source cell
        for broken in (good.replace("| sourced | [2] |", "| sourced | [9] |"), good.replace("| sourced | [2] |", "| sourced | [2][3] |")):
            try:
                run(broken)
                raise AssertionError("malformed v5 output passed")
            except Malformed:
                pass
        # (h) R5: a differing volume, an unknown DOI, Crossref down, a title not on its page; any-date year passes
        s = run(good)
        assert s["items"]["R5"]["pass"] and s["references"]["2"]["pass"], s["items"]["R5"]  # 2019 is the print year
        recs = {**V5_CROSSREF, "10.5555/sample.2019.2": {**V5_CROSSREF["10.5555/sample.2019.2"], "volume": "12", "issue": None}}
        r5 = run(good, recs=recs)["items"]["R5"]
        assert not r5["pass"] and "[2] volume (entry 10, Crossref 12)" in r5["detail"] and "[2] issue (entry 2, Crossref none)" in r5["detail"]
        assert "[1] DOI not in Crossref" in run(good, recs={})["items"]["R5"]["detail"]

        def down(doi):
            raise OSError("offline")
        assert "Crossref unreachable" in score(good, "t", checker=ok, crossref=down)["items"]["R5"]["detail"]
        no_title = lambda c, d=None: {**ok(c), "pass": c["quote"] != "Why learning styles persist"}
        assert "[3] title not found" in run(good, no_title)["items"]["R5"]["detail"]
        wrong = good.replace("Example, A. (2020).", "Exampel, A. (2021).")
        assert "[1] first author" in run(wrong)["items"]["R5"]["detail"] and "[1] year (entry 2021" in run(wrong)["items"]["R5"]["detail"]
        assert "plain" in s and set(s["plain"]["items"]) == {"P1", "P2", "P3", "P4"}
        review_probes(good, run, cr)
        ref_list_probes(good, run)
        return known_pair()
    finally:
        load(os.path.join(HERE, "answer-key.json"))


def v51_self_check():
    """Checker v5.1: the v5 fixture, its review probes and the known pair on the v5.1 key; then the tie rule and C1's
    plurals, each probe also on the v5 key, where I1 must not move; then v5-d01's own Claim 6 on both keys."""
    good = V5_GOOD.replace("{e1q}", json.load(open(os.path.join(HERE, "answer-key-t2-researcher-v5.json"),
                                                   encoding="utf-8"))["known_against"][0]["evidence"]["quote"])
    ok = lambda c, d=None: {"url": c["url"], "quote": c["quote"], "pass": True, "reason": "fake", "route": "this Mac",
                            "final": "https://www.frontiersin.org/x" if "doi.org/10.3389" in c["url"] else c["url"]}
    cr = lambda recs: (lambda doi: recs.get(doi))
    run = lambda t, chk=ok, recs=V5_CROSSREF: score(t, "t", checker=chk, crossref=cr(recs))
    tie = good.replace("assume leaders liking a format", "assume leaders liking a matched learning style")
    probes = {  # name: (note, I1 on v5.1, I1 on v5)
        "tie, row 2 names C2": (tie, "2 of 2", "1 of 2"),
        "tie, no row named": (tie.replace("- Claim 2: Both", "- Both"), "1 of 2", "1 of 2"),
        "tie, row 2 matches both": (tie.replace("| 2 | Leaders like the idea |", "| 2 | Leaders like matching to their learning style |"),
                                    "1 of 2", "1 of 2"),
        "tie, bullet argues only the other claim": (good.replace(
            "- Claim 2: Both sides assume leaders liking a format predicts learning from it. If that is not true, measure learning, not liking.",
            "- Claim 2: Both sides assume matching to a learner's style produces better recall. If that is not true, "
            "the formats cost more than they return."), "1 of 2", "1 of 2"),
        "plural styles": (good.replace("- Claim 1: Matching to style helps", "- Matching to styles helps"), "2 of 2", "1 of 2"),
        "plural modalities": (good.replace("- Claim 1: Matching to style helps", "- Matching modalities helps"), "2 of 2", "1 of 2"),
    }
    d01 = os.path.join(HERE, "rounds-researcher", "v5-d01", "output.md")
    try:
        for name, col in (("answer-key-t2-researcher-v5.1.json", 1), ("answer-key-t2-researcher-v5.json", 2)):
            load(os.path.join(HERE, name))
            for probe, row in probes.items():
                got = run(row[0])["items"]["I1"]["detail"]
                assert got.startswith(row[col]), (name, probe, got)
            if os.path.exists(d01):  # the real note: Claim 6 matches C1 and C2, and its row 6 matches C2 only
                t = open(d01, encoding="utf-8").read()
                sec = sections(t)
                refs = references(sec["references"])
                got = integration(sec["integration"], {k: rows_of(k, sec[k], refs) for k in ("for", "against")})["detail"]
                assert got.startswith("2 of 2" if col == 1 else "1 of 2"), (name, got)
                assert ("Claim 6 to C2" in got) == (col == 1), got
        load(os.path.join(HERE, "answer-key-t2-researcher-v5.1.json"))
        assert KEY["checker"] == "v5.1" and "Claim 2 to C2" in run(tie)["items"]["I1"]["detail"]
        s = run(good)
        assert s["pass"] and s["verdict"] == "pass" and s["checker"] == "v5.1", json.dumps(s["items"], indent=1)
        # every v5 version check holds on v5.1: R1 critical, the route, the bold-line rule, the chip rule for S1
        assert "R1" in run(good, lambda c, d=None: {**ok(c), "pass": "a.example" not in c["url"]})["critical_failures"]
        assert run(good, lambda c, d=None: {**ok(c), **({"pass": False, "refused": True} if "a.example" in c["url"] else {})}
                   )["verdict"] == "awaiting route"
        assert "works if True" in s["items"]["S2"]["detail"] and "route" in s
        assert "belief in styles is common [15]" in {c["quote"] for c in s["citations"]}  # a bare [n] is no chip
        assert run(good.replace("found no gain. [1]", "found no gain. [1] [frontiersin.org]"))["items"]["S1"]["pass"]
        assert not run(good.replace("found no gain. [1]", "found no gain. [1] [outside.example]"))["items"]["S1"]["pass"]
        review_probes(good, run, cr)
        ref_list_probes(good, run)
        return known_pair() and os.path.exists(d01)
    finally:
        load(os.path.join(HERE, "answer-key.json"))


def review_probes(good, run, cr):
    """Review probes (p05, p07, p07b, p08, p12, p14, p14b), kept in the self-check."""
    import tempfile
    assert run(good.replace("## References", "**References**"))["pass"]  # p05: a bold line equal to a section name opens it
    # p07, p07b: a bold finding that names a section is content, and the [n] on its next line cites the point
    own = good.replace("**Point 3: Belief is common.** Many staff like the idea. [3]",
                       "**Point 3: A one-month test would settle it.**\nMany staff like the idea. [3]")
    s = run(own)
    assert s["pass"] and "points cited [True, True, True]" in s["items"]["S2"]["detail"], s["items"]["S2"]
    assert "points cited [True, True, False]" in run(own.replace("like the idea. [3]", "like the idea."))["items"]["S2"]["detail"]
    assert run(good.replace("**Point 2: One small benefit exists.** It came",
                            "**Point 2: One small benefit exists.**\n**Strongest evidence:**\nIt came"))["items"]["S2"]["pass"]
    assert run(good.replace("## Evidence for the idea\n", "## Evidence for the idea\n**Table 1**\n"))["pass"]  # content, not a heading
    # p08: an article number after the volume is not the volume; a title's ", 2019," does not displace it
    el = lambda e: entry_elements(e + " https://doi.org/10.5555/x")
    assert el("Maya, J. (2021). T. *Sustainability*, *13*(6), 3341.") == {"family": "Maya", "year": "2021", "volume": "13", "issue": "6"}
    assert el("Lehmann, J. (2020). T. *Frontiers in Psychology*, *10*, 2820.")["volume"] == "10"
    assert el("Smith, A. (2020). Trends, 2019, and beyond. *J*, *13*.")["volume"] == "13"
    assert run(good.replace("*10*(2), 45–67.", "*10*(2), 45."))["items"]["R5"]["pass"]
    # p12: References derived without --keep-structure ("- " entries) are numbered by position
    head, tail = good.split("## References\n")
    s = run(head + "## References\n" + re.sub(r"^\d+\. ", "- ", tail, flags=re.M))
    assert s["pass"] and sorted(s["references"]) == ["1", "2", "3"], s["items"]
    # p14, p14b: a doi.org address refused by its publisher (403), Chrome text saved under either address; a summary
    # chip names the publisher's host, kept as "reached" while "final" stays the cited address
    doi1, pub1 = "https://doi.org/10.3389/fpsyg.2020.00164", "https://www.publisher.example/articles/164"
    e1 = KEY["known_against"][0]["evidence"]["quote"]
    page = " ".join((e1, "visual learners scored higher", "learning styles have little support",
                     "belief in styles is common [15]", "Why learning styles persist")) + " filler" * 450
    chipped = good.replace("found no gain. [1]", "found no gain. [1] [publisher.example]")
    for name, target in ((doi1, pub1), (pub1, pub1), (doi1, doi1)):
        fetch = lambda url: (403, target, "", "") if url == doi1 else (200, url, "Article", page)
        with tempfile.TemporaryDirectory() as td:
            open(os.path.join(td, check_urls.key(name) + ".txt"), "w", encoding="utf-8").write(page)
            s = score(chipped, "t", text_dir=td, checker=lambda c, d=None: check_urls.check(c, d, fetcher=fetch), crossref=cr(V5_CROSSREF))
        c1 = next(c for c in s["citations"] if c["url"] == doi1)
        assert c1["via"] == "chrome" and c1["pass"] and c1["final"] == doi1, c1
        if target == pub1:
            assert s["items"]["S1"]["pass"] and c1["reached"] == pub1, (s["items"]["S1"], c1)
        else:  # no redirect target known: the publisher's host is not a cited host, and no "reached" field is added
            assert not s["items"]["S1"]["pass"] and "reached" not in c1, (s["items"]["S1"], c1)


def ref_list_probes(good, run):
    """Copilot's References are <ol><li><p> items. derive.py --keep-structure puts each number on its entry's
    line (the derive fix), and references() reads a number alone on its line followed by the entry (the second guard)."""
    import importlib.util
    head, tail = good.split("## References\n")
    lone = re.sub(r"^(\d+)\. ", r"\1.\n", tail, flags=re.M)  # as derive.py --keep-structure wrote <li><p> before the fix
    s = run(head + "## References\n" + lone)
    assert s["pass"] and sorted(s["references"]) == ["1", "2", "3"], s["items"]
    assert sorted(references(lone.replace("2.\n", "2.\n\n"))) == ["1", "2", "3"]  # a blank line before the entry
    dpath = os.path.join(HERE, "..", "inbox-triage", "derive.py")
    if not os.path.exists(dpath):
        print("score_rnd v5 reference-list derive probe: skipped (no inbox-triage/derive.py)")
        return
    spec = importlib.util.spec_from_file_location("inbox_derive", dpath)
    dv = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dv)
    entries = [re.sub(r"^\d+\. ", "", e) for e in tail.strip().splitlines()]
    html = "<h2>References</h2>\n<ol>\n" + "".join(f"<li>\n<p>{e}</p>\n</li>\n" for e in entries) + "</ol>"
    derived = dv.derive(html, True)
    assert derived == "## References\n\n" + "\n\n".join(f"{i}. {e}" for i, e in enumerate(entries, 1)) + "\n", derived
    assert run(head + derived)["pass"]


def capture_path_probe(proto_md, recs):
    """Review probe p13: the prototype as Copilot's HTML (pandoc stands in for its renderer: <strong>, <ol>, compact
    tables) through inbox-triage/derive.py. Without --keep-structure every structure item passes (References numbered by
    position); with it, P1 to P4 pass as well. Pages hold each row's quote and each reference's title."""
    import importlib.util, shutil, subprocess
    dpath = os.path.join(HERE, "..", "inbox-triage", "derive.py")
    if not (shutil.which("pandoc") and os.path.exists(dpath)):
        print("score_rnd v5 capture-path probe: skipped (no pandoc or no inbox-triage/derive.py)")
        return
    spec = importlib.util.spec_from_file_location("inbox_derive", dpath)
    dv = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dv)
    html = subprocess.run(["pandoc", "-f", "markdown_strict+pipe_tables", "-t", "html", "--wrap=none"], input=proto_md,
                          capture_output=True, text=True, check=True).stdout
    html = re.sub(r"<colgroup>.*?</colgroup>", "", html, flags=re.S)
    html = re.sub(r"(<table>.*?</table>)", lambda m: re.sub(r">\s+<", "><", m.group(1)), html, flags=re.S)
    sec = sections(proto_md)
    refs = references(sec["references"])
    pages = {e["url"]: entry_title(e["entry"]) for e in refs.values()}
    for side in ("for", "against"):
        for r in rows_of(side, sec[side], refs):
            if r["URL"]:
                pages[r["URL"]] += " " + r["Quote"]
    fetch = lambda url: (200, url, "Article", pages[url] + " filler" * 450) if url in pages else (404, url, "", "not found")
    for keep in (False, True):
        s = score(dv.derive("<html><body>" + html + "</body></html>", keep), "p13",
                  checker=lambda c, d=None: check_urls.check(c, d, fetcher=fetch), crossref=lambda doi: recs.get(doi))
        assert all(v["pass"] for v in s["items"].values()), (keep, json.dumps(s["items"], indent=1))
    assert s["plain"]["pass"], s["plain"]  # --keep-structure: the numbered list and the bold labels reach plain_check


def known_pair():
    """The known pair on checker v5, with stubbed fetches: v4-d01 (a v4 note) and the plain prototype."""
    root = os.path.join(HERE, "..", "..")
    d01 = os.path.join(HERE, "rounds-researcher", "v4-d01", "output.md")
    proto = os.path.join(root, "docs", "plans", "exec-four-skills", "plain-english", "rnd-prototype.md")
    if not (os.path.exists(d01) and os.path.exists(proto)):
        print("score_rnd v5 known pair: skipped (v4-d01 or the prototype is not in this checkout)")
        return False
    t = open(d01, encoding="utf-8").read()
    try:
        score(t, "v4-d01", checker=lambda c, d=None: {"url": c["url"], "pass": True}, crossref=lambda doi: None)
        raise AssertionError("v4-d01 parsed on the v5 key")
    except Malformed as e:  # no v5 appendix sections and no References
        assert "References" in str(e) and "Evidence for the idea" in str(e), e
    assert not any(v["pass"] for v in plain_items(t)["plain"]["items"].values()), plain_items(t)
    recs = {doi: {"title": [ti], "author": [{"family": fam, "sequence": "first"}], "issued": {"date-parts": [[yr]]},
                  "volume": vol, **({"issue": iss} if iss else {})} for doi, (ti, fam, yr, vol, iss) in PROTO_CROSSREF.items()}
    ok = lambda c, d=None: {"url": c["url"], "quote": c["quote"], "pass": True, "reason": "fake", "route": "this Mac", "final": c["url"]}
    pmd = open(proto, encoding="utf-8").read()
    s = score(pmd, "rnd-prototype", checker=ok, crossref=lambda doi: recs.get(doi))
    assert all(v["pass"] for k, v in s["items"].items() if k != "R5"), json.dumps(s["items"], indent=1)
    assert s["plain"]["pass"], s["plain"]
    # Reference 4 was corrected from 2019 to 2020 in review: Crossref and the publisher's own citation give
    # 2020 (published 9 January 2020 in volume 10, labelled 2019).
    assert s["items"]["R5"]["pass"], s["items"]["R5"]
    capture_path_probe(pmd, recs)
    return True


if __name__ == "__main__":
    a = sys.argv[1:]
    if a == ["--self-check"]:
        self_check(); sys.exit(0)
    opt = lambda f: a[a.index(f) + 1] if f in a else None
    if opt("--key"):
        load(os.path.abspath(opt("--key")))
    if opt("--route-dir"):  # checker v4.3: replay the rows the route wizard fetched with the VPN off
        check_urls.load_route(opt("--route-dir"))
    md = open(a[0], encoding="utf-8").read()
    try:
        res = score(md, opt("--round"), opt("--artefact"), opt("--text-dir"))
    except Malformed as e:
        print(json.dumps({"round": opt("--round"), "key": KEY["version"], "checker": KEY.get("checker", "v3"), "pass": False,
                          "malformed": str(e), **plain_items(md)}, indent=1, ensure_ascii=False))
        sys.exit(2)
    print(json.dumps(res, indent=1))
