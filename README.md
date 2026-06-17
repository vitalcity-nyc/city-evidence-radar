# City Evidence Radar

A standing scanner that vets new research — NBER & arXiv working papers, peer-reviewed
journal articles, Campbell systematic reviews, and applied think-tank work — for
**scalable, cost-effective ideas to improve city life, with an emphasis on public
safety**. It scores each study for causal strength, scalability, cost-effectiveness, and
NYC applicability, publishes a searchable web app, and texts Josh a weekly digest of the
best new finds.

See **[METHODOLOGY.md](METHODOLOGY.md)** for every source, filter, and calculation.

## Run it manually

```bash
./run.sh                 # full run: fetch → score → publish → push → digest
python3 -m scanner.fetch # just fetch candidates → data/raw.json
python3 -m scanner.score # score unseen candidates → data/papers.json (uses Claude API)
python3 -m scanner.digest "https://<live-url>"   # send the iMessage digest
```

The Anthropic API key is read from the macOS Keychain (`ANTHROPIC_API_KEY`) or the
environment. Scoring only touches *new* items, so reruns are cheap.

## Layout

```
scanner/  config.py · fetch.py · score.py · digest.py
data/     raw.json (latest fetch) · papers.json (scored archive — source of truth)
docs/     index.html + papers.json (the web app — served by GitHub Pages)
run.sh    weekly orchestrator
logs/     per-run logs + saved digests
```

## Weekly automation

A launchd job (`com.vitalcity.evidence-radar.plist`) runs `run.sh` weekly. The recurring
cost is pennies (only new papers are scored). Digest delivery is iMessage via osascript.
