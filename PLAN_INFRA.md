# PLAN INFRASTRUCTURE - IACA

> Plan à exécuter via `universal-orchestrator` qui distribuera aux LLMs selon difficulté

---

## ARCHITECTURE CIBLE

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND (Next.js)                      │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌────────┐ │
│  │Dashboard│ │Flashcard│ │  Quiz   │ │  Vocal  │ │Matières│ │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └────────┘ │
└─────────────────────────┬───────────────────────────────────┘
                          │ REST API
┌─────────────────────────▼───────────────────────────────────┐
│                      BACKEND (FastAPI)                       │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌────────┐ │
│  │Documents│ │Flashcard│ │  Quiz   │ │  Vocal  │ │Reco    │ │
│  │ Service │ │ Service │ │ Service │ │ Service │ │Service │ │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └───┬────┘ │
│       │          │          │          │          │        │
│  ┌────▼──────────▼──────────▼──────────▼──────────▼────┐   │
│  │                    DATABASE (SQLite)                 │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│    Claude     │ │    Gemini     │ │    Ollama     │
│ (via CLI abo) │ │    (API)      │ │   (local)     │
│               │ │               │ │               │
│ - Analyse doc │ │ - Reco web    │ │ - Prof vocal  │
│ - Flashcards  │ │ - Mind maps   │ │ - Chat        │
│ - QCM         │ │ - YouTube     │ │               │
└───────────────┘ └───────────────┘ └───────────────┘
                                           │
                                    ┌──────┴──────┐
                                    ▼             ▼
                              ┌─────────┐   ┌─────────┐
                              │ Whisper │   │  Piper  │
                              │  (STT)  │   │  (TTS)  │
                              └─────────┘   └─────────┘
```

---

## STRUCTURE DOSSIERS

```
IACA/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app
│   │   ├── config.py            # Settings
│   │   ├── database.py          # SQLite connection
│   │   ├── models/              # SQLAlchemy models
│   │   │   ├── document.py
│   │   │   ├── flashcard.py
│   │   │   ├── quiz.py
│   │   │   └── matiere.py
│   │   ├── routers/             # API endpoints
│   │   │   ├── documents.py
│   │   │   ├── flashcards.py
│   │   │   ├── quiz.py
│   │   │   ├── vocal.py
│   │   │   └── recommandations.py
│   │   ├── services/            # Business logic
│   │   │   ├── document_parser.py   # PDF/PPTX extraction
│   │   │   ├── claude_service.py    # Claude via CLI
│   │   │   ├── gemini_service.py    # Gemini API
│   │   │   ├── ollama_service.py    # Ollama local
│   │   │   ├── whisper_service.py   # STT
│   │   │   └── piper_service.py     # TTS
│   │   └── schemas/             # Pydantic schemas
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── app/                     # Next.js App Router
│   │   ├── page.tsx             # Dashboard
│   │   ├── matieres/
│   │   ├── flashcards/
│   │   ├── quiz/
│   │   └── vocal/
│   ├── components/
│   │   ├── FlashCard.tsx
│   │   ├── QuizQuestion.tsx
│   │   ├── VocalChat.tsx
│   │   └── MindMap.tsx
│   ├── package.json
│   └── tailwind.config.js
│
├── docs/                        # Documents source
│   └── (lien vers Drive)
│
├── data/
│   └── iaca.db                  # SQLite database
│
└── docker-compose.yml
```

---

## TACHES PAR DIFFICULTE

### HAIKU (Simple) - Recherche, setup, configs

| ID | Tâche | Fichiers |
|----|-------|----------|
| H1 | Créer structure dossiers backend/ | mkdir |
| H2 | Créer structure dossiers frontend/ | mkdir |
| H3 | Créer requirements.txt | backend/requirements.txt |
| H4 | Créer package.json Next.js | frontend/package.json |
| H5 | Créer tailwind.config.js | frontend/tailwind.config.js |
| H6 | Créer .env.example | .env.example |
| H7 | Créer Dockerfile backend | backend/Dockerfile |
| H8 | Créer docker-compose.yml | docker-compose.yml |

### SONNET (Moyen) - Implémentation standard

| ID | Tâche | Fichiers |
|----|-------|----------|
| S1 | Implémenter FastAPI main.py + config | app/main.py, config.py |
| S2 | Implémenter database.py SQLite | app/database.py |
| S3 | Créer models SQLAlchemy | app/models/*.py |
| S4 | Créer schemas Pydantic | app/schemas/*.py |
| S5 | Implémenter router documents | app/routers/documents.py |
| S6 | Implémenter router flashcards | app/routers/flashcards.py |
| S7 | Implémenter router quiz | app/routers/quiz.py |
| S8 | Implémenter document_parser (PDF/PPTX) | app/services/document_parser.py |
| S9 | Créer page Dashboard Next.js | frontend/app/page.tsx |
| S10 | Créer composant FlashCard | frontend/components/FlashCard.tsx |
| S11 | Créer composant QuizQuestion | frontend/components/QuizQuestion.tsx |
| S12 | Créer page Matières | frontend/app/matieres/page.tsx |
| S13 | Créer page Flashcards | frontend/app/flashcards/page.tsx |
| S14 | Créer page Quiz | frontend/app/quiz/page.tsx |

### OPUS (Complexe) - Architecture, intégrations LLM

| ID | Tâche | Fichiers |
|----|-------|----------|
| O1 | Implémenter claude_service (CLI wrapper) | app/services/claude_service.py |
| O2 | Implémenter gemini_service (API + reco) | app/services/gemini_service.py |
| O3 | Implémenter ollama_service | app/services/ollama_service.py |
| O4 | Implémenter whisper_service (STT) | app/services/whisper_service.py |
| O5 | Implémenter piper_service (TTS) | app/services/piper_service.py |
| O6 | Implémenter router vocal (WebSocket) | app/routers/vocal.py |
| O7 | Créer composant VocalChat | frontend/components/VocalChat.tsx |
| O8 | Créer page Vocal | frontend/app/vocal/page.tsx |
| O9 | Intégration complète Prof Vocal | E2E vocal flow |
| O10 | Pipeline génération flashcards | Analyse → Claude → DB |
| O11 | Pipeline recommandations externes | Gemini → Web → DB |

---

## ORDRE D'EXECUTION

```
Phase 1: Setup (HAIKU)
├── H1-H8 en parallèle
│
Phase 2: Backend Core (SONNET)
├── S1 → S2 → S3 → S4 (séquentiel - dépendances)
├── S5, S6, S7 en parallèle (routers)
├── S8 (parser docs)
│
Phase 3: Frontend Core (SONNET)
├── S9 → S12, S13, S14 (pages)
├── S10, S11 en parallèle (composants)
│
Phase 4: Intégrations LLM (OPUS)
├── O1, O2, O3 en parallèle (services LLM)
├── O4 → O5 → O6 → O7 → O8 → O9 (vocal - séquentiel)
├── O10, O11 (pipelines)
```

---

## DEPENDANCES

### Backend (requirements.txt)
```
fastapi==0.109.0
uvicorn==0.27.0
sqlalchemy==2.0.25
pydantic==2.5.3
python-multipart==0.0.6
pymupdf==1.23.8
python-pptx==0.6.23
google-generativeai==0.3.2
openai-whisper==20231117
httpx==0.26.0
```

### Frontend (package.json)
```json
{
  "dependencies": {
    "next": "14.1.0",
    "react": "18.2.0",
    "tailwindcss": "3.4.1",
    "@radix-ui/react-*": "latest"
  }
}
```

---

## COMMANDE ORCHESTRATEUR

```bash
# Charger l'orchestrateur
@agents_library/agent-orchestrator-universal/universal-orchestrator.md

# Lancer avec le plan
/start "Exécuter PLAN_INFRA.md - Phase 1 (Setup HAIKU)"
```

---

*Plan prêt pour orchestration*
