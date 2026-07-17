#!/bin/bash
# City Evidence Radar — full weekly run.
# fetch -> score (only new items) -> publish data to site -> commit & push -> digest
set -e
cd "$(dirname "$0")"
# Append (not prepend) system paths: keeps launchd able to find git/python,
# without shadowing a CI-provided Python that has the pip deps installed.
export PATH="$PATH:/usr/bin:/bin:/usr/local/bin"

# Pin the interpreter so it never depends on which python3 wins on PATH — the
# exact bug that kept breaking CI. CI sets PYTHON to the interpreter that has
# the pip deps; launchd/local falls back to python3.
PY="${PYTHON:-python3}"

mkdir -p logs   # not committed to the repo; must exist for the log redirect below (e.g. fresh CI checkout)
STAMP=$(date +%Y%m%d_%H%M)
LOG="logs/run_$STAMP.log"
SITE_URL="${RADAR_SITE_URL:-}"

{
  echo "=== City Evidence Radar run $STAMP ==="
  git pull --quiet --no-edit || true

  echo "-- fetch --";  "$PY" -m scanner.fetch
  echo "-- score --";  "$PY" -m scanner.score
  echo "-- publish --"; cp data/papers.json docs/papers.json

  # commit + push updated data (account/remote configured at deploy time)
  if [ -n "$(git status --porcelain data/papers.json docs/papers.json)" ]; then
    git add data/papers.json docs/papers.json
    git commit -q -m "Radar refresh $STAMP [skip ci]" || true
    # Push with rebase-and-retry so a concurrent commit landing during the run
    # never silently drops the scored data. If it still can't push after the
    # retries, exit non-zero so the run fails loudly (GitHub emails Josh) rather
    # than reporting success while quietly publishing nothing.
    branch=$(git rev-parse --abbrev-ref HEAD)
    pushed=0
    for attempt in 1 2 3; do
      if git push -q origin "$branch"; then pushed=1; break; fi
      echo "push rejected (attempt $attempt/3); rebasing on remote and retrying"
      git pull --rebase --autostash -q origin "$branch" || true
    done
    [ "$pushed" = 1 ] || { echo "ERROR: could not push radar data after 3 attempts"; exit 1; }
  fi

  echo "-- digest --"; "$PY" -m scanner.digest "$SITE_URL"
  echo "=== done ==="
} >> "$LOG" 2>&1

echo "Run complete. Log: $LOG"
