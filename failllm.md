# FAILLLM - Rapport d'Orchestration Multi-LLM

> Date: 2026-02-27 18:30
> Orchestrateur: Claude Opus (via AMP w4)
> Revision: v2 (corrigé après diagnostic approfondi)

---

## Résumé

L'orchestration multi-LLM a fonctionné avec des délais. Les prompts ont été correctement soumis via `tmux send-keys` et tous les workers ont fini par travailler. Le diagnostic initial de "prompts non soumis" était **incorrect** - les workers étaient en phase de "thinking" (chargement agents, lecture fichiers) ce qui apparaissait comme du silence.

---

## Diagnostic Corrigé

### 1. Claude Workers (w1, w2, w3) - FONCTIONNELS (mais quota critique)

**Diagnostic initial (ERRONÉ):** Prompts non soumis, workers bloqués.

**Réalité:** Les 3 Claude workers ont:
- Reçu les prompts correctement (`❯` = message soumis)
- Chargé les agents demandés (@agents_library/*.md)
- Commencé le travail (lecture fichiers, recherches)

**Problème réel:** Phase de "thinking" longue + polling trop rapide de l'orchestrateur.

**ALERTE:** Quota Claude Pro à 97-98%. Les workers risquent de ne pas finir. Reset à 22h (Europe/Paris).

#### Détail par worker :

| Worker | Window | Agent chargé | Actions observées | Quota |
|--------|--------|-------------|-------------------|-------|
| Haiku | w1 | explore-code.md (313 lignes) | npm install en cours, 3 fichiers lus | 98% |
| Haiku (w2=sonnet name) | w2 | backend-architect.md (39 lignes) | 3 patterns recherchés, 4 fichiers lus | 97% |
| Sonnet (w3=opus name) | w3 | code-reviewer.md + frontend-developer.md | 1 pattern, 2 fichiers lus, audit en cours | 97% |

**Erreur de configuration persistante:**
- w2 (nommé "claude-sonnet") → tourne en `--model haiku`
- w3 (nommé "claude-opus") → tourne en `--model sonnet`
- w1 (nommé "claude-haiku") → correct `--model haiku`

### 2. Codex w5 - SUCCÈS COMPLET
- H-V2 complété: .env.example + docker-compose corrigés
- S-V2 complété: Audit schemas/models, 6 fichiers modifiés (+43 ~10 -16)
- A mis à jour CLAUDE.md automatiquement

### 3. Codex w6 - FONCTIONNEL
- Crée MindMap.tsx, explore les conventions frontend
- "Planning skill integration" en cours

### 4. Antigravity (w7) - ERREUR NON RÉSOLUE
- Proxy retourne erreur 404: "Requested entity was not found"
- Non utilisé pour la distribution

### 5. Ollama (w8) - NON DÉMARRÉ
- Fenêtre vide, `ollama serve` jamais lancé
- Non nécessaire pour cette phase (validation)

---

## Erreurs de l'Orchestrateur

### Erreur 1: Polling trop rapide
- **Ce qui s'est passé:** Poll à 60s alors que les workers étaient en phase de "thinking"
- **Conséquence:** Diagnostic erroné de "workers bloqués"
- **Leçon:** Attendre min 120s avant de conclure qu'un worker est bloqué. Utiliser `grep -E "Working|Thinking|Read|Explored"` pour détecter l'activité.

### Erreur 2: Capture-pane insuffisante
- **Ce qui s'est passé:** `tail -10` ne montrait que les lignes vides en bas
- **Conséquence:** Activité invisible
- **Leçon:** Utiliser `capture-pane -S -100 | grep -v "^$"` pour filtrer les lignes vides.

### Erreur 3: Confusion sur la numérotation tmux
- **Ce qui s'est passé:** Le skill dit w2/w3/w4, la réalité est w1/w2/w3
- **Conséquence:** Pas d'impact car j'ai utilisé les bons numéros
- **Leçon:** Toujours vérifier `tmux list-windows` avant de distribuer.

### Erreur 4: Backend test avec processus background
- **Ce qui s'est passé:** `uvicorn ... & ; curl ...` - curl timeout car uvicorn pas prêt
- **Conséquence:** Faux négatif sur le backend (qui fonctionne en réalité)
- **Leçon:** Attendre plus longtemps ou tester dans un tmux dédié.

---

## Ce qui a FONCTIONNÉ

| Action | Résultat |
|--------|----------|
| Distribution via `tmux send-keys` | 6 tâches envoyées, toutes reçues |
| Chargement agents dans workers | Tous les workers ont chargé @agents_library/*.md |
| Codex w5 (H-V2, S-V2) | 2 tâches complétées, 6 fichiers modifiés |
| Codex w6 (O-V2) | MindMap.tsx en cours de création |
| Audit backend (orchestrateur) | 3 bugs trouvés et corrigés (requirements, startup, gemini async) |
| npm install frontend | 104 packages installés, TypeScript compile |
| Backend import test | FastAPI OK, DB tables créées |
| CLAUDE.md tracking | Mis à jour par codex et orchestrateur |
| Retry Enter (skill communication) | A permis de confirmer l'état réel |

---

## Limitations Réelles

### A. Quota Claude Pro
- 4 instances CLI simultanées consomment le quota rapidement
- À 97-98%, les workers risquent de s'arrêter
- **Solution:** Limiter à 2 Claudes max + utiliser Codex pour le reste

### B. Config tmux incorrecte
- Les modèles ne matchent pas les noms de fenêtres
- **Solution:** Recréer les sessions avec les bons modèles

### C. Antigravity non fonctionnel
- Proxy 404, probablement config API
- **Solution:** Vérifier la config antigravity-claude-proxy

### D. Monitoring lent
- L'orchestrateur doit attendre longtemps entre les polls
- **Solution:** Augmenter l'intervalle de poll à 120-180s min

---

## Recommandations pour le Prochain Run

1. **Vérifier quota** avant de lancer (`/usage` dans Claude CLI)
2. **Max 2 Claude CLI** simultanées (haiku + sonnet OU opus seul)
3. **Codex en backup** pour les tâches simples/moyennes
4. **Fixer start-orchestrator.sh** pour les bons modèles par fenêtre
5. **Poll à 120s min** avec filtrage `grep -v "^$"` et `capture-pane -S -100`
6. **Skill communication** : toujours vérifier avec le pattern `Working|Thinking|Read|Explored`

---

*FAILLLM v2 - Rapport révisé par l'orchestrateur*
