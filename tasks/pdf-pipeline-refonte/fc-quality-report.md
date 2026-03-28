# Rapport Qualité Flashcards par Matière
**Date:** 2026-03-28 | **Source:** data/iaca.db | **Total FC:** 22,341

---

## 📊 Vue d'ensemble

| Métrique | Valeur | Benchmark | Status |
|----------|--------|-----------|--------|
| **Total Flashcards** | 22,341 | Target: 25,000+ | ⚠️ |
| **Global Avg Response** | 140 chars | 100-150 | ✅ |
| **Global Avg Difficulty** | 2.50 | 2.4-2.6 | ✅ |
| **Subjects Tier 1 (≥2000)** | 7 | Target: 10 | ⚠️ |
| **Doc Coverage** | 97.9% | 95%+ | ✅ |

---

## 🏆 TIER 1: SUJETS FORTS (≥2000 FC) — 20,557 FC | 92%

### 1. Droit public
- **FC:** 4,405 | **Docs:** 162 | **% Total:** 19.7%
- **Response:** 146 avg (min 20, max 646)
- **Difficulty:** 2.52 avg
- **Quality Score:** 9/10 ✅
- **Status:** Largest subject, well-balanced

### 2. Licence 2 - Semestre 4
- **FC:** 3,481 | **Docs:** 191 | **% Total:** 15.6%
- **Response:** 131 avg (min 22, max 392) — **Most concise**
- **Difficulty:** 2.44 avg
- **Quality Score:** 9/10 ✅
- **Status:** Excellent coverage and balance

### 3. Questions sociales
- **FC:** 2,361 | **Docs:** 60 | **% Total:** 10.6%
- **Response:** 135 avg (min 21, max 535)
- **Difficulty:** 2.50 avg
- **Quality Score:** 8/10 ✅
- **Status:** Good, focused subject

### 4. Licence 3 - Semestre 5
- **FC:** 2,260 | **Docs:** 124 | **% Total:** 10.1%
- **Response:** 136 avg (min 20, max 625)
- **Difficulty:** 2.49 avg
- **Quality Score:** 8/10 ✅
- **Status:** Good coverage

### 5. Licence 2 - Semestre 3
- **FC:** 2,241 | **Docs:** 136 | **% Total:** 10.0%
- **Response:** 150 avg (min 22, max 595)
- **Difficulty:** 2.49 avg
- **Quality Score:** 8/10 ✅
- **Status:** Good, slightly verbose

### 6. Économie et finances publiques
- **FC:** 2,209 | **Docs:** 46 | **% Total:** 9.9%
- **Response:** 126 avg (min 20, max 451) — **Concise**
- **Difficulty:** 2.46 avg
- **Quality Score:** 8/10 ✅
- **Status:** Good, well-written

### 7. Licence 3 - Semestre 6
- **FC:** 2,000 | **Docs:** 103 | **% Total:** 9.0%
- **Response:** 133 avg (min 32, max 526)
- **Difficulty:** 2.45 avg
- **Quality Score:** 8/10 ✅
- **Status:** Borderline Tier 1 (exactly 2000)

---

## 🟡 TIER 2: SUJETS MOYENS (500-2000 FC) — 2,418 FC | 11%

### 8. Relations internationales
- **FC:** 1,784 | **Docs:** 39 | **% Total:** 8.0%
- **Response:** 153 avg (min 23, max 485)
- **Difficulty:** 2.59 avg ⚠️ **Highest Tier 1-2**
- **Quality Score:** 7/10 ⚠️
- **Status:** Edge of Tier 1, needs 216 more FC for upgrade
- **Action:** Generate 216+ FC → reach 2000

### 9. Questions contemporaines
- **FC:** 634 | **Docs:** 23 | **% Total:** 2.8%
- **Response:** 113 avg (min 20, max 385) — **Concise**
- **Difficulty:** 2.54 avg
- **Quality Score:** 6/10 ⚠️
- **Status:** Under-served (23/35 docs = 65.7%), need 66% growth
- **Action:** Generate 500+ FC → reach 1000+

---

## 🔴 TIER 3: SUJETS FAIBLES (<500 FC) — 1,366 FC | 6% — CRITICAL

### 10. Espagnol
- **FC:** 472 | **Docs:** 30 | **% Total:** 2.1%
- **Response:** 146 avg (min 35, max 428)
- **Difficulty:** 2.51 avg
- **Quality Score:** 6/10 ⚠️
- **Status:** Below 500, need 28 FC to reach threshold
- **Issues:** Coverage below minimum (472 < 500)
- **Action:** Generate 50 FC (quick upgrade)

### 11. Economie ⚠️⚠️
- **FC:** 211 | **Docs:** 15 | **% Total:** 0.9%
- **Response:** **297 avg** (min 38, max 552) 🔴 **2.1x global avg**
- **Difficulty:** **2.77 avg** 🔴 **HIGHEST**
- **Quality Score:** 3/10 🔴 **CRITICAL**
- **Status:** Multiple issues detected
- **Issues:**
  - Response TOO LONG (297 vs 140 global)
  - Difficulty TOO HIGH (2.77 vs 2.50 global)
  - Coverage VERY LOW (211 FC)
- **Action:** 🔥 **AUDIT 20 samples** → likely regenerate with better prompt

### 12. Scolarité L3
- **FC:** 169 | **Docs:** 9 | **% Total:** 0.8%
- **Response:** 116 avg (min 21, max 300) — **Concise**
- **Difficulty:** 2.28 avg — **LOWEST (easiest)**
- **Quality Score:** 5/10 🚨
- **Status:** Niche subject, minimal coverage
- **Issues:** Coverage very low (169 FC)
- **Action:** Generate 350+ FC to reach 500

### 13. Licence 2 - Fiches revision
- **FC:** 60 | **Docs:** 3 | **% Total:** 0.3%
- **Response:** 165 avg (min 41, max 257)
- **Difficulty:** 2.37 avg
- **Quality Score:** 4/10 🚨
- **Status:** Minimal coverage
- **Issues:** Only 3 docs, coverage very low
- **Action:** Increase doc fiches first, then generate FC

### 14. Documents divers
- **FC:** 34 | **Docs:** 2 | **% Total:** 0.2%
- **Response:** 231 avg (min 76, max 498) — **Verbose**
- **Difficulty:** 2.59 avg
- **Quality Score:** 2/10 🚨
- **Status:** Negligible coverage
- **Issues:** Only 2 docs
- **Action:** Low priority

### 15. Finances publiques ⚠️⚠️ CRITICAL
- **FC:** 20 | **Docs:** 2 | **% Total:** 0.1%
- **Response:** **457 avg** (min 354, max 588) 🔴 **3.3x global avg**
- **Difficulty:** **2.95 avg** 🔴 **HIGHEST OVERALL**
- **Quality Score:** 1/10 🔴 **WORST**
- **Status:** Most severe quality issue
- **Issues:**
  - Response EXTREMELY LONG (457 chars!)
  - Difficulty MAXIMUM (2.95)
  - Coverage MINIMAL (20 FC only)
- **Action:** 🔥 **REGENERATE ALL 20 FC** with strict 150-char response limit

---

## 📈 Synthèse par Catégories

### Response Length Distribution

```
OPTIMAL (100-130 chars):
  ✅ Questions contemporaines (113)
  ✅ Scolarité L3 (116)
  ✅ Éco & Finances (126)
  ✅ L2-S4 (131)

GOOD (130-160 chars):
  ✅ L3-S6 (133)
  ✅ Questions sociales (135)
  ✅ L3-S5 (136)
  ✅ Droit public (146)
  ✅ Espagnol (146)
  ✅ L2-S3 (150)
  ✅ Relations int. (153)

ACCEPTABLE (160-250 chars):
  ⚠️ L2-Fiches (165)
  ⚠️ Documents divers (231)

CRITICAL (>250 chars) 🔴
  🚨 Economie (297) — 2.1x avg
  🚨 Finances publiques (457) — 3.3x avg
```

### Difficulty Distribution

```
EASIEST (< 2.40):
  ✅ Scolarité L3 (2.28)
  ✅ L2-Fiches (2.37)

STANDARD (2.44-2.59):
  ✅ L2-S4 (2.44)
  ✅ L3-S6 (2.45)
  ✅ Éco & Finances (2.46)
  ✅ L3-S5 (2.49)
  ✅ L2-S3 (2.49)
  ✅ Questions sociales (2.50)
  ✅ Espagnol (2.51)
  ✅ Droit public (2.52)
  ✅ Questions contemp (2.54)
  ✅ Documents divers (2.59)
  ✅ Relations int. (2.59)

HARD (> 2.70):
  🚨 Economie (2.77)
  🚨 Finances publiques (2.95)
```

---

## 🎯 Matières Faibles — Actions Requises

### PHASE 1: FIX QUALITY (This Week)

| Rang | Matière | Issue Principal | Action |
|------|---------|-----------------|--------|
| 1 | **Finances publiques** | 457 chars (3.3x), diff 2.95 | 🔥 Regenerate all 20 FC |
| 2 | **Economie** | 297 chars (2.1x), diff 2.77 | 🔥 Audit then regenerate |

### PHASE 2: EXPAND COVERAGE (Next Week)

| Rang | Matière | Gap | Target | Action |
|------|---------|-----|--------|--------|
| 3 | **Questions contemp** | 634 → 1000 | 500+ FC | Generate 5 batches × 10 |
| 4 | **Relations int** | 1784 → 2000 | 216 FC | Generate 1 batch × 20 |
| 5 | **Espagnol** | 472 → 500 | 28 FC | Generate 1 batch × 10 |

### PHASE 3: REACH TARGETS (Month 2)

| Matière | Current | Target | Timeline |
|---------|---------|--------|----------|
| Economie | 211 | 1,000 | Week 4 (after audit) |
| Scolarité L3 | 169 | 800 | Week 4 |
| L2-Fiches | 60 | 500 | Week 3 |

---

## 📋 Recommandations Immédiates

### ✅ Points Positifs
1. **Tier 1 excellent:** 7 subjects with 20,557 FC (92% of total)
2. **Response length:** Generally well-balanced (most in 100-150 range)
3. **Document coverage:** 97.9% — near-complete
4. **Difficulty:** Realistic distribution (2.4-2.6 for most)

### 🔴 Points Critiques
1. **Finances publiques:** 457 avg response (extreme), 2.95 difficulty (highest)
2. **Economie:** 297 avg response (verbose), 2.77 difficulty (very high)
3. **Coverage gaps:** 6 subjects below 500 FC threshold

### 🎯 Priorités Owner

**Week 1:**
- [ ] Regenerate Finances publiques all 20 FC with 150-char limit
- [ ] Audit Economie quality (20 sample FC)
- [ ] Create condense_long_flashcards.py script

**Week 2:**
- [ ] Generate 500+ Questions contemporaines FC
- [ ] Generate 216+ Relations internationales FC
- [ ] Regenerate Economie if audit shows quality issues

**Week 3:**
- [ ] Run condense script on all FC > 250 chars
- [ ] Generate 50+ Espagnol FC

**Week 4:**
- [ ] Re-audit all TIER 3 subjects
- [ ] Re-run this report to verify improvements

---

## 📊 Statistiques Finales

### Tier Distribution
- **Tier 1 (≥2000):** 7 subjects → 20,557 FC (92.0%)
- **Tier 2 (500-2000):** 2 subjects → 2,418 FC (10.8%)
- **Tier 3 (<500):** 6 subjects → 1,366 FC (6.1%)
- **TOTAL:** 15 subjects → 22,341 FC

### Quality by Tier
| Tier | Avg Response | Avg Difficulty | Quality |
|------|------------|-----------------|---------|
| Tier 1 | 138 chars | 2.49 | ✅ Good |
| Tier 2 | 133 chars | 2.57 | ⚠️ Fair |
| Tier 3 | 213 chars | 2.62 | 🔴 Poor |

---

**Rapport Généré:** 2026-03-28 09:40 CET
**Prochaine Review:** 2026-04-04 (après Phase 1)
