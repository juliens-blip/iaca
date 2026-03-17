#!/usr/bin/env python3
"""
Import missing PDFs from docs/ into the documents table.

Behavior:
- scans the five top-level matiere folders under docs/
- resolves folder -> matiere_id from the matieres table
- deduplicates by normalized document title only
- copies imported files into data/uploads, like the upload route
- extracts content with backend.app.services.document_parser.parse_document
- inserts rows with sqlite3 directly

Usage:
  python3 scripts/import_missing_pdfs.py --dry-run --limit 3
"""

from __future__ import annotations

import argparse
import asyncio
import shutil
import sqlite3
import sys
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.services.document_parser import parse_document


DB_PATH = REPO_ROOT / "data" / "iaca.db"
DOCS_ROOT = REPO_ROOT / "docs"
UPLOAD_ROOT = REPO_ROOT / "data" / "uploads"

FOLDER_TO_MATIERE_NAME = {
    "droit-public": "Droit public",
    "economie-finances-publiques": "Economie et finances publiques",
    "questions-contemporaines": "Questions contemporaines",
    "questions-sociales": "Questions sociales",
    "relations-internationales": "Relations internationales",
}


@dataclass(frozen=True)
class ImportCandidate:
    source_path: Path
    folder_name: str
    matiere_id: int
    matiere_name: str
    titre: str
    chapitre: str
    tags: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import missing PDFs from docs/ into sqlite.")
    parser.add_argument("--db-path", type=Path, default=DB_PATH, help="Path to the sqlite database.")
    parser.add_argument("--docs-root", type=Path, default=DOCS_ROOT, help="Root docs directory.")
    parser.add_argument("--upload-root", type=Path, default=UPLOAD_ROOT, help="Target upload directory.")
    parser.add_argument(
        "--matiere",
        choices=sorted(FOLDER_TO_MATIERE_NAME),
        help="Restrict import to one top-level docs folder.",
    )
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of PDFs to process.")
    parser.add_argument("--dry-run", action="store_true", help="Parse and plan inserts without writing to DB.")
    return parser.parse_args()


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    stripped = "".join(char for char in normalized if not unicodedata.combining(char))
    stripped = stripped.replace("’", "'").replace("`", "'")
    collapsed = " ".join(stripped.lower().strip().split())
    return collapsed


def open_db(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(str(db_path), timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA busy_timeout=30000")
    return connection


def fetch_matieres(connection: sqlite3.Connection) -> list[sqlite3.Row]:
    return connection.execute("SELECT id, nom FROM matieres ORDER BY id").fetchall()


def resolve_folder_mapping(matieres: list[sqlite3.Row]) -> dict[str, tuple[int, str]]:
    matiere_lookup = {normalize_text(row["nom"]): (row["id"], row["nom"]) for row in matieres}
    resolved: dict[str, tuple[int, str]] = {}

    for folder_name, expected_name in FOLDER_TO_MATIERE_NAME.items():
        lookup_key = normalize_text(expected_name)
        if lookup_key not in matiere_lookup:
            raise SystemExit(f"Matiere not found in DB for folder '{folder_name}': {expected_name}")
        resolved[folder_name] = matiere_lookup[lookup_key]

    return resolved


def count_pdfs_by_folder(docs_root: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    for folder_name in FOLDER_TO_MATIERE_NAME:
        folder_path = docs_root / folder_name
        counts[folder_name] = sum(1 for path in folder_path.rglob("*.pdf") if path.is_file())
    return counts


def fetch_existing_titles(connection: sqlite3.Connection) -> set[str]:
    rows = connection.execute("SELECT titre FROM documents").fetchall()
    return {normalize_text(row["titre"]) for row in rows}


def build_candidate(path: Path, docs_root: Path, matiere_id: int, matiere_name: str) -> ImportCandidate:
    relative_path = path.relative_to(docs_root)
    folder_name = relative_path.parts[0]
    chapitre = relative_path.parent.relative_to(folder_name).as_posix()
    if chapitre == ".":
        chapitre = ""
    return ImportCandidate(
        source_path=path,
        folder_name=folder_name,
        matiere_id=matiere_id,
        matiere_name=matiere_name,
        titre=path.stem,
        chapitre=chapitre,
        tags=folder_name,
    )


def collect_candidates(
    docs_root: Path,
    resolved_mapping: dict[str, tuple[int, str]],
    existing_titles: set[str],
    matiere_filter: str | None,
) -> list[ImportCandidate]:
    candidates: list[ImportCandidate] = []
    seen_titles = set(existing_titles)

    folder_names = [matiere_filter] if matiere_filter else sorted(FOLDER_TO_MATIERE_NAME)
    for folder_name in folder_names:
        folder_path = docs_root / folder_name
        matiere_id, matiere_name = resolved_mapping[folder_name]

        for pdf_path in sorted(folder_path.rglob("*.pdf")):
            title_key = normalize_text(pdf_path.stem)
            if title_key in seen_titles:
                continue
            seen_titles.add(title_key)
            candidates.append(build_candidate(pdf_path, docs_root, matiere_id, matiere_name))

    return candidates


def make_upload_path(upload_root: Path, source_path: Path) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    return upload_root / f"{timestamp}_{source_path.name}"


def extract_content(file_path: Path) -> tuple[str, str | None]:
    try:
        content = asyncio.run(parse_document(str(file_path))).strip()
        return content, None
    except Exception as exc:
        return "", str(exc)


def insert_document(connection: sqlite3.Connection, candidate: ImportCandidate, stored_path: Path, content: str) -> int:
    cursor = connection.execute(
        """
        INSERT INTO documents (
            titre, fichier_path, type_fichier, contenu_extrait, matiere_id, chapitre, tags, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            candidate.titre,
            str(stored_path),
            "pdf",
            content,
            candidate.matiere_id,
            candidate.chapitre,
            candidate.tags,
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    connection.commit()
    return int(cursor.lastrowid)


def print_matieres(matieres: list[sqlite3.Row]) -> None:
    print("Matieres table:")
    for row in matieres:
        print(f"  {row['id']:>2} | {row['nom']}")


def print_folder_counts(folder_counts: dict[str, int]) -> None:
    print("PDF counts in docs/:")
    for folder_name, count in folder_counts.items():
        print(f"  {folder_name}: {count}")
    print(f"  total: {sum(folder_counts.values())}")


def process_candidate(
    connection: sqlite3.Connection,
    candidate: ImportCandidate,
    upload_root: Path,
    dry_run: bool,
) -> None:
    if dry_run:
        content, error = extract_content(candidate.source_path)
        status = "WARN" if error else "OK"
        print(
            f"[{status}] dry-run | {candidate.titre} | matiere={candidate.matiere_id} "
            f"| chars={len(content)} | source={candidate.source_path}"
        )
        if error:
            print(f"       extraction error: {error}")
        return

    upload_root.mkdir(parents=True, exist_ok=True)
    stored_path = make_upload_path(upload_root, candidate.source_path)
    shutil.copy2(candidate.source_path, stored_path)

    content, error = extract_content(stored_path)
    try:
        document_id = insert_document(connection, candidate, stored_path, content)
    except Exception:
        if stored_path.exists():
            stored_path.unlink()
        raise

    status = "WARN" if error else "OK"
    print(
        f"[{status}] imported | doc_id={document_id} | {candidate.titre} "
        f"| matiere={candidate.matiere_id} | chars={len(content)}"
    )
    if error:
        print(f"       extraction error: {error}")


def main() -> int:
    args = parse_args()

    if not args.db_path.exists():
        raise SystemExit(f"Database not found: {args.db_path}")
    if not args.docs_root.exists():
        raise SystemExit(f"Docs root not found: {args.docs_root}")

    connection = open_db(args.db_path)
    try:
        matieres = fetch_matieres(connection)
        resolved_mapping = resolve_folder_mapping(matieres)
        folder_counts = count_pdfs_by_folder(args.docs_root)
        existing_titles = fetch_existing_titles(connection)
        candidates = collect_candidates(args.docs_root, resolved_mapping, existing_titles, args.matiere)

        if args.limit is not None:
            candidates = candidates[: args.limit]

        print_folder_counts(folder_counts)
        print()
        print_matieres(matieres)
        print()
        print("Resolved folder mapping:")
        for folder_name, (matiere_id, matiere_name) in resolved_mapping.items():
            print(f"  {folder_name} -> {matiere_id} ({matiere_name})")
        print()
        print(f"Existing document titles: {len(existing_titles)}")
        print(f"Candidates to process: {len(candidates)}")
        if args.matiere:
            print(f"Filtered matiere: {args.matiere}")
        if args.dry_run:
            print("Mode: dry-run")
        print()

        if not candidates:
            print("No missing PDFs matched the current selection.")
            return 0

        for candidate in candidates:
            process_candidate(connection, candidate, args.upload_root, args.dry_run)

        return 0
    finally:
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
