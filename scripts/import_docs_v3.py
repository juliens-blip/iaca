#!/usr/bin/env python3
"""
Import v3: Dynamic bulk import from Drive using matiere_mapping.json.
Creates matieres via API if missing, uploads files with dedup (title check).
Usage: python3 scripts/import_docs_v3.py [drive_root]
"""

import os
import sys
import json
import time
import io
import urllib.request
import urllib.error

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAPPING_FILE = os.path.join(SCRIPT_DIR, "matiere_mapping.json")
BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")
DRIVE_ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser(
    "~/Téléchargements/drive-download-20260226T072425Z-3-001"
)
LOG_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "logs")
LOG_FILE = os.path.join(LOG_DIR, "import_v3.log")

ALLOWED_EXT = {".pdf", ".pptx", ".docx"}


def load_mapping():
    """Load matiere_mapping.json."""
    with open(MAPPING_FILE, "r") as f:
        return json.load(f)


def api_get(path):
    """GET request to API."""
    try:
        req = urllib.request.Request(f"{BASE_URL}{path}")
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"  [ERR] GET {path}: {e}")
        return None


def api_post_json(path, data):
    """POST JSON to API."""
    body = json.dumps(data).encode()
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except Exception as e:
        return 0, str(e)


def multipart_encode(fields, files):
    """Encode multipart/form-data."""
    boundary = b"----PythonImportV3Boundary7369421"
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
    """Upload a file via POST /api/documents/upload."""
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


def get_or_create_matiere(mapping_entry, existing_matieres):
    """Find matiere by name or create it via API. Returns matiere_id."""
    name = mapping_entry["matiere"]

    # Check existing
    for m in existing_matieres:
        if m["nom"].lower().strip() == name.lower().strip():
            return m["id"], False

    # Create new
    status, resp = api_post_json("/api/matieres/", {
        "nom": name,
        "description": mapping_entry.get("description", ""),
        "couleur": mapping_entry.get("couleur", "#2563eb"),
    })
    if 200 <= status < 300:
        existing_matieres.append(resp)
        return resp["id"], True
    else:
        print(f"  [ERR] Creation matiere '{name}' echouee: HTTP {status}")
        return None, False


def get_existing_titles():
    """Get set of existing document titles for dedup."""
    docs = api_get("/api/documents/")
    if docs is None:
        return set()
    return {d.get("titre", "").lower().strip() for d in docs}


def collect_files(mapping, drive_root):
    """Collect all files to import based on mapping."""
    files = []
    mappings = mapping["mappings"]

    for entry in mappings:
        rel_path = entry["path"]
        full_dir = os.path.join(drive_root, rel_path)
        if not os.path.isdir(full_dir):
            print(f"[WARN] Dossier manquant: {full_dir}")
            continue

        for root, _, filenames in os.walk(full_dir):
            for fname in sorted(filenames):
                ext = os.path.splitext(fname)[1].lower()
                if ext not in ALLOWED_EXT:
                    continue
                full_path = os.path.join(root, fname)
                relative = os.path.relpath(full_path, full_dir)
                chapitre = os.path.dirname(relative)
                if chapitre == ".":
                    chapitre = ""
                files.append({
                    "path": full_path,
                    "mapping_entry": entry,
                    "chapitre": chapitre,
                    "tags": entry["matiere"],
                })

    # Root files
    root_matiere = mapping.get("root_files_matiere", "Documents divers")
    for fname in sorted(os.listdir(drive_root)):
        full_path = os.path.join(drive_root, fname)
        if not os.path.isfile(full_path):
            continue
        ext = os.path.splitext(fname)[1].lower()
        if ext not in ALLOWED_EXT:
            continue
        files.append({
            "path": full_path,
            "mapping_entry": {
                "matiere": root_matiere,
                "description": mapping.get("root_files_description", ""),
                "couleur": mapping.get("root_files_couleur", "#64748b"),
            },
            "chapitre": "",
            "tags": root_matiere,
        })

    return files


def main():
    os.makedirs(LOG_DIR, exist_ok=True)
    print(f"Import v3 - Drive: {DRIVE_ROOT}")
    print(f"API: {BASE_URL}")
    print(f"Mapping: {MAPPING_FILE}")
    print("-" * 60)

    # Load mapping
    mapping = load_mapping()
    print(f"Mappings: {len(mapping['mappings'])} dossiers configures")

    # Get existing matieres
    existing_matieres = api_get("/api/matieres/") or []
    print(f"Matieres existantes: {len(existing_matieres)}")

    # Get existing titles for dedup
    existing_titles = get_existing_titles()
    print(f"Documents existants: {len(existing_titles)} (pour dedup)")

    # Collect files
    files = collect_files(mapping, DRIVE_ROOT)
    print(f"Fichiers a traiter: {len(files)}")
    print("=" * 60)

    # Resolve matiere IDs
    matiere_cache = {}
    for entry in mapping["mappings"]:
        name = entry["matiere"]
        if name not in matiere_cache:
            mid, created = get_or_create_matiere(entry, existing_matieres)
            matiere_cache[name] = mid
            if created:
                print(f"  [NEW] Matiere creee: {name} (id={mid})")

    # Root files matiere
    root_name = mapping.get("root_files_matiere", "Documents divers")
    if root_name not in matiere_cache:
        mid, created = get_or_create_matiere({
            "matiere": root_name,
            "description": mapping.get("root_files_description", ""),
            "couleur": mapping.get("root_files_couleur", "#64748b"),
        }, existing_matieres)
        matiere_cache[root_name] = mid
        if created:
            print(f"  [NEW] Matiere creee: {root_name} (id={mid})")

    print(f"\nMatieres resolues: {len(matiere_cache)}")
    print("-" * 60)

    # Upload
    uploaded = 0
    skipped = 0
    failed = 0
    total = len(files)

    with open(LOG_FILE, "w") as log:
        log.write(f"Import v3 demarre: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        log.write(f"Drive: {DRIVE_ROOT}\n")
        log.write(f"Total fichiers: {total}\n\n")

        for i, f in enumerate(files, 1):
            path = f["path"]
            fname = os.path.basename(path)
            title_key = os.path.splitext(fname)[0].lower().strip()
            matiere_name = f["mapping_entry"]["matiere"]
            matiere_id = matiere_cache.get(matiere_name)

            if not matiere_id:
                failed += 1
                log.write(f"[KO] {path} - matiere '{matiere_name}' non resolue\n")
                print(f"[{i:3d}/{total}] SKIP (matiere?) {fname[:50]}")
                continue

            # Dedup check
            if title_key in existing_titles:
                skipped += 1
                log.write(f"[SKIP] {path} - titre deja en DB\n")
                if i <= 20 or i % 50 == 0:
                    print(f"[{i:3d}/{total}] SKIP (dedup) {fname[:50]}")
                continue

            size_mb = os.path.getsize(path) / 1024 / 1024
            print(f"[{i:3d}/{total}] {matiere_name[:20]:20s} {fname[:40]} ({size_mb:.1f}MB)...", end=" ", flush=True)

            status, resp = upload_file(path, matiere_id, f["chapitre"], f["tags"])

            if 200 <= status < 300:
                uploaded += 1
                doc_id = resp.get("id", "?") if isinstance(resp, dict) else "?"
                existing_titles.add(title_key)
                print(f"OK (id={doc_id})")
                log.write(f"[OK] {path} -> doc_id={doc_id}, matiere={matiere_name}\n")
            else:
                failed += 1
                err = resp if isinstance(resp, str) else json.dumps(resp)[:100]
                print(f"ERR HTTP {status}: {err[:60]}")
                log.write(f"[KO] {path} HTTP {status}: {err}\n")

        log.write(f"\nImport termine: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        log.write(f"Resultat: {uploaded} OK, {skipped} skipped, {failed} KO\n")

    print("=" * 60)
    print(f"Resultat: {uploaded} uploades, {skipped} dedupliques, {failed} erreurs")
    print(f"Log: {LOG_FILE}")

    # Summary per matiere
    print("\nRepartition matieres:")
    for name, mid in sorted(matiere_cache.items()):
        print(f"  {name}: id={mid}")


if __name__ == "__main__":
    main()
