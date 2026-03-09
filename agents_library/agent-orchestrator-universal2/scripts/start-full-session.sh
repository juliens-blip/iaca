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
  local allowed_regex='^(0|1|2|3|4|5|6):'
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

  if [[ "$current" == "codex" || "$current" == "node" || "$current" == "amp" || "$current" == "ollama" || "$current" == "antigravity" || "$current" == "antigravity-claude-proxy" || "$current" == "claude" ]]; then
    return 0
  fi

  tmux send-keys -t "$SESSION:$index" "cd \"$PROJECT_DIR\" && $cmd" Enter
}

ollama_is_running() {
  if ! command -v ollama >/dev/null 2>&1; then
    return 1
  fi
  ollama list >/dev/null 2>&1
}

ensure_session

# Universal-orchestrator2 window map (Universal-1 style hierarchy)
ensure_window 1 "codex-fast"
ensure_window 2 "amp"
ensure_window 3 "antigravity-proxy"
ensure_window 4 "codex-orchestrator"
ensure_window 5 "antigravity"
ensure_window 6 "ollama"
cleanup_extra_windows

if command -v codex >/dev/null 2>&1; then
  start_in_window 1 "codex -m gpt-5.3-codex -c reasoning_effort=low -c update_on_startup=false --dangerously-bypass-approvals-and-sandbox"
else
  echo "WARN: codex not found in PATH"
fi

if command -v amp >/dev/null 2>&1; then
  start_in_window 2 "amp -m large --dangerously-allow-all"
else
  echo "WARN: amp not found in PATH"
fi

if command -v antigravity-claude-proxy >/dev/null 2>&1; then
  start_in_window 3 "antigravity-claude-proxy start --fallback"
else
  echo "WARN: antigravity-claude-proxy not found in PATH"
fi

if command -v claude >/dev/null 2>&1; then
  # Antigravity worker runs through Claude CLI routed to local proxy.
  # This gives an interactive terminal chat worker in w5.
  start_in_window 5 "ANTHROPIC_BASE_URL=\"http://localhost:8080\" ANTHROPIC_AUTH_TOKEN=\"test\" claude --dangerously-skip-permissions --model claude-opus-4-5-thinking"
else
  echo "WARN: claude not found in PATH (required for antigravity worker via proxy)"
fi

if command -v ollama >/dev/null 2>&1; then
  if ollama_is_running; then
    tmux send-keys -t "$SESSION:6" "cd \"$PROJECT_DIR\" && echo \"Ollama already running on 127.0.0.1:11434\" && ollama list" Enter
  else
    start_in_window 6 "ollama serve"
  fi
else
  echo "WARN: ollama not found in PATH"
fi

# Send orchestrator bootstrap prompt to codex orchestrator window.
"$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/start-codex-orchestrator.sh" "$SESSION" "$ORCH_WINDOW" "$PROJECT_DIR"

echo ""
echo "Session ready: $SESSION"
tmux list-windows -t "$SESSION"
echo ""
echo "Attach with: tmux attach -t $SESSION"
