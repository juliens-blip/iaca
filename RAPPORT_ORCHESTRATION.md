# RAPPORT D'ORCHESTRATION IACA

> Date : 2026-02-27
> Orchestrateur : Claude Opus 4.6 (window 4 - amp)
> Session tmux : iaca-orchestration
> Plan executé : PLAN_INFRA.md (33 tâches : H1-H8, S1-S14, O1-O11)

---

## 1. CONTEXTE

### Objectif initial

Exécuter le PLAN_INFRA.md via un système d'orchestration multi-LLM :
- **3 sessions Claude Code** dans des fenêtres tmux séparées
- Distribution par difficulté : H* → Haiku (cheap), S* → Sonnet (moyen), O* → Opus (complexe)
- Orchestrateur Opus qui dispatche, poll et reboucle
- Économie de tokens en utilisant le bon modèle pour chaque tâche

### État de la session tmux au lancement

| Window | Nom | Modèle détecté | État |
|--------|-----|----------------|------|
| 0 | main | - | Terminal shell |
| 1 | claude-haiku | Aucun | Shell vide (nvm error) |
| 2 | claude-sonnet | **Haiku 4.5** | Claude Code prêt, prompt vide |
| 3 | claude-opus | **Sonnet 4.6** | Claude Code prêt, prompt vide |
| 4 | amp | **Opus 4.6** | Orchestrateur (moi) |
| 5 | codex | - | Non utilisé |
| 8 | ollama | - | Non utilisé |

**Note :** Les modèles étaient mal assignés aux fenêtres (Haiku dans "sonnet", Sonnet dans "opus"), mais cela n'a pas eu d'impact car l'orchestration tmux n'a finalement pas fonctionné.

### État du projet au lancement

- Aucun dossier `backend/` ni `frontend/`
- Projet vierge (uniquement docs, plans, configs agent)
- Pas de CLAUDE.md de tracking
- Documents source : 1128 fichiers dans le dossier Téléchargements

---

## 2. TENTATIVE D'ORCHESTRATION TMUX

### 2.1. Envoi de la première tâche

**Action :** Envoi du batch H1-H8 à Haiku (window 2) via :
```bash
tmux send-keys -t iaca-orchestration:2 "Lis PLAN_INFRA.md et execute les taches H1 a H8..." Enter
```

**Résultat :** Le texte est arrivé dans Claude Code mais en mode "paste detection" :
```
❯ [Pasted text #1 +1 lines]
```
Claude Code attendait une confirmation pour le texte collé.

### 2.2. Confirmation du paste

**Action :** Envoi d'un Enter supplémentaire :
```bash
tmux send-keys -t iaca-orchestration:2 Enter
```

**Résultat :** Haiku a commencé à travailler :
- Lu PLAN_INFRA.md ✓
- Analysé les tâches ✓
- Lancé la première commande bash (mkdir) ✓

### 2.3. Blocage sur les permissions

**Problème critique :** Claude Code a affiché un prompt de permission interactif :

```
Bash command
  mkdir -p backend/app/{models,routers,services,schemas} && touch backend/app/__init__.py
  Command contains brace expansion that could alter command parsing
Do you want to proceed?
❯ 1. Yes
  2. No
```

**Action :** Envoi de "1" + Enter pour approuver :
```bash
tmux send-keys -t iaca-orchestration:2 "1" Enter
```

**Résultat :** La commande a été approuvée, mais le problème se répèterait pour chaque outil suivant (Write, Edit, Bash, etc.). Une tâche H* simple nécessite ~5-10 appels d'outils, donc 5-10 approbations manuelles.

### 2.4. Pourquoi c'est non viable

| Problème | Impact |
|----------|--------|
| **Chaque outil demande confirmation** | 33 tâches × ~8 outils = ~264 approbations à envoyer via tmux |
| **Pas de détection fiable du prompt** | `tmux capture-pane` retourne du texte brut avec codes ANSI, difficile à parser pour détecter "Do you want to proceed?" |
| **Timing imprévisible** | Le délai entre l'envoi et le prompt de permission varie (réseau, complexité, modèle) |
| **Pas de feedback structuré** | Impossible de savoir si la commande a réussi ou échoué sans parser l'output visuel |
| **Race conditions** | Si j'envoie "1" avant que le prompt apparaisse, ça tape "1" dans le prompt de saisie de Claude Code |

### 2.5. Décision

J'ai présenté 3 options à l'utilisateur :
1. **Je fais tout moi-même** (recommandé) — pas de blocage
2. **Activer auto-approve** — user va dans chaque fenêtre régler les permissions
3. **Approbation manuelle** — user approuve dans chaque fenêtre pendant que je poll

**Choix de l'utilisateur : Option 1 — tout faire moi-même.**

---

## 3. EXÉCUTION RÉELLE

### Méthode utilisée

- **Tâches simples (H*, S1-S4, O*) :** Exécutées directement par l'orchestrateur Opus
- **Tâches parallélisables (S5-S8, S9-S14) :** Déléguées à des subagents internes (Task tool) — agents dans ma propre session, pas des sessions tmux séparées
- **Tests :** Exécutés directement par l'orchestrateur

### Chronologie

```
18:15  Phase 1 (H1-H8) — Moi-même
       H1: mkdir backend/app/{models,routers,services,schemas}
       H2: mkdir frontend/app/{matieres,flashcards,quiz,vocal}, frontend/components
       H3: Write requirements.txt
       H4: Write package.json
       H5: Write tailwind.config.js
       H6: Write .env.example
       H7: Write Dockerfile
       H8: Write docker-compose.yml
       → COMPLETE en ~2 min

18:17  Phase 2a (S1-S4) — Moi-même
       S1: Write config.py + main.py (FastAPI)
       S2: Write database.py (SQLAlchemy async + SQLite)
       S3: Write 4 models (Matiere, Document, Flashcard, Quiz/QuizQuestion)
       S4: Write 4 schemas Pydantic
       → COMPLETE en ~3 min

18:20  Phase 2b (S5-S8) — Subagent interne #1 (background)
       S5: Router documents (upload, list, get, delete)
       S6: Router flashcards (CRUD + SM-2 algorithm)
       S7: Router quiz (CRUD + submit/score)
       S8: Service document_parser (PDF/PPTX/DOCX)
       → COMPLETE en ~2 min (parallèle)

18:20  Phase 3 (S9-S14) — Subagent interne #2 (background)
       + layout.tsx, globals.css, tsconfig.json, postcss.config, next.config
       S9:  Dashboard (stats, révisions, activité)
       S10: Composant FlashCard (flip 3D, notation SM-2)
       S11: Composant QuizQuestion (radio, correction)
       S12: Page Matières (grid, ajout)
       S13: Page Flashcards (mode liste + révision)
       S14: Page Quiz (liste + quiz + résultats)
       → COMPLETE en ~6 min (parallèle)

18:20  Phase 4 (O1-O11) — Moi-même (en parallèle des subagents)
       O1:  claude_service.py (CLI wrapper, génération flashcards/QCM/analyse)
       O2:  gemini_service.py (API, recommandations, mind maps, chronologies)
       O3:  ollama_service.py (chat, interrogation document)
       O4:  whisper_service.py (STT)
       O5:  piper_service.py (TTS)
       O6:  Router vocal WebSocket
       O7:  Composant VocalChat (WebSocket + MediaRecorder)
       O8:  Page Vocal (status services + chat)
       O9:  Intégration E2E (O6 connecte O3+O4+O5)
       O10: Pipeline flashcards (router recommandations)
       O11: Pipeline recommandations (router recommandations)
       → COMPLETE en ~5 min

18:30  Phase 5 (Tests Ralph)
       - Compilation Python : OK (27 fichiers)
       - Imports backend : OK
       - Fix #1 : google.generativeai deprecated → migré vers google.genai
       - Fix #2 : chemin SQLite relatif → chemin absolu
       - Démarrage serveur : OK (27 routes)
       - Test CRUD flashcard : OK (create + SM-2 review)
       - Test CRUD quiz : OK (create + submit + score 1/1)
       - Test vocal status : OK (ollama=true, whisper=true, piper=false)
       → COMPLETE en ~7 min

18:37  FIN — Toutes les 33 tâches complétées
```

---

## 4. RÉSULTAT PRODUIT

### Backend (27 fichiers Python)

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              ← FastAPI app, 17 endpoints, CORS
│   ├── config.py             ← Settings via pydantic-settings
│   ├── database.py           ← SQLAlchemy async + aiosqlite
│   ├── models/
│   │   ├── matiere.py        ← Matière (nom, couleur, relations)
│   │   ├── document.py       ← Document (fichier, contenu extrait, tags)
│   │   ├── flashcard.py      ← Flashcard (SM-2 fields)
│   │   └── quiz.py           ← Quiz + QuizQuestion (JSON choices)
│   ├── schemas/
│   │   ├── matiere.py        ← Create/Response
│   │   ├── document.py       ← Create/Response
│   │   ├── flashcard.py      ← Create/Response/Review
│   │   └── quiz.py           ← Create/Response/Submission/Result
│   ├── routers/
│   │   ├── documents.py      ← POST upload, GET list, GET/DELETE by id
│   │   ├── flashcards.py     ← CRUD + GET /revision + POST review (SM-2)
│   │   ├── quiz.py           ← CRUD + POST submit (score calculation)
│   │   ├── vocal.py          ← WebSocket chat + GET status
│   │   └── recommandations.py ← Pipelines Claude/Gemini
│   └── services/
│       ├── claude_service.py  ← CLI wrapper (flashcards, QCM, analyse)
│       ├── gemini_service.py  ← API (recommandations, mind maps)
│       ├── ollama_service.py  ← Chat local (Mistral)
│       ├── whisper_service.py ← STT
│       ├── piper_service.py   ← TTS
│       └── document_parser.py ← PDF/PPTX/DOCX extraction
├── requirements.txt
├── Dockerfile
└── .venv/ (créé pendant les tests)
```

### Frontend (15 fichiers)

```
frontend/
├── app/
│   ├── layout.tsx         ← Sidebar navigation, responsive
│   ├── globals.css        ← Tailwind + composants utilitaires
│   ├── page.tsx           ← Dashboard (stats, révisions, activité)
│   ├── matieres/page.tsx  ← Grid matières, modal ajout
│   ├── flashcards/page.tsx ← Liste + mode révision SM-2
│   ├── quiz/page.tsx      ← Liste + quiz + résultats détaillés
│   └── vocal/page.tsx     ← Status services + chat IA
├── components/
│   ├── FlashCard.tsx      ← Flip 3D, notation 1-5
│   ├── QuizQuestion.tsx   ← Radio buttons, correction
│   └── VocalChat.tsx      ← WebSocket, MediaRecorder, audio playback
├── package.json
├── tailwind.config.js
├── tsconfig.json
├── postcss.config.js
└── next.config.js         ← Proxy API vers backend
```

### Config / DevOps

```
IACA/
├── docker-compose.yml     ← Backend + Frontend
├── .env.example           ← Template variables d'environnement
└── data/
    ├── iaca.db            ← SQLite (créé automatiquement au startup)
    └── uploads/           ← Stockage fichiers uploadés
```

### Endpoints API testés

| Méthode | Endpoint | Testé | Résultat |
|---------|----------|-------|----------|
| GET | `/` | ✓ | `{"app":"IACA API","status":"running"}` |
| GET | `/health` | ✓ | `{"status":"ok"}` |
| GET | `/api/flashcards/` | ✓ | `[]` (vide) |
| POST | `/api/flashcards/` | ✓ | Flashcard créée avec champs SM-2 |
| POST | `/api/flashcards/1/review` | ✓ | SM-2 update (repetitions 0→1, prochaine_revision +1j) |
| GET | `/api/quiz/` | ✓ | `[]` (vide) |
| POST | `/api/quiz/` | ✓ | Quiz + questions créés |
| POST | `/api/quiz/1/submit` | ✓ | Score 1/1, détails par question |
| GET | `/api/vocal/status` | ✓ | `{"ollama":true,"piper":false,"whisper":true}` |
| GET | `/openapi.json` | ✓ | 17 endpoints documentés |

### Bugs trouvés et corrigés (méthode Ralph)

| # | Bug | Cause | Fix |
|---|-----|-------|-----|
| 1 | `google.generativeai` deprecated warning | Package obsolète | Migré vers `google.genai` + modèle `gemini-2.0-flash` |
| 2 | `unable to open database file` au startup | Chemin SQLite relatif (`./data/iaca.db`) résolu depuis `backend/` au lieu de la racine | Chemin absolu via `PROJECT_ROOT` dans config.py |

---

## 5. ANALYSE DE L'ÉCHEC D'ORCHESTRATION

### Le problème fondamental

Claude Code en mode interactif impose un **système de permissions par outil**. Chaque appel à Bash, Write, Edit, etc. déclenche un prompt :

```
Do you want to proceed?
❯ 1. Yes
  2. No
```

Ce système est conçu pour l'interaction humaine, pas pour l'automatisation via tmux.

### Pourquoi tmux send-keys ne suffit pas

1. **Pas de parsing structuré** — `tmux capture-pane` retourne du texte visuel (avec codes couleur, boxes Unicode) impossible à parser de manière fiable
2. **Timing non déterministe** — entre l'envoi d'un prompt et l'apparition du prompt de permission, le délai varie (réseau API, complexité du raisonnement)
3. **Race conditions** — si on envoie "1" trop tôt, ça s'insère dans le prompt de saisie ; trop tard, le timeout expire
4. **Pas de signalisation de complétion** — impossible de savoir quand une tâche est finie sans parser le output visuel
5. **Accumulation** — 33 tâches × ~8 outils/tâche = ~264 interactions à orchestrer, chacune pouvant échouer

### Solutions possibles pour une v2

| Solution | Effort | Fiabilité |
|----------|--------|-----------|
| `claude --dangerously-skip-permissions` sur les workers | Faible | Haute (mais risque sécurité) |
| `claude -p "prompt" --print` (mode one-shot) | Moyen | Haute |
| API Anthropic directe (pas Claude Code) | Moyen | Très haute |
| Configuration `allowedTools` dans les settings des workers | Faible | Haute |
| Claude Code SDK (mode programmatique) | Élevé | Très haute |

### Recommandation

Pour une orchestration multi-modèle fiable, la meilleure approche serait :

```bash
# Mode one-shot (pas de permissions interactives)
claude -p "Tâche H1 : créer structure backend..." --print --model haiku
```

Ou encore mieux : utiliser l'**API Anthropic directement** depuis un script Python orchestrateur, ce qui donne un contrôle total sur le routage des modèles et le parsing des réponses.

---

## 6. BILAN ÉCONOMIQUE

### Prévu (orchestration multi-modèle)

| Modèle | Tâches | Coût relatif |
|--------|--------|--------------|
| Haiku | H1-H8 (8 tâches) | 8 × 1x = **8x** |
| Sonnet | S1-S14 (14 tâches) | 14 × 10x = **140x** |
| Opus | O1-O11 (11 tâches) | 11 × 30x = **330x** |
| **Total estimé** | | **~478x** |

### Réel (tout en Opus)

| Modèle | Tâches | Coût relatif |
|--------|--------|--------------|
| Opus | 33 tâches | 33 × 30x = **990x** |
| **Total réel** | | **~990x** |

**Surcoût : ~2x** par rapport à l'orchestration multi-modèle prévue.

---

## 7. CE QUI RESTE À FAIRE

1. [ ] `cd frontend && npm install && npm run dev` — installer dépendances et tester l'UI
2. [ ] Lancer le backend en continu : `cd backend && source .venv/bin/activate && uvicorn app.main:app --reload`
3. [ ] Importer les 1128 documents via `POST /api/documents/upload`
4. [ ] Générer flashcards : `POST /api/recommandations/generer-flashcards/{doc_id}`
5. [ ] Générer QCM : `POST /api/recommandations/generer-qcm/{doc_id}`
6. [ ] Tester le frontend complet (navigation, flashcards, quiz)
7. [ ] Configurer le prof vocal (Ollama + Piper TTS)
8. [ ] Déployer via `docker-compose up`

---

*Rapport généré le 2026-02-27 par l'orchestrateur IACA (Claude Opus 4.6)*
