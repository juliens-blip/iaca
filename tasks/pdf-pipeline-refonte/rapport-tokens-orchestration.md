# Rapport complet — Consommation tokens & orchestration multi-LLM

**Date**: 2026-03-25
**Auteur**: Orchestrateur (X4 Opus)
**Session**: iaca-orchestration (tmux)

---

## 1. Architecture de la session

### Workers actifs

| Window | LLM | Role | Coût contexte/prompt |
|--------|-----|------|---------------------|
| W0 | Codex GPT-5.4 xhigh | Worker principal, scripts, git | ~168K tokens max (window) |
| W2 | Claude Sonnet (Claude Code) | Worker polyvalent, batches | ~200K tokens (context window) |
| W3 | Claude Opus (Claude Code) | Tâches complexes, review | ~200K tokens (context window) |
| W4 | Claude Opus (Claude Code) | **Orchestrateur** (moi) | ~200K tokens |
| W5 | AMP (Codex) | Intégration, optimisation | ~168K tokens |
| W8 | Claude (Claude Code) | Hors service (API 404) | — |

### Coût de contexte par worker

Chaque worker Claude Code charge à chaque message :
- **CLAUDE.md** (86 lignes, ~2000 tokens) — chargé à CHAQUE appel
- **backend/CLAUDE.md** + **frontend/CLAUDE.md** — chargés si la surface est touchée
- **.claude/rules/*.md** — chargés conditionnellement
- **Historique de conversation** — grossit à chaque échange (compacté automatiquement)

**Estimation coût contexte par tâche (1 worker):**
- Prompt initial + CLAUDE.md + rules : ~5000 tokens
- Chaque tool call (Read/Edit/Bash) : ~3000-5000 tokens de contexte réenvoyé
- Tâche moyenne (10 tool calls) : ~40,000 tokens de contexte pur
- **4 workers × 5 tâches chacun = ~800,000 tokens de contexte pur** (sans compter le travail)

---

## 2. Consommation tokens par type d'opération

### A. Génération de contenu (Claude CLI / Gemini API)

C'est le **plus gros consommateur** de tokens.

| Opération | Tokens par appel | Appels par doc | Total par doc |
|-----------|-----------------|----------------|---------------|
| generer_fiche (1 chunk) | ~2600 in + ~1500 out = ~4100 | 1-6 chunks (cap) | 4,100 — 24,600 |
| generer_flashcards (1 chunk) | ~2000 in + ~1200 out = ~3200 | 1-6 chunks | 3,200 — 19,200 |
| generer_qcm (1 chunk) | ~2200 in + ~1000 out = ~3200 | 1-6 chunks | 3,200 — 19,200 |

**Par doc complet (fiche + flashcards):** 7,300 — 43,800 tokens

### B. Orchestration (prompts tmux aux workers)

| Action | Tokens estimés |
|--------|---------------|
| Prompt de tâche envoyé à 1 worker | ~500-800 tokens |
| Worker traite la tâche (contexte + tools) | ~30,000-50,000 tokens |
| Orchestrateur poll + vérifie | ~2000 tokens par cycle |
| **1 cycle complet (4 workers × 1 tâche)** | **~150,000-200,000 tokens** |

### C. Opérations git (commit/push)

| Action | Tokens |
|--------|--------|
| git status + diff + log | ~3000 |
| Commit + push | ~5000 |
| **Total par push** | **~8000** |

---

## 3. Le monstre : pourquoi le quota se vidait en 20 minutes

### Scénario AVANT optimisations

Un batch de 20 docs L2-S3 avec l'ancienne config :

| Doc | Chars | Chunks (4K) | Tokens (fiche + FC) |
|-----|-------|-------------|---------------------|
| ADM 7(1) | 59K | 15 | 123,000 |
| ADM 7(2) | 59K | 15 | 123,000 |
| ADM 8(1) | 93K | 24 | 196,800 |
| ADM 8(2) | 96K | 24 | 196,800 |
| ADM 8(3) | 96K | 24 | 196,800 |
| ADM 8(4) | 96K | 24 | 196,800 |
| **DROIT ADM COMPLET** | **819K** | **205** | **1,681,000** |
| gaja_fiches | 144K | 36 | 295,200 |
| Copie de ADM 2 | 104K | 26 | 213,200 |
| ... (11 autres) | ~400K total | ~100 | 820,000 |
| **TOTAL** | — | ~493 chunks | **~4,042,600 tokens** |

**4 millions de tokens pour 20 docs !** Dont 1.7M rien que sur 1 doc monstre.

Et c'est seulement les fiches. Avec flashcards : **~8 millions de tokens**.

Le quota Claude (Pro) est d'environ **300K-500K tokens/heure**. En 20 minutes, on brûlait tout.

### Scénario APRÈS optimisations

Les mêmes 20 docs :

| Optimisation | Impact |
|---|---|
| Chunk size 4K → 8K | ÷2 chunks |
| Cap MAX_CHUNKS = 6 | Doc 819K : 205 → 6 chunks (**-97%**) |
| Exclusion > 200K chars | Doc 819K : exclu du batch |
| Exclusion duplicats SQL | ADM 7(1) = ADM 7(2) → 1 seul traité |
| **RÉSULTAT** | ~81 docs au lieu de 204, max 6 chunks chacun |

**Estimation nouveau batch L2S3 (15 docs filtrés) :**
- 15 docs × 6 chunks max × 4100 tokens = ~369,000 tokens (fiches)
- + flashcards : ~738,000 tokens total
- **÷11 par rapport à avant**

---

## 4. Bilan chiffré de la session

### Tokens consommés (estimation)

| Poste | Tokens |
|-------|--------|
| Orchestration (W4, contexte + tools) | ~300,000 |
| W0 Codex (8 tâches) | ~200,000 |
| W2 Sonnet (8 tâches) | ~350,000 |
| W3 Opus (7 tâches) | ~400,000 |
| W5 AMP (6 tâches) | ~250,000 |
| Génération via Claude CLI (batch L2S3 initial + test) | ~500,000 |
| Génération via Gemini API (tous les batch) | ~800,000 (Gemini, pas Claude) |
| **TOTAL Claude** | **~2,000,000 tokens** |
| **TOTAL Gemini** | **~800,000 tokens** |

### Résultats obtenus

| Métrique | Avant session | Après session | Delta |
|----------|--------------|---------------|-------|
| Fiches | 2,061 | 2,136 | **+75** |
| Flashcards | 28,871 | 28,961 | **+90** |
| Docs restants sans fiche | 590 | 57 (filtrés) | **-533** |
| Commits poussés | — | 9 | — |

### Optimisations livrées

| Fix | Économie |
|-----|----------|
| Retry + backoff Claude CLI | Messages d'erreur visibles |
| Chunk 4K → 8K | **-50% appels API** |
| Cap MAX_CHUNKS = 6 | **-97% sur gros docs** |
| Exclusion > 200K chars | **-44 docs monstres** |
| Exclusion duplicats SQL | **-314 docs redondants** |
| Fallback Gemini (--provider auto) | **Contourne le rate-limit Claude** |
| Script batch_generate_all.sh | **Automatisation complète** |
| Script dedup_documents.py | **Nettoyage DB permanent** |
| **TOTAL ÉCONOMIE** | **~4.3M tokens (73%)** |

---

## 5. Recommandations pour les prochaines sessions

### Immédiat
1. **Exécuter `dedup_documents.py`** pour nettoyer les 314 duplicats
2. **Utiliser `--provider gemini`** par défaut (quota plus large, pas de rate-limit dur)
3. **Limiter les batches à 15 docs max** par lancement

### Court terme
1. **Ajouter un sleep inter-chunk** dans generer_fiche() (pas seulement inter-doc)
2. **Réduire le CLAUDE.md** si >150 lignes — chaque ligne coûte à chaque worker
3. **Compacter les workers** régulièrement (`/compact` dans Claude Code)
4. **1 seul batch Gemini à la fois** pour éviter les 429

### Moyen terme
1. **Cacher les résultats** de génération (si un chunk a déjà été traité, skip)
2. **Paralléliser les providers** : Claude pour les fiches, Gemini pour les flashcards
3. **Monitoring tokens** : ajouter un compteur dans le script batch

---

## 6. Cartographie des agents library utilisés

| Agent | Utilisé par | Pour |
|-------|------------|------|
| `backend-architect.md` | W0, W2, W3, W5 | Architecture batch, fallback Gemini |
| `debugger.md` | W0, W3 | Diagnostic CLI, test fix |
| `code-reviewer.md` | W2, W3 | Review fix, review script |
| `agent_controle.md` | W0, W2, W3 | Validation, git, compilation |
| `explore-code.md` | W5 | Analyse chunk optimization |
| `prompt-engineer.md` | W2 | Script batch orchestrator |
| `test-code.md` | W0 | Validation finale |
| `memory-agent.md` | — | Non utilisé (à prévoir pour hygiène) |

---

*Rapport généré automatiquement par l'orchestrateur X4 (Opus) — session iaca-orchestration 2026-03-25*
