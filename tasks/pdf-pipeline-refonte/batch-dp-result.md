# Batch Droit public — fiches — Résultat T-048

Date: 2026-03-25 (~04:19 Europe/Paris)

## Résultat

**0/10 fiches générées — rate limit atteint.**

## Log exact (doc 490, 1er essai)

```
04:15:48 INFO    Phase 2 — génération fiches: 1 documents sans fiche
04:15:48 INFO    [fiche] [490] Les arrêts [Droit public] …
04:17:16 WARNING Claude CLI error (attempt 1/3, rc=1): You've hit your limit · resets 8am (Europe/Paris) — retry in 30s
04:18:00 WARNING Claude CLI error (attempt 2/3, rc=1): You've hit your limit · resets 8am (Europe/Paris) — retry in 60s
04:19:08 ERROR   [fiche] [490] ERREUR: Claude CLI error (rc=1): You've hit your limit · resets 8am (Europe/Paris)
04:19:18 INFO    Phase 2 terminée — ok=0 skipped=0 error=1
```

## Analyse

- Le CLI Claude répond correctement (rc=1 + message explicite), pas un crash.
- Le retry/backoff fonctionne comme prévu (2 tentatives loggées, 3e lève).
- La limite horaire/quotidienne Claude est atteinte à ~04h15.
- **Reset à 8h00 Europe/Paris** (dans ~3h45 au moment de l'erreur).

## Prochaine action

Relancer après 8h00 (heure locale) :

```bash
python3 scripts/reextract_and_generate.py --matiere "Droit public" --limit 10 --skip-extract --skip-flashcards 2>&1 | tee tasks/pdf-pipeline-refonte/batch-dp-fiches-v2.log
```

## Note sur le doc 490

- `contenu_extrait` = 52175 chars → ~13 chunks → 13 appels Claude CLI
- Premier chunk déjà bloqué → limite atteinte dès le 1er appel de la session
