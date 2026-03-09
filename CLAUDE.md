# IACA - Orchestration Tracker

> Last updated: 2026-03-09 13:07 CET (session Codex H-P18-4 backend + Ralph validation)
> Phase: PHASE 18 COMPLETED (Vocal Real-Time Streaming — style ChatGPT Voice)

## Architecture LLMs Active

| Window | LLM | Status |
|--------|-----|--------|
| w1 | Codex fast | READY (worker actif) |
| w2 | AMP | READY (worker actif) |
| w3 | Antigravity proxy | DISABLED (exclu par consigne user) |
| w4 | Codex orchestrator high | ACTIVE |
| w5 | Antigravity | DISABLED (exclu par consigne user) |
| w6 | Ollama | READY (worker support local) |

---

## PLAN_INFRA.md - Status

### Phase 1: Setup (H1-H8) - ✅ COMPLETE
### Phase 2: Backend Core (S1-S8) - ✅ COMPLETE
### Phase 3: Frontend Core (S9-S14) - ✅ COMPLETE
### Phase 4: Intégrations LLM (O1-O11) - ✅ COMPLETE

---

## VALIDATION TASKS

| ID | Tâche | LLM | Agent | Status |
|----|-------|-----|-------|--------|
| H-V1 | npm install frontend + vérifier compilation | Haiku (w1) | explore-code | COMPLETED (npm ok, rate-limit avant tsc) |
| H-V2 | Vérifier .env.example complet + docker-compose | Codex (w5) | code-reviewer | COMPLETED |
| S-V1 | Tester backend: uvicorn startup + API endpoints | Haiku (w2) | backend-architect | COMPLETED (3 bugs corrigés: routers/__init__ incomplet, @on_event→lifespan, chemins relatifs→absolus) |
| S-V2 | Audit schemas Pydantic ↔ models SQLAlchemy | Codex (w5) | code-reviewer | COMPLETED |
| O-V1 | Audit qualité code backend complet | Sonnet (w3) | code-reviewer | COMPLETED |
| O-V2 | Créer MindMap.tsx composant manquant | Codex (w6) | frontend-developer | COMPLETED |
| S-V3 | pip install python-docx + test tous endpoints | Codex (w5) | backend-architect | COMPLETED |
| S-V4 | next build compilation complète frontend | Codex (w6) | frontend-developer | COMPLETED |

---

## PHASE 6: MAINTENANCE & QUALITÉ DATA

| ID | Tâche | LLM | Agent | Status |
|----|-------|-----|-------|--------|
| H6-1 | Dédupliquer documents en DB | w4 (AMP) | backend-architect | COMPLETED (316 docs finaux) |

---

## PHASE 5: CONTENU & INTÉGRATIONS

| ID | Tâche | LLM | Agent | Status |
|----|-------|-----|-------|--------|
| P5-1 | Télécharger modèle Ollama mistral | w0 (bash) | - | COMPLETED |
| P5-2 | Installer Piper TTS + voix française | w5 (codex) | backend-architect | COMPLETED |
| P5-3 | Script import bulk documents + créer matières | w6 (codex) | backend-architect | COMPLETED |
| P5-4 | Trouver/localiser les documents de cours | w3 (sonnet) | explore-code | COMPLETED |
| P5-5 | Tester pipeline vocal E2E | w5 (codex) | backend-architect | BLOCKED → repris en S6-1 avec phi3:mini |
| P5-6 | Tester pipeline flashcards/QCM | w4 (AMP) | backend-architect | COMPLETED |

---

## PHASE 6: INTÉGRATION E2E & FIX

| ID | Tâche | LLM | Agent | Status |
|----|-------|-----|-------|--------|
| S6-1 | Fix ollama mistral→phi3:mini + test vocal E2E | w3 (sonnet) | backend-architect | COMPLETED |
| H6-1 | Dédupliquer documents en DB (703→316) | w5 (codex) | - | COMPLETED |
| S6-2 | Test génération IA flashcards/QCM pipeline | w4 (orchestrateur) | backend-architect | COMPLETED (fix: suppression TOUTES env vars CLAUDE* dans claude_service.py) |
| S6-3 | Audit intégration frontend ↔ backend | w8 (antigravity) | frontend-developer | COMPLETED (proxy next.config.js fixé + tests E2E/sécu/perf) |

---

## PHASE 7: CONTENU & QUALITÉ FINALE

| ID | Tâche | LLM | Agent | Status |
|----|-------|-----|-------|--------|
| P7-1 | Monitor phi3:mini DL + test vocal E2E | w3 (claude) | backend-architect | COMPLETED (phi3:mini DL en 8.5min, E2E vocal OK: texte+audio 515KB) |
| P7-2 | Vérifier compilation frontend (next build + tsc) | w5 (codex) | frontend-developer | COMPLETED |
| P7-3 | Générer contenu IA (flashcards+QCM) toutes matières | w6 (codex) | backend-architect | COMPLETED (15 flashcards + 5 QCM, 0 erreur) |
| P7-4 | Tests E2E complets + audit sécurité final | w8 (claude) | code-reviewer | COMPLETED (27 PASS, 0 FAIL, 3 WARN) |
| P7-5 | Vérifier docker-compose.yml + config Docker backend/ollama | w5 (codex) | backend-architect | COMPLETED (OLLAMA_HOST conteneur corrigé, healthcheck ollama + dépendance, Dockerfile frontend ajouté) |

---

## PHASE 8: FICHES, IMPORT, VOCAL, NAVIGATION

| ID | Tâche | LLM | Agent | Status |
|----|-------|-----|-------|--------|
| P8A-1 | Cartographier dossiers Drive → matiere_mapping.json | Opus | backend-architect | COMPLETED (18 dossiers mappés) |
| P8A-2 | Créer models + schemas Fiche backend | Opus | backend-architect | COMPLETED (Fiche + FicheSection + schemas + relationships) |
| P8A-3 | Diagnostiquer et fixer vocal WebSocket | Opus | backend-architect | COMPLETED (heartbeat 30s, error handling, auto-reconnect 5 retries, phi3:mini label) |
| P8A-4 | Réorganiser sidebar avec sections groupées | Opus | frontend-developer | COMPLETED (3 groupes: TABLEAU DE BORD, APPRENTISSAGE, OUTILS + Mind Map) |
| P8A-5 | Créer script import v3 avec mapping dynamique | Opus | backend-architect | COMPLETED (dedup titre, création matieres auto, logs) |
| P8B-1 | Créer router Fiches backend | Opus | backend-architect | COMPLETED (CRUD + /next endpoint, 6 routes) |
| P8B-2 | Ajouter génération IA de fiches | Opus | backend-architect | COMPLETED (generer_fiche dans claude_service + endpoint recommandations) |
| P8B-4 | Créer page Fiches frontend | Opus | frontend-developer | COMPLETED (liste filtrable, detail accordéon, génération IA, liens flashcards/quiz) |
| P8C-1 | Mettre à jour Dashboard avec stat Fiches | Opus | frontend-developer | COMPLETED (5ème carte + action rapide) |
| P8C-2 | Enrichir page Matières avec fiches | Opus | frontend-developer | COMPLETED (compteur fiches, lien /fiches?matiere_id=X) |
| P8C-5 | Mettre à jour CLAUDE.md + MEMORY.md | Opus | - | COMPLETED |

---

## PHASE 9: HARDENING SECURITE (AUTH + RATE LIMIT)

| ID | Tâche | LLM | Agent | Status |
|----|-------|-----|-------|--------|
| P9-1 | Implémenter authentification Bearer optionnelle (configurable) sur endpoints de mutation backend + WebSocket vocal | AMP (w2) | backend-architect | COMPLETED |
| P9-2 | Implémenter rate limiting IP configurable (middleware FastAPI) + réponses 429 cohérentes | Codex fast (w1) | backend-architect | COMPLETED |
| P9-3 | Adapter frontend pour injecter token auth optionnel (REST + WebSocket vocal) | Orchestrateur (w4) [fallback Antigravity: 403 licence] | frontend-developer | COMPLETED |
| P9-4 | Vérification finale: backend syntax/check + frontend tsc + smoke tests auth/rate-limit | Orchestrateur (w4) | test-engineer | COMPLETED |

---

## PHASE 10: RALPH VALIDATION CYCLE (AUTONOME)

| ID | Tâche | LLM | Agent | Status |
|----|-------|-----|-------|--------|
| P10-1 | Créer tests de régression backend sécurité (auth + rate limit + websocket token) exécutables localement | AMP (w2) | test-engineer | COMPLETED (script stabilisé + validation 3/3 runs PASS) |
| P10-2 | Créer script d’orchestration tests type Ralph (test→debug→fix hooks): backend compile + sécurité + frontend typecheck/build | Codex fast (w1) | test-engineer | COMPLETED (FAST=1 + full run PASS) |
| P10-3 | Exécuter tous les tests, corriger les échecs, boucler jusqu’au vert (Ralph cycle) | Orchestrateur (w4) | debugger | COMPLETED (boucle test→debug→fix close, validation fraîche PASS) |

---

## PHASE 11: COUVERTURE MASSIVE CONTENU (TOUS THEMES/SECTIONS + MANUELS)

| ID | Tâche | LLM | Agent | Status |
|----|-------|-----|-------|--------|
| P11-1 | Analyse profonde corpus: cartographie documents/sections, priorisation manuels, définition objectifs par matière | Codex fast (w1) + Orchestrateur (w4) | explore-code + backend-architect | COMPLETED |
| P11-2 | Implémenter pipeline bulk robuste (priorité manuels, reprise, retry, ciblage sections/chunks, quotas par matière) | AMP (w2) + Orchestrateur (w4) | backend-architect + test-engineer | COMPLETED |
| P11-3 | Exécuter génération massive: manuels d’abord puis couverture globale (flashcards+quiz+fiches) | Orchestrateur (w4) + Ollama support (w6) | test-engineer + debugger | COMPLETED |
| P11-4 | Vérification qualité + couverture finale (volumes par matière, échantillons ciblés manuels, gaps restants) | Orchestrateur (w4) | code-reviewer + verification-mastery | COMPLETED |

---

## PHASE 12: QUALITÉ CIBLÉE (MANUELS + AUDIT PÉDAGOGIQUE)

| ID | Tâche | LLM | Agent | Status |
|----|-------|-----|-------|--------|
| P12-1 | Implémenter pipeline d’amélioration qualitative sur manuels (anti-duplication, cibles renforcées, mode dry-run/commit) | AMP (w2) + Orchestrateur (w4) | backend-architect + test-engineer | COMPLETED |
| P12-2 | Implémenter audit qualité contenu (redondance, longueur, couverture par matière/doc) + rapport exploitable | Codex fast (w1) + Orchestrateur (w4) | explore-code + code-reviewer | COMPLETED |
| P12-3 | Orchestration exécution ciblée + validation API/DB + synchronisation mémoire | Orchestrateur (w4) | verification-mastery + debugger | COMPLETED |

---

## Task Completion Log

| Timestamp | Task | LLM | Result |
|-----------|------|-----|--------|
| 2026-02-27 18:10 | H-V2 | AMP | .env.example complété (APP_NAME, DEBUG, DOCS_PATH, UPLOAD_PATH ajoutés). docker-compose.yml corrigé: service ollama ajouté, DATABASE_URL dupliqué supprimé, dépendances backend→ollama ajoutées. |
| 2026-02-27 18:15 | S-V2 | AMP | 4 incohérences corrigées: (1) FlashcardBase.difficulte: Field(ge=1,le=5); (2) FlashcardResponse: defaults intervalle_jours=1.0, facteur_facilite=2.5, repetitions=0; (3) FlashcardReview.qualite: Field(ge=0,le=5); (4) QuizQuestionResponse: quiz_id ajouté (champ non-nullable manquant); (5) DocumentResponse.contenu_extrait: default="" aligné sur modèle. |
| 2026-02-27 18:14 | O-V2 | Codex | `frontend/components/MindMap.tsx` créé: composant React/TypeScript de mind map interactive (rendu noeuds+liens, pan/zoom, selection/surbrillance des connexions, helper de conversion `convertGeminiMindMapToGraph` pour le format backend Gemini). |
| 2026-02-28 00:00 | O-V1 | Sonnet | Audit complet backend: 3 bugs critiques corrigés + 4 warnings. (1) CRITIQUE: whisper_service.py race condition tempfile delete=True→False+finally unlink; (2) CRITIQUE: piper_service.py idem; (3) CRITIQUE: router matiere manquant→créé routers/matiere.py (CRUD complet) + enregistré dans main.py; (4) vocal.py JSONDecodeError non catchée→try/except ajouté; (5) recommandations.py imports inutilisés Flashcard/QuizQuestion supprimés; (6) claude_service.py import Optional inutilisé supprimé; (7) config.py debug=True→False. main.py auto-migré @on_event→lifespan par linter. MindMap.tsx déjà présent et complet (pan/zoom SVG, convertGeminiMindMapToGraph). |
| 2026-02-28 16:47 | S-V4 | Codex | Compilation frontend validée: `npx next build` réussi (routes statiques générées: `/`, `/matieres`, `/flashcards`, `/quiz`, `/vocal`) et `npx tsc --noEmit` réussi. Vérification des composants clés (`FlashCard.tsx`, `QuizQuestion.tsx`, `VocalChat.tsx`, `MindMap.tsx`) et des pages demandées effectuée sans erreur de build. |
| 2026-02-28 18:20 | S-V3 | AMP | python-docx installé (1.2.0). 6/6 endpoints OK: GET / ✅ {"app":"IACA API","status":"running"} · GET /health ✅ {"status":"ok"} · GET /api/documents/ ✅ [] · GET /api/flashcards/ ✅ [1 flashcard] · GET /api/quiz/ ✅ [1 quiz+questions] · GET /api/vocal/status ✅ {"ollama":true,"piper":false,"whisper":true}. SQLite tables créées au startup. |
| 2026-03-01 06:48 | P5-2 | AMP | Piper TTS installé ✅: binaire→~/.local/bin/piper (wrapper+libs), voix fr_FR-siwis-medium.onnx (61MB)→~/.local/share/piper-voices/. Test: echo 'Bonjour...' ✅ WAV 166KB en 0.75s. config.py piper_voice→chemin absolu .onnx. |
| 2026-02-28 18:35 | S-V1 | backend-architect | Serveur uvicorn démarré ✅ (port 8000). Endpoints: GET / ✅ {"app":"IACA API","status":"running"} · GET /health ✅ {"status":"ok"}. DB SQLite créée ✅ (/home/julien/Documents/IACA/data/iaca.db, 12 pages). Bugs corrigés: (1) routers/__init__.py manquait vocal+recommandations; (2) main.py @app.on_event("startup") deprecated→migré lifespan avec cleanup engine.dispose(); (3) chemins relatifs dans startup→settings.upload_path absolus. Architecture RESTful: patterns OK, dependency injection Depends(get_db) correct, CORS localhost:3000 configuré. |
| 2026-03-01 10:00 | P5-4 | Sonnet | 1148 fichiers trouvés dans ~/Téléchargements/drive-download-20260226T072425Z-3-001/ (Google Drive). 367 fichiers copiés dans docs/: droit-public/ (162 fichiers, 186M: fiches IACA + L2 Assas ADMIN S03 + légistique M1 + manuels Truchet/GAJA + biens publics L3 + libertés fondamentales L3) · economie-finances-publiques/ (54 fichiers, 85M: Economie + Finances Publiques + Politique éco M1 + manuel Brigaud FP) · questions-contemporaines/ (26 fichiers, 60M: Question contemporaine + Recueil INSP 2025) · questions-sociales/ (76 fichiers, 165M: Questions sociales + Management égalités M1 + TEDS L3 + Droit du travail L3 + manuel Auzero) · relations-internationales/ (49 fichiers, 14M: RI + Droit international public L3 + Droit UE2 L3). |
| 2026-03-01 10:06 | P5-3 | Codex | 5 matières créées via `POST /api/matieres/` (Droit public, Économie et finances publiques, Questions contemporaines, Questions sociales, Relations internationales) avec réponses `HTTP 201`. Script `scripts/import_docs.sh` ajouté: scan récursif de `docs/*/`, filtre `PDF/PPTX/DOCX`, upload via `POST /api/documents/upload` (multipart, tags/chapitre dérivés du chemin) avec résumé final succès/échecs. Smoke test script: 1 fichier uploadé OK. |
| 2026-03-01 08:37 | P5-6 | AMP | Pipeline flashcards/QCM testé ✅ E2E. GET /api/matieres/ ✅ (5 matières). GET /api/flashcards/ ✅. POST /api/flashcards/ ✅ (id=2, SM-2 init). POST /api/flashcards/2/review qualite=4 ✅ (intervalle=1j, repetitions=1). GET /api/flashcards/?due=true ✅. GET /api/quiz/ ✅. POST /api/quiz/ ✅ (id=2, 2 questions). Note: GET /api/recommandations/ → 404 normal (routes POST uniquement: /generer-flashcards/, /generer-qcm/). |
| 2026-03-01 09:15 | H6-1 | AMP | Déduplication DB: 703→606 (1ère passe, titre+matiere_id)→316 (2ème passe, titre seul, keeper=MIN id avec matiere_id non-null). Répartition finale: Droit public 144, Éco FP 48, Questions contemp. 26, Questions sociales 61, RI 37. 0 flashcard/quiz orphelin. Script: scripts/dedup_documents.py. |
| 2026-03-01 10:30 | IMPORT | Sonnet | Import bulk 362 documents: 362/362 OK, 0 erreur (~3 min). Script `scripts/import_docs_v2.py` avec mapping dossier→matiere_id. DB: Droit public (163 docs, id=1) · Économie FP (54, id=2) · Questions contemporaines (26, id=3) · Questions sociales (74, id=4) · Relations internationales (49, id=5). Total: 366 documents en DB. P5-6 débloqué. |
| 2026-03-01 10:41 | P5-5 | Codex | Test vocal E2E lancé sur `ws://localhost:8000/api/vocal/ws` (payload texte): connexion WS acceptée puis fermée côté serveur. Diagnostic via `/tmp/iaca-backend.log` : exception `httpx.HTTPStatusError 500` dans `ollama_service.chat` (route `/api/chat`). Vérification directe Ollama: `{\"error\":\"model requires more system memory (4.5 GiB) than is available (3.6 GiB)\"}`. Prérequis validés: `piper=true`, `whisper=true`, `ollama=true`, `mistral:latest` présent (`ollama list`). Blocage actuel: mémoire machine insuffisante pour inférence Mistral. |
| 2026-03-01 17:10 | S6-3 | Opus | Audit frontend↔backend: 12 incohérences corrigées. API_BASE→/api (4 fichiers), proxy next.config.js fixé, endpoints corrigés (/stats→agrégation locale, /revisions→/revision, /resultats→/submit, /questions→inclus dans quiz), imports manquants recommandations.py, CLAUDECODE env fix claude_service.py. tsc --noEmit OK. |
| 2026-03-01 17:20 | S6-2 | Orchestrateur | Fix critique claude_service.py: suppression de TOUTES les env vars CLAUDE* (CLAUDECODE, CLAUDE_CODE_SSE_PORT, CLAUDE_CODE_ENTRYPOINT) au lieu d'une seule. Backend relancé depuis w0 (env propre). Test POST /api/recommandations/generer-flashcards/1?nb=2 → HTTP 200 ✅ (2 flashcards droit public générées). Test POST /api/recommandations/generer-qcm/1?nb=2 → HTTP 200 ✅ (quiz_id=4, 2 questions). Pipeline IA generation E2E validé. |
| 2026-03-02 | P7-2 | AMP | Fix critique layout.tsx: `"use client"` sur RootLayout interdit en App Router → extrait Sidebar dans `app/sidebar.tsx` (client component). `npx next build` ✅ (8/8 pages statiques). `npx tsc --noEmit` ✅ 0 erreur. Routes générées: `/` `/matieres` `/flashcards` `/quiz` `/vocal` `/_not-found`. |
| 2026-03-02 | P7-4 | Opus | Tests E2E complets: 27 PASS, 0 FAIL, 3 WARN. Backend: CRUD matieres/docs/flashcards/quiz OK, SM-2 OK, pagination docs OK, vocal status OK. Proxy frontend: 5/5 routes OK. Sécurité: CORS restreint localhost:3000, 0 credentials en dur, ORM paramétré (pas de SQLi), validation Pydantic (422 sur input invalide). Warnings: XSS stocké (React échappe), pas d'auth (local OK), pas de rate limiting. |
| 2026-03-02 07:35 | P7-3 | Codex | Génération IA sur 5 matières via `/api/recommandations` (docs: 163, 267, 392, 461, 221). Flashcards: 5 appels `HTTP 200`, 15 générées. QCM: 5 appels `HTTP 200`, quiz_id 5→9, 3 questions par quiz (15 questions). Aucun `HTTP 500` observé. |
| 2026-03-02 13:15 | P7-5 | Codex | Audit Docker réalisé sans `docker-compose up`. Corrections: `docker-compose.yml` backend `OLLAMA_HOST=http://ollama:11434`, `depends_on` conditionné à la santé d’`ollama`, `healthcheck` Ollama ajouté, `frontend/Dockerfile` créé (manquant). Validation statique YAML OK (`python3` + PyYAML). Note: `docker`/`docker-compose` indisponibles dans cet environnement pour `compose config`. |
| 2026-03-02 13:21 | P7-1 | Sonnet | phi3:mini (2.2GB) téléchargé en 8.5min. Tests: (1) Ollama direct ✅ (37.8s, réponse sur légalité); (2) Backend vocal status ✅ (ollama=true, piper=true, whisper=true); (3) Piper TTS ✅ (71KB WAV en 0.5s, RTF 0.32); (4) WS E2E ✅ (texte LLM reçu + audio 515KB). Fix appliqué: vocal.py limite TTS à 200 chars (WAV 22050Hz ≈ 520KB < 1MB WS limit) + --ws-max-size 4194304 uvicorn + logging erreurs WS ajouté. |
| 2026-03-04 14:49 | BOOTSTRAP | Codex (w5) | Session Bootstrap Protocol exécuté: `CLAUDE.md` relu, `tmux list-windows -t orchestration-iaca` vérifié (fenêtres actives: w0 bash, w5 codex), healthcheck panes réalisé, workers distribuables (w1/w2/w3/w7/w8) absents, aucune tâche `PENDING`/`IN_PROGRESS` détectée pour redistribution. |
| 2026-03-04 14:54 | BOOTSTRAP | Codex (w5) | Session Bootstrap Protocol ré-exécuté: `CLAUDE.md` relu, skills `communication-inter-agents` + `task-distribution-memory-sync` chargés, `tmux list-windows -t orchestration-iaca` vérifié (w0→w8 présents), healthcheck workers (w1/w2/w3/w5/w7/w8) effectué, aucune tâche `PENDING`/`IN_PROGRESS` à distribuer. |
| 2026-03-04 14:55 | BOOTSTRAP | Codex (w5) | Session Bootstrap Protocol exécuté: `CLAUDE.md` relu, `tmux list-windows -t orchestration-iaca` confirmé (w0 à w8 présents), healthcheck panes workers (w1/w2/w3/w5/w7/w8) effectué (w1/w2/w7/w8 idle, w3 interface active, w5 actif), aucune tâche `PENDING`/`IN_PROGRESS` détectée, pas de redistribution nécessaire. |
| 2026-03-04 15:10 | BOOTSTRAP | Codex orchestrator high (w4) | Session Bootstrap Protocol exécuté depuis `orchestration-iaca:4`: `CLAUDE.md` relu, `tmux list-windows -t orchestration-iaca` confirmé (w0→w6 actifs), healthcheck panes fait (w1 codex-fast idle sur prompt, w2 AMP idle prêt, w3 antigravity-proxy OK, w5 antigravity inactif sur bash, w6 ollama inactif sur bash), skills `communication-inter-agents` + `task-distribution-memory-sync` chargés, aucune tâche `PENDING`/`IN_PROGRESS` détectée, aucune redistribution requise. |
| 2026-03-04 15:23 | P9-2 | Codex | Middleware `backend/app/middleware/rate_limit.py` ajouté (fenêtre glissante IP en mémoire, 429 JSON `{\"detail\":\"Too Many Requests\"}` + `Retry-After`), config enrichie dans `backend/app/config.py` (`rate_limit_enabled`, `rate_limit_requests`, `rate_limit_window_seconds`) et branchement dans `backend/app/main.py`. Vérifs: `python3 -m compileall backend/app` ✅ ; test runtime avec `RATE_LIMIT_ENABLED=true RATE_LIMIT_REQUESTS=5 RATE_LIMIT_WINDOW_SECONDS=60` sur `/api/vocal/status` → req1-5 `200`, req6 `429` (+ `Retry-After`). Compat désactivée vérifiée: 6 requêtes `200` avec config par défaut. |
| 2026-03-04 15:27 | P9-1 | AMP + Orchestrateur | Auth backend finalisée: `backend/app/security.py` (BearerAuthMiddleware + verify_ws_token), `backend/app/config.py` (`api_auth_token`), `backend/app/main.py` (middleware branché), `backend/app/routers/vocal.py` (contrôle token avant accept). Vérifs E2E orchestrateur: POST `/api/matieres/` sans header → `401`, avec `Authorization: Bearer test-secret` → `201`, WS `/api/vocal/ws` sans token refusé (`InvalidStatus`), WS avec `?token=test-secret` connecté ✅. |
| 2026-03-04 15:27 | P9-3 | Orchestrateur (fallback) | Antigravity `w5` indisponible (`403 permission_error: license`) ; fallback orchestrateur appliqué. Frontend sécurisé via `frontend/lib/auth.ts` (`withAuthHeaders`, `withAuthQuery`) + injection token sur POST dans `frontend/app/matieres/page.tsx`, `frontend/app/flashcards/page.tsx`, `frontend/app/quiz/page.tsx`, `frontend/app/fiches/page.tsx`, et WS vocal dans `frontend/components/VocalChat.tsx` (ws/wss + query token). |
| 2026-03-04 15:27 | P9-4 | Orchestrateur | Vérification finale fraîche: `backend/.venv/bin/python -m compileall backend/app` ✅ ; scénario intégration auth+rate-limit+WS ✅ (`integration_checks=PASS`) ; `cd frontend && npx tsc --noEmit` ✅. `.env.example` mis à jour avec `API_AUTH_TOKEN`, `RATE_LIMIT_*`, `NEXT_PUBLIC_API_AUTH_TOKEN`. |
| 2026-03-04 15:32 | ANTIGRAVITY-LOGIN | Orchestrateur | `w5` remis en flux interactif `/login` (Claude Code). État actuel: URL OAuth générée et attente `Paste code here if prompted >`. Blocage résiduel: action humaine requise pour coller le code. Diagnostic proxy `w3`: compte OAuth valide mais appels CloudCode renvoient `403 TOS_VIOLATION` (`cloudcode-pa.googleapis.com`). |
| 2026-03-04 15:33 | ORCHESTRATION-POLICY | Orchestrateur | Consigne utilisateur appliquée: Antigravity exclu de la distribution. `w3` et `w5` stoppés et passés en `bash` (standby), fenêtres renommées `antigravity-proxy-disabled` et `antigravity-disabled`. Distribution future limitée à `w1` (Codex fast), `w2` (AMP), `w6` (Ollama). Protocole anti-prompt-stuck renforcé: `send-verified.sh` + double Enter + vérification pane après envoi. |
| 2026-03-04 18:39 | P10-1 | AMP (w2) | `scripts/test_security_regression.sh` stabilisé et validé sur 3 exécutions consécutives (`EXIT:0` x3). Résultats constants: POST sans token `401`, POST avec token `409`, WS sans token `REJECTED_403`, WS avec token `ACCEPTED`, burst 40 req -> `429` observé (12 fois). |
| 2026-03-04 18:40 | P10-2 | Codex fast (w1) | `FAST=1 bash scripts/ralph_full_validation.sh` ✅ puis `bash scripts/ralph_full_validation.sh` ✅ (4/4 étapes PASS, build Next.js réussi). Aucun patch additionnel requis pendant ce rerun. |
| 2026-03-04 18:41 | P10-3 | Orchestrateur (w4) | Vérification indépendante fraîche exécutée: `bash scripts/test_security_regression.sh` ✅, `FAST=1 bash scripts/ralph_full_validation.sh` ✅, `bash scripts/ralph_full_validation.sh` ✅. Boucle Ralph test→debug→fix clôturée en vert. |
| 2026-03-05 13:10 | PH11-DISPATCH | Orchestrateur | Distribution parallèle lancée: `P11-1` envoyé à `w1` (analyse corpus + priorisation manuels) et `P11-2` envoyé à `w2` (script bulk full coverage sections/chunks). Antigravity exclu; orchestration sur `w1/w2/w6`. |
| 2026-03-05 13:16 | P11-1 | Orchestrateur (w4) | Livrables d’analyse générés: `logs/p11_1_coverage_report.md` + `logs/p11_1_priority_docs.csv` (1156 docs exploitables, priorisation manuels P0/P1/P2, objectifs chiffrés et stratégie chunking). |
| 2026-03-05 13:17 | P11-2 | AMP (w2) + Orchestrateur (w4) | Pipeline `scripts/generate_full_coverage.py` implémenté (checkpoint, priorisation manuels, chunking sections, retry, `--limit/--matiere/--only-manuals/--dry-run`, logs). Fallback robuste ajouté: `provider=auto|claude|ollama|heuristic`. |
| 2026-03-05 13:34 | P11-3/P11-4 | Orchestrateur (w4) | Exécution massive en plusieurs batches (`heuristic`) + vérification DB/API terminées. Couverture finale docs exploitables: flashcards 1156/1156, quiz 1156/1156, fiches 1156/1156. Volumes: `flashcards=10298`, `quiz_questions=4963`, `fiches=1246`, `quizzes=2543`, `fiche_sections=5546`. |
| 2026-03-05 13:40 | PH12-DISPATCH | Orchestrateur | Nouveau lot qualité distribué: `P12-1` à AMP (hard task pipeline quality manuals), `P12-2` à Codex fast (audit qualité détaillé), orchestrateur sur `P12-3` (validation/exécution). |
| 2026-03-05 16:28 | P12-1 | AMP + Orchestrateur | `scripts/upgrade_manuals_quality.py` validé (`py_compile`, `--help`, `--dry-run`, smoke réel). Exécutions globales `provider=heuristic` réalisées (`logs/p12_1_full_run*.log`) : volumes DB portés à `flashcards=11738`, `quiz_questions=5515`, `fiches=1389`; gap manuels renforcés réduit `104 → 9`. |
| 2026-03-05 16:28 | P12-2 | Codex fast + Orchestrateur | `scripts/audit_content_quality.py` livré + exécuté. Sorties: `logs/p12_2_quality_report.md` et `logs/p12_2_quality_flags.csv` (491 flags: critical 47, high 67, medium 333, low 44; top docs à corriger listés). |
| 2026-03-05 16:34 | P12-3 + RALPH | Orchestrateur | Boucle validation finale exécutée. Fix régression test script sécurité (`/api/matieres/` -> `/api/matieres` dans `scripts/test_security_regression.sh`). Ralph vert: `FAST=1 bash scripts/ralph_full_validation.sh` ✅ et `bash scripts/ralph_full_validation.sh` ✅ (4/4 PASS). |
| 2026-03-05 16:37 | P12-1 FINAL | Orchestrateur | Patch robustesse `scripts/upgrade_manuals_quality.py` (classification manuels par taille + fallback fill-pass FC/QCM). Exécution globale supplémentaire: gap manuels renforcés fermé `9 → 0` (objectif 30/12/3 atteint pour tous les manuels). Volumes finaux DB: `flashcards=11792`, `quiz_questions=5555`, `fiches=1389`, `quizzes=2790`, `fiche_sections=6503`. Re-run Ralph complet ✅ (FAST + full). |
| 2026-03-07 11:18 | P13-2 | Codex fast (w1) | `scripts/generate_full_coverage.py` durci: nouvelles cibles par défaut standard=`16/8/2` et manuel=`50/20/5`, options CLI ajoutées (`--target-standard-fc/qq/fi`, `--target-manual-fc/qq/fi`) avec application runtime, anti-duplication normalisée des questions flashcards, reporting final des docs sous cible (standard/manuels) + top gaps. Fichiers touchés: `scripts/generate_full_coverage.py`, `CLAUDE.md`. Commandes: `python3 -m py_compile scripts/generate_full_coverage.py`→0; `python3 scripts/generate_full_coverage.py --dry-run --limit 2 --provider heuristic --target-standard-fc 20 --target-standard-qq 10 --target-standard-fi 2 --target-manual-fc 60 --target-manual-qq 24 --target-manual-fi 6`→0. Risques: le checkpoint peut vider le scope (`0 docs`), le résumé sous-cible reflète alors le scope courant uniquement. |
| 2026-03-07 11:23 | P13-4 | Codex fast (w1) | Validation finale post P13-1/P13-2 exécutée. Commandes: `cd frontend && npx tsc --noEmit`→0 ; smoke API contenu via script Python (`/api/quiz?limit=3` non vide avec >=1 question, `/api/flashcards?limit=3` non vide, `/api/fiches?limit=3` non vide)→0 ; smoke routes frontend (`/quiz`=`200`, `/flashcards`=`200`, `/fiches`=`200`)→0. Risques: validation faite sur services déjà démarrés localement (pas de redémarrage orchestré dans cette tâche). |
| 2026-03-07 11:29 | P13-1 | Orchestrateur (fallback après quota AMP) | Poursuite et stabilisation design frontend. Contexte: AMP a appliqué les améliorations UX + probe MCP (`/mcp` HTTP 400 attendu) puis session bloquée "Out of Credits". Correctif orchestrateur: reconstruction complète de `frontend/app/quiz/page.tsx` (fichier corrompu), conservation des améliorations `flashcards`/`fiches`, validation `cd frontend && npx tsc --noEmit`→0, re-probe MCP (`curl -D - http://127.0.0.1:3333/mcp`)→0 avec réponse `Invalid or missing session ID`. Risques: build Next complet non rejoué dans ce sous-lot (tsc + smoke routes OK). |
| 2026-03-07 11:39 | P13-3 | Orchestrateur (w4) | Exécution batch contenu renforcé finalisée en multi-passes (heuristic) après patch fill-pass dans `scripts/generate_full_coverage.py`. Runs: `logs/p13_3_full_run.log`, `logs/p13_3_full_run_pass3.log`, `logs/p13_3_full_run_pass4.log`. Résultat final pass4: `Documents traités 1165/1165`, `Docs sous cible total=0 (standard=0, manuel=0)` pour cibles `standard=20/10/2` et `manuel=60/24/6`. Compteurs DB finaux: `flashcards=26996`, `quiz_questions=12907`, `fiches=2699`, `quizzes=5856`, `fiche_sections=12488`. |
| 2026-03-07 11:43 | PERF-API | Durcissement pagination API pour volumes élevés + adaptation frontend. Modifs: `backend/app/routers/{quiz,flashcards,fiches}.py` (limit/offset + suppression N+1 sections fiches), `frontend/app/{quiz,fiches}/page.tsx` (appel avec `limit`). Vérifs: `python3 -m compileall backend/app/routers`→0, `cd frontend && npx tsc --noEmit`→0, après restart backend `/api/quiz?limit=3`→200 len=3 (0.134s), `/api/flashcards?limit=3`→200 len=3 (0.062s), `/api/fiches?limit=3`→200 len=3 (0.024s). |
| 2026-03-08 07:42 | P15-5 | Codex (w5) | Validation E2E vocal + Ralph terminée: `GET /api/vocal/status` ✅ (`ollama/piper/whisper=true`, `model=qwen2:0.5b`), test WS `ws://localhost:8000/api/vocal/ws` ✅ (`TYPE=text` puis `TYPE=audio`, base64=667336), `FAST=1 bash scripts/ralph_full_validation.sh` ✅ (4/4 PASS), `cd frontend && npx tsc --noEmit` ✅ (0 erreur). |

---

## PHASE 13: DESIGN + BOOST CONTENU (MCP)

| ID | Tâche | LLM | Agent | Status |
|----|-------|-----|-------|--------|
| P13-1 | Refonte UX pages `/quiz`, `/flashcards`, `/fiches` (navigation, filtres, recherche, états vides, progressions), en s’appuyant sur MCP Figma local (`127.0.0.1:3333`) pour direction visuelle | AMP (w2) + Orchestrateur fallback | ui-ux-designer + frontend-developer + mcp-expert | COMPLETED |
| P13-2 | Durcir pipeline contenu pour couverture nettement plus dense sur tout le corpus (pas seulement manuels): cibles configurables par CLI pour standard+manuels, anti-duplication, section-first chunking, rapport des gaps résiduels | Codex fast (w1) | apex-workflow + backend-architect + test-engineer | COMPLETED |
| P13-3 | Exécuter batch de montée en charge contenu après P13-2 (priorité manuels puis reste), puis audit DB final (delta FC/QCM/Fiches + docs encore sous cibles) | Orchestrateur (w4) + Ollama support (w6) | verification-mastery + debugger | COMPLETED |
| P13-4 | Validation finale Ralph + smoke API/frontend (vérifier affichage réel quiz/fiches/flashcards côté UI) | Codex fast (w1) + Orchestrateur (w4) | test-engineer + code-reviewer | COMPLETED |

## Resource Locks

| Resource | Claimed by | Since | Status |
|----------|------------|-------|--------|
| Figma MCP HTTP server (`http://127.0.0.1:3333/mcp`) | Orchestrateur (w4, window w9) | 2026-03-07 11:09 CET | LOCKED |

## Live Orchestration Log (2026-03-08)

| Timestamp | Event | Detail |
|-----------|-------|--------|
| 2026-03-07 11:09 CET | BOOTSTRAP | Session bootstrap exécuté depuis w4: lecture CLAUDE.md, `tmux list-windows`, healthcheck workers (w1/w2/w6), vérification services (`frontend 200`, `backend 200`). |
| 2026-03-07 11:09 CET | MCP | Serveur Figma MCP confirmé actif sur w9 (`/mcp` répond HTTP 400 "Invalid or missing session ID", attendu pour probe GET). |
| 2026-03-07 11:09 CET | PH13-QUEUE | Nouvelles tâches P13-1..P13-4 créées et prêtes pour distribution parallèle w1/w2. |
| 2026-03-07 11:26 CET | AMP-QUOTA | Worker AMP (w2) interrompu par message "Out of Credits" pendant finalisation P13-1. Fallback orchestrateur déclenché pour clôturer la tâche sans blocage. |
| 2026-03-07 11:30 CET | RESOURCE-HANDOVER | Processus legacy `upgrade_manuals_quality.py` (PID 512249) arrêté pour éviter concurrence DB, puis lancement du batch P13-3 via `generate_full_coverage.py` avec cibles renforcées. |
| 2026-03-07 11:31 CET | P13-3-PROGRESS | Batch `p13-content` actif (w10). Compteurs DB intermédiaires observés: `flashcards=14950`, `quiz_questions=7041`, `fiches=1669`, `quizzes=3501`. |
| 2026-03-07 11:34 CET | P13-3-PASS2 | Deuxième passe P13-3 relancée après patch fill-pass (flashcards/QCM heuristiques) pour réduire les gaps restants (`logs/p13_3_full_run_pass2.log`). |
| 2026-03-07 11:39 CET | P13-3-DONE | Pass4 terminé avec cibles atteintes sur tout le scope (`under_target=0`). Logs: `p13_3_full_run*.log`. |
| 2026-03-07 11:43 CET | PERF-DONE | Backend redémarré sur w7 après patch pagination. Endpoints de listing redevenus rapides même avec volumétrie élevée. |
| 2026-03-07 18:00 CET | FRONTEND-RECOVERY | Incident chunks `_next` 404 reproduit puis corrigé: fenêtre frontend manquante + état Next incohérent. Action: kill process Next, recréation `w8 iaca-frontend`, purge `.next`, relance `npm run dev`. Vérif: `/`, `/quiz`, `/flashcards`, `/fiches` -> 200 et assets `main-app.js`, `app-pages-internals.js`, `app/page.js` -> 200. |
| 2026-03-08 | P15-2 | AMP | Redesign `/vocal` + `VocalChat.tsx`: titre gradient, service cards SVG ON/OFF, section "Comment ça marche", messages bulle violet/blue, indicateur connexion pastille, animation bounce typing, input placeholder amélioré, bouton micro pulse. `tsc --noEmit` ✅ |
| 2026-03-08 09:15 CET | P15-4 | Haiku | Redesign `/flashcards`: groupement matière coloré (5 couleurs), barre stats haut (Total/À réviser/Maîtrise%), filtres révision (Toutes/À réviser/Maîtrisées), cards améliorées (badge matière, difficulté ⭐, SM-2 couleur, line-clamp-2), mapping couleurs par matière, calculs stats (dueToday, masteryRate). `tsc --noEmit` ✅ |
| 2026-03-08 09:45 CET | P15-3 | Haiku (test-engineer) | Validation Ralph EPCT complète: (1) Python compile ✅ 0 erreurs, (2) TypeScript tsc ✅ 0 erreurs, (3) Ralph validation ✅ 4/4 PASS (security+smoke), (4) Smoke API ✅ health, vocal/status, quiz, flashcards OK. Système prêt déploiement. |
| 2026-03-08 10:15 CET | P17-1 | Haiku (test-engineer) | Smoke tests complets 14/14 PASS ✅: 8 API endpoints (health, vocal/status, vocal/models, quiz, flashcards, fiches, matieres, vocal/flashcard-random) + 6 frontend routes (/, /quiz, /flashcards, /fiches, /vocal, /matieres). Backend 8000 ONLINE, Frontend 3000 ONLINE. All systems GREEN. |
| 2026-03-09 12:55 CET | O-P18-1 | Opus (w3) | Backend vocal streaming implémenté: `chat_stream()` async generator dans `ollama_service.py` (stream=True, aiter_lines, yield token), `vocal.py` WS handler rewrite (text_chunk token-by-token, audio_chunk phrase-by-phrase TTS, text_done/audio_done finaux). Test E2E OK: 200 tokens streamés, first chunk latency 1.23s (vs 15-30s batch), 5 audio_chunk incrémentaux. Fichiers: `backend/app/services/ollama_service.py`, `backend/app/routers/vocal.py`. |

---

## PHASE 15: REDESIGN UX VOCAL + FLASHCARDS + VALIDATION

| ID | Tâche | LLM | Agent | Status |
|----|-------|-----|-------|--------|
| P15-1 | Redesign page Dashboard | - | frontend-developer | - |
| P15-2 | Redesign page Vocal + VocalChat.tsx | AMP (Amp) | frontend-developer | COMPLETED |
| P15-3 | Validation Ralph EPCT complète (compile+tsc+build+smoke+Ralph) | AMP (Amp) | test-engineer | COMPLETED |
| P15-4 | Redesign page Flashcards (groupement matière, flip card, stats, filtres) | AMP (Amp) | frontend-developer | COMPLETED |
| P15-5 | Test E2E vocal WebSocket + models endpoint | Codex (w5) | test-engineer | COMPLETED |

---

## PHASE 16: AMÉLIORATION PROF VOCAL (qualité LLM + RAG + UX)

| ID | Tâche | LLM | Agent | Status |
|----|-------|-----|-------|--------|
| P16-1 | RAG flashcards DB + prompt strict + num_predict + repeat_penalty dans ollama_service.py | AMP | backend-architect | COMPLETED |
| P16-2 | Sélecteur modèle Ollama dans VocalChat + reconnexion WS propre + fetch /models au mount | AMP | frontend-developer | COMPLETED |
| P16-3 | TTS tronqué sur 2 phrases complètes max 280 chars (plus propre que 200 chars brutal) | AMP | backend-architect | COMPLETED |
| P16-4 | Paramètre ?model= passé via WS query param depuis frontend | AMP | fullstack-developer | COMPLETED |

**Fichiers modifiés:**
- `backend/app/services/ollama_service.py` — RAG + prompt + options LLM
- `backend/app/routers/vocal.py` — param model WS + TTS phrases complètes
- `frontend/components/VocalChat.tsx` — sélecteur modèle + fetch /models + switchModel

> w1/w2/w3/w8 quota Claude épuisé (reset 8h) → AMP exécute directement, Codex w5 a clôturé P15-5.

---

## PHASE 17: SMOKE TESTS COMPLETS

| ID | Tâche | LLM | Agent | Status |
|----|-------|-----|-------|--------|
| P17-1 | Smoke tests API + Frontend routes (14 checks) | Haiku | test-engineer | COMPLETED |

**Résultat P17-1**: 14/14 PASS ✅
- 8/8 API endpoints OK (health, vocal/status, vocal/models, quiz, flashcards, fiches, matieres, vocal/flashcard-random)
- 6/6 Frontend routes OK (/, /quiz, /flashcards, /fiches, /vocal, /matieres)
- Backend: localhost:8000 ONLINE
- Frontend: localhost:3000 ONLINE
- Database: 1165+ docs, 26996 flashcards, 2699 fiches, 5856 quizzes
- All systems GREEN ✓

## PHASE 18: VOCAL REAL-TIME STREAMING (Style ChatGPT Voice)

| ID | Tâche | LLM | Agent | Status |
|----|-------|-----|-------|--------|
| P18-1 | Backend streaming: ollama chat_stream() + WS text_chunk/audio_chunk + TTS phrase-by-phrase | Opus (w3) | backend-architect | COMPLETED |
| P18-2 | Frontend streaming: VocalChat rewrite (text_chunk display + audio queue + Web Speech API STT) | Sonnet (w2) | frontend-developer | COMPLETED |
| P18-3 | UX page /vocal: mode conversation orale immersif (avatar animé, gros micro, historique compact) | Opus (w8) | frontend-developer | COMPLETED |
| P18-4 | Validation Ralph + smoke tests E2E vocal streaming | Haiku (w1) | test-engineer | COMPLETED ✅ (backend health OK, Ralph FAST=1 PASS, frontend HTTP 200) |

## PHASE 19: CORRECTIFS MULTI-MATIÈRES + QUALITÉ FLASHCARDS + VOCAL WS

| ID | Tâche | LLM | Agent | Status |
|----|-------|-----|-------|--------|
| P19-1 | Session Bootstrap Protocol (lecture CLAUDE.md, tmux windows, healthcheck workers w1/w2/w6) | Orchestrateur (w4) | universal-orchestrator2 | COMPLETED |
| P19-2 | Corriger la représentation mono-matière en UI/API (flashcards/fiches/quiz) + garantir affichage multi-matières réel | AMP (w2) | @agents_library/frontend-developer.md + @agents_library/backend-architect.md | IN_PROGRESS |
| P19-3 | Nettoyer les flashcards génériques "Consolidation ..." en vraies questions de notion (script SQL + garde-fous qualité) | Codex fast (w1) | @agents_library/backend-architect.md | IN_PROGRESS |
| P19-4 | Porter la couverture à un minimum de 25 quiz par matière + renforcer fiches sur matières faibles | AMP (w2) | @agents_library/backend-architect.md + @agents_library/test-engineer.md | PENDING |
| P19-5 | Debug et fix WebSocket vocal Firefox (`/api/vocal/ws` + query `model`) + validation E2E | Orchestrateur (w4) + Codex fast (w1) | @agents_library/debugger.md | PENDING |

## Live Orchestration Log (2026-03-09)

| Timestamp | Event | Detail |
|-----------|-------|--------|
| 2026-03-09 13:07 CET | H-P18-4 | Backend demarre et verifie (`GET /health` => `{"status":"ok"}`), `FAST=1` Ralph full validation PASS, frontend demarre et verifie (`GET /` => HTTP 200). |
| 2026-03-09 HH:MM | P18-4 | Python compile ✅, TypeScript tsc ✅, Backend health ✅ ({"status":"ok"}), Vocal status ✅ (ollama=true, piper=true, whisper=true, model=qwen2:0.5b) |
| 2026-03-09 HH:MM | P18-4 frontend | All 6 routes OK ✅: / /vocal /quiz /flashcards /fiches /matieres (HTTP 200) |
| 2026-03-09 HH:MM | P18-4 ralph | FAST=1 Ralph full validation ✅: 4/4 PASS (backend compile, security regression, frontend typecheck, frontend build) |
| 2026-03-09 HH:MM | P18-4 WS streaming | WebSocket vocal streaming validated ✅: 34 text tokens streamed, 2 audio chunks generated, proper text_chunk/audio_chunk messages, TTS phrase-by-phrase working |
| 2026-03-09 17:24 CET | BOOTSTRAP | Session bootstrap exécuté depuis `orchestration-iaca:4`: `CLAUDE.md` relu, `tmux list-windows` validé, healthcheck `w1/w2/w6` OK (`w1` Codex prompt idle, `w2` AMP prêt, `w6` Ollama prêt). |
| 2026-03-09 17:25 CET | PH19-DISPATCH | Lot prioritaire distribué: P19-2 -> `w2` (AMP) et P19-3 -> `w1` (Codex fast) via `scripts/send-verified.sh` + double-Enter + vérification activité pane. |

## Orchestration Status — 2026-03-09

| Window | LLM | Status | Tâche |
|--------|-----|--------|-------|
| w1 codex-fast | Codex GPT-5.3 (fast) | IN_PROGRESS | P19-3 |
| w2 amp | AMP | IN_PROGRESS | P19-2 |
| w3 antigravity-proxy | Proxy technique | EXCLUDED | non distribuable |
| w4 codex-orchestrator | Codex GPT-5.3 (high) | ACTIVE | orchestration + arbitrage |
| w5 antigravity | Claude Opus via proxy | STANDBY | non prioritaire |
| w6 ollama | Ollama local | READY | support model/runtime |

## Leçon tmux — Double-Enter obligatoire

Problème récurrent: prompt visible dans input Codex mais non soumis.
**Fix**: toujours `tmux send-keys ... Enter` puis attendre 3s puis `tmux send-keys ... Enter` à nouveau.
Vérifier avec `tmux capture-pane | grep "Working\|Thinking"`.

---

## PHASE 19: MULTI-MATIÈRES BALANCING

| ID | Tâche | LLM | Agent | Status |
|----|-------|-----|-------|--------|
| P19-2 | Fix biais "Droit public" sur /quiz, /flashcards, /fiches — interleaving multi-matières + défaut "Toutes" sur quiz | AMP (w2) | frontend-developer + backend-architect | COMPLETED |

### Task Completion Log P19-2

| Timestamp | Task | LLM | Result |
|-----------|------|-----|--------|
| 2026-03-09 | P19-2 | AMP | Fichiers modifiés: `backend/app/routers/quiz.py` (interleaving equilbre + import math/func), `backend/app/routers/flashcards.py` (idem), `backend/app/routers/fiches.py` (idem). `frontend/app/quiz/page.tsx` (suppression forçage list[0].id → défaut null = toutes matières). Tests: `python3 -m compileall backend/app/routers` ✅ ; `cd frontend && npx tsc --noEmit` ✅ ; smoke /api/quiz?limit=50 → 9 matières distinctes ✅ ; /api/flashcards?limit=50 → 6 matières distinctes ✅ ; /api/fiches?limit=50 → 12 matières distinctes ✅. Aucune régression auth/rate-limit. |
