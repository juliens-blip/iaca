# Plan d'Implémentation: Fiches + Vocal Fiabilité

## Objectifs
1. Augmenter fortement la qualité des fiches générées.
2. Supprimer l’erreur `No module named whisper` en production locale.
3. Stabiliser le flux WS vocal et le statut de disponibilité.

## Checklist
- [ ] Renforcer le prompt `generer_fiche` avec format et exigences de couverture strictes.
- [ ] Ajouter post-traitement/normalisation défensive des fiches (sections vides, longueur minimale).
- [ ] Rendre `whisper_service` tolérant: check disponibilité + erreur explicite + fallback sans crash WS.
- [ ] Corriger `/api/vocal/status` pour refléter la disponibilité réelle de Whisper.
- [ ] Vérifier dépendances runtime côté venv backend.
- [ ] Valider: compile backend, build frontend, endpoints `200`, WS vocal (texte/audio).

## Délégation
- AMP: diagnostic/fix vocal (whisper + websocket robustesse).
- Codex-fast: amélioration qualité génération fiches (prompt + normalisation).

## Validation
- `python -m compileall backend/app`
- `npm run build` (frontend)
- `curl` endpoints clés
- test WebSocket vocal (connexion + message texte)
