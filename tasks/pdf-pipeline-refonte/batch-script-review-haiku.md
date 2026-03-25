# Batch Script Review — reextract_and_generate.py

**Date**: 2026-03-18
**Examinateur**: Haiku 4.5
**Scope**: Appels à `generer_flashcards()` et `generer_fiche()` dans le script batch
**Version**: Phase 1 extract + Phase 2 fiches + Phase 3 flashcards

---

## Phase 2 — Génération fiches (lignes 218-248)

### Appel (ligne 239)
```python
fiche_data = await claude_service.generer_fiche(contenu, matiere_nom, doc["titre"])
```

**Arguments**:
1. `contenu`: `doc["contenu_extrait"].strip()` (validé ≥120 chars, ligne 225)
2. `matiere_nom`: `doc["matiere_nom"] or "droit public"` (fallback sain)
3. `doc["titre"]`: Titre du document source

**Source de matière_nom**:
- SQL ligne 82: `m.nom AS matiere_nom` via LEFT JOIN matieres
- Fallback "droit public" si NULL (ligne 230) ✅

**Contenu passe par chunking**:
- Dans `generer_fiche()` (claude_service.py:514):
  - `source = _ensure_generation_source(contenu)` → sanitize + validate
  - `chunks = chunk_content(source, max_chars=4000)` (ligne 515) ✅
  - Boucle sur chunks et appel Claude par chunk

**Verdict**: ✅ Arguments corrects, matière extraite, contenu chunké.

---

## Phase 3 — Génération flashcards (lignes 251-284)

### Appel (ligne 276)
```python
cards = await claude_service.generer_flashcards(contenu, matiere_nom, nb=10)
```

**Arguments**:
1. `contenu`: `doc["contenu_extrait"].strip()` (validé ≥120 chars, ligne 258)
2. `matiere_nom`: `doc["matiere_nom"] or "droit public"` (fallback sain)
3. `nb=10`: Nombre de flashcards à générer

**Source de matière_nom**:
- SQL ligne 105: `m.nom AS matiere_nom` via LEFT JOIN matieres
- Fallback "droit public" si NULL (ligne 263) ✅
- Accès sécurisé: `doc["matiere_nom"] or "..."` pattern

**Contenu passe par chunking**:
- Dans `generer_flashcards()` (claude_service.py:378):
  - `source = _ensure_generation_source(contenu)` → sanitize + validate
  - `chunks = chunk_content(source, max_chars=4000)` (ligne 381) ✅
  - Boucle sur chunks avec `nb_per_chunk = max(5, nb // nb_chunks)` (ligne 386)
  - Fallback regeneration si < 50% cartes valides (ligne 438)

**Verdict**: ✅ Arguments corrects, matière extraite, contenu chunké.

---

## Requêtes SQL — Extraction matière_nom

### fetch_docs_without_fiche() (ligne 82)
```sql
SELECT ... m.nom AS matiere_nom
FROM documents d
LEFT JOIN matieres m ON m.id = d.matiere_id
```
✅ Jointure correcte, alias `matiere_nom` utilisable

### fetch_docs_with_few_flashcards() (ligne 105)
```sql
SELECT ... m.nom AS matiere_nom, COUNT(fc.id) AS nb_flashcards
FROM documents d
LEFT JOIN matieres m ON m.id = d.matiere_id
LEFT JOIN flashcards fc ON fc.document_id = d.id
```
✅ Jointure correcte, aggégation COUNT(fc.id) pour détection faible couverture

---

## Validation contenu avant appel

| Phase | Min chars | Check | Notes |
|-------|-----------|-------|-------|
| Fiches (ligne 225) | 120 | `len(contenu) < 120 → skip` | Avant appel generer_fiche |
| Flashcards (ligne 258) | 120 | `len(contenu) < 120 → skip` | Avant appel generer_flashcards |

✅ Validation cohérente avec `_ensure_generation_source()` (120 chars minimum)

---

## Fallback et robustesse

| Cas | Code | Comportement |
|-----|------|-----|
| `matiere_nom` NULL | ligne 230, 263 | Fallback "droit public" ✅ |
| Contenu < 120 | ligne 225, 258 | Log warning + skip ✅ |
| generer_fiche() exception | ligne 244 | Log error, continuer (stats["error"]) ✅ |
| generer_flashcards() exception | ligne 280 | Log error, continuer (stats["error"]) ✅ |
| Dry-run | ligne 233, 270 | Dès après check contenu, avant appel ✅ |

---

## Résumé

✅ **Appels cohérents**: Arguments passés dans le bon ordre et type
✅ **Matière extraite**: Via LEFT JOIN + fallback "droit public"
✅ **Contenu chunké**: Passe par `chunk_content(max_chars=4000)` dans les deux services
✅ **Validation pré-appel**: Minimum 120 chars avant Claude
✅ **Gestion erreurs**: Try/catch + log + stats + continue
✅ **SQL robuste**: LEFT JOIN bien formées, fallback cohérent
✅ **Dry-run**: Placé après validation, avant appel réel

**Recommandation**: Script batch prêt production. Pipeline validation correct.
