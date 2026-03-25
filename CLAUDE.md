# IACA

Mémoire racine compacte du projet. Ce fichier doit rester stable, factuel et court.

## Règle de mémoire

- Garder ce fichier sous 150-250 lignes.
- Pas de journal de phase, pas de task board, pas de transcript tmux ici.
- Cheatsheet commandes: [QUICK_REF.md](/home/julien/Documents/IACA/QUICK_REF.md)
- Mémoire volatile / learnings récents: [.claude/memory/recent-learnings.md](/home/julien/Documents/IACA/.claude/memory/recent-learnings.md)
- Règles ciblées: [.claude/rules/typescript.md](/home/julien/Documents/IACA/.claude/rules/typescript.md), [.claude/rules/tests.md](/home/julien/Documents/IACA/.claude/rules/tests.md), [.claude/rules/backend.md](/home/julien/Documents/IACA/.claude/rules/backend.md)
- Contexte par surface: [backend/CLAUDE.md](/home/julien/Documents/IACA/backend/CLAUDE.md), [frontend/CLAUDE.md](/home/julien/Documents/IACA/frontend/CLAUDE.md)

## Produit

IACA est une plateforme de préparation aux concours administratifs.

- Backend: FastAPI + SQLAlchemy async + SQLite par défaut
- Frontend: Next.js 14 App Router + React 18 + TypeScript + Tailwind
- Domaine principal: matières, documents, fiches, flashcards, quiz, vocal, recommandations
- Génération de contenu: scripts Python + appels Claude/Gemini/Ollama/Whisper/Piper selon le flux

## Carte rapide du repo

- `backend/`: API, modèles SQLAlchemy, schémas Pydantic, services IA, sécurité, middleware
- `frontend/`: interface Next.js, pages App Router, composants, proxy `/api`, styles Tailwind
- `scripts/`: import, génération de contenu, validation, audits, correctifs batch
- `agents_library/agent-memory/`: agent mémoire réutilisable, skills, hooks et templates pour garder `CLAUDE.md` compact
- `docs/`: corpus de documents source suivi par le projet
- `data/`: base SQLite, uploads et artefacts runtime
- `tasks/`: notes ou chantiers ponctuels
- `.claude/`: règles locales, mémoire courte, settings Claude Code

## Faits techniques stables

- Le package root ne gère qu’un workspace `frontend`.
- Le backend démarre sur `:8000`; le frontend sur `:3000`.
- Le backend crée les tables au démarrage via `Base.metadata.create_all`.
- DB par défaut: `sqlite:///./data/iaca.db` côté env, résolue vers `data/iaca.db` dans le repo.
- Les routers actifs sont montés dans [backend/app/main.py](/home/julien/Documents/IACA/backend/app/main.py):
  - `/api/matieres`
  - `/api/documents`
  - `/api/flashcards`
  - `/api/quiz`
  - `/api/fiches`
  - `/api/vocal`
  - `/api/recommandations`
- L’auth API est facultative mais supportée via bearer token (`API_AUTH_TOKEN`).
- Le rate limiting existe déjà via `RateLimitMiddleware`.
- Le frontend appelle en priorité des URLs relatives `/api/*`; la réécriture vers le backend est gérée dans [frontend/next.config.js](/home/julien/Documents/IACA/frontend/next.config.js).

## Avant de modifier

- Lire le `CLAUDE.md` local de la surface touchée.
- Si le changement touche du TypeScript ou du frontend, lire aussi `.claude/rules/typescript.md`.
- Si le changement touche du backend ou de la DB, lire aussi `.claude/rules/backend.md`.
- Si le changement touche le comportement, prévoir la vérification minimale définie dans `.claude/rules/tests.md`.

## Conventions de travail

- Privilégier des changements ciblés et réversibles.
- Ne pas transformer ce fichier racine en journal opérationnel.
- Documenter les commandes utiles dans `QUICK_REF.md`, pas ici.
- Conserver les invariants sécurité déjà présents: auth bearer, CORS configuré par env, rate limiting optionnel.
- Éviter la dérive de schéma: quand un champ bouge, vérifier modèle, schéma, route, consommateur frontend et doc/env concernés.
- Les gros traitements de contenu passent d’abord par `scripts/` avant toute logique one-off.

## Zones chaudes

- [scripts/extract_and_generate.py](/home/julien/Documents/IACA/scripts/extract_and_generate.py): pipeline principal d’extraction/génération depuis des dossiers source
- [scripts/ralph_full_validation.sh](/home/julien/Documents/IACA/scripts/ralph_full_validation.sh): validation globale
- [scripts/test_security_regression.sh](/home/julien/Documents/IACA/scripts/test_security_regression.sh): auth, websocket et rate limit
- [agents_library/memory-agent.md](/home/julien/Documents/IACA/agents_library/memory-agent.md): agent dédié à l’hygiène mémoire Claude Code
- [backend/app/services/claude_service.py](/home/julien/Documents/IACA/backend/app/services/claude_service.py): génération via Claude
- [backend/app/services/gemini_service.py](/home/julien/Documents/IACA/backend/app/services/gemini_service.py): génération Gemini
- [frontend/lib/api.ts](/home/julien/Documents/IACA/frontend/lib/api.ts) et [frontend/lib/auth.ts](/home/julien/Documents/IACA/frontend/lib/auth.ts): base URL API, websocket et auth côté UI

## Ce qui ne doit pas vivre ici

- Statut de sprint / phase en cours
- File de tâches par agent
- Historique daté de réalisations
- Commandes shell détaillées
- Learnings temporaires ou incidents du jour

Ces éléments vont dans `.claude/memory/recent-learnings.md`, `tasks/`, ou dans des notes d’exécution dédiées.
