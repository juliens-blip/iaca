#!/usr/bin/env bash
set -euo pipefail

SESSION="${1:-orchestration-$(basename "$(pwd)")}"
PROJECT_DIR="${2:-$(pwd)}"
HANDOFF_FILE="${3:-$PROJECT_DIR/HANDOFF_TO_AMP.md}"
SOURCE_WINDOW="${4:-codex}"
TARGET_WINDOW="${5:-amp-orchestrator}"
SOURCE_NAME="${6:-CODEX}"
TARGET_NAME="${7:-AMP}"

quota=$(tmux capture-pane -t "$SESSION:$SOURCE_WINDOW" -p 2>/dev/null | grep -oE "used [0-9]+%" | grep -oE "[0-9]+" | tail -1 || true)

cat > "$HANDOFF_FILE" << EOF2
# HANDOFF SUMMARY

**Date:** $(date '+%Y-%m-%d %H:%M')
**From:** $SOURCE_NAME
**To:** $TARGET_NAME
**Reason:** quota reached (${quota:-unknown}%)

## Actions
1) Read this file
2) Read $PROJECT_DIR/CLAUDE.md
3) Check workers via tmux
EOF2

tmux send-keys -t "$SESSION:$TARGET_WINDOW" "HANDOFF: you are the new orchestrator. Read $HANDOFF_FILE and $PROJECT_DIR/CLAUDE.md" Enter

echo "Handoff message sent to window $TARGET_WINDOW"
