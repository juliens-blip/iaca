#!/usr/bin/env bash
set -euo pipefail

SESSION="${1:-orchestration-iaca}"
PROJECT_DIR="${2:-$(pwd)}"
ORCH_WINDOW="${3:-4}"

if [[ ! -d "$PROJECT_DIR" ]]; then
  echo "ERROR: project directory not found: $PROJECT_DIR"
  exit 1
fi

ensure_session() {
  if ! tmux has-session -t "$SESSION" 2>/dev/null; then
    tmux new-session -d -s "$SESSION" -n main -c "$PROJECT_DIR"
  fi
}

ensure_window() {
  local index="$1"
  local name="$2"
  if tmux list-windows -t "$SESSION" | grep -q "^${index}:"; then
    tmux rename-window -t "$SESSION:$index" "$name"
    tmux respawn-window -k -t "$SESSION:$index" -c "$PROJECT_DIR"
  else
    tmux new-window -d -t "$SESSION:$index" -n "$name" -c "$PROJECT_DIR"
  fi
}

cleanup_extra_windows() {
  local allowed_regex='^(0|1|2|3|4|5|8):'
  while IFS= read -r line; do
    if [[ ! "$line" =~ $allowed_regex ]]; then
      local idx
      idx="${line%%:*}"
      tmux kill-window -t "$SESSION:$idx"
    fi
  done < <(tmux list-windows -t "$SESSION")
}

start_in_window() {
  local index="$1"
  local cmd="$2"
  local current
  current="$(tmux list-panes -t "$SESSION:$index" -F "#{pane_current_command}" | head -1 || true)"

  if [[ "$current" == "claude" || "$current" == "node" || "$current" == "amp" || "$current" == "ollama" ]]; then
    return 0
  fi

  tmux send-keys -t "$SESSION:$index" "cd \"$PROJECT_DIR\" && $cmd" Enter
}

ensure_session

# Universal-orchestrator window map (Codex Lead with AMP orchestrator)
ensure_window 1 "haiku"
ensure_window 2 "sonnet"
ensure_window 3 "opus"
ensure_window 4 "opus-orch"
ensure_window 5 "codex"
ensure_window 8 "claude-worker"
cleanup_extra_windows

if command -v claude >/dev/null 2>&1; then
  start_in_window 1 "claude --model claude-haiku-4-5-20251001 --dangerously-skip-permissions"
else
  echo "WARN: claude not found in PATH for haiku worker"
fi

if command -v claude >/dev/null 2>&1; then
  start_in_window 2 "claude --model claude-sonnet-4-6 --dangerously-skip-permissions"
else
  echo "WARN: claude not found in PATH for sonnet worker"
fi

if command -v claude >/dev/null 2>&1; then
  start_in_window 3 "claude --model claude-opus-4-6 --dangerously-skip-permissions"
else
  echo "WARN: claude not found in PATH for opus worker"
fi

if command -v claude >/dev/null 2>&1; then
  start_in_window 4 "claude --model claude-opus-4-6 --dangerously-skip-permissions"
else
  echo "WARN: claude not found in PATH for orchestrator"
fi

if command -v codex >/dev/null 2>&1; then
  start_in_window 5 "codex -m gpt-5.3-codex -c reasoning_effort=low -c update_on_startup=false --dangerously-bypass-approvals-and-sandbox"
else
  echo "WARN: codex not found in PATH for codex worker"
fi

if command -v claude >/dev/null 2>&1; then
  start_in_window 8 "claude --model claude-opus-4-6 --dangerously-skip-permissions"
else
  echo "WARN: claude not found in PATH for extra worker"
fi

# Send orchestrator bootstrap prompt to amp orchestrator window.
"$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/start-opus-orchestrator.sh" "$SESSION" "$ORCH_WINDOW" "$PROJECT_DIR"

echo ""
echo "Session ready: $SESSION"
tmux list-windows -t "$SESSION"
echo ""
echo "Attach with: tmux attach -t $SESSION"
