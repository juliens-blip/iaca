#!/usr/bin/env bash
set -euo pipefail

SESSION="${1:-orchestration-$(basename "$(pwd)")}"
WINDOW="${2:-4}"
PROJECT_DIR="${3:-$(pwd)}"

# Try multiple agent path locations
AGENT_PATH=""
for path in "agents_library/universal-orchestrator.md" "agent-orchestrator-universal/universal-orchestrator.md"; do
  if [[ -f "$PROJECT_DIR/$path" ]]; then
    AGENT_PATH="$path"
    break
  fi
done

if [[ -z "$AGENT_PATH" ]]; then
  echo "ERROR: universal-orchestrator.md not found in:"
  echo "  - $PROJECT_DIR/agents_library/universal-orchestrator.md"
  echo "  - $PROJECT_DIR/agent-orchestrator-universal/universal-orchestrator.md"
  exit 1
fi

TARGET="${SESSION}:${WINDOW}"

if ! tmux has-session -t "$SESSION" 2>/dev/null; then
  tmux new-session -d -s "$SESSION" -n bash -c "$PROJECT_DIR"
fi

if ! tmux list-windows -t "$SESSION" | grep -q "^${WINDOW}:"; then
  tmux new-window -t "$SESSION:$WINDOW" -n opus-orch -c "$PROJECT_DIR"
fi

tmux send-keys -t "$TARGET" C-c
sleep 0.2
tmux send-keys -t "$TARGET" "cd \"$PROJECT_DIR\" && claude --model claude-opus-4-6 --dangerously-skip-permissions" Enter

for _ in $(seq 1 40); do
  if tmux list-panes -t "$TARGET" -F "#{pane_current_command}" 2>/dev/null | grep -qE "^(claude|node)$"; then
    break
  fi
  sleep 0.5
done

if ! tmux list-panes -t "$TARGET" -F "#{pane_current_command}" 2>/dev/null | grep -qE "^(claude|node)$"; then
  echo "ERROR: claude process not confirmed in $TARGET"
  tmux capture-pane -t "$TARGET" -p | tail -20
  exit 1
fi

PROMPT=$(cat <<EOF
@${AGENT_PATH}

Tu es l'orchestrateur principal de la session tmux '${SESSION}'.
Tu opères depuis la fenêtre '${WINDOW}' (Opus, orchestrateur).
Hiérarchie à appliquer: Opus (w4, toi) > Sonnet (w2) > Claude w8 > Codex (w5) > Haiku (w1).
Lis CLAUDE.md, vérifie l'état des workers, puis exécute immédiatement le Session Bootstrap Protocol de l'agent chargé.
EOF
)

# Paste/send full multi-line prompt to claude opus.
tmux load-buffer - <<<"$PROMPT"
tmux paste-buffer -t "$TARGET"
tmux send-keys -t "$TARGET" Enter
sleep 1
tmux send-keys -t "$TARGET" Enter

sleep 2
echo "Prompt orchestrator sent to $TARGET"
echo "--- Last pane lines ---"
tmux capture-pane -t "$TARGET" -p | tail -20
