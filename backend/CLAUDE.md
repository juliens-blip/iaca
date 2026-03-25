# Backend CLAUDE

## Surface

API FastAPI de révision IACA. Le backend gère matières, documents, fiches, flashcards, quiz, vocal et recommandations.

## Structure utile

- [app/main.py](/home/julien/Documents/IACA/backend/app/main.py): app FastAPI, middleware, routers
- [app/config.py](/home/julien/Documents/IACA/backend/app/config.py): settings
- [app/database.py](/home/julien/Documents/IACA/backend/app/database.py): engine async, session, base
- `app/models/`: SQLAlchemy
- `app/schemas/`: Pydantic
- `app/routers/`: endpoints
- `app/services/`: intégrations IA, parsing documents, STT/TTS

## Invariants

- Tables créées au startup; pas de système de migration détecté.
- DB locale par défaut: SQLite sous `data/iaca.db`.
- Auth via bearer optionnel; ne pas ouvrir par inadvertance des routes d’écriture.
- Rate limit configurable par env; ne pas contourner le middleware pour des routes publiques.
- Les uploads et corpus sont des données métier; éviter toute logique destructive.

## Endpoints majeurs

- `/api/matieres`
- `/api/documents`
- `/api/flashcards`
- `/api/quiz`
- `/api/fiches`
- `/api/vocal`
- `/api/recommandations`

## Commandes courantes

```bash
source backend/.venv/bin/activate
cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
python3 -m compileall backend/app
bash scripts/test_security_regression.sh
```

## Si tu modifies cette zone

- Lire aussi [.claude/rules/backend.md](/home/julien/Documents/IACA/.claude/rules/backend.md)
- Vérifier les schémas d’entrée/sortie, pas seulement les modèles
- Contrôler l’impact sur `frontend/lib/auth.ts` et les fetchs UI si le contrat HTTP change
- Pour les scripts de génération, privilégier un `--dry-run` ou un sous-ensemble réduit avant batch complet
