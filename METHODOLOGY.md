# City Evidence Radar — Methodology

A standing scanner that vets new research — working papers, conference/preprints, and
journal articles — for **scalable, cost-effective ideas to improve city life, with an
emphasis on public safety**. Nothing here is a black box; this document records every
source, filter, and calculation.

## What it does, end to end

1. **Fetch** the newest items from each source (see below).
2. **Gate** the noisiest broad feeds with a keyword filter so off-topic papers never
   reach the paid scoring step.
3. **Score** every unseen item with Claude (Haiku) reading the **title + abstract only**.
4. **Rank** with a transparent 0–100 formula.
5. **Publish** to the web app and **send a weekly iMessage digest** of new high-scorers.

Already-scored items are cached by ID, so each weekly run only scores genuinely new
papers. That keeps the recurring API cost to pennies.

## Sources (all free, no-key APIs/feeds)

| Source | What | How fetched |
|---|---|---|
| **NBER** | New economics working papers | `back.nber.org/rss/new.xml` |
| **arXiv** | Preprints in `econ.GN`, `cs.CY`, `stat.AP` | arXiv API, newest 120 |
| **12 peer-reviewed journals** | Criminology + urban/policy/health (see `scanner/config.py`) | Crossref API by ISSN, newest 12 each |
| **Campbell Collaboration** | Systematic reviews of social/justice interventions | Wiley RSS |
| **Urban Institute** | Applied urban-policy research | `urban.org/research/rss.xml` |
| **J-PAL** | Randomized-evaluation lab | `povertyactionlab.org/rss.xml` |

### Journals indexed
Journal of Quantitative Criminology · Journal of Experimental Criminology · Criminology ·
Criminology & Public Policy · Justice Quarterly · Journal of Research in Crime and
Delinquency · Journal of Urban Economics · Urban Affairs Review · Journal of Policy
Analysis and Management · Regional Science and Urban Economics · Housing Policy Debate ·
Journal of Urban Health.

### Known gaps (transparency)
- **SSRN** has no open RSS/API; its crime and economics work largely resurfaces via NBER
  and Crossref, but coverage is not guaranteed.
- **Brookings, MDRC, RAND, Vera Institute, Manhattan Institute, Arnold Ventures** —
  their feeds 404 or block automated access as of the last probe and are not indexed.

## The four scoring dimensions

Claude reads each abstract and returns structured judgments. These are **AI estimates
from the abstract only**, not from the full paper.

- **Causal strength** — `RCT` / `strong quasi-experimental` / `observational` /
  `descriptive` / `non-empirical`. A rigorous systematic review or meta-analysis of
  experiments counts as strong quasi-experimental. The web app defaults to showing only
  the top two tiers ("causal evidence only").
- **Scalability** (1–5) — how readily the idea scales city- or nationwide.
- **Cost-effectiveness** (1–5) — cheapness per person helped; per-unit costs noted when
  the abstract states them.
- **NYC applicability** (1–5) — how directly NYC could implement it given its agencies
  and existing programs.

It also tags **topic**, a **public-safety** flag, a one-sentence **idea**, a 2–3 sentence
**summary**, a one-sentence **method** note, and its own **confidence** (low/med/high).

## The overall score (0–100)

```
score  = (scalability + cost + nyc_applicability) / 15 * 55      # up to 55
       + causal_bonus                                            # up to 25
       + 15  if public_safety                                    # safety weighting
       - 5   if AI confidence is "low"
clamped to 0–100
```

`causal_bonus`: RCT 25 · strong quasi-experimental 18 · observational 8 · descriptive 2 ·
non-empirical 0.

The weights encode Josh's stated priorities: a causal-evidence bar, explicit
scalability + cost flags, NYC applicability, and extra weight on public safety. They are
deliberately simple and visible — adjust them in `scanner/score.py` (`compute_score`).

## Limitations

- Scores come from **abstracts, not full papers** — they can misjudge design, cost, or
  relevance. Always read the linked study before citing or acting.
- The causal-strength label is a heuristic; borderline designs may be mis-tiered.
- Real-world cost and scalability depend heavily on local context the abstract omits.
- Coverage is partial (see gaps above); absence from the radar is not evidence of absence.

## Cost

The only paid component is Claude scoring (Haiku 4.5, ~$1/$5 per million input/output
tokens). The one-time backfill of the initial archive cost well under $1; weekly runs
score only new items and cost pennies. Every run logs its token use and estimated cost.

## Files

- `scanner/config.py` — sources, journal ISSNs, thresholds
- `scanner/fetch.py` — resilient fetchers (one dead source never aborts the run)
- `scanner/score.py` — keyword gate + Claude scoring + score formula
- `scanner/digest.py` — weekly iMessage digest
- `run.sh` — orchestrator (fetch → score → publish → push → digest)
- `site/` — the web app (reads `papers.json`)
- `data/papers.json` — the scored archive (source of truth)
