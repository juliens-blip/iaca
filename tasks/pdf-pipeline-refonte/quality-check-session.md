# Rapport qualité des fiches — Session 2026-03-25

## Contexte

Aucune fiche n'a été générée lors de la session du 2026-03-25 : le batch T-048 a été bloqué par le rate limit Claude (reset 8h00). L'audit porte donc sur :
1. Les **3 meilleures fiches en DB** (ids 2525, 2527, 2528) — représentatives de la génération haute qualité
2. La **dernière session batch** (2026-03-09, ids ~1421-1724) — révèle des problèmes systémiques

---

## Partie 1 — Fiches haute qualité (ids 2525, 2527, 2528)

### Fiche 2528 — "Le sport comme phénomène social et politique"

| Critère | Valeur | Verdict |
|---|---|---|
| Sections | 10/10 | ✅ |
| Sections courtes (<220 chars) | 0 | ✅ |
| Titres génériques | 0 | ✅ |
| Titres dupliqués | 0 | ✅ |
| Longueur moyenne section | 1632 chars | ✅ |
| Contenu structuré | 2/10 | ⚠️ |

**Verdict : OK**

Exemples de titres de sections :
- "L'ascension du sport au rang de fait social total dans la modernité" ✅
- "Les 'maîtres du soupçon' appliqués au sport : Marx, Nietzsche et Freud" ✅
- "La tension centrale : le sport, réalité autonome ou outil..." ✅

Contenu : reformulé, références académiques (Mauss, Huizinga, Caillois), pas de copier-coller détecté.

---

### Fiche 2527 — "La justice en procès : légitimité, indépendance et place dans l'État démocratique"

| Critère | Valeur | Verdict |
|---|---|---|
| Sections | 10/10 | ✅ |
| Sections courtes (<220 chars) | 0 | ✅ |
| Titres génériques | 0 | ✅ |
| Titres dupliqués | 0 | ✅ |
| Longueur moyenne section | 1943 chars | ✅ |
| Contenu structuré | 10/10 | ✅ |

**Verdict : OK**

Exemples de titres :
- "La polysémie du concept de justice : valeur, activité et institution" ✅
- "Le paradoxe de la justice contemporaine : plus indépendante, moins légitime" ✅
- "Du sacrifice au procès : la justice institutionnelle comme substitut civilisationnel" ✅

Contenu : structure cohérente avec marqueurs pédagogiques (**Définition et principe**, **Mécanisme**, **Illustration**), jurisprudence citée (Montesquieu, Girard). Très haute qualité.

---

### Fiche 2525 — "Le principe de continuité du service public"

| Critère | Valeur | Verdict |
|---|---|---|
| Sections | 10/10 | ✅ |
| Sections courtes (<220 chars) | 0 | ✅ |
| Titres génériques | 0 | ✅ |
| Titres dupliqués | 0 | ✅ |
| Longueur moyenne section | 1732 chars | ✅ |
| Contenu structuré | 9/10 | ✅ |

**Verdict : OK**

Exemples de titres :
- "L'arrêt Winkell (1909) : la continuité comme fondement de l'interdiction..." ✅
- "L'arrêt Dehaene (1950) : la conciliation entre droit de grève et continuité" ✅
- "La décision du Conseil constitutionnel de 1979 : la continuité élevée au rang constitutionnel" ✅

Contenu : structure jurisprudentielle chronologique, balises pédagogiques, pas de copier-coller. Excellente fiche de concours administratif.

---

## Partie 2 — Session batch 2026-03-09 (problèmes systémiques)

### Métriques globales

| Indicateur | Valeur |
|---|---|
| Fiches générées | ~304 fiches (ids 1421–1724) |
| Fiches avec titre fallback ("Fiche - ") | **100%** |
| Fiches avec sections insuffisantes (<6) | ~40% |
| Documents avec fiches dupliquées | **75 documents** |
| Max doublons par document | 6 fiches pour le même doc |

### Problème 1 — Titre fallback systématique (CRITIQUE)

**Toutes** les fiches de cette session ont un titre de la forme `"Fiche - <nom_fichier>"` au lieu d'un titre généré par Claude.

Cause probable : le prompt de `generer_fiche` retourne `{"titre_fiche": "..."}` mais le code assemblait `titre_fiche` depuis le premier chunk seulement, et si ce chunk retournait un titre invalide ou si Claude ne renvoyait pas le champ, le fallback `f"Fiche - {titre_doc}"` prenait le relais systématiquement.

**Impact** : UI dégradée (titres non informatifs), expérience utilisateur médiocre.

### Problème 2 — Fiches dupliquées (CRITIQUE)

75 documents ont **plusieurs fiches** (4 à 6 par document). Cela indique que le batch a été lancé plusieurs fois sans vérification préalable de l'existence d'une fiche.

**Impact** : pollution de la DB, affichage incohérent côté frontend.

### Problème 3 — Sections insuffisantes (~40%)

Plusieurs fiches avec 1 à 5 sections au lieu des 6 minimum requis. Probablement lié à des documents sources trop courts ou à des extractions PDF dégradées.

**Impact** : fiches incomplètes présentées aux utilisateurs.

---

## Synthèse

| Périmètre | Verdict |
|---|---|
| Fiches haute qualité (2525, 2527, 2528) | **OK — qualité excellente** |
| Batch 2026-03-09 | **KO — 3 problèmes critiques** |

## Actions correctives recommandées

1. **Dédoublonner** : supprimer les fiches en doublons (garder la plus récente par document) — peut s'écrire en SQL : `DELETE FROM fiches WHERE id NOT IN (SELECT MAX(id) FROM fiches GROUP BY document_id)`
2. **Titre fallback** : vérifier pourquoi `titre_fiche` n'est pas capturé depuis le premier chunk dans la session 2026-03-09 — peut être lié à une version ancienne de `generer_fiche` sans l'assemblage multi-chunk
3. **Guard anti-doublon** : `fetch_docs_without_fiche` est correct (`NOT EXISTS`) mais le batch semble avoir été relancé plusieurs fois sur les mêmes docs — ajouter un log de vérification en début de batch
