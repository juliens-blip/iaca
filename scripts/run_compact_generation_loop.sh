#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="${LOG_FILE:-${ROOT_DIR}/logs/full_coverage_compact_1200_5x1_loop.log}"
PYTHON_BIN="${PYTHON_BIN:-}"
MIN_CONTENT_LEN="${MIN_CONTENT_LEN:-1200}"
MAX_CONTENT_LEN="${MAX_CONTENT_LEN:-60000}"
EXCLUDE_MATIERE="${EXCLUDE_MATIERE:-8}"
TARGET_STANDARD_FC="${TARGET_STANDARD_FC:-5}"
TARGET_STANDARD_QQ="${TARGET_STANDARD_QQ:-0}"
TARGET_STANDARD_FI="${TARGET_STANDARD_FI:-1}"
TARGET_MANUAL_FC="${TARGET_MANUAL_FC:-5}"
TARGET_MANUAL_QQ="${TARGET_MANUAL_QQ:-0}"
TARGET_MANUAL_FI="${TARGET_MANUAL_FI:-1}"

if [ -z "$PYTHON_BIN" ]; then
  if [ -x "${ROOT_DIR}/backend/.venv/bin/python" ]; then
    PYTHON_BIN="${ROOT_DIR}/backend/.venv/bin/python"
  else
    PYTHON_BIN="python3"
  fi
fi

count_items() {
  "$PYTHON_BIN" - <<'PY'
import sqlite3

conn = sqlite3.connect('data/iaca.db')
cur = conn.cursor()
flashcards = cur.execute('SELECT COUNT(*) FROM flashcards').fetchone()[0]
fiches = cur.execute('SELECT COUNT(*) FROM fiches').fetchone()[0]
print(f"{flashcards}|{fiches}")
PY
}

main() {
  local max_passes="${1:-30}"
  local min_delta="${2:-1}"
  local provider="${3:-${GEN_PROVIDER:-ollama}}"
  local ollama_url="${OLLAMA_URL:-http://localhost:11434}"
  local ollama_model="${4:-${OLLAMA_MODEL:-phi3:mini}}"
  local reset_first_pass="${RESET_STATE:-1}"
  local pass=1

  mkdir -p "$(dirname "$LOG_FILE")"
  : > "$LOG_FILE"

  cd "$ROOT_DIR"

  while [ "$pass" -le "$max_passes" ]; do
    local before before_fc before_fi after after_fc after_fi delta_fc delta_fi delta_total

    before="$(count_items)"
    before_fc="${before%%|*}"
    before_fi="${before##*|}"
    echo "=== PASS $pass START $(date -Iseconds) provider=$provider model=$ollama_model fc=$before_fc fi=$before_fi ===" >> "$LOG_FILE"

    local reset_state="0"
    if [ "$pass" -eq 1 ] && [ "$reset_first_pass" = "1" ]; then
      reset_state="1"
    fi

    if ! {
      if [ "$reset_state" = "1" ]; then
        "$PYTHON_BIN" scripts/generate_full_coverage.py \
          --reset-state \
          --exclude-matiere "$EXCLUDE_MATIERE" \
          --skip-garbage-titles \
          --min-content-len "$MIN_CONTENT_LEN" \
          --provider "$provider" \
          --ollama-url "$ollama_url" \
          --ollama-model "$ollama_model" \
          --target-standard-fc "$TARGET_STANDARD_FC" \
          --target-standard-qq "$TARGET_STANDARD_QQ" \
          --target-standard-fi "$TARGET_STANDARD_FI" \
          --target-manual-fc "$TARGET_MANUAL_FC" \
          --target-manual-qq "$TARGET_MANUAL_QQ" \
          --target-manual-fi "$TARGET_MANUAL_FI" \
          --shortest-first \
          --max-content-len "$MAX_CONTENT_LEN"
      else
        "$PYTHON_BIN" scripts/generate_full_coverage.py \
          --exclude-matiere "$EXCLUDE_MATIERE" \
          --skip-garbage-titles \
          --min-content-len "$MIN_CONTENT_LEN" \
          --provider "$provider" \
          --ollama-url "$ollama_url" \
          --ollama-model "$ollama_model" \
          --target-standard-fc "$TARGET_STANDARD_FC" \
          --target-standard-qq "$TARGET_STANDARD_QQ" \
          --target-standard-fi "$TARGET_STANDARD_FI" \
          --target-manual-fc "$TARGET_MANUAL_FC" \
          --target-manual-qq "$TARGET_MANUAL_QQ" \
          --target-manual-fi "$TARGET_MANUAL_FI" \
          --shortest-first \
          --max-content-len "$MAX_CONTENT_LEN"
      fi
    } >> "$LOG_FILE" 2>&1; then
      echo "PASS $pass failed" >> "$LOG_FILE"
    fi

    after="$(count_items)"
    after_fc="${after%%|*}"
    after_fi="${after##*|}"
    delta_fc=$((after_fc - before_fc))
    delta_fi=$((after_fi - before_fi))
    delta_total=$((delta_fc + delta_fi))
    echo "=== PASS $pass END $(date -Iseconds) fc=$after_fc fi=$after_fi delta_fc=$delta_fc delta_fi=$delta_fi delta_total=$delta_total ===" >> "$LOG_FILE"

    if [ "$delta_total" -lt "$min_delta" ]; then
      echo "Stopping: delta_total < $min_delta" >> "$LOG_FILE"
      break
    fi

    pass=$((pass + 1))
    sleep 2
  done
}

main "$@"
