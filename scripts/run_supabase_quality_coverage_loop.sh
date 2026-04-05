#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="$ROOT_DIR/backend/.venv/bin/python"
GEN_SCRIPT="$ROOT_DIR/scripts/generate_supabase_quality_coverage.py"
GEN_LOG="$ROOT_DIR/logs/supabase_quality_coverage.log"

cd "$ROOT_DIR"

mkdir -p "$(dirname "$GEN_LOG")"
touch "$GEN_LOG"

last_selected_docs() {
  local value
  value="$(rg -o 'docs sélectionnés: [0-9]+' "$GEN_LOG" | tail -n 1 | awk '{print $3}')"
  if [[ -z "${value:-}" ]]; then
    echo "unknown"
  else
    echo "$value"
  fi
}

run_generation() {
  "$PYTHON_BIN" "$GEN_SCRIPT" \
    --limit 20 \
    --smallest-first \
    --min-content-len 5000 \
    --preview-dir "$ROOT_DIR/data/supabase_quality_previews" \
    --flashcards-timeout 1200 \
    --fiche-timeout 1200
}

round=0

while true; do
  round=$((round + 1))
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] round=$round start"

  run_generation || true

  selected="$(last_selected_docs)"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] round=$round selected_after_run=$selected"

  if [[ "$selected" == "0" ]]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] no eligible docs detected, sleep before retry"
    sleep 300
    continue
  fi

  sleep 10
done
