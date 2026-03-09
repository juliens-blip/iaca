# Rapport 2 : Analyse des erreurs d'orchestration

> Date : 2026-03-01
> Auteur : Claude Opus (Orchestrateur w4)
> Contexte : Phase 6 - Distribution des taches aux LLMs workers

---

## 1. Probleme principal : Echec de distribution aux workers apres compaction

### Symptome observe par l'utilisateur
"Je ne vois aucun prompt soumis dans les autres LLMs" - Les fenetres w1 (haiku), w2 (sonnet), w5 (codex) etaient vides/idle sans nouvelles taches.

### Cause racine : Perte de continuite apres compaction de contexte

La conversation a atteint la limite de contexte et a ete compactee (resumee). A la reprise :

1. **Erreur de raisonnement** : Au lieu de reprendre immediatement le role d'orchestrateur et redistribuer des taches, j'ai fait un simple "etat des lieux" passif. J'ai confondu "comprendre la situation" avec "agir sur la situation".

2. **Absence de reflexe orchestrateur** : Un orchestrateur doit, a chaque reprise :
   - Verifier l'etat de chaque worker
   - Identifier les taches en attente
   - Distribuer immediatement

   Je n'ai fait que le point 1 (verification) sans enchainer sur les points 2 et 3.

3. **Surestimation du travail deja fait** : En voyant les taches Phase 5 marquees COMPLETED dans CLAUDE.md, j'ai conclu "presque tout est fait" sans identifier proactivement les taches Phase 6 a distribuer.

### Classification : **Erreur de raisonnement** (pas une erreur de code)

---

## 2. Erreur technique : 3 tentatives de `ollama pull phi3:mini` concurrentes

### Symptome
3 processus `ollama pull phi3:mini` tournaient simultanement (PID 231299, 232202, 236910).

### Cause
- Mon pull en background (via Bash tool)
- Le pull lance par w3 (Sonnet) dans sa boucle d'attente
- Un pull supplementaire lance par w3 dans un retry

### Impact
Gaspillage de bande passante, potentiel conflit de fichiers. Aucun des pulls n'a abouti (phi3:mini toujours absent apres 20+ minutes).

### Fix applique
Kills des doublons, relance d'un seul pull.

### Classification : **Erreur de coordination** (orchestrateur + worker agissant en doublon)

---

## 3. Erreur technique : Variables d'environnement Claude incompletes

### Symptome
`POST /api/recommandations/generer-flashcards/` retournait HTTP 500.
Logs : `RuntimeError: Claude CLI error: Error: Claude Code cannot be launched inside another Claude Code session.`

### Cause
`claude_service.py` ne supprimait qu'une seule variable :
```python
env.pop("CLAUDECODE", None)  # Insuffisant !
```

Mais 3 variables existent :
- `CLAUDECODE=1`
- `CLAUDE_CODE_SSE_PORT=21608`
- `CLAUDE_CODE_ENTRYPOINT=cli`

### Fix applique
```python
for key in list(env.keys()):
    if key.startswith("CLAUDE"):
        del env[key]
```

### Qui a introduit le bug initial ?
Le code initial de `claude_service.py` (Phase 4, O1-O11) ne gerait qu'une variable. Le fix partiel de S6-3 (w8 Antigravity) n'a ajoute que `CLAUDECODE`. C'est l'orchestrateur (moi) qui a identifie les 3 variables et applique le fix complet.

### Classification : **Erreur de code** (connaissance incomplete des env vars Claude Code)

---

## 4. Erreur technique : Prompts non soumis dans tmux (Enter avale)

### Symptome
Les prompts envoyes via `tmux send-keys ... Enter` apparaissaient dans le buffer d'input des Claude Code instances mais n'etaient pas soumis.

### Cause
Claude Code traite les multi-line pastes comme "[Pasted text #N +X lines]" et attend une confirmation. Le `Enter` a la fin du send-keys est consomme par la paste, pas par la soumission.

### Fix applique
Pattern "retry Enter" du skill `communication-inter-agents.md` :
```bash
tmux send-keys -t $SESSION:$w Enter  # 2eme Enter pour soumettre
```

### Classification : **Erreur connue** (documentee dans les skills, mais pas systematiquement appliquee)

---

## 5. Erreur : phi3:mini jamais telecharge malgre 3 tentatives

### Symptome
Apres 20+ minutes de pull et 3 processus concurrents, `ollama list` ne montre que `mistral:latest`.

### Causes probables
1. Les 3 pulls concurrents se sont interferes (lock files, partial downloads)
2. Le pull initial etait a 58% (1.3/2.2 GB) a ~1 MB/s quand les doublons ont ete kills
3. Le processus survivant (PID 231299) a probablement ete termine par le timeout de w3 ou par la fin de la session Claude

### Classification : **Erreur de coordination** + **manque de monitoring**

---

## Resume des erreurs

| # | Type | Erreur | Impact | Evitable ? |
|---|------|--------|--------|------------|
| 1 | Raisonnement | Pas de redistribution apres compaction | Workers idle 10+ min | Oui - reflexe orchestrateur a chaque reprise |
| 2 | Coordination | 3 pulls ollama concurrents | Download echoue | Oui - un seul agent doit piloter le download |
| 3 | Code | env.pop("CLAUDECODE") insuffisant | Pipeline IA 500 error | Oui - lister toutes les env vars avant de coder |
| 4 | Technique | Enter avale par paste multi-ligne tmux | Prompts pas soumis | Partiellement - pattern connu mais pas fiable |
| 5 | Monitoring | phi3:mini jamais verifie apres kills | Vocal toujours bloque | Oui - poll periodique du download |

---

## Lecons pour le futur

1. **Apres toute compaction** : distribuer en < 30s, pas d'analyse passive prolongee
2. **Un seul agent par download** : l'orchestrateur coordonne, un seul worker execute
3. **Tester `env | grep CLAUDE`** avant de coder un env cleanup
4. **Toujours double-Enter** apres tmux send-keys multi-ligne vers Claude Code
5. **Poll actif des downloads longs** : verifier toutes les 2 min avec `ollama list`

---

## Resolution finale (2026-03-02)

### phi3:mini finalement telecharge
Apres 8+ tentatives echouees sur 2 jours, phi3:mini a finalement ete telecharge.
- Cause principale des echecs : kills intempestifs des pulls par l'orchestrateur et les workers
- La bonne approche : lancer `nohup ollama pull phi3:mini &` et NE PLUS Y TOUCHER
- Ollama resume les downloads partiels (fichier sha256-*-partial) mais les concurrent pulls interferent

### claude_service.py fix confirme
La suppression de TOUTES les env vars CLAUDE* (pas juste CLAUDECODE) a resolu le pipeline de generation IA.
Flashcards + QCM generes avec succes pour les 5 matieres.

### Lecons integrees dans l'orchestrateur v2026.2
Les 5 lecons ci-dessus ont ete formalisees dans `agent-orchestrator-universal/universal-orchestrator.md` :
1. Post-Compaction Recovery Protocol (lecon 1)
2. Resource Coordination Rules (lecon 2)
3. Environment Variable Audit (lecon 3)
4. Golden Rule #4: double-Enter tmux (lecon 4)
5. Monitoring Long Operations (lecon 5)
