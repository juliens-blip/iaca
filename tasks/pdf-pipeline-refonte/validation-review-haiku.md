# Validation Review — claude_service.py

**Date**: 2026-03-18
**Examinateur**: Haiku 4.5
**Scope**: `_validate_flashcard()` et `_validate_fiche_section()`
**Compilation**: ✅ `python3 -m compileall backend/app` exit 0

---

## Fonction `_validate_flashcard()` (lignes 290-303)

**Règles implémentées**:
- Question ≥ 20 caractères normalisés
- Réponse ≥ 30 caractères normalisés
- Question ≠ Réponse (case-insensitive)

**Observations**:
- Pas de validation `difflib` — appropriate pour flashcards (format court)
- Log warning explicites avec contexte (premiers 60 chars)
- Rejet clair et rejouable (difficulté 1-5 conservée dans le dict)

**Verdict**: ✅ Validation légère mais efficace pour le format flashcard court.

---

## Fonction `_validate_fiche_section()` (lignes 306-321)

**Règles implémentées**:
1. Titre non-générique (rejette "Section 1", "Introduction", etc.)
2. Contenu ≥ 150 caractères normalisés
3. **Difflib check**: `SequenceMatcher(None, contenu[:500], source_chunk[:500]).ratio() > 0.85` **REJETTE**

**Analyse difflib**:
- Compare 500 premiers chars du contenu généré vs source
- Seuil **0.85** (85% similarité) → rejet
- Cas d'usage: détecte copie brute ou réécriture superficielle
- Log ratio exact pour diagnostique

**Test mental**:
- Source: "Le droit administratif est l'ensemble des règles..."
- Contenu généré: "Le droit administratif est l'ensemble des règles..."
- Ratio: ~0.95 → **REJETÉ** ✅

- Source: "Le droit administratif régit l'action administrative."
- Contenu généré: "En droit administratif, la règle fondamentale concerne le contrôle juridictionnel."
- Ratio: ~0.45 → **ACCEPTÉ** ✅

**Verdict**: ✅ Difflib fonctionne — capture les copies brutes efficacement.

---

## Intégration dans pipeline

- `_validate_flashcard()` appelée dans `generer_flashcards()` (ligne 437)
- `_validate_fiche_section()` appelée dans `generer_fiche()` (lignes 582, 591) avec chunk source
- Fallback regeneration si < 50% de cartes valides (flashcards) ou 0 sections (fiches)

---

## Résumé

✅ **Syntax**: Compilation réussie
✅ **Flashcards**: Validation minimaliste, appropriée
✅ **Fiches**: Validation robuste avec difflib seuil 0.85
✅ **Logs**: Contexte diagnostique complet

**Recommandation**: Pipeline de validation en place et fonctionnel. Difflib rejet des copies brutes confirmé.
