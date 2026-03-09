#!/usr/bin/env python3
"""Clean garbage fiches from IACA database.

Identifies and removes:
1. Quizlet link fiches
2. Student exam copies (7-digit ID + name pattern, or 'numérique en droit')
3. Exact-title duplicates (keeps the one with lowest id)

Usage:
    backend/.venv/bin/python scripts/clean_fiches.py --dry-run
    backend/.venv/bin/python scripts/clean_fiches.py
"""

import argparse
import os
import sqlite3
import re

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "iaca.db")


def get_garbage_ids(conn: sqlite3.Connection) -> dict[str, set[int]]:
    """Return sets of fiche IDs to delete, grouped by reason."""
    c = conn.cursor()

    reasons: dict[str, set[int]] = {
        "quizlet": set(),
        "student_exam": set(),
        "duplicate": set(),
    }

    # 1. Quizlet fiches (any case)
    c.execute(
        "SELECT id, titre FROM fiches "
        "WHERE LOWER(titre) LIKE '%quizlet%' OR LOWER(titre) LIKE '%quizzlet%'"
    )
    for row in c.fetchall():
        reasons["quizlet"].add(row[0])

    # 2. Student exam copies:
    #    a) 7+ digit student ID followed by underscore
    #    b) 'numérique en droit' (case-insensitive)
    c.execute(
        "SELECT id, titre FROM fiches "
        "WHERE titre GLOB '*[0-9][0-9][0-9][0-9][0-9][0-9][0-9]_*'"
    )
    for row in c.fetchall():
        reasons["student_exam"].add(row[0])

    c.execute(
        "SELECT id, titre FROM fiches "
        "WHERE LOWER(titre) LIKE '%numérique en droit%' "
        "OR LOWER(REPLACE(titre, 'é', 'e')) LIKE '%numerique en droit%'"
    )
    for row in c.fetchall():
        reasons["student_exam"].add(row[0])

    # 3. Exact-title duplicates: keep lowest id per title, delete the rest
    c.execute(
        "SELECT id, titre FROM fiches ORDER BY id"
    )
    seen: dict[str, int] = {}
    for fid, titre in c.fetchall():
        if titre in seen:
            reasons["duplicate"].add(fid)
        else:
            seen[titre] = fid

    return reasons


def main():
    parser = argparse.ArgumentParser(description="Clean garbage fiches from IACA DB")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, no deletion")
    args = parser.parse_args()

    db_path = os.path.abspath(DB_PATH)
    if not os.path.exists(db_path):
        print(f"ERROR: DB not found at {db_path}")
        return 1

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM fiches")
    total_before = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM fiche_sections")
    sections_before = c.fetchone()[0]

    reasons = get_garbage_ids(conn)

    # Merge all IDs (some may overlap across categories)
    all_ids = set()
    for ids in reasons.values():
        all_ids |= ids

    print(f"=== {'DRY RUN' if args.dry_run else 'LIVE RUN'} ===")
    print(f"Total fiches before: {total_before}")
    print(f"Total fiche_sections before: {sections_before}")
    print()
    print(f"Garbage by category (may overlap):")
    for reason, ids in sorted(reasons.items()):
        print(f"  {reason}: {len(ids)}")
    print(f"  TOTAL unique to delete: {len(all_ids)}")
    print(f"  Will remain: {total_before - len(all_ids)}")
    print()

    if args.dry_run:
        # Show samples per category
        for reason, ids in sorted(reasons.items()):
            if ids:
                sample_ids = sorted(ids)[:5]
                placeholders = ",".join("?" * len(sample_ids))
                c.execute(f"SELECT id, titre FROM fiches WHERE id IN ({placeholders})", sample_ids)
                print(f"  Sample {reason}:")
                for row in c.fetchall():
                    print(f"    [{row[0]}] {row[1][:100]}")
                if len(ids) > 5:
                    print(f"    ... and {len(ids) - 5} more")
                print()
        print("No changes made (dry run).")
        return 0

    # Delete sections first, then fiches
    id_list = list(all_ids)
    batch_size = 500
    sections_deleted = 0
    fiches_deleted = 0

    for i in range(0, len(id_list), batch_size):
        batch = id_list[i:i + batch_size]
        placeholders = ",".join("?" * len(batch))

        c.execute(f"DELETE FROM fiche_sections WHERE fiche_id IN ({placeholders})", batch)
        sections_deleted += c.rowcount

        c.execute(f"DELETE FROM fiches WHERE id IN ({placeholders})", batch)
        fiches_deleted += c.rowcount

    conn.commit()

    c.execute("SELECT COUNT(*) FROM fiches")
    total_after = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM fiche_sections")
    sections_after = c.fetchone()[0]

    print(f"Deleted {fiches_deleted} fiches, {sections_deleted} fiche_sections")
    print(f"Fiches remaining: {total_after}")
    print(f"Fiche_sections remaining: {sections_after}")
    print("Done.")
    return 0


if __name__ == "__main__":
    exit(main())
