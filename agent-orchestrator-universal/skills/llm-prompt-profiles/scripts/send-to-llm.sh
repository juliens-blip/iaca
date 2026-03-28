#!/bin/bash
# send-to-llm.sh — Send prompt to any LLM worker with correct submission protocol
# Usage: send-to-llm.sh <session> <window> <llm_type|auto> <message>
#
# llm_type: claude-code | codex | amp | bash | auto
# If "auto", detects the LLM type from pane content.

set -euo pipefail

SESSION="${1:?session required}"
WINDOW="${2:?window required}"
LLM_TYPE="${3:?llm_type required (claude-code|codex|amp|bash|auto)}"
shift 3
MESSAGE="${*:?message required}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Auto-detect if requested
if [[ "$LLM_TYPE" == "auto" ]]; then
  LLM_TYPE=$("$SCRIPT_DIR/detect-llm-type.sh" "$SESSION" "$WINDOW")
  echo "Detected: $LLM_TYPE (W$WINDOW)"
fi

# Activity patterns per LLM
case "$LLM_TYPE" in
  claude-code) ACTIVITY_RE="Working|Thinking|Explored|Read|Baked|Hullaballooing|Simmering" ;;
  codex)       ACTIVITY_RE="Working|Ran |• |Waiting for background" ;;
  amp)         ACTIVITY_RE="Discombobulating|Simmering|Running|Hullaballooing" ;;
  bash)        ACTIVITY_RE="NEVER_MATCH_BASH_IS_SYNC" ;;
  *)           echo "WARN: unknown LLM type '$LLM_TYPE', using generic patterns"; ACTIVITY_RE="Working|Thinking|Running" ;;
esac

# ── SEND ──────────────────────────────────────────────────

if [[ "$LLM_TYPE" == "codex" ]]; then
  # Codex: clear buffer, send message, double-Enter with delay
  tmux send-keys -t "$SESSION:$WINDOW" C-u
  sleep 0.5
  tmux send-keys -t "$SESSION:$WINDOW" "$MESSAGE" Enter
  sleep 2
  tmux send-keys -t "$SESSION:$WINDOW" Enter
  echo "Sent to Codex W$WINDOW (double-Enter)"

elif [[ "$LLM_TYPE" == "bash" ]]; then
  # Bash: send command directly
  tmux send-keys -t "$SESSION:$WINDOW" "$MESSAGE" Enter
  echo "Sent to bash W$WINDOW"
  exit 0

else
  # Claude Code / AMP: single Enter
  tmux send-keys -t "$SESSION:$WINDOW" "$MESSAGE" Enter
  sleep 1
  # Safety double-Enter for Claude Code (handles paste edge case)
  tmux send-keys -t "$SESSION:$WINDOW" Enter
  echo "Sent to $LLM_TYPE W$WINDOW"
fi

# ── VERIFY ────────────────────────────────────────────────

sleep 3
output=$(tmux capture-pane -t "$SESSION:$WINDOW" -p | tail -10)

if echo "$output" | grep -qE "$ACTIVITY_RE"; then
  echo "OK: $LLM_TYPE active (W$WINDOW)"
  exit 0
fi

# ── RETRY ─────────────────────────────────────────────────

echo "RETRY: no activity, sending Enter again (W$WINDOW)"
tmux send-keys -t "$SESSION:$WINDOW" Enter
sleep 3

output2=$(tmux capture-pane -t "$SESSION:$WINDOW" -p | tail -10)
if echo "$output2" | grep -qE "$ACTIVITY_RE"; then
  echo "OK: $LLM_TYPE active after retry (W$WINDOW)"
  exit 0
fi

# ── FULL RESEND ───────────────────────────────────────────

echo "RESEND: clearing and re-sending full prompt (W$WINDOW)"
tmux send-keys -t "$SESSION:$WINDOW" C-c
sleep 1
tmux send-keys -t "$SESSION:$WINDOW" C-u
sleep 0.5

if [[ "$LLM_TYPE" == "codex" ]]; then
  tmux send-keys -t "$SESSION:$WINDOW" "$MESSAGE" Enter
  sleep 2
  tmux send-keys -t "$SESSION:$WINDOW" Enter
else
  tmux send-keys -t "$SESSION:$WINDOW" "$MESSAGE" Enter
  sleep 1
  tmux send-keys -t "$SESSION:$WINDOW" Enter
fi

sleep 4
output3=$(tmux capture-pane -t "$SESSION:$WINDOW" -p | tail -10)
if echo "$output3" | grep -qE "$ACTIVITY_RE"; then
  echo "OK: $LLM_TYPE active after resend (W$WINDOW)"
  exit 0
fi

echo "WARN: $LLM_TYPE still idle after full retry cycle (W$WINDOW)"
exit 1
