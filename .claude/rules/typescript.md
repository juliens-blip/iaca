# TypeScript Rules

- Rester en TypeScript strict; éviter `any` hors frontière externe clairement justifiée.
- Préférer des types locaux explicites pour les payloads API et l’état UI.
- Garder les composants `use client` au strict nécessaire.
- Dans le frontend, appeler des chemins relatifs `/api/*`; ne pas hardcoder `localhost` dans les composants.
- Réutiliser [frontend/lib/api.ts](/home/julien/Documents/IACA/frontend/lib/api.ts) et [frontend/lib/auth.ts](/home/julien/Documents/IACA/frontend/lib/auth.ts) pour base URL, websocket et auth.
- Gérer explicitement `loading`, `error` et état vide pour toute vue qui fetch.
- Conserver les classes utilitaires existantes définies dans [frontend/app/globals.css](/home/julien/Documents/IACA/frontend/app/globals.css) avant d’ajouter de nouveaux patterns visuels.
- Respecter l’architecture App Router: page dans `app/`, UI réutilisable dans `components/`, helpers sans UI dans `lib/`.
- Préférer des composants lisibles et courts; si un fichier devient dense, extraire du rendu ou des helpers.
