#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$REPO_ROOT/logs"
QUALITY_REPORT="$LOG_DIR/p12_2_quality_report.md"
SUMMARY_REPORT="$LOG_DIR/post_upgrade_summary.md"
DB_PATH="$REPO_ROOT/data/iaca.db"

mkdir -p "$LOG_DIR"

cd "$REPO_ROOT"
python3 "$REPO_ROOT/scripts/audit_content_quality.py"

export REPO_ROOT
python3 - <<'PY'
from datetime import datetime, timezone
from pathlib import Path
import os
import sqlite3

repo_root = Path(os.environ["REPO_ROOT"])
log_dir = repo_root / "logs"
quality_report_path = log_dir / "p12_2_quality_report.md"
summary_path = log_dir / "post_upgrade_summary.md"
db_path = repo_root / "data" / "iaca.db"

conn = sqlite3.connect(db_path)
cur = conn.cursor()

counters = {}
for table_name in ("documents", "flashcards", "quiz_questions", "fiches"):
    cur.execute(f"SELECT COUNT(*) FROM {table_name}")
    counters[table_name] = cur.fetchone()[0]

conn.close()

top_table_lines = []
if quality_report_path.exists():
    lines = quality_report_path.read_text(encoding="utf-8").splitlines()
    capture = False
    for line in lines:
        if line.strip() == "## Top 10 Docs to Fix":
            capture = True
            continue
        if capture and line.startswith("## "):
            break
        if capture and line.startswith("|"):
            top_table_lines.append(line)

if not top_table_lines:
    top_table_lines = [
        "| Rank | doc_id | matiere | text_len | score | issue types | titre |",
        "|---:|---:|---|---:|---:|---|---|",
        "| _N/A_ | _N/A_ | _N/A_ | _N/A_ | _N/A_ | _N/A_ | Impossible d'extraire la section Top 10 |",
    ]

utc_now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
content_lines = [
    "# Post-upgrade Summary",
    "",
    f"Generated at: {utc_now}",
    "",
    "## Commands executed",
    "",
    "- `python3 scripts/audit_content_quality.py`",
    "",
    "## Global DB counters",
    "",
    "| Metric | Count |",
    "|---|---:|",
    f"| documents | {counters['documents']} |",
    f"| flashcards | {counters['flashcards']} |",
    f"| quiz_questions | {counters['quiz_questions']} |",
    f"| fiches | {counters['fiches']} |",
    "",
    "## Top 10 docs to fix (from logs/p12_2_quality_report.md)",
    "",
]
content_lines.extend(top_table_lines)
content_lines.extend([
    "",
    "## Sources",
    "",
    f"- `{quality_report_path}`",
    f"- `{db_path}`",
    "",
])

summary_path.write_text("\n".join(content_lines), encoding="utf-8")
print(f"WROTE {summary_path}")
PY
