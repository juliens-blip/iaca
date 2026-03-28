# Audit matieres a flashcards faibles

Date: 2026-03-28
Base analysee: `data/iaca.db`

## Methode

- Metrique 1: `avg_difficulty` = moyenne du champ `flashcards.difficulte` (echelle `1-5`, plus bas = plus faible dans cet audit).
- Metrique 2: `avg_response_len` = moyenne de `LENGTH(reponse)` par matiere.
- Pour eviter les faux signaux, la conclusion principale ne retient que les matieres avec au moins `100` flashcards.
- Matieres exclues du classement principal pour faible volume: `TEDS (L3)` (`72`), `Licence 2 - Fiches revision` (`60`), `(sans matiere)` (`1`).

## Resume

Les matieres qui ressortent comme les plus faibles sur le croisement `faible difficulte` + `reponses courtes` sont:

1. `M1 Politique economique`
2. `Scolarite L3`
3. `Économie et finances publiques`
4. `Licence 2 - Semestre 4`

Lecture:

- `M1 Politique economique` est la plus courte en longueur moyenne de reponse (`112.91`) et reste tres basse en difficulte moyenne (`2.43`).
- `Scolarite L3` est la plus faible en difficulte moyenne (`2.28`) et la 3e plus courte en reponse (`116.20`).
- `Économie et finances publiques` combine bon volume (`966` flashcards), difficulte basse (`2.41`) et reponses courtes (`126.84`).
- `Licence 2 - Semestre 4` est moins extreme, mais le signal est important car il porte sur le plus gros volume (`3481` flashcards).

## Classement combine

Score combine = rang difficulte la plus basse + rang reponse la plus courte.
Plus le score est bas, plus la matiere est faible selon cet audit.

| Rang | Matiere | Flashcards | Avg difficulty | Avg response len | % diff <= 2 | % reponses < 80 | Score combine |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | M1 Politique economique | 414 | 2.43 | 112.91 | 61.4% | 33.6% | 4 |
| 2 | Scolarite L3 | 169 | 2.28 | 116.20 | 66.9% | 30.2% | 4 |
| 3 | Économie et finances publiques | 966 | 2.41 | 126.84 | 58.9% | 28.6% | 7 |
| 4 | Licence 2 - Semestre 4 | 3481 | 2.44 | 130.63 | 56.2% | 25.5% | 11 |
| 5 | M1 Management et egalites | 463 | 2.50 | 129.21 | 53.8% | 27.2% | 15 |
| 6 | Licence 3 - Semestre 6 | 2610 | 2.47 | 137.31 | 53.5% | 25.1% | 15 |
| 7 | Questions contemporaines | 666 | 2.57 | 114.58 | 52.3% | 34.4% | 17 |
| 8 | Licence 3 - Semestre 5 | 2739 | 2.49 | 137.03 | 51.8% | 22.1% | 17 |
| 9 | Questions sociales | 1188 | 2.47 | 139.93 | 53.5% | 23.0% | 17 |
| 10 | Licence 2 - Semestre 3 | 3327 | 2.49 | 143.47 | 52.6% | 23.1% | 19 |

## Top matieres par difficulte moyenne la plus basse

| Rang | Matiere | Flashcards | Avg difficulty | Avg response len |
| --- | --- | ---: | ---: | ---: |
| 1 | Scolarite L3 | 169 | 2.28 | 116.20 |
| 2 | Économie et finances publiques | 966 | 2.41 | 126.84 |
| 3 | M1 Politique economique | 414 | 2.43 | 112.91 |
| 4 | Licence 2 - Semestre 4 | 3481 | 2.44 | 130.63 |
| 5 | Licence 3 - Semestre 6 | 2610 | 2.47 | 137.31 |
| 6 | Questions sociales | 1188 | 2.47 | 139.93 |
| 7 | Licence 2 - Semestre 3 | 3327 | 2.49 | 143.47 |
| 8 | Licence 3 - Semestre 5 | 2739 | 2.49 | 137.03 |

## Top matieres par reponses les plus courtes

| Rang | Matiere | Flashcards | Avg response len | Avg difficulty |
| --- | --- | ---: | ---: | ---: |
| 1 | M1 Politique economique | 414 | 112.91 | 2.43 |
| 2 | Questions contemporaines | 666 | 114.58 | 2.57 |
| 3 | Scolarite L3 | 169 | 116.20 | 2.28 |
| 4 | M1 Droit et legistique | 106 | 118.30 | 2.57 |
| 5 | Économie et finances publiques | 966 | 126.84 | 2.41 |
| 6 | M1 Management et egalites | 463 | 129.21 | 2.50 |
| 7 | Licence 2 - Semestre 4 | 3481 | 130.63 | 2.44 |
| 8 | Documents divers | 177 | 133.51 | 2.59 |

## Interpretation

- Signal le plus solide:
  - `Économie et finances publiques`
  - `Licence 2 - Semestre 4`
  - `M1 Politique economique`

Ces trois matieres cumulent un volume significatif et des scores faibles sur les deux axes.

- Signal a surveiller mais volume plus petit:
  - `Scolarite L3`
  - `M1 Droit et legistique`
  - `Documents divers`

## Recommandation prioritaire

Si vous devez lancer une passe de regeneration ou de cleanup qualite, l'ordre prioritaire le plus defensable est:

1. `M1 Politique economique`
2. `Économie et finances publiques`
3. `Licence 2 - Semestre 4`
4. `Scolarite L3`
5. `Questions contemporaines`
