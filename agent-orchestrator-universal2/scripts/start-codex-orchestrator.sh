#!/usr/bin/env bash
set -euo pipefail

SESSION="${1:-orchestration-$(basename "$(pwd)")}"
WINDOW="${2:-4}"
PROJECT_DIR="${3:-$(pwd)}"
AGENT_PATH="agents_library/agent-orchestrator-universal2/universal-orchestrator2.md"
TARGET="${SESSION}:${WINDOW}"

if [[ ! -f "$PROJECT_DIR/$AGENT_PATH" ]]; then
  echo "ERROR: agent file not found: $PROJECT_DIR/$AGENT_PATH"
  exit 1
fi

if ! tmux has-session -t "$SESSION" 2>/dev/null; then
  tmux new-session -d -s "$SESSION" -n bash -c "$PROJECT_DIR"
fi

if ! tmux list-windows -t "$SESSION" | grep -q "^${WINDOW}:"; then
  tmux new-window -t "$SESSION:$WINDOW" -n codex -c "$PROJECT_DIR"
fi

tmux send-keys -t "$TARGET" C-c
sleep 0.2
tmux send-keys -t "$TARGET" "cd \"$PROJECT_DIR\" && codex -m gpt-5.3-codex -c reasoning_effort=high -c update_on_startup=false --dangerously-bypass-approvals-and-sandbox" Enter

for _ in $(seq 1 40); do
  if tmux list-panes -t "$TARGET" -F "#{pane_current_command}" 2>/dev/null | grep -qE "^(codex|node)$"; then
    break
  fi
  sleep 0.5
done

if tmux capture-pane -t "$TARGET" -p | grep -q "Update now"; then
  tmux send-keys -t "$TARGET" "2" Enter
  sleep 1
  tmux send-keys -t "$TARGET" Enter
  sleep 1
fi

if ! tmux list-panes -t "$TARGET" -F "#{pane_current_command}" 2>/dev/null | grep -qE "^(codex|node)$"; then
  echo "ERROR: codex process not confirmed in $TARGET"
  tmux capture-pane -t "$TARGET" -p | tail -20
  exit 1
fi

PROMPT=$(cat <<EOF
@${AGENT_PATH}

Tu es l'orchestrateur principal de la session tmux '${SESSION}'.
Tu opères depuis la fenêtre '${WINDOW}' (Codex gpt-5.3-codex, reasoning_effort=high).
Hiérarchie à appliquer: Codex orchestrator high (toi) > AMP > Antigravity > Codex fast > Ollama.
Lis CLAUDE.md, vérifie l'état des workers, puis exécute immédiatement le Session Bootstrap Protocol de l'agent chargé.
EOF
)

# Paste/send full multi-line prompt to codex.
tmux load-buffer - <<<"$PROMPT"
tmux paste-buffer -t "$TARGET"
tmux send-keys -t "$TARGET" Enter
sleep 1
tmux send-keys -t "$TARGET" Enter

sleep 2
echo "Prompt orchestrator sent to $TARGET"
echo "--- Last pane lines ---"
tmux capture-pane -t "$TARGET" -p | tail -20
