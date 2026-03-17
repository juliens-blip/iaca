# Priorités de Régénération — Analyse DB

**Généré le:** 2026-03-17
**Script:** `scripts/identify_regen_targets.py`
**Base:** `data/iaca.db` — 1614 documents

---

## Résumé Exécutif

| Niveau | Critère | Nb docs | % total |
|--------|---------|---------|---------|
| 🔴 Urgents | score ≥ 10 | 346 | 21 % |
| 🟠 Importants | score 5–9 | 298 | 18 % |
| 🟡 Mineurs | score 1–4 | 866 | 54 % |
| ✅ OK | score = 0 | 104 | 6 % |

**Scoring:**
- +10 contenu vide ou < 200 chars
- +5 aucune fiche
- +3 aucune flashcard
- +2 titre de fiche générique (`Fiche - <nom doc>`)
- +1 moins de 10 flashcards

---

## Répartition par Matière (docs urgents + importants)

| Matière | Total docs | 🔴 Urgents | 🟠 Importants |
|---------|-----------|-----------|--------------|
| Licence 2 - Semestre 4 | 279 | 75 | 13 |
| Droit public | 277 | 53 | 85 |
| Licence 2 - Semestre 3 | 257 | 57 | 85 |
| Licence 3 - Semestre 5 | 191 | 30 | 32 |
| Licence 3 - Semestre 6 | 144 | 25 | 20 |
| Questions contemporaines | 68 | 25 | 20 |
| Questions sociales | 83 | 8 | 14 |
| Economie | 53 | 13 | 13 |
| M1 Politique économique | 34 | 16 | 0 |
| M1 Management et égalités | 38 | 16 | 0 |
| Espagnol | 38 | 7 | 7 |
| Documents divers | 11 | 7 | 1 |
| Relations internationales | 46 | 3 | 4 |
| Livres et manuels | 8 | 3 | 2 |
| Finances publiques | 11 | 2 | 2 |
| M1 Droit et légistique | 12 | 4 | 0 |
| Économie et finances publiques | 48 | 1 | 0 |
| Licence 2 - Fiches révision | 4 | 1 | 0 |

**Priorité batch recommandée:** Licence 2 S4 (75 urgents), Droit public (53), Licence 2 S3 (57)

---

## Top 20 Documents à Traiter en Premier

| ID | Titre | Matière | Score | FC | Fi | Raisons |
|----|-------|---------|-------|----|----|---------|
| 16 | Test Upload | Droit public | 18 | 0 | 0 | contenu vide/court, aucune fiche, aucune flashcard |
| 17 | Compo laïcité Elno | Droit public | 18 | 0 | 0 | contenu vide/court, aucune fiche, aucune flashcard |
| 22 | Note DF Elno | Droit public | 18 | 0 | 0 | contenu vide/court, aucune fiche, aucune flashcard |
| 23 | Note Opérationnelle Gabriel Faudou 4A-CA 29.11 | Droit public | 18 | 0 | 0 | contenu vide/court, aucune fiche, aucune flashcard |
| 46 | CE 1903 Terrier | Droit public | 18 | 0 | 0 | contenu vide/court, aucune fiche, aucune flashcard |
| 47 | CE 1968 Semoules | Droit public | 18 | 0 | 0 | contenu vide/court, aucune fiche, aucune flashcard |
| 48 | CE 1989 Nicolo | Droit public | 18 | 0 | 0 | contenu vide/court, aucune fiche, aucune flashcard |
| 49 | TC 1873 Blanco | Droit public | 18 | 0 | 0 | contenu vide/court, aucune fiche, aucune flashcard |
| 202 | QCM-2 économie | Économie et finances publiques | 18 | 0 | 0 | contenu vide/court, aucune fiche, aucune flashcard |
| 224 | B. Manin - Principes gvt représentatif | Questions contemporaines | 18 | 0 | 0 | contenu vide/court, aucune fiche, aucune flashcard |
| 238 | LEMAIRE | Questions contemporaines | 18 | 0 | 0 | contenu vide/court, aucune fiche, aucune flashcard |
| 259 | Etat | Questions contemporaines | 18 | 0 | 0 | contenu vide/court, aucune fiche, aucune flashcard |
| 266 | Nation | Questions contemporaines | 18 | 0 | 0 | contenu vide/court, aucune fiche, aucune flashcard |
| 295 | Mngmt S4 | Questions sociales | 18 | 0 | 0 | contenu vide/court, aucune fiche, aucune flashcard |
| 301 | Mngt S3 | Questions sociales | 18 | 0 | 0 | contenu vide/court, aucune fiche, aucune flashcard |
| 462 | B. Manin - Principes gvt représentatif | Questions contemporaines | 18 | 0 | 0 | contenu vide/court, aucune fiche, aucune flashcard |
| 471 | LEMAIRE | Questions contemporaines | 18 | 0 | 0 | contenu vide/court, aucune fiche, aucune flashcard |
| 480 | Etat | Questions contemporaines | 18 | 0 | 0 | contenu vide/court, aucune fiche, aucune flashcard |
| 485 | Nation | Questions contemporaines | 18 | 0 | 0 | contenu vide/court, aucune fiche, aucune flashcard |
| 486 | République | Questions contemporaines | 18 | 0 | 0 | contenu vide/court, aucune fiche, aucune flashcard |

> Tous les top-20 ont le score maximum (18) : contenu non extrait + aucune fiche + aucune flashcard.
> Plusieurs doublons (même titre, IDs différents) — à vérifier avant batch.

---

## Fichiers Générés

- `regen-priorities.txt` — top 50 affichage console
- `regen-priorities.csv` — export complet (1614 lignes, tous les docs)
- `regen-priorities.md` — ce fichier

## Commandes de Traitement

```bash
# Traiter les urgents par matière (exemple Droit public)
python3 scripts/reextract_and_generate.py --matiere "droit public" --limit 50

# Traiter avec un score minimum
python3 scripts/identify_regen_targets.py --min-score 10 --export urgent.csv

# Batch complet urgents
python3 scripts/reextract_and_generate.py --limit 346
```
