#!/usr/bin/env python3
"""
Batch content generation: flashcards + QCM + fiches for all documents with content.
Uses Ollama phi3:mini directly (fast, local) instead of Claude CLI.
"""

import sqlite3
import json
import re
import sys
import time
import httpx

DB_PATH = "/home/julien/Documents/IACA/data/iaca.db"
OLLAMA_URL = "http://localhost:11434"
MODEL = "phi3:mini"

# How many items per document
FLASHCARDS_PER_DOC = 5
QCM_PER_DOC = 3


def ollama_generate(prompt: str, timeout: int = 300) -> str:
    """Call Ollama and return text response."""
    resp = httpx.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        },
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"]


def extract_json_array(text: str) -> list:
    """Extract JSON array from LLM output."""
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return []


def extract_json_object(text: str) -> dict:
    """Extract JSON object from LLM output."""
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {}


def generate_flashcards(contenu: str, matiere: str, nb: int = 5) -> list:
    prompt = f"""Tu es un expert en {matiere}. Genere exactement {nb} flashcards de revision.

CONTENU:
{contenu[:2000]}

Reponds UNIQUEMENT en JSON valide:
[
  {{"question": "...", "reponse": "...", "explication": "...", "difficulte": 2}}
]
Difficulte de 1 a 5. Questions variees testant la comprehension."""

    result = ollama_generate(prompt)
    return extract_json_array(result)


def generate_qcm(contenu: str, matiere: str, nb: int = 3) -> list:
    prompt = f"""Tu es un expert en {matiere}. Genere exactement {nb} QCM.

CONTENU:
{contenu[:2000]}

Reponds UNIQUEMENT en JSON valide:
[
  {{"question": "...", "choix": ["A. ...", "B. ...", "C. ...", "D. ..."], "reponse_correcte": 0, "explication": "...", "difficulte": 2}}
]
reponse_correcte = index (0-3) du bon choix."""

    result = ollama_generate(prompt)
    return extract_json_array(result)


def generate_fiche(contenu: str, matiere: str, titre: str) -> dict:
    prompt = f"""Tu es un expert en {matiere}. Genere une fiche de revision structuree pour: {titre}

CONTENU:
{contenu[:2000]}

Reponds UNIQUEMENT en JSON valide:
{{
  "titre": "...",
  "resume": "Resume en 3 phrases",
  "sections": [
    {{"titre": "...", "contenu": "Contenu detaille 3-8 phrases"}}
  ]
}}
Genere 4 a 6 sections couvrant les points essentiels."""

    result = ollama_generate(prompt)
    return extract_json_object(result)


def get_docs_to_process(conn):
    """Get documents with content, prioritized by matiere importance."""
    c = conn.cursor()
    # Priority matieres for concours
    priority_matieres = [
        'Droit public', 'Questions sociales', 'Questions contemporaines',
        'Relations internationales', 'Économie et finances publiques',
        'Finances publiques', 'Economie',
    ]

    docs = []
    # First: priority matieres
    for mat_name in priority_matieres:
        c.execute("""
            SELECT d.id, d.titre, d.contenu_extrait, d.matiere_id, m.nom
            FROM documents d
            JOIN matieres m ON d.matiere_id = m.id
            WHERE m.nom = ? AND LENGTH(d.contenu_extrait) > 200
            ORDER BY d.id
        """, (mat_name,))
        docs.extend(c.fetchall())

    # Then: other matieres
    placeholders = ','.join('?' * len(priority_matieres))
    c.execute(f"""
        SELECT d.id, d.titre, d.contenu_extrait, d.matiere_id, m.nom
        FROM documents d
        JOIN matieres m ON d.matiere_id = m.id
        WHERE m.nom NOT IN ({placeholders}) AND LENGTH(d.contenu_extrait) > 200
        ORDER BY d.id
    """, priority_matieres)
    docs.extend(c.fetchall())

    return docs


def get_already_processed(conn):
    """Get doc IDs that already have flashcards/fiches."""
    c = conn.cursor()
    c.execute("SELECT DISTINCT document_id FROM flashcards WHERE document_id IS NOT NULL")
    fc_docs = {row[0] for row in c.fetchall()}
    c.execute("SELECT DISTINCT document_id FROM fiches WHERE document_id IS NOT NULL")
    fiche_docs = {row[0] for row in c.fetchall()}
    return fc_docs, fiche_docs


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")

    docs = get_docs_to_process(conn)
    fc_done, fiche_done = get_already_processed(conn)

    print(f"Documents exploitables: {len(docs)}")
    print(f"Deja traites: {len(fc_done)} flashcards, {len(fiche_done)} fiches")
    print(f"Ollama: {OLLAMA_URL} / {MODEL}")
    print("=" * 70)

    total_fc = 0
    total_qcm = 0
    total_fiches = 0
    errors = 0
    processed = 0

    now = time.strftime("%Y-%m-%d %H:%M:%S")

    for i, (doc_id, titre, contenu, matiere_id, matiere_nom) in enumerate(docs, 1):
        if len(contenu or "") < 200:
            continue

        already_has_fc = doc_id in fc_done
        already_has_fiche = doc_id in fiche_done

        if already_has_fc and already_has_fiche:
            continue

        print(f"[{i:4d}/{len(docs)}] {matiere_nom[:20]:20s} | {titre[:45]:45s}", end=" ", flush=True)

        # Generate flashcards
        if not already_has_fc:
            try:
                cards = generate_flashcards(contenu, matiere_nom, FLASHCARDS_PER_DOC)
                for card in cards:
                    if not card.get("question") or not card.get("reponse"):
                        continue
                    conn.execute(
                        "INSERT INTO flashcards (question, reponse, explication, difficulte, matiere_id, document_id, intervalle_jours, facteur_facilite, repetitions, prochaine_revision, created_at) VALUES (?,?,?,?,?,?,1.0,2.5,0,?,?)",
                        (card["question"], card["reponse"], card.get("explication", ""),
                         min(max(card.get("difficulte", 2), 1), 5),
                         matiere_id, doc_id, now, now)
                    )
                total_fc += len(cards)
                fc_done.add(doc_id)
                print(f"FC={len(cards)}", end=" ", flush=True)
            except Exception as e:
                print(f"FC_ERR({e.__class__.__name__})", end=" ", flush=True)
                errors += 1

        # Generate QCM (1 quiz per doc)
        if not already_has_fc:  # same condition - new docs get QCM too
            try:
                questions = generate_qcm(contenu, matiere_nom, QCM_PER_DOC)
                if questions:
                    c = conn.cursor()
                    c.execute(
                        "INSERT INTO quizzes (titre, matiere_id, document_id, created_at) VALUES (?,?,?,?)",
                        (f"QCM - {titre[:80]}", matiere_id, doc_id, now)
                    )
                    quiz_id = c.lastrowid
                    for q in questions:
                        if not q.get("question"):
                            continue
                        choix = json.dumps(q.get("choix", []), ensure_ascii=False)
                        c.execute(
                            "INSERT INTO quiz_questions (quiz_id, question, choix, reponse_correcte, explication, difficulte) VALUES (?,?,?,?,?,?)",
                            (quiz_id, q["question"], choix,
                             q.get("reponse_correcte", 0), q.get("explication", ""),
                             min(max(q.get("difficulte", 2), 1), 5))
                        )
                    total_qcm += len(questions)
                    print(f"QCM={len(questions)}", end=" ", flush=True)
            except Exception as e:
                print(f"QCM_ERR({e.__class__.__name__})", end=" ", flush=True)
                errors += 1

        # Generate fiche
        if not already_has_fiche:
            try:
                fiche = generate_fiche(contenu, matiere_nom, titre)
                if fiche.get("sections"):
                    c = conn.cursor()
                    c.execute(
                        "INSERT INTO fiches (titre, resume, matiere_id, document_id, tags, ordre, created_at) VALUES (?,?,?,?,?,0,?)",
                        (fiche.get("titre", f"Fiche - {titre}"),
                         fiche.get("resume", ""), matiere_id, doc_id, matiere_nom, now)
                    )
                    fiche_id = c.lastrowid
                    for j, s in enumerate(fiche["sections"]):
                        c.execute(
                            "INSERT INTO fiche_sections (fiche_id, titre, contenu, ordre) VALUES (?,?,?,?)",
                            (fiche_id, s.get("titre", f"Section {j+1}"),
                             s.get("contenu", ""), j)
                        )
                    total_fiches += 1
                    fiche_done.add(doc_id)
                    print(f"FICHE={len(fiche['sections'])}s", end="", flush=True)
            except Exception as e:
                print(f"FICHE_ERR({e.__class__.__name__})", end="", flush=True)
                errors += 1

        conn.commit()
        processed += 1
        print()

        # Progress every 20 docs
        if processed % 20 == 0:
            print(f"  --- Progress: {processed} docs, {total_fc} FC, {total_qcm} QCM, {total_fiches} fiches, {errors} errors ---")

    conn.close()
    print("=" * 70)
    print(f"DONE: {processed} docs traites")
    print(f"  Flashcards: +{total_fc}")
    print(f"  QCM questions: +{total_qcm}")
    print(f"  Fiches: +{total_fiches}")
    print(f"  Erreurs: {errors}")


if __name__ == "__main__":
    main()
