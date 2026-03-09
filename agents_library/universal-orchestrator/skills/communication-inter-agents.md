# Skill: Communication Inter-Agents (tmux)

> Communication entre LLMs via tmux send-keys

---

## Vue d'ensemble

Ce skill gère la communication entre l'orchestrateur et les workers LLM via tmux.

---

## Fenêtres tmux

| Window | Nom | LLM | Difficulté |
|--------|-----|-----|------------|
| 0 | main | Terminal | - |
| 2 | claude-haiku | Claude haiku | Simple (H*) |
| 3 | claude-sonnet | Claude sonnet | Moyenne (S*) |
| 4 | claude-opus | Claude opus | Complexe (O*) |
| 5 | amp | AMP | Backup O* |
| 6 | codex | Codex | Backup H* |
| 7 | antigravity-proxy | Proxy | - |
| 8 | antigravity | Antigravity | Complexe |
| 9 | ollama | Ollama | Vocal local |

---

## RÈGLE ABSOLUE - Prompts Obligatoires

**JAMAIS envoyer un prompt sans ces éléments :**
1. ✅ Chargement du skill `problem-reporting.md`
2. ✅ Chargement de l'agent approprié (si applicable)
3. ✅ Instruction de mise à jour CLAUDE.md
4. ✅ Instruction de reporting problème dans probleme.Md

---

## Commandes de Base

### Envoyer un message (MAUVAIS - NE PAS FAIRE)

```bash
# ❌ INCORRECT - prompt trop simple, pas d'agent, pas de skill
tmux send-keys -t $SESSION:2 "Tâche H1 : Créer dossiers" Enter
```

### Envoyer un message (CORRECT - TOUJOURS FAIRE)

```bash
# ✅ CORRECT - prompt complet avec agents et skills
tmux send-keys -t $SESSION:2 "AVANT DE COMMENCER:
1. Charge @agents_library/universal-orchestrator/skills/problem-reporting.md
2. Si problème → écrire dans probleme.Md

Tâche H1 : Créer structure dossiers backend/app/{models,routers,services,schemas}

Quand terminé:
1) Mets à jour CLAUDE.md : status H1 → COMPLETED
2) Si problème → documenter dans probleme.Md" Enter

# ✅ CORRECT - tâche backend avec agent
tmux send-keys -t $SESSION:3 "AVANT DE COMMENCER:
1. Charge @agents_library/universal-orchestrator/skills/problem-reporting.md
2. Charge @agents_library/backend-architect.md
3. Si problème → écrire dans probleme.Md

Tâche S1 : Implémenter FastAPI main.py avec CORS et healthcheck

Quand terminé:
1) Mets à jour CLAUDE.md : status S1 → COMPLETED
2) Si problème → documenter dans probleme.Md" Enter

# ✅ CORRECT - tâche service LLM avec agent
tmux send-keys -t $SESSION:4 "AVANT DE COMMENCER:
1. Charge @agents_library/universal-orchestrator/skills/problem-reporting.md
2. Charge @agents_library/fullstack-developer.md
3. Charge @agents_library/universal-orchestrator/skills/skill-harvesting.md
4. Si problème → écrire dans probleme.Md

Tâche O1 : Implémenter claude_service.py (CLI wrapper, génération flashcards/QCM)

Quand terminé:
1) Mets à jour CLAUDE.md : status O1 → COMPLETED
2) Si problème → documenter dans probleme.Md
3) Si solution complexe → créer skill via skill-harvesting.md" Enter
```

### Vérifier un LLM

```bash
# Capturer les dernières lignes
tmux capture-pane -t $SESSION:N -p | tail -20

# Vérifier si travaille
tmux capture-pane -t $SESSION:N -p | grep -E "Working|Thinking"
```

### Soumettre si en attente

```bash
# Si le prompt n'est pas soumis, envoyer Enter
tmux send-keys -t $SESSION:N Enter
```

---

## Vérifier Tous les LLMs

```bash
# Tous les Claudes
for w in 2 3 4; do
  echo "=== Window $w (Claude) ==="
  tmux capture-pane -t $SESSION:$w -p | tail -10
done

# Tous les LLMs
for w in 2 3 4 5 6; do
  echo "=== Window $w ==="
  tmux capture-pane -t $SESSION:$w -p | tail -10
done
```

---

## Script d'Envoi Vérifié

```bash
#!/bin/bash
# send-verified.sh - Envoie et vérifie la soumission

SESSION="${1:-iaca-orchestration}"
WINDOW="$2"
PROMPT="$3"

# Envoyer
tmux send-keys -t $SESSION:$WINDOW "$PROMPT" Enter

# Attendre
sleep 3

# Vérifier
output=$(tmux capture-pane -t $SESSION:$WINDOW -p | tail -10)

if echo "$output" | grep -qE "Working|Thinking|Explored|Read"; then
  echo "✅ Prompt soumis et en cours"
else
  echo "⚠️  Retry Enter"
  tmux send-keys -t $SESSION:$WINDOW Enter
  sleep 2

  # Re-vérifier
  output=$(tmux capture-pane -t $SESSION:$WINDOW -p | tail -10)
  if echo "$output" | grep -qE "Working|Thinking|Explored|Read"; then
    echo "✅ OK après retry"
  else
    echo "❌ Échec - vérifier manuellement"
  fi
fi
```

---

## Détection d'État

### Signes de WORKING
- `Working (Xs • esc to interrupt)`
- `Thinking...`
- `Reading file...`
- `Explored`

### Signes de DONE/IDLE
- `files changed +X ~Y -Z`
- Prompt `›` ou `❯` vide
- Pas de changement pendant 30s

### Signes de PROBLÈME
- `Error:`
- `Out of Credits`
- `rate limit`

---

## Annuler et Relancer

```bash
# Annuler tâche en cours
tmux send-keys -t $SESSION:N C-c
sleep 2

# Relancer avec nouveau prompt
tmux send-keys -t $SESSION:N "Nouveau prompt" Enter
```

---

## Navigation tmux

| Raccourci | Action |
|-----------|--------|
| `Ctrl+b 2` | Aller à haiku |
| `Ctrl+b 3` | Aller à sonnet |
| `Ctrl+b 4` | Aller à opus |
| `Ctrl+b n` | Fenêtre suivante |
| `Ctrl+b p` | Fenêtre précédente |
| `Ctrl+b w` | Liste des fenêtres |
| `Ctrl+b d` | Détacher |

---

*Skill Communication Inter-Agents v1.0*
