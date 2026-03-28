#!/usr/bin/env python3
"""
fix_flashcards_quality.py — Nettoyage qualité des flashcards.

Actions :
  1. Supprime les doublons (même question, tous document_id) — garde la réponse la plus longue
  2. Supprime les flashcards avec réponse < 20 chars
  3. Supprime les flashcards test (question contient 'Test Q')

Usage :
  python3 scripts/fix_flashcards_quality.py           # dry-run (défaut)
  python3 scripts/fix_flashcards_quality.py --apply   # exécute les suppressions
"""

import argparse
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "iaca.db"


def find_duplicates(cur):
    """Retourne les IDs à supprimer pour les doublons (même question, tous document_id confondus).
    Garde la FC avec la réponse la plus longue ; en cas d'égalité, garde le plus grand ID."""
    cur.execute("""
        SELECT id FROM flashcards
        WHERE id NOT IN (
            SELECT id FROM (
                SELECT id,
                       ROW_NUMBER() OVER (
                           PARTITION BY question
                           ORDER BY LENGTH(reponse) DESC, id DESC
                       ) AS rn
                FROM flashcards
            ) ranked
            WHERE rn = 1
        )
    """)
    return [row[0] for row in cur.fetchall()]


def find_short_reponse(cur, min_len=20):
    """Retourne les IDs avec réponse trop courte."""
    cur.execute("SELECT id FROM flashcards WHERE LENGTH(reponse) < ?", (min_len,))
    return [row[0] for row in cur.fetchall()]


def find_test_flashcards(cur):
    """Retourne les IDs de flashcards test."""
    cur.execute("SELECT id FROM flashcards WHERE question LIKE '%Test Q%'")
    return [row[0] for row in cur.fetchall()]


def delete_ids(cur, ids, label):
    if not ids:
        return
    placeholders = ",".join("?" * len(ids))
    cur.execute(f"DELETE FROM flashcards WHERE id IN ({placeholders})", ids)


def main():
    parser = argparse.ArgumentParser(description="Nettoyage qualité flashcards")
    parser.add_argument("--apply", action="store_true",
                        help="Exécute les suppressions (défaut: dry-run)")
    parser.add_argument("--db", default=str(DB_PATH),
                        help="Chemin vers la base SQLite")
    args = parser.parse_args()

    dry_run = not args.apply

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM flashcards")
    total_before = cur.fetchone()[0]

    # --- Détection ---
    dup_ids     = find_duplicates(cur)
    short_ids   = find_short_reponse(cur)
    test_ids    = find_test_flashcards(cur)

    # Dédupliquer les ensembles (une FC peut être à la fois courte ET doublon)
    all_ids = set(dup_ids) | set(short_ids) | set(test_ids)

    print(f"{'[DRY-RUN] ' if dry_run else ''}Analyse — {total_before} flashcards en base")
    print(f"  Doublons à supprimer       : {len(dup_ids)}")
    print(f"  Réponse < 20 chars         : {len(short_ids)}")
    print(f"  Flashcards test ('Test Q') : {len(test_ids)}")
    print(f"  Total unique à supprimer   : {len(all_ids)}")
    print(f"  Reste après nettoyage      : {total_before - len(all_ids)}")

    if dry_run:
        print("\nMode dry-run — aucune suppression. Relancer avec --apply pour appliquer.")
        conn.close()
        sys.exit(0)

    # --- Application ---
    delete_ids(cur, list(all_ids), "all")
    conn.commit()

    cur.execute("SELECT COUNT(*) FROM flashcards")
    total_after = cur.fetchone()[0]
    conn.close()

    print(f"\nSupprimées : {total_before - total_after} flashcards")
    print(f"Restantes  : {total_after}")


if __name__ == "__main__":
    main()
