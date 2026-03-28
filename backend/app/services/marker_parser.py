"""
Parser PDF via marker — produit du markdown structuré (titres, listes, tableaux).
Fallback automatique sur pymupdf (fitz) si marker échoue ou n'est pas disponible.
"""

import asyncio
import logging
import re
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Patterns de nettoyage post-marker
_REPEATED_HEADER_RE = re.compile(r"(?m)^(.{5,80})\n(?:.*\n)*?\1\n", re.MULTILINE)
_PAGE_NUMBER_RE = re.compile(r"(?m)^\s*-?\s*\d+\s*-?\s*$")
_BLANK_LINES_RE = re.compile(r"\n{3,}")


def _clean_markdown(text: str) -> str:
    """Supprime les artefacts courants: numéros de page isolés, lignes vides excessives."""
    text = _PAGE_NUMBER_RE.sub("", text)
    text = _BLANK_LINES_RE.sub("\n\n", text)
    return text.strip()


def _extract_markdown_from_rendered(rendered) -> str:
    """Extrait le texte markdown depuis l'objet rendu par marker."""
    # MarkdownOutput expose .markdown
    if hasattr(rendered, "markdown"):
        return rendered.markdown or ""
    # Fallback: essai text_from_rendered
    try:
        from marker.output import text_from_rendered  # type: ignore
        text, _, _ = text_from_rendered(rendered)
        return text or ""
    except Exception:
        return str(rendered)


def _parse_with_marker_sync(file_path: str) -> str:
    """Conversion synchrone via marker PdfConverter (chargement des modèles inclus)."""
    sys.path.insert(0, str(Path(__file__).parents[5] / "marker"))

    from marker.converters.pdf import PdfConverter  # type: ignore
    from marker.models import create_model_dict  # type: ignore

    artifact_dict = create_model_dict()
    converter = PdfConverter(artifact_dict=artifact_dict)
    rendered = converter(file_path)
    return _extract_markdown_from_rendered(rendered)


def _fallback_fitz(file_path: str) -> str:
    """
    Extraction structurée via pymupdf (fitz) — détecte titres via font size/style.
    Produit du markdown avec titres détectés, listes préservées, nettoyage des artefacts.
    """
    import fitz  # type: ignore  # pymupdf

    all_blocks: list[str] = []
    font_sizes: list[float] = []

    # Première passe: collecter les tailles de font pour détecter les seuils de titres
    with fitz.open(file_path) as doc:
        for page in doc:
            try:
                text_dict = page.get_text("dict")
                if not text_dict or "blocks" not in text_dict:
                    continue
                for block in text_dict["blocks"]:
                    if block.get("type") != 0:  # Text blocks only
                        continue
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            size = span.get("size", 0)
                            if size > 0:
                                font_sizes.append(size)
            except Exception:
                continue

    # Calculer les seuils: titre principal > 75e percentile, sous-titre > 50e percentile
    title_threshold = (
        sorted(font_sizes)[int(len(font_sizes) * 0.75)]
        if len(font_sizes) > 20
        else 14.0
    )
    subtitle_threshold = (
        sorted(font_sizes)[int(len(font_sizes) * 0.5)]
        if len(font_sizes) > 20
        else 11.0
    )

    # Deuxième passe: extraire le texte avec détection de titres
    with fitz.open(file_path) as doc:
        for page_num, page in enumerate(doc):
            try:
                text_dict = page.get_text("dict")
                if not text_dict or "blocks" not in text_dict:
                    continue

                for block in text_dict["blocks"]:
                    if block.get("type") != 0:  # Text blocks only
                        continue

                    for line in block.get("lines", []):
                        line_text = ""
                        max_font_size = 0
                        is_bold = False

                        for span in line.get("spans", []):
                            text = span.get("text", "")
                            size = span.get("size", 0)
                            flags = span.get("flags", 0)
                            max_font_size = max(max_font_size, size)
                            # Check for bold (bit 4 of flags)
                            if flags & 16:
                                is_bold = True
                            line_text += text

                        line_text = line_text.strip()
                        if not line_text:
                            continue

                        # Skip page numbers (standalone digits)
                        if re.match(r"^\s*-?\s*\d+\s*-?\s*$", line_text):
                            continue

                        # Detect title level based on font size and boldness
                        if max_font_size >= title_threshold and (is_bold or max_font_size > 13):
                            all_blocks.append(f"## {line_text}")
                        elif max_font_size >= subtitle_threshold and (is_bold or max_font_size > 11):
                            all_blocks.append(f"### {line_text}")
                        else:
                            # Preserve bullet lists and numbered lists
                            if re.match(r"^[\•\-\*]\s+", line_text):
                                cleaned = re.sub(r'^[\•\-\*]\s+', '', line_text)
                                all_blocks.append(f"- {cleaned}")
                            elif re.match(r"^\d+[\.\)]\s+", line_text):
                                num = re.match(r"^(\d+)[\.\)]\s+", line_text)
                                if num:
                                    rest = re.sub(r"^\d+[\.\)]\s+", "", line_text)
                                    all_blocks.append(f"{num.group(1)}. {rest}")
                                else:
                                    all_blocks.append(line_text)
                            else:
                                all_blocks.append(line_text)
            except Exception:
                continue

    # Join and clean
    markdown = "\n\n".join(all_blocks)

    # Remove repeated headers/footers
    markdown = _REPEATED_HEADER_RE.sub("", markdown)

    # Clean up excessive blank lines and page numbers
    markdown = _clean_markdown(markdown)

    return markdown if markdown else ""


async def parse_pdf_with_marker(file_path: str) -> str:
    """
    Parse un fichier PDF en markdown structuré via marker.

    Utilise marker (PdfConverter) pour produire du markdown avec titres (##, ###),
    listes et tableaux. Nettoie les artefacts de mise en page courants.
    Retombe sur fitz si marker échoue.

    Args:
        file_path: Chemin absolu vers le fichier PDF.

    Returns:
        Markdown structuré (ou texte brut en cas de fallback fitz).
    """
    loop = asyncio.get_event_loop()
    try:
        raw = await loop.run_in_executor(None, _parse_with_marker_sync, file_path)
        result = _clean_markdown(raw)
        if not result:
            raise ValueError("marker a retourné un contenu vide")
        logger.info("marker_parser: extraction marker OK — %d chars", len(result))
        return result
    except Exception as exc:
        logger.warning(
            "marker_parser: marker a échoué (%s), fallback fitz", exc
        )
        try:
            raw = await loop.run_in_executor(None, _fallback_fitz, file_path)
            return raw
        except Exception as fitz_exc:
            logger.error("marker_parser: fitz a aussi échoué: %s", fitz_exc)
            raise
