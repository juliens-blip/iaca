# Backend Rules

- Point d’entrée API: [backend/app/main.py](/home/julien/Documents/IACA/backend/app/main.py)
- Organisation:
  - `models/`: SQLAlchemy
  - `schemas/`: Pydantic
  - `routers/`: couche HTTP
  - `services/`: logique métier, IA, parsing, audio
  - `middleware/` et `security.py`: garde-fous transverses

## Conventions

- Garder les routers minces; pousser la logique dans `services/` dès que ça dépasse le mapping HTTP.
- Préférer `AsyncSession` et SQLAlchemy aux accès directs SQLite.
- Préserver l’invariant async-ready du `database_url`; SQLite local aujourd’hui, Postgres possible plus tard.
- Toute nouvelle entrée env doit être ajoutée à [backend/app/config.py](/home/julien/Documents/IACA/backend/app/config.py) et documentée dans [.env.example](/home/julien/Documents/IACA/.env.example).
- Ne pas casser `BearerAuthMiddleware`, `RateLimitMiddleware` ni le CORS piloté par env.
- Les fichiers et uploads doivent continuer à vivre sous `docs/` et `data/uploads/` sauf besoin explicite contraire.

## Check de changement backend

- Modèle touché: vérifier schéma Pydantic, route, sérialisation et compatibilité données
- Route touchée: vérifier auth, erreurs HTTP et payload de sortie
- Service IA touché: gérer explicitement timeouts, erreurs upstream et fallback si déjà prévu
- Script touché: mettre à jour `QUICK_REF.md` si la commande opératoire change
