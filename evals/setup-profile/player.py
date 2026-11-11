#!/usr/bin/env python3
"""Persona player: given the persona file only, write the executive's next chat message.

    python3 evals/setup-profile/player.py <persona.md> <transcript.md>
    python3 evals/setup-profile/player.py --self-check

The transcript holds the interview so far (Copilot's messages and the player's replies). This runs
a separate Claude with no tools, no project settings and an empty working folder, so the player
sees the persona and the transcript only, never the scorer or its rules.

v2 (ticket 36): the player never sees Copilot's suggested-reply buttons. The operator records them in
the transcript as a line "(Suggested replies shown: ...)"; strip() drops each such line before the
transcript reaches the player, so every reply is the persona's own.

v3 (ticket 48): a style question (brief length, tone, anything to avoid) gets the persona's own words
from its "Style answers" section, with no model call, so the player cannot add a preference. style()
reads only the question line of Copilot's last message; any other question goes to the model.
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
    # ponytail: drop the scoring block so the player never sees the match patterns
    persona = persona.split("## Match patterns")[0]
    system = persona + "\nYou are in a chat with an AI assistant. Reply with your next message to it only: no notes, no quotes, no labels."
    with tempfile.TemporaryDirectory() as d:
        r = subprocess.run(["claude", "-p", "--model", "sonnet", "--tools", "", "--strict-mcp-config",
                            "--disable-slash-commands", "--setting-sources", "", "--no-session-persistence",
                            "--system-prompt", system],
                           input="The chat so far:\n\n" + transcript + "\n\nWrite your next message.",
                           capture_output=True, text=True, cwd=d, timeout=300)
    sys.stdout.write(r.stdout.strip() + "\n")
    sys.exit(r.returncode)
