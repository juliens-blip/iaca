#!/usr/bin/env python3
"""
Generate flashcards, QCM and fiches for ALL documents via backend API (uses Claude CLI).
Much faster than Ollama on low-RAM machines (~10-15s per call vs 5min).
Processes all documents with extractable content, prioritized by matiere importance.
"""

import json
import time
import sys
import urllib.request
import urllib.error
import sqlite3

BASE_URL = "http://localhost:8000"
DB_PATH = "/home/julien/Documents/IACA/data/iaca.db"

FC_PER_DOC = 5
QCM_PER_DOC = 3

# Priority order - concours matieres first, then academic
PRIORITY_MATIERES = [
    "Droit public",
    "Questions contemporaines",
    "Questions sociales",
    "Relations internationales",
    "Économie et finances publiques",
    "Finances publiques",
    "Economie",
    "Espagnol",
    "Licence 3 - Semestre 5",
    "Licence 3 - Semestre 6",
    "Licence 2 - Semestre 3",
    "Licence 2 - Semestre 4",
    "M1 Droit et legistique",
    "M1 Politique economique",
    "M1 Management et egalites",
    "Livres et manuels",
    "Licence 2 - Fiches revision",
    "TEDS (L3)",
    "Scolarite L3",
    "Documents divers",
]


def api_post(path, timeout=180):
    req = urllib.request.Request(f"{BASE_URL}{path}", method="POST", data=b"")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:200]
    except Exception as e:
        return 0, str(e)[:200]


def get_docs_to_process():
    """Get ALL docs with content that don't already have flashcards/fiches."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Get existing doc IDs with flashcards/fiches
    c.execute("SELECT DISTINCT document_id FROM flashcards WHERE document_id IS NOT NULL")
    fc_docs = {r[0] for r in c.fetchall()}
    c.execute("SELECT DISTINCT document_id FROM fiches WHERE document_id IS NOT NULL")
    fiche_docs = {r[0] for r in c.fetchall()}

    docs = []
    seen_ids = set()

    # First: priority matieres in order
    for mat_name in PRIORITY_MATIERES:
        c.execute("""
            SELECT d.id, d.titre, m.nom, m.id as matiere_id
            FROM documents d
            JOIN matieres m ON d.matiere_id = m.id
            WHERE m.nom = ? AND LENGTH(d.contenu_extrait) > 200
            ORDER BY d.id
        """, (mat_name,))

        for row in c.fetchall():
            doc_id = row[0]
            if doc_id in seen_ids:
                continue
            seen_ids.add(doc_id)
            needs_fc = doc_id not in fc_docs
            needs_fiche = doc_id not in fiche_docs
            if needs_fc or needs_fiche:
                docs.append({
                    "id": doc_id,
                    "titre": row[1],
                    "matiere": row[2],
                    "needs_fc": needs_fc,
                    "needs_fiche": needs_fiche,
                })

    # Then: any remaining matieres not in priority list
    c.execute("""
        SELECT d.id, d.titre, m.nom, m.id as matiere_id
        FROM documents d
        JOIN matieres m ON d.matiere_id = m.id
        WHERE LENGTH(d.contenu_extrait) > 200
        ORDER BY d.id
    """)
    for row in c.fetchall():
        doc_id = row[0]
        if doc_id in seen_ids:
            continue
        seen_ids.add(doc_id)
        needs_fc = doc_id not in fc_docs
        needs_fiche = doc_id not in fiche_docs
        if needs_fc or needs_fiche:
            docs.append({
                "id": doc_id,
                "titre": row[1],
                "matiere": row[2],
                "needs_fc": needs_fc,
                "needs_fiche": needs_fiche,
            })

    conn.close()
    return docs


def api_post_retry(path, max_retries=2, timeout=180):
    """POST with retry on transient errors."""
    for attempt in range(max_retries + 1):
        status, resp = api_post(path, timeout=timeout)
        if status == 0 and attempt < max_retries:
            time.sleep(5)
            continue
        if status == 500 and attempt < max_retries:
            time.sleep(3)
            continue
        return status, resp
    return status, resp


def main():
    start_time = time.time()
    docs = get_docs_to_process()
    print(f"Documents a traiter: {len(docs)}")
    print(f"API: {BASE_URL}")
    est_calls = sum(2 if d["needs_fc"] else 0 for d in docs) + sum(1 if d["needs_fiche"] else 0 for d in docs)
    print(f"Appels API estimes: ~{est_calls} (~{est_calls * 15 // 60} min)")
    print("=" * 70)

    total_fc = 0
    total_qcm = 0
    total_fiches = 0
    errors = 0

    for i, doc in enumerate(docs, 1):
        doc_id = doc["id"]
        print(f"[{i:3d}/{len(docs)}] {doc['matiere'][:20]:20s} | {doc['titre'][:45]:45s}", end=" ", flush=True)

        # Generate flashcards
        if doc["needs_fc"]:
            status, resp = api_post_retry(f"/api/recommandations/generer-flashcards/{doc_id}?nb={FC_PER_DOC}")
            if 200 <= status < 300:
                n = resp.get("generated", 0) if isinstance(resp, dict) else 0
                total_fc += n
                print(f"FC={n}", end=" ", flush=True)
            else:
                print(f"FC_ERR({status})", end=" ", flush=True)
                errors += 1

            # Generate QCM
            status, resp = api_post_retry(f"/api/recommandations/generer-qcm/{doc_id}?nb={QCM_PER_DOC}")
            if 200 <= status < 300:
                n = resp.get("questions_generated", 0) if isinstance(resp, dict) else 0
                total_qcm += n
                print(f"QCM={n}", end=" ", flush=True)
            else:
                print(f"QCM_ERR({status})", end=" ", flush=True)
                errors += 1

        # Generate fiche
        if doc["needs_fiche"]:
            status, resp = api_post_retry(f"/api/recommandations/generer-fiche/{doc_id}")
            if 200 <= status < 300:
                n = resp.get("sections_generated", 0) if isinstance(resp, dict) else 0
                total_fiches += 1
                print(f"FICHE={n}s", end="", flush=True)
            else:
                print(f"FICHE_ERR({status})", end="", flush=True)
                errors += 1

        print()

        if i % 10 == 0:
            elapsed = time.time() - start_time
            rate = i / elapsed if elapsed > 0 else 0
            remaining = (len(docs) - i) / rate if rate > 0 else 0
            print(f"  --- Progress: {i}/{len(docs)}, FC={total_fc}, QCM={total_qcm}, Fiches={total_fiches}, Err={errors}, ETA={remaining/60:.0f}min ---")

    elapsed = time.time() - start_time
    print("=" * 70)
    print(f"TERMINE en {elapsed/60:.1f} min: {len(docs)} docs traites")
    print(f"  +{total_fc} flashcards")
    print(f"  +{total_qcm} questions QCM")
    print(f"  +{total_fiches} fiches")
    print(f"  {errors} erreurs")


if __name__ == "__main__":
    main()
