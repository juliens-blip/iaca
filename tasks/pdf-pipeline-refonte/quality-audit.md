# Audit qualité des fiches existantes

Date: 2026-03-17
Base auditée: `/home/julien/Documents/IACA/data/iaca.db`

## Méthodologie

Le binaire `sqlite3` n'est pas installé dans cet environnement. La base a donc été interrogée avec le module standard Python `sqlite3`, sur le même fichier `data/iaca.db`.

Requête exécutée:

```sql
SELECT f.id, f.titre, f.resume, fs.titre as section_titre, fs.contenu, LENGTH(fs.contenu) as len
FROM fiches f
JOIN fiche_sections fs ON fs.fiche_id = f.id
ORDER BY RANDOM()
LIMIT 40;
```

Constat important: la requête ci-dessus n'échantillonne pas `20 fiches avec toutes leurs sections`, mais `40 sections aléatoires`. Sur ce tirage précis, cela a donné `40 sections issues de 40 fiches distinctes`.

Critères de revue:

- `Titre de section générique`: titre de type `Section 1`, mot isolé auto-dérivé (`puis`, `code`, `rare`), ou intertitre non informatif.
- `Contenu brut / non reformulé`: texte qui ressemble à une extraction directe du support source, à des notes de cours, à une transcription orale, à une citation brute, à une consigne pédagogique ou à un fragment incomplet.
- `Contenu reformulé`: texte rédigé comme une synthèse autonome, avec phrases complètes, progression logique et angle explicite.

## Résultats

- Nb fiches sampled: `40`
- Nb sections revues: `40`
- % with generic section titles: `27/40` soit `67.5%`
- % with raw/non-reformulated content: `25/40` soit `62.5%`
- Average section length: `375.5` caractères

Signal complémentaire:

- Longueur moyenne des sections `brutes`: `198.4` caractères
- Longueur moyenne des sections `reformulées`: `670.6` caractères
- Longueur moyenne des sections à titre `générique`: `218.4` caractères
- Longueur moyenne des sections à titre `spécifique`: `701.7` caractères

Lecture globale: l'échantillon montre encore une majorité de sections issues d'une extraction ou d'un découpage faible, avec des titres auto-générés peu utiles. Deux sections sont des cas intermédiaires: prose acceptable, mais titrage encore générique.

## Audit détaillé de l'échantillon

| # | Fiche | Titre de section | Titre générique | Contenu brut | Note |
|---|---:|---|---|---|---|
| 1 | 891 | `Section 1 - chapitre` | Oui | Oui | Métadonnée de chapitre, sans vraie synthèse. |
| 2 | 425 | `Section 5 - étapes` | Oui | Oui | Plan de cours sur l'UE/Brexit, proche du support source. |
| 3 | 1279 | `Section 8 — Enfin` | Oui | Oui | Fragment de transition, incomplet hors contexte. |
| 4 | 1548 | `Section 6 - puis` | Oui | Oui | Transcription orale de cours. |
| 5 | 855 | `Section 3 - affaiblissement` | Oui | Oui | Notes télégraphiques et abréviations. |
| 6 | 405 | `Section 6 - modèle` | Oui | Oui | Intertitre auto-dérivé, contenu de plan de cours. |
| 7 | 105 | `Section 4 - peut` | Oui | Oui | Citation brute du texte juridique. |
| 8 | 2218 | `Conséquences du Maintien de la Personnalité Morale Pendant la Liquidation` | Non | Non | Bonne synthèse juridique, autonome et claire. |
| 9 | 106 | `Section 5 - alors` | Oui | Oui | Style oral (`Alors d'abord`), non éditorialisé. |
| 10 | 161 | `Section 1 - dénonciation` | Oui | Oui | Question de cours brute, sans reformulation. |
| 11 | 102 | `Section 1 - troisième` | Oui | Oui | Introduction de chapitre recopiée. |
| 12 | 139 | `Section 2 - source` | Oui | Oui | Liste d'acteurs et sources, syntaxe de notes. |
| 13 | 1643 | `Section 1 - état` | Oui | Oui | Presque un simple intertitre, pas une section synthétique. |
| 14 | 1003 | `Section 6 - attendant` | Oui | Oui | Mot de fin aux étudiants, hors format fiche. |
| 15 | 1682 | `Section 3 - s'agit` | Oui | Oui | Liste managériale brute avec numérotation. |
| 16 | 1005 | `Section 2 - enquête` | Oui | Non | Prose juridique correcte, mais titrage encore auto-généré. |
| 17 | 155 | `Section 1 - clélia` | Oui | Oui | Énoncé de cas pratique, non synthétisé. |
| 18 | 460 | `Section 2 - vous` | Oui | Oui | Consignes pédagogiques, pas une reformulation. |
| 19 | 1723 | `Section 1 - grés` | Oui | Oui | Fragment de mise en situation, texte tronqué. |
| 20 | 1919 | `Universalité de l'Information et Contrôle : Une Perspective Historique` | Non | Non | Angle clair, bonne contextualisation historique. |
| 21 | 292 | `Section 3 - d'abord` | Oui | Oui | Explication orale non synthétisée. |
| 22 | 2322 | `Approfondissement de la Stratégie RSE : Actions Environnementales Avancées` | Non | Non | Titre précis, contenu actionnable et structuré. |
| 23 | 1319 | `Section 5 — Rare` | Oui | Oui | Abréviations et références jurisprudentielles brutes. |
| 24 | 1099 | `Section 4 - code` | Oui | Oui | Citation de code tronquée, faible valeur pédagogique seule. |
| 25 | 142 | `Section 2 - s'agit` | Oui | Oui | Phrase très courte, strictement introductive. |
| 26 | 1734 | `Arbitrages pratiques : congés, matériel personnel et sobriété énergétique (situations 6 et 11)` | Non | Non | Bonne synthèse opérationnelle et contextualisée. |
| 27 | 114 | `Section 3 - code` | Oui | Oui | Définition de cours très courte, peu retravaillée. |
| 28 | 2168 | `Gestion des retards répétés d'un agent` | Non | Non | Procédure claire, progressive, directement exploitable. |
| 29 | 2235 | `Justification de la Restriction aux Personnes Morales (Loi du 15 mai 2001)` | Non | Non | Explication juridique précise et autonome. |
| 30 | 2240 | `Contrôle de Constitutionnalité et Normes Supra-Législatives` | Non | Non | Section thématique cohérente, ton synthétique. |
| 31 | 520 | `Section 3 - étudiant` | Oui | Oui | Consigne d'examen, pas un contenu de fiche. |
| 32 | 2304 | `Chômage Structurel vs. Conjoncturel et Phénomène d'Hystérèse` | Non | Non | Bonne synthèse économique. |
| 33 | 407 | `Section 2 - distinction` | Oui | Oui | Fragment de phrase quasi inexploitable seul. |
| 34 | 1403 | `Définition et périmètre du droit administratif des biens` | Non | Non | Définition structurée, oppositions conceptuelles claires. |
| 35 | 949 | `Section 3 - article` | Oui | Oui | Copie quasi littérale d'article de code. |
| 36 | 2312 | `Le contexte : L'âge d'or du droit administratif et la question du critère pertinent` | Non | Non | Contexte doctrinal bien posé. |
| 37 | 2246 | `Codification-Modification (Lege Ferenda)` | Non | Non | Définition et portée bien reformulées. |
| 38 | 1729 | `Différences avec la dissertation et exigences renforcées` | Non | Non | Comparaison claire et pédagogique. |
| 39 | 1801 | `Activation progressive des infractions : logique jurisprudentielle anti-impunité` | Non | Non | Analyse synthétique aboutie. |
| 40 | 1529 | `Section 1 - crise` | Oui | Non | Contenu lisible, mais titre de section faible et non éditorial. |

## Exemples de bonnes sections

- Fiche `2168`, section `Gestion des retards répétés d'un agent`: titre directement exploitable, contenu organisé en étapes d'action concrètes.
- Fiche `1403`, section `Définition et périmètre du droit administratif des biens`: définition nette, distinctions conceptuelles explicites, rédaction autonome.
- Fiche `1801`, section `Activation progressive des infractions : logique jurisprudentielle anti-impunité`: angle analytique clair et synthèse juridique aboutie.

## Exemples de mauvaises sections

- Fiche `891`, section `Section 1 - chapitre`: quasi uniquement une référence de chapitre.
- Fiche `1279`, section `Section 8 — Enfin`: simple fragment de transition, inutilisable seul.
- Fiche `1319`, section `Section 5 — Rare`: abréviations, références empilées, pas de reformulation.
- Fiche `1003`, section `Section 6 - attendant`: message de fin d'un support de révision, hors sujet pour une fiche.

## Recommandations

- Refuser les titres de section faibles au moment de la génération: patrons `^Section`, mot unique non informatif, ou reprise mécanique du premier token du paragraphe.
- Ajouter une étape de réécriture systématique pour convertir transcription orale, notes télégraphiques, citations de code et consignes pédagogiques en synthèses autonomes.
- Mettre en quarantaine les sections trop courtes ou suspectes avant insertion en base, par exemple `< 150 caractères`, présence d'artefacts OCR, abondance d'abréviations, ou absence de verbe/conclusion.
- Ajouter un audit automatique post-génération sur un échantillon aléatoire avec quatre métriques simples: `% titres génériques`, `% sections suspectées brutes`, longueur moyenne, et liste de sections à revoir manuellement.
