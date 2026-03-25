#!/usr/bin/env python3
"""Deduplicate documents by identical contenu_extrait.

Default mode is dry-run. Use --apply to execute updates and deletions.
"""

from __future__ import annotations

import argparse
import sqlite3
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = REPO_ROOT / "data" / "iaca.db"
DEFAULT_MIN_CONTENT_LENGTH = 1000


@dataclass
class DedupStats:
    group_count: int = 0
    duplicate_docs: int = 0
    transferred_fiches: int = 0
    transferred_flashcards: int = 0
    transferred_quizzes: int = 0
    deleted_docs: int = 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Deduplicate documents sharing the same contenu_extrait.",
    )
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the deduplication without writing to the database (default).",
    )
    mode_group.add_argument(
        "--apply",
        action="store_true",
        help="Apply document transfers and deletions.",
    )
    parser.add_argument(
        "--db-path",
        default=str(DEFAULT_DB_PATH),
        help=f"SQLite database path (default: {DEFAULT_DB_PATH})",
    )
    parser.add_argument(
        "--min-content-length",
        type=int,
        default=DEFAULT_MIN_CONTENT_LENGTH,
        help=(
            "Minimum trimmed contenu_extrait length to consider for deduplication "
            f"(default: {DEFAULT_MIN_CONTENT_LENGTH})."
        ),
    )
    parser.add_argument(
        "--sample-limit",
        type=int,
        default=5,
        help="How many duplicate groups to print in the preview (default: 5).",
    )
    return parser.parse_args()


def open_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def build_duplicate_map(conn: sqlite3.Connection, min_content_length: int) -> list[tuple[int, int]]:
    rows = conn.execute(
        """
        WITH grouped AS (
            SELECT contenu_extrait, MIN(id) AS keeper_id
            FROM documents
            WHERE contenu_extrait IS NOT NULL
              AND length(trim(contenu_extrait)) >= ?
            GROUP BY contenu_extrait
            HAVING COUNT(*) > 1
        )
        SELECT d.id AS duplicate_id, grouped.keeper_id
        FROM documents d
        JOIN grouped ON grouped.contenu_extrait = d.contenu_extrait
        WHERE d.id != grouped.keeper_id
        ORDER BY grouped.keeper_id, d.id
        """,
        (min_content_length,),
    ).fetchall()
    return [(int(row["duplicate_id"]), int(row["keeper_id"])) for row in rows]


def preview_groups(
    conn: sqlite3.Connection,
    min_content_length: int,
    sample_limit: int,
) -> list[sqlite3.Row]:
    return conn.execute(
        """
        WITH grouped AS (
            SELECT contenu_extrait, MIN(id) AS keeper_id, COUNT(*) AS doc_count
            FROM documents
            WHERE contenu_extrait IS NOT NULL
              AND length(trim(contenu_extrait)) >= ?
            GROUP BY contenu_extrait
            HAVING COUNT(*) > 1
        )
        SELECT
            keeper_id,
            doc_count,
            (
                SELECT group_concat(id, ', ')
                FROM documents d2
                WHERE d2.contenu_extrait = grouped.contenu_extrait
                ORDER BY id
            ) AS doc_ids,
            substr(replace(replace(contenu_extrait, char(10), ' '), char(13), ' '), 1, 90) AS preview
        FROM grouped
        ORDER BY doc_count DESC, keeper_id ASC
        LIMIT ?
        """,
        (min_content_length, sample_limit),
    ).fetchall()


def create_temp_map(conn: sqlite3.Connection, duplicate_map: list[tuple[int, int]]) -> None:
    conn.execute("DROP TABLE IF EXISTS temp.duplicate_map")
    conn.execute(
        """
        CREATE TEMP TABLE duplicate_map (
            duplicate_id INTEGER PRIMARY KEY,
            keeper_id INTEGER NOT NULL
        )
        """
    )
    conn.executemany(
        "INSERT INTO duplicate_map (duplicate_id, keeper_id) VALUES (?, ?)",
        duplicate_map,
    )


def count_transfer_candidates(conn: sqlite3.Connection) -> DedupStats:
    stats = DedupStats()
    stats.group_count = conn.execute(
        "SELECT COUNT(DISTINCT keeper_id) FROM duplicate_map"
    ).fetchone()[0]
    stats.duplicate_docs = conn.execute(
        "SELECT COUNT(*) FROM duplicate_map"
    ).fetchone()[0]
    stats.transferred_fiches = conn.execute(
        "SELECT COUNT(*) FROM fiches WHERE document_id IN (SELECT duplicate_id FROM duplicate_map)"
    ).fetchone()[0]
    stats.transferred_flashcards = conn.execute(
        "SELECT COUNT(*) FROM flashcards WHERE document_id IN (SELECT duplicate_id FROM duplicate_map)"
    ).fetchone()[0]
    stats.transferred_quizzes = conn.execute(
        "SELECT COUNT(*) FROM quizzes WHERE document_id IN (SELECT duplicate_id FROM duplicate_map)"
    ).fetchone()[0]
    return stats


def apply_dedup(conn: sqlite3.Connection, stats: DedupStats) -> None:
    conn.execute(
        """
        UPDATE fiches
        SET document_id = (
            SELECT keeper_id
            FROM duplicate_map
            WHERE duplicate_id = fiches.document_id
        )
        WHERE document_id IN (SELECT duplicate_id FROM duplicate_map)
        """
    )
    conn.execute(
        """
        UPDATE flashcards
        SET document_id = (
            SELECT keeper_id
            FROM duplicate_map
            WHERE duplicate_id = flashcards.document_id
        )
        WHERE document_id IN (SELECT duplicate_id FROM duplicate_map)
        """
    )
    conn.execute(
        """
        UPDATE quizzes
        SET document_id = (
            SELECT keeper_id
            FROM duplicate_map
            WHERE duplicate_id = quizzes.document_id
        )
        WHERE document_id IN (SELECT duplicate_id FROM duplicate_map)
        """
    )
    deleted = conn.execute(
        "DELETE FROM documents WHERE id IN (SELECT duplicate_id FROM duplicate_map)"
    ).rowcount
    stats.deleted_docs = max(deleted, 0)


def print_summary(stats: DedupStats, dry_run: bool, min_content_length: int) -> None:
    mode = "DRY-RUN" if dry_run else "APPLY"
    print(f"Mode                 : {mode}")
    print(f"Min content length   : {min_content_length}")
    print(f"Duplicate groups     : {stats.group_count}")
    print(f"Documents a supprimer: {stats.duplicate_docs}")
    print(f"Fiches a transferer  : {stats.transferred_fiches}")
    print(f"Flashcards a transferer: {stats.transferred_flashcards}")
    print(f"Quizzes a transferer : {stats.transferred_quizzes}")
    if dry_run:
        print("Suppression executee : 0")
    else:
        print(f"Suppression executee : {stats.deleted_docs}")


def print_preview(rows: list[sqlite3.Row]) -> None:
    if not rows:
        print("Aucun groupe duplique detecte.")
        return

    print("\nApercu des groupes dupliques:")
    for row in rows:
        print(
            f"- keeper={row['keeper_id']} total_docs={row['doc_count']} "
            f"ids=[{row['doc_ids']}] preview={row['preview']!r}"
        )


def main() -> int:
    args = parse_args()
    dry_run = not args.apply

    conn = open_db(args.db_path)
    try:
        duplicate_map = build_duplicate_map(conn, args.min_content_length)
        create_temp_map(conn, duplicate_map)
        stats = count_transfer_candidates(conn)
        samples = preview_groups(conn, args.min_content_length, args.sample_limit)

        print_summary(stats, dry_run=dry_run, min_content_length=args.min_content_length)
        print_preview(samples)

        if stats.duplicate_docs == 0:
            return 0

        if dry_run:
            print("\nDry-run termine. Aucune ecriture en base.")
            return 0

        conn.commit()
        conn.execute("BEGIN IMMEDIATE")
        apply_dedup(conn, stats)
        conn.commit()
        print("\nDeduplication appliquee avec succes.")
        print_summary(stats, dry_run=False, min_content_length=args.min_content_length)
        return 0
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
