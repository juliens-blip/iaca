# Revue d'Intégration — Batch Script reextract_and_generate.py

**Date:** 2026-03-18
**Fichier:** `scripts/reextract_and_generate.py`
**Scope:** Phase 2 (génération fiches) et Phase 3 (génération flashcards)

---

## 📋 Résumé Exécutif

✅ **INTÉGRATION CORRECTE** — Le script batch appelle les bonnes fonctions avec les bons arguments, extrait correctement la matière depuis la DB, et laisse le chunking à faire par `generer_fiche()` et `generer_flashcards()`.

---

## 1️⃣ Phase 2 — Génération Fiches (L.218-248)

### Appel de Fonction

```python
# L.239
fiche_data = await claude_service.generer_fiche(contenu, matiere_nom, doc["titre"])
```

### Arguments Passés

| Paramètre | Valeur | Type | Source | Validation |
|-----------|--------|------|--------|-----------|
| `contenu` | `doc["contenu_extrait"]` | str | Document DB | >= 120 chars (L.225) |
| `matiere_nom` | `doc["matiere_nom"]` | str | JOIN matieres | Fallback: "droit public" (L.230) |
| `titre_doc` | `doc["titre"]` | str | Document DB | Utilisé pour contexte fiche |

### ✅ Validations

1. **Contenu suffisant:**
   ```python
   # L.224-228
   contenu = (doc["contenu_extrait"] or "").strip()
   if len(contenu) < 120:
       log.warning("[fiche] [%d] contenu insuffisant (%d chars) — sauté")
       stats["skipped"] += 1
       continue
   ```
   ✅ Vérifie >= 120 chars avant appel

2. **Matière extraite correctement:**
   ```python
   # L.220, 230
   SELECT d.id, d.titre, ... d.matiere_id, m.nom AS matiere_nom
   FROM documents d
   LEFT JOIN matieres m ON m.id = d.matiere_id
   ...
   matiere_nom = doc["matiere_nom"] or "droit public"
   ```
   ✅ JOIN avec matieres, fallback défini

3. **Chunking délégué:**
   - ✅ `generer_fiche()` appelle `chunk_content(source, max_chars=4000)` en interne
   - ✅ Boucle sur les chunks pour générer sections partielles
   - ✅ Assemble les sections finales

### Sauvegarde en DB

```python
# L.240
fiche_id = save_fiche(conn, doc["id"], doc["matiere_id"], fiche_data)
```

**Fonction save_fiche (L.136-157):**
```python
def save_fiche(conn, doc_id, matiere_id, fiche_data):
    # Insert INTO fiches (titre, resume, document_id, matiere_id, tags)
    # Insert INTO fiche_sections pour chaque section (fiche_id, titre, contenu, ordre)
    # Filtre sections < 40 chars
```
✅ Structure correcte, filtrage des sections trop courtes

---

## 2️⃣ Phase 3 — Génération Flashcards (L.251-284)

### Appel de Fonction

```python
# L.276
cards = await claude_service.generer_flashcards(contenu, matiere_nom, nb=10)
```

### Arguments Passés

| Paramètre | Valeur | Type | Source | Validation |
|-----------|--------|------|--------|-----------|
| `contenu` | `doc["contenu_extrait"]` | str | Document DB | >= 120 chars (L.258) |
| `matiere` | `doc["matiere_nom"]` | str | JOIN matieres | Fallback: "droit public" (L.263) |
| `nb` | `10` | int | Hardcodé | Nombre de flashcards demandé |

### ✅ Validations

1. **Contenu suffisant:**
   ```python
   # L.257-261
   contenu = (doc["contenu_extrait"] or "").strip()
   if len(contenu) < 120:
       log.warning("[flashcard] [%d] contenu insuffisant (%d chars) — sauté")
       stats["skipped"] += 1
       continue
   ```
   ✅ Vérifie >= 120 chars avant appel

2. **Matière extraite correctement:**
   ```python
   # L.252-253, 263
   SELECT d.id, d.titre, ... d.matiere_id, m.nom AS matiere_nom
   FROM documents d
   LEFT JOIN matieres m ON m.id = d.matiere_id
   ...
   matiere_nom = doc["matiere_nom"] or "droit public"
   ```
   ✅ JOIN avec matieres, fallback défini

3. **Chunking délégué:**
   - ✅ `generer_flashcards()` appelle `chunk_content(source, max_chars=4000)` en interne
   - ✅ Génère `nb_per_chunk = max(2, nb // nb_chunks)` cartes par chunk
   - ✅ Valide avec `_validate_flashcard()` et régénère si < 50% valides

### Sauvegarde en DB

```python
# L.277
saved = save_flashcards(conn, doc["id"], doc["matiere_id"], cards)
```

**Fonction save_flashcards (L.160-177):**
```python
def save_flashcards(conn, doc_id, matiere_id, cards):
    # Insert INTO flashcards (question, reponse, explication, difficulte, document_id, matiere_id)
    # pour chaque flashcard
```
✅ Structure correcte, tous les champs sauvegardés

---

## 3️⃣ Flux Complet de Chunking

```
Batch Script (contenu brut)
        ↓
generer_fiche(contenu, matiere, titre)
        ↓
        ├─→ chunk_content(contenu, max_chars=4000)
        ├─→ pour chaque chunk: appel Claude
        ├─→ génération sections partielles
        └─→ assembly des sections finales
        ↓
save_fiche(conn, doc_id, matiere_id, fiche_data)
        ↓
INSERT INTO fiches + fiche_sections
```

✅ **Chunking bien isolé dans generer_fiche()**
✅ **Le batch ne fait QUE passer le contenu brut**
✅ **Délégation correcte des responsabilités**

---

## 4️⃣ Extraction de la Matière

### Requête Phase 2

```sql
-- L.80-88
SELECT d.id, d.titre, d.fichier_path, d.type_fichier, d.contenu_extrait, d.matiere_id,
       m.nom AS matiere_nom
FROM documents d
LEFT JOIN matieres m ON m.id = d.matiere_id
WHERE d.contenu_extrait IS NOT NULL
  AND length(trim(d.contenu_extrait)) >= 120
  AND NOT EXISTS (SELECT 1 FROM fiches f WHERE f.document_id = d.id)
```

✅ **LEFT JOIN matieres:** Récupère le nom de matière
✅ **Alias:** `m.nom AS matiere_nom`
✅ **Accessible dans le code:** `doc["matiere_nom"]`

### Requête Phase 3

```sql
-- L.100-118 (similaire)
SELECT d.id, d.titre, ..., m.nom AS matiere_nom
FROM documents d
LEFT JOIN matieres m ON m.id = d.matiere_id
WHERE ...
```

✅ **Même jointure, même alias**
✅ **Cohérent avec Phase 2**

### Fallback

```python
# L.230, 263
matiere_nom = doc["matiere_nom"] or "droit public"
```

✅ **Fallback défini** si matière NULL (LEFT JOIN)

---

## 5️⃣ Points Vérifiés ✅

| Aspect | Vérification | Résultat |
|--------|-------------|----------|
| **Phase 2 - Appel fonction** | `generer_fiche(contenu, matiere_nom, doc["titre"])` | ✅ Correct |
| **Phase 2 - Arguments** | Types et sources validés | ✅ OK |
| **Phase 2 - Chunking** | Délégué à `generer_fiche()` | ✅ OK |
| **Phase 2 - Sauvegarde** | `save_fiche()` structure correcte | ✅ OK |
| **Phase 3 - Appel fonction** | `generer_flashcards(contenu, matiere_nom, nb=10)` | ✅ Correct |
| **Phase 3 - Arguments** | Types et sources validés | ✅ OK |
| **Phase 3 - Chunking** | Délégué à `generer_flashcards()` | ✅ OK |
| **Phase 3 - Sauvegarde** | `save_flashcards()` structure correcte | ✅ OK |
| **Matière - Phase 2** | LEFT JOIN + fallback | ✅ OK |
| **Matière - Phase 3** | LEFT JOIN + fallback | ✅ OK |
| **Validation contenu** | >= 120 chars avant appel | ✅ OK |
| **Dry-run** | Skip appels Claude en mode dry | ✅ OK |

---

## 6️⃣ Diagramme d'Intégration

```
┌─────────────────────────────────────────────────┐
│     reextract_and_generate.py (Batch)           │
├─────────────────────────────────────────────────┤
│ Récupère documents de DB                        │
│   - contenu_extrait                             │
│   - matiere_nom (via JOIN)                      │
│   - titre                                       │
└──────────────┬──────────────────────────────────┘
               │
       ┌───────┴────────┐
       │                │
       ↓                ↓
┌─────────────────┐  ┌──────────────────────┐
│ Phase 2: Fiches │  │ Phase 3: Flashcards  │
├─────────────────┤  ├──────────────────────┤
│ generer_fiche() │  │generer_flashcards()  │
│   ├─chunk()     │  │   ├─chunk()          │
│   ├─Claude      │  │   ├─Claude per chunk │
│   └─assembly    │  │   └─validate         │
└────────┬────────┘  └──────────┬───────────┘
         │                      │
         ↓                      ↓
   save_fiche()         save_flashcards()
         │                      │
         └───────┬──────────────┘
                 ↓
          INSERT INTO DB
              ✅ Done
```

---

## 7️⃣ Recommandations Mineures

| Point | Observation | Importance |
|-------|-------------|-----------|
| nb=10 flashcards | Hardcodé — considérer le rendre configurable? | Basse |
| Logs débug | Suffisants pour suivi production | N/A |
| Erreur handling | Try-except pour chaque appel — bon | N/A |
| Matière fallback | "droit public" — approprié | N/A |

---

## 🎯 Conclusion

✅ **VALIDATION COMPLÈTE** — Le script d'intégration batch est correctement implémenté:

1. **Phase 2 (Fiches):** Appelle `generer_fiche()` avec les bons arguments
2. **Phase 3 (Flashcards):** Appelle `generer_flashcards()` avec les bons arguments
3. **Chunking:** Correctement délégué aux fonctions de génération
4. **Matière:** Extraite correctement via LEFT JOIN + fallback
5. **Sauvegarde:** Fonctions `save_fiche()` et `save_flashcards()` structures correctes
6. **Validation:** Contenu >= 120 chars, fallbacks définis, dry-run fonctionnel

**Prêt pour exécution batch sur 150 PDFs manquants et régénération fiches/flashcards.**

---

## 📊 Intégration API

```python
# claude_service.py
async def generer_fiche(contenu: str, matiere: str, titre_doc: str) -> dict:
    # Chunking en interne
    # Retourne: {titre, resume, sections: [{titre, contenu}, ...]}

async def generer_flashcards(contenu: str, matiere: str, nb: int) -> list[dict]:
    # Chunking en interne
    # Retourne: [{question, reponse, explication, difficulte}, ...]
```

✅ **Contrat API respecté** — Batch et services alignés
