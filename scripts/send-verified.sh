#!/usr/bin/env bash
# send-verified.sh — Send a prompt to a tmux worker and verify it was submitted
# Usage: send-verified.sh <session> <window> "prompt text"

set -euo pipefail

SESSION="${1:?Usage: send-verified.sh <session> <window> <prompt>}"
WINDOW="${2:?Usage: send-verified.sh <session> <window> <prompt>}"
PROMPT="${3:?Usage: send-verified.sh <session> <window> <prompt>}"
MAX_RETRIES=3

send_prompt() {
    # Clear any stuck input first
    tmux send-keys -t "${SESSION}:${WINDOW}" C-c 2>/dev/null || true
    sleep 0.5
    # Send the prompt
    tmux send-keys -t "${SESSION}:${WINDOW}" "$PROMPT" Enter
    sleep 1
    # Double-Enter (known tmux issue with Claude Code)
    tmux send-keys -t "${SESSION}:${WINDOW}" Enter
}

check_activity() {
    local before after
    before=$(tmux capture-pane -t "${SESSION}:${WINDOW}" -p | md5sum)
    sleep 3
    after=$(tmux capture-pane -t "${SESSION}:${WINDOW}" -p | md5sum)
    [[ "$before" != "$after" ]]
}

for attempt in $(seq 1 $MAX_RETRIES); do
    echo "[send-verified] Attempt $attempt/$MAX_RETRIES to w${WINDOW}..."
    send_prompt
    sleep 3

    # Check if prompt was submitted (look for activity indicators)
    pane_content=$(tmux capture-pane -t "${SESSION}:${WINDOW}" -p)
    if echo "$pane_content" | grep -qE "(Thinking|Working|Reading|Bash|Agent|Galloping|Drizzling|Gusting|Sautéed|Churned|Baked|Cooked|Running)"; then
        echo "[send-verified] ✅ Worker w${WINDOW} is active"
        exit 0
    fi

    if check_activity; then
        echo "[send-verified] ✅ Worker w${WINDOW} shows activity"
        exit 0
    fi

    echo "[send-verified] ⚠️  No activity detected, retrying..."
done

echo "[send-verified] ❌ Failed to submit after $MAX_RETRIES attempts"
exit 1
