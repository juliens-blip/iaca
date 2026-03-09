# Problemes Rencontres

> Les agents documentent ici les problemes rencontres pendant l'execution des taches.

---

## Format

```markdown
### [DATE] - [AGENT] - [TACHE]
**Probleme:** Description
**Erreur:** Message d'erreur si applicable
**Contexte:** Ce qui a ete tente
**Status:** En attente / Resolu
**Solution:** (si resolu)
```

---

## Historique

### [2026-02-26] - universal-orchestrator - Orchestration tmux echec permissions
@agents: agent-orchestrator-uniersal
**Probleme:** L'orchestration multi-LLM via tmux n'a pas pu tourner de facon fiable.
**Contexte:** Les workers Claude Code restaient en mode interactif avec demandes de confirmation, et le polling `tmux capture-pane` n'etait pas fiable.
**Status:** En attente
**Constats:**
- Permissions Claude Code: chaque outil demande confirmation interactive.
- Pas de mode headless actif sur les workers.
- Polling fragile sur texte brut ANSI.
- Pas de bus de signalisation robuste entre orchestrateur et workers.
**Pistes de solution:**
1. Lancer workers avec permissions pre-acceptees (`--dangerously-skip-permissions` / `allowedTools`).
2. Preferer `claude --print -p "..."` pour des taches one-shot.
3. Introduire un bus de messages (fichiers semaphores, named pipes, Redis).
4. Evaluer un passage API natif au lieu de sessions CLI interactives.

### [2026-03-09] - codex-gpt5 (w5) - H-P18-4 backend + Ralph validation
**Probleme:** Le backend ne restait pas actif apres lancement avec `... &` dans un shell non persistant.
**Erreur:** `HEALTHCHECK_FAILED` (curl `http://localhost:8000/health` ne repondait pas)
**Contexte:**
- Commande de lancement executee en arriere-plan exactement comme demandee.
- Verification `/health` en boucle: echec.
- `ps` ne montrait aucun processus `uvicorn` actif.
**Status:** Resolu
**Pistes de solution:**
1. Lancer `uvicorn` en session active pour confirmer l'absence d'erreur applicative.
2. Relancer en mode detache robuste (`setsid ... < /dev/null`) pour eviter l'arret lors de la fermeture du shell.
**Solution:** Backend relance en mode detache via `setsid`, puis verification `curl /health` OK (`{"status":"ok"}`). Validation Ralph ensuite PASS, frontend demarre et verifie HTTP 200.
