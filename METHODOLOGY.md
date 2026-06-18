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
| **28 peer-reviewed journals** | Criminology, urban economics, policy, housing, transit, health and education (see `scanner/config.py`) | Crossref API by ISSN, newest 12 each |
| **Campbell Collaboration** | Systematic reviews of social and justice interventions | Wiley RSS |
| **World Bank** | Policy research working papers | Documents and Reports API, newest 60 |
| **SocArXiv** | Open social-science preprints | OSF API, newest 50 |
| **Urban Institute** | Applied urban-policy research | `urban.org/research/rss.xml` |
| **J-PAL** | Randomized-evaluation lab | `povertyactionlab.org/rss.xml` |

### Journals indexed
Criminology and public safety: Journal of Quantitative Criminology · Journal of
Experimental Criminology · Criminology · Criminology & Public Policy · Justice Quarterly ·
Journal of Research in Crime and Delinquency · Criminal Justice and Behavior · Police
Quarterly · Journal of Criminal Justice · Injury Prevention.
Urban, policy and economics: Journal of Urban Economics · Urban Affairs Review · Journal
of Urban Affairs · Journal of Policy Analysis and Management · Regional Science and Urban
Economics · Journal of Public Economics · American Economic Journal: Applied Economics ·
American Economic Journal: Economic Policy · Journal of Human Resources.
Housing and transit: Housing Policy Debate · Housing Studies · Transportation Research
Part A.
Health: Journal of Urban Health · American Journal of Public Health · American Journal of
Preventive Medicine · Prevention Science · Health Affairs.
Education: Educational Evaluation and Policy Analysis.

### Known gaps (transparency)
- **SSRN** has no open feed or API; its crime and economics work largely resurfaces via
  NBER, Crossref and SocArXiv, but coverage is not guaranteed.
- **IZA** discussion papers and the **Cochrane Library** were tested but their feeds
  returned nothing on the last probe.
- **Brookings, MDRC, RAND, Vera Institute, Manhattan Institute and Arnold Ventures** —
  their feeds 404 or block automated access as of the last probe and are not indexed.

## The four scoring dimensions

Claude reads each abstract and returns structured judgments. These are **AI estimates
from the abstract only**, not from the full paper.

- **Causal strength** — `RCT` / `strong quasi-experimental` / `observational` /
  `descriptive` / `non-empirical`. A rigorous systematic review or meta-analysis of
  experiments counts as strong quasi-experimental. The web app defaults to showing only
  the top two tiers ("causal evidence only").
- **Effect magnitude** (1–5) — how large and robust the demonstrated effect is. A null or
  statistically insignificant result scores 1–2, so a rigorously evaluated study that found
  nothing ranks below one that moved the needle. This is the single heaviest factor.
- **Scalability** (1–5) — how readily the idea scales city- or nationwide.
- **Cost-effectiveness** (1–5) — cheapness per person helped; per-unit costs noted when
  the abstract states them.
- **NYC applicability** (1–5) — how directly NYC could implement it given its agencies
  and existing programs.
- **Underused** (1–5) — the gap between how strong the evidence is and how little the idea
  is actually deployed or funded in big US cities. Mainstream interventions (hot-spot
  policing, focused deterrence, body cameras) score low; well-evidenced but neglected ideas
  score high.
- **Novelty** (1–5) — how fresh or counterintuitive the framing is for public-safety or
  urban policy.
- **Theme** — the single best-fit editorial bundle (see below), used for the "group by
  theme" view.

It also tags **topic**, a **public-safety** flag, a one-sentence **idea**, a 2–3 sentence
**summary**, a one-sentence **method** note, and its own **confidence** (low/med/high).

For every paper it also extracts two scannable facts, shown on each card:
- **Size of effect** — the magnitude and direction of the study's main finding as the
  abstract reports it (e.g. "15% fewer parole violations", "0.18 SD higher test scores",
  "no significant effect"). Marked "Not quantified in abstract" when none is given.
- **People reached** — how many people/units the study covered (e.g. "1,156 parolees",
  "~30,000 court cases", "12 cities over 6 years"). Marked "Not stated in abstract" when
  the abstract omits it. This is the study's sample/scope, not a projection of how many a
  city-wide rollout would reach.

## The overall score (0–100)

Balanced weighting: effect size and rigor dominate; feasibility matters; underuse and
novelty are meaningful but secondary.

```
score  = effect_magnitude / 5 * 26      # up to 26 — the heaviest factor
       + causal_bonus                   # up to 20
       + scalability      / 5 * 13      # up to 13
       + cost             / 5 * 13      # up to 13
       + nyc_applicability/ 5 * 12      # up to 12
       + underused        / 5 * 9       # up to 9
       + novelty          / 5 * 7       # up to 7
       + 8   if public_safety           # public-safety emphasis
       - 5   if AI confidence is "low"
clamped to 0–100
```

`causal_bonus`: RCT 20 · strong quasi-experimental 14 · observational 6 · descriptive 1 ·
non-empirical 0.

The weights encode Josh's priorities: effect size first (so rigorously evaluated nulls
sink), then rigor and feasibility, then a secondary lift for underused and novel ideas,
with a small public-safety emphasis. They are deliberately simple and visible — adjust
them in `scanner/score.py` (`compute_score`).

## Editorial themes

Every idea is assigned one best-fit theme. The list seeds Josh's bundles — alcohol and
addiction, reentry and reemployment, lead and environmental exposure, domestic violence,
schools and the school-to-prison pipeline — plus emergent ones (gun and community violence
intervention, behavioral and cognitive programs, place and the built environment, policing
and courts, housing, health and overdose response, youth and family, economic security).
The "group by theme" view bundles ideas under each theme with a short narrative framing,
so they read as policy directions rather than isolated studies. Themes live in
`scanner/config.py` (`THEMES`).

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
