# Déduplication DB — 2026-03-28

## Commandes exécutées

### 1. Contrôle avant exécution

```bash
python3 - <<'PY'
import sqlite3
conn = sqlite3.connect('data/iaca.db')
queries = {
    'documents_before': 'SELECT COUNT(*) FROM documents',
    'duplicate_docs_scope_before': "WITH g AS (SELECT COUNT(*) c FROM documents WHERE contenu_extrait IS NOT NULL AND length(trim(contenu_extrait)) >= 1000 GROUP BY contenu_extrait HAVING COUNT(*)>1) SELECT COALESCE(SUM(c-1),0) FROM g",
}
for name, sql in queries.items():
    print(name, conn.execute(sql).fetchone()[0])
conn.close()
PY
```

Résultat :

```text
documents_before 1300
duplicate_docs_scope_before 0
```

### 2. Dry-run

```bash
python3 scripts/dedup_documents.py --dry-run
```

Résultat :

```text
Mode                 : DRY-RUN
Min content length   : 1000
Duplicate groups     : 0
Documents a supprimer: 0
Fiches a transferer  : 0
Flashcards a transferer: 0
Quizzes a transferer : 0
Suppression executee : 0
Aucun groupe duplique detecte.
```

### 3. Exécution réelle

```bash
python3 scripts/dedup_documents.py --apply
```

Résultat :

```text
Mode                 : APPLY
Min content length   : 1000
Duplicate groups     : 0
Documents a supprimer: 0
Fiches a transferer  : 0
Flashcards a transferer: 0
Quizzes a transferer : 0
Suppression executee : 0
Aucun groupe duplique detecte.
```

### 4. Vérification finale

```bash
python3 - <<'PY'
import sqlite3
conn = sqlite3.connect('data/iaca.db')
print('documents_after', conn.execute('SELECT COUNT(*) FROM documents').fetchone()[0])
print('duplicate_docs_scope_after', conn.execute("WITH g AS (SELECT COUNT(*) c FROM documents WHERE contenu_extrait IS NOT NULL AND length(trim(contenu_extrait)) >= 1000 GROUP BY contenu_extrait HAVING COUNT(*)>1) SELECT COALESCE(SUM(c-1),0) FROM g").fetchone()[0])
conn.close()
PY
```

Résultat :

```text
documents_after 1300
duplicate_docs_scope_after 0
```

## Conclusion

- La déduplication ciblée par `scripts/dedup_documents.py` avait déjà été appliquée avant cette exécution.
- Le run du `2026-03-28` est un **no-op vérifié**.
- `data/iaca.db` n'est pas versionné dans Git ; ce rapport sert de trace d'exécution.
