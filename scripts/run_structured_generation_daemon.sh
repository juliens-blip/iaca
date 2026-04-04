#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="${LOG_FILE:-${ROOT_DIR}/logs/structured_generation_daemon.log}"
LOOP_LOG="${LOOP_LOG:-${ROOT_DIR}/logs/full_coverage_compact_1200_5x1_structured_loop.log}"
MAX_CYCLES="${1:-12}"
MAX_PASSES_PER_CYCLE="${2:-30}"
MIN_DELTA="${3:-1}"
PROVIDER="${4:-ollama}"

count_items() {
  python3 - <<'PY'
import sqlite3

conn = sqlite3.connect('data/iaca.db')
cur = conn.cursor()
flashcards = cur.execute('SELECT COUNT(*) FROM flashcards').fetchone()[0]
fiches = cur.execute('SELECT COUNT(*) FROM fiches').fetchone()[0]
print(f"{flashcards}|{fiches}")
PY
}

main() {
  local cycle=1
  local idle_cycles=0

  mkdir -p "$(dirname "$LOG_FILE")"
  : > "$LOG_FILE"

  cd "$ROOT_DIR"

  while [ "$cycle" -le "$MAX_CYCLES" ]; do
    local before before_fc before_fi after after_fc after_fi delta_fc delta_fi delta_total

    before="$(count_items)"
    before_fc="${before%%|*}"
    before_fi="${before##*|}"
    echo "=== DAEMON CYCLE $cycle START $(date -Iseconds) fc=$before_fc fi=$before_fi ===" >> "$LOG_FILE"

    LOG_FILE="$LOOP_LOG" RESET_STATE=1 GEN_PROVIDER="$PROVIDER" \
      bash scripts/run_compact_generation_loop.sh "$MAX_PASSES_PER_CYCLE" "$MIN_DELTA" "$PROVIDER" >> "$LOG_FILE" 2>&1 || true

    after="$(count_items)"
    after_fc="${after%%|*}"
    after_fi="${after##*|}"
    delta_fc=$((after_fc - before_fc))
    delta_fi=$((after_fi - before_fi))
    delta_total=$((delta_fc + delta_fi))

    echo "=== DAEMON CYCLE $cycle END $(date -Iseconds) fc=$after_fc fi=$after_fi delta_fc=$delta_fc delta_fi=$delta_fi delta_total=$delta_total ===" >> "$LOG_FILE"

    if [ "$delta_total" -eq 0 ]; then
      idle_cycles=$((idle_cycles + 1))
    else
      idle_cycles=0
    fi

    if [ "$idle_cycles" -ge 2 ]; then
      echo "Stopping daemon: 2 cycles sans nouveau contenu." >> "$LOG_FILE"
      break
    fi

    cycle=$((cycle + 1))
    sleep 5
  done
}

main "$@"
