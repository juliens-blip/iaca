# IACA - Memoire Projet

> Assistant IA personnel de revision pour Master en Droit

---

## Docs Officielles (toujours prioritaires)
- Quickstart: https://code.claude.com/docs/en/quickstart
- Best Practices: https://www.anthropic.com/engineering/claude-code-best-practices
- MCP: https://code.claude.com/docs/en/mcp

Lis-les avant toute tache. Utilise Context7 MCP pour docs libs.

---

## REGLES OBLIGATOIRES

### 1. Problemes
Quand il y a un probleme avec la realisation d'une tache d'un agent = toujours l'inscrire dans `probleme.Md` en expliquant bien le probleme.

### 2. Selection de modeles (economie tokens)

| Tache | Modele | Exemples |
|-------|--------|----------|
| Simple | `/model haiku` | recherche basique, formatage, questions rapides |
| Moyenne | `/model sonnet` | analyse code, implementation routine |
| Complexe | `/model opus` | refactoring majeur, architecture, raisonnement multi-etapes |

**Toujours evaluer la tache avant de commencer et switcher avec /model. Verifier quotas avant Opus.**

### 3. Communication inter-LLM
Utiliser `universal-orchestrator.md` pour coordonner les LLMs.

### 4. Agents obligatoires
Utiliser les agents et skills de `agents_library/` pour TOUTE tache.

### 5. Pas de Claude caché en fond
- Ne jamais lancer de batch autonome détaché qui appelle le CLI `claude` par défaut.
- Tout job long en arrière-plan doit utiliser un provider local explicite, en pratique `--provider ollama`.
- Réserver `claude` aux sessions visibles, interactives, ou à une demande explicite de l'utilisateur.
- Si un batch de génération est lancé en fond, noter le provider choisi dans `CLAUDE.md` et le log associé.

---

## ORCHESTRATION

Le gros du travail se fera via l'agent `universal-orchestrator` qui:
- Gère **3 sessions Claude** (haiku, sonnet, opus) + Amp + Codex
- Distribue les tâches par difficulté (H* → haiku, S* → sonnet, O* → opus)
- Applique la méthode Ralph (test/debug/fix)
- Gère le contexte via CLAUDE.md

**Architecture LLMs:**
```
┌─────────────────────────────────────────┐
│           ORCHESTRATEUR                  │
└─────────────────┬───────────────────────┘
    ┌─────────────┼─────────────┐
    ▼             ▼             ▼
┌───────┐   ┌─────────┐   ┌─────────┐
│HAIKU  │   │ SONNET  │   │  OPUS   │
│ (w2)  │   │  (w3)   │   │  (w4)   │
│  H*   │   │   S*    │   │   O*    │
└───────┘   └─────────┘   └─────────┘
```

**Lancement:**
```bash
bash agents_library/agent-orchestrator-universal/scripts/start-iaca-orchestrator.sh
```

**Fichiers:**
- `universal-orchestrator.md` - Agent principal (modifié pour 3 Claudes)
- `iaca-orchestrator.md` - Version spécifique IACA
- `scripts/start-iaca-orchestrator.sh` - Script de lancement

---

## SPECIFICATIONS PROJET

| Aspect | Choix |
|--------|-------|
| Interface | Application Web |
| Documents | PDF, PowerPoint |
| Domaine | Concours administratif / Droit public |
| Architecture | Hybride (local + cloud) |
| STT | Whisper (local) |
| TTS | Piper TTS (local) |
| LLM Analyse docs | Claude (credits abo) - QUALITE MAX |
| LLM Prof vocal | Ollama local (gratuit) |
| LLM Visuel | Gemini API |

---

## MATIERES ET STRUCTURE

### 1. Droit public (thématique)
- Droits fondamentaux
- Dualité des ordres de juridictions
- Fonction publique
- Hiérarchie des normes
- Jurisprudence / Fiches d'arrêts
- Les acteurs
- Police administrative
- Pouvoir de décision
- Service public

### 2. Finances publiques
- Fiches thématiques (HCFP, responsabilité gestionnaires, CT...)

### 3. Questions sociales (3 thèmes)
- Thème 1 : Évolution des formes du travail
- Thème 2 : Transition écologique et conditions de travail
- Thème 3 : Négociation collective

### 4. Questions contemporaines (chapitres)
- Chapitres numérotés (Médias, Transparence, Nations, Populisme...)
- Fiches sur les notions

### 5. Relations internationales (séances)
- Séance 3 : Multilatéralisme en crise
- Séance 4-5 : Transformations diplomatie

---

## FONCTIONNALITES PREVUES

### Claude (credits abo - qualite max)
1. **Ingestion documents** - Upload et extraction PDF/PPTX
2. **Organisation** - Matieres, chapitres, tags
3. **Flashcards** - Generation automatique avec repetition espacee
4. **QCM** - Questions a choix multiples, cas pratiques juridiques

### Gemini API (recherche + visuels)
5. **Recommandations externes** - Recherche et suggestion de :
   - Podcasts (audio)
   - Videos YouTube
   - Articles web
   - Ressources complementaires aux cours
6. **Mind maps** - Schemas de synthese, chronologies

### Ollama (local gratuit)
7. **Prof vocal** - Professeur interactif (STT Whisper + TTS Piper + Ollama)

---

## CLES API (A CONFIGURER)

```env
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
```

---

## SOURCE DOCUMENTS

**Chemin:** `/home/julien/Téléchargements/drive-download-20260226T072425Z-3-001`
**Total:** 1128 documents (PDF, PPTX, DOCX)

### Structure
- Prépa INSP (Questions sociales, contemporaines, RI, Finances, Droit public)
- Licence 2-3 Assas (Droit admin, pénal, constit, finances...)
- M1 (Politique éco, Légistique, Management)
- Manuels et livres

---

## PROCHAINES ETAPES

1. [x] Configurer les cles API (Gemini OK, Claude via abo)
2. [x] Definir les matieres
3. [x] Recuperer les documents (1128 fichiers)
4. [x] Creer le plan d'infra (PLAN_INFRA.md)
5. [x] **Lancer orchestrateur** → Executer PLAN_INFRA.md (COMPLETE)
6. [ ] Traiter les documents par matiere
7. [ ] Generer flashcards et QCM
8. [ ] Installer frontend (npm install) et tester UI
9. [ ] Deployer (docker-compose up)

---

## FICHIERS MEMOIRE

| Fichier | Role |
|---------|------|
| `claude.md` | Memoire principale (ce fichier) |
| `AGENT.md` | Catalogue des agents |
| `PLAN_INFRA.md` | Plan d'implementation (taches par difficulte) |
| `probleme.Md` | Log des problemes |
| `readme.md` | Doc technique |

---

*Derniere MAJ: 2026-02-26*
