# Test --provider gemini — Résultat T-060

Date: 2026-03-25 (08:21–08:25 Europe/Paris)

## Résultat

**2/2 fiches générées via Gemini — SUCCÈS**

## Diagnostic initial

**Problème rencontré** : `No module named 'google'`

**Cause** : `google-genai` est installé dans le venv backend (`backend/.venv`), pas dans le Python système. Le script était lancé avec `python3` système.

**Correction** : lancer avec `/home/julien/Documents/IACA/backend/.venv/bin/python3` (ou activer le venv avant).

Commande opératoire :
```bash
set -a && source .env && set +a && \
backend/.venv/bin/python3 scripts/reextract_and_generate.py \
  --matiere "Questions sociales" --limit 2 \
  --skip-extract --skip-flashcards --provider gemini
```

## Performance

| Doc | Titre | Durée | Appels Gemini | Sections | Verdict |
|---|---|---|---|---|---|
| 580 | HCSP-2025 Planification écologique | ~3m56s | 13 | 10 | ✅ OK |
| 581 | Pt2 Exécution contrat L | ~57s | 4 | 10 | ✅ OK |

Total : 17 appels HTTP `gemini-2.0-flash`, ~4m53s pour 2 docs.

## Qualité des fiches

### Fiche 2529 — Planification Écologique Emplois-Compétences
- Titre : "Planification Écologique des Emplois et des Compétences à l'Échelle Territoriale" ✅
- 10 sections, longueurs 1587–2010 chars ✅
- Titres précis et non génériques ✅

### Fiche 2530 — Exécution du contrat de travail
- Titre : "L'exécution du contrat de travail et le pouvoir de direction de l'employeur" ✅
- 10 sections, longueurs 1752–2054 chars ✅
- Sections jurisprudentielles structurées (harcèlement, forfait-jours, SMIC) ✅

**Qualité comparable aux meilleures fiches Claude** (voir quality-check-session.md).

## Note importante

Pour toute utilisation en production :
- Toujours utiliser `backend/.venv/bin/python3` (pas `python3` système)
- Toujours sourcer `.env` avant (contient `GOOGLE_API_KEY`)
- Ajouter un wrapper dans `QUICK_REF.md` avec ces deux prérequis
