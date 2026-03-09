# Journal d'Implémentation: Fiches + Vocal Fiabilité

## Informations
- Date début: 2026-03-06
- Basé sur: 02_plan.md
- Statut: Termine

## Progression
- [x] Délégation Codex-fast: amélioration génération fiche (`claude_service.py`).
- [x] Délégation AMP: robustesse vocal (`whisper_service.py`, `vocal.py`).
- [x] Intégration orchestrateur: fallback ffmpeg via `imageio-ffmpeg` + sections fiche renforcées.
- [x] Installation dépendances runtime STT dans venv backend.
- [x] Relance backend/frontend et validation de non-régression.

## Modifications principales
- `backend/app/services/claude_service.py`
  - prompt fiche renforcé
  - parsing JSON robuste
  - sanitation de sections (anti-générique, anti-vide, fallback)
  - seuils relevés (`FICHE_MIN_SECTIONS=6`, `FICHE_MAX_SECTIONS=10`)
- `backend/app/services/whisper_service.py`
  - check disponibilité whisper réel
  - fallback ffmpeg (shim `ffmpeg` via `imageio-ffmpeg`)
  - erreurs explicites et récupérables
- `backend/app/routers/vocal.py`
  - erreurs audio/LLM renvoyées en JSON sans crash session
  - `/api/vocal/status` retourne `whisper` réel
- `backend/requirements.txt`
  - ajout `setuptools<81`
  - ajout `imageio-ffmpeg==0.5.1`

## Validation exécutée
- `backend/.venv/bin/python -m compileall backend/app` -> OK
- `cd frontend && npm run build` -> OK
- Endpoints frontend/pages `/ /quiz /flashcards /fiches /mindmap /vocal` -> 200
- API proxy `/api/vocal/status /api/fiches /api/quiz /api/flashcards/revision` -> 200
- WS vocal audio test -> message `type=transcription` reçu (pas d'erreur ffmpeg/whisper)
- Génération fiche réelle -> `sections_generated: 9`, fiche créée en DB

## Dépendances installées (venv backend)
- `torch==2.3.1+cpu`
- `openai-whisper==20231117`
- `imageio-ffmpeg==0.5.1`
- `numpy==2.2.2`
- `numba==0.61.2`
- `llvmlite==0.44.0`
- `tiktoken==0.9.0`
- `more-itertools==10.6.0`
- `regex==2024.11.6`

## Résultat final
- Fiches plus détaillées et plus intuitives à la génération.
- Prof vocal fonctionnel côté transcription audio (whisper actif).
- Session WebSocket vocal reste opérationnelle en cas d’erreur récupérable.

## Exécution autonome continue (2026-03-07)
- Batch en cours: `backend/.venv/bin/python3 scripts/upgrade_manuals_quality.py --provider auto`
- Cibles runtime: `fc>=40`, `qq>=16`, `fi>=4`.
- Progression intermédiaire observée: 25 documents manuels complétés, delta DB courant `+257 flashcards`, `+100 quiz_questions`, `+25 fiches`.
- Log de suivi: `logs/manual_quality_upgrade.log`.
