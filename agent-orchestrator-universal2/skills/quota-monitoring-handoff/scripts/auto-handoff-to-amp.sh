#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

exec "$SCRIPT_DIR/auto-handoff.sh" "${1:-orchestration-$(basename "$(pwd)")}" "${2:-$(pwd)}" "${3:-$(pwd)/HANDOFF_TO_AMP.md}" "${4:-codex}" "${5:-amp-orchestrator}" "${6:-CODEX}" "${7:-AMP}"
