# Analyse: Fiches + Vocal Fiabilité

## Contexte
- Date: 2026-03-06
- Demande: rendre les fiches beaucoup plus précises et intuitives, corriger erreur vocal `No module named 'whisper'` et déconnexions WS.

## État actuel observé
- Backend route vocal: `backend/app/routers/vocal.py`.
- Service transcription: `backend/app/services/whisper_service.py` importe `whisper` au runtime.
- Dépendance `openai-whisper==20231117` présente dans `backend/requirements.txt`, mais erreur runtime indique module absent dans l’environnement actif.
- Route status vocal renvoie actuellement `"whisper": true` sans vraie vérification.
- Génération fiche: `backend/app/services/claude_service.py::generer_fiche` avec prompt court (4-8 sections, peu de contraintes de granularité/couverture).

## Risques techniques
- Si Whisper non installé, audio casse mais WS reste ouvert avec erreurs répétées.
- Prompt fiche trop permissif => sections génériques, faible couverture des thèmes.
- JSON LLM potentiellement mal formé ou partiel.

## Objectif cible
- Fiches plus actionnables: structure stricte, couverture exhaustive des thèmes/sections, précision (définitions, cas, pièges, points d’examen).
- Vocal robuste: détection réelle de disponibilité Whisper + fallback clair + WS stable.

## Fichiers candidats
- backend/app/services/claude_service.py
- backend/app/routers/recommandations.py
- backend/app/services/whisper_service.py
- backend/app/routers/vocal.py
- backend/requirements.txt (si manque dependency runtime)
