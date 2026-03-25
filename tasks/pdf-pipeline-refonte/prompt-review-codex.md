# Prompt Review — generer_fiche / claude_service.py

**Date:** 2026-03-18  
**Fichier:** `backend/app/services/claude_service.py`  
**Lignes analysées:** 522–577 (prompt `generer_fiche`)

---

## 1. Vérification syntaxe JSON attendue dans le prompt

Le JSON attendu dans le prompt (lignes 566–575) est :

```json
{
  "resume_partiel": "...",
  "sections": [
    {
      "titre": "...",
      "contenu": "..."
    }
  ]
}
```

**Résultat : ✅ JSON syntaxiquement correct.**

- Les accolades sont équilibrées.
- Les clés sont entre guillemets doubles.
- Le tableau `sections` contient un objet avec deux clés string (`titre`, `contenu`).
- Pas de virgule traînante, pas de commentaire interdit en JSON.
- Dans le f-string Python, les accolades littérales sont correctement doublées (`{{`, `}}`), ce qui produira `{`, `}` dans le prompt effectif.

---

## 2. Observations sur le prompt

### Points positifs
- Instructions détaillées en 4 sous-points (TITRE, CONTENU a/b/c/d, RESUME PARTIEL, REGLES ABSOLUES).
- Exemples concrets de bons/mauvais titres.
- Interdiction explicite du copier-coller.
- Contrainte de volume (200-350 mots, 2-4 sections).

### Point d'attention (non bloquant)
- Le prompt indique "Reponds UNIQUEMENT en JSON valide (pas de markdown, pas de texte autour)" mais utilise des indentations avec espaces dans le JSON exemple — comportement attendu de Claude, aucun impact sur le parsing car `_extract_json_object` gère cela.

---

## 3. Résultat compileall

```
$ python3 -m compileall backend/app
```

**Exit code : 0 — aucune erreur.**

Tous les modules compilés sans avertissement :
- `backend/app/services/claude_service.py` ✅
- `backend/app/services/marker_parser.py` ✅
- `backend/app/services/document_parser.py` ✅
- `backend/app/routers/documents.py` ✅
- `backend/app/models/`, `backend/app/schemas/`, `backend/app/middleware/` ✅

---

**Conclusion : prompt correct, compilation OK, rien à corriger.**
