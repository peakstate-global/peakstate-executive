#!/usr/bin/env python3
"""Fetch every cited URL and check that the page holds the quoted sentence. Fails closed.

    python3 evals/rnd/check_urls.py <citations.json>          # [{"url": ..., "quote": ...}, ...]
    python3 evals/rnd/check_urls.py --self-check

A citation passes only when all three hold:
i) the fetch returns HTTP 200 (after redirects);
ii) the page is not a soft 404 (a "not found" page served with 200, or a redirect from a deep
   link to the site's home page);
iii) every part of the quote (split at an ellipsis) is in the page text, after normalising case,
   quotation marks, dashes, punctuation and white space.
A PDF is read with pdftotext. A page that refuses a script (HTTP 401, 403 or 429, or a human-check or challenge
page in any language, checker v2; such a page served with an HTTP error status such as a Cloudflare 503,
checker v3) can be checked from its text captured in Chrome: put the text in <text-dir>/<sha1 of url>.txt and
pass --text-dir. The result then says "via": "chrome" and a status of 200 is assumed. If the Chrome text is also
only a challenge page, the row fails.
Checker v4.2 (9 November 2026, ticket 33): a page that answers the script with HTTP 200 and has a title but lacks the
quote (an article rendered by script) goes to the same Chrome text route as a refusal; Chrome text that holds the quote
passes the row. Without captured Chrome text the row fails as before. The industry scorer (ANY_LANGUAGE False) keeps v1.
Checker v4.3 (9 November 2026, ticket 41): the blocked-host second route. This Mac's VPN exit is refused by some hosts.
A row whose host refused or stalled the script (status None, 401, 403, 429 or a challenge) and that the Chrome text did not
resolve carries "refused": true; while the VPN-off route has not tried it, route_summary() lists it as awaiting route and
a v4.3 scorer gives the run no final score. The route wizard (blocked-host-route-wizard.sh) has the executive switch the
VPN off, fetches only those URLs (--route-fetch), has them switch it back on, checks the exit and records it (--route-mark).
A scorer given --route-dir replays those saved responses for those URLs only (load_route); every row records its route
("this Mac" or "VPN off"). A row still refused with the VPN off fails. Not comparable with v4.2 for a run with a refused
row: v4.2 failed it at once.
Checker v4.3 review fixes (9 November 2026, before any run): a score is final only when vpn_back_on is recorded for a
route that fetched rows; an Akamai bot-manager challenge served 200 (bm-verify, sec-if-cpt, _abck) is a challenge; under
the industry ruler (ANY_LANGUAGE False) a 503 is a refusal that awaits the route, since that ruler drops the error body.
These apply only when the scorer's key turns the route on (ROUTE_ON), so v4.2 and v11.1 score as before.
"""
import hashlib, html, json, os, re, subprocess, sys, tempfile, urllib.parse, urllib.request
from html.parser import HTMLParser

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/142.0 Safari/537.36")
NOT_FOUND = re.compile(r"page (?:was )?not found|404|page (?:does not|doesn't) exist|"
                       r"(?:cannot|can't|could not) (?:be )?find (?:the|that|this) page|"
                       r"page (?:is )?no longer available|page (?:you|you're) (?:are )?looking for", re.I)
CHALLENGE = re.compile(r"just a moment|verify you are human|enable javascript and cookies|access denied", re.I)
# Checker v2 (8 November 2026): a human-check or challenge page in any language. Words seen on such pages
# (English, Chinese, Japanese, Korean, European languages), plus vendor markers that only a challenge page carries.
CHALLENGE_ANY = re.compile(
    r"client challenge|captcha|are you (?:a )?(?:human|robot)|not a robot|security check|checking your browser|"
    r"bot (?:check|detection|protection)|human verification|slide to (?:verify|complete)|drag the slider|"
    r"人机|验证|驗證|滑动|滑動|拼图|拼圖|防火墙|防火牆|安全检查|ロボット|認証|確認しています|로봇|보안 문자|"
    r"vérifi\w* que vous|vous êtes un humain|sicherheitsüberprüfung|kein roboter|verifica que eres|no soy un robot|"
    r"non sono un robot|verificação de segurança|не робот|проверка безопасности", re.I)
CHALLENGE_MARK = re.compile(r"cdn-cgi/challenge-platform|cf-chl|_incapsula_resource|px-captcha|geetest|datadome|"
                            r"hcaptcha|recaptcha|turnstile|aliyun_waf|awswaf|perimeterx", re.I)


# Checker v4.3: the blocked-host route. url -> (status, final, Content-Type, body) saved with the VPN off; load_route() fills it.
ROUTE, ROUTE_META = {}, {}
ROUTE_ON = False  # set by a scorer whose key has the route (checker v4.3, ruler t2-past v11.2)
AKAMAI_MARK = re.compile(r"bm-verify|sec-if-cpt|_abck", re.I)  # v4.3 review: Akamai bot-manager challenge pages

ANY_LANGUAGE = True  # checker v2 and v3; the industry scorer sets False, so its rulers keep checker v1 in full:
# the English-only challenge rule, HTTP-error bodies dropped (fetch_raw's default) and no superscript rule
SUPERSCRIPT = re.compile(r"\s+(?=[\u00b9\u00b2\u00b3\u2070-\u209f])")


def is_challenge(title, text, raw=""):
    """A page whose content is a human check, not an article: short, and its title, opening text or markup names a challenge."""
    akamai = ROUTE_ON and bool(AKAMAI_MARK.search(raw))  # v4.3 review fix, route keys only
    if not ANY_LANGUAGE:
        return bool((CHALLENGE.search(title + " " + text[:400]) or akamai) and len(text.split()) < 300)
    if len(text.split()) >= 300 and len(text) >= 1500:  # a CJK article has few spaces, so length counts too
        return False
    head = title + " " + text[:600]
    return bool(CHALLENGE.search(head) or CHALLENGE_ANY.search(head) or CHALLENGE_MARK.search(raw) or akamai)


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.skip, self.title, self.in_title = [], 0, "", False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript", "svg"):
            self.skip += 1
        self.in_title = tag == "title"

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript", "svg") and self.skip:
            self.skip -= 1
        self.in_title = False

    def handle_data(self, d):
        if self.in_title:
            self.title += d
        if not self.skip:
            self.parts.append(d)


def html_text(raw):
    p = _Text()
    p.feed(raw)
    return p.title.strip(), " ".join(p.parts)


def norm(s):
    s = html.unescape(s).casefold()
    s = re.sub(r"[­​‌‍﻿]", "", s)  # soft hyphen and zero-width characters
    s = re.sub(r"[^\w%$]+", " ", s)  # punctuation, quotes and dashes become one space
    s = " ".join(s.split())
    if ANY_LANGUAGE:  # checker v3: a superscript or subscript character joins the character before it ("I ²" is "I²")
        s = SUPERSCRIPT.sub("", s)
    return s


def holds(quote, text):
    q = quote.strip().strip('"“”‘’\'*_ ')
    parts = [norm(p) for p in re.split(r"\.\.\.|…|\[\.\.\.\]", q)]
    parts = [p for p in parts if p]
    t = norm(text)
    return bool(parts) and all(p in t for p in parts)


def soft_404(requested, final, title, text):
    """The reason a 200 page is really a not-found page, or None."""
    req, fin = urllib.parse.urlsplit(requested), urllib.parse.urlsplit(final)
    if req.path.strip("/") and not fin.path.strip("/") and not fin.query:
        return f"redirected from a deep link to the home page {final}"
    head = (title + " " + text[:600])
    if NOT_FOUND.search(title) or (NOT_FOUND.search(head) and len(text.split()) < 400):
        return f"not-found page (title {title[:80]!r})"
    return None


def key(url):
    return hashlib.sha1(url.encode()).hexdigest()


def is_pdf(ctype, body):
    """A PDF by its Content-Type or its %PDF- prefix (shared with the industry scorer, ruler t2-past v5)."""
    return "pdf" in (ctype or "").lower() or body[:5] == b"%PDF-"


def fetch_raw(url, timeout=30, keep_error_body=False):
    """(status, final URL, Content-Type, body bytes); on an error, (code or None, url, "", reason).
    keep_error_body (checker v3): an HTTP error keeps its body bytes and Content-Type, so the page can be classified.
    Checker v4.3: a URL the route wizard fetched with the VPN off is replayed from ROUTE, never fetched again."""
    if url in ROUTE:
        status, final, ctype, body = ROUTE[url]
        if status not in (None, 200) and not keep_error_body:
            return status, url, "", ""
        return ROUTE[url]
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/pdf,*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.geturl(), r.headers.get("Content-Type", ""), r.read()
    except urllib.error.HTTPError as e:
        if keep_error_body:
            try:
                body = e.read()
            except Exception:
                body = b""
            return e.code, e.geturl() or url, e.headers.get("Content-Type", "") if e.headers else "", body
        return e.code, url, "", ""
    except Exception as e:  # DNS, TLS, timeout
        return None, url, "", f"{type(e).__name__}: {e}"


def fetch(url, timeout=30):
    status, final, ctype, body = fetch_raw(url, timeout, keep_error_body=ANY_LANGUAGE)
    if status != 200 and not isinstance(body, bytes):
        return status, final, "", body
    if is_pdf(ctype, body):
        with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
            f.write(body); f.flush()
            out = subprocess.run(["pdftotext", f.name, "-"], capture_output=True, text=True)
        return status, final, "", out.stdout
    raw = body.decode("utf-8", "replace")
    title, text = html_text(raw)
    if (status == 200 or ANY_LANGUAGE) and is_challenge(title, text, raw):  # checker v3: any status, so a 503 challenge routes
        status = "challenge"
    return status, final, title, text


def check(cite, text_dir=None, fetcher=fetch):
    url, quote = cite["url"].strip().strip("<>"), cite.get("quote", "")
    res = {"url": url, "quote": quote, "via": "script", "route": "VPN off" if url in ROUTE else "this Mac"}  # checker v4.3
    if not re.match(r"https?://", url):
        return {**res, "pass": False, "reason": "not an http(s) URL"}
    status, final, title, text = fetcher(url)
    res.update(status=status, final=final)
    blocked = status in (None, 401, 403, 429, "challenge") or (status == 200 and is_challenge(title, text))
    blocked = blocked or (ROUTE_ON and not ANY_LANGUAGE and status == 503)  # v11.2 review: the body is dropped, so a 503 may be a challenge  # checker v4.2: None (DNS or network failure) routes to Chrome text like a refusal
    if blocked and text_dir and os.path.exists(os.path.join(text_dir, key(url) + ".txt")):
        text = open(os.path.join(text_dir, key(url) + ".txt"), encoding="utf-8").read()
        status, title, final = 200, "", url
        res.update(via="chrome", status=200, final=url)
        if is_challenge("", text):
            return {**res, "pass": False, "refused": True, "reason": "Chrome also got only a challenge page, not the article"}
    elif blocked:
        why = "still unreachable with the VPN off" if url in ROUTE else "no Chrome text captured"
        return {**res, "pass": False, "refused": True, "reason": f"refused the script (status {status}); {why}"}
    if status != 200:
        return {**res, "pass": False, "reason": f"status {status} {text[:120]}".strip()}
    soft = soft_404(url, final, title, text)
    if soft:
        return {**res, "pass": False, "reason": "soft 404: " + soft}
    if not holds(quote, text):
        cpath = os.path.join(text_dir, key(url) + ".txt") if text_dir else ""
        if ANY_LANGUAGE and res["via"] == "script" and title.strip() and cpath and os.path.exists(cpath):  # checker v4.2
            ctext = open(cpath, encoding="utf-8").read()
            res.update(via="chrome")
            if is_challenge("", ctext):
                return {**res, "pass": False, "reason": "script page lacks the quote; Chrome also got only a challenge page"}
            if holds(quote, ctext):
                return {**res, "pass": True, "reason": "script page lacks the quote; Chrome text holds it"}
            return {**res, "pass": False, "reason": "neither the script page nor the Chrome text holds the quote"}
        return {**res, "pass": False, "reason": "page does not hold the quote"}
    return {**res, "pass": True, "reason": "page holds the quote"}


def awaiting(r):
    """Checker v4.3: a failed row whose host refused or stalled this Mac, not yet tried with the VPN off."""
    return bool(r.get("refused")) and not r["pass"] and r.get("route") != "VPN off"


def route_summary(results):
    """Checker v4.3: the route record a scorer adds to score.json. final is False while any row awaits the route."""
    aw = sorted({r["url"] for r in results if awaiting(r)})
    return {"awaiting": aw, "vpn_off": sorted({r["url"] for r in results if r.get("route") == "VPN off"}),
            "final": not aw and (not ROUTE or bool(ROUTE_META.get("vpn_back_on"))),  # v4.3 review: VPN must be back on
            "vpn_back_on": ROUTE_META.get("vpn_back_on")}


def load_route(d):
    """Checker v4.3: load the VPN-off responses the route wizard saved in d (route.json plus one body file per row)."""
    ROUTE.clear(); ROUTE_META.clear()
    p = os.path.join(d, "route.json")
    if not os.path.exists(p):
        return ROUTE_META
    ROUTE_META.update(json.load(open(p, encoding="utf-8")))
    for url, e in ROUTE_META.get("rows", {}).items():
        body = open(os.path.join(d, e["body"]), "rb").read() if e.get("body") else e.get("error", "")
        ROUTE[url] = (e["status"], e["final"], e["ctype"], body)
    return ROUTE_META


def _now():
    import datetime
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def _route_meta(d):
    p = os.path.join(d, "route.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {"rows": {}}


def _save_route(d, meta):
    os.makedirs(d, exist_ok=True)
    tmp = os.path.join(d, "route.json.tmp")
    json.dump(meta, open(tmp, "w", encoding="utf-8"), indent=1)
    os.replace(tmp, os.path.join(d, "route.json"))


def route_fetch(score_path, d, exit_org, fetcher=None):
    """Checker v4.3, run by the wizard with the VPN off: fetch only the score's awaiting URLs and save each response."""
    urls = json.load(open(score_path, encoding="utf-8")).get("route", {}).get("awaiting", [])
    os.makedirs(d, exist_ok=True)
    meta, now = _route_meta(d), _now()
    meta.update(score=os.path.abspath(score_path), exit_during=exit_org, fetched_at=now)
    meta.pop("vpn_back_on", None)  # set again only by route_mark, after the exit check
    for u in urls:
        status, final, ctype, body = (fetcher or (lambda x: fetch_raw(x, keep_error_body=True)))(u)
        e = {"status": status, "final": final, "ctype": ctype, "route": "VPN off", "fetched_at": now}
        if isinstance(body, bytes):
            e["body"] = key(u) + ".body"
            open(os.path.join(d, e["body"]), "wb").write(body)
        else:
            e["error"] = body
        meta["rows"][u] = e
    _save_route(d, meta)
    return urls, meta


def route_mark(d, exit_org):
    """Checker v4.3: record that the VPN is back on (the wizard calls this only after its exit check passes)."""
    meta = _route_meta(d)
    meta["vpn_back_on"] = {"at": _now(), "exit_org": exit_org}
    _save_route(d, meta)


def v43_self_check():
    """Checker v4.3: a blocked row resolved by the route, a blocked row still failing, and no blocked rows."""
    q = "Belts did not cut injury claims."
    page = b"<html><title>Claims study</title><body><p>Belts did not cut injury claims.</p></body></html>"
    ok_u, bad_u, chal_u, open_u = ("https://blocked.example/a", "https://blocked.example/b",
                                   "https://challenge.example/c", "https://open.example/d")
    net = {ok_u: (403, ok_u, "", b""), bad_u: (None, bad_u, "", "TimeoutError: timed out"),
           chal_u: (200, chal_u, "text/html", b"<title>Just a moment...</title><p>verify you are human</p>"),
           open_u: (200, open_u, "text/html", page)}
    g, real = globals(), fetch_raw

    def fake(u, timeout=30, keep_error_body=False):  # the network as this Mac sees it; ROUTE replays first, as in fetch_raw
        return real(u, timeout, keep_error_body) if u in ROUTE else net[u]
    g["fetch_raw"] = fake
    try:
        ROUTE.clear(); ROUTE_META.clear()
        # (c) no blocked rows: the score is final and no wizard is needed
        r = check({"url": open_u, "quote": q})
        assert r["pass"] and r["route"] == "this Mac" and not r.get("refused"), r
        s = route_summary([r])
        assert s["final"] and s["awaiting"] == [] and s["vpn_off"] == [], s
        # refused, stalled and challenged rows await the route; a content fail on an open host does not
        rs = [check({"url": u, "quote": q}) for u in (ok_u, bad_u, chal_u, open_u)]
        rs.append(check({"url": open_u, "quote": "a sentence on no page"}))
        s = route_summary(rs)
        assert not s["final"] and s["awaiting"] == sorted([ok_u, bad_u, chal_u]), s
        with tempfile.TemporaryDirectory() as d:
            sp, rd = os.path.join(d, "score.json"), os.path.join(d, "route")
            json.dump({"route": s}, open(sp, "w"))
            vpn_off = {ok_u: (200, ok_u, "text/html", page), bad_u: (None, bad_u, "", "TimeoutError: timed out"),
                       chal_u: (403, chal_u, "text/html", b"<title>Access Denied</title>")}
            urls, meta = route_fetch(sp, rd, "AS1 Home ISP", fetcher=lambda u: vpn_off[u])
            assert urls == s["awaiting"] and set(os.listdir(rd)) == {"route.json", key(ok_u) + ".body", key(chal_u) + ".body"}
            # review fix: rows fetched but vpn_back_on missing is never final
            load_route(rd)
            s1 = route_summary([check({"url": u, "quote": q}) for u in (ok_u, bad_u, chal_u, open_u)])
            assert s1["awaiting"] == [] and not s1["final"] and s1["vpn_back_on"] is None, s1
            route_mark(rd, "AS136557 Host Universal Pty Ltd")
            load_route(rd)
            rs = [check({"url": u, "quote": q}) for u in (ok_u, bad_u, chal_u, open_u)]
            # (a) a blocked row resolved: the VPN-off page holds the quote
            assert rs[0]["pass"] and rs[0]["route"] == "VPN off", rs[0]
            # (b) blocked rows still failing: still unreachable with the VPN off, and no longer awaiting
            assert not rs[1]["pass"] and rs[1]["route"] == "VPN off" and "still unreachable with the VPN off" in rs[1]["reason"], rs[1]
            assert not rs[2]["pass"] and rs[2]["route"] == "VPN off" and "still unreachable" in rs[2]["reason"], rs[2]
            assert rs[3]["pass"] and rs[3]["route"] == "this Mac", rs[3]
            s2 = route_summary(rs)
            assert s2["final"] and s2["awaiting"] == [] and s2["vpn_off"] == sorted([ok_u, bad_u, chal_u]), s2
            assert s2["vpn_back_on"]["exit_org"].startswith("AS136557"), s2
            # the replay honours keep_error_body: industry mode (False) gets no error body
            assert real(chal_u)[3] == "" and real(chal_u, keep_error_body=True)[3].startswith(b"<title>")
            assert real(bad_u) == (None, bad_u, "", "TimeoutError: timed out")
    finally:
        g["fetch_raw"] = real
        ROUTE.clear(); ROUTE_META.clear()
    v43_review_check()
    print("check_urls v4.3 self-check: ok")


def v43_review_check():
    """Checker v4.3 review fixes: an Akamai 200 challenge and an industry 503 await the route; route keys only."""
    global ROUTE_ON, ANY_LANGUAGE
    u = "https://akamai.example/a"
    raw = b'<html><title>Loading</title><body><div id="sec-if-cpt"></div><input name="bm-verify" value="x"></body></html>'
    net = {u: (200, u, "text/html", raw), "https://down.example/b": (503, "https://down.example/b", "", "")}
    g, real = globals(), fetch_raw
    g["fetch_raw"] = lambda x, timeout=30, keep_error_body=False: net[x]
    try:
        for lang in (True, False):
            ANY_LANGUAGE = lang
            ROUTE_ON = False  # v4.2 and v11.1: unchanged, the Akamai page is read as content
            r = check({"url": u, "quote": "x"})
            assert not r["pass"] and not r.get("refused"), r
            ROUTE_ON = True
            r = check({"url": u, "quote": "x"})
            assert r.get("refused") and r["status"] == "challenge" and route_summary([r])["awaiting"] == [u], r
        # industry ruler: a 503 (body dropped) awaits the route on v11.2, and fails as status 503 on v11.1
        ANY_LANGUAGE, ROUTE_ON = False, True
        r = check({"url": "https://down.example/b", "quote": "x"})
        assert r.get("refused") and "status 503" in r["reason"] and not route_summary([r])["final"], r
        ROUTE_ON = False
        r = check({"url": "https://down.example/b", "quote": "x"})
        assert not r.get("refused") and r["reason"].startswith("status 503"), r
    finally:
        g["fetch_raw"] = real
        ANY_LANGUAGE, ROUTE_ON = True, False
    print("check_urls v4.3 review self-check: ok")


def self_check():
    page = "<html><title>Study</title><body><p>Students with GPT Base did 17% worse on the exam.</p><script>x</script></body></html>"
    title, text = html_text(page)
    assert title == "Study" and "x" not in text.split()
    assert holds("“students with GPT base did 17% worse”", text)
    assert holds("Students with ... 17% worse on the exam.", text)
    assert not holds("students did 30% better", text)
    assert not holds("", text)
    assert holds("did 17% worse", "did 17%­ worse")  # soft hyphen
    assert soft_404("https://a.example/research/x", "https://a.example/", "Home", "welcome") is not None
    assert soft_404("https://a.example/research/x", "https://a.example/research/x", "Page not found", "sorry") is not None
    assert soft_404("https://a.example/x", "https://a.example/x", "Oops", "The page you are looking for has moved") is not None
    assert soft_404("https://a.example/x", "https://a.example/x", "Study", "long text " * 300 + " 404 ") is None
    assert soft_404("https://a.example/", "https://a.example/", "Home", "fine") is None

    def fake(pages):
        return lambda u: pages[u]
    ok = check({"url": "https://a.example/s", "quote": "17% worse"}, fetcher=fake({"https://a.example/s": (200, "https://a.example/s", "Study", text)}))
    assert ok["pass"], ok
    assert not check({"url": "https://a.example/s", "quote": "30% faster"}, fetcher=fake({"https://a.example/s": (200, "https://a.example/s", "Study", text)}))["pass"]
    assert not check({"url": "https://a.example/s", "quote": "x"}, fetcher=fake({"https://a.example/s": (404, "https://a.example/s", "", "")}))["pass"]
    soft = check({"url": "https://a.example/s", "quote": "home"}, fetcher=fake({"https://a.example/s": (200, "https://a.example/", "Home", "home page")}))
    assert not soft["pass"] and "soft 404" in soft["reason"], soft
    assert not check({"url": "tenant.example", "quote": "x"}, fetcher=fake({}))["pass"]
    with tempfile.TemporaryDirectory() as d:
        u = "https://b.example/p"
        blocked = fake({u: (403, u, "", "")})
        assert "refused" in check({"url": u, "quote": "17% worse"}, fetcher=blocked)["reason"]
        open(os.path.join(d, key(u) + ".txt"), "w").write(text)
        r = check({"url": u, "quote": "17% worse"}, text_dir=d, fetcher=blocked)
        assert r["pass"] and r["via"] == "chrome", r
        # checker v2: challenge pages in any language go to the Chrome route, like 401, 403 and 429
        waf = "WEB 应用防火墙 当前正在对访问请求进行人机识别检测，请稍等片刻 确认 向右滑动填充拼图"
        for t, x, raw in (("WEB 应用防火墙", waf, ""), ("Client Challenge", "A required part of this site couldn’t load.", ""),
                          ("Un instant", "Vérifions que vous êtes un humain.", ""), ("x", "loading", '<div id="px-captcha"></div>')):
            assert is_challenge(t, x, raw), t
        assert not is_challenge("Study", text) and not is_challenge("Study", "captcha " + "word " * 400)
        assert not is_challenge("研究", "学生" * 1000)
        for st, t, x in ((200, "WEB 应用防火墙", waf), ("challenge", "Client Challenge", "A required part of this site couldn’t load.")):
            ch = fake({u: (st, u, t, x)})
            assert "refused" in check({"url": u, "quote": "17% worse"}, fetcher=ch)["reason"]
            assert check({"url": u, "quote": "17% worse"}, text_dir=d, fetcher=ch)["pass"]
        open(os.path.join(d, key(u) + ".txt"), "w").write(waf)
        r = check({"url": u, "quote": "17% worse"}, text_dir=d, fetcher=fake({u: (200, u, "WEB 应用防火墙", waf)}))
        assert not r["pass"] and "Chrome also got only a challenge" in r["reason"], r
    v3_self_check()
    v42_self_check()
    v43_self_check()
    print("check_urls self-check: ok")


def v3_self_check():
    """Checker v3: (i) a challenge page served with an HTTP error status routes to Chrome; (ii) superscripts join."""
    global ANY_LANGUAGE
    import http.server, threading
    pages = {"/cf503": (503, "<html><head><title>Just a moment...</title></head><body>Checking your browser."
                              '<script src="/cdn-cgi/challenge-platform/h/b/orchestrate/x"></script></body></html>'),
             "/waf503": (503, "<html><title>WEB 应用防火墙</title><body>人机识别检测 向右滑动填充拼图</body></html>"),
             "/down503": (503, "<html><title>Service Unavailable</title><body>The server is down for maintenance.</body></html>"),
             "/gone": (404, "<html><title>Page not found</title><body>Sorry.</body></html>"),
             "/ok": (200, "<html><title>Study</title><body><p>Belts did not cut injury claims.</p></body></html>")}

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            code, body = pages[self.path]
            self.send_response(code); self.send_header("Content-Type", "text/html; charset=utf-8"); self.end_headers()
            self.wfile.write(body.encode())

        def log_message(self, *a):
            pass
    srv = http.server.HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    try:
        # (i) the body of an HTTP error page is kept and classified
        assert fetch(base + "/cf503")[0] == "challenge" and fetch(base + "/waf503")[0] == "challenge"
        assert fetch(base + "/down503")[0] == 503 and fetch(base + "/gone")[0] == 404 and fetch(base + "/ok")[0] == 200
        r = check({"url": base + "/cf503", "quote": "did not cut injury claims"})
        assert not r["pass"] and "refused the script (status challenge)" in r["reason"], r
        r = check({"url": base + "/down503", "quote": "x"})
        assert not r["pass"] and r["reason"].startswith("status 503"), r
        assert check({"url": base + "/ok", "quote": "Belts did not cut injury claims."})["pass"]
        with tempfile.TemporaryDirectory() as d:
            u = base + "/cf503"
            open(os.path.join(d, key(u) + ".txt"), "w").write("Belts did not cut injury claims.")
            r = check({"url": u, "quote": "did not cut injury claims"}, text_dir=d)
            assert r["pass"] and r["via"] == "chrome", r
        # (ii) a superscript or subscript character joins the character before it, on every page
        page = html_text("<p>though with high heterogeneity (<em>I</em>²=97%).</p>")[1]
        assert holds("though with high heterogeneity (I²=97%).", page)
        assert holds("an area of 40 m²", "an area of 40 m ²") and holds("CO₂ levels", "CO ₂ levels")
        assert norm("x ⁿ") == "xⁿ" and norm("I 2") == "i 2"  # plain digits never join
        assert not holds("I²=50%", page)
        # industry mode (ANY_LANGUAGE False) keeps checker v1 in full
        ANY_LANGUAGE = False
        assert not holds("though with high heterogeneity (I²=97%).", page)
        assert fetch(base + "/cf503")[0] == 503 and fetch_raw(base + "/cf503")[3] == ""
    finally:
        ANY_LANGUAGE = True
        srv.shutdown()
    print("check_urls v3 self-check: ok")


def v42_self_check():
    """Checker v4.2: HTTP 200 with a title but without the quote goes to the Chrome text route."""
    global ANY_LANGUAGE
    u, q = "https://c.example/article", "both quoted sentences appear here"
    shell = (200, u, "Long-term use of filtering glasses | Journal", "Journal Article Loading Sign in " * 20)
    page = {u: shell}
    fetcher = lambda x: page[x]
    with tempfile.TemporaryDirectory() as d:
        r = check({"url": u, "quote": q}, fetcher=fetcher)
        assert not r["pass"] and r["via"] == "script" and r["reason"] == "page does not hold the quote", r
        r = check({"url": u, "quote": q}, text_dir=d, fetcher=fetcher)  # no Chrome text captured: fails as before
        assert not r["pass"] and r["via"] == "script", r
        open(os.path.join(d, key(u) + ".txt"), "w").write("Results. In this study both quoted sentences appear here, word for word.")
        r = check({"url": u, "quote": q}, text_dir=d, fetcher=fetcher)
        assert r["pass"] and r["via"] == "chrome" and "Chrome text holds it" in r["reason"], r
        r = check({"url": u, "quote": "a sentence on no page"}, text_dir=d, fetcher=fetcher)
        assert not r["pass"] and r["via"] == "chrome" and r["reason"].startswith("neither"), r
        page[u] = (200, u, "", shell[3])  # no title: not an article shell, no Chrome route
        assert check({"url": u, "quote": q}, text_dir=d, fetcher=fetcher)["via"] == "script"
        page[u] = shell
        ANY_LANGUAGE = False  # industry mode keeps checker v1
        try:
            r = check({"url": u, "quote": q}, text_dir=d, fetcher=fetcher)
            assert not r["pass"] and r["via"] == "script", r
        finally:
            ANY_LANGUAGE = True
        open(os.path.join(d, key(u) + ".txt"), "w").write("Just a moment... verify you are human")
        r = check({"url": u, "quote": q}, text_dir=d, fetcher=fetcher)
        assert not r["pass"] and "challenge" in r["reason"], r
    # network failure (status None) routes to the Chrome text like a refusal
    n = "https://d.example/gone"
    down = lambda x: (None, x, "", "URLError: nodename nor servname provided")
    with tempfile.TemporaryDirectory() as d:
        r = check({"url": n, "quote": q}, text_dir=d, fetcher=down)
        assert not r["pass"] and "no Chrome text captured" in r["reason"], r
        open(os.path.join(d, key(n) + ".txt"), "w").write("Results. In this study both quoted sentences appear here.")
        r = check({"url": n, "quote": q}, text_dir=d, fetcher=down)
        assert r["pass"] and r["via"] == "chrome", r
    print("check_urls v4.2 self-check: ok")


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-check"]:
        self_check(); sys.exit(0)
    if sys.argv[1:2] == ["--route-fetch"]:  # checker v4.3, the wizard's VPN-off step: <score.json> <route-dir> <exit org>
        urls, meta = route_fetch(*sys.argv[2:5])
        for u in urls:
            st = meta['rows'][u]['status']
            print(f"PASS: status 200  {u}" if st == 200 else f"FAIL: status {st}  {u}")
        sys.exit(0)
    if sys.argv[1:2] == ["--route-mark"]:  # checker v4.3: <route-dir> <exit org>, after the exit check passed
        route_mark(*sys.argv[2:4]); sys.exit(0)
    args = sys.argv[1:]
    td = None
    if "--text-dir" in args:
        i = args.index("--text-dir"); td = args[i + 1]; del args[i:i + 2]
    cites = json.load(open(args[0]))
    out = [check(c, td) for c in cites]
    print(json.dumps({"checked": len(out), "passed": sum(r["pass"] for r in out), "results": out}, indent=1))
