# Test Rules

- Le repo n’a pas de suite unit/integration centralisée détectée; la base de vérification est surtout scriptée.
- Toute modification doit au minimum exécuter la vérification la plus proche de la zone touchée.

## Minimum attendu

- Backend Python: `python3 -m compileall backend/app`
- Frontend TypeScript: `cd frontend && npx tsc --noEmit`
- Frontend routing/config/styling large: `cd frontend && npm run build`

## Quand utiliser plus

- Auth, websocket ou rate limiting: `bash scripts/test_security_regression.sh`
- Vérification transversale rapide: `FAST=1 bash scripts/ralph_full_validation.sh`
- Changement batch ou génération de contenu: lancer le script ciblé en mode `--dry-run` si disponible

## Règle de régression

- Pour un bug corrigé, ajouter une vérification reproductible.
- Si une vraie suite de tests n’existe pas encore sur la zone, une vérification scriptée ciblée est acceptable.
- Dans le compte rendu final, toujours citer les commandes réellement exécutées et les limites éventuelles.
