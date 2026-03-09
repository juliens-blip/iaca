#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="${ROOT_DIR}/logs/manual_quality_upgrade.log"
DB_FILE="${ROOT_DIR}/data/iaca.db"

if [[ ! -f "${LOG_FILE}" ]]; then
  echo "Log introuvable: ${LOG_FILE}"
  exit 1
fi

completed_docs="$(grep -c "APRÈS: fc=40 qq=16 fi=4" "${LOG_FILE}" || true)"
last_doc_id="$(grep -Eo '\[doc=[0-9]+\]' "${LOG_FILE}" | tail -n 1 | tr -d '[]' | cut -d= -f2 || true)"
last_event="$(tail -n 1 "${LOG_FILE}" || true)"

if [[ -z "${last_doc_id}" ]]; then
  last_doc_id="N/A"
fi

read -r flashcards quiz_questions fiches < <(
  python3 - "${DB_FILE}" <<'PY'
import sqlite3
import sys
db = sys.argv[1]
conn = sqlite3.connect(db)
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM flashcards")
fc = cur.fetchone()[0]
cur.execute("""
SELECT COUNT(*)
FROM quiz_questions
""")
qq = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM fiches")
fi = cur.fetchone()[0]
conn.close()
print(fc, qq, fi)
PY
)

upgrade_pid="$(pgrep -f "upgrade_manuals_quality.py --provider auto" | head -n1 || true)"
upgrade_state="stopped"
if [[ -n "${upgrade_pid}" ]]; then
  upgrade_state="running(pid=${upgrade_pid})"
fi

printf '%s\n' "=== UPGRADE STATUS ==="
printf 'state            : %s\n' "${upgrade_state}"
printf 'completed_docs   : %s\n' "${completed_docs}"
printf 'last_doc_id      : %s\n' "${last_doc_id}"
printf 'flashcards       : %s\n' "${flashcards}"
printf 'quiz_questions   : %s\n' "${quiz_questions}"
printf 'fiches           : %s\n' "${fiches}"
printf 'last_event       : %s\n' "${last_event}"
