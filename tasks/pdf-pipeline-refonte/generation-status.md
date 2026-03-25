# État de génération — 2026-03-19

Audit de la base `data/iaca.db` : 1614 documents, 2061 fiches, 28871 flashcards.

## Légende des colonnes

| Colonne | Définition |
|---|---|
| **Total docs** | Nombre de documents dans la matière |
| **Sans fiche** | Documents n'ayant aucune fiche associée |
| **< 5 flashcards** | Documents avec moins de 5 flashcards (génération incomplète ou absente) |
| **Contenu court** | Documents dont `contenu_extrait` < 120 caractères (extraction insuffisante / inutilisable) |

---

## Tableau par matière

| Matière | Total docs | Sans fiche | < 5 flashcards | Contenu court |
|---|---|---|---|---|
| Droit public | 277 | **133** | 81 | 51 |
| Licence 2 - Semestre 3 | 257 | **138** | 77 | 54 |
| Licence 2 - Semestre 4 | 279 | **88** | 75 | 75 |
| Licence 3 - Semestre 5 | 191 | **59** | 30 | 30 |
| Licence 3 - Semestre 6 | 144 | **37** | 25 | 25 |
| Questions contemporaines | 68 | **35** | 25 | 25 |
| Questions sociales | 83 | **20** | 8 | 8 |
| M1 Politique économique | 34 | **16** | 16 | 16 |
| M1 Management et égalités | 38 | **16** | 16 | 16 |
| Économie | 53 | **13** | 17 | 13 |
| Espagnol | 38 | **10** | 14 | 7 |
| Documents divers | 11 | **8** | 7 | 7 |
| Livres et manuels | 8 | **5** | 3 | 3 |
| M1 Droit et légistique | 12 | **4** | 4 | 4 |
| Relations internationales | 46 | **4** | 3 | 3 |
| Finances publiques | 11 | **2** | 2 | 2 |
| Économie et finances publiques | 48 | **1** | 1 | 1 |
| Licence 2 - Fiches révision | 4 | **1** | 1 | 1 |
| Scolarité L3 | 9 | 0 | 0 | 0 |
| TEDS (L3) | 3 | 0 | 0 | 0 |
| **TOTAL** | **1614** | **590** | **405** | **341** |

---

## Synthèse

- **590 documents sans fiche** (37 % du corpus) — priorité génération fiches
- **405 documents avec < 5 flashcards** (25 %) — génération flashcards incomplète
- **341 documents à contenu court** (21 %) — extraction PDF défaillante ou docs trop courts ; pipeline marker à relancer en priorité sur ces docs

### Top 3 priorités immédiates

1. **Licence 2 - Semestre 3** : 138 sans fiche, 54 à contenu court → relancer extraction + génération
2. **Droit public** : 133 sans fiche, 51 à contenu court → idem
3. **Licence 2 - Semestre 4** : 88 sans fiche, 75 à contenu court → le plus fort taux de contenu court (27 %)

### Cas particulier

- **M1 Politique économique** et **M1 Management et égalités** : 100 % des docs sans fiche et peu de flashcards → jamais traités
- **Espagnol** : 14 docs avec peu de flashcards pour seulement 10 sans fiche → des fiches existent mais flashcards incomplètes

---

## Requêtes utilisées

```sql
-- Documents sans fiche
SELECT m.nom, COUNT(*) FROM documents d
LEFT JOIN matieres m ON d.matiere_id=m.id
WHERE d.id NOT IN (SELECT DISTINCT document_id FROM fiches WHERE document_id IS NOT NULL)
GROUP BY m.nom ORDER BY COUNT(*) DESC;

-- Documents avec moins de 5 flashcards
SELECT m.nom, COUNT(*) FROM documents d
LEFT JOIN matieres m ON d.matiere_id=m.id
WHERE (SELECT COUNT(*) FROM flashcards f WHERE f.document_id=d.id) < 5
GROUP BY m.nom ORDER BY COUNT(*) DESC;

-- Documents à contenu court (<120 chars)
SELECT m.nom, COUNT(*) FROM documents d
LEFT JOIN matieres m ON d.matiere_id=m.id
WHERE LENGTH(COALESCE(d.contenu_extrait, '')) < 120
GROUP BY m.nom ORDER BY COUNT(*) DESC;
```
