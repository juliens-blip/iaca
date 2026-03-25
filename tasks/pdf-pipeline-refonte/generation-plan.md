# Plan de Génération — 2026-03-25

## 📊 État Actuel

```
Fiches générées (dernière 48h): 0
Flashcards générées (dernière 48h): 0
Status: Quota Claude reset à 8:00 AM CET

Documents sans fiche: 587/1614 (36.4%)
Documents < 5 flashcards: 405/1614 (25%)
```

**Dernière mise à jour status:** 2026-03-19 (591 → 587 docs, léger progrès)

---

## 🎯 Stratégie de Génération

### Contraintes Identifiées

1. **Quota Claude quotidien très limité** (test QC a montré ~2-3 fiches/jour avant rate-limit)
2. **Rate-limit fonctionne** (retry avec backoff exponentiel 30s/60s activé)
3. **Pas de fallback Gemini** actuellement → abandon quand Claude rate-limit
4. **Flashcards moins critiques** que fiches en priorité

### Approche Recommandée

**Phase 1 (Court terme - cette semaine):**
- Générer **fiches** sur les 3 matieres prioritaires (par batches de 10-15 docs)
- Espacer les batches pour eviter rate-limit quotidien
- Monitoring des logs pour ajuster si nécessaire

**Phase 2 (Moyen terme):**
- Implémenter fallback Gemini quand Claude rate-limit
- Relancer flashcards sur matieres clés
- Retraiter docs à contenu court

---

## 📋 Ordre de Priorité des Matières

Triées par nombre de docs sans fiche (descendant):

| Rang | Matière | Sans fiche | < 5 FC | Contenu court | Priorité |
|------|---------|-----------|--------|---------------|----------|
| 1 | **Licence 2 - Semestre 3** | 137 | 77 | 54 | 🔴 CRITIQUE |
| 2 | **Droit public** | 133 | 81 | 51 | 🔴 CRITIQUE |
| 3 | **Licence 2 - Semestre 4** | 88 | 75 | 75 | 🔴 CRITIQUE |
| 4 | **Licence 3 - Semestre 5** | 59 | 30 | 30 | 🟡 HAUTE |
| 5 | **Licence 3 - Semestre 6** | 37 | 25 | 25 | 🟡 HAUTE |
| 6 | **Questions contemporaines** | 33 | 25 | 25 | 🟡 HAUTE |
| 7 | **Questions sociales** | 20 | 8 | 8 | 🟢 MOYENNE |
| 8-13 | Autres matieres (< 20 docs) | 92 | 89 | 44 | 🟢 MOYENNE |

---

## 🚀 Batches de Génération

### Batch Strategy

- **Taille par batch:** 10-15 docs (limiter rate-limit)
- **Délai inter-batch:** 2-3 heures (laisser quota reposer)
- **Commande base:** `python3 scripts/reextract_and_generate.py --matiere "..." --limit N --skip-extract --skip-flashcards`

### Batch 1A: L2S3 Partie 1 (Jour 1 matin)

```bash
# À lancer après 8:05 AM (quota reset)
python3 scripts/reextract_and_generate.py \
  --matiere "Licence 2 - Semestre 3" \
  --limit 15 \
  --skip-extract \
  --skip-flashcards \
  2>&1 | tee tasks/pdf-pipeline-refonte/batch-l2s3-1.log
```

**Target:** ~10-15 fiches OK (si quota permet)
**Estim. duration:** 2-3 heures
**Success criteria:** ≥ 10/15 fiches OK (67%)

---

### Batch 1B: L2S3 Partie 2 (Jour 1 après-midi)

```bash
# À lancer après Batch 1A terminé + 3h repos
python3 scripts/reextract_and_generate.py \
  --matiere "Licence 2 - Semestre 3" \
  --limit 15 \
  --skip-extract \
  --skip-flashcards \
  --min-flashcards 0 \
  2>&1 | tee tasks/pdf-pipeline-refonte/batch-l2s3-2.log
```

**Cible:** Couvrir documents 151-166 de L2S3
**Note:** Option `--min-flashcards 0` pour éviter sauter les 137 docs

---

### Batch 2A: Droit Public Partie 1 (Jour 2 matin)

```bash
# Lendemain matin après reset quota
python3 scripts/reextract_and_generate.py \
  --matiere "Droit public" \
  --limit 15 \
  --skip-extract \
  --skip-flashcards \
  2>&1 | tee tasks/pdf-pipeline-refonte/batch-dp-1.log
```

**Target:** ~10-15 fiches OK
**Estim. duration:** 2-3 heures

---

### Batch 2B: Droit Public Partie 2 (Jour 2 après-midi)

```bash
# À lancer après Batch 2A terminé + 3h repos
python3 scripts/reextract_and_generate.py \
  --matiere "Droit public" \
  --limit 15 \
  --skip-extract \
  --skip-flashcards \
  --min-flashcards 0 \
  2>&1 | tee tasks/pdf-pipeline-refonte/batch-dp-2.log
```

---

### Batch 3A: L2S4 Partie 1 (Jour 3 matin)

```bash
python3 scripts/reextract_and_generate.py \
  --matiere "Licence 2 - Semestre 4" \
  --limit 15 \
  --skip-extract \
  --skip-flashcards \
  2>&1 | tee tasks/pdf-pipeline-refonte/batch-l2s4-1.log
```

---

### Batch 3B: L2S4 Partie 2 (Jour 3 après-midi)

```bash
python3 scripts/reextract_and_generate.py \
  --matiere "Licence 2 - Semestre 4" \
  --limit 15 \
  --skip-extract \
  --skip-flashcards \
  --min-flashcards 0 \
  2>&1 | tee tasks/pdf-pipeline-refonte/batch-l2s4-2.log
```

---

### Batches Suivants (Jour 4+)

Si quota et throughput permettent:

#### Batch 4A: L3S5 Partie 1
```bash
python3 scripts/reextract_and_generate.py \
  --matiere "Licence 3 - Semestre 5" \
  --limit 15 \
  --skip-extract \
  --skip-flashcards \
  2>&1 | tee tasks/pdf-pipeline-refonte/batch-l3s5-1.log
```

#### Batch 4B: L3S5 Partie 2
```bash
python3 scripts/reextract_and_generate.py \
  --matiere "Licence 3 - Semestre 5" \
  --limit 15 \
  --skip-extract \
  --skip-flashcards \
  --min-flashcards 0 \
  2>&1 | tee tasks/pdf-pipeline-refonte/batch-l3s5-2.log
```

#### Batch 5A: L3S6 + Questions Contemporaines (petit batch)
```bash
python3 scripts/reextract_and_generate.py \
  --matiere "Licence 3 - Semestre 6" \
  --limit 20 \
  --skip-extract \
  --skip-flashcards \
  2>&1 | tee tasks/pdf-pipeline-refonte/batch-l3s6-qc.log
```

---

## 📅 Calendrier Proposé

```
JOUR 1 (2026-03-25):
  08:05 - Batch 1A (L2S3 p1) → 2-3h
  11:30 - Repos + monitoring
  14:30 - Batch 1B (L2S3 p2) → 2-3h
  17:30 - Repos

JOUR 2 (2026-03-26):
  08:05 - Batch 2A (DP p1) → 2-3h
  11:30 - Repos
  14:30 - Batch 2B (DP p2) → 2-3h

JOUR 3 (2026-03-27):
  08:05 - Batch 3A (L2S4 p1) → 2-3h
  14:30 - Batch 3B (L2S4 p2) → 2-3h

JOUR 4+ (2026-03-28+):
  Batches 4-5 si quota + throughput permettent
```

---

## ⚠️ Risques & Mitigations

| Risque | Mitigation |
|--------|-----------|
| **Quota Claude s'épuise** | Batches de 10-15 docs, délai inter-batch |
| **Rate-limit 429 temporaires** | Retry logic activé (30s/60s backoff) |
| **Docs avec contenu vide** | Audit L2S3 identifié 46 docs vides; filter pendant génération |
| **Pas de fallback Gemini** | Implémenter après cette vague si possible |
| **Flashcards oubliées** | Phase 2 dédiée aux flashcards après fiches |

---

## 🔍 Monitoring Pendant Exécution

Pour chaque batch, vérifier:

1. **Pendant l'exécution (tail logs)**
   ```bash
   tail -f tasks/pdf-pipeline-refonte/batch-*.log
   ```

2. **Chercher les patterns**
   - ✅ Lignes "OK — fiche_id=..." = succès
   - ⚠️ Lignes "WARNING Claude CLI error (attempt N/3)" = retry en cours
   - ❌ Lignes "ERROR [fiche]" = doc échoué

3. **Interrompre si**
   - Plus de 8 erreurs consécutives (signe que quota épuisé)
   - Erreurs autres que "You've hit your limit" (signe bug)

---

## 📊 Metrics à Tracker

Après chaque batch, noter:
- Nombre de fiches générées (OK)
- Nombre d'erreurs
- Taux d'acceptation (OK / total)
- Heure de début/fin

Exemple log:
```
Batch 1A (L2S3 p1): 12/15 OK, 3 error (rate-limit), durée 2h45, success 80%
Batch 1B (L2S3 p2): 9/15 OK, 6 error (rate-limit), durée 2h20, success 60%
```

---

## 🎯 Success Criteria

**Pour cette session:**
- ✅ Générer ≥ 50 fiches L2S3 (de 137 actuels)
- ✅ Générer ≥ 50 fiches Droit public (de 133 actuels)
- ✅ Générer ≥ 30 fiches L2S4 (de 88 actuels)
- ✅ **Zéro crash / corruption de données**
- ✅ **100% des logs sauvegardés** pour post-mortem

---

## 🔧 Prérequis Avant de Commencer

- [x] Fix rate-limit appliqué et testé (validé Batch QC)
- [x] Audit L2S3 identifié 46 docs vides (filter pendant génération)
- [x] Commandes préparées (ci-dessus)
- [x] Répertoire logs créé et accessible
- [ ] Backend démarré sur port 8000
- [ ] Vérifier quota Claude reset à 8am (message logs)

---

## 📝 Notes Opérationnelles

- Chaque batch est **indépendant** — peut être lancé en // si ressources permettent
- Les **logs sont cumulatifs** (voir "tail" les fichiers pour monitoring live)
- **Pas de --dry-run** — les fiches sont écrites en DB
- Utiliser **screen** ou **tmux** si execution longue (résiste aux disconnections)

---

**Préparé par:** T-052 Generation Plan
**Date:** 2026-03-25 04:30 CET
**Status:** ✅ PRÊT À LANCER

Attendre reset quota 08:00 AM, puis lancer Batch 1A.
