#!/usr/bin/env python3
"""Forum case-t3 (PRACTICE case): self-check, and the scorer for the new fields until a ruler version adopts them.

    python3 evals/forum-prep/case-t3/check.py              # build check, good document, probes
    python3 evals/forum-prep/case-t3/check.py <output.md>  # score a run: ruler v3.1 items plus the case-t3 fields
    python3 evals/forum-prep/case-t3/check.py <output.md> --key <answer-key-t3-vN.json>  # reproduce an earlier key's score

The current items are scored by ruler v3.1 (score_forum.score_doc, unchanged). The key's `rankings` and
`opportunities` are scored here by score_t3(), which reuses score_forum's heading, unit and citation helpers:
- key t3 v2: a top ranking with found.opportunity also needs a cited unit under those headings that names its area
  only and calls it an opportunity (the rank and the opportunity may sit in two bullets);
- key t3 v3: R1's persistence words (still, again, remains, previously, last time, a second time, continues, ...)
  must sit outside citations (persist_scope "text"), so a "(previous pack: ...)" label alone is not persistence,
  and must be tied to the rank: a bare word sits within a few function words of a rank term ("still at the bottom",
  "last, unchanged"), or a phrase names the earlier period ("previous pack", "two packs running", "for the 2nd time");
- a ranking is found when a unit under one of its "found" headings matches every pattern (area name plus ranking
  words, hyphen or space), the persistence pattern when given, and carries a citation that holds on its page;
- its response is found when a unit under the response headings matches every pattern and cites a response page;
- its questions pass when every pattern matches some unit under the question headings and the area is named there;
- an opportunity is found as a ranking is, with its point_match on the text outside citations;
- every found unit and response unit must name an expected area and no other area (pasting one area fails).
"""
import importlib.util, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FORUM = os.path.dirname(HERE)
KEY_PATH = os.path.join(HERE, "answer-key-t3-v3.json")  # key t3 v3 (ticket 53); v2 and v1 runs keep their recorded scores
sys.path.insert(0, FORUM)
import score_forum as sf  # noqa: E402


def _mod(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def own_area(u, areas):
    others = [a for a in sf.KEY["areas"] if a not in areas]
    return any(sf.has_phrase(u, a) for a in areas) and not any(sf.has_phrase(u, a) for a in others)


def hits(blocks, headings, match, pages, areas, point=(), persist=None, persist_text=False):
    out = []
    for h in headings:
        for u in sf.units(blocks.get(h, [])):
            full, pt = sf.bare(u).casefold() + " " + u.casefold(), sf.bare(u).casefold()
            if not all(re.search(p, full) for p in match) or not all(re.search(p, pt) for p in point):
                continue
            if persist and not re.search(persist, pt if persist_text else full):
                continue
            if any(pg in pages and ok for pg, _, ok in sf.cites_of(u)) and own_area(u, areas):
                out.append(u)
    return out


def score_t3(text):
    _, blocks, _ = sf.doc_blocks(text)
    res = {}
    for r in sf.KEY["rankings"]:
        f, rp, q = r["found"], r["response"], r["questions"]
        why = []
        if not hits(blocks, f["headings"], f["match"], r["pages"], r["areas"], persist=f.get("persist_match"),
                    persist_text=f.get("persist_scope") == "text"):
            why.append("ranking not found")
        op = f.get("opportunity")  # key t3 v2: the top ranking named as an opportunity, a cited unit of its own
        if op and not hits(blocks, op["headings"], op["match"], r["pages"], r["areas"]):
            why.append("top ranking not named as an opportunity")
        if not hits(blocks, rp["headings"], rp["match"], rp["pages"], r["areas"]):
            why.append("no response")
        qu = [sf.bare(u).casefold() for h in q["headings"] for u in sf.units(blocks.get(h, []))]
        why += [f"no question matching {p!r}" for p in q["all"] if not any(re.search(p, u, re.S) for u in qu)]
        if not any(re.search(q["area_match"], u) for u in qu):
            why.append("questions do not name the area")
        res[r["id"]] = why
    for o in sf.KEY["opportunities"]:
        found = hits(blocks, o["headings"], o["match"], o["pages"], o["areas"], point=o.get("point_match", ()))
        res[o["id"]] = [] if found else ["opportunity not found"]
    return {"ruler": "case-t3 extension (check.py)", "failed": {k: v for k, v in res.items() if v},
            "pass": not any(res.values())}


def self_check():
    _mod("build_t3", os.path.join(HERE, "build.py")).check()
    good = open(os.path.join(HERE, "good.md"), encoding="utf-8").read()
    r = sf.score_doc(good)
    assert r["pass"] and not r["missed"] and not r["critical_errors"], r
    t = score_t3(good)
    assert t["pass"], t
    print(f"good document: ruler v3.1 pass ({len(r['found'])} traps, {r['words_per_pack_page']} words per page), case-t3 fields pass")

    def fails(doc, want, label):
        got = score_t3(doc)["failed"]
        assert sorted(got) == sorted(want), (label, got)
        print(f"probe fails as expected, {label}: {got}")

    r1 = good.split("- Coastal region: ranks last")[1].split("\n")[0]
    fails(good.replace("- Coastal region: ranks last" + r1 + "\n", ""), ["R1"], "ranking missed")
    no_plan = good.replace("- You need to explain why the Coastal region is still last and table an action plan with dated "
                           "actions (p. 7: \"The plan must have dated actions and be tabled at this meeting\").\n", "")
    no_plan = re.sub(r"- Coastal region: why are we still.*?\n- What more can we do before the March quarter\?\n", "None.\n",
                     no_plan, flags=re.S)
    assert no_plan != good and "still at the bottom" not in no_plan
    got = score_t3(no_plan)["failed"]
    assert list(got) == ["R1"] and "ranking not found" not in got["R1"] and "no response" in got["R1"], got
    print(f"probe fails as expected, bottom ranking reported with no action plan or questions: {got}")
    fails(re.sub(r"- Inland region: the Regional Telehealth Fund.*?\n", "", good), ["O1"], "opportunity missing")
    # key v2 i): "against" is not persistence. Drop the persistence words from the R1 line, keep "against".
    r1_line = good.split("- Coastal region: ranks last")[1].split("\n")[0]
    no_persist = good.replace(r1_line, r1_line.replace("and was still last in the previous pack at 73%", "and sits at 73% "
                              "in the extract").split(" (previous pack:")[0])
    assert no_persist != good and "against" in no_persist.split("- Coastal region: ranks last")[1].split("\n")[0]
    fails(no_persist, ["R1"], "bottom ranking with 'against' and no persistence word")
    # key v3: every plain way to say the Coastal region is still or again at the bottom passes; wrong forms fail.
    old = "and was still last in the previous pack at 73%"
    assert old in r1_line
    accepted = ["and was also last previously at 73%", "and is still at the bottom", "and is at the bottom again",
                "and remains at the bottom", "and remained last at 73%", "the same rank as last time",
                "for a second time", "and continues to rank last", "and was last in the previous pack at 73%",
                "and was last in the prior pack at 73%", "and was last in the earlier pack at 73%",
                "two packs running", "for two quarters", "the bottom rank persists", "once more at the bottom",
                "last for the second pack in a row", "back-to-back", "last in consecutive packs",
                "and was last in both packs", "a persistent bottom rank", "and has been last since the last pack",
                # review fixes: plain forms the first v3 pattern missed
                "and it ranks last, as before", "and it ranks last, unchanged", "and it ranks last for another quarter",
                "for the third pack running", "in two successive packs", "and it ranks last repeatedly",
                "for the 2nd time", "as in the pack before"]
    label = r1_line[r1_line.index(" (previous pack:"):].rstrip(".")
    for w in accepted:
        doc = good.replace(r1_line, r1_line.replace(old, w))
        assert doc != good and score_t3(doc)["pass"], (w, score_t3(doc))
        bare_doc = good.replace(r1_line, r1_line.replace(old, w).replace(label, ""))  # no previous-pack citation
        assert "(previous pack:" not in bare_doc.split("- Coastal region: ranks last")[1].split("\n")[0], w
        assert score_t3(bare_doc)["pass"], (w, "without the previous-pack citation", score_t3(bare_doc))
    print(f"probes pass as expected, {len(accepted)} persistence forms accepted, with and without the previous-pack citation")
    rejected = ["and sits at the bottom against target",   # 'again' inside 'against'
                "and the remainder sit higher",            # 'remain' inside 'remainder'
                "a secondary concern at 73%",              # 'second' inside 'secondary'
                "with continuity of care at risk",         # 'continu' inside 'continuity'
                "and lastly it sits at 73%"]               # 'last' alone is the rank, not persistence
    for w in rejected:
        doc = good.replace(r1_line, r1_line.replace(old, w))
        assert doc != good, w
        fails(doc, ["R1"], f"no persistence ({w!r})")
    # review fixes: a persistence word must be tied to the rank statement, so unrelated uses beside the bottom
    # ranking fail. Each probe also restates the bottom rank next to the stray word.
    unrelated = ["and it ranks last; whether it recovers remains to be seen",
                 "and it ranks last, below the remaining regions", "and it ranks last, though staff continue to work hard",
                 "and it ranks last, with persistent staffing gaps", "and it ranks last after consecutive weeks of high demand",
                 "and it ranks last, as raised the last time we met", "and it ranks last, and the plan was again delayed",
                 "and it ranks last, as the previous CEO noted"]
    for w in unrelated:
        doc = good.replace(r1_line, r1_line.replace(old, w))
        assert doc != good, w
        fails(doc, ["R1"], f"persistence word not tied to the rank ({w!r})")
    # A "(previous pack: ...)" citation label is not a statement of persistence (persist_scope "text").
    label_only = good.replace(r1_line, r1_line.replace(old, "and sits at 73% in the extract"))
    assert "(previous pack:" in label_only.split("- Coastal region: ranks last")[1].split("\n")[0]
    fails(label_only, ["R1"], "persistence only in the '(previous pack: ...)' citation label")
    # key v2 ii): the top ranking named, but never called an opportunity.
    fails(good.replace(", an opportunity to show the rest of the health service what works", ""), ["R2"],
          "top ranking not named as an opportunity")
    # key v2 ii): rank and opportunity in two cited bullets still pass (a pattern per claim).
    split = good.replace(", an opportunity to show the rest of the health service what works (p. 15: \"Virtual care 92 1 of 7\").",
                         " (p. 15: \"Virtual care 92 1 of 7\").\n- Virtual care: the top rank is an opportunity to show the "
                         "rest of the health service what works (p. 15: \"Virtual care 92 1 of 7\").")
    assert split != good and score_t3(split)["pass"], score_t3(split)
    print("probe passes as expected, top rank and opportunity in two cited bullets")
    pasted = re.sub(r"^- ", "- Coastal region: ", good, flags=re.M)
    fails(pasted, ["R2", "O1"], "one area pasted on every point")
    assert sf.score_doc(pasted)["PA1_failed"] == ["X1", "U1"]
    print("case-t3 self-check passed")


def main(a):
    key = KEY_PATH
    if "--key" in a:
        i = a.index("--key")
        key, a = a[i + 1], a[:i] + a[i + 2:]
    sf.load(key)
    if not a:
        return self_check()
    text = open(a[0], encoding="utf-8").read()
    r = sf.score_doc(text)
    t = score_t3(text)
    print(json.dumps({"ruler_v3_1": r, "case_t3": t, "pass": r["pass"] and t["pass"]}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
