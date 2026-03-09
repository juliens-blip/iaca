#!/usr/bin/env python3
"""Déduplique les documents en DB par (titre, matiere_id), garde le MIN(id)."""
import sqlite3

DB_PATH = "/home/julien/Documents/IACA/data/iaca.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Avant
total_before = cur.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
print(f"Documents avant : {total_before}")

# IDs à garder : MIN(id) par (titre, matiere_id)
cur.execute("""
    SELECT MIN(id) FROM documents
    GROUP BY titre, matiere_id
""")
keep_ids = {r[0] for r in cur.fetchall()}
print(f"Docs à conserver : {len(keep_ids)}")

# Réaffecter les flashcards/quizzes qui pointent vers des doublons → vers le keeper
cur.execute("""
    SELECT id, document_id FROM flashcards WHERE document_id IS NOT NULL
""")
flashcards = cur.fetchall()
reassigned_fc = 0
for fc_id, doc_id in flashcards:
    if doc_id not in keep_ids:
        # Trouver le keeper pour ce document
        cur.execute("SELECT titre, matiere_id FROM documents WHERE id=?", (doc_id,))
        row = cur.fetchone()
        if row:
            cur.execute("SELECT MIN(id) FROM documents WHERE titre=? AND matiere_id IS ?", row)
            keeper = cur.fetchone()[0]
            if keeper:
                cur.execute("UPDATE flashcards SET document_id=? WHERE id=?", (keeper, fc_id))
                reassigned_fc += 1

cur.execute("""
    SELECT id, document_id FROM quizzes WHERE document_id IS NOT NULL
""")
quizzes = cur.fetchall()
reassigned_qz = 0
for qz_id, doc_id in quizzes:
    if doc_id not in keep_ids:
        cur.execute("SELECT titre, matiere_id FROM documents WHERE id=?", (doc_id,))
        row = cur.fetchone()
        if row:
            cur.execute("SELECT MIN(id) FROM documents WHERE titre=? AND matiere_id IS ?", row)
            keeper = cur.fetchone()[0]
            if keeper:
                cur.execute("UPDATE quizzes SET document_id=? WHERE id=?", (keeper, qz_id))
                reassigned_qz += 1

print(f"Flashcards réassignées : {reassigned_fc}")
print(f"Quizzes réassignées    : {reassigned_qz}")

# Supprimer les doublons
placeholders = ",".join("?" * len(keep_ids))
cur.execute(f"DELETE FROM documents WHERE id NOT IN ({placeholders})", list(keep_ids))
deleted = cur.rowcount
conn.commit()

# Après
total_after = cur.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
print(f"\nSupprimés  : {deleted}")
print(f"Documents après : {total_after}")

# Vérifier orphelins
orphan_fc = cur.execute("""
    SELECT COUNT(*) FROM flashcards f
    WHERE f.document_id IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM documents d WHERE d.id = f.document_id)
""").fetchone()[0]
orphan_qz = cur.execute("""
    SELECT COUNT(*) FROM quizzes q
    WHERE q.document_id IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM documents d WHERE d.id = q.document_id)
""").fetchone()[0]
print(f"Flashcards orphelines : {orphan_fc}")
print(f"Quizzes orphelins     : {orphan_qz}")

conn.close()
print("\n✅ Déduplication terminée.")
