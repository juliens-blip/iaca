# AGENT.md - Catalogue des Agents

> REGLE: Toujours utiliser les agents et skills de `agents_library/` - Ne jamais improviser.

---

## AGENT PRINCIPAL - UNIVERSAL ORCHESTRATOR

**Chemin:** `agents_library/agent-orchestrator-universal/universal-orchestrator.md`

**Role:** Orchestrateur multi-LLM qui divise et coordonne les taches complexes.

**Fonctions:**
- Decompose les taches en sous-taches atomiques
- Distribue aux LLMs selon complexite (Claude=complexe, Amp=moyen, Codex=simple)
- Synchronise via CLAUDE.md
- Applique methode Ralph (test/debug/fix en boucle)
- Handoff automatique a 95% tokens

**Skills integres:**
- `skills/communication-inter-agents.md` - Communication tmux
- `skills/quota-monitoring-handoff.md` - Gestion quota Claude
- `skills/task-distribution-memory-sync.md` - Distribution taches

**Usage:** Charger cet agent pour TOUTE tache complexe du projet IACA.

---

## AGENTS UTILES POUR IACA

### Workflow & Orchestration
| Agent | Usage |
|-------|-------|
| `apex-workflow` | Workflow /analyze → /plan → /implement |
| `context-manager` | Preservation contexte multi-sessions |
| `epct` | Chain-of-thought expert |

### Developpement
| Agent | Usage |
|-------|-------|
| `frontend-developer` | Interface web React |
| `backend-architect` | API FastAPI |
| `fullstack-developer` | Vue complete stack |
| `code-reviewer` | Review qualite/securite |
| `debugger` | Fix bugs |
| `test-engineer` | Tests unitaires/e2e |

### AI & Prompts
| Agent | Usage |
|-------|-------|
| `prompt-engineer` | Optimiser prompts flashcards |

### Reference
| Agent | Usage |
|-------|-------|
| `legal-advisor` | Terminologie juridique |
| `ui-ux-designer` | Design experience revision |

---

## MATRICE DE SELECTION

| Tache | Agent |
|-------|-------|
| Projet complet / tache complexe | `universal-orchestrator` |
| Feature unique multi-etapes | `apex-workflow` |
| Composant React | `frontend-developer` |
| API endpoint | `backend-architect` |
| Optimisation prompt | `prompt-engineer` |
| Debug | `debugger` |
| Tests | `test-engineer` |

---

## COMMENT UTILISER

```bash
# Charger un agent
@agents_library/agent-orchestrator-universal/universal-orchestrator.md

# Ou via Task tool
Task(subagent_type="universal-orchestrator", prompt="...")
```

---

*26 agents disponibles dans agents_library/*
