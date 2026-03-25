#!/usr/bin/env python3
"""Extract structured content from PDF/DOCX source files and generate fiches+flashcards via Claude."""

import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

# Ensure backend venv packages are available
VENV_SITE = Path(__file__).resolve().parent.parent / "backend" / ".venv" / "lib"
for p in VENV_SITE.glob("python3*/site-packages"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import pdfplumber
import docx
import google.generativeai as genai

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "iaca.db"
SOURCE_DIR = Path("/home/julien/Téléchargements/drive-download-20260226T072425Z-3-001")

MATIERE_MAPPING = {
    "Droit public": 1,
    "Economie": 6,
    "Espagnol": 8,
    "Finances Publiques": 7,
    "Licence 2 Assas": None,  # sub-mapped by subfolder
    "Licence 3 assas": None,
    "Livres et manuels": 16,
    "Question contemporaine": 3,
    "Questions sociales": 4,
    "Relations internationales": 5,
    "S1_M1_Droit et légistique": 17,
    "S1_M1_Politique économique": 18,
    "S1_Management et égalités pro _(": 19,
}

L2_SUBFOLDER_MAP = {
    "DROIT L2 Semestre 3": 9,
    "DROIT L2 Semestre 4": 10,
    "Fiche de révision 2025 - 2026": 11,
}

L3_SUBFOLDER_MAP = {
    "Semestre 5": 12,
    "Semestre 6": 13,
    "TEDS": 14,
    "Scolarité": 15,
}


def extract_pdf_text(filepath: Path) -> str:
    """Extract full text from PDF using pdfplumber."""
    try:
        with pdfplumber.open(filepath) as pdf:
            pages = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages.append(text.strip())
            return "\n\n".join(pages)
    except Exception as e:
        print(f"  [WARN] PDF extraction failed for {filepath.name}: {e}")
        return ""


def extract_docx_text(filepath: Path) -> str:
    """Extract text from DOCX preserving paragraph structure."""
    try:
        doc = docx.Document(filepath)
        paragraphs = []
        for p in doc.paragraphs:
            text = p.text.strip()
            if not text:
                continue
            style = p.style.name if p.style else ""
            # Mark headings for structure detection
            if "Heading" in style or "heading" in style or "Title" in style:
                level = 1
                for ch in style:
                    if ch.isdigit():
                        level = int(ch)
                        break
                paragraphs.append(f"\n{'#' * level} {text}\n")
            else:
                paragraphs.append(text)
        return "\n".join(paragraphs)
    except Exception as e:
        print(f"  [WARN] DOCX extraction failed for {filepath.name}: {e}")
        return ""


def detect_sections(text: str, filename: str) -> list[dict]:
    """Split text into sections based on headings, numbered patterns, or thematic breaks."""
    sections = []
    lines = text.split("\n")

    # Patterns for section detection
    heading_patterns = [
        re.compile(r"^#{1,4}\s+(.+)$"),                          # Markdown headings
        re.compile(r"^(CHAPITRE|TITRE|PARTIE|SECTION|SOUS-SECTION)\s+[\dIVXLCDM]+", re.IGNORECASE),
        re.compile(r"^(I{1,3}V?|VI{0,3}|IX|X{0,3})\s*[\.\)]\s+(.+)$"),  # Roman numerals
        re.compile(r"^\d+[\.\)]\s+[A-Z]"),                       # Numbered sections starting uppercase
        re.compile(r"^[A-Z][A-Z\s]{5,}$"),                       # ALL CAPS lines (titles)
        re.compile(r"^(Article|Art\.)\s+\d+", re.IGNORECASE),    # Article references
    ]

    current_title = filename
    current_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            current_lines.append("")
            continue

        is_heading = False
        new_title = stripped

        for pat in heading_patterns:
            m = pat.match(stripped)
            if m:
                is_heading = True
                new_title = stripped.lstrip("#").strip()
                break

        if is_heading and len(current_lines) > 0:
            content = "\n".join(current_lines).strip()
            if len(content) > 100:
                sections.append({"titre": current_title[:200], "contenu": content})
            current_title = new_title[:200]
            current_lines = []
        else:
            current_lines.append(stripped)

    # Last section
    content = "\n".join(current_lines).strip()
    if len(content) > 100:
        sections.append({"titre": current_title[:200], "contenu": content})

    # If no sections detected, treat whole text as one section
    if not sections and len(text.strip()) > 100:
        sections.append({"titre": filename, "contenu": text.strip()})

    return sections


def resolve_matiere_id(folder_name: str, subfolder: str = "") -> int:
    """Resolve matiere_id from folder/subfolder names."""
    if folder_name in MATIERE_MAPPING and MATIERE_MAPPING[folder_name] is not None:
        return MATIERE_MAPPING[folder_name]
    if "Licence 2" in folder_name:
        return L2_SUBFOLDER_MAP.get(subfolder, 11)  # default to fiches revision
    if "Licence 3" in folder_name:
        return L3_SUBFOLDER_MAP.get(subfolder, 12)  # default to S5
    return 20  # Documents divers


def _load_gemini():
    """Init Gemini client from .env GOOGLE_API_KEY."""
    from pathlib import Path as _Path
    env_path = _Path(__file__).resolve().parent.parent / ".env"
    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key and env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("GOOGLE_API_KEY="):
                api_key = line.split("=", 1)[1].strip()
                break
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY manquante dans .env")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.0-flash")

_GEMINI_MODEL = None

def call_claude(prompt: str, max_retries: int = 2) -> str:
    """Generate content via Gemini API (remplace Claude CLI)."""
    global _GEMINI_MODEL
    if _GEMINI_MODEL is None:
        _GEMINI_MODEL = _load_gemini()
    for attempt in range(max_retries + 1):
        try:
            response = _GEMINI_MODEL.generate_content(
                prompt,
                generation_config={"temperature": 0.3, "max_output_tokens": 4096},
            )
            text = response.text.strip() if response.text else ""
            if text:
                return text
        except Exception as e:
            print(f"  [WARN] Gemini attempt {attempt+1}: {e}")
            if attempt < max_retries:
                time.sleep(3)
    return ""


def parse_json_response(text: str) -> dict | list | None:
    """Extract JSON from Claude response, handling code fences."""
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*$", "", text)
    text = text.strip()

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try finding JSON object/array
    for start_char, end_char in [("{", "}"), ("[", "]")]:
        start = text.find(start_char)
        if start == -1:
            continue
        depth = 0
        for i in range(start, len(text)):
            if text[i] == start_char:
                depth += 1
            elif text[i] == end_char:
                depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    break
    return None


def generate_fiche_for_section(section_text: str, matiere_nom: str, doc_titre: str, section_titre: str) -> dict | None:
    """Generate a detailed fiche for a document section via Claude."""
    truncated = section_text[:6000]
    prompt = f"""Tu es un professeur préparant des fiches de révision pour un étudiant en droit/économie/sciences politiques (préparation concours IACA/INSP).

Matière : {matiere_nom}
Document : {doc_titre}
Section : {section_titre}

À partir du texte ci-dessous, crée une fiche de révision structurée. Réponds UNIQUEMENT en JSON valide, sans texte avant/après :

{{
  "titre": "titre précis de la fiche (pas générique)",
  "resume": "résumé en 2-3 phrases des points clés",
  "sections": [
    {{"titre": "sous-titre thématique", "contenu": "développement détaillé avec définitions, dates, jurisprudence, articles de loi, exemples concrets (minimum 250 caractères par section)"}},
    ...
  ]
}}

Règles :
- Minimum 4 sections, maximum 8
- Chaque section doit contenir des informations factuelles précises (dates, articles, arrêts, chiffres)
- Pas de contenu générique type "Ce thème est important"
- Le titre doit refléter le contenu exact, pas être vague

TEXTE SOURCE :
{truncated}"""

    response = call_claude(prompt)
    if not response:
        return None
    return parse_json_response(response)


def generate_flashcards_for_section(section_text: str, matiere_nom: str, doc_titre: str, nb: int = 5) -> list | None:
    """Generate flashcards for a document section via Claude."""
    truncated = section_text[:5000]
    prompt = f"""Tu es un professeur créant des flashcards de révision pour un étudiant préparant le concours IACA/INSP.

Matière : {matiere_nom}
Document : {doc_titre}

Crée exactement {nb} flashcards à partir du texte ci-dessous. Réponds UNIQUEMENT en JSON valide (array) :

[
  {{
    "question": "question précise testant une connaissance factuelle (article, date, définition, jurisprudence)",
    "reponse": "réponse complète et précise",
    "explication": "contexte ou développement supplémentaire",
    "difficulte": 3
  }},
  ...
]

Règles :
- Questions factuelles et précises (pas "Qu'est-ce que le droit public ?")
- Tester des connaissances vérifiables : articles de loi, dates d'arrêts, définitions juridiques, chiffres clés
- Difficulté de 1 (basique) à 5 (expert)
- Varier les types : définition, date, article, jurisprudence, principe, exception

TEXTE SOURCE :
{truncated}"""

    response = call_claude(prompt)
    if not response:
        return None
    result = parse_json_response(response)
    return result if isinstance(result, list) else None


def get_db():
    """Get SQLite connection with WAL mode for concurrent writes."""
    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.row_factory = sqlite3.Row
    return conn


def get_matiere_nom(conn, matiere_id: int) -> str:
    """Get matiere name by ID."""
    row = conn.execute("SELECT nom FROM matieres WHERE id = ?", (matiere_id,)).fetchone()
    return row["nom"] if row else "Inconnue"


def find_or_create_document(conn, titre: str, filepath: str, matiere_id: int, contenu: str) -> int:
    """Find existing document or create new one. Update contenu_extrait if better."""
    row = conn.execute("SELECT id, LENGTH(contenu_extrait) as len FROM documents WHERE titre = ? AND matiere_id = ?",
                       (titre, matiere_id)).fetchone()
    if row:
        doc_id = row["id"]
        old_len = row["len"] or 0
        if len(contenu) > old_len:
            conn.execute("UPDATE documents SET contenu_extrait = ?, fichier_path = ? WHERE id = ?",
                         (contenu, filepath, doc_id))
            conn.commit()
        return doc_id

    conn.execute(
        "INSERT INTO documents (titre, fichier_path, type_fichier, contenu_extrait, matiere_id) VALUES (?, ?, ?, ?, ?)",
        (titre, filepath, Path(filepath).suffix.lstrip("."), contenu, matiere_id),
    )
    conn.commit()
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def insert_fiche(conn, fiche_data: dict, matiere_id: int, document_id: int) -> int | None:
    """Insert a fiche + sections into DB. Skip if duplicate title for same matiere."""
    titre = fiche_data.get("titre", "")[:500]
    if not titre:
        return None

    existing = conn.execute("SELECT id FROM fiches WHERE titre = ? AND matiere_id = ?", (titre, matiere_id)).fetchone()
    if existing:
        return None

    resume = fiche_data.get("resume", "")[:2000]
    conn.execute(
        "INSERT INTO fiches (titre, resume, matiere_id, document_id, ordre) VALUES (?, ?, ?, ?, 0)",
        (titre, resume, matiere_id, document_id),
    )
    fiche_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    for i, sec in enumerate(fiche_data.get("sections", [])):
        sec_titre = sec.get("titre", f"Section {i+1}")[:500]
        sec_contenu = sec.get("contenu", "")
        if len(sec_contenu) < 50:
            continue
        conn.execute(
            "INSERT INTO fiche_sections (fiche_id, titre, contenu, ordre) VALUES (?, ?, ?, ?)",
            (fiche_id, sec_titre, sec_contenu, i),
        )

    conn.commit()
    return fiche_id


def insert_flashcards(conn, cards: list, matiere_id: int, document_id: int) -> int:
    """Insert flashcards into DB. Skip duplicates by question text."""
    inserted = 0
    for card in cards:
        question = card.get("question", "").strip()
        if not question or len(question) < 10:
            continue
        existing = conn.execute("SELECT id FROM flashcards WHERE question = ? AND matiere_id = ?",
                                (question, matiere_id)).fetchone()
        if existing:
            continue
        conn.execute(
            "INSERT INTO flashcards (question, reponse, explication, difficulte, matiere_id, document_id) VALUES (?, ?, ?, ?, ?, ?)",
            (question, card.get("reponse", ""), card.get("explication", ""),
             min(max(card.get("difficulte", 3), 1), 5), matiere_id, document_id),
        )
        inserted += 1
    conn.commit()
    return inserted


def process_file(filepath: Path, matiere_id: int, conn, stats: dict, generate: bool = True):
    """Process a single file: extract, detect sections, generate content."""
    titre = filepath.stem
    ext = filepath.suffix.lower()

    if ext == ".pdf":
        text = extract_pdf_text(filepath)
    elif ext in (".docx", ".doc"):
        text = extract_docx_text(filepath)
    else:
        stats["skipped"] += 1
        return

    if len(text) < 100:
        print(f"  [SKIP] Too short ({len(text)} chars): {filepath.name}")
        stats["skipped"] += 1
        return

    doc_id = find_or_create_document(conn, titre, str(filepath), matiere_id, text)
    matiere_nom = get_matiere_nom(conn, matiere_id)
    stats["docs_processed"] += 1

    sections = detect_sections(text, titre)
    print(f"  [{ext}] {titre}: {len(text)} chars, {len(sections)} sections")

    if not generate:
        return

    # Generate fiche for each meaningful section
    for sec in sections:
        if len(sec["contenu"]) < 200:
            continue
        fiche_data = generate_fiche_for_section(sec["contenu"], matiere_nom, titre, sec["titre"])
        if fiche_data:
            fid = insert_fiche(conn, fiche_data, matiere_id, doc_id)
            if fid:
                stats["fiches_created"] += 1
                print(f"    + Fiche: {fiche_data.get('titre', '?')[:60]}")

    # Generate flashcards (batch per document, proportional to size)
    nb_cards = min(max(len(text) // 1000, 3), 10)
    cards = generate_flashcards_for_section(text[:8000], matiere_nom, titre, nb_cards)
    if cards:
        n = insert_flashcards(conn, cards, matiere_id, doc_id)
        stats["flashcards_created"] += n
        print(f"    + {n} flashcards")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Extract and generate content from source documents")
    parser.add_argument("--dry-run", action="store_true", help="Extract only, no Claude generation")
    parser.add_argument("--folder", type=str, help="Process only this top-level folder")
    parser.add_argument("--limit", type=int, default=0, help="Max files to process (0=all)")
    parser.add_argument("--matiere-id", type=int, help="Force a specific matiere_id")
    args = parser.parse_args()

    conn = get_db()
    stats = {"docs_processed": 0, "fiches_created": 0, "flashcards_created": 0, "skipped": 0, "errors": 0}
    processed = 0

    # Also handle root-level files
    all_targets = []

    for item in sorted(SOURCE_DIR.iterdir()):
        if item.is_file() and item.suffix.lower() in (".pdf", ".docx", ".doc", ".pptx"):
            mid = args.matiere_id or 20
            all_targets.append((item, mid))
        elif item.is_dir():
            folder_name = item.name.strip()
            if args.folder and folder_name != args.folder.strip():
                continue
            for fpath in sorted(item.rglob("*")):
                if not fpath.is_file():
                    continue
                if fpath.suffix.lower() not in (".pdf", ".docx", ".doc"):
                    continue
                # Determine subfolder for L2/L3
                rel = fpath.relative_to(item)
                subfolder = rel.parts[0] if len(rel.parts) > 1 else ""
                mid = args.matiere_id or resolve_matiere_id(folder_name, subfolder)
                all_targets.append((fpath, mid))

    print(f"Found {len(all_targets)} files to process")

    for fpath, mid in all_targets:
        if args.limit and processed >= args.limit:
            break
        try:
            process_file(fpath, mid, conn, stats, generate=not args.dry_run)
            processed += 1
        except Exception as e:
            print(f"  [ERROR] {fpath.name}: {e}")
            stats["errors"] += 1

    conn.close()

    print(f"\n{'='*60}")
    print(f"RESULTS:")
    print(f"  Documents processed: {stats['docs_processed']}")
    print(f"  Fiches created:      {stats['fiches_created']}")
    print(f"  Flashcards created:  {stats['flashcards_created']}")
    print(f"  Skipped:             {stats['skipped']}")
    print(f"  Errors:              {stats['errors']}")


if __name__ == "__main__":
    main()
