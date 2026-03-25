#!/usr/bin/env python3
"""
Batch: re-extraire PDFs mal extraits via marker, puis générer fiches et flashcards manquantes.

Usage:
  python3 scripts/reextract_and_generate.py [options]

Options:
  --dry-run          Affiche ce qui serait fait sans modifier la DB
  --limit N          Limite le nombre de documents traités (par phase)
  --matiere NOM      Filtre sur le nom de la matière (insensible à la casse)
  --skip-extract     Saute la phase de ré-extraction
  --skip-fiches      Saute la phase de génération de fiches
  --skip-flashcards  Saute la phase de génération de flashcards
  --min-flashcards N Seuil de flashcards en dessous duquel on régénère (défaut: 5)
  --provider         Fournisseur IA : claude | gemini | auto (défaut: auto)
                     auto = essaie claude, repasse sur gemini si rate-limit
"""

import argparse
import asyncio
import contextlib
import logging
import os
import sqlite3
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = REPO_ROOT / "data" / "iaca.db"
BACKEND_DIR = REPO_ROOT / "backend"

# Ajouter backend/ au path pour importer les services
sys.path.insert(0, str(BACKEND_DIR))
# Ajouter le dossier marker/ au path (pour marker_parser qui le charge aussi)
sys.path.insert(0, str(REPO_ROOT / "marker"))

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("reextract")

# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def open_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def fetch_docs_to_reextract(conn: sqlite3.Connection, matiere_filter: str | None, limit: int | None) -> list[sqlite3.Row]:
    """Documents PDF dont contenu_extrait est vide ou < 200 chars."""
    sql = """
        SELECT d.id, d.titre, d.fichier_path, d.type_fichier, d.contenu_extrait, d.matiere_id,
               m.nom AS matiere_nom
        FROM documents d
        LEFT JOIN matieres m ON m.id = d.matiere_id
        WHERE d.type_fichier = 'pdf'
          AND (d.contenu_extrait IS NULL OR length(trim(d.contenu_extrait)) < 200)
    """
    params: list = []
    if matiere_filter:
        sql += " AND lower(m.nom) LIKE ?"
        params.append(f"%{matiere_filter.lower()}%")
    sql += " ORDER BY d.id"
    if limit:
        sql += f" LIMIT {limit}"
    return conn.execute(sql, params).fetchall()


def fetch_docs_without_fiche(conn: sqlite3.Connection, matiere_filter: str | None, limit: int | None) -> list[sqlite3.Row]:
    """Documents sans fiche ET avec contenu_extrait suffisant."""
    sql = """
        SELECT d.id, d.titre, d.fichier_path, d.type_fichier, d.contenu_extrait, d.matiere_id,
               m.nom AS matiere_nom
        FROM documents d
        LEFT JOIN matieres m ON m.id = d.matiere_id
        WHERE d.contenu_extrait IS NOT NULL
          AND length(trim(d.contenu_extrait)) >= 120
          AND length(trim(d.contenu_extrait)) <= 200000
          AND NOT EXISTS (SELECT 1 FROM fiches f WHERE f.document_id = d.id)
          AND d.id NOT IN (
              SELECT d2.id FROM documents d2
              WHERE EXISTS (
                  SELECT 1 FROM documents d3
                  WHERE d3.contenu_extrait = d2.contenu_extrait AND d3.id < d2.id
              )
          )
    """
    params: list = []
    if matiere_filter:
        sql += " AND lower(m.nom) LIKE ?"
        params.append(f"%{matiere_filter.lower()}%")
    sql += " ORDER BY d.id"
    if limit:
        sql += f" LIMIT {limit}"
    return conn.execute(sql, params).fetchall()


def fetch_docs_with_few_flashcards(
    conn: sqlite3.Connection, matiere_filter: str | None, limit: int | None, min_fc: int
) -> list[sqlite3.Row]:
    """Documents avec < min_fc flashcards ET contenu_extrait suffisant."""
    sql = """
        SELECT d.id, d.titre, d.fichier_path, d.type_fichier, d.contenu_extrait, d.matiere_id,
               m.nom AS matiere_nom,
               COUNT(fc.id) AS nb_flashcards
        FROM documents d
        LEFT JOIN matieres m ON m.id = d.matiere_id
        LEFT JOIN flashcards fc ON fc.document_id = d.id
        WHERE d.contenu_extrait IS NOT NULL
          AND length(trim(d.contenu_extrait)) >= 120
          AND length(trim(d.contenu_extrait)) <= 200000
          AND d.id NOT IN (
              SELECT d2.id FROM documents d2
              WHERE EXISTS (
                  SELECT 1 FROM documents d3
                  WHERE d3.contenu_extrait = d2.contenu_extrait AND d3.id < d2.id
              )
          )
        GROUP BY d.id
        HAVING nb_flashcards < ?
    """
    params: list = [min_fc]
    if matiere_filter:
        sql = sql.replace(
            "GROUP BY d.id",
            "AND lower(m.nom) LIKE ? GROUP BY d.id"
        )
        params = [f"%{matiere_filter.lower()}%", min_fc]
    sql += " ORDER BY d.id"
    if limit:
        sql += f" LIMIT {limit}"
    return conn.execute(sql, params).fetchall()


def save_contenu(conn: sqlite3.Connection, doc_id: int, contenu: str) -> None:
    conn.execute(
        "UPDATE documents SET contenu_extrait = ? WHERE id = ?",
        (contenu, doc_id),
    )
    conn.commit()


def save_fiche(conn: sqlite3.Connection, doc_id: int, matiere_id: int | None, fiche_data: dict) -> int:
    cur = conn.execute(
        "INSERT INTO fiches (titre, resume, document_id, matiere_id, tags) VALUES (?, ?, ?, ?, ?)",
        (
            fiche_data.get("titre", ""),
            fiche_data.get("resume", ""),
            doc_id,
            matiere_id,
            "",
        ),
    )
    fiche_id = cur.lastrowid
    for i, s in enumerate(fiche_data.get("sections", [])):
        contenu_sec = s.get("contenu", "")
        if len(str(contenu_sec).strip()) < 40:
            continue
        conn.execute(
            "INSERT INTO fiche_sections (fiche_id, titre, contenu, ordre) VALUES (?, ?, ?, ?)",
            (fiche_id, s.get("titre", f"Section {i+1}"), contenu_sec, i),
        )
    conn.commit()
    return fiche_id


def save_flashcards(conn: sqlite3.Connection, doc_id: int, matiere_id: int | None, cards: list[dict]) -> int:
    count = 0
    for fc in cards:
        conn.execute(
            "INSERT INTO flashcards (question, reponse, explication, difficulte, document_id, matiere_id)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (
                fc.get("question", ""),
                fc.get("reponse", ""),
                fc.get("explication", ""),
                fc.get("difficulte", 1),
                doc_id,
                matiere_id,
            ),
        )
        count += 1
    conn.commit()
    return count


# ---------------------------------------------------------------------------
# Provider routing
# ---------------------------------------------------------------------------

@contextlib.asynccontextmanager
async def _gemini_backend():
    """Temporarily replace claude_service.run_claude_cli with gemini_service._generate.

    Both share the same signature: async (prompt: str) -> str.
    This lets generer_fiche / generer_flashcards run unchanged while using Gemini.
    """
    from app.services import claude_service, gemini_service  # type: ignore
    original = claude_service.run_claude_cli
    claude_service.run_claude_cli = gemini_service._generate
    try:
        yield
    finally:
        claude_service.run_claude_cli = original


async def _generer_fiche_provider(contenu: str, matiere: str, titre: str, provider: str) -> dict:
    from app.services import claude_service  # type: ignore
    if provider == "gemini":
        async with _gemini_backend():
            return await claude_service.generer_fiche(contenu, matiere, titre)
    if provider == "auto":
        try:
            return await claude_service.generer_fiche(contenu, matiere, titre)
        except RuntimeError as exc:
            if "limit" in str(exc).lower() or "rate" in str(exc).lower():
                log.warning("Claude rate-limit — bascule Gemini pour cette fiche")
                async with _gemini_backend():
                    return await claude_service.generer_fiche(contenu, matiere, titre)
            raise
    # provider == "claude"
    return await claude_service.generer_fiche(contenu, matiere, titre)


async def _generer_flashcards_provider(contenu: str, matiere: str, nb: int, provider: str) -> list[dict]:
    from app.services import claude_service  # type: ignore
    if provider == "gemini":
        async with _gemini_backend():
            return await claude_service.generer_flashcards(contenu, matiere, nb=nb)
    if provider == "auto":
        try:
            return await claude_service.generer_flashcards(contenu, matiere, nb=nb)
        except RuntimeError as exc:
            if "limit" in str(exc).lower() or "rate" in str(exc).lower():
                log.warning("Claude rate-limit — bascule Gemini pour ces flashcards")
                async with _gemini_backend():
                    return await claude_service.generer_flashcards(contenu, matiere, nb=nb)
            raise
    # provider == "claude"
    return await claude_service.generer_flashcards(contenu, matiere, nb=nb)


# ---------------------------------------------------------------------------
# Phases async
# ---------------------------------------------------------------------------

async def phase_reextract(conn: sqlite3.Connection, docs: list, dry_run: bool) -> dict:
    from app.services.marker_parser import parse_pdf_with_marker  # type: ignore

    stats = {"attempted": 0, "ok": 0, "skipped": 0, "error": 0}
    for doc in docs:
        stats["attempted"] += 1
        fpath = doc["fichier_path"]
        if not fpath or not os.path.exists(fpath):
            log.warning("[extract] [%d] fichier introuvable: %s", doc["id"], fpath)
            stats["skipped"] += 1
            continue

        log.info("[extract] [%d] %s …", doc["id"], doc["titre"][:60])
        if dry_run:
            log.info("[extract] [%d] DRY-RUN — ignoré", doc["id"])
            stats["ok"] += 1
            continue

        try:
            contenu = await parse_pdf_with_marker(fpath)
            if len(contenu.strip()) < 200:
                log.warning("[extract] [%d] contenu trop court après extraction (%d chars)", doc["id"], len(contenu))
                stats["skipped"] += 1
                continue
            save_contenu(conn, doc["id"], contenu)
            log.info("[extract] [%d] OK — %d chars", doc["id"], len(contenu))
            stats["ok"] += 1
        except Exception as exc:
            log.error("[extract] [%d] ERREUR: %s", doc["id"], exc)
            stats["error"] += 1

    return stats


async def phase_fiches(conn: sqlite3.Connection, docs: list, dry_run: bool, provider: str = "auto") -> dict:
    stats = {"attempted": 0, "ok": 0, "skipped": 0, "error": 0}
    for doc in docs:
        stats["attempted"] += 1
        contenu = (doc["contenu_extrait"] or "").strip()
        if len(contenu) < 120:
            log.warning("[fiche] [%d] contenu insuffisant (%d chars) — sauté", doc["id"], len(contenu))
            stats["skipped"] += 1
            continue

        matiere_nom = doc["matiere_nom"] or "droit public"
        log.info("[fiche] [%d] %s [%s] [%s] …", doc["id"], doc["titre"][:60], matiere_nom, provider)

        if dry_run:
            log.info("[fiche] [%d] DRY-RUN — ignoré", doc["id"])
            stats["ok"] += 1
            continue

        try:
            fiche_data = await _generer_fiche_provider(contenu, matiere_nom, doc["titre"], provider)
            fiche_id = save_fiche(conn, doc["id"], doc["matiere_id"], fiche_data)
            nb_sec = len(fiche_data.get("sections", []))
            log.info("[fiche] [%d] OK — fiche_id=%d sections=%d", doc["id"], fiche_id, nb_sec)
            stats["ok"] += 1
            await asyncio.sleep(5)  # Rate-limit spacing
        except Exception as exc:
            log.error("[fiche] [%d] ERREUR: %s", doc["id"], exc)
            stats["error"] += 1
            await asyncio.sleep(10)  # Longer pause after error

    return stats


async def phase_flashcards(conn: sqlite3.Connection, docs: list, dry_run: bool, provider: str = "auto") -> dict:
    stats = {"attempted": 0, "ok": 0, "skipped": 0, "error": 0}
    for doc in docs:
        stats["attempted"] += 1
        contenu = (doc["contenu_extrait"] or "").strip()
        if len(contenu) < 120:
            log.warning("[flashcard] [%d] contenu insuffisant (%d chars) — sauté", doc["id"], len(contenu))
            stats["skipped"] += 1
            continue

        matiere_nom = doc["matiere_nom"] or "droit public"
        nb_existing = doc["nb_flashcards"] if "nb_flashcards" in doc.keys() else 0
        log.info(
            "[flashcard] [%d] %s [%s] [%s] — existantes: %d …",
            doc["id"], doc["titre"][:60], matiere_nom, provider, nb_existing,
        )

        if dry_run:
            log.info("[flashcard] [%d] DRY-RUN — ignoré", doc["id"])
            stats["ok"] += 1
            continue

        try:
            cards = await _generer_flashcards_provider(contenu, matiere_nom, nb=10, provider=provider)
            saved = save_flashcards(conn, doc["id"], doc["matiere_id"], cards)
            log.info("[flashcard] [%d] OK — %d cartes insérées", doc["id"], saved)
            stats["ok"] += 1
            await asyncio.sleep(5)  # Rate-limit spacing
        except Exception as exc:
            log.error("[flashcard] [%d] ERREUR: %s", doc["id"], exc)
            stats["error"] += 1
            await asyncio.sleep(10)  # Longer pause after error

    return stats


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main(args: argparse.Namespace) -> None:
    if not DB_PATH.exists():
        log.error("Base de données introuvable: %s", DB_PATH)
        sys.exit(1)

    conn = open_db()
    dry_run = args.dry_run
    limit = args.limit
    matiere = args.matiere
    min_fc = args.min_flashcards
    provider = args.provider
    log.info("Fournisseur IA: %s", provider)

    if dry_run:
        log.info("=== MODE DRY-RUN — aucune écriture en DB ===")

    # --- Phase 1: ré-extraction ---
    if not args.skip_extract:
        docs_extract = fetch_docs_to_reextract(conn, matiere, limit)
        log.info("Phase 1 — ré-extraction: %d documents à traiter", len(docs_extract))
        if docs_extract:
            stats = await phase_reextract(conn, docs_extract, dry_run)
            log.info(
                "Phase 1 terminée — ok=%d skipped=%d error=%d",
                stats["ok"], stats["skipped"], stats["error"],
            )
        else:
            log.info("Phase 1 — rien à ré-extraire")

    # --- Phase 2: génération fiches ---
    if not args.skip_fiches:
        docs_fiches = fetch_docs_without_fiche(conn, matiere, limit)
        log.info("Phase 2 — génération fiches: %d documents sans fiche", len(docs_fiches))
        if docs_fiches:
            stats = await phase_fiches(conn, docs_fiches, dry_run, provider)
            log.info(
                "Phase 2 terminée — ok=%d skipped=%d error=%d",
                stats["ok"], stats["skipped"], stats["error"],
            )
        else:
            log.info("Phase 2 — toutes les fiches sont présentes")

    # --- Phase 3: génération flashcards ---
    if not args.skip_flashcards:
        docs_fc = fetch_docs_with_few_flashcards(conn, matiere, limit, min_fc)
        log.info(
            "Phase 3 — génération flashcards: %d documents avec < %d flashcards",
            len(docs_fc), min_fc,
        )
        if docs_fc:
            stats = await phase_flashcards(conn, docs_fc, dry_run, provider)
            log.info(
                "Phase 3 terminée — ok=%d skipped=%d error=%d",
                stats["ok"], stats["skipped"], stats["error"],
            )
        else:
            log.info("Phase 3 — flashcards suffisantes partout")

    conn.close()
    log.info("Terminé.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Batch re-extraction PDF + génération fiches/flashcards via marker + Claude."
    )
    parser.add_argument("--dry-run", action="store_true", help="Aucune écriture en DB")
    parser.add_argument("--limit", type=int, default=None, metavar="N", help="Limite de documents par phase")
    parser.add_argument("--matiere", type=str, default=None, metavar="NOM", help="Filtre sur le nom de la matière")
    parser.add_argument("--skip-extract", action="store_true", help="Sauter la phase de ré-extraction")
    parser.add_argument("--skip-fiches", action="store_true", help="Sauter la génération de fiches")
    parser.add_argument("--skip-flashcards", action="store_true", help="Sauter la génération de flashcards")
    parser.add_argument("--min-flashcards", type=int, default=5, metavar="N", help="Seuil min flashcards (défaut: 5)")
    parser.add_argument(
        "--provider",
        choices=["claude", "gemini", "auto"],
        default="auto",
        help="Fournisseur IA : claude | gemini | auto (défaut: auto = claude puis fallback gemini)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    asyncio.run(main(parse_args()))
