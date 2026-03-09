# Skill: Task Distribution & Memory Sync

> Gestion des tâches avec IDs et synchronisation via CLAUDE.md

---

## Format des Task IDs

Convention : Préfixe + numéro
- `H-001`, `H-002` → Tâches simples (haiku)
- `S-001`, `S-002` → Tâches moyennes (sonnet)
- `O-001`, `O-002` → Tâches complexes (opus)

---

## Structure CLAUDE.md

```markdown
# Mémoire Projet - IACA

## État Global
- **Tâche principale:** [description]
- **Progression:** 0%
- **Session:** iaca-orchestration

## Task Assignment Queue
| ID | Task | Window | Status | Created |
|----|------|--------|--------|---------|
| H-001 | Créer dossiers | w2 (haiku) | IN_PROGRESS | 2026-02-27 |
| S-001 | Implémenter API | w3 (sonnet) | PENDING | 2026-02-27 |
| O-001 | Architecture | w4 (opus) | PENDING | 2026-02-27 |

## Task Completion Log
| Date | Window | ID | Status | Notes |
|------|--------|-----|--------|-------|

## Problèmes
Voir probleme.Md
```

---

## Statuts

| Statut | Description |
|--------|-------------|
| PENDING | En attente |
| IN_PROGRESS | En cours |
| COMPLETED | Terminé |
| BLOCKED | Bloqué |

---

## Polling CLAUDE.md

```bash
# Toutes les 60-90 secondes
while true; do
  # Lire statuts
  grep -E "IN_PROGRESS|COMPLETED|BLOCKED" CLAUDE.md

  # Compter
  echo "Completed: $(grep -c COMPLETED CLAUDE.md)"
  echo "In Progress: $(grep -c IN_PROGRESS CLAUDE.md)"

  sleep 80
done
```

---

*Skill Task Distribution v1.0*
