#!/usr/bin/env bash
# auto-submit.sh — Force submit a prompt stuck in Claude Code input
# Usage: auto-submit.sh <session> <window>

SESSION="${1:?Usage: auto-submit.sh <session> <window>}"
WINDOW="${2:?Usage: auto-submit.sh <session> <window>}"

echo "[auto-submit] Forcing Enter on ${SESSION}:${WINDOW}..."
tmux send-keys -t "${SESSION}:${WINDOW}" Enter
sleep 2
tmux send-keys -t "${SESSION}:${WINDOW}" Enter
sleep 3

pane=$(tmux capture-pane -t "${SESSION}:${WINDOW}" -p)
if echo "$pane" | grep -qE "(Thinking|Working|Reading|Bash|Agent|Running)"; then
    echo "[auto-submit] ✅ Submitted successfully"
else
    echo "[auto-submit] ⚠️  May need manual intervention"
fi
