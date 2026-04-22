#!/usr/bin/env python3
"""Insert assistant-authored fiches and flashcards into Supabase.

Input is JSON on stdin:
{
  "documents": [
    {
      "document_id": 123,
      "fiche": {"titre": "...", "resume": "...", "sections": [...]},
      "flashcards": [{"question": "...", "reponse": "...", "explication": "...", "difficulte": 3}]
    }
  ]
}
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import asyncpg

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"

sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(REPO_ROOT))

from app.services.claude_service import _validate_fiche_payload, _validate_flashcard
from scripts.generate_full_coverage import _normalize_question
from scripts.generate_supabase_quality_coverage import (
    DATABASE,
    HOST,
    PASSWORD,
    PORT,
    USER,
    connect_ssl_context,
    normalized,
)

logging.getLogger("app.services.claude_service").setLevel(logging.ERROR)


async def fetch_doc(conn: asyncpg.Connection, document_id: int) -> dict[str, Any] | None:
    row = await conn.fetchrow(
        """
        select d.id, d.titre, d.matiere_id, d.chapitre, coalesce(m.nom, 'Documents divers') as matiere,
               coalesce(fc.cnt,0) as flashcards,
               coalesce(fi.cnt,0) as fiches
        from public.documents d
        left join public.matieres m on m.id=d.matiere_id
        left join (select document_id, count(*) cnt from public.flashcards group by document_id) fc
            on fc.document_id=d.id
        left join (select document_id, count(*) cnt from public.fiches group by document_id) fi
            on fi.document_id=d.id
        where d.id=$1
        """,
        document_id,
    )
    return dict(row) if row else None


async def existing_questions(conn: asyncpg.Connection, document_id: int) -> set[str]:
    rows = await conn.fetch(
        "select question from public.flashcards where document_id=$1 and question is not null",
        document_id,
    )
    return {_normalize_question(row["question"]) for row in rows if row["question"]}


async def insert_fiche(
    conn: asyncpg.Connection,
    doc: dict[str, Any],
    payload: dict[str, Any],
    dry_run: bool,
) -> int:
    if int(doc.get("fiches") or 0) > 0:
        return 0
    if not _validate_fiche_payload(payload):
        raise ValueError(f"fiche invalide document_id={doc['id']}")
    if dry_run:
        return 1
    now = datetime.now(UTC).replace(tzinfo=None)
    fiche_id = await conn.fetchval(
        """
        insert into public.fiches (titre, resume, matiere_id, document_id, chapitre, tags, ordre, created_at)
        values ($1,$2,$3,$4,$5,$6,$7,$8)
        returning id
        """,
        str(payload.get("titre") or "").strip()[:180],
        str(payload.get("resume") or "").strip()[:1400],
        doc["matiere_id"],
        doc["id"],
        (doc.get("chapitre") or "")[:180],
        "direct-assistant",
        0,
        now,
    )
    for idx, section in enumerate(payload.get("sections") or []):
        await conn.execute(
            "insert into public.fiche_sections (fiche_id, titre, contenu, ordre) values ($1,$2,$3,$4)",
            fiche_id,
            str(section.get("titre") or "").strip()[:180],
            str(section.get("contenu") or "").strip()[:2400],
            idx,
        )
    return 1


async def insert_flashcards(
    conn: asyncpg.Connection,
    doc: dict[str, Any],
    cards: list[dict[str, Any]],
    dry_run: bool,
    min_flashcards: int,
) -> int:
    current = int(doc.get("flashcards") or 0)
    missing = max(0, min_flashcards - current)
    if missing <= 0:
        return 0
    seen = await existing_questions(conn, int(doc["id"]))
    now = datetime.now(UTC).replace(tzinfo=None)
    inserted = 0
    for card in cards:
        if inserted >= missing:
            break
        if not _validate_flashcard(card):
            raise ValueError(f"flashcard invalide document_id={doc['id']}: {card.get('question')!r}")
        question = str(card.get("question") or "").strip()
        norm = _normalize_question(question)
        if not question or norm in seen:
            continue
        seen.add(norm)
        if not dry_run:
            await conn.execute(
                """
                insert into public.flashcards
                    (question, reponse, explication, difficulte, matiere_id, document_id,
                     intervalle_jours, facteur_facilite, repetitions, prochaine_revision, created_at)
                values ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
                """,
                question[:280],
                str(card.get("reponse") or "").strip()[:900],
                str(card.get("explication") or "").strip()[:600],
                min(max(int(card.get("difficulte") or 3), 1), 5),
                doc["matiere_id"],
                doc["id"],
                1.0,
                2.5,
                0,
                now,
                now,
            )
        inserted += 1
    return inserted


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--min-flashcards", type=int, default=10)
    args = parser.parse_args()

    raw = sys.stdin.read()
    payload = json.loads(raw)
    docs_payload = payload.get("documents") or []
    if not isinstance(docs_payload, list):
        raise ValueError("documents must be a list")

    conn = await asyncpg.connect(
        host=HOST,
        port=PORT,
        user=USER,
        password=PASSWORD,
        database=DATABASE,
        ssl=connect_ssl_context(),
    )
    dry_run = not args.apply
    totals = {"documents": 0, "fiches": 0, "flashcards": 0, "skipped": 0}
    try:
        for item in docs_payload:
            document_id = int(item["document_id"])
            doc = await fetch_doc(conn, document_id)
            if not doc:
                totals["skipped"] += 1
                continue
            if "scolarite" in normalized(doc.get("matiere") or ""):
                totals["skipped"] += 1
                continue
            fiche_count = 0
            if item.get("fiche"):
                fiche_count = await insert_fiche(conn, doc, item["fiche"], dry_run)
                totals["fiches"] += fiche_count
                if fiche_count:
                    doc["fiches"] = int(doc.get("fiches") or 0) + fiche_count
            cards_count = await insert_flashcards(
                conn,
                doc,
                item.get("flashcards") or [],
                dry_run,
                args.min_flashcards,
            )
            totals["flashcards"] += cards_count
            if fiche_count or cards_count:
                totals["documents"] += 1
        mode = "DRY-RUN" if dry_run else "APPLY"
        print(f"{mode}: {totals}")
        return 0
    finally:
        await conn.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
