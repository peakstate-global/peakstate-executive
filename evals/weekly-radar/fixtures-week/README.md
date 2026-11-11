# Fixtures for score_week.py

Hand-written, small and invented. These are not the practice week: that is in `../case-week/`.
Run `python3 evals/weekly-radar/score_week.py --self-check` from the repo root. It scores `answer-good.md` and `answer-bad.md` against `week.json` and `week-key.json`.

`probes/` holds review probes: paraphrased titles, claims with curly apostrophes, a missing part, invented citations, heading variants, and negated claims. `probes/expected.json` gives the expected summary values for each probe. The self-check runs every probe and fails on any mismatch.
