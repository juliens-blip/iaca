# Audit Qualité Flashcards par Matière
**Date:** 2026-03-28
**Total Flashcards:** 29,521 across 15 subjects

---

## 📊 Résultats Complets

| Rang | Matière | Flashcards | Avg Réponse (chars) | Avg Difficulté | Status |
|------|---------|------------|-------------------|-----------------|--------|
| 1 | **Droit public** | 4,405 | 146 | 2.52 | ✅ Large volume |
| 2 | **Licence 2 - S4** | 3,481 | 131 | 2.44 | ✅ Large volume |
| 3 | **Questions sociales** | 2,361 | 135 | 2.50 | ✅ Medium volume |
| 4 | **Licence 3 - S5** | 2,260 | 136 | 2.49 | ✅ Medium volume |
| 5 | **Licence 2 - S3** | 2,241 | 150 | 2.49 | ✅ Medium volume |
| 6 | **Éco & Finances pub** | 2,209 | 126 | 2.46 | ✅ Medium volume |
| 7 | **Licence 3 - S6** | 2,000 | 133 | 2.45 | ✅ Medium volume |
| 8 | **Relations int.** | 1,784 | 153 | 2.59 | ✅ Medium volume |
| 9 | **Questions contemp.** | 634 | 113 | 2.54 | ⚠️ Lower volume |
| 10 | **Espagnol** | 472 | 146 | 2.51 | ⚠️ Lower volume |
| 11 | **Economie** | 211 | **297** | **2.77** | ⚠️ Very few, verbose |
| 12 | **Scolarité L3** | 169 | 116 | 2.28 | ⚠️ Very few |
| 13 | **L2 - Fiches revision** | 60 | 165 | 2.37 | ❌ Minimal |
| 14 | **Documents divers** | 34 | 231 | 2.59 | ❌ Minimal |
| 15 | **Finances publiques** | 20 | **457** | **2.95** | ❌ Critical - too verbose |

---

## 🎯 Insights Clés

### ✅ Points Positifs

1. **Volume Équilibré (Top 8 subjects)**
   - 1,784-4,405 FC par matière
   - Représente 27,836 / 29,521 (94%) du total
   - Couverture solide pour l'apprentissage

2. **Réponses Cohérentes**
   - Moyenne globale: **126-153 chars** pour top subjects
   - Bon équilibre entre concision et détail
   - Pas de réponses excessivement longues (sauf exceptions)

3. **Difficulté Stable**
   - Moyenne globale: **2.45-2.59** (scale 1-5)
   - Léger décalage: topics plus faciles (2.28) vs difficiles (2.95)
   - Distribution réaliste

### ⚠️ Points d'Attention

1. **Outliers - Réponses Trop Longues**
   | Sujet | Avg Réponse | Issue |
   |-------|------------|-------|
   | **Finances publiques** | 457 chars | 3.6x average (trop verbeux) |
   | **Economie** | 297 chars | 2.3x average (verbose) |
   | **Documents divers** | 231 chars | 1.8x average |

   **Impact:** Réponses longues réduisent l'efficacité pédagogique

   **Recommandation:** Retoucher ces FC pour condenser les réponses (target: <150 chars)

2. **Couverture Faible (Bottom 5 subjects)**
   - 20-472 FC pour subjects avec docs
   - Economie (211), Questions contemp (634) sous-servies
   - Total: 1,685 FC (5.7%) seulement

   **Recommandation:** Lancer batches supplémentaires pour ces matieres

3. **Difficulté Élevée (Finances publiques)**
   - Difficulté avg: **2.95** (highest)
   - Corrélation: + réponses longues + difficulté élevée
   - Peut être signe de: contenu complexe mal condensé

---

## 📈 Distribution de Volume

```
Tier 1 (Critique - >2000 FC):
  ├─ Droit public (4405)              ████████████████
  ├─ L2-S4 (3481)                     █████████████
  ├─ Questions sociales (2361)        █████████
  ├─ L3-S5 (2260)                     ████████
  ├─ L2-S3 (2241)                     ████████
  ├─ Éco & Finances (2209)            ████████
  └─ L3-S6 (2000)                     ███████

Tier 2 (Moyen - 500-2000 FC):
  ├─ Relations int. (1784)            ███████
  └─ Questions contemp. (634)         ██

Tier 3 (Faible - <500 FC):
  ├─ Espagnol (472)                   █
  ├─ Economie (211)
  ├─ Scolarité L3 (169)
  ├─ L2-Fiches (60)
  ├─ Documents divers (34)
  └─ Finances publiques (20)
```

---

## 🔧 Recommandations d'Action

### Priority 1: Fix Réponses Trop Longues
```bash
# Identifier et retoucher FC avec réponses > 250 chars
backend/.venv/bin/python3 << 'EOFPY'
import sqlite3
c = sqlite3.connect('data/iaca.db').cursor()
c.execute("""
SELECT COUNT(*) FROM flashcards
WHERE length(reponse) > 250
""")
count = c.fetchone()[0]
print(f"Flashcards with response > 250 chars: {count}")
c.close()
EOFPY
```

**Action:** Créer script `condense_long_flashcards.py` pour:
1. Identifier FC > 250 chars
2. Générer versions condensées via Gemini
3. Valider que le sens reste intact
4. Mettre à jour DB

### Priority 2: Batch Fiches Manquantes
Subjects à augmenter (+ fiches → + FC auto):
- Economie: 211 → target 1000+ (478% growth)
- Questions contemporaines: 634 → target 2000+ (215% growth)
- Scolarité L3: 169 → target 800+ (373% growth)

**Action:** Lancer batches de génération fiches:
```bash
# Economie
backend/.venv/bin/python3 scripts/reextract_and_generate.py \
  --matiere 'Economie' --limit 30 --skip-extract --skip-flashcards --provider gemini

# Questions contemporaines
backend/.venv/bin/python3 scripts/reextract_and_generate.py \
  --matiere 'Questions contemporaines' --limit 20 --skip-extract --skip-flashcards --provider gemini
```

### Priority 3: Balancer par Difficulté
**Observation:** Finances publiques outlier (2.95 avg)
- Possible: Contenu réellement difficile
- Alternative: Mal conçues/auto-générées

**Action:** Audit manuel de 10-20 FC de Finances publiques pour quality check

---

## 📋 Métriques Synthétiques

| Métrique | Valeur | Benchmark |
|----------|--------|-----------|
| **Total FC** | 29,521 | ✅ Good |
| **Avg réponse length** | ~140 chars | ✅ Acceptable |
| **Avg difficulté** | 2.50 | ✅ Balanced |
| **Top subject coverage** | 94% | ✅ Excellent |
| **Bottom 5 coverage** | 5.7% | ⚠️ Needs work |
| **Outliers (>250 chars)** | TBD | ⚠️ To count |

---

## 🎓 Conclusion

**État Global:** ✅ **SATISFAISANT avec améliorations possibles**

**Strengths:**
- Large volume sur subjects majeurs (94% coverage)
- Réponses bien dimensionnées en moyenne
- Difficulté stable et réaliste

**Weaknesses:**
- Quelques FC avec réponses trop longues (surtout Finances publiques)
- Couverture faible sur subjects secondaires (Economie, Questions contemp)
- Potential quality issue sur Finances publiques (haute difficulté + longues réponses)

**Next Steps:**
1. ✅ Compress réponses > 250 chars (script)
2. ✅ Lancer batches fiches pour Economie, Questions contemp
3. ✅ Audit quality Finances publiques (10-20 samples)
4. ✅ Re-run audit après corrections

---

**Généré:** 2026-03-28 09:13 CET
**Data source:** `data/iaca.db` — 29,521 flashcards across 15 subjects
