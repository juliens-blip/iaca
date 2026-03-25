# Frontend CLAUDE

## Surface

Frontend Next.js 14 App Router pour le cockpit de révision IACA.

## Structure utile

- [app/layout.tsx](/home/julien/Documents/IACA/frontend/app/layout.tsx): layout global, fonts, shell
- [app/page.tsx](/home/julien/Documents/IACA/frontend/app/page.tsx): dashboard
- [app/sidebar.tsx](/home/julien/Documents/IACA/frontend/app/sidebar.tsx): navigation et stats rapides
- `app/*/page.tsx`: pages métier
- `components/`: composants UI métier
- [lib/api.ts](/home/julien/Documents/IACA/frontend/lib/api.ts): base API + websocket
- [lib/auth.ts](/home/julien/Documents/IACA/frontend/lib/auth.ts): headers/query auth
- [app/globals.css](/home/julien/Documents/IACA/frontend/app/globals.css): tokens et classes utilitaires

## Invariants

- Les fetchs UI doivent cibler `/api/*`, pas une URL backend codée en dur.
- Le rewrite vers le backend est défini dans [next.config.js](/home/julien/Documents/IACA/frontend/next.config.js).
- `NEXT_PUBLIC_API_AUTH_TOKEN` peut injecter un bearer côté frontend; préserver ce comportement.
- Le design existant utilise un thème sombre, des fonts `Public Sans` + `Cormorant Garamond`, et des utilitaires Tailwind maison.

## Commandes courantes

```bash
cd frontend && npm run dev
cd frontend && npx tsc --noEmit
cd frontend && npm run build
```

## Si tu modifies cette zone

- Lire aussi [.claude/rules/typescript.md](/home/julien/Documents/IACA/.claude/rules/typescript.md)
- Garder des états `loading` et `error` explicites sur les vues qui fetchent
- Réutiliser les styles et helpers existants avant de créer de nouveaux patterns
- Si le contrat API change, vérifier à la fois le fetch, les types locaux et les fallbacks d’UI
