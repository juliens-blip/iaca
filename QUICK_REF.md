# QUICK REF

## Stack

- Backend: FastAPI, SQLAlchemy 2 async, Pydantic 2, SQLite par défaut, Uvicorn
- Frontend: Next.js 14 App Router, React 18, TypeScript 5, Tailwind 3
- IA / media: Claude, Gemini, Ollama, Whisper, Piper, ffmpeg

## Dossiers utiles

- `backend/app/`: API
- `frontend/app/`: pages
- `frontend/components/`: UI
- `frontend/lib/`: helpers API/auth
- `scripts/`: import, génération, validation
- `docs/`: corpus source
- `data/`: DB + uploads

## Setup local

```bash
cp .env.example .env
python3 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements.txt
cd frontend && npm install
```

## Démarrage local

```bash
source backend/.venv/bin/activate
cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

```bash
cd frontend && npm run dev
```

```bash
docker compose up --build
```

## Vérifications rapides

```bash
python3 -m compileall backend/app
cd frontend && npx tsc --noEmit
cd frontend && npm run build
FAST=1 bash scripts/ralph_full_validation.sh
bash scripts/test_security_regression.sh
curl http://localhost:8000/health
```

## Génération de contenu

```bash
backend/.venv/bin/python3 scripts/extract_and_generate.py --folder "<FOLDER>" --matiere-id <ID>
backend/.venv/bin/python3 scripts/extract_and_generate.py --folder "<FOLDER>" --matiere-id <ID> --dry-run
python3 scripts/p20_3_import_missing_docs.py
```

## Mémoire Claude

```bash
# Dans Claude Code: /memory-hygiene audit|bootstrap|hooks|full
python3 agents_library/agent-memory/skills/memory-audit/scripts/audit_claude_memory.py --root .
python3 agents_library/agent-memory/skills/memory-hooks/scripts/install_memory_hooks.py --root .
python3 agents_library/agent-memory/skills/memory-hooks/scripts/install_memory_hooks.py --root . --write
```

## Variables d’env à connaître

- `DATABASE_URL`
- `API_AUTH_TOKEN`
- `RATE_LIMIT_ENABLED`
- `CORS_ORIGINS`
- `ANTHROPIC_API_KEY`
- `GOOGLE_API_KEY`
- `NEXT_PUBLIC_API_URL`
- `INTERNAL_API_URL`
- `NEXT_PUBLIC_API_AUTH_TOKEN`

## Endpoints racine

- `GET /health`
- `GET /api/matieres`
- `GET /api/documents`
- `GET /api/flashcards`
- `GET /api/quiz`
- `GET /api/fiches`
- `GET /api/vocal/status`
- `POST /api/recommandations/*`
