#!/usr/bin/env python3
"""
generate_supabase_quality_coverage.py
====================================

Generate quality flashcards and fiches directly into Supabase for documents
still missing coverage, reusing the repo's extraction/generation stack.

Quality rules:
- no heuristic/fill-pass flashcards
- Claude-only generation for flashcards/fiches
- strict document filtering (skip garbage titles / noisy content)
- deduplicate per document on normalized question/title
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import ssl
import sys
import unicodedata
from datetime import UTC, datetime
from pathlib import Path

import asyncpg

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
LOG_PATH = REPO_ROOT / "logs" / "supabase_quality_coverage.log"
DEFAULT_PREVIEW_DIR = REPO_ROOT / "data" / "supabase_quality_previews"

sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(BACKEND_DIR))

from app.services.claude_service import (  # noqa: E402
    _validate_fiche_payload,
    generer_fiche,
    generer_flashcards,
)
from scripts.generate_full_coverage import (  # noqa: E402
    _is_garbage_title,
    _normalize_question,
    _prepare_generation_source,
    _should_skip_document_for_generation,
)

HOST = "aws-1-ap-northeast-1.pooler.supabase.com"
PORT = 5432
USER = "postgres.hssjsvsvenfawegmhecx"
PASSWORD = "a:aZbZDjfa8xN4D"
DATABASE = "postgres"


def setup_logging() -> logging.Logger:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("supabase_quality_coverage")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    file_handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    return logger


def connect_ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def normalized(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.split())


def target_flashcards(content_len: int) -> int:
    if content_len >= 400_000:
        return 12
    if content_len >= 120_000:
        return 8
    if content_len >= 40_000:
        return 6
    return 4


def should_skip_doc(title: str, contenu: str, matiere: str, include_espagnol: bool) -> bool:
    if not include_espagnol and "espagnol" in normalized(matiere):
        return True
    if _is_garbage_title(title):
        return True
    if _should_skip_document_for_generation(title, contenu):
        return True
    return False


async def fetch_docs(
    conn: asyncpg.Connection,
    limit: int | None,
    only_missing_both: bool,
    min_content_len: int,
    max_content_len: int | None,
    smallest_first: bool,
    include_espagnol: bool,
) -> list[asyncpg.Record]:
    where_clause = "where coalesce(fc.cnt,0)=0 or coalesce(fi.cnt,0)=0"
    if only_missing_both:
        where_clause = "where coalesce(fc.cnt,0)=0 and coalesce(fi.cnt,0)=0"
    order_direction = "asc" if smallest_first else "desc"
    sql = f"""
        select d.id, d.titre, d.contenu_extrait, d.matiere_id, d.chapitre, coalesce(m.nom, 'Documents divers') as matiere,
               length(coalesce(d.contenu_extrait,'')) as content_len,
               coalesce(fc.cnt,0) as flashcards,
               coalesce(fi.cnt,0) as fiches
        from public.documents d
        left join public.matieres m on m.id=d.matiere_id
        left join (select document_id, count(*) cnt from public.flashcards group by document_id) fc on fc.document_id=d.id
        left join (select document_id, count(*) cnt from public.fiches group by document_id) fi on fi.document_id=d.id
        {where_clause}
        order by length(coalesce(d.contenu_extrait,'')) {order_direction}, d.id asc
    """
    rows = await conn.fetch(sql)
    docs = []
    for row in rows:
        title = row["titre"] or ""
        contenu = row["contenu_extrait"] or ""
        matiere = row["matiere"] or ""
        if len(contenu) < min_content_len:
            continue
        if max_content_len is not None and len(contenu) > max_content_len:
            continue
        if should_skip_doc(title, contenu, matiere, include_espagnol):
            continue
        docs.append(row)
        if limit and len(docs) >= limit:
            break
    return docs


async def existing_questions(conn: asyncpg.Connection, doc_id: int) -> set[str]:
    rows = await conn.fetch(
        "select question from public.flashcards where document_id=$1 and question is not null",
        doc_id,
    )
    return {_normalize_question(row["question"]) for row in rows if row["question"]}


async def existing_fiche_titles(conn: asyncpg.Connection, doc_id: int) -> set[str]:
    rows = await conn.fetch(
        "select titre from public.fiches where document_id=$1 and titre is not null",
        doc_id,
    )
    return {normalized(row["titre"]) for row in rows if row["titre"]}


async def insert_flashcards(
    conn: asyncpg.Connection,
    doc: asyncpg.Record,
    cards: list[dict],
    logger: logging.Logger,
) -> int:
    seen = await existing_questions(conn, doc["id"])
    inserted = 0
    now = datetime.now(UTC).replace(tzinfo=None)
    for card in cards:
        question = str(card.get("question", "")).strip()
        if not question:
            continue
        norm = _normalize_question(question)
        if norm in seen:
            continue
        seen.add(norm)
        await conn.execute(
            """
            insert into public.flashcards
                (question, reponse, explication, difficulte, matiere_id, document_id,
                 intervalle_jours, facteur_facilite, repetitions, prochaine_revision, created_at)
            values ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
            """,
            question[:280],
            str(card.get("reponse", "")).strip()[:900],
            str(card.get("explication", "")).strip()[:600],
            int(card.get("difficulte", 3)),
            doc["matiere_id"],
            doc["id"],
            1.0,
            2.5,
            0,
            now,
            now,
        )
        inserted += 1
    if inserted:
        logger.info("doc=%s +%s flashcards", doc["id"], inserted)
    return inserted


async def insert_fiche(
    conn: asyncpg.Connection,
    doc: asyncpg.Record,
    fiche: dict | None,
    logger: logging.Logger,
) -> int:
    if not fiche:
        return 0
    if not fiche.get("sections"):
        return 0
    seen_titles = await existing_fiche_titles(conn, doc["id"])
    titre = str(fiche.get("titre", "")).strip()[:180]
    if normalized(titre) in seen_titles:
        return 0
    now = datetime.now(UTC).replace(tzinfo=None)
    fiche_id = await conn.fetchval(
        """
        insert into public.fiches (titre, resume, matiere_id, document_id, chapitre, tags, ordre, created_at)
        values ($1,$2,$3,$4,$5,$6,$7,$8)
        returning id
        """,
        titre or f"Fiche - {doc['titre'][:120]}",
        str(fiche.get("resume", "")).strip()[:1400],
        doc["matiere_id"],
        doc["id"],
        (doc["chapitre"] or "")[:180],
        "",
        0,
        now,
    )
    for idx, section in enumerate(fiche.get("sections", [])):
        await conn.execute(
            "insert into public.fiche_sections (fiche_id, titre, contenu, ordre) values ($1,$2,$3,$4)",
            fiche_id,
            str(section.get("titre", "")).strip()[:180],
            str(section.get("contenu", "")).strip()[:2400],
            idx,
        )
    logger.info("doc=%s +1 fiche", doc["id"])
    return 1


def dump_preview(doc: asyncpg.Record, cards: list[dict], fiche: dict | None, preview_dir: Path) -> None:
    preview_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "document_id": doc["id"],
        "titre": doc["titre"],
        "matiere": doc["matiere"],
        "chapitre": doc["chapitre"],
        "content_len": doc["content_len"],
        "flashcards": cards,
        "fiche": fiche,
        "generated_at": datetime.now(UTC).replace(tzinfo=None).isoformat(),
    }
    target = preview_dir / f"doc_{doc['id']}.json"
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


async def process_doc(
    conn: asyncpg.Connection,
    doc: asyncpg.Record,
    logger: logging.Logger,
    preview_dir: Path | None,
    dry_run: bool,
    flashcards_timeout: int,
    fiche_timeout: int,
) -> tuple[int, int]:
    contenu = _prepare_generation_source(doc["contenu_extrait"] or "")
    matiere = doc["matiere"] or "Documents divers"
    flashcards_inserted = 0
    fiches_inserted = 0
    cards: list[dict] = []
    fiche: dict | None = None

    if doc["flashcards"] == 0:
        target = target_flashcards(doc["content_len"])
        cards = await asyncio.wait_for(
            generer_flashcards(contenu, matiere, nb=target),
            timeout=flashcards_timeout,
        )
        if not dry_run:
            flashcards_inserted = await insert_flashcards(conn, doc, cards, logger)

    if doc["fiches"] == 0:
        fiche = await asyncio.wait_for(
            generer_fiche(contenu, matiere, doc["titre"] or ""),
            timeout=fiche_timeout,
        )
        if fiche and not _validate_fiche_payload(fiche):
            logger.warning("doc=%s fiche rejetée après génération: payload insuffisant ou trop brut", doc["id"])
            fiche = None
        if not dry_run:
            fiches_inserted = await insert_fiche(conn, doc, fiche, logger)

    if preview_dir is not None and (cards or fiche):
        dump_preview(doc, cards, fiche, preview_dir)

    return flashcards_inserted, fiches_inserted


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--only-missing-both", action="store_true")
    parser.add_argument("--doc-id", type=int, default=None)
    parser.add_argument("--min-content-len", type=int, default=1600)
    parser.add_argument("--max-content-len", type=int, default=None)
    parser.add_argument("--smallest-first", action="store_true")
    parser.add_argument("--include-espagnol", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--preview-dir", type=Path, default=DEFAULT_PREVIEW_DIR)
    parser.add_argument("--flashcards-timeout", type=int, default=1200)
    parser.add_argument("--fiche-timeout", type=int, default=1200)
    args = parser.parse_args()

    logger = setup_logging()
    conn = await asyncpg.connect(
        host=HOST,
        port=PORT,
        user=USER,
        password=PASSWORD,
        database=DATABASE,
        ssl=connect_ssl_context(),
    )
    try:
        if args.doc_id is not None:
            rows = await conn.fetch(
                """
                select d.id, d.titre, d.contenu_extrait, d.matiere_id, d.chapitre, coalesce(m.nom, 'Documents divers') as matiere,
                       length(coalesce(d.contenu_extrait,'')) as content_len,
                       coalesce(fc.cnt,0) as flashcards,
                       coalesce(fi.cnt,0) as fiches
                from public.documents d
                left join public.matieres m on m.id=d.matiere_id
                left join (select document_id, count(*) cnt from public.flashcards group by document_id) fc on fc.document_id=d.id
                left join (select document_id, count(*) cnt from public.fiches group by document_id) fi on fi.document_id=d.id
                where d.id=$1
                """,
                args.doc_id,
            )
            docs = [
                row
                for row in rows
                if len(row["contenu_extrait"] or "") >= args.min_content_len
                and (args.max_content_len is None or len(row["contenu_extrait"] or "") <= args.max_content_len)
                and not should_skip_doc(
                    row["titre"],
                    row["contenu_extrait"] or "",
                    row["matiere"] or "",
                    args.include_espagnol,
                )
            ]
        else:
            docs = await fetch_docs(
                conn,
                args.limit,
                args.only_missing_both,
                args.min_content_len,
                args.max_content_len,
                args.smallest_first,
                args.include_espagnol,
            )
        logger.info("docs sélectionnés: %s", len(docs))

        total_fc = 0
        total_fi = 0
        errors = 0
        for doc in docs:
            try:
                logger.info(
                    "doc=%s matiere=%s len=%s flashcards=%s fiches=%s titre=%r",
                    doc["id"], doc["matiere"], doc["content_len"], doc["flashcards"], doc["fiches"], doc["titre"][:120],
                )
                fc, fi = await process_doc(
                    conn,
                    doc,
                    logger,
                    args.preview_dir,
                    args.dry_run,
                    args.flashcards_timeout,
                    args.fiche_timeout,
                )
                total_fc += fc
                total_fi += fi
            except Exception as exc:
                errors += 1
                logger.exception("échec doc=%s: %s", doc["id"], exc)
        logger.info("termine docs=%s flashcards=%s fiches=%s errors=%s", len(docs), total_fc, total_fi, errors)
        return 0 if errors == 0 else 1
    finally:
        await conn.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
