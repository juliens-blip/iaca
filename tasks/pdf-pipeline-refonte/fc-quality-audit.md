# Audit qualité flashcards

Date: 2026-03-28
Base auditée: `data/iaca.db`

## Périmètre

- Flashcards totales liées à un document: `24_813`
- Documents avec au moins une flashcard: `953`

## Méthodologie

- **Doublon exact**: même `question` dans un même `document_id`. C'est la même définition que dans `scripts/fix_flashcards_quality.py`.
- **Quasi-doublon normalisé**: même question après normalisation légère (`lower(trim(...))` + écrasement simple des retours à la ligne/espaces), dans un même `document_id`.
- **Longueur moyenne de réponse**: `AVG(LENGTH(reponse))` par document, calculée sur toutes les flashcards du document.

## 1. Documents avec le plus de flashcards dupliquées

Constat principal:

- `0` document avec doublons exacts résiduels
- `0` flashcard en doublon exact résiduelle

Conclusion:

- Le top 10 des doublons exacts est vide: la base ne contient plus de doublons exacts selon la règle de nettoyage actuelle.

Quasi-doublons après normalisation légère de la question:

| Rang | Doc ID | Matière | Titre | Groupes dupliqués | Flashcards dupliquées | Exemple de question |
| --- | ---: | --- | --- | ---: | ---: | --- |
| 1 | 1109 | Licence 3 - Semestre 5 | 11.Titre I avant dernier (1) | 1 | 1 | Quel est le rôle du Haut Conseil du Commissariat aux Comptes (HCCC) ? |

Note:

- Un seul document remonte encore en quasi-doublon après normalisation.
- Il n'y a donc pas 10 documents non triviaux à lister sur cet axe.

## 2. Top 10 des documents avec la plus faible longueur moyenne de réponse

| Rang | Doc ID | Matière | Titre | Nb flashcards | Moy. longueur réponse | Min | Max |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: |
| 1 | 1750 | Licence 3 - Semestre 5 | 2025_2026 matieres option droit_prive-public | 2 | 23.00 | 20 | 26 |
| 2 | 1753 | Licence 3 - Semestre 5 | 2025_2026 matieres option droit_prive | 4 | 25.50 | 25 | 26 |
| 3 | 1747 | Licence 3 - Semestre 5 | 2025_2026 matieres option Droit public | 4 | 40.00 | 23 | 89 |
| 4 | 1755 | Licence 3 - Semestre 5 | Avancer a son rythme - atuces | 3 | 42.67 | 33 | 62 |
| 5 | 1015 | Licence 2 - Semestre 4 | 2407000_FAHLOUN NELIA L2 numérique en droit Mai 2025 Droit civil 2 (les obligations) | 9 | 43.67 | 40 | 50 |
| 6 | 772 | Licence 2 - Semestre 3 | DOC-20250219-WA0013. | 6 | 45.50 | 42 | 49 |
| 7 | 840 | Licence 2 - Semestre 4 | Plan de cours DPG | 60 | 46.27 | 33 | 88 |
| 8 | 794 | Licence 2 - Semestre 3 | 2407000_FAHLOUN NELIA L2 numérique en droit Janvier 2025 Droit civil 1 (les obligations) | 19 | 49.11 | 37 | 65 |
| 9 | 1736 | Relations internationales | Recueil_de_conseils_preuves_crites_INSP_g_n_ral_2025_1761149014 | 44 | 59.66 | 23 | 178 |
| 10 | 1186 | Licence 3 - Semestre 6 | Plan de cours Agorassas-1 | 60 | 60.00 | 35 | 152 |

## Observations rapides

- Les 4 premiers résultats sont des documents avec très peu de flashcards (`2` à `4`), ce qui peut biaiser fortement la moyenne vers le bas.
- Les cas les plus sensibles en volume réel sont plutôt:
  - `840` (`60` flashcards, moyenne `46.27`)
  - `1736` (`44` flashcards, moyenne `59.66`)
  - `1186` (`60` flashcards, moyenne `60.00`)
- Sur l'axe doublons, la base est globalement propre: plus aucun doublon exact détecté.
