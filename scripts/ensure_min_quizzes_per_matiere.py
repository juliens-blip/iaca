#!/usr/bin/env python3
"""
Ensure each matiere with documents has at least N quizzes.

This fills only missing quiz count (not question count) using existing flashcards
as deterministic material, to avoid empty/under-covered subjects.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = REPO_ROOT / "data" / "iaca.db"


def sanitize_text(text: str, max_len: int) -> str:
    cleaned = re.sub(r"\s+", " ", (text or "").strip())
    cleaned = cleaned.replace("\x00", "")
    return cleaned[:max_len]


def build_question(base_question: str, matiere: str, idx: int) -> str:
    question = sanitize_text(base_question, 240)
    if len(question) >= 20:
        return question
    return f"En {matiere}, quelle affirmation est correcte (serie {idx}) ?"


def build_choices(correct: str, distractors: list[str], rng: random.Random) -> tuple[list[str], int]:
    options = [sanitize_text(correct, 180)]
    for item in distractors[:3]:
        options.append(sanitize_text(item, 180))

    while len(options) < 4:
        options.append(f"Option de consolidation {len(options) + 1}")

    # Prefix A/B/C/D for compatibility with existing rendering.
    rng.shuffle(options)
    correct_index = options.index(sanitize_text(correct, 180))
    formatted = [f"{letter}. {text}" for letter, text in zip(["A", "B", "C", "D"], options)]
    return formatted, correct_index


def main() -> int:
    parser = argparse.ArgumentParser(description="Ensure minimum quizzes per matiere")
    parser.add_argument("--db-path", default=str(DEFAULT_DB))
    parser.add_argument("--min-quizzes", type=int, default=25)
    parser.add_argument("--apply", action="store_true", help="Apply DB writes")
    parser.add_argument("--matiere", type=int, default=0, help="Restrict to one matiere_id")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    query = """
        SELECT m.id, m.nom,
               (SELECT COUNT(*) FROM documents d WHERE d.matiere_id = m.id) AS docs,
               (SELECT COUNT(*) FROM quizzes q WHERE q.matiere_id = m.id) AS quizzes
        FROM matieres m
        WHERE (SELECT COUNT(*) FROM documents d WHERE d.matiere_id = m.id) > 0
    """
    rows = cur.execute(query).fetchall()

    summary: list[tuple[int, str, int, int, int]] = []

    for row in rows:
        matiere_id = row["id"]
        matiere_name = row["nom"]
        docs_count = row["docs"]
        current_quizzes = row["quizzes"]

        if args.matiere and matiere_id != args.matiere:
            continue
        if current_quizzes >= args.min_quizzes:
            summary.append((matiere_id, matiere_name, current_quizzes, 0, docs_count))
            continue

        needed = args.min_quizzes - current_quizzes
        flashcards = cur.execute(
            """
            SELECT id, question, reponse, explication
            FROM flashcards
            WHERE matiere_id = ?
              AND LENGTH(TRIM(COALESCE(question, ''))) > 10
              AND LENGTH(TRIM(COALESCE(reponse, ''))) > 10
            ORDER BY id
            """,
            (matiere_id,),
        ).fetchall()

        if len(flashcards) < 4:
            summary.append((matiere_id, matiere_name, current_quizzes, 0, docs_count))
            continue

        rng = random.Random(10_000 + matiere_id)
        created = 0
        now = datetime.now(timezone.utc).isoformat()

        for i in range(needed):
            base_index = (i * 4) % len(flashcards)
            batch = [flashcards[(base_index + j) % len(flashcards)] for j in range(4)]

            quiz_title = f"Quiz renforcement {matiere_name} #{current_quizzes + i + 1}"
            if args.apply:
                cur.execute(
                    "INSERT INTO quizzes (titre, matiere_id, document_id, created_at) VALUES (?, ?, NULL, ?)",
                    (quiz_title, matiere_id, now),
                )
                quiz_id = cur.lastrowid
            else:
                quiz_id = -1

            for q_idx, card in enumerate(batch, start=1):
                correct_answer = sanitize_text(card["reponse"], 180)
                distract_pool = [
                    sanitize_text(other["reponse"], 180)
                    for other in flashcards
                    if other["id"] != card["id"] and sanitize_text(other["reponse"], 180) != correct_answer
                ]
                rng.shuffle(distract_pool)
                choix, reponse_correcte = build_choices(correct_answer, distract_pool, rng)
                question_text = build_question(card["question"], matiere_name, q_idx)
                explication = sanitize_text(card["explication"] or "", 300) or "Question construite a partir de flashcards existantes."

                if args.apply:
                    cur.execute(
                        """
                        INSERT INTO quiz_questions (quiz_id, question, choix, reponse_correcte, explication, difficulte)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (quiz_id, question_text, json.dumps(choix, ensure_ascii=False), reponse_correcte, explication, 2),
                    )

            created += 1

        summary.append((matiere_id, matiere_name, current_quizzes, created, docs_count))

    if args.apply:
        conn.commit()
    conn.close()

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"mode={mode} min_quizzes={args.min_quizzes}")
    for mid, name, existing, created, docs in sorted(summary, key=lambda x: x[0]):
        print(
            f"matiere_id={mid} name={name} docs={docs} "
            f"existing={existing} created={created} final={existing + created}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
