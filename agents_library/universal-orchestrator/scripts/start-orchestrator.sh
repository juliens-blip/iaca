#!/bin/bash
# start-orchestrator.sh
# Lance 3 sessions Claude (haiku, sonnet, opus) + autres LLMs

SESSION="iaca-orchestration"
PROJECT="/home/julien/Documents/IACA"
LLM_STARTUP_WAIT=5

echo "🚀 Démarrage Universal Orchestrator (Multi-Claude)..."
echo "   Projet: $PROJECT"

# Vérifier si session existe déjà
if tmux has-session -t $SESSION 2>/dev/null; then
    echo "⚠️  Session $SESSION existe déjà."
    read -p "Supprimer et recréer ? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        tmux kill-session -t $SESSION
    else
        echo "Attachement à la session existante..."
        tmux attach -t $SESSION
        exit 0
    fi
fi

# Créer session avec fenêtre principale
echo "📦 Création session tmux..."
tmux new-session -d -s $SESSION -n main -c $PROJECT

# Créer fenêtres pour chaque LLM
echo "📦 Création des fenêtres..."
tmux new-window -t $SESSION -n claude-haiku -c $PROJECT       # w2
tmux new-window -t $SESSION -n claude-sonnet -c $PROJECT      # w3
tmux new-window -t $SESSION -n claude-opus -c $PROJECT        # w4
tmux new-window -t $SESSION -n amp -c $PROJECT                # w5
tmux new-window -t $SESSION -n codex -c $PROJECT              # w6
tmux new-window -t $SESSION -n antigravity-proxy -c $PROJECT  # w7
tmux new-window -t $SESSION -n antigravity -c $PROJECT        # w8
tmux new-window -t $SESSION -n ollama -c $PROJECT             # w9

# Démarrer les 3 Claudes avec --dangerously-skip-permissions
echo "🤖 Démarrage Claude Haiku (w2 - tâches simples H*)..."
tmux send-keys -t $SESSION:2 "claude --dangerously-skip-permissions --model haiku" Enter
sleep $LLM_STARTUP_WAIT

echo "🤖 Démarrage Claude Sonnet (w3 - tâches moyennes S*)..."
tmux send-keys -t $SESSION:3 "claude --dangerously-skip-permissions --model sonnet" Enter
sleep $LLM_STARTUP_WAIT

echo "🤖 Démarrage Claude Opus (w4 - tâches complexes O*)..."
tmux send-keys -t $SESSION:4 "claude --dangerously-skip-permissions --model opus" Enter
sleep $LLM_STARTUP_WAIT

# Démarrer Amp si disponible
if command -v amp &> /dev/null; then
    echo "🤖 Démarrage Amp (w5 - backup complexe)..."
    tmux send-keys -t $SESSION:5 "amp -m large --dangerously-allow-all" Enter
    sleep $LLM_STARTUP_WAIT
else
    echo "⏭️  Amp non installé"
fi

# Démarrer Codex si disponible
if command -v codex &> /dev/null; then
    echo "🤖 Démarrage Codex (w6 - backup simple)..."
    tmux send-keys -t $SESSION:6 "codex --dangerously-bypass-approvals-and-sandbox" Enter
    sleep $LLM_STARTUP_WAIT
else
    echo "⏭️  Codex non installé"
fi

# Antigravity si disponible
if command -v antigravity-claude-proxy &> /dev/null; then
    echo "🔌 Démarrage Antigravity Proxy (w7)..."
    tmux send-keys -t $SESSION:7 "antigravity-claude-proxy start" Enter
    sleep 8
    echo "🤖 Démarrage Antigravity (w8)..."
    tmux send-keys -t $SESSION:8 "export ANTHROPIC_BASE_URL=\"http://localhost:8080\"" Enter
    tmux send-keys -t $SESSION:8 "claude --dangerously-skip-permissions --model claude-opus-4-5-thinking" Enter
else
    echo "⏭️  Antigravity non installé"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "✅ Universal Orchestrator prêt !"
echo ""
echo "📋 Fenêtres:"
echo "   2: claude-haiku  (H*)"
echo "   3: claude-sonnet (S*)"
echo "   4: claude-opus   (O*) ← ORCHESTRATEUR"
echo "   5: amp, 6: codex, 7-8: antigravity, 9: ollama"
echo ""
echo "🎮 Navigation: Ctrl+b puis 2/3/4/5/6"
echo ""
echo "🚀 Pour attacher: tmux attach -t $SESSION"
echo "═══════════════════════════════════════════════════════════"
