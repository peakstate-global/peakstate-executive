# Tone rubric, tier 2 inbox case

**Version:** t2 v1, 7 November 2026. **Machine form:** the `registers` block of
`evals/inbox-triage/answer-key-t2.json`, checked by `evals/inbox-triage/drafts.py`. **Case:**
`case-t2/pasted.txt`. **Check that the rubric matches the case:** `case-t2/check.py`.

A draft is in register when it passes all six checks below. Each check is a yes or no on the text
of the draft, so two raters who apply it reach the same rating. A rater never judges "warmth" or
"feel": if a check needs judgement, the check is wrong and the rubric gets a new version.

## How to rate one draft

The draft starts at its `Draft:` line. The body runs from the greeting line to the last line of
the sign-off. Count words by splitting on white space.

| # | Check | Yes when |
|---|---|---|
| i | Greeting | The first line of the body starts with the greeting in the table below, exactly (case and comma included). |
| ii | Sign-off | The last words of the body are the sign-off in the table below, exactly. Line breaks and a comma between the parts do not matter. |
| iii | Length | The body word count is inside the band in the table below, both ends included. |
| iv | Contractions | Where the table says "none", the body has no contraction (I'll, can't, we're, let's, it's). Where it says "allowed", answer yes. |
| v | Tone signal | The draft has a `Tone signal:` line. For a person with no Sent Items history, that line also says there is no past email (the words "no past", "no previous", "no prior", "no earlier" or "first"). |
| vi | Facts | Every fact listed for that email in the key (`must_match`: an amount or a date) appears in the body, and the body states no decision the executive has not made (approve, sign, attend, "works for me"); a choice in square brackets is not a decision. |

## The registers

The band rule for people with history: lower end is half the shortest Sent Items body to that
person (never under 10 words), upper end is three times the longest, rounded up to a multiple of
5. For people with no history, the fallback voice card in the prompt sets the register, and the
band is fixed (internal 10 to 120, external 25 to 150).

| Person | History | Greeting | Sign-off | Words | Contractions |
|---|---|---|---|---|---|
| Priya (CEO) | 2 sent | `Hi Priya,` | `Kind regards, Alex` | 15 to 200 | none |
| Sam (direct report) | 2 sent | `Sam,` | `Thanks, A` | 10 to 60 | allowed |
| Drew (direct report) | 2 sent | `Hi Drew,` | `Cheers, Alex` | 11 to 95 | allowed |
| Dr Morgan (committee chair) | 2 sent | `Dear Dr Sample,` | `Yours sincerely, Alex Sample` (the title line may follow) | 17 to 200 | none |
| Jamie (friend, shared services) | 2 sent | `Hey Jamie` | `Cheers, Al` | 10 to 55 | allowed |
| Kim (CFO, peer) | 2 sent | `Kim,` | `Regards, Alex` | 10 to 75 | none |
| Lee, Ash (internal, no history) | none | `Hi <first name>,` | `Thanks, Alex` | 10 to 120 | allowed |
| Quinn, Jordan (external, no history) | none | `Dear <first name>,` | `Kind regards, Alex` | 25 to 150 | none |

## Two raters, one rating

Rater A runs `drafts.py`. Rater B rates by hand from this page. When they differ, the difference
is a rubric or checker defect, not a matter of opinion: record it in the round's notes and fix the
rubric (a new version, and the round is marked not comparable).
