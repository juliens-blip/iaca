# Skill: Multi-Claude Distribution (H*/S*/O*)

> Distribution automatique des tâches vers les 3 Claudes selon difficulté

---

## Vue d'ensemble

Ce skill gère la distribution des tâches vers les 3 instances Claude en fonction de leur préfixe de difficulté :

| Préfixe | Difficulté | Modèle | Window | Commande de lancement |
|---------|------------|--------|--------|----------------------|
| H* | Simple | haiku | 2 | `claude --dangerously-skip-permissions --model haiku` |
| S* | Moyenne | sonnet | 3 | `claude --dangerously-skip-permissions --model sonnet` |
| O* | Complexe | opus | 4 | `claude --dangerously-skip-permissions --model opus` |

---

## Règles de Classification

### H* - Tâches Simples (Haiku)
- Création de dossiers (mkdir)
- Fichiers de configuration (requirements.txt, package.json)
- Formatage et linting
- Recherches basiques
- Copie/déplacement de fichiers

### S* - Tâches Moyennes (Sonnet)
- Implémentation de fonctions/méthodes
- Création de composants React
- Endpoints API
- Services backend
- Tests unitaires
- Documentation

### O* - Tâches Complexes (Opus)
- Architecture système
- Intégrations LLM
- Refactoring majeur
- Debugging complexe
- Décisions de design
- Orchestration multi-services

---

## PROMPTS OBLIGATOIRES (CRITICAL)

**RÈGLE ABSOLUE:** Chaque prompt envoyé à un worker DOIT suivre ce template exact. Ne JAMAIS envoyer un prompt sans ces éléments.

### Template Prompt Complet

```
AVANT DE COMMENCER:
1. Charge @agents_library/universal-orchestrator/skills/problem-reporting.md
2. Charge @agents_library/<AGENT_APPROPRIÉ>.md
3. Si problème → écrire dans probleme.Md

Tâche <TASK_ID> : <DESCRIPTION>

Contexte:
- Projet: IACA (révision Master Droit)
- Fichiers concernés: <LISTE>

Quand terminé:
1) Mets à jour CLAUDE.md : status <TASK_ID> → COMPLETED
2) Ajoute ligne dans Task Completion Log
3) Si problème rencontré → documenter dans probleme.Md
4) Si solution non triviale → créer skill via skill-harvesting.md
```

### Mapping Tâche → Agent OBLIGATOIRE

| Type de tâche | Agent à charger |
|---------------|-----------------|
| Structure dossiers (H*) | Aucun (bash simple) |
| Config/Setup (H*) | Aucun |
| API Backend (S*) | `@agents_library/backend-architect.md` |
| Composant React (S*) | `@agents_library/frontend-developer.md` |
| Models/Schemas (S*) | `@agents_library/backend-architect.md` |
| Service LLM (O*) | `@agents_library/fullstack-developer.md` |
| Architecture (O*) | `@agents_library/backend-architect.md` |
| Debug (tout) | `@agents_library/debugger.md` |
| Tests (tout) | `@agents_library/test-engineer.md` |

---

## Fonction de Routage (avec prompts forcés)

```bash
#!/bin/bash
# route-task.sh - Route une tâche vers le bon Claude avec prompt obligatoire

SESSION="${SESSION:-iaca-orchestration}"

# Mapping task type → agent
get_agent() {
  local task_type=$1
  case "$task_type" in
    "backend"|"api"|"router") echo "@agents_library/backend-architect.md" ;;
    "frontend"|"react"|"component") echo "@agents_library/frontend-developer.md" ;;
    "service"|"llm"|"integration") echo "@agents_library/fullstack-developer.md" ;;
    "debug"|"fix") echo "@agents_library/debugger.md" ;;
    "test") echo "@agents_library/test-engineer.md" ;;
    *) echo "" ;;
  esac
}

route_task() {
  local task_id=$1
  local prompt=$2
  local task_type=${3:-"general"}  # backend, frontend, service, debug, test
  local window
  local model
  local agent

  # Déterminer window et modèle selon préfixe
  case ${task_id:0:1} in
    H|h)
      window=2
      model="haiku"
      ;;
    S|s)
      window=3
      model="sonnet"
      ;;
    O|o)
      window=4
      model="opus"
      ;;
    *)
      window=3
      model="sonnet"  # défaut
      ;;
  esac

  agent=$(get_agent "$task_type")

  echo "📤 Envoi $task_id → window $window ($model)"

  # Construire le prompt COMPLET avec agents et skills forcés
  local full_prompt="AVANT DE COMMENCER:
1. Charge @agents_library/universal-orchestrator/skills/problem-reporting.md"

  if [ -n "$agent" ]; then
    full_prompt="$full_prompt
2. Charge $agent"
  fi

  full_prompt="$full_prompt
3. Si problème → écrire dans probleme.Md

Tâche $task_id : $prompt

Quand terminé:
1) Mets à jour CLAUDE.md : status $task_id → COMPLETED
2) Si problème → documenter dans probleme.Md"

  # Envoyer la tâche
  tmux send-keys -t $SESSION:$window "$full_prompt" Enter

  # Vérifier soumission
  sleep 3
  if ! tmux capture-pane -t $SESSION:$window -p | tail -5 | grep -qE "Working|Thinking|Read"; then
    echo "⚠️  Retry Enter pour $task_id"
    tmux send-keys -t $SESSION:$window Enter
  fi
}

# Usage: route_task "S5" "Implémenter router documents" "backend"
```

---

## Distribution en Batch (avec prompts forcés)

```bash
#!/bin/bash
# distribute-batch.sh - Distribue un batch avec prompts OBLIGATOIRES

SESSION="${SESSION:-iaca-orchestration}"

# Format: "ID:TYPE:PROMPT"
# TYPE: none, backend, frontend, service, debug, test

declare -a HAIKU_TASKS=(
  "H1:none:Créer structure dossiers backend"
  "H2:none:Créer requirements.txt"
  "H3:none:Créer package.json frontend"
)

declare -a SONNET_TASKS=(
  "S1:backend:Implémenter FastAPI main.py avec config"
  "S2:backend:Créer modèles SQLAlchemy (Matiere, Document, Flashcard)"
  "S3:backend:Implémenter router documents (upload, list, delete)"
  "S4:frontend:Créer composant FlashCard avec flip 3D"
)

declare -a OPUS_TASKS=(
  "O1:service:Implémenter claude_service.py (CLI wrapper, flashcards, QCM)"
  "O2:service:Implémenter gemini_service.py (API, recommandations)"
  "O3:service:Architecture vocale Whisper+Piper+Ollama"
)

# Fonction pour construire le prompt complet
build_full_prompt() {
  local id=$1
  local type=$2
  local desc=$3
  local agent=""

  case "$type" in
    "backend") agent="@agents_library/backend-architect.md" ;;
    "frontend") agent="@agents_library/frontend-developer.md" ;;
    "service") agent="@agents_library/fullstack-developer.md" ;;
    "debug") agent="@agents_library/debugger.md" ;;
    "test") agent="@agents_library/test-engineer.md" ;;
  esac

  echo "AVANT DE COMMENCER:
1. Charge @agents_library/universal-orchestrator/skills/problem-reporting.md"

  if [ -n "$agent" ]; then
    echo "2. Charge $agent"
  fi

  echo "3. Si problème → écrire dans probleme.Md

Tâche $id : $desc

Quand terminé:
1) Mets à jour CLAUDE.md : status $id → COMPLETED
2) Si problème → documenter dans probleme.Md"
}

# Distribuer HAIKU (w2)
for task in "${HAIKU_TASKS[@]}"; do
  IFS=':' read -r id type desc <<< "$task"
  full_prompt=$(build_full_prompt "$id" "$type" "$desc")
  tmux send-keys -t $SESSION:2 "$full_prompt" Enter
  sleep 2
done

# Distribuer SONNET (w3)
for task in "${SONNET_TASKS[@]}"; do
  IFS=':' read -r id type desc <<< "$task"
  full_prompt=$(build_full_prompt "$id" "$type" "$desc")
  tmux send-keys -t $SESSION:3 "$full_prompt" Enter
  sleep 2
done

# Distribuer OPUS (w4)
for task in "${OPUS_TASKS[@]}"; do
  IFS=':' read -r id type desc <<< "$task"
  full_prompt=$(build_full_prompt "$id" "$type" "$desc")
  tmux send-keys -t $SESSION:4 "$full_prompt" Enter
  sleep 2
done

echo "✅ Batch distribué avec agents et skills forcés"
```

---

## Vérification des Workers

```bash
#!/bin/bash
# check-workers.sh - Vérifie l'état des 3 Claudes

SESSION="${SESSION:-iaca-orchestration}"

echo "🔍 État des workers Claude:"
echo ""

for w in 2 3 4; do
  case $w in
    2) name="haiku" ;;
    3) name="sonnet" ;;
    4) name="opus" ;;
  esac

  output=$(tmux capture-pane -t $SESSION:$w -p 2>/dev/null | tail -5)

  if echo "$output" | grep -qE "Working|Thinking"; then
    status="🔄 WORKING"
  elif echo "$output" | grep -qE "›|❯"; then
    status="✅ IDLE"
  else
    status="⏳ STARTING"
  fi

  echo "  w$w ($name): $status"
done
```

---

## Backups (Load Balancing)

Si un Claude est surchargé, utiliser les backups :

| Principal | Backup | Condition |
|-----------|--------|-----------|
| haiku (w2) | codex (w6) | Si haiku queue > 3 tâches |
| sonnet (w3) | - | Pas de backup |
| opus (w4) | amp (w5) | Si opus queue > 2 tâches |

```bash
# Vérifier charge et rediriger si nécessaire
check_and_redirect() {
  local task_id=$1
  local prompt=$2
  local primary_window=$3
  local backup_window=$4

  # Compter tâches en cours sur primary
  local count=$(grep -c "IN_PROGRESS.*w$primary_window" CLAUDE.md)

  if [ "$count" -ge 3 ] && [ -n "$backup_window" ]; then
    echo "⚠️  Redirection vers backup w$backup_window"
    tmux send-keys -t $SESSION:$backup_window "Tâche $task_id : $prompt" Enter
  else
    tmux send-keys -t $SESSION:$primary_window "Tâche $task_id : $prompt" Enter
  fi
}
```

---

## Économie de Tokens

| Modèle | Coût relatif | Usage optimal |
|--------|--------------|---------------|
| Haiku | 1x | Maximiser pour tâches simples |
| Sonnet | ~10x | Gros du travail |
| Opus | ~30x | Réserver pour complexe uniquement |

**Stratégie :**
- Préférer haiku quand possible
- Ne pas envoyer de tâche simple à opus
- Vérifier la classification avant envoi

---

*Skill Multi-Claude Distribution v1.0*
