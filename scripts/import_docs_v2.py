#!/usr/bin/env python3
"""
Import bulk des documents de cours dans l'API IACA.
Mappe chaque dossier docs/<matiere>/ au bon matiere_id.
Usage: python3 scripts/import_docs_v2.py [docs_root]
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
import mimetypes
import io

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")
DOCS_ROOT = sys.argv[1] if len(sys.argv) > 1 else "docs"
LOG_FILE = "logs/import_docs.log"

# Mapping dossier → matiere_id
MATIERE_MAP = {
    "droit-public": 1,
    "economie-finances-publiques": 2,
    "questions-contemporaines": 3,
    "questions-sociales": 4,
    "relations-internationales": 5,
}

ALLOWED_EXT = {".pdf", ".pptx", ".docx"}


def multipart_encode(fields, files):
    """Encode multipart/form-data."""
    boundary = b"----PythonImportBoundary7369421"
    body = io.BytesIO()
    for name, value in fields.items():
        body.write(b"--" + boundary + b"\r\n")
        body.write(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        body.write(str(value).encode() + b"\r\n")
    for name, (filename, data, content_type) in files.items():
        body.write(b"--" + boundary + b"\r\n")
        body.write(f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode())
        body.write(f"Content-Type: {content_type}\r\n\r\n".encode())
        body.write(data + b"\r\n")
    body.write(b"--" + boundary + b"--\r\n")
    return body.getvalue(), b"multipart/form-data; boundary=" + boundary


def upload_file(file_path, matiere_id, chapitre, tags):
    """Upload un fichier via POST /api/documents/upload."""
    filename = os.path.basename(file_path)
    ext = os.path.splitext(filename)[1].lower()
    content_type = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }.get(ext, "application/octet-stream")

    with open(file_path, "rb") as f:
        file_data = f.read()

    fields = {
        "matiere_id": str(matiere_id),
        "chapitre": chapitre,
        "tags": tags,
    }
    files = {"file": (filename, file_data, content_type)}
    body, content_type_header = multipart_encode(fields, files)

    req = urllib.request.Request(
        f"{BASE_URL}/api/documents/upload",
        data=body,
        headers={"Content-Type": content_type_header.decode()},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except Exception as e:
        return 0, str(e)


def collect_files():
    """Collecte tous les fichiers à importer avec leur matiere_id."""
    files = []
    for matiere_slug, matiere_id in MATIERE_MAP.items():
        matiere_dir = os.path.join(DOCS_ROOT, matiere_slug)
        if not os.path.isdir(matiere_dir):
            print(f"[WARN] Dossier manquant: {matiere_dir}")
            continue
        for root, _, filenames in os.walk(matiere_dir):
            for fname in sorted(filenames):
                ext = os.path.splitext(fname)[1].lower()
                if ext not in ALLOWED_EXT:
                    continue
                full_path = os.path.join(root, fname)
                relative = os.path.relpath(full_path, matiere_dir)
                chapitre = os.path.dirname(relative)
                if chapitre == ".":
                    chapitre = ""
                files.append({
                    "path": full_path,
                    "matiere_id": matiere_id,
                    "matiere_slug": matiere_slug,
                    "chapitre": chapitre,
                    "tags": matiere_slug,
                })
    return files


def main():
    os.makedirs("logs", exist_ok=True)
    files = collect_files()
    total = len(files)
    print(f"Fichiers à importer: {total}")
    print(f"Destination: {BASE_URL}")
    print("-" * 60)

    uploaded = 0
    failed = 0
    skipped = 0

    with open(LOG_FILE, "w") as log:
        log.write(f"Import démarré: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        log.write(f"Total fichiers: {total}\n\n")

        for i, f in enumerate(files, 1):
            path = f["path"]
            size_mb = os.path.getsize(path) / 1024 / 1024
            fname = os.path.basename(path)
            print(f"[{i:3d}/{total}] {f['matiere_slug']}/{fname[:50]} ({size_mb:.1f}MB)...", end=" ", flush=True)

            status, resp = upload_file(path, f["matiere_id"], f["chapitre"], f["tags"])

            if 200 <= status < 300:
                uploaded += 1
                doc_id = resp.get("id", "?") if isinstance(resp, dict) else "?"
                print(f"OK (id={doc_id})")
                log.write(f"[OK] {path} → doc_id={doc_id}\n")
            else:
                failed += 1
                err = resp if isinstance(resp, str) else json.dumps(resp)[:100]
                print(f"ERREUR HTTP {status}: {err[:80]}")
                log.write(f"[KO] {path} HTTP {status}: {err}\n")

        log.write(f"\nImport terminé: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        log.write(f"Résultat: {uploaded} OK, {failed} KO, {skipped} ignorés\n")

    print("=" * 60)
    print(f"Résultat: {uploaded} uploadés, {failed} erreurs")
    print(f"Log: {LOG_FILE}")


if __name__ == "__main__":
    main()
