# Skill: Quota Monitoring & Handoff

> Monitoring des quotas Claude et handoff automatique

---

## Seuils

| Quota | Action |
|-------|--------|
| < 75% | OK, travail normal |
| 75-92% | Attention, préparer handoff |
| >= 93% | HANDOFF IMMÉDIAT |

---

## Vérifier Quota

```bash
tmux capture-pane -t $SESSION:claude -p | grep -oE "used [0-9]+%"
```

---

## Handoff vers AMP

À 93%, transférer le contrôle :

```bash
tmux send-keys -t $SESSION:5 "HANDOFF: Tu deviens orchestrateur. Lis CLAUDE.md section 'Tâches Restantes' et continue." Enter
```

---

*Skill Quota Monitoring v1.0*
