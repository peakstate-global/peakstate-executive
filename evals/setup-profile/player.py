#!/usr/bin/env python3
"""Persona player: given the persona file only, write the executive's next chat message.

    python3 evals/setup-profile/player.py <persona.md> <transcript.md>
    python3 evals/setup-profile/player.py --self-check

The transcript holds the interview so far (Copilot's messages and the player's replies). This runs
a separate Claude with no tools, no project settings and an empty working folder, so the player
sees the persona and the transcript only, never the scorer or its rules.

v2: the player never sees Copilot's suggested-reply buttons. The operator records them in
the transcript as a line "(Suggested replies shown: ...)"; strip() drops each such line before the
transcript reaches the player, so every reply is the persona's own.

v3: a style question (brief length, tone, anything to avoid) gets the persona's own words
from its "Style answers" section, with no model call, so the player cannot add a preference. style()
reads only the question line of Copilot's last message; any other question goes to the model.

v4: the player never sees the persona's name. Run d02 failed N1 because one model call
volunteered the name ("I'm Rosalind Hartigan, ...") although the persona said not to give it: the name
reached the model in the heading and in the "You are <name>, an executive." line. nameless() reads the
name from that line and removes the full name everywhere in the system prompt. As a guard, play()
checks each reply for the name's words, except words that also appear in the persona's facts (the kit
persona "Alex Sample" works at "Meridian Sample Water", so "Sample" is not a name word there). A
rejected reply never reaches Copilot, so a fresh call is harness work, not a re-run: up to two fresh
calls, each rejection written to stderr, and a third trip exits non-zero, which stops turn.py.
"""
import re, subprocess, sys, tempfile

SUGGESTED = re.compile(r"(?im)^[ \t]*\(suggested repl(?:y|ies)[^\n]*\n?")


def strip(transcript):
    return re.sub(r"\n{3,}", "\n\n", SUGGESTED.sub("", transcript))


# ponytail: keyword routing on the question line; a style question worded with none of these words
# falls through to the model, which the persona's own rule still binds.
STYLE = [("brief", re.compile(r"(?i)\bbriefs?\b.*\b(long|length|short)\b|\b(long|length)\b.*\bbriefs?\b")),
         ("tone", re.compile(r"(?i)\btone\b")),
         ("avoid", re.compile(r"(?i)\bavoid\b"))]
ALL_STYLE = re.compile(r"(?i)how (do )?you (like to )?work|working style|\bstyle\b")


def answers(persona):
    """The persona's Style answers section as {key: words}."""
    sec = persona.split("## Style answers", 1)[1].split("\n## ", 1)[0]
    return dict(re.findall(r"(?m)^- (brief|tone|avoid): (.+)$", sec))


def style(persona, transcript):
    """The scripted reply when Copilot's last question is about style, else None."""
    last = strip(transcript).rsplit("**Copilot:**", 1)[-1]
    lines = [l.strip() for l in last.splitlines() if l.strip() and not l.startswith("**Executive")]
    if not lines:
        return None
    q = next((l for l in reversed(lines) if l.endswith("?")), lines[-1])
    keys = [k for k, rx in STYLE if rx.search(q)] or (["brief", "tone", "avoid"] if ALL_STYLE.search(q) else [])
    if not keys:
        return None
    a = answers(persona)
    return " ".join(a[k] for k in keys)


FULL = re.compile(r"(?m)^You are (.+?), an executive\.")
ASK = "\nYou are in a chat with an AI assistant. Reply with your next message to it only: no notes, no quotes, no labels."


def nameless(persona):
    """(name, system prompt): the persona without its scoring block and with its full name removed."""
    n = FULL.search(persona).group(1)
    # ponytail: drop the scoring block so the player never sees the match patterns
    s = persona.split("## Match patterns")[0]
    s = s.replace(f"You are {n}, an executive", "You are an executive").replace(f": {n}\n", "\n").replace(n, "")
    return n, s + ASK


def name_words(persona, n):
    """The name's words that do not appear in the persona's facts."""
    facts = persona.split("## Facts", 1)[1].split("\n## ", 1)[0]
    return [w for w in re.findall(r"[\w'-]+", n) if not re.search(r"(?i)\b" + re.escape(w) + r"\b", facts)]


def named(reply, words):
    return any(re.search(r"(?i)\b" + re.escape(w) + r"\b", reply) for w in words)


def claude(system, prompt):
    with tempfile.TemporaryDirectory() as d:
        r = subprocess.run(["claude", "-p", "--model", "sonnet", "--tools", "", "--strict-mcp-config",
                            "--disable-slash-commands", "--setting-sources", "", "--no-session-persistence",
                            "--system-prompt", system],
                           input=prompt, capture_output=True, text=True, cwd=d, timeout=300)
    return r.returncode, r.stdout.strip()


def play(persona, transcript, call=claude, tries=3):
    """(exit code, reply) from the model; a reply with a name word is rejected and asked again."""
    n, system = nameless(persona)
    words = name_words(persona, n)
    prompt = "The chat so far:\n\n" + transcript + "\n\nWrite your next message."
    for i in range(1, tries + 1):
        code, reply = call(system, prompt)
        if code or not named(reply, words):
            return code, reply
        print(f"player guard: reply {i} of {tries} gave the persona's name, rejected: {reply}", file=sys.stderr)
    sys.exit(f"player guard: {tries} replies gave the persona's name; stopping")


def self_check():
    t = 'Q?\n\n(Suggested replies shown: "Nothing else to avoid.", "Show me")\n\n\n**Executive:**\n\nA\n'
    out = strip(t)
    assert "Suggested" not in out and "Nothing else" not in out and out == "Q?\n\n**Executive:**\n\nA\n", out
    assert strip("I said (suggested replies are fine) inline.\n") == "I said (suggested replies are fine) inline.\n"
    import os
    per = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "case", "persona-1.md")).read()
    a = answers(per)
    assert a == {"brief": "I like short briefs, one page at most.", "tone": "Plain, direct language.",
                 "avoid": "Avoid jargon and long preambles."}, a
    c = lambda msg: "Intro\n\n**Executive:**\n\nx\n\n**Copilot:**\n\n" + msg + "\n"
    # the three p04 style questions, with the suggested-reply line the operator records
    assert style(per, c("How long do you like your briefs to be?\n\n(Suggested replies shown: \"Skip\")")) == a["brief"]
    assert style(per, c('What tone do you want in drafts written for you?\n\n(Suggested replies shown: "Say what matters first")')) == a["tone"]
    assert style(per, c("Is there anything to avoid in what I write for you?")) == a["avoid"]
    assert style(per, c("How do you like to work?")) == " ".join(a[k] for k in ("brief", "tone", "avoid"))
    assert style(per, c("Briefs: how long, what tone, and anything to avoid?")) == " ".join(a.values())
    # not style: the p04 summary (it holds "Short briefs" and "long preambles") and ordinary questions
    summ = "Role\nShort briefs, one page at most\nNo long preambles\nPlain and direct\n\nIs anything wrong in this summary?"
    assert style(per, c(summ)) is None
    assert style(per, c("What forums do you sit on, such as committees, boards or leadership meetings?")) is None
    assert style(per, c("What are your top priorities for the next year? Please give up to five.")) is None
    assert style(per, "**Executive:** pasted.\n\n**Copilot:**\n\nWhat is your role?\n") is None
    # v4: the name is gone from the system prompt, a name reply trips the guard, an organisation reply passes
    import contextlib, io
    demo = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "case-demo", "persona-1.md")).read()
    for p, n, words, org in ((per, "Alex Sample", ["Alex"], "Meridian Sample Water"),
                             (demo, "Rosalind Hartigan", ["Rosalind", "Hartigan"], "Mulgara Valley Water")):
        got, system = nameless(p)
        assert got == n and all(w not in system for w in words + [n]), got
        assert "# Persona 1\n" in system and "You are an executive. An AI" in system and "Match patterns" not in system
        assert org in system and system.endswith(ASK)
        assert name_words(p, n) == words, name_words(p, n)
        assert named(f"I'm {n}, Executive General Manager Strategy at {org}.", words)
        assert named(f"{n.split()[0].lower()} here.", words)
        assert not named(f"I'm Executive General Manager Strategy at {org}. I'd rather not give my name.", words)
        # retries: two trips then a clean reply is kept; three trips exit non-zero
        replies = iter([f"I'm {n}.", f"{n} here.", "I'd rather not say."])
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            assert play(p, "t", call=lambda s, q: (0, next(replies))) == (0, "I'd rather not say.")
        assert err.getvalue().count("player guard: reply") == 2, err.getvalue()
        assert play(p, "t", call=lambda s, q: (1, f"{n} error")) == (1, f"{n} error")
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                play(p, "t", call=lambda s, q: (0, f"I'm {n}."))
            raise AssertionError("three trips did not stop")
        except SystemExit as e:
            assert e.code and str(e.code).startswith("player guard"), e.code
    print("self-check ok")


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-check"]:
        self_check()
        sys.exit(0)
    persona, transcript = open(sys.argv[1]).read(), strip(open(sys.argv[2]).read())
    scripted = style(persona, transcript)
    if scripted:
        print(scripted)
        sys.exit(0)
    code, reply = play(persona, transcript)
    sys.stdout.write(reply + "\n")
    sys.exit(code)
