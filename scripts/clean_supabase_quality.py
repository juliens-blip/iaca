#!/usr/bin/env python3
"""Remove Supabase fiches/flashcards that fail the current quality validators."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

import asyncpg

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"

sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(REPO_ROOT))

from app.services.claude_service import _validate_fiche_payload, _validate_flashcard
from scripts.generate_supabase_quality_coverage import (
    DATABASE,
    HOST,
    PASSWORD,
    PORT,
    USER,
    connect_ssl_context,
)

logging.getLogger("app.services.claude_service").setLevel(logging.ERROR)


async def invalid_flashcard_ids(conn: asyncpg.Connection) -> list[int]:
    rows = await conn.fetch(
        "select id, document_id, question, reponse, explication, difficulte from public.flashcards order by id"
    )
    return [int(row["id"]) for row in rows if not _validate_flashcard(dict(row))]


async def invalid_fiche_ids(conn: asyncpg.Connection) -> list[int]:
    fiches = await conn.fetch("select id, document_id, titre, resume from public.fiches order by id")
    sections = await conn.fetch(
        "select fiche_id, titre, contenu from public.fiche_sections order by fiche_id, ordre, id"
    )
    by_fiche: dict[int, list[dict]] = {}
    for section in sections:
        by_fiche.setdefault(int(section["fiche_id"]), []).append(
            {"titre": section["titre"] or "", "contenu": section["contenu"] or ""}
        )

    bad: list[int] = []
    for fiche in fiches:
        payload = {
            "titre": fiche["titre"] or "",
            "resume": fiche["resume"] or "",
            "sections": by_fiche.get(int(fiche["id"]), []),
        }
        if not _validate_fiche_payload(payload):
            bad.append(int(fiche["id"]))
    return bad


async def delete_ids(conn: asyncpg.Connection, table: str, column: str, ids: list[int]) -> int:
    if not ids:
        return 0
    result = await conn.execute(f"delete from public.{table} where {column} = any($1::int[])", ids)
    try:
        return int(result.split()[-1])
    except Exception:
        return len(ids)


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Delete invalid rows. Default is dry-run.")
    args = parser.parse_args()

    conn = await asyncpg.connect(
        host=HOST,
        port=PORT,
        user=USER,
        password=PASSWORD,
        database=DATABASE,
        ssl=connect_ssl_context(),
    )
    try:
        flashcard_ids = await invalid_flashcard_ids(conn)
        fiche_ids = await invalid_fiche_ids(conn)
        mode = "DRY-RUN" if not args.apply else "APPLY"
        if args.apply:
            section_deleted = await delete_ids(conn, "fiche_sections", "fiche_id", fiche_ids)
            fiche_deleted = await delete_ids(conn, "fiches", "id", fiche_ids)
            flashcard_deleted = await delete_ids(conn, "flashcards", "id", flashcard_ids)
            print(
                f"{mode}: flashcards_deleted={flashcard_deleted} "
                f"fiches_deleted={fiche_deleted} sections_deleted={section_deleted}"
            )
        else:
            print(f"{mode}: invalid_flashcards={len(flashcard_ids)} invalid_fiches={len(fiche_ids)}")
        return 0
    finally:
        await conn.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
