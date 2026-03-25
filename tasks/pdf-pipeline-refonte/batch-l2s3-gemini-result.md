# Batch L2S3 Gemini — Résultat T-066

Date: 2026-03-25 (08:40–09:08 Europe/Paris)

## Résultat

**11/15 fiches générées — SUCCÈS (acceptance: 8/15)**

Durée totale : ~28 minutes pour 15 documents.

## Détail par document

| Doc ID | Titre | Statut | Fiche ID | Sections |
|---|---|---|---|---|
| 632 | ADM 7 | ✅ OK | 2553 | 10 |
| 633 | ADM 8(1) | ✅ OK | 2556 | 10 |
| 634 | ADM 8(2) | ✅ OK | 2557 | 10 |
| 635 | ADM 8(3) | ✅ OK | 2558 | 10 |
| 636 | ADM 8(4) | ✅ OK | 2559 | 10 |
| 637 | ADM 8 | ✅ OK | 2561 | 10 |
| 638 | ADM 9(1) | ❌ JSON invalide | — | — |
| 639 | ADM 9(2) | ❌ JSON invalide | — | — |
| 640 | ADM 9 | ✅ OK | 2564 | 10 |
| 641 | Copie de ADM 2 | ✅ OK | 2567 | 10 |
| 642 | Copy of ADM 12 | ❌ JSON invalide | — | — |
| 643 | Copy of ADM 7 | ✅ OK | 2569 | 10 |
| 645 | DROIT ADMINISTRATIF COMPLET | ❌ JSON invalide | — | — |
| 646 | JP cas pratique admin | ✅ OK | 2570 | 10 |
| 647 | Récapitulatif majeures cas pratiques word | ✅ OK | 2571 | 10 |

## Analyse des erreurs (4/15)

**Erreur** : `Claude n'a pas retourné un JSON object valide`

Ce n'est PAS un rate limit. Gemini a répondu mais avec du contenu non-JSON (texte libre, markdown avec ```, ou JSON malformé). Cause probable : documents sources longs avec mise en forme complexe que Gemini n'arrive pas à structurer proprement dans le format attendu.

Docs concernés : 638, 639, 642, 645 — probablement des documents avec un contenu atypique (tableaux, listes imbriquées, formatage non standard).

## Diagnostic du run précédent (1/15)

Le premier run (08:21–08:35) a échoué à 1/15 car `_generate_sync` n'avait pas encore le retry 429. Après ajout du retry (30s/60s/90s par W0), le second run a absorbé tous les 429 automatiquement — aucun 429 visible dans les logs du second run.

## Performance Gemini Flash

- Débit moyen : ~1 doc / 2 min (documents ~8-15 chunks)
- Rate limit Gemini Flash free tier : ~15 RPM — géré par le retry backoff
- Qualité : 10 sections / fiche sur tous les succès

## Prochaine action

Relancer les 4 docs échoués avec un prompt plus robuste ou réessayer (Gemini peut être non-déterministe) :

```bash
# Cibler uniquement les docs sans fiche parmi 638, 639, 642, 645
set -a && source .env && set +a && \
backend/.venv/bin/python3 scripts/reextract_and_generate.py \
  --matiere "Licence 2 - Semestre 3" --limit 10 \
  --skip-extract --skip-flashcards --provider gemini 2>&1 | \
  tee tasks/pdf-pipeline-refonte/batch-l2s3-gemini-v3.log
```
