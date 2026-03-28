#!/usr/bin/env python3
"""Re-extract content from documents with empty/minimal content using marker."""

import sqlite3
import asyncio
from pathlib import Path

# Try to import marker_pdf - if not available, use pypdf as fallback
try:
    import marker
    HAS_MARKER = True
except ImportError:
    HAS_MARKER = False
    print("⚠️ marker not installed, attempting fallback with pypdf")

REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = REPO_ROOT / "data" / "iaca.db"

# List of document IDs with empty content (≤120 chars)
EMPTY_DOC_IDS = [16, 259, 266, 267, 693, 702, 722, 724, 1046, 1373, 1401, 1441, 1443, 1449]

def get_empty_docs():
    """Fetch docs with minimal content from DB."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT id, titre, fichier_path, contenu_extrait
        FROM documents
        WHERE length(trim(contenu_extrait)) <= 120
        ORDER BY id
    """)
    docs = c.fetchall()
    conn.close()
    return docs

def extract_with_marker(file_path: str) -> str:
    """Extract text from file using marker (PDF) or fallback."""
    path = Path(file_path)

    if not path.exists():
        return f"[ERREUR] Fichier introuvable: {file_path}"

    try:
        if path.suffix.lower() == '.pdf':
            # Try marker first
            if HAS_MARKER:
                try:
                    result = marker.mark([str(path)])
                    if result and len(result) > 0:
                        # marker returns a list of results
                        text = result[0].get('text', '') if isinstance(result[0], dict) else str(result[0])
                        return text[:5000]  # Cap at 5000 chars
                except Exception as e:
                    print(f"⚠️ marker failed for {path.name}: {e}, trying pypdf")

            # Fallback: pypdf
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(path)
                text = ""
                for page in reader.pages[:10]:  # First 10 pages
                    text += page.extract_text()
                return text[:5000] if text else "[PDF vide - pas de texte extractible]"
            except Exception as e:
                return f"[ERREUR pypdf] {str(e)}"

        elif path.suffix.lower() in ['.docx', '.doc']:
            # Try python-docx
            try:
                from docx import Document
                doc = Document(path)
                text = "\n".join([para.text for para in doc.paragraphs])
                return text[:5000] if text else "[DOCX vide - pas de texte extractible]"
            except Exception as e:
                return f"[ERREUR docx] {str(e)}"

        else:
            return f"[FORMAT NON SUPPORTÉ] {path.suffix}"

    except Exception as e:
        return f"[ERREUR GÉNÉRAL] {str(e)}"

def update_document_content(doc_id: int, new_content: str):
    """Update document content in DB."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        UPDATE documents
        SET contenu_extrait = ?
        WHERE id = ?
    """, (new_content, doc_id))
    conn.commit()
    conn.close()

def main():
    """Main extraction loop."""
    docs = get_empty_docs()

    print(f"\n{'='*100}")
    print(f"RÉEXTRACTION DOCUMENTS VIDES ({len(docs)} docs)")
    print(f"{'='*100}\n")

    success_count = 0
    fail_count = 0

    for idx, (doc_id, titre, fichier_path, old_content) in enumerate(docs, 1):
        print(f"\n[{idx}/{len(docs)}] Doc #{doc_id}: {titre}")
        print(f"  Fichier: {fichier_path}")
        print(f"  Ancien contenu: {len(old_content)} chars")

        # Extract new content
        new_content = extract_with_marker(fichier_path)
        new_len = len(new_content.strip())

        # Check if extraction was successful
        if new_len > 120 and not new_content.startswith("["):
            print(f"  ✅ SUCCÈS: {new_len} chars extraits")
            update_document_content(doc_id, new_content)
            success_count += 1
        else:
            print(f"  ❌ ÉCHEC: {new_content[:80]}...")
            fail_count += 1

    print(f"\n{'='*100}")
    print(f"RÉSUMÉ")
    print(f"{'='*100}")
    print(f"Succès: {success_count}/{len(docs)}")
    print(f"Échecs: {fail_count}/{len(docs)}")

    if success_count > 0:
        print(f"\n✅ {success_count} documents réextraits avec succès")
    else:
        print(f"\n⚠️ Aucun document n'a pu être réextrait")
        print("Note: Certains fichiers peuvent être des schémas/diagrams avec peu de texte")

if __name__ == "__main__":
    main()
