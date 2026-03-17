#!/usr/bin/env python3
"""
Test end-to-end du pipeline PDF: extraction marker → chunking → (optionnel) génération IA.

Usage:
  python3 scripts/test_pdf_pipeline.py [PDF_PATH] [options]

  PDF_PATH          Chemin vers un fichier PDF (défaut: premier PDF trouvé dans docs/)
  --generate        Appelle generer_fiche() et generer_flashcards() via Claude
  --dry-run         Analyse seulement, sans appel IA (défaut)
"""

import argparse
import asyncio
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))
sys.path.insert(0, str(REPO_ROOT / "marker"))


def find_default_pdf() -> Path | None:
    docs_dir = REPO_ROOT / "docs"
    if docs_dir.exists():
        for pdf in sorted(docs_dir.rglob("*.pdf")):
            return pdf
    return None


def detect_section_titles(markdown: str) -> list[str]:
    return re.findall(r"^#{1,3} (.+)", markdown, re.MULTILINE)


# ---------------------------------------------------------------------------
# Core pipeline
# ---------------------------------------------------------------------------

async def run_pipeline(pdf_path: Path, generate: bool) -> None:
    print(f"\n=== Pipeline PDF — {pdf_path.name} ===\n")

    # ------------------------------------------------------------------
    # Etape 1: Extraction via marker
    # ------------------------------------------------------------------
    print("[ 1/3 ] Extraction marker …")
    from app.services.marker_parser import parse_pdf_with_marker  # type: ignore

    try:
        markdown = await parse_pdf_with_marker(str(pdf_path))
    except Exception as exc:
        print(f"  ERREUR extraction: {exc}")
        sys.exit(1)

    nb_chars = len(markdown)
    nb_lines = markdown.count("\n")
    print(f"  OK — {nb_chars} chars, {nb_lines} lignes")

    # ------------------------------------------------------------------
    # Etape 2: Chunking
    # ------------------------------------------------------------------
    print("\n[ 2/3 ] Chunking (max 4000 chars/chunk) …")
    from app.services.claude_service import chunk_content  # type: ignore

    chunks = chunk_content(markdown, max_chars=4000)
    nb_chunks = len(chunks)
    avg_size = int(sum(len(c) for c in chunks) / nb_chunks) if nb_chunks else 0
    print(f"  {nb_chunks} chunks — taille moyenne: {avg_size} chars")

    # ------------------------------------------------------------------
    # Etape 3: Stats
    # ------------------------------------------------------------------
    print("\n[ 3/3 ] Statistiques")
    titles = detect_section_titles(markdown)
    print(f"  Titres de sections détectés ({len(titles)}):")
    for t in titles[:20]:
        print(f"    • {t}")
    if len(titles) > 20:
        print(f"    … et {len(titles) - 20} autres")

    print("\n--- Résumé ---")
    print(f"  Fichier     : {pdf_path}")
    print(f"  Taille raw  : {pdf_path.stat().st_size // 1024} Ko")
    print(f"  Chars extrait: {nb_chars}")
    print(f"  Lignes       : {nb_lines}")
    print(f"  Sections     : {len(titles)}")
    print(f"  Chunks       : {nb_chunks}")
    print(f"  Moy. chunk   : {avg_size} chars")

    # Aperçu premier chunk
    if chunks:
        preview = chunks[0][:300].replace("\n", " ")
        print(f"\n  Aperçu chunk 1: {preview} …")

    # ------------------------------------------------------------------
    # Génération IA (optionnel)
    # ------------------------------------------------------------------
    if generate:
        from app.services.claude_service import generer_fiche, generer_flashcards  # type: ignore

        matiere = "droit public"
        titre_doc = pdf_path.stem

        print(f"\n[ IA ] generer_fiche() — matière: {matiere} …")
        try:
            fiche = await generer_fiche(markdown, matiere, titre_doc)
            print(json.dumps(fiche, ensure_ascii=False, indent=2)[:2000])
        except Exception as exc:
            print(f"  ERREUR fiche: {exc}")

        print(f"\n[ IA ] generer_flashcards() — 5 cartes …")
        try:
            cards = await generer_flashcards(markdown, matiere, nb=5)
            print(json.dumps(cards, ensure_ascii=False, indent=2)[:2000])
        except Exception as exc:
            print(f"  ERREUR flashcards: {exc}")
    else:
        print("\n  (Mode dry-run — utilisez --generate pour lancer la génération IA)")

    print("\n=== Pipeline terminé ===")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Test end-to-end du pipeline PDF: marker → chunking → génération IA optionnelle."
    )
    parser.add_argument(
        "pdf",
        nargs="?",
        default=None,
        metavar="PDF_PATH",
        help="Chemin vers un fichier PDF (défaut: premier PDF dans docs/)",
    )
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Appelle generer_fiche() et generer_flashcards() via Claude",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Analyse uniquement, sans appel IA (défaut)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.pdf:
        pdf_path = Path(args.pdf).resolve()
    else:
        pdf_path = find_default_pdf()
        if pdf_path is None:
            print("Aucun PDF trouvé dans docs/ — fournissez un chemin en argument.")
            sys.exit(1)

    if not pdf_path.exists():
        print(f"Fichier introuvable: {pdf_path}")
        sys.exit(1)

    asyncio.run(run_pipeline(pdf_path, generate=args.generate))


if __name__ == "__main__":
    main()
