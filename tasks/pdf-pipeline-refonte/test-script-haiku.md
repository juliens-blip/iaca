# Test Script Review — test_new_prompts.py

**Date**: 2026-03-18
**Examinateur**: Haiku 4.5
**Fichier**: `scripts/test_new_prompts.py`
**Tests exécutés**: `--help` et `--dry-run --limit 1`

---

## Existence et aide

✅ **Fichier trouvé**: `scripts/test_new_prompts.py`

✅ **`--help` fonctionne**:
```
usage: test_new_prompts.py [-h] [--limit LIMIT] [--dry-run]

Test les nouveaux prompts Claude pour flashcards et fiches

options:
  -h, --help     show this help message and exit
  --limit LIMIT  Nombre de documents à tester (défaut: 1)
  --dry-run      Affiche juste le document choisi sans appeler Claude
```

---

## Exécution `--dry-run --limit 1`

### Commande
```bash
python3 scripts/test_new_prompts.py --dry-run --limit 1
```

### Résultat

✅ **Affichage du document**:
```
===========================================================================
Test 1/1 — Document 136
===========================================================================
Titre: Fiche 4 - Le service public - corrige
Matière: Droit public
Contenu: 12,249 chars

🔍 Mode dry-run: affichage du document uniquement

Aperçu du contenu (500 chars):
---------------------------------------------------------------------------
      1. Conseils généraux  Université Paris Panthéon-Assas  Année universitaire 2024-2025    Deuxième année de licence (parcours numérique) –  Droit administratif général    Séance n° 4 : Le service public    Pour des conseils généraux sur la méthodologie se référer à la fiche n° 3.    Le présent corrigé constitue une proposition de réponse au cas pratique. Il ne préjuge en rien de la qualité  des travaux rendus.    2. Proposition de corrigé du cas pratique    Un spectacle suscite la polémique ...
---------------------------------------------------------------------------
```

### Vérifications

| Élement | Affiche | Notes |
|---------|---------|-------|
| Document ID | ✅ Document 136 | Sélection aléatoire depuis DB |
| Titre | ✅ "Fiche 4 - Le service public - corrige" | Cohérent |
| Matière | ✅ "Droit public" | Via LEFT JOIN matieres |
| Contenu length | ✅ 12,249 chars | > 1000 chars (filtre script) |
| Aperçu 500 chars | ✅ Affiché avec ... | Preview lisible |
| Mode dry-run | ✅ Non-appel Claude | Comportement attendu |

---

## Analyse du code

**Flux**:
1. Parse `--limit` et `--dry-run` ✅
2. Connexion SQLite à `data/iaca.db` ✅
3. SELECT documents avec `contenu_extrait > 1000 chars` + `ORDER BY RANDOM()` ✅
4. LEFT JOIN matieres pour récupérer `matiere_nom` ✅
5. Affichage document en mode dry-run ✅
6. Appel optionnel `generer_flashcards()` et `generer_fiche()` (non testé, mode dry-run)

**Robustesse**:
- DB non trouvée → exit 1 ✅
- Aucun document trouvé → exit 1 ✅
- Import error (claude_service) → exit 1 ✅
- KeyboardInterrupt → exit 0 avec message ✅
- Exception → exit 1 avec message ✅

---

## Résumé

✅ **Script existe et fonctionne**
✅ **`--help` affiche les options correctement**
✅ **`--dry-run --limit 1` affiche un document complet**:
  - Document ID et titre
  - Matière correctement extraite
  - Contenu length
  - Aperçu 500 chars
✅ **Gestion erreurs robuste**
✅ **Interruptible (Ctrl+C)**

**Recommandation**: Script de test prêt à l'emploi. Dry-run fonctionne pour validation rapide avant appels Claude.
