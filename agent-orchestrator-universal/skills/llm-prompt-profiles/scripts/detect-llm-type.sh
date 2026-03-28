#!/bin/bash
# detect-llm-type.sh — Detect which LLM runs in a tmux pane
# Usage: detect-llm-type.sh <session> <window>
# Returns: claude-code | codex | amp | bash | unknown

set -euo pipefail

SESSION="${1:?session required}"
WINDOW="${2:?window required}"

output=$(tmux capture-pane -t "$SESSION:$WINDOW" -p 2>/dev/null | tail -20)
window_name=$(tmux list-windows -t "$SESSION" -F '#{window_index}:#{window_name}' 2>/dev/null | grep "^$WINDOW:" | cut -d: -f2)

# 1. Check by window name first (fastest)
case "$window_name" in
  *codex*)    echo "codex"; exit 0 ;;
  *amp*)      echo "amp"; exit 0 ;;
  *claude*|*haiku*|*sonnet*|*opus*) echo "claude-code"; exit 0 ;;
esac

# 2. Check by content patterns
if echo "$output" | grep -qE "gpt-5|codex|› "; then
  echo "codex"
elif echo "$output" | grep -qE "Discombobulating|Simmering|Hullaballooing"; then
  echo "amp"
elif echo "$output" | grep -qE "❯|bypass permissions|auto-compact|Baked for"; then
  echo "claude-code"
elif echo "$output" | grep -qE '^\$|^julien@|^root@'; then
  echo "bash"
else
  echo "unknown"
fi
