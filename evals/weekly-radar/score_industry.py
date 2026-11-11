#!/usr/bin/env python3
"""Score one industry round's output.md against answer-key.json. Fails closed.

    python3 evals/weekly-radar/score_industry.py <output.md> [--round rNN] [--text-dir <dir>] [--route-dir <dir>]
    python3 evals/weekly-radar/score_industry.py --self-check
    Tier 2: add --key evals/weekly-radar/answer-key-t2.json --week A (or B); the week's addendum must be committed to git.
    Ruler t2-past v3 (--key answer-key-t2-past-v3.json): as v2, plus a page with no metadata or labelled date may be
    dated by a line that holds only a day-month-year date. Not comparable with earlier rounds.
    Ruler t2-past v4 (--key answer-key-t2-past-v4.json): as v3, plus a PDF is dated from its pdftotext text by the
    same rules; its document-info or embedded XMP date is used only when the text has none. Not comparable.
    Ruler t2-past v5 (--key answer-key-t2-past-v5.json): as v4, plus a PDF is known by its Content-Type as well as its
    %PDF- prefix (check_urls.is_pdf), and an XMP CreateDate in a compressed stream is read (pdfinfo -meta). Not comparable.
    Ruler t2-past v6 (--key answer-key-t2-past-v6.json): as v5, plus a citation chip whose shortened domain holds any
    run of dots and ellipsis characters, such as [abcb.prod....bcb.gov.au], is stripped. Not comparable.
    Ruler t2-past v7 (--key answer-key-t2-past-v7.json): as v6, plus a page the script fetched with HTTP 200 whose
    text lacks the quote is checked from its Chrome text in --text-dir (chrome_text_on_miss); that text never dates a
    200 page, and a page with no date still fails T1. Not comparable.
    Ruler t2-past v9 (--key answer-key-t2-past-v9.json): as v8, plus a PDF whose text gives no date is dated from the
    release page that links that exact PDF (pdf_release_page): a breadth-first crawl of the publisher's own site from
    the PDF's path ancestors and the site's home page, at most two links deep and 2,000 pages, stopping at the first
    depth where a page links the PDF; the earliest such page dated by the HTML rules wins. Only when none is found
    does the document-info date apply. The crawl never reads the row's date. Not comparable.
    Ruler t2-past v10 (--key answer-key-t2-past-v10.json): the new table (# | Type | Date | Development | Why it matters
    to your portfolio | So what | Action | Source URL | Quote). Adds C1 (at most five industry and three AI rows; the
    key's tag decides a keyed story's type, a story tagged both counts under Copilot's label), PA1 (every row names one
    or two profile portfolio areas; a row on a key story names one it expects and none it does not), A2 (Action is
    None, "You" plus a verb phrase, or a Leadership team role) and a
    'Nothing material this week: <type>' line per empty type. The profile fixture must be committed. --legacy scores
    an answer in the v9 columns on the old items only (diagnostic). Not comparable.
    Ruler t2-past v10.1 (--key answer-key-t2-past-v10.json, version "t2-past v10.1"): as v10, plus parse_date fixes a
    crash, not a scoring rule. Every n/n/yyyy date used to be read as day/month, so a US month-first date with the
    day over 12 (such as a page metadata or row Date of 10/30/2026, meaning 30 October) raised ValueError that
    __main__ did not catch, and the run got no score. v10.1 reads n/n/yyyy as month/day only when the second field
    is over 12 and the first is 12 or under, the one unambiguous case; both fields 12 or under still default to
    day/month (Australian), an acknowledged limit on a genuinely ambiguous date; any date invalid under the chosen
    reading, or raised anywhere else in parse_date, returns None (unreadable) instead of crashing. No column, trap,
    cap, portfolio area or pass rule changed. Not comparable with t2-past v10 for a run that crashed on this bug.
    Ruler t2-past v11 (--key answer-key-t2-past-v11.json): as v10.1, plus week P2's addendum t2-past-2 v11 (a must AI
    story) and page_date_line_mdy: a page line that holds only a month-first date ("November 3, 2026") dates the page,
    as a day-first line has since v3. Holdout: holdout-past-3 v1. Not comparable.
    Ruler t2-past v11.2 (--key answer-key-t2-past-v11.2.json, ticket 41): as v11.1, plus the blocked-host second route
    (blocked_host_route, checker v4.3 in rnd/check_urls.py). A row whose host refused or stalled this Mac, and that Chrome
    text did not resolve, is awaiting route: verdict "awaiting route", pass false, route.final false, until
    rnd/blocked-host-route-wizard.sh has fetched only those rows with the VPN off and the run is re-scored with
    --route-dir <dir>. The replayed response serves both the quote check and the page date. A row still refused with the
    VPN off fails. Not comparable with v11.1 for a run with a refused row.
    Ruler t2-past v11.3 (--key answer-key-t2-past-v11.3.json, ticket 56): as v11.2, plus week P1's addendum
    t2-past-1 v11.3: W2's costs-plus-rise-verb branch and its input-costs branch refuse would, could, will, may, might,
    should, can, or expected, set, likely, going or forecast followed by to, before the verb, so a cost forecast (run t2-v7r-p1-2 row 4, "construction costs would increase") no longer maps to W2.
    Probes in v113_check. Runs after this commit score on v11.3. Not comparable with v11.2 on P1 T2 and K1 for a run
    with a cost-forecast row; nothing re-scored.
    Ruler t2-past v11.4 (--key answer-key-t2-past-v11.4.json, ticket 62): as v11.3, plus section_date: the dated section
    (a heading that holds only a date, to the next such heading) that holds the row's quote dates the page, before
    metadata; a calculated or rolling footer date (updated, modified, reviewed, edited, revised) never dates a page; a
    section whose stated coverage ends before the window is stale. Review fixes before any run: section dating needs two
    or more date-only headings (or no metadata date), a quote in two sections takes the oldest, and the footer skip is
    only for <footer> or a label-and-date line. Probes in v114_check. Runs after this commit score
    on v11.4. Not comparable with v11.3 on T1 and T3 for a row on a dated-section or footer-dated page; nothing re-scored.
    Ruler t2-past v11.5 (--key answer-key-t2-past-v11.5.json, ticket 73): as v11.4, plus joined_header: a line that holds
    a sentence and then the key's exact header is split before the header and the table is read; the split table must
    have a separator of the header's width and a row, else malformed; a sentence with pipes that is not the header is
    untouched; an ordinary table reads exactly as on v11.4 (v11.4 keys keep the old parse). Probes in v115_check; the
    v11.4 vs v11.5 parse of every saved capture in v115_recheck.py. Not comparable with v11.4 on format for a run with a
    joined header line; nothing re-scored.
    Ruler t2-past v11.6 (--key answer-key-t2-past-v11.6.json, ticket 76): as v11.5, plus two rules. spaced_slash_date:
    a labelled date (released, published, posted, issued, release date) written with spaces around the slashes
    ("Released 05 / 11 / 2026") reads as the same date with no spaces; an unlabelled spaced date and a spaced date in a
    row's Date cell are not read. trailing_chips: a table line that ends with its closing pipe and then only a run of
    citation chips ([1], [abs.gov.au], [ministers....ury.gov.au]) has that run cut; any other text after the closing
    pipe still fails, and a cut row with the wrong number of cells fails as before. Probes in v116_check; the v11.5 vs
    v11.6 parse and date of every saved capture in v116_recheck.py. Not comparable with v11.5 on T1 and T3 for a row
    on a page with a spaced labelled date, and on format for a run with chips after a closing pipe; nothing re-scored.

The output holds one table with the key's columns, or the key's "nothing material" line. Every row's
URL is checked by rnd/check_urls.py (HTTP 200, no soft 404, page holds the quote). Each source page's
own date is read from its HTML (published-time meta, JSON-LD datePublished, <time datetime>), or, when
there is none, from the row's date written on the page. Rows are mapped to key stories by source URL
first, then by the story's match pattern on the Development cell. Exit 2 with the reason on malformed
output (renamed column, more than one table, unparseable date, blank URL or quote). No row is dropped.
"""
import html
import datetime as dt, json, os, re, subprocess, sys, tempfile, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, "..", "rnd"), os.path.join(HERE, "..", "lib")]
from score import Malformed, split_row, tables  # noqa: E402
import check_urls  # noqa: E402

check_urls.ANY_LANGUAGE = False  # industry rulers up to t2-past v4 use checker v1's English-only challenge rule

KEY = json.load(open(os.path.join(HERE, "answer-key.json")))


def load(key_path, week=None):
    """Tier 2: merge one week (A or B) and its addendum into the key. Fails closed if the addendum is missing."""
    global KEY
    base = json.load(open(key_path, encoding="utf-8"))
    if "weeks" not in base:
        KEY = base
        return
    if week not in base["weeks"]:
        raise Malformed(f"tier-2 key needs --week, one of {sorted(base['weeks'])}")
    w = base["weeks"][week]
    add_path = os.path.join(os.path.dirname(os.path.abspath(key_path)), w["addendum"])
    committed = committed_at(add_path)
    if not committed:
        raise Malformed(f"week {week} addendum {w['addendum']} is missing, uncommitted or edited since its commit: write and commit it before the week's first run")
    add = json.load(open(add_path, encoding="utf-8"))
    stale = w["stale"] + add.get("stale", [])
    for s in stale:
        if not (isinstance(s, dict) and isinstance(s.get("id"), str) and isinstance(s.get("urls"), list)
                and all(isinstance(s.get(k), str) and s[k] for k in ("topic", "period"))):
            raise Malformed(f"week {week} stale item {s!r} needs id, urls (a list), topic and period")
    for st in (x for x in add["stories"] if x.get("must")):
        ev = st.get("evidence") or {}
        ok_src = ("page metadata", "page text") if base.get("page_text_date") else ("page metadata",)
        if ev.get("page_date_source") not in ok_src:
            raise Malformed(f"must story {st.get('id')}: evidence needs page_date_source in {ok_src} (require_meta_date fails any other page)")
        txt = f"{st.get('what', '')} {ev.get('quote', '')}"
        hit = next((s["id"] for s in stale if re.search(s["topic"], txt, re.I) and re.search(s["period"], txt, re.I)), None)
        if hit:
            raise Malformed(f"must story {st.get('id')}: its evidence matches stale item {hit} by topic and period")
    if base.get("story_match_exclusive"):
        # Ruler t2-past v8: each story's match pattern names its own story and no other story in the same week.
        for st in add["stories"]:
            own = f"{st.get('what', '')} {(st.get('evidence') or {}).get('quote', '')}"
            if not re.search(st["match"], own, re.I):
                raise Malformed(f"story {st['id']}: its match pattern does not match its own what or evidence quote")
            for o in add["stories"]:
                txt = f"{o.get('what', '')} {(o.get('evidence') or {}).get('quote', '')}"
                if o is not st and re.search(st["match"], txt, re.I):
                    raise Malformed(f"story {st['id']}: its match pattern also matches story {o['id']}")
    extra = v10_load(base, add["stories"], os.path.dirname(os.path.abspath(key_path))) if base.get("v10") else {}
    KEY = {**base, **extra, "window": w["window"], "stories": add["stories"], "stale": stale, "addendum_committed": committed,
           "version": f"{base['version']}; week {week} addendum {add['version']}"}


def committed_at(path):
    """Commit time of a file git tracks with no edit since its commit, else None."""
    d, name = os.path.split(path)
    git = lambda *a: subprocess.run(["git", "-C", d, *a], capture_output=True, text=True)
    when = git("log", "-1", "--format=%cI", "--", name).stdout.strip() or None if os.path.exists(path) else None
    if not when or git("ls-files", "--error-unmatch", name).returncode or git("diff", "--quiet", "HEAD", "--", name).returncode:
        return None
    return when


def v10_load(base, stories, key_dir):
    """Ruler t2-past v10: read the profile fixture's portfolio and leadership team; every story has a type tag, and every
    must story names one or more expected portfolio areas, each an exact portfolio item of the profile."""
    path = os.path.join(key_dir, base["profile"])
    when = committed_at(path)
    if not when:
        raise Malformed(f"profile fixture {base['profile']} is missing, uncommitted or edited since its commit")
    sections = dict(re.findall(r"^## (.+?)\n(.*?)(?=^## |\Z)", open(path, encoding="utf-8").read(), re.M | re.S))
    portfolio = re.findall(r"^\d+\.\s+(.+?)\s*$", sections.get("Portfolio", ""), re.M)
    actors = re.findall(r"^- (.+?):", sections.get("Leadership team", ""), re.M)
    if not portfolio or not actors:
        raise Malformed(f"profile fixture {base['profile']} needs a numbered Portfolio list and a Leadership team list")
    for st in stories:
        if st.get("type") not in ("industry", "AI", "both"):
            raise Malformed(f"story {st.get('id')}: type {st.get('type')!r} is not industry, AI or both")
        areas = st.get("areas") or []
        if st.get("must") and not areas:
            raise Malformed(f"must story {st.get('id')}: needs areas, the portfolio area or areas a row is expected to name")
        bad = [a for a in areas if a not in portfolio]
        if bad:
            raise Malformed(f"story {st.get('id')}: areas {bad} are not portfolio items in {base['profile']} ({portfolio})")
    return {"portfolio": portfolio, "actors": actors, "profile_committed": when}
DAY = dt.timedelta(days=1)
# Citation chips Copilot puts at the end of a cell: [1], or the source's domain, such as [rba.gov.au] (v1.1),
# also shortened with an ellipsis, such as [masterbuil...ers.com.au] (v1.2).
CHIP = re.compile(r"\s*\[(?:\d+|[a-z0-9-]+(?:(?:\.\.\.|…|\.)[a-z0-9-]+)+)\]", re.I)
# Ruler t2-past v6: a shortened domain whose ellipsis sits next to a dot, such as [abcb.prod....bcb.gov.au]. Any run
# of dots and ellipsis characters may join two label parts; the chip still holds only domain characters.
CHIP_RUN = re.compile(r"\s*\[(?:\d+|[a-z0-9-]+(?:[.…]+[a-z0-9-]+)+)\]", re.I)


def strip_chips(cell):
    return (CHIP_RUN if KEY.get("chip_dot_run") else CHIP).sub("", cell)
MONTHS = {m: i + 1 for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july",
                                          "august", "september", "october", "november", "december"])}
META_DATE = [r'article:published_time"\s+content="([^"]+)', r'"datePublished"\s*:\s*"([^"]+)',
             r'<time[^>]*datetime="([^"]+)']
# A labelled release date in the page text: "Released 30/10/2026", "Published: 29 October 2026". "Next Release" is not one.
TEXT_DATE = re.compile(r"(?<!next )\b(?:released|published|posted|issued|release date(?: and time)?)\s*:?\s*"
                       r"(\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2}|\d{1,2} [A-Za-z]+ \d{4}|[A-Za-z]+ \d{1,2}, \d{4})", re.I)
# Ruler t2-past v11.6 (spaced_slash_date): the same labelled date, with spaces allowed around the slashes, such as
# "Released 05 / 11 / 2026". Only the slash form gains spaces; the label is still required.
TEXT_DATE_SPACED = re.compile(TEXT_DATE.pattern.replace(r"\d{1,2}/\d{1,2}/\d{4}", r"\d{1,2} ?/ ?\d{1,2} ?/ ?\d{4}", 1), re.I)

# Ruler t2-past v3: a line that holds only a date, such as "29 October 2026" or "Thursday, 29 October 2026".
DATE_LINE = re.compile(r"(?:[A-Za-z]+day,? )?(\d{1,2} [A-Za-z]+ \d{4})")
# Ruler t2-past v11: the same, month first, such as "November 3, 2026" (a US publisher's own date line).
# The month is a full month name or a three-letter abbreviation (Sept too), then a non-letter, so "Mayor 3, 2026" is not a date.
DATE_LINE_MDY = re.compile(r"(?i)(?:[A-Za-z]+day,? )?((?:january|february|march|april|may|june|july|august|september|october|"
                           r"november|december|jan|feb|mar|apr|jun|jul|aug|sept?|oct|nov|dec)(?![A-Za-z]) \d{1,2},? \d{4})")

# Ruler t2-past v11.4: a calculated or rolling footer ("Last updated on 2026-09-24", "Page last modified: 24 September 2026")
# records an edit, not a publication, so its date never dates a page.
_ANY_DATE = r"(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}|\d{1,2} [A-Za-z]+,? \d{4}|[A-Za-z]+ \d{1,2},? \d{4})"
FOOTER_LABEL = r"\b(?:last\s+)?(?:updated|modified|reviewed|edited|revised)(?:\s+on)?\s*:?"
FOOTER = re.compile(r"(?i)" + FOOTER_LABEL + r"\s*" + _ANY_DATE)
# A line that holds only the label and the date ("Page last updated: 24 September 2026"), up to two words before the label.
FOOTER_LINE = re.compile(r"(?i)(?:[A-Za-z]+\s+){0,2}?" + FOOTER_LABEL + r"\s*" + _ANY_DATE + r"\.?")
LABEL_LINE = re.compile(r"(?i)(?:[A-Za-z]+\s+){0,2}?" + FOOTER_LABEL)


def footer_lines_out(flat, lined):
    """Ruler t2-past v11.4: (flat, lined) without each line that holds only a footer label and its date, or a date
    line under a line that holds only the label. A dated statement in a sentence stays."""
    flat = " ".join(flat.split())
    keep, prev = [], ""
    for raw in lined.split("\n"):
        line = " ".join(raw.split())
        if not line:
            continue
        drop = FOOTER_LINE.fullmatch(line) or (LABEL_LINE.fullmatch(prev) and re.fullmatch(_ANY_DATE + r"\.?", line))
        if drop:
            gone = f"{prev} {line}" if not FOOTER_LINE.fullmatch(line) else line
            flat = flat.replace(gone, " ") if gone in flat else flat.replace(line, " ")
        else:
            keep.append(line)
        prev = line
    return flat, "\n".join(keep)


# Ruler t2-past v11.4: a heading that holds only a date opens a dated section; its first lines may state the dates it covers.
DATE_HEAD = re.compile(r"(?is)<h([1-6])\b[^>]*>(.*?)</h\1>")
COVERAGE = re.compile(r"(?i)\b(?:released|published|announced|updates|covers?|covering)\b[^.]{0,40}?\b(?:between|from)\s+"
                      + _ANY_DATE + r"\s*,?\s+(?:and|to|until|through)\s+" + _ANY_DATE)


def section_date(body, quote):
    """Ruler t2-past v11.4: (date, how) from the dated section that holds the quote, else None (the v11.3 order then
    applies). A section runs from a heading that holds only a date to the next such heading. Section dating applies
    when the page has two or more such headings, or when the quote sits in a section and the page has no metadata
    date; one date-only heading never overrides page metadata. A quote in more than one section takes the oldest
    section. If that section's first 300 characters state a coverage period ("Updates released between October 28,
    2026 and November 3, 2026") that ends before the window, the section is stale and is dated by that end; otherwise
    the heading date dates the page. A quote on a page with two or more dated sections, in none of them, gets no date
    (fails closed) unless the page metadata holds a date."""
    heads = []
    for m in DATE_HEAD.finditer(body):
        t = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", m.group(2))).split())
        if (DATE_LINE.fullmatch(t) or DATE_LINE_MDY.fullmatch(t)) and parse_date(t):
            heads.append((m.start(), parse_date(t)))
    hits = []
    for (start, day), (end, _) in zip(heads, heads[1:] + [(len(body), None)]):
        text = " ".join(check_urls.html_text(body[start:end])[1].split())
        if check_urls.holds(quote, text):
            hits.append((day, text))
    meta = meta_date(body)
    if len(heads) < 2 and (meta or not hits):
        return None
    if hits:
        day, text = min(hits, key=lambda h: h[0])  # a repeat on a newest-first page never borrows a newer heading
        cover = COVERAGE.search(text[:300])
        last = parse_date(cover.group(2)) if cover else None
        if last and "window" in KEY and last < dt.date.fromisoformat(KEY["window"]["from"]):
            return last, "section coverage ends before the window"
        return day, "section heading"
    if not meta and check_urls.holds(quote, check_urls.html_text(body)[1]):
        return None, "quote outside every dated section"  # a dated-section page's newest heading is not the quote's date
    return None


def meta_date(body):
    """The page's metadata date (published-time meta, JSON-LD datePublished, <time datetime>), else None."""
    for p in META_DATE:
        m = re.search(p, body)
        if m and parse_date(m.group(1)):
            return parse_date(m.group(1))
    return None


def parse_date(s):
    """A date written as 3 November 2026, November 3, 2026, 2026-11-03, 03/11/2026 or Tue, 03/11/2026.
    Ruler t2-past v10.1: an n/n/yyyy date defaults day/month (Australian), unless the month-candidate field is
    over 12 and the day-candidate field is 12 or under, which can only be a US month/day date (unambiguous);
    a date with no valid reading either way (both fields over 12) is unreadable. An ambiguous date where both
    fields are 12 or under still reads day/month, and that stays a known limit. Any invalid calendar date
    (whichever source) returns None instead of raising."""
    s = re.sub(r"[*_]", "", s).strip()
    try:
        m = re.search(r"(\d{4})-(\d{2})-(\d{2})", s)
        if m:
            return dt.date(*map(int, m.groups()))
        m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", s)
        if m:
            f1, f2, y = int(m[1]), int(m[2]), int(m[3])
            if f2 > 12 and f1 <= 12:
                day, month = f2, f1  # unambiguous US month/day: f2 cannot be a month
            else:
                day, month = f1, f2  # day/month default (Australian); ambiguous n/n/yyyy stays a limit
            return dt.date(y, month, day)
        m = re.search(r"(\d{1,2})(?:st|nd|rd|th)? ([A-Za-z]+),? (\d{4})", s) or re.search(r"([A-Za-z]+) (\d{1,2}),? (\d{4})", s)
        if m:
            a, b, y = m.groups()
            d, mon = (a, b) if a.isdigit() else (b, a)
            mo = next((v for k, v in MONTHS.items() if k.startswith(mon.casefold()[:3])), None)
            if mo:
                return dt.date(int(y), mo, int(d))
    except ValueError:
        return None
    return None


def date_forms(d):
    m = d.strftime("%B")
    return [f"{d.day} {m} {d.year}", f"{m} {d.day}, {d.year}", f"{m} {d.day} {d.year}", d.isoformat(),
            f"{d.day:02d}/{d.month:02d}/{d.year}", f"{d.day} {m[:3]} {d.year}", f"{d.day:02d} {m[:3]} {d.year}"]


def page_date(url, row_date, text_dir=None, quote=None):
    """(date, how) for the page: its own published date, else the row's date if the page shows it, else (None, why).
    Ruler t2-past v11.4 (section_date): first the dated section that holds the row's quote (section_date)."""
    tf = os.path.join(text_dir, check_urls.key(url) + ".txt") if text_dir else None
    if tf and os.path.exists(tf) and KEY.get("chrome_text_on_miss") and check_urls.fetch(url)[0] == 200:
        tf = None  # ruler t2-past v7: Chrome text saved for a quote miss never dates a page the script fetched with 200
    if tf and os.path.exists(tf):
        body = open(tf, encoding="utf-8").read()
    else:
        if KEY.get("pdf_content_type"):  # ruler t2-past v5: check_urls' own fetch and PDF test, Content-Type included
            status, _, ctype, raw = check_urls.fetch_raw(url)
            if not isinstance(raw, bytes):
                return None, f"fetch failed: {raw or status}"
            pdf = check_urls.is_pdf(ctype, raw)
        else:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": check_urls.UA})
                raw = urllib.request.urlopen(req, timeout=30).read()
            except Exception as e:
                return None, f"fetch failed: {type(e).__name__}"
            pdf = raw[:5] == b"%PDF-"
        if KEY.get("pdf_text_date") and pdf:
            return pdf_date(raw, url)
        body = raw.decode("utf-8", "replace")
    if KEY.get("section_date") and quote:
        d = section_date(body, quote)
        if d:
            return d
    d = html_date(body)
    if d[0]:
        return d
    if KEY.get("require_meta_date"):  # tier 2: the row's own date text on the page is not proof of the page's date
        return None, "no metadata date on the page"
    text = check_urls.norm(check_urls.html_text(body)[1])
    if row_date and any(check_urls.norm(f) in text for f in date_forms(row_date)):
        return row_date, "row date shown on page"
    return None, "no published date on the page"


def html_date(body):
    """(date, how) from an HTML page's own metadata, then (by the key's flags) its text. Never the row's date."""
    if meta_date(body):
        return meta_date(body), "page metadata"
    if KEY.get("page_text_date") or KEY.get("page_date_line"):
        if KEY.get("section_date"):  # ruler t2-past v11.4: a labelled date inside <footer> never dates a page
            body = re.sub(r"(?is)<footer\b.*?</footer>",
                          lambda m: "<p>" + FOOTER.sub(" ", re.sub(r"<[^>]+>", "\n", m.group(0))) + "</p>", body)
        # lines end only at block tags and <br>; every other tag and comment joins its text to the line,
        # so a date inside a sentence never stands alone
        s = re.sub(r"(?is)<!--.*?-->|<(script|style|noscript)\b.*?</\1>", " ", body)
        s = re.sub(r"(?i)<(?:br|/?(?:p|div|li|ul|ol|h[1-6]|tr|td|th|table|section|article|header|footer|main|aside|nav|dt|dd|dl|blockquote|figure|figcaption|pre|hr))\b[^>]*>", "\n", s)
        d = text_date(check_urls.html_text(body)[1], html.unescape(re.sub(r"<[^>]+>", "", s)))
        if d[0]:
            return d
    return None, "no date on the page"


def text_date(flat, lined):
    """(date, how) from a page's text: ruler t2-past v2 labelled or standalone yyyy-mm-dd date in flat text,
    then ruler t2-past v3 a line that holds only a day-month-year date. Never a search for the row's date."""
    if KEY.get("section_date"):  # ruler t2-past v11.4: skip a line that holds only a footer label and its date
        flat, lined = footer_lines_out(flat, lined)
    if KEY.get("page_text_date"):
        raw = " ".join(flat.split())
        m = (TEXT_DATE_SPACED if KEY.get("spaced_slash_date") else TEXT_DATE).search(raw) \
            or re.search(r"(?<![\d-])(\d{4}-\d{2}-\d{2})(?![\d-])", raw)
        d = parse_date(re.sub(r" ?/ ?", "/", m.group(1))) if m else None  # ruler t2-past v11.6: "05 / 11 / 2026"
        if d:
            return d, "page text"
    if KEY.get("page_date_line"):
        for line in (" ".join(l.split()) for l in lined.split("\n")):
            if not line:
                continue
            m = DATE_LINE.fullmatch(line) or (KEY.get("page_date_line_mdy") and DATE_LINE_MDY.fullmatch(line))
            if m and parse_date(m.group(1)):
                return parse_date(m.group(1)), "page text date line"
    return None, "no date in the page text"


def site_of(host):
    """The publisher's registrable domain: the last two labels, or three under a second-level .au name."""
    p = (host or "").casefold().split(".")
    return ".".join(p[-3:] if len(p) > 2 and p[-1] == "au" and p[-2] in ("com", "gov", "org", "net", "edu", "asn", "id") else p[-2:])


def release_page(pdf_url, max_depth=2, max_pages=2000):
    """Ruler t2-past v9: (date, how) from the page on the PDF publisher's own site that links that exact PDF, else
    (None, why). Breadth-first from the PDF's path ancestors on its host and the site's home page; same-site links
    only, query strings dropped; stops at the first depth where any page links the PDF and dates those pages by the
    HTML rules, earliest first. The row's date is never read.
    ponytail: a fresh crawl per scored PDF row (about 1,300 pages, 40 s for one publisher); cache by URL if scored often."""
    import urllib.parse as up
    from concurrent.futures import ThreadPoolExecutor
    norm = lambda u: up.unquote(u.split("#")[0]).strip()
    target, sp = norm(pdf_url), up.urlsplit(pdf_url)
    site = site_of(sp.hostname)
    parts = sp.path.split("/")[:-1]
    level = [f"{sp.scheme}://{sp.netloc}" + "/".join(parts[:i]) + "/" for i in range(len(parts), 0, -1)]
    level += [f"https://www.{site}/", f"https://{site}/"]
    level = list(dict.fromkeys(level))
    seen, fetched = set(level), 0

    def get(u):
        status, final, ctype, raw = check_urls.fetch_raw(u, timeout=20)
        ok = status == 200 and isinstance(raw, bytes) and not check_urls.is_pdf(ctype, raw)
        return final, raw.decode("utf-8", "replace") if ok else ""

    def links(base, body):
        for l in re.findall(r"""href\s*=\s*(?:"([^"]*)"|'([^']*)')""", body, re.I):
            a = up.urljoin(base, html.unescape(l[0] or l[1]).strip())
            h = (up.urlsplit(a).hostname or "").casefold()
            if a.startswith("http") and (h == site or h.endswith("." + site)):
                yield a
    for depth in range(max_depth + 1):
        level = level[:max_pages - fetched]
        if not level:
            break
        with ThreadPoolExecutor(16) as ex:
            pages = list(ex.map(get, level))
        fetched += len(level)
        hits = [(u, b) for u, b in pages if any(norm(a) == target for a in links(u, b))]
        if hits:
            dated = sorted((d, u) for d, u in ((html_date(b)[0], u) for u, b in hits) if d)
            if dated:
                return dated[0][0], f"pdf release page {dated[0][1]}"
            return None, "release page found but undated"
        nxt = []
        for u, b in pages:
            for a in links(u, b):
                a = a.split("#")[0].split("?")[0]
                if a not in seen and not re.search(r"\.(pdf|jpe?g|png|gif|svg|webp|zip|docx?|xlsx?|pptx?|mp[34]|css|js|xml)$", a, re.I):
                    seen.add(a); nxt.append(a)
        level = nxt
    return None, f"no page linking the pdf in {fetched} same-site pages"


def pdf_date(raw, url=None):
    """Ruler t2-past v4: a PDF is dated from its own text (pdftotext, the same rules as HTML text). Only when the
    text has no date: the document-info CreationDate, then the first embedded XMP CreateDate."""
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        f.write(raw); f.flush()
        text = subprocess.run(["pdftotext", f.name, "-"], capture_output=True, text=True).stdout
        info = subprocess.run(["pdfinfo", "-isodates", f.name], capture_output=True, text=True).stdout
        meta = subprocess.run(["pdfinfo", "-meta", f.name], capture_output=True, text=True).stdout
    d, how = text_date(text, text)
    if d:
        return d, "pdf " + how
    if KEY.get("pdf_release_page") and url:  # ruler t2-past v9: the release page that links this exact PDF
        r = release_page(url)
        if r[0]:
            return r
    m = re.search(r"^CreationDate:\s*(\d{4}-\d{2}-\d{2})", info, re.M)
    if m:
        return parse_date(m.group(1)), "pdf document info"
    m = re.search(rb"CreateDate[^0-9]{0,40}(\d{4}-\d{2}-\d{2})", raw)
    if m:
        return parse_date(m.group(1).decode()), "pdf embedded xmp"
    if KEY.get("pdf_xmp_decoded"):  # ruler t2-past v5: XMP in a compressed stream, decoded by poppler's pdfinfo -meta
        m = re.search(r"CreateDate[^0-9]{0,40}(\d{4}-\d{2}-\d{2})", meta)
        if m:
            return parse_date(m.group(1)), "pdf xmp metadata stream"
    return None, "no date in the pdf text or metadata"


def n_sentences(cell):
    """Sentences in a cell: a split at . ! or ? followed by a space and a capital letter or a digit."""
    s = cell.strip().strip('"“”')
    return len([x for x in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9“\"])", s) if x.strip()]) if s else 0


def host_path(url):
    return url.casefold().split("://")[-1].removeprefix("www.")


def page_id(url):
    """host+path for comparing two URLs: no scheme, www, query, fragment or trailing slash."""
    return re.split(r"[?#]", host_path(url))[0].rstrip("/")


def story_of(row, groups):
    u = host_path(row["Source URL"])
    for g in groups:
        if any(u.startswith(p.casefold()) for p in g.get("urls", [])):
            return g["id"]
    for g in groups:
        if re.search(g["match"], row["Development"], re.I):
            return g["id"]
    return None


def nothing_line(text, typ):
    """Ruler t2-past v10: the line 'Nothing material this week: <type>', bold or italic marks allowed."""
    return re.search(r"nothing material this week:[*_\s]*" + re.escape(typ) + r"\b", text, re.I) is not None


SEP_CELL = re.compile(r":?-{3,}:?")
# Ruler t2-past v11.6 (trailing_chips): a table line that ends with its closing pipe and then only citation chips.
TRAILING_CHIPS = re.compile(r"^(\s*\|.*\|)(?:\s*\[(?:\d+|[a-z0-9-]+(?:[.…]+[a-z0-9-]+)+)\])+\s*$", re.I)


def cut_trailing_chips(text):
    """Ruler t2-past v11.6: cut a run of citation chips after a table line's closing pipe. Only chips are cut (a
    number or a domain, as CHIP_RUN reads them); any other text after the closing pipe is left, so the row still fails."""
    return "\n".join(TRAILING_CHIPS.sub(r"\1", l) if l.strip().startswith("|") else l for l in text.split("\n"))


def split_joined_header(text, want):
    """Ruler t2-past v11.5 (joined_header): a line that holds a sentence and then the key's exact table header is
    split before the header, so the table is read. The split table must still be whole: the next line is a separator
    of the header's width and a row follows it, else Malformed. A sentence with pipes that does not end in the exact
    header is left as it is (and fails as before if it breaks the table)."""
    lines, out = text.splitlines(), []
    for i, line in enumerate(lines):
        s = line.strip()
        for j in [m.start() for m in re.finditer(r"\|", s)] if s and not s.startswith("|") and s.endswith("|") else []:
            try:
                if [h.strip("*") for h in split_row(s[j:])] != want or not s[:j].strip():
                    continue
            except Malformed:
                continue
            nxt = lines[i + 1] if i + 1 < len(lines) else ""
            try:
                sep = split_row(nxt)
            except Malformed:
                sep = []
            if len(sep) != len(want) or not all(SEP_CELL.fullmatch(c) for c in sep):
                raise Malformed(f"joined header line: the line after the header is not a separator of {len(want)} cells: {nxt!r}")
            if i + 2 >= len(lines) or not lines[i + 2].strip().startswith("|"):
                raise Malformed("joined header line: the table has no rows")
            line = s[:j].rstrip() + "\n" + s[j:]
            break
        out.append(line)
    return "\n".join(out)


CARD_MARK = re.compile(r"^(?:[-*•>#]+\s*)*")


def card_line(line):
    """Ruler t2-past v11.7: a card line without list, heading or bold marks; returns (label, value) for a labelled line,
    else (None, plain text)."""
    t = CARD_MARK.sub("", line.strip()).replace("**", "").replace("__", "").strip()
    for lab in KEY["card_labels"]:
        m = re.match(re.escape(lab) + r"\s*:\s*(.*)$", t, re.I)
        if m:
            return lab, m.group(1).strip()
    return None, t


def parse_cards(text):
    """Ruler t2-past v11.7 (card_layout): read one card per development. A card is a title line, then the key's eight
    labelled lines, each once. Returns rows shaped as the v11.6 table rows, numbered by card order. Fails closed."""
    if tables(text):
        raise Malformed("card layout: the answer holds a table")
    lines = [card_line(l) for l in text.splitlines() if l.strip()]
    rows, i = [], 0
    while i < len(lines):
        lab, val = lines[i]
        if lab is None and i + 1 < len(lines) and lines[i + 1][0] is not None:
            title = re.sub(r"^\d+[.)]\s*", "", val).strip("*_ ")
            if not title:
                raise Malformed(f"card {len(rows) + 1}: no title line")
            card, i = {}, i + 1
            while i < len(lines) and lines[i][0] is not None:
                if lines[i][0] in card:
                    raise Malformed(f"card {len(rows) + 1}: label {lines[i][0]!r} appears twice")
                card[lines[i][0]] = lines[i][1]
                i += 1
            missing = [x for x in KEY["card_labels"] if x not in card]
            if missing:
                raise Malformed(f"card {len(rows) + 1} ({title!r}): missing {missing}")
            owner, action = card["Owner"].strip("*_ .").strip(), card["Action"].strip()
            if re.fullmatch(r"none", owner, re.I):
                act = action  # no owner: the Action line alone must be None or name who acts
            else:
                act = f"{owner}: {action}"
            rows.append({"#": str(len(rows) + 1), "Type": card["Type"], "Date": card["Date"], "Development": title,
                         "Why it matters to your portfolio": card["Why it matters to you"], "So what": card["So what"],
                         "Action": act, "Source URL": card["Source"], "Quote": card["Quote"]})
            continue
        if lab is not None:
            raise Malformed(f"card layout: labelled line {lab!r} outside a card (no title line before it)")
        i += 1
    if not rows and not all(nothing_line(text, t) for t in KEY["type_caps"]):
        raise Malformed(f"no cards and not every nothing line: {[KEY['nothing_type'].format(type=t) for t in KEY['type_caps']]}")
    return rows


def parse(text, legacy=False):
    if KEY.get("card_layout") and not legacy:  # ruler t2-past v11.7
        return [finish_row(r, False) for r in parse_cards(text)]
    if KEY.get("trailing_chips"):  # ruler t2-past v11.6
        text = cut_trailing_chips(text)
    if KEY.get("joined_header"):  # ruler t2-past v11.5
        text = split_joined_header(text, KEY["legacy_columns"] if KEY.get("v10") and legacy else KEY["columns"])
    blocks = tables(text)
    v10 = KEY.get("v10") and not legacy
    if not blocks:
        if v10:
            if all(nothing_line(text, t) for t in KEY["type_caps"]):
                return []
            raise Malformed(f"no table and not every nothing line: {[KEY['nothing_type'].format(type=t) for t in KEY['type_caps']]}")
        if KEY["nothing_material"].casefold().rstrip(".") in text.casefold():
            return []
        raise Malformed("no table and no nothing-material line")
    if len(blocks) != 1:
        raise Malformed(f"expected one table, found {len(blocks)}")
    header = [h.strip("*") for h in split_row(blocks[0][0])]
    want = KEY["legacy_columns"] if KEY.get("v10") and legacy else KEY["columns"]
    if header != want:
        raise Malformed(f"header {header} does not equal {want}")
    rows = []
    for line in blocks[0][2:]:
        cells = split_row(line)
        if len(cells) != len(header):
            raise Malformed(f"row has {len(cells)} cells: {line!r}")
        rows.append(finish_row(dict(zip(header, cells)), legacy))
    return rows


def finish_row(r, legacy):
    """Type, date, URL and quote checks for one parsed row (a table row, or a card since ruler t2-past v11.7)."""
    if KEY.get("v10") and legacy:
        # diagnostic only: a v9-column answer read as industry rows with no So what or Action
        r.update({"Type": "industry", "Why it matters to your portfolio": r.pop("Why it matters to us"), "So what": "", "Action": ""})
    elif KEY.get("v10"):
        t = {"industry": "industry", "ai": "AI"}.get(r["Type"].strip("*_ ").casefold())
        if not t:
            raise Malformed(f"row {r['#']}: Type {r['Type']!r} is not industry or AI")
        r["Type"] = t
    r["date"] = parse_date(r["Date"])
    if not r["date"]:
        raise Malformed(f"row {r['#']}: date {r['Date']!r} does not parse")
    c = strip_chips(r["Source URL"])
    m = re.search(r"\]\((https?://[^)\s]+)\)", c) or re.search(r"https?://[^\s<>\"')\]]+", c)
    if not m:
        raise Malformed(f"row {r['#']}: no URL in {r['Source URL']!r}")
    r["Source URL"] = (m.group(1) if m.lastindex else m.group(0)).rstrip(".,;")
    r["Quote"] = strip_chips(r["Quote"]).strip()
    if not r["Quote"].strip("-–— "):
        raise Malformed(f"row {r['#']}: blank quote")
    return r


def check_row(checker, cite, text_dir):
    """Ruler t2-past v7: a page the script fetched with HTTP 200 but whose text lacks the quote (for example a page
    that builds its text by script) goes to the Chrome-text route: pass only if the Chrome text in text_dir holds it."""
    c = checker(cite, text_dir)
    if not (KEY.get("chrome_text_on_miss") and not c["pass"] and c.get("via") == "script" and c.get("status") == 200
            and c.get("reason") == "page does not hold the quote"):
        return c
    tf = os.path.join(text_dir, check_urls.key(c["url"]) + ".txt") if text_dir else None
    if not (tf and os.path.exists(tf)):
        return {**c, "reason": "page does not hold the quote; no Chrome text captured"}
    text = open(tf, encoding="utf-8").read()
    if check_urls.is_challenge("", text):
        return {**c, "via": "chrome", "reason": "Chrome also got only a challenge page, not the article"}
    ok = check_urls.holds(cite["quote"], text)
    return {**c, "via": "chrome", "pass": ok,
            "reason": "Chrome text holds the quote" if ok else "neither the script page nor its Chrome text holds the quote"}


def score(text, round_id=None, text_dir=None, checker=check_urls.check, dater=page_date, legacy=False):
    check_urls.ROUTE_ON = bool(KEY.get("blocked_host_route"))  # v11.2 review fixes (Akamai, 503) apply to route keys only
    res = _score(text, round_id, text_dir, checker, dater, legacy)
    if KEY.get("blocked_host_route"):  # ruler t2-past v11.2: no final score while a row awaits the route
        res["route"] = check_urls.route_summary([o["check"] for o in res["rows"]])
        if not res["route"]["final"]:
            res.update({"pass": False, "verdict": "awaiting route"})
    return res


def _score(text, round_id=None, text_dir=None, checker=check_urls.check, dater=page_date, legacy=False):
    rows = parse(text, legacy)
    lo, hi = (dt.date.fromisoformat(KEY["window"][k]) for k in ("from", "to"))
    stories, stale = KEY["stories"], KEY["stale"]
    out = []
    for r in rows:
        c = check_row(checker, {"url": r["Source URL"], "quote": r["Quote"]}, text_dir)
        words = len(r["Quote"].strip('"“”').split())
        pd, how = (dater(r["Source URL"], r["date"], text_dir, quote=r["Quote"]) if KEY.get("section_date")
                   else dater(r["Source URL"], r["date"], text_dir))
        sid = story_of(r, stories)
        stale_id = None
        u = host_path(r["Source URL"])
        stale_id = next((s["id"] for s in stale if any(u.startswith(p.casefold()) for p in s["urls"])), None)
        review = None
        ev_url = next(((g.get("evidence") or {}).get("url") for g in stories if g["id"] == sid), None)
        if not stale_id and not (ev_url and page_id(ev_url) == page_id(u)) and "topic" in (stale[0] if stale else {}):
            # tier 2: topic AND period, never one token; only the story's own evidence page skips it, a match-regex mapping does not
            txt = r["Development"] + " " + r["Quote"]
            stale_id = next((s["id"] for s in stale if re.search(s["topic"], txt, re.I) and re.search(s["period"], txt, re.I)), None)
            review = next((s["id"] for s in stale if not stale_id and not sid and re.search(s["topic"], txt, re.I)), None)
            sid = None if stale_id else sid
        elif not stale_id and not sid:
            stale_id = next((s["id"] for s in stale if re.search(s["match"], r["Development"], re.I)), None)
        out.append({"#": r["#"], "date": r["date"].isoformat(), "url": r["Source URL"], "story": sid, "stale": stale_id,
                    "page_date": pd.isoformat() if pd else None, "page_date_how": how,
                    "date_ok": lo <= r["date"] <= hi and pd is not None and lo <= pd <= hi and abs(pd - r["date"]) <= DAY,
                    "stale_topic_only": review, "quote_words": words, "check": c,
                    "sentences": {col: n_sentences(r[col]) for col in KEY.get("one_sentence", [])},
                    "r1": c["pass"] and words <= KEY["max_quote_words"]})
        if KEY.get("v10"):
            out[-1].update(v10_row(r, sid))
    if KEY.get("v10"):
        return v10_score(text, round_id, out, legacy)
    items = {}
    items["R1"] = {"pass": all(o["r1"] for o in out), "critical": True,
                   "detail": f"{sum(o['r1'] for o in out)} of {len(out)} rows: page holds the quote, quote of {KEY['max_quote_words']} words or fewer"}
    bad_t1 = [o["#"] for o in out if not o["date_ok"] or o["stale"]]
    items["T1"] = {"pass": not bad_t1, "critical": True, "detail": f"stale, out-of-window or undated rows: {bad_t1}"}
    seen = [o["story"] for o in out if o["story"]]
    dups = sorted({s for s in seen if seen.count(s) > 1})
    items["T2"] = {"pass": not dups, "critical": True, "detail": f"stories counted more than once: {dups}"}
    unkeyed = [o["#"] for o in out if not o["story"]]
    items["T3"] = {"pass": len(out) <= KEY["max_rows"] and items["R1"]["pass"] and items["T1"]["pass"], "critical": True,
                   "detail": f"{len(out)} rows (limit {KEY['max_rows']}); unkeyed rows passing every check, for review: {unkeyed}"}
    if KEY.get("one_sentence"):
        multi = [f"{o['#']} {col}" for o in out for col, n in o["sentences"].items() if n != 1]
        items["S1"] = {"pass": not multi, "detail": f"cells that are not one sentence: {multi}"}
    must = [s["id"] for s in stories if s["must"]]
    items["K1"] = {"pass": all(m in seen for m in must), "detail": f"must stories found: {[m for m in must if m in seen]} of {must}"}
    items["F1"] = {"pass": True, "detail": "table parses" if out else "nothing-material line"}
    extra = {"addendum_committed": KEY["addendum_committed"]} if "addendum_committed" in KEY else {}
    return {"round": round_id, "key": KEY["version"], **extra, "pass": all(v["pass"] for v in items.values()),
            "critical_failures": [k for k, v in items.items() if v.get("critical") and not v["pass"]],
            "items": items, "counter_metric": {"items_reported": len(out), "words_of_output": len(text.split())},
            "rows": out}


def v10_row(r, sid):
    """Ruler t2-past v10 row fields. The key's tag decides the type of a keyed story; a story tagged both, or a row no
    story matched, keeps Copilot's label. Copilot's label never decides which story a row matches."""
    st = next((g for g in KEY["stories"] if g["id"] == sid), {})
    typ = st["type"] if st.get("type") in ("industry", "AI") else r["Type"]
    norm = lambda x: " ".join(x.replace("’", "'").casefold().split())
    want = st.get("areas") or []
    why = norm(strip_chips(r["Why it matters to your portfolio"]))
    named = [a for a in KEY["portfolio"] if norm(a) in why]
    # PA1: one or two profile areas; on a story the key gives areas, at least one expected and none it does not expect.
    # An unkeyed row (or a story with no areas) still names one or two profile areas.
    pa1 = 1 <= len(named) <= 2 and (not want or (any(a in want for a in named) and all(a in want for a in named)))
    act = strip_chips(r["Action"]).strip().strip("*_ ").rstrip(".").strip("*_ ")
    # A2: None (a short reason may follow), "You" plus a verb phrase of two or more words, or a Leadership team role.
    a2 = (re.match(r"none\b", act, re.I) is not None and len(act.split()) <= 12
          or re.match(r"you\b[\s:,;-]*\w+\W+\w+", act, re.I) is not None
          or any(re.search(r"\b" + re.escape(a) + r"\b", act, re.I) for a in KEY["actors"]))
    return {"label": r["Type"], "type": typ, "areas": named, "pa1": pa1, "a2": a2}


def v10_score(text, round_id, out, legacy):
    """Ruler t2-past v10 items. Each failed item carries 'cause': the types (by the key's tag) of the rows or stories
    that failed it, so a failed run is logged as an industry rule or an AI rule."""
    stories = KEY["stories"]
    stype = {g["id"]: g["type"] for g in stories}
    caps = KEY["type_caps"]
    items = {}

    def item(k, bad, detail, critical=False, cause=None):
        items[k] = {"pass": not bad, **({"critical": True} if critical else {}), "detail": detail}
        if bad:
            items[k]["cause"] = sorted(set(cause if cause is not None else [o["type"] for o in out if o["#"] in bad]))
    bad = [o["#"] for o in out if not o["r1"]]
    item("R1", bad, f"{len(out) - len(bad)} of {len(out)} rows: page holds the quote, quote of {KEY['max_quote_words']} words or fewer", True)
    item("T1", [o["#"] for o in out if not o["date_ok"] or o["stale"]], f"stale, out-of-window or undated rows: {[o['#'] for o in out if not o['date_ok'] or o['stale']]}", True)
    seen = [o["story"] for o in out if o["story"]]
    dups = sorted({s for s in seen if seen.count(s) > 1})
    item("T2", dups, f"stories counted more than once: {dups}", True, [stype[s] for s in dups])
    limit = caps["industry"] if legacy else KEY["max_rows"]
    unkeyed = [o["#"] for o in out if not o["story"]]
    t3 = len(out) <= limit and items["R1"]["pass"] and items["T1"]["pass"]
    item("T3", not t3, f"{len(out)} rows (limit {limit}); unkeyed rows passing every check, for review: {unkeyed}", True,
         [o["type"] for o in out if not o["r1"] or not o["date_ok"] or o["stale"]] or [o["type"] for o in out])
    multi = [f"{o['#']} {col}" for o in out for col, n in o["sentences"].items() if n != 1]
    item("S1", multi, f"cells that are not one sentence: {multi}", cause=[o["type"] for o in out if any(n != 1 for n in o["sentences"].values())])
    musts = [g for g in stories if g["must"] and (not legacy or g["type"] in ("industry", "both"))]
    missed = [g["id"] for g in musts if g["id"] not in seen]
    item("K1", missed, f"must stories found: {[g['id'] for g in musts if g['id'] in seen]} of {[g['id'] for g in musts]}",
         cause=[stype[m] for m in missed])
    by_type = {t: sum(o["type"] == t for o in out) for t in caps}
    if legacy:
        item("F1", [], "table parses (legacy v9 columns, diagnostic only)" if out else "nothing-material line")
    else:
        over = [t for t in caps if by_type[t] > caps[t]]
        item("C1", over, f"rows by type (the key's tag decides a keyed story): {by_type}; caps {caps}", True, over)
        bad = [o["#"] for o in out if not o["pa1"]]
        item("PA1", bad, f"rows naming no profile portfolio area, more than two, or an area their key story does not expect"
                         f" (a keyed story needs one it expects): {bad}")
        bad = [o["#"] for o in out if not o["a2"]]
        item("A2", bad, f"Action cells that are neither None nor name who acts: {bad}")
        lines = {t: nothing_line(text, t) for t in caps}
        wrong = [t for t in caps if lines[t] == any(o["label"] == t for o in out)]
        item("F1", wrong, f"table parses; types whose nothing line is missing or contradicts a row: {wrong}", cause=wrong)
    found = {t: f"{sum(g['id'] in seen for g in musts if g['type'] == t)} of {sum(g['type'] == t for g in musts)}"
             for t in list(caps) + (["both"] if any(g["type"] == "both" for g in musts) else [])}
    extra = {k: KEY[k] for k in ("addendum_committed", "profile_committed") if k in KEY}
    return {"round": round_id, "key": KEY["version"], **({"legacy": True} if legacy else {}), **extra,
            "pass": all(v["pass"] for v in items.values()),
            "critical_failures": [k for k, v in items.items() if v.get("critical") and not v["pass"]],
            "failure_cause": sorted({c for v in items.values() for c in v.get("cause", [])}),
            "items": items, "counter_metric": {"items_reported": len(out), "items_by_type": by_type,
                                               "must_found_by_type": found, "words_of_output": len(text.split())},
            "rows": out}


def self_check():
    assert parse_date("3 November 2026") == dt.date(2026, 11, 3) == parse_date("**Nov 3, 2026**") == parse_date("2026-11-03T14:30+11:00")
    assert parse_date("Tue, 03/11/2026 - 11:30") == dt.date(2026, 11, 3) and parse_date("last week") is None
    # Ruler t2-past v10.1: a US month/day date with a day over 12 reads correctly instead of crashing; the
    # equivalent day/month date is unchanged; a date invalid either way is unreadable, not a crash.
    assert parse_date("10/30/2026") == dt.date(2026, 10, 30)
    assert parse_date("30/10/2026") == dt.date(2026, 10, 30)
    assert parse_date("13/13/2026") is None
    head = "| # | Date | Development | Why it matters to us | Source URL | Quote |\n|---|---|---|---|---|---|\n"
    rba = "| 1 | 3 November 2026 | Reserve Bank lifts the cash rate to 4.85% | Dearer loans for buyers | https://www.rba.gov.au/media-releases/2026/mr-26-30.html | increase the cash rate target [1] |\n"
    abs_ = "| 2 | 2 November 2026 | Dwelling approvals rose 5.1% | Fewer house approvals | [ABS](https://www.abs.gov.au/statistics/industry/building-and-construction/building-approvals-australia/latest-release) | Total dwellings approved rose 5.1% |\n"
    ok = lambda c, d=None: {"pass": True, "reason": "fake"}
    good_date = lambda u, d, t=None: (d, "fake")
    seen_q = []
    s = score(head + rba.replace("target [1]", "target [rba.gov.au]") + abs_, "t",
              checker=lambda c, d=None: seen_q.append(c["quote"]) or ok(c), dater=good_date)
    assert seen_q[0] == "increase the cash rate target", seen_q
    seen_q.clear()
    score(head + rba.replace("target [1]", "target [masterbuil...ers.com.au]") + abs_, checker=lambda c, d=None: seen_q.append(c["quote"]) or ok(c), dater=good_date)
    assert seen_q[0] == "increase the cash rate target", seen_q
    chip_check()
    miss_check()
    pc = "| 3 | 5 November 2026 | Interim proposals on insolvency pathways for small business | x | https://pc.example/interim | q |\n"
    assert score(head + rba + abs_ + pc, checker=ok, dater=good_date)["items"]["T1"]["pass"]  # key v1.1: S3 anchored
    s = score(head + rba + abs_, "t", checker=ok, dater=good_date)
    assert s["pass"], json.dumps(s["items"], indent=1)
    assert [o["story"] for o in s["rows"]] == ["W1", "W2"] and s["counter_metric"]["items_reported"] == 2
    echo = rba.replace("| 1 |", "| 3 |").replace("https://www.rba.gov.au/media-releases/2026/mr-26-30.html", "https://news.example/rates")
    s = score(head + rba + abs_ + echo, checker=ok, dater=good_date)
    assert not s["items"]["T2"]["pass"] and "T2" in s["critical_failures"]
    cpi = "| 3 | 4 November 2026 | New dwelling prices up 4.7% in a year | Costs | https://news.example/cpi | prices rose |\n"
    s = score(head + rba + abs_ + cpi, checker=ok, dater=good_date)
    assert not s["items"]["T1"]["pass"] and s["rows"][2]["stale"] == "L1"
    old = abs_.replace("2 November 2026", "29 October 2026")
    assert not score(head + rba + old, checker=ok, dater=good_date)["items"]["T1"]["pass"]
    assert not score(head + rba + abs_, checker=ok, dater=lambda u, d, t=None: (None, "none"))["items"]["T1"]["pass"]
    assert not score(head + rba + abs_, checker=ok, dater=lambda u, d, t=None: (d - 5 * DAY, "meta"))["items"]["T1"]["pass"]
    long_q = rba.replace("increase the cash rate target", " ".join(["word"] * 31))
    assert not score(head + long_q + abs_, checker=ok, dater=good_date)["items"]["R1"]["pass"]
    extra = "".join(f"| {i} | 4 November 2026 | Other news {i} | x | https://o.example/{i} | q |\n" for i in range(3, 7))
    s = score(head + rba + abs_ + extra, checker=ok, dater=good_date)
    assert not s["items"]["T3"]["pass"]
    assert not score(head + rba, checker=ok, dater=good_date)["items"]["K1"]["pass"]
    assert score("Nothing material this week.", checker=ok, dater=good_date)["counter_metric"]["items_reported"] == 0
    for broken in (head.replace("| Quote |", "| Source |") + rba, head + rba.replace("3 November 2026", "this week"),
                   head + rba.replace("https://www.rba.gov.au/media-releases/2026/mr-26-30.html", "RBA"), "No table here.",
                   head + rba + "\n\n" + head + abs_):
        try:
            score(broken, checker=ok, dater=good_date)
            raise AssertionError(f"malformed output passed: {broken[:60]!r}")
        except Malformed:
            pass
    t2_self_check()
    v10_check()
    v11_check()
    v112_check()
    v113_check()
    v114_check()
    v115_check()
    v116_check()
    v117_check()
    print("score_industry self-check: ok (tier 1, tier 2, v10, v11, v11.2, v11.3, v11.4, v11.5, v11.6 and v11.7)")


def saved_captures():
    """The saved practice captures (rounds-t2/<run>/output.md). The public evals folder ships without them, so the
    capture probes below are skipped there and only the synthetic probes run."""
    d = os.path.join(HERE, "rounds-t2")
    return os.listdir(d) if os.path.isdir(d) else []


JOINED = ["t2-p1-1", "t2-v2-p1-1", "t2-v3k3-p1-3", "t2-v8-p1-2"]  # the saved captures v11.4 refused for a joined header line


def capture_parse(run, key_file, legacy=None):
    """Ruler t2-past v11.5 probe helper: parse (never score) a saved practice capture on a ruler. A capture in the v9
    columns is read with --legacy, the only way a v10 key reads those columns. Returns the rows or the Malformed text."""
    load(os.path.join(HERE, key_file), "P2" if "-p2-" in run else "P1")
    text = open(os.path.join(HERE, "rounds-t2", run, "output.md"), encoding="utf-8").read()
    if legacy is None:
        legacy = "| Type |" not in text
    try:
        return [{k: v for k, v in r.items() if k != "date"} for r in parse(text, legacy)]
    except Malformed as e:
        return f"malformed: {e}"


def v115_check():
    """Ruler t2-past v11.5: a line with a sentence and then the exact header is split before the header; a broken table
    still fails; a sentence with pipes is never read as a header; every other capture parses as on v11.4."""
    global KEY
    saved = KEY
    v114 = json.load(open(os.path.join(HERE, "answer-key-t2-past-v11.4.json"), encoding="utf-8"))
    v115 = json.load(open(os.path.join(HERE, "answer-key-t2-past-v11.5.json"), encoding="utf-8"))
    own = {"version", "previous_version", "ruler_change", "comparable", "joined_header"}
    assert v115["joined_header"] is True and "joined_header" not in v114
    assert not [f for f in set(v114) | set(v115) if f not in own and v114.get(f) != v115.get(f)]  # only the parse rule moved
    head = "| " + " | ".join(v115["columns"]) + " |"
    sep = "|" + "---|" * len(v115["columns"])
    row = lambda n, w="30 October 2026": f"| {n} | industry | {w} | Builders face higher costs. | Pricing is exposed. | Margins may tighten. | None | https://news.example/{n} | costs rose |"
    lead = "The Weekly Industry and AI Scan is complete."
    body = "\n".join([sep, row(1), row(2)]) + "\n"
    plain, joined = f"{lead}\n\n{head}\n{body}", f"{lead} {head}\n{body}"
    ok = lambda c, d=None: {"pass": True, "reason": "fake"}
    good_date = lambda u, d, t=None, quote=None: (d, "fake")
    n = {"synthetic": 0, "captures": 0}

    def fails(text, why):
        try:
            parse(text)
        except Malformed:
            n["synthetic"] += 1
            return
        raise AssertionError(f"v11.5: {why} parsed")
    try:
        load(os.path.join(HERE, "answer-key-t2-past-v11.4.json"), "P1")
        fails(joined, "v11.4 behaviour kept: a joined header line")  # v11.4 stays selectable by its key
        v114_plain = parse(plain)
        load(os.path.join(HERE, "answer-key-t2-past-v11.5.json"), "P1")
        # a joined header line reads as the same table, and scores the same (so must stories found is unchanged)
        assert parse(joined) == parse(plain) == v114_plain and len(v114_plain) == 2
        s1, s2 = (score(x, "p", checker=ok, dater=good_date) for x in (joined, plain))
        assert s1 == s2 and s1["counter_metric"] == s2["counter_metric"]
        n["synthetic"] += 2
        assert parse(f"**{lead}** {head.replace('| Quote |', '| **Quote** |')}\n{body}") == v114_plain  # bold marks
        assert parse(f"Week 44 | the scan. {head}\n{body}") == v114_plain, "a pipe in the sentence before the header"
        n["synthetic"] += 2
        # broken tables still fail: separator malformed, narrow, missing; ragged rows; header with no rows
        fails(f"{lead} {head}\n|--|--|--|--|--|--|--|--|--|\n{row(1)}\n", "a separator of two-hyphen cells")
        fails(f"{lead} {head}\n|---|---|---|\n{row(1)}\n", "a separator narrower than the header")
        fails(f"{lead} {head}\n|---|abc|---|---|---|---|---|---|---|\n{row(1)}\n", "a separator with a text cell")
        fails(f"{lead} {head}\n{row(1)}\n", "a joined header with no separator")
        fails(f"{lead} {head}\n{sep}\n{row(1)[:-2].rsplit('|', 1)[0]}|\n", "a ragged row (one cell short)")
        fails(f"{lead} {head}\n{sep}\n{row(1)} extra |\n", "a ragged row (one cell over)")
        fails(f"{lead} {head}\n{sep}\n", "a header with no rows at the end")
        fails(f"{lead} {head}\n{sep}\n\nNothing material this week: industry\nNothing material this week: AI\n", "a header with no rows before text")
        fails(f"{lead} {head.replace('| Quote |', '| Source quote |')}\n{body}", "a joined renamed header")
        # an ordinary passing table is read exactly as on v11.4 (and the next probe's sentence keeps its pipes)
        assert parse(plain) == v114_plain
        # negative: a real sentence with pipes is not a header, so it is left as text and the table below is read
        pipes = "Costs rose | see the note | below |"
        assert split_joined_header(pipes, v115["columns"]) == pipes
        assert parse(f"{pipes}\n\n{head}\n{body}") == v114_plain
        n["synthetic"] += 3
        # every saved practice capture: the four joined lines now parse with rows; every other capture is unchanged
        for run in sorted(r for r in saved_captures() if r.startswith("t2-")):
            a, b = capture_parse(run, "answer-key-t2-past-v11.4.json"), capture_parse(run, "answer-key-t2-past-v11.5.json")
            if run in JOINED:
                # v11.5 reads past the header, but each of these captures also ends its last row with the citation
                # chips after the closing pipe (the table was one paragraph), so it still fails, as a broken table must
                assert isinstance(a, str) and "header ['---" in a, (run, a)
                assert isinstance(b, str) and "row does not start and end with a pipe" in b, (run, b)
                # probe only, no ruler change: with that chip run cut in memory, the split capture reads with rows
                text = open(os.path.join(HERE, "rounds-t2", run, "output.md"), encoding="utf-8").read()
                cut = re.sub(r"(?m)^(\|.*\|)(?:\s*\[[^\]\n]+\])+\s*$", r"\1", text)
                load(os.path.join(HERE, "answer-key-t2-past-v11.5.json"), "P1")
                assert parse(cut, "| Type |" not in text), run
                load(os.path.join(HERE, "answer-key-t2-past-v11.4.json"), "P1")
                try:
                    parse(cut, "| Type |" not in text); raise AssertionError(f"v11.4 read the joined capture {run}")
                except Malformed:
                    pass
            else:
                assert a == b, (run, a, b)
            n["captures"] += 1
        assert not saved_captures() or n["captures"] >= 25, n  # 25 at ticket 73; ticket 74 added four captures (none joined)
    finally:
        KEY = saved
    return n


def v116_check():
    """Ruler t2-past v11.6: a labelled date with spaces around the slashes dates a page; a run of citation chips after a
    table line's closing pipe is cut; anything else after the closing pipe still fails; v11.5 behaviour is kept."""
    global KEY
    saved = KEY
    v115 = json.load(open(os.path.join(HERE, "answer-key-t2-past-v11.5.json"), encoding="utf-8"))
    v116 = json.load(open(os.path.join(HERE, "answer-key-t2-past-v11.6.json"), encoding="utf-8"))
    own = {"version", "previous_version", "ruler_change", "comparable", "spaced_slash_date", "trailing_chips"}
    assert v116["spaced_slash_date"] is True and v116["trailing_chips"] is True
    assert "spaced_slash_date" not in v115 and "trailing_chips" not in v115
    assert not [f for f in set(v115) | set(v116) if f not in own and v115.get(f) != v116.get(f)]  # only the two rules moved
    n = {"dating": 0, "parsing": 0, "captures": 0}
    page = lambda line: f"<html><body><h1>Interim report</h1><p>{line}</p><p>The processes of businesses setting up.</p></body></html>"
    head = "| " + " | ".join(v116["columns"]) + " |"
    sep = "|" + "---|" * len(v116["columns"])
    row = lambda i: f"| {i} | industry | 30 October 2026 | Builders face higher costs. | Pricing is exposed. | Margins may tighten. | None | https://news.example/{i} | costs rose |"
    plain = "\n".join(["The scan is complete.", "", head, sep, row(1), row(2)]) + "\n"
    ok = lambda c, d=None: {"pass": True, "reason": "fake"}
    good_date = lambda u, d, t=None, quote=None: (d, "fake")

    def fails(text, why):
        try:
            parse(text)
        except Malformed:
            n["parsing"] += 1
            return
        raise AssertionError(f"v11.6: {why} parsed")
    try:
        # (i) dating: the row 3 form, read on v11.6 only; the unspaced form is the same on both rulers
        cases = [("Released 05 / 11 / 2026", None, dt.date(2026, 11, 5)),
                 ("Released 05/11/2026", dt.date(2026, 11, 5), dt.date(2026, 11, 5)),
                 ("Published: 5 /11/ 2026", None, dt.date(2026, 11, 5)),
                 ("Released 10 / 30 / 2026", None, dt.date(2026, 10, 30)),  # the v10.1 month/day rule still applies
                 ("05 / 11 / 2026", None, None),  # no label: not read
                 ("Next release 05 / 11 / 2026", None, None),  # a next release is not a release date
                 ("Released 05 /  / 2026", None, None),
                 ("Released 05 - 11 - 2026", None, None)]
        for line, want115, want116 in cases:
            KEY = v115
            a = html_date(page(line))[0]
            KEY = v116
            b = html_date(page(line))[0]
            assert (a, b) == (want115, want116), (line, a, b)
            n["dating"] += 1
        # metadata still comes first, and a footer label line is still skipped
        KEY = v116
        meta = page("Released 05 / 11 / 2026").replace("<body>", '<head><meta property="article:published_time" content="2026-10-01"></head><body>')
        assert html_date(meta) == (dt.date(2026, 10, 1), "page metadata")
        assert html_date(page("Last updated: 05 / 11 / 2026"))[0] is None
        n["dating"] += 2
        # a spaced date in a row's Date cell is not read (the rule is for a labelled page date only)
        load(os.path.join(HERE, "answer-key-t2-past-v11.6.json"), "P1")
        fails(plain.replace("| 1 | industry | 30 October 2026 |", "| 1 | industry | 30 / 10 / 2026 |"), "a spaced Date cell")
        # (ii) parsing: chips after the closing pipe
        chips = " [abs.gov.au] [ministers....ury.gov.au] [abcb.prod....bcb.gov.au] [1]"
        last = plain.rstrip("\n") + chips + "\n"
        every = "\n".join(l + chips if l.startswith("| 1") or l.startswith("| 2") else l for l in plain.split("\n"))
        load(os.path.join(HERE, "answer-key-t2-past-v11.5.json"), "P1")
        base = parse(plain)
        fails(last, "v11.5 behaviour kept: chips after the closing pipe")
        load(os.path.join(HERE, "answer-key-t2-past-v11.6.json"), "P1")
        assert parse(last) == parse(every) == parse(plain) == base and len(base) == 2
        s1, s2 = (score(x, "p", checker=ok, dater=good_date) for x in (last, plain))
        wo = lambda r: {**r, "counter_metric": {k: v for k, v in r["counter_metric"].items() if k != "words_of_output"}}
        assert wo(s1) == wo(s2), "chips after the pipe scored differently"  # must stories found is unchanged
        # words_of_output counts the whole answer as written, chips included, as it does for chips inside a cell
        assert cut_trailing_chips(plain) == plain
        n["parsing"] += 3
        # broken tables still fail on v11.6
        fails(plain.rstrip("\n") + " see the note\n", "text after the closing pipe")
        fails(plain.rstrip("\n") + " [abs.gov.au] see the note\n", "chips and then text after the closing pipe")
        fails(plain.rstrip("\n") + " [note]\n", "a bracket that is not a chip")
        fails(plain.rstrip("\n") + " [abs.gov.au], [rba.gov.au]\n", "chips joined by a comma")
        fails(plain.replace(" costs rose |\n", " costs rose [abs.gov.au]\n", 1), "a row with no closing pipe")
        fails(plain.replace(row(2), row(2).rsplit(" costs rose |", 1)[0] + chips), "a row one cell short once the chips are cut")
        fails(plain.replace(row(2), row(2).rsplit(" costs rose |", 1)[0] + "| [abs.gov.au] |"), "a chip as the last cell")
        # every saved practice capture: the four joined captures now parse with rows; every other capture is unchanged
        for run in sorted(r for r in saved_captures() if r.startswith("t2-")):
            a, b = capture_parse(run, "answer-key-t2-past-v11.5.json"), capture_parse(run, "answer-key-t2-past-v11.6.json")
            if run in JOINED:
                assert isinstance(a, str) and "row does not start and end with a pipe" in a, (run, a)
                assert isinstance(b, list) and b, (run, b)
                text = open(os.path.join(HERE, "rounds-t2", run, "output.md"), encoding="utf-8").read()
                cut = re.sub(r"(?m)^(\|.*\|)(?:\s*\[[^\]\n]+\])+\s*$", r"\1", text)  # ticket 73's in-memory probe cut
                load(os.path.join(HERE, "answer-key-t2-past-v11.5.json"), "P1")
                assert [{k: v for k, v in r.items() if k != "date"} for r in parse(cut, "| Type |" not in text)] == b, run
            else:
                assert a == b, (run, a, b)
            n["captures"] += 1
        assert not saved_captures() or n["captures"] >= 29, n
    finally:
        KEY = saved
    return n


def v117_check():
    """Ruler t2-past v11.7: a card answer reads as the same rows and scores the same items as the v11.6 table answer;
    broken cards fail closed; every saved table capture is refused on v11.7."""
    global KEY
    saved = KEY
    v116 = json.load(open(os.path.join(HERE, "answer-key-t2-past-v11.6.json"), encoding="utf-8"))
    v117 = json.load(open(os.path.join(HERE, "answer-key-t2-past-v11.7.json"), encoding="utf-8"))
    own = {"version", "previous_version", "ruler_change", "comparable", "card_layout", "card_labels"}
    assert v117["card_layout"] is True and "card_layout" not in v116
    assert not [f for f in set(v116) | set(v117) if f not in own and v116.get(f) != v117.get(f)]  # only the layout moved
    n = {"cards": 0, "broken": 0, "captures": 0}
    area = "Estimating and contract pricing"
    head = "| " + " | ".join(v116["columns"]) + " |"
    sep = "|" + "---|" * len(v116["columns"])
    rows = [("industry", "30 October 2026", "Builders face higher costs", "Head of Estimating: update the cost book", 1),
            ("AI", "31 October 2026", "A rival uses an AI estimating tool", "None", 2)]
    table = "\n".join(["The scan is complete.", "", head, sep] + [
        f"| {i} | {t} | {d} | {dev}. | {area} is exposed. | Margins may tighten. | {act} | https://news.example/{i} | costs rose |"
        for t, d, dev, act, i in rows]) + "\n"

    def cards(title=lambda i, dev: f"**{i}. {dev}**", mark="", drop=None, extra=None):
        out = ["Summary", "- Costs rose.", "- A rival moved on AI.", ""]
        for t, d, dev, act, i in rows:
            owner, action = (act.split(": ", 1) if ": " in act else ("None", "None"))
            lab = [("Type", t), ("Date", d), ("Source", f"https://news.example/{i}"), ("Why it matters to you", f"{area} is exposed."),
                   ("So what", "Margins may tighten."), ("Action", action), ("Owner", owner), ("Quote", "costs rose")]
            out += [title(i, dev)] + [f"{mark}{k}: {v}" for k, v in lab if k != drop] + (extra or []) + [""]
        return "\n".join(out)
    ok = lambda c, d=None: {"pass": True, "reason": "fake"}
    good_date = lambda u, d, t=None, quote=None: (d, "fake")
    strip = lambda rs: [{k: v for k, v in r.items() if k not in ("Development",)} for r in rs]

    def fails(text, why):
        try:
            parse(text)
        except Malformed:
            n["broken"] += 1
            return
        raise AssertionError(f"v11.7: {why} parsed")
    try:
        load(os.path.join(HERE, "answer-key-t2-past-v11.6.json"), "P1")
        t_rows, t_score = parse(table), score(table, "p", checker=ok, dater=good_date)
        load(os.path.join(HERE, "answer-key-t2-past-v11.7.json"), "P1")
        forms = [cards(), cards(title=lambda i, dev: f"- {dev}"), cards(mark="- "), cards(title=lambda i, dev: f"### {i}) {dev}", mark="**"),
                 cards(mark="- **").replace(": ", ":** ", 1)]
        for c in forms:  # bold, list (derive drops the number), bulleted labels, heading title, bold labels
            got = parse(c)
            assert strip(got) == strip(t_rows), (c, got)
            assert [r["Development"] for r in got] == [r["Development"].rstrip(".") for r in t_rows]
            c_score = score(c, "p", checker=ok, dater=good_date)
            assert {k: v["pass"] for k, v in c_score["items"].items()} == {k: v["pass"] for k, v in t_score["items"].items()}
            assert c_score["counter_metric"]["must_found_by_type"] == t_score["counter_metric"]["must_found_by_type"]
            n["cards"] += 1
        # A2 on cards: Owner None needs Action None; a role or You owns the action
        a2 = lambda owner, action: v10_row({**parse(cards())[0], "Action": parse(cards().replace(
            "Action: update the cost book", f"Action: {action}").replace("Owner: Head of Estimating", f"Owner: {owner}"))[0]["Action"]}, None)["a2"]
        assert a2("Head of Estimating", "update the cost book") and a2("You", "check the bill") and a2("None", "None")
        assert not a2("None", "update the cost book") and not a2("Chief Wizard", "update the cost book")
        n["cards"] += 5
        assert parse("Nothing material this week: industry\nNothing material this week: AI\n") == []
        fails("Nothing material this week: industry\n", "no cards and one nothing line")
        fails(cards() + "\n" + table, "a card answer with a table")
        fails(table, "a table answer")
        fails(cards(drop="Quote"), "a card with no Quote line")
        fails(cards(drop="Owner"), "a card with no Owner line")
        fails(cards(extra=["Date: 1 November 2026"]), "a label twice")
        fails(cards().replace("Summary", "Source: https://news.example/9", 1), "a Source line outside a card")
        fails(cards(title=lambda i, dev: f"**{i}.**"), "a card with no title")
        fails(cards().replace("Date: 30 October 2026", "Date: last week"), "an unparseable date")
        fails(cards().replace("Type: AI", "Type: policy"), "a Type that is not industry or AI")
        # every saved table capture is refused on v11.7 (the ruler reads cards only)
        for run in sorted(r for r in saved_captures() if r.startswith("t2-") and "-v11-" not in r):
            text = open(os.path.join(HERE, "rounds-t2", run, "output.md"), encoding="utf-8").read()
            if "| # |" in text or "| Date |" in text:
                fails(text, f"saved table capture {run}")
                n["captures"] += 1
        assert not saved_captures() or n["captures"] >= 29, n
    finally:
        KEY = saved
    return n


def v114_check():
    """Ruler t2-past v11.4: a page is dated from the dated section that holds the quote; a calculated or rolling footer
    ("Last updated on ...") never dates a page; a section whose stated coverage ends before the window is stale."""
    import tempfile
    global KEY
    saved = KEY
    v113 = json.load(open(os.path.join(HERE, "answer-key-t2-past-v11.3.json"), encoding="utf-8"))
    v114 = json.load(open(os.path.join(HERE, "answer-key-t2-past-v11.4.json"), encoding="utf-8"))
    own = {"version", "previous_version", "ruler_change", "comparable", "section_date", "row4_ruling"}
    assert v114["section_date"] is True and v114["weeks"] == v113["weeks"]
    assert not [f for f in set(v113) | set(v114) if f not in own and v113.get(f) != v114.get(f)]  # only the dating rule moved
    d = tempfile.mkdtemp(dir="/tmp")
    u = "https://docs.example.com/copilot/release-notes"
    tf = os.path.join(d, check_urls.key(u) + ".txt")
    q = "In Copilot in Excel, the response contains links to highlight where changes are made in your workbook."
    foot = '<footer><span>Last updated on 2026-09-24</span></footer>'
    sec = lambda head, cover, body: f"<h2>{head}</h2><p>{cover}</p><h3>Excel</h3><p>{body}</p>"
    in_win = sec("November 4, 2026", "Updates released between October 28, 2026 and November 3, 2026.", q)
    older = sec("October 27, 2026", "Updates released between October 13, 2026, and October 27, 2026.", "Learning Agent is here.")
    all_old = sec("November 4, 2026", "Updates released between October 20, 2026 and October 30, 2026.", q)

    def dated(page, quote=q):
        open(tf, "w").write(page)
        return page_date(u, dt.date(2026, 11, 4), d, quote=quote)
    try:
        KEY = {**v113, "page_text_date": True, "page_date_line": True, "page_date_line_mdy": True, "require_meta_date": True,
               "window": v113["weeks"]["P2"]["window"]}
        # v11.3 behaviour, kept for every key without section_date: the footer dates the release-notes page
        open(tf, "w").write(f"<h1>Release notes</h1>{in_win}{older}{foot}")
        assert page_date(u, dt.date(2026, 11, 4), d) == (dt.date(2026, 9, 24), "page text"), "v11.3 read the footer"
        KEY = {**KEY, "section_date": True}
        # probe i: a footer-dated page with no dated section has no date (a rolling footer is not a publication date)
        assert dated(f"<h1>Guide</h1><p>{q}</p>{foot}")[0] is None
        assert dated("<p>Page last updated: 24 September 2026</p><p>x</p>")[0] is None
        assert dated("<p>Last modified</p>\n<p>24 September 2026</p>")[0] is None, "a footer label on the line above"
        assert dated("<p>Published 3 November 2026. Last updated 2026-09-24</p>") == (dt.date(2026, 11, 3), "page text")
        # probe ii: an in-window section dates the page from its heading, not the footer
        assert dated(f"<h1>Release notes</h1>{in_win}{older}{foot}") == (dt.date(2026, 11, 4), "section heading"), dated(f"<h1>Release notes</h1>{in_win}{older}{foot}")
        assert dated(f"<h1>Release notes</h1>{sec('November 4, 2026', '', q)}{foot}") == (dt.date(2026, 11, 4), "section heading")
        # the quote in an older section takes that section's date, so T1 fails
        assert dated(f"{in_win}{older}{foot}", "Learning Agent is here.") == (dt.date(2026, 10, 27), "section coverage ends before the window")
        assert dated(f"{in_win}{sec('October 27, 2026', '', 'Learning Agent is here.')}", "Learning Agent is here.") == (dt.date(2026, 10, 27), "section heading")
        # the quote outside every dated section falls back to the v11.3 rules, footer skipped
        assert dated(f"<p>Guide text.</p>{in_win}{older}{foot}", "Guide text.") == (None, "quote outside every dated section")
        # section dating wins over metadata, because the section is where the quote sits
        meta = '<meta property="article:published_time" content="2026-01-13T09:00">'
        assert dated(f"{meta}{in_win}{older}") == (dt.date(2026, 11, 4), "section heading")
        assert dated(f"{meta}<p>{q}</p>") == (dt.date(2026, 1, 13), "page metadata")
        # probe iii: a section that starts before the window is in the window when its coverage ends in it (in_win
        # above), and stale when its stated coverage ends before the window (the ruler v11.1 roundup precedent)
        assert dated(all_old) == (dt.date(2026, 10, 30), "section coverage ends before the window"), dated(all_old)
        assert dated(sec("4 November 2026", "Covers updates from 20 October 2026 to 1 November 2026.", q))[1] == "section coverage ends before the window"
        assert dated(sec("4 November 2026", "Covers updates from 20 October 2026 to 2 November 2026.", q)) == (dt.date(2026, 11, 4), "section heading")
        lo, hi = (dt.date.fromisoformat(KEY["window"][k]) for k in ("from", "to"))
        assert lo <= dated(in_win)[0] <= hi and not lo <= dated(all_old)[0] <= hi
        # v11.4 review fixes (amended before any run). One date-only heading never overrides page metadata: a sidebar
        # heading after the body, or a heading before the body, leaves the metadata date in place.
        meta_in = '<meta property="article:published_time" content="2026-11-04T09:00">'
        assert dated(f"{meta_in}<p>{q}</p><aside><h4>3 March 2025</h4><p>Older post.</p></aside>") == (dt.date(2026, 11, 4), "page metadata")
        assert dated(f"{meta_in}<h2>12 March 2025</h2><p>{q}</p>") == (dt.date(2026, 11, 4), "page metadata")
        # a dated-section page never returns no date while its metadata holds one
        assert dated(f"{meta_in}<p>Guide text.</p>{in_win}{older}", "Guide text.") == (dt.date(2026, 11, 4), "page metadata")
        # the footer skip keeps a dated statement in body text; it skips only a <footer> date or a label-and-date line
        assert html_date("<p>The code was revised on 2026-11-03 after review.</p>") == (dt.date(2026, 11, 3), "page text")
        assert html_date("<footer><p>Content revised on 2026-09-24 by the web team</p></footer>")[0] is None
        # a quote repeated in two sections (a newest-first page) takes the oldest section's date
        rep = sec("October 20, 2026", "", q)
        assert dated(f"{in_win}{rep}") == (dt.date(2026, 10, 20), "section heading"), dated(f"{in_win}{rep}")
    finally:
        KEY = saved
        for f in (tf,):
            if os.path.exists(f):
                os.remove(f)
        os.rmdir(d)


def v113_check():
    """Ruler t2-past v11.3: week P1's W2 match no longer accepts a cost forecast (a modal, or expected/set/likely/going/forecast to)."""
    v112 = json.load(open(os.path.join(HERE, "answer-key-t2-past-v11.2.json"), encoding="utf-8"))
    v113 = json.load(open(os.path.join(HERE, "answer-key-t2-past-v11.3.json"), encoding="utf-8"))
    own = {"version", "previous_version", "comparable", "ruler_change", "weeks"}
    assert not [f for f in set(v112) | set(v113) if f not in own and v112.get(f) != v113.get(f)]  # only the P1 addendum moved
    assert v113["weeks"]["P2"] == v112["weeks"]["P2"] and v113["weeks"]["P1"]["addendum"] == "answer-key-t2-past-1-v11.3.json"
    assert {k: v for k, v in v113["weeks"]["P1"].items() if k != "addendum"} == {k: v for k, v in v112["weeks"]["P1"].items() if k != "addendum"}
    old = json.load(open(os.path.join(HERE, v112["weeks"]["P1"]["addendum"]), encoding="utf-8"))["stories"]
    new = json.load(open(os.path.join(HERE, v113["weeks"]["P1"]["addendum"]), encoding="utf-8"))["stories"]
    assert [(s["id"], s["match"]) for s in old if s["id"] != "W2"] == [(s["id"], s["match"]) for s in new if s["id"] != "W2"]
    assert [{k: v for k, v in s.items() if k != "match"} for s in old] == [{k: v for k, v in s.items() if k != "match"} for s in new]
    row = lambda dev, url="https://news.example.com/x": {"Development": dev, "Source URL": url}
    # the false match: run t2-v7r-p1-2 row 4, a builders' submission on a trust tax (a forecast, not the PPI release)
    r4 = row("A national builders\u2019 submission opposed the proposed 30% minimum tax on discretionary trusts, warning that construction costs would increase. [masterbuil...ers.com.au]",
             "https://masterbuilders.com.au/wp-content/uploads/2026/10/Master-Builders-Australia-Submission-Senate-Economic-Legislation-Committee-291026.pdf")
    assert story_of(r4, old) == "W2", "v11.2 had this false match"
    assert story_of(r4, new) is None, story_of(r4, new)
    # true misses: other cost forecasts and other stories stay off W2
    for dev in ("Building costs could rise further if the trust tax passes.", "Construction costs are expected to increase next year.",
                "Materials costs will climb as tariffs bite.", "Consumer prices rose 4.3% over the year to September.",
                "Building costs are expected to rise next year.", "Construction costs are set to increase under the reforms.",
                "Input costs would increase under the trust tax.", "Input prices are expected to rise in 2027."):
        assert story_of(row(dev), new) != "W2", dev
    # true hits: a row that reports W2's story still maps to W2, by text alone
    for dev in ("House-construction input prices rose 3.9% over the year to September 2026. [abs.gov.au]",  # row 5's text
                "Building costs rose at the fastest pace in three years.", "Construction costs increased 3.9% over the year to September.",
                "Producer price indexes show house construction up 1.0% in the quarter.", "Materials costs jumped 1.0% in the September quarter.",
                # review fix, before any run on v11.3: "to" after a non-forecast verb is a past report, not a forecast
                "Building costs continue to rise, up 3.9% over the year to September.",
                "Construction costs have continued to climb, rising 3.9% over the year.",
                "House building costs are starting to rise faster, up 3.9% a year.", "Input prices rose 3.9% over the year."):
        assert story_of(row(dev), new) == "W2", dev
        assert story_of(row(dev), old) == "W2", dev  # the narrowing loses no hit v11.2 had


def v112_check():
    """Ruler t2-past v11.2: a blocked row resolved by the route, a blocked row still failing, and no blocked rows."""
    global KEY
    v11 = json.load(open(os.path.join(HERE, "answer-key-t2-past-v11.json"), encoding="utf-8"))
    v112 = json.load(open(os.path.join(HERE, "answer-key-t2-past-v11.2.json"), encoding="utf-8"))
    own = {"version", "previous_version", "comparable", "ruler_change", "blocked_host_route"}
    assert v112["blocked_host_route"] is True and v112["weeks"] == v11["weeks"]
    assert not [f for f in set(v11) | set(v112) if f not in own and v11.get(f) != v112.get(f)]  # only the route changed
    t1 = KEY
    head = "| # | Date | Development | Why it matters to us | Source URL | Quote |\n|---|---|---|---|---|---|\n"
    blocked = "https://www.rba.gov.au/media-releases/2026/mr-26-30.html"
    text = head + (f"| 1 | 3 November 2026 | Reserve Bank lifts the cash rate to 4.85% | Dearer loans for buyers | {blocked} | increase the cash rate target |\n"
                   "| 2 | 2 November 2026 | Dwelling approvals rose 5.1% | Fewer house approvals | https://www.abs.gov.au/statistics/industry/building-and-construction/building-approvals-australia/latest-release | Total dwellings approved rose 5.1% |\n")

    def checker(state):
        def c(cite, d=None):
            r = {"url": cite["url"], "pass": True, "reason": "fake", "route": "this Mac"}
            if cite["url"] == blocked and state == "resolved":
                r["route"] = "VPN off"
            elif cite["url"] == blocked and state == "still":
                r.update({"route": "VPN off", "pass": False, "refused": True, "reason": "refused the script (status 403); still unreachable with the VPN off"})
            elif cite["url"] == blocked and state == "awaiting":
                r.update({"pass": False, "refused": True, "reason": "refused the script (status 403); no Chrome text captured"})
            return r
        return c
    dater = lambda u, d, t=None: (d, "fake")
    try:
        KEY = {**t1, "blocked_host_route": True}
        # (c) no blocked rows: final at once, no wizard needed
        s = score(text, "t", checker=checker(None), dater=dater)
        assert s["pass"] and s["route"]["final"] and s["route"]["awaiting"] == [] and "verdict" not in s, s.get("route")
        # a blocked row before the wizard: no final score
        s = score(text, "t", checker=checker("awaiting"), dater=dater)
        assert not s["pass"] and s["verdict"] == "awaiting route" and s["route"]["awaiting"] == [blocked], s["route"]
        # (a) a blocked row resolved by the route
        s = score(text, "t", checker=checker("resolved"), dater=dater)
        assert s["pass"] and s["route"]["final"] and s["route"]["vpn_off"] == [blocked], s["route"]
        assert s["rows"][0]["check"]["route"] == "VPN off"
        # (b) a blocked row still failing with the VPN off: a final fail on R1
        s = score(text, "t", checker=checker("still"), dater=dater)
        assert not s["pass"] and s["route"]["final"] and "R1" in s["critical_failures"] and "verdict" not in s, s["critical_failures"]
        # a key without the route (v11.1 and earlier) is unchanged: no route record
        KEY = t1
        s = score(text, "t", checker=checker("awaiting"), dater=dater)
        assert not s["pass"] and "route" not in s
    finally:
        KEY = t1


def v11_check():
    """Ruler t2-past v11: a line that holds only a month-first date ("November 3, 2026") dates a page; v10 does not read it."""
    global KEY
    saved = KEY
    page = '<h1>Results</h1><p class="x">November 3, 2026</p><p>Body text, written on November 4, 2026 in a sentence.</p>'
    try:
        KEY = {**saved, "page_text_date": True, "page_date_line": True}
        assert html_date(page)[0] is None, "v10 must not read a month-first date line"
        KEY = {**KEY, "page_date_line_mdy": True}
        assert html_date(page) == (dt.date(2026, 11, 3), "page text date line"), html_date(page)
        assert html_date("<p>Written on November 4, 2026 by staff</p>")[0] is None, "a date inside a sentence is not a date line"
        for line, want in (("Mayor 3, 2026", None), ("Novel 3, 2026", None), ("Decade 3, 2026", None), ("Nov 3, 2026", dt.date(2026, 11, 3)),
                           ("Sept 3, 2026", dt.date(2026, 9, 3)), ("Sep. 3, 2026", None), ("Tuesday, November 3, 2026", dt.date(2026, 11, 3)), ("May 3 2026", dt.date(2026, 5, 3))):
            assert html_date(f"<p>{line}</p>")[0] == want, (line, html_date(f"<p>{line}</p>"))
    finally:
        KEY = saved


def v10_check():
    """Ruler t2-past v10: Type column, per-type caps, PA1 against the key's expected areas, A2, nothing lines per type,
    the key's tag decides a story's type, profile and addendum must be committed, legacy diagnostic for v9 columns."""
    import shutil, tempfile
    global KEY
    t1 = KEY
    d = tempfile.mkdtemp(dir="/tmp")
    git = lambda *a: subprocess.run(["git", "-C", d, *a], check=True, capture_output=True)
    commit = lambda: (git("add", "-A"), git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "c"))
    try:
        git("init", "-q")
        profile = ("# Profile\n\n## Portfolio\n\n1. Sales and customer experience\n2. Construction delivery\n3. Digital and data\n\n"
                   "## Leadership team\n\n- Head of Sales: owns Sales and customer experience.\n"
                   "- Head of Construction: owns Construction delivery.\n- Head of Digital: owns Digital and data.\n")
        os.makedirs(os.path.join(d, "case")); open(os.path.join(d, "case", "profile.md"), "w").write(profile)
        base = {"version": "test v10", "v10": True, "profile": "case/profile.md",
                "columns": ["#", "Type", "Date", "Development", "Why it matters to your portfolio", "So what", "Action", "Source URL", "Quote"],
                "legacy_columns": ["#", "Date", "Development", "Why it matters to us", "Source URL", "Quote"],
                "type_caps": {"industry": 5, "AI": 3}, "max_rows": 8, "max_quote_words": 30,
                "nothing_material": "Nothing material this week.", "nothing_type": "Nothing material this week: {type}",
                "one_sentence": ["Why it matters to your portfolio", "Quote"], "story_match_exclusive": True,
                "weeks": {"P1": {"window": {"from": "2026-10-26", "to": "2026-11-01"}, "addendum": "add.json", "stale": []}}}
        kp = os.path.join(d, "key.json"); json.dump(base, open(kp, "w"))
        ev = lambda u: {"url": "https://" + u, "quote": "q", "date": "2026-10-28", "page_date_source": "page metadata"}
        W1 = {"id": "W1", "type": "industry", "must": True, "what": "CPI rose", "urls": ["abs.example/cpi"], "match": "CPI",
              "areas": ["Sales and customer experience"], "evidence": ev("abs.example/cpi")}
        W2 = {"id": "W2", "type": "industry", "must": False, "what": "Approvals fell", "urls": ["abs.example/appr"], "match": "approvals",
              "areas": ["Construction delivery"], "evidence": ev("abs.example/appr")}
        A1 = {"id": "A1", "type": "AI", "must": True, "what": "Copilot agents for site diaries", "urls": ["vendor.example/agents"],
              "match": "site diar", "areas": ["Digital and data", "Construction delivery"], "evidence": ev("vendor.example/agents")}
        B1 = {"id": "B1", "type": "both", "must": False, "what": "Builder uses AI to estimate", "urls": ["peer.example/ai"],
              "match": "estimat", "evidence": ev("peer.example/ai")}
        add_path = os.path.join(d, "add.json")
        stories = [W1, W2, A1, B1]

        def write(st, prof=profile, do_commit=True):
            json.dump({"version": "add v10", "stories": st, "stale": []}, open(add_path, "w"))
            open(os.path.join(d, "case", "profile.md"), "w").write(prof)
            if do_commit:
                commit()

        def refused(why, **kw):
            write(**kw)
            try:
                load(kp, "P1")
            except Malformed:
                return
            raise AssertionError(why)
        refused("v10: a story type outside industry, AI or both must not load", st=[dict(W1, type="news")] + stories[1:])
        refused("v10: a must story with no areas must not load", st=[dict(A1, areas=[])] + [W1, W2, B1])
        refused("v10: an area that is not a portfolio item in the profile must not load",
                st=[dict(A1, areas=["Digital"])] + [W1, W2, B1])
        write(stories); open(os.path.join(d, "case", "profile.md"), "a").write("edited\n")
        try:
            load(kp, "P1"); raise AssertionError("v10: a profile edited since its commit must not load")
        except Malformed:
            pass
        write(stories)
        load(kp, "P1")
        assert KEY["portfolio"] == ["Sales and customer experience", "Construction delivery", "Digital and data"], KEY["portfolio"]
        assert KEY["actors"] == ["Head of Sales", "Head of Construction", "Head of Digital"], KEY["actors"]
        ok = lambda c, x=None: {"pass": True, "reason": "fake"}
        good = lambda u, dd, tt=None: (dd, "fake")
        head = "| # | Type | Date | Development | Why it matters to your portfolio | So what | Action | Source URL | Quote |\n|---|---|---|---|---|---|---|---|---|\n"
        row = lambda n, t, dev, why, act, url: f"| {n} | {t} | 28 October 2026 | {dev} | {why} | Act early. | {act} | https://{url} | q |\n"
        r_w1 = row(1, "industry", "CPI rose 4.3%", "Higher prices squeeze sales and customer experience this quarter.", "None", "abs.example/cpi")
        r_a1 = row(2, "AI", "Vendor adds site diary agents", "This could speed Construction delivery reporting.", "Head of Digital: trial it.", "vendor.example/agents")
        sc = lambda t: score(t, checker=ok, dater=good)
        s = sc(head + r_w1 + r_a1)
        assert s["pass"], json.dumps(s["items"], indent=1)
        assert s["counter_metric"]["items_by_type"] == {"industry": 1, "AI": 1}, s["counter_metric"]
        assert s["counter_metric"]["must_found_by_type"] == {"industry": "1 of 1", "AI": "1 of 1"}, s["counter_metric"]
        # PA1 checks the key's expected areas, never any area name: W1 expects Sales and customer experience only
        s = sc(head + r_w1.replace("sales and customer experience", "Digital and data") + r_a1)
        assert not s["items"]["PA1"]["pass"] and s["items"]["PA1"]["cause"] == ["industry"], s["items"]["PA1"]
        # Gaming probes (review fixes before any v10 round), each must fail PA1 or A2
        # PA1 limit: two must rows that genuinely share one expected area both naming only that area must pass.
        shared = dict(A1, areas=["Sales and customer experience", "Digital and data"])
        write([W1, W2, shared, B1])
        load(kp, "P1")
        s = sc(head + r_w1 + r_a1.replace("Construction delivery", "Sales and customer experience"))
        assert s["items"]["PA1"]["pass"], "two must rows naming the one area they genuinely share pass PA1"
        write(stories)
        load(kp, "P1")
        # A pasted area on a keyed non-must story whose expected area differs still fails PA1 (W2 expects
        # Construction delivery; pasting W1's area onto a row matched to W2 is caught by the key check, not a
        # paste counter-check).
        paste = row(3, "industry", "Approvals fell again", "Sales and customer experience responds.", "None", "abs.example/appr")
        s = sc(head + r_w1 + r_a1 + paste)
        assert not s["items"]["PA1"]["pass"], "a pasted area on a keyed non-must story with a different expected area fails PA1"
        all3 = "This hits Sales and customer experience, Construction delivery and Digital and data."
        s = sc(head + r_w1.replace("Higher prices squeeze sales and customer experience this quarter.", all3) + r_a1)
        assert not s["items"]["PA1"]["pass"], "a cell naming every area fails PA1"
        s = sc(head + r_w1 + r_a1 + row(3, "AI", "Model news", all3, "None", "ai.example/3"))
        assert not s["items"]["PA1"]["pass"], "an unkeyed row naming three areas fails PA1"
        s = sc(head + r_w1 + r_a1 + row(3, "AI", "Model news", "AI is changing fast.", "None", "ai.example/3"))
        assert not s["items"]["PA1"]["pass"], "an unkeyed AI row naming no area fails PA1"
        assert sc(head + r_w1 + r_a1 + row(3, "AI", "Model news", "Digital and data may move.", "None", "ai.example/3"))["items"]["PA1"]["pass"]
        # A2: None (a short reason may follow), or names who acts (an LT role, or the executive as "You" plus a verb phrase)
        for act, want in (("None.", True), ("**None**", True), ("None: nothing for us to do yet.", True),
                          ("You", False), ("You.", False), ("**You**", False), ("You: raise it at the next ELT.", True),
                          ("Ask the head of construction to check contracts.", True), ("Review the contract templates.", False)):
            assert sc(head + r_w1.replace("| None |", f"| {act} |") + r_a1)["items"]["A2"]["pass"] is want, act
        # The key's tag decides type: Copilot labels the AI story "industry"; K1 still finds it, and it counts as AI
        s = sc(head + r_w1 + r_a1.replace("| AI |", "| industry |") + "\nNothing material this week: AI\n")
        assert s["pass"] and s["rows"][1]["type"] == "AI", json.dumps(s["items"], indent=1)
        # Caps: five industry rows plus one AI-labelled row the key tags industry is six industry: C1 fails
        ind = "".join(row(i, "industry", f"Other news {i}", "Construction delivery.", "None", f"o.example/{i}") for i in range(3, 7))
        s = sc(head + r_w1 + r_a1 + ind + row(7, "AI", "Approvals fell", "Construction delivery.", "None", "abs.example/appr"))
        assert not s["items"]["C1"]["pass"] and s["items"]["C1"]["cause"] == ["industry"], s["items"]["C1"]
        # A story the key tags both cannot break the caps: it counts under Copilot's label
        ai3 = "".join(row(i, "AI", f"AI news {i}", "Digital and data.", "None", f"ai.example/{i}") for i in (8,))
        s = sc(head + r_w1 + r_a1 + ind + ai3 + row(9, "AI", "Builder estimating with AI", "Digital and data.", "None", "peer.example/ai"))
        assert s["items"]["C1"]["pass"], s["items"]["C1"]
        s = sc(head + r_w1 + r_a1 + ind + row(9, "industry", "Builder estimating with AI", "Digital and data.", "None", "peer.example/ai"))
        assert s["items"]["C1"]["pass"] is False, "six industry-labelled rows break the industry cap"
        s = sc(head + r_w1 + r_a1 + "".join(row(i, "AI", f"AI news {i}", "Digital and data.", "None", f"ai.example/{i}") for i in (8, 10, 11)))
        assert not s["items"]["C1"]["pass"] and s["items"]["C1"]["cause"] == ["AI"], "four AI rows break the AI cap"
        # K1 cause names the type of the missed must story
        s = sc(head + r_w1 + "\nNothing material this week: AI\n")
        assert not s["items"]["K1"]["pass"] and s["items"]["K1"]["cause"] == ["AI"], s["items"]["K1"]
        assert s["items"]["F1"]["pass"], s["items"]["F1"]
        # Nothing lines: a type with no row needs its line; a type with rows must not carry it
        assert not sc(head + r_w1)["items"]["F1"]["pass"], "no AI row and no AI nothing line fails F1"
        assert not sc(head + r_w1 + r_a1 + "\nNothing material this week: AI\n")["items"]["F1"]["pass"]
        write([W2, B1])
        load(kp, "P1")
        s = sc("Nothing material this week: industry\n\nNothing material this week: AI\n")
        assert s["pass"] and s["counter_metric"]["items_reported"] == 0, json.dumps(s["items"], indent=1)
        for broken in ("Nothing material this week: industry\n", head + r_w1.replace("| industry |", "| News |"),
                       head.replace("| So what |", "| So |") + r_w1):
            try:
                sc(broken); raise AssertionError(f"v10 malformed output passed: {broken[:50]!r}")
            except Malformed:
                pass
        # Legacy diagnostic: v9 columns score only the old items, against industry and both stories
        write(stories)
        load(kp, "P1")
        old = ("| # | Date | Development | Why it matters to us | Source URL | Quote |\n|---|---|---|---|---|---|\n"
               "| 1 | 28 October 2026 | CPI rose 4.3% | Buyers stretch. | https://abs.example/cpi | q |\n")
        try:
            sc(old); raise AssertionError("v9 columns are malformed on v10 without --legacy")
        except Malformed:
            pass
        s = score(old, checker=ok, dater=good, legacy=True)
        assert s["pass"] and s["legacy"] and set(s["items"]) == {"R1", "T1", "T2", "T3", "S1", "K1", "F1"}, json.dumps(s, indent=1)
        assert not score(old.replace("CPI rose", "Rates rose").replace("abs.example/cpi", "x.example/r"), checker=ok, dater=good,
                         legacy=True)["items"]["K1"]["pass"]
    finally:
        KEY = t1
        shutil.rmtree(d)


def chip_check():
    """Ruler t2-past v6: chips with a run of dots or ellipses are stripped; earlier rulers keep them; text stays."""
    global KEY
    t1 = KEY
    run = ["[abcb.prod....bcb.gov.au]", "[abcb.prod.…bcb.gov.au]", "[a.b…..c.gov.au]", "[www....gov.au]"]
    kept = ["[see p.3 of the report]", "[ABS]", "[1.]", "[.gov.au]", "[nsw.gov.au/news]"]
    try:
        for k in (t1, dict(t1, chip_dot_run=True)):
            KEY = k
            for c in ("[1]", "[rba.gov.au]", "[masterbuil...ers.com.au]", "[masterbuil…ers.com.au]"):
                assert strip_chips("target. " + c) == "target.", (k.get("chip_dot_run"), c)
            for c in kept:
                assert strip_chips("target. " + c) == "target. " + c, (k.get("chip_dot_run"), c)
            for c in run:
                assert (strip_chips("target. " + c) == "target.") == bool(k.get("chip_dot_run")), (k.get("chip_dot_run"), c)
        assert strip_chips("web_open:https://a.example/x") == "web_open:https://a.example/x", "a tool marker is not a chip"
    finally:
        KEY = t1


def miss_check():
    """Ruler t2-past v7: the Chrome-text route for a 200 page that lacks the quote; earlier rulers and other faults unchanged."""
    import shutil, tempfile
    global KEY
    t1, real = KEY, check_urls.fetch
    d = tempfile.mkdtemp(dir="/tmp")
    u, q = "https://a.example/consult", "The regulations have been made and will commence on 31 March 2027."
    script_page = (200, u, "Consultation", "Have your say. Loading.")
    pages = {u: script_page}
    check_urls.fetch = lambda url, timeout=30: pages[url]
    ck = lambda cite, td: check_urls.check(cite, td, fetcher=lambda url: pages[url])
    chk = lambda: check_row(ck, {"url": u, "quote": q}, d)
    put = lambda t: open(os.path.join(d, check_urls.key(u) + ".txt"), "w", encoding="utf-8").write(t)
    try:
        KEY = dict(t1, require_meta_date=True, page_text_date=True, page_date_line=True, pdf_text_date=True,
                   pdf_content_type=True)
        put("Consultation\n" + q + "\nUpdated 1 November 2026")
        assert not chk()["pass"], "v6: a 200 page that lacks the quote fails, Chrome text or not"
        KEY = dict(KEY, chrome_text_on_miss=True)
        r = chk()
        assert r["pass"] and r["via"] == "chrome", r
        put("Consultation\nSomething else.")
        assert chk()["reason"] == "neither the script page nor its Chrome text holds the quote"
        put("Just a moment... verify you are human")
        assert not chk()["pass"] and "challenge" in chk()["reason"]
        os.remove(os.path.join(d, check_urls.key(u) + ".txt"))
        assert chk()["reason"] == "page does not hold the quote; no Chrome text captured"
        put(q)
        for st in ((404, u, "", "Not Found"), (200, "https://a.example/", "Home", "Welcome home page " + q)):
            pages[u] = st
            assert not chk()["pass"], ("only a 200 page that lacks the quote is routed", st)
        pages[u] = script_page
        assert not check_row(ck, {"url": u, "quote": q}, None)["pass"], "no --text-dir, no route"
        # dating: Chrome text saved for a quote miss never dates a page the script fetched with 200
        real_raw = check_urls.fetch_raw
        try:
            check_urls.fetch_raw = lambda url, timeout=30, keep_error_body=False: (200, url, "text/html", b"<p>Have your say.</p>")
            put(q + "\n29 October 2026")
            assert page_date(u, dt.date(2026, 10, 27), d) == (None, "no metadata date on the page"), "no page date fails T1"
            pages[u] = (403, u, "", "")
            assert page_date(u, None, d) == (dt.date(2026, 10, 29), "page text date line"), "a refused page is dated from Chrome text"
        finally:
            check_urls.fetch_raw = real_raw
    finally:
        KEY, check_urls.fetch = t1, real
        shutil.rmtree(d)


def t2_self_check():
    import shutil, tempfile
    global KEY
    t1 = KEY
    d = tempfile.mkdtemp(dir="/tmp")
    try:
        shutil.copy(os.path.join(HERE, "answer-key-t2.json"), d)
        kp = os.path.join(d, "answer-key-t2.json")
        try:
            load(kp, "A")
            raise AssertionError("a week with no addendum must not load")
        except Malformed:
            pass
        import subprocess
        git = lambda *a: subprocess.run(["git", "-C", d, *a], check=True, capture_output=True)
        git("init", "-q"); git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "base")
        add_path = os.path.join(d, "answer-key-t2-week-a.json")

        def refused(add, why, commit=True):
            json.dump(add, open(add_path, "w"))
            if commit:
                git("add", "-A"); git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "a")
            try:
                load(kp, "A")
            except Malformed:
                return
            raise AssertionError(why)
        story = {"id": "N1", "must": True, "what": "x", "urls": ["abs.gov.au/new-release"], "match": "lending",
                 "evidence": {"url": "https://www.abs.gov.au/new-release", "quote": "q", "date": "2026-11-12",
                              "page_date_source": "page metadata"}}
        refused({"version": "test", "stories": [story]}, "an addendum git does not track must not load", commit=False)
        git("add", "-A")
        try:
            load(kp, "A")
            raise AssertionError("a staged addendum with no commit must not load")
        except Malformed:
            pass
        no_meta = dict(story, evidence={k: v for k, v in story["evidence"].items() if k != "page_date_source"})
        refused({"version": "test", "stories": [no_meta]}, "a must story with no page-metadata date must not load")
        stale_ev = dict(story, evidence=dict(story["evidence"], quote="Lending fell after the 3 November rate rise."))
        refused({"version": "test", "stories": [stale_ev]}, "must-story evidence that matches a stale item must not load")
        refused({"version": "test", "stories": [story], "stale": [{"id": "P1", "urls": []}]}, "a stale item with no topic or period must not load")
        json.dump(dict(json.load(open(kp)), story_match_exclusive=True), open(kp, "w"))
        other = dict(story, id="N2", must=False, what="Lending rules for builders eased", match="rules? eased")
        refused({"version": "test", "stories": [story, other]}, "v8: a match pattern that matches another story must not load")
        refused({"version": "test", "stories": [dict(story, match="approvals")]}, "v8: a match pattern that misses its own story must not load")
        json.dump({k: v for k, v in json.load(open(kp)).items() if k != "story_match_exclusive"}, open(kp, "w"))
        json.dump({"version": "test", "stories": [story]}, open(add_path, "w"))
        git("add", "-A"); git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "addendum")
        load(kp, "A")
        json.dump({"version": "edited", "stories": [story]}, open(add_path, "w"))
        try:
            load(kp, "A")
            raise AssertionError("an addendum edited after its commit must not load")
        except Malformed:
            pass
        git("checkout", "--", "answer-key-t2-week-a.json")
        load(kp, "A")
        bad = subprocess.run([sys.executable, os.path.abspath(__file__), os.path.join(d, "none.md"), "--key", kp, "--week", "B"],
                             capture_output=True, text=True)
        assert bad.returncode == 2 and json.loads(bad.stdout)["key"].startswith("t2 "), bad.stdout
        head = "| # | Date | Development | Why it matters to us | Source URL | Quote |\n|---|---|---|---|---|---|\n"
        new = "| 1 | 12 November 2026 | New home lending fell in October | Fewer buyers will sign this quarter. | https://www.abs.gov.au/new-release | Lending fell. |\n"
        ok = lambda c, x=None: {"pass": True, "reason": "fake"}
        good_date = lambda u, dd, tt=None: (dd, "fake")
        s = score(head + new, checker=ok, dater=good_date)
        assert s["pass"], json.dumps(s["items"], indent=1)
        assert s["addendum_committed"], "the score records the addendum's commit time"
        after = new.replace("fell in October", "fell in October after the 3 November rate rise")
        s = score(head + after, checker=ok, dater=good_date)
        assert s["rows"][0]["stale"] is None and s["items"]["T1"]["pass"], "a row about a keyed story is not stale by topic and period"
        rerun = "| 2 | 13 November 2026 | Analysts say the 3 November rate rise to 4.85% is biting | Buyers pull back. | https://news.example/rates | Rates are 4.85%. |\n"
        s = score(head + new + rerun, checker=ok, dater=good_date)
        assert not s["items"]["T1"]["pass"] and s["rows"][1]["stale"] == "L1", "stale story re-reported with a new date"
        loose = rerun.replace("Analysts say the 3 November rate rise to 4.85% is biting", "Lending to slow after the 3 November rate rise to 4.85%")
        s = score(head + new + loose, checker=ok, dater=good_date)
        assert s["rows"][1]["stale"] == "L1" and s["rows"][1]["story"] is None and not s["items"]["T1"]["pass"], "a match-regex mapping does not escape the stale check"
        topic_only = rerun.replace("the 3 November rate rise to 4.85% is biting", "mortgage stress rises as the cash rate bites").replace("Rates are 4.85%.", "Stress rose.")
        s = score(head + new + topic_only, checker=ok, dater=good_date)
        assert s["items"]["T1"]["pass"] and s["rows"][1]["stale_topic_only"] == "L1", "topic alone is a review flag, not a fail"
        s = score(head + new.replace("this quarter.", "this quarter. Margins will fall too."), checker=ok, dater=good_date)
        assert not s["items"]["S1"]["pass"], "a two-sentence Why fails S1"
        assert not score(head + new.replace("12 November", "9 November"), checker=ok, dater=good_date)["items"]["T1"]["pass"], "window is 10 to 16 November"
        KEY = dict(KEY, require_meta_date=True)
        html_page = os.path.join(d, check_urls.key("https://www.abs.gov.au/new-release") + ".txt")
        open(html_page, "w").write("<p>Released 12 November 2026</p>")
        assert page_date("https://www.abs.gov.au/new-release", dt.date(2026, 11, 12), d)[0] is None, "row date text alone is not a page date"
        open(html_page, "w").write('<meta property="article:published_time" content="2026-11-12T09:00">')
        assert page_date("https://www.abs.gov.au/new-release", None, d)[0] == dt.date(2026, 11, 12)
        KEY = dict(KEY, page_text_date=True)  # ruler t2-past v2
        u = "https://www.abs.gov.au/new-release"
        for page, want in (("<p>Reference period October 2026 Released 12/11/2026 Next Release 10/12/2026</p>", dt.date(2026, 11, 12)),
                           ("<p>Corrigenda issued 2026-11-12 The board has published notes</p>", dt.date(2026, 11, 12)),
                           ("<p>Next Release 12/11/2026</p>", None), ("<p>Lending fell on 12 November 2026.</p>", None),
                           ("<p>Published 3 November 2026. Lending fell on 12 November 2026.</p>", dt.date(2026, 11, 3))):
            open(html_page, "w").write(page)
            assert page_date(u, dt.date(2026, 11, 12), d)[0] == want, (page, want)
        open(html_page, "w").write('<meta property="article:published_time" content="2026-11-01T09:00"><p>Released 12/11/2026</p>')
        assert page_date(u, None, d) == (dt.date(2026, 11, 1), "page metadata"), "metadata wins over page text"
        KEY = dict(KEY, page_date_line=True)  # ruler t2-past v3
        for page, want in (("<h1>Updates</h1>\n<p>29 October 2026</p>\n<p>Rules changed.</p>", dt.date(2026, 10, 29)),
                           ("Updates\nThursday, 29 October 2026\nRules changed.", dt.date(2026, 10, 29)),
                           ("<p>Caretaker from Tuesday 3 November 2026. Lending fell on 12 November 2026.</p>", None),
                           ("<p>Released 30/10/2026</p><p>29 October 2026</p>", dt.date(2026, 10, 30)),
                           ("<p>No date here.</p>", None), ("<p>29 Banana 2026</p>", None)):
            open(html_page, "w").write(page)
            assert page_date(u, dt.date(2026, 10, 29), d)[0] == want, (page, want)
        KEY = dict(KEY, pdf_text_date=True)  # ruler t2-past v4
        xmp = b"<x:xmpmeta><xmp:CreateDate>2011-01-06T10:00:00</xmp:CreateDate></x:xmpmeta>"
        for lines, info, want in ((["Gazette No. S 1 Friday 30 October 2026", "Order made.", "30 October 2026"], "2026-10-30", (dt.date(2026, 10, 30), "pdf page text date line")),
                                  (["Released 29/10/2026"], None, (dt.date(2026, 10, 29), "pdf page text")),
                                  (["Made on 30 October 2026 by the Minister."], "2026-10-28", (dt.date(2026, 10, 28), "pdf document info")),
                                  (["No date here."], None, (dt.date(2011, 1, 6), "pdf embedded xmp"))):
            assert pdf_date(_pdf(lines, info, xmp)) == want, (lines, want, pdf_date(_pdf(lines, info, xmp)))
        assert pdf_date(_pdf(["No date here."], None, b""))[0] is None
        # ruler t2-past v5, item b: an XMP CreateDate only in a Flate-compressed metadata stream
        packed = _pdf(["No date here."], None, b"", xmp_flate=xmp)
        assert b"CreateDate" not in packed and pdf_date(packed)[0] is None, "v4 cannot read a compressed XMP stream"
        KEY = dict(KEY, pdf_xmp_decoded=True)
        assert pdf_date(packed) == (dt.date(2011, 1, 6), "pdf xmp metadata stream"), pdf_date(packed)
        assert pdf_date(_pdf(["30 October 2026"], None, b"", xmp_flate=xmp))[1] == "pdf page text date line", "text still wins"
        # item a: a PDF known only by its Content-Type (bytes before %PDF-), fetched by check_urls.fetch_raw
        served = b"\r\n" + _pdf(["Order made.", "30 October 2026"])
        real = check_urls.fetch_raw
        try:
            check_urls.fetch_raw = lambda url, timeout=30: (200, url, "application/pdf", served)
            assert page_date(u, None, None)[1] != "pdf page text date line", "v4 knows a PDF by its prefix only"
            KEY = dict(KEY, pdf_content_type=True)
            assert page_date(u, None, None) == (dt.date(2026, 10, 30), "pdf page text date line"), page_date(u, None, None)
            check_urls.fetch_raw = lambda url, timeout=30: (200, url, "text/html", b"<p>29 October 2026</p>")
            assert page_date(u, None, None) == (dt.date(2026, 10, 29), "page text date line"), "HTML stays HTML"
            check_urls.fetch_raw = lambda url, timeout=30: (None, url, "", "URLError: timed out")
            assert page_date(u, None, None)[0] is None
            release_check(real)
        finally:
            check_urls.fetch_raw = real
    finally:
        KEY = t1
        shutil.rmtree(d)


def release_check(real_fetch):
    """Ruler t2-past v9: a PDF with no text date is dated from the same-site page that links that exact PDF."""
    global KEY
    pdf_url = "https://files.example.com.au/assets/Index%20NOV%202026.pdf"
    undated = _pdf(["Values fell 1.2% over the month."], "2026-10-30")
    meta = lambda d: '<meta property="article:published_time" content="%sT09:00">' % d

    def site(pages):
        def fake(url, timeout=30):
            if url == pdf_url:
                return 200, url, "application/pdf", undated
            if url in pages:
                return 200, url, "text/html", pages[url].encode()
            return 404, url, "", ""
        check_urls.fetch_raw = fake
    home, listing, art = "https://www.example.com.au/", "https://www.example.com.au/news", "https://www.example.com.au/news/values-fall"
    link = '<a href="/assets/Index NOV 2026.pdf">x</a>'.replace("/assets", "https://files.example.com.au/assets")
    base = {home: '<a href="/news">News</a>', listing: '<a href="/news/values-fall?ref=list">Values fall</a>' + meta("2026-10-01"),
            art: meta("2026-11-02") + "<p>Values fell.</p>" + link}
    v8 = dict(KEY)
    site(base)
    assert page_date(pdf_url, dt.date(2026, 11, 2)) == (dt.date(2026, 10, 30), "pdf document info"), "v8 keeps the document-info date"
    KEY = dict(v8, pdf_release_page=True)
    assert page_date(pdf_url, None) == (dt.date(2026, 11, 2), f"pdf release page {art}"), page_date(pdf_url, None)
    site(dict(base, **{"https://files.example.com.au/assets/": meta("2026-11-04") + link}))
    assert page_date(pdf_url, None)[0] == dt.date(2026, 11, 4), "the page the PDF's address sits under is depth 0, so it wins"
    site(dict(base, **{"https://www.example.com.au/news/older": meta("2026-11-01") + link,
                       listing: base[listing] + '<a href="/news/older">o</a>'}))
    assert page_date(pdf_url, None)[0] == dt.date(2026, 11, 1), "two linking pages at one depth: the earliest date"
    site(dict(base, **{art: meta("2026-11-02") + "<p>Values fell on 2 November 2026.</p>"}))
    assert page_date(pdf_url, dt.date(2026, 11, 2)) == (dt.date(2026, 10, 30), "pdf document info"), "no linking page: fall back"
    site(dict(base, **{art: "<p>Values fell.</p>" + link}))
    assert page_date(pdf_url, dt.date(2026, 11, 2))[1] == "pdf document info", "an undated linking page: fall back"
    site({home: '<a href="https://other.example.org/p">p</a>', "https://other.example.org/p": meta("2026-11-02") + link})
    assert page_date(pdf_url, None)[1] == "pdf document info", "a page on another site is never followed"
    site(dict(base, **{listing: base[listing].replace("/news/values-fall?ref=list", "/news/far")}))
    assert page_date(pdf_url, None)[1] == "pdf document info", "a page three links deep is not reached"
    check_urls.fetch_raw = lambda url, timeout=30: (200, url, "application/pdf", _pdf(["Released 29/10/2026"]) if url == pdf_url else b"")
    assert page_date(pdf_url, None) == (dt.date(2026, 10, 29), "pdf page text"), "a text date still wins, with no crawl"
    assert site_of("discover.cotality.example") == "cotality.example" and site_of("www.nsw.gov.au") == "nsw.gov.au"
    check_urls.fetch_raw = real_fetch
    KEY = v8


def _pdf(lines, created=None, extra=b"", xmp_flate=None):
    """A minimal one-page PDF holding lines of text, an optional document-info CreationDate, extra raw bytes and
    an optional XMP packet in a Flate-compressed catalog metadata stream."""
    import zlib
    text = b"BT /F1 10 Tf 20 700 Td 12 TL " + b" ".join(b"(" + l.encode() + b") '" for l in lines) + b" ET"
    objs = [b"<< /Type /Catalog /Pages 2 0 R%s >>" % (b" /Metadata 7 0 R" if xmp_flate else b""), b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 600 800] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
            b"<< /Length %d >>\nstream\n" % len(text) + text + b"\nendstream",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            b"<< /CreationDate (D:%s000000) >>" % created.replace("-", "").encode() if created else b"<< >>"]
    if xmp_flate:
        z = zlib.compress(b'<?xpacket begin="" id="W5M0MpCehiHzreSzNTczkc9d"?><x:xmpmeta xmlns:x="adobe:ns:meta/" '
                          b'xmlns:xmp="http://ns.adobe.com/xap/1.0/">' + xmp_flate.split(b">", 1)[1] + b'<?xpacket end="r"?>')
        objs.append(b"<< /Type /Metadata /Subtype /XML /Filter /FlateDecode /Length %d >>\nstream\n" % len(z) + z + b"\nendstream")
    out, offs = b"%PDF-1.4\n", []
    for i, o in enumerate(objs, 1):
        offs.append(len(out)); out += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    x = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1) + b"".join(b"%010d 00000 n \n" % o for o in offs)
    return out + b"trailer\n<< /Size %d /Root 1 0 R /Info 6 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, x) + extra


if __name__ == "__main__":
    a = sys.argv[1:]
    if a == ["--self-check"]:
        self_check(); sys.exit(0)
    opt = lambda f: a[a.index(f) + 1] if f in a else None
    ver = None
    try:
        if opt("--key"):
            ver = json.load(open(opt("--key"), encoding="utf-8"))["version"]  # shown if load() refuses the week
            load(os.path.abspath(opt("--key")), opt("--week"))
        ver = KEY["version"]
        if opt("--route-dir"):  # ruler t2-past v11.2: replay the rows the route wizard fetched with the VPN off
            check_urls.load_route(opt("--route-dir"))
        res = score(open(a[0], encoding="utf-8").read(), opt("--round"), opt("--text-dir"), legacy="--legacy" in a)
    except Malformed as e:
        print(json.dumps({"round": opt("--round"), "key": ver, "pass": False, "malformed": str(e)}, indent=1))
        sys.exit(2)
    print(json.dumps(res, indent=1))
