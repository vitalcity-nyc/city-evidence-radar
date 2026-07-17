#!/bin/bash
# City Evidence Radar — full weekly run.
# fetch -> score (only new items) -> publish data to site -> commit & push -> digest
set -e
cd "$(dirname "$0")"
export PATH="/usr/bin:/bin:/usr/local/bin:$PATH"

mkdir -p logs   # not committed to the repo; must exist for the log redirect below (e.g. fresh CI checkout)
STAMP=$(date +%Y%m%d_%H%M)
LOG="logs/run_$STAMP.log"
SITE_URL="${RADAR_SITE_URL:-}"

{
  echo "=== City Evidence Radar run $STAMP ==="
  git pull --quiet --no-edit || true

  echo "-- fetch --";  python3 -m scanner.fetch
  echo "-- score --";  python3 -m scanner.score
  echo "-- publish --"; cp data/papers.json docs/papers.json

  # commit + push updated data (account/remote configured at deploy time)
  if [ -n "$(git status --porcelain data/papers.json docs/papers.json)" ]; then
    git add data/papers.json docs/papers.json
    git commit -q -m "Radar refresh $STAMP [skip ci]" || true
    git push -q || echo "push skipped/failed"
  fi

  echo "-- digest --"; python3 -m scanner.digest "$SITE_URL"
  echo "=== done ==="
} >> "$LOG" 2>&1

echo "Run complete. Log: $LOG"
