#!/usr/bin/env python3
"""
Fix generic flashcard prompts like "Consolidation ..." into notion-based questions.

Idempotence:
- Only rows where question LIKE 'Consolidation %' are considered.
- Once corrected, the question no longer matches that pattern, so reruns do not
  re-edit corrected rows.

Safety:
- If a case is judged unreliable, it is skipped and counted with a reason.
"""

from __future__ import annotations

import argparse
import re
import sqlite3
import unicodedata
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = REPO_ROOT / "data" / "iaca.db"

GENERIC_PREFIX = "Consolidation "

STRONG_NOISE_PATTERNS = [
    re.compile(r"\bnote de delib[ée]ration\b", re.IGNORECASE),
    re.compile(r"\bnote de correction\b", re.IGNORECASE),
    re.compile(r"\bcorrecteur\b", re.IGNORECASE),
    re.compile(r"\bappr[eé]ciation\b", re.IGNORECASE),
    re.compile(r"\bbar[eè]me\b", re.IGNORECASE),
    re.compile(r"\bquiz+let\b", re.IGNORECASE),
    re.compile(r"\bhttps?://|\bwww\.", re.IGNORECASE),
    re.compile(r"\bquestion\s*\d+\b", re.IGNORECASE),
    re.compile(r"\b/\s*20\b", re.IGNORECASE),
]

STRUCTURE_PATTERN = re.compile(
    r"\b(section|partie|chapitre|titre)\s*\d+\b",
    re.IGNORECASE,
)

STOPWORDS = {
    "ainsi",
    "alors",
    "apres",
    "avant",
    "avec",
    "cette",
    "comme",
    "dans",
    "des",
    "donc",
    "elle",
    "elles",
    "entre",
    "etre",
    "leur",
    "leurs",
    "mais",
    "meme",
    "nous",
    "pour",
    "sans",
    "ses",
    "son",
    "sont",
    "sur",
    "tout",
    "tous",
    "toutes",
    "une",
    "vos",
    "vous",
    "etre",
    "avoir",
    "aux",
    "ces",
    "ceci",
    "cela",
    "les",
    "des",
    "qui",
    "que",
    "est",
    "sont",
    "dans",
    "pour",
    "avec",
    "sans",
    "par",
    "entre",
    "matiere",
    "droit",
    "cours",
    "licence",
    "semestre",
    "question",
    "questions",
    "correction",
    "corrige",
    "corrigee",
    "notes",
    "note",
    "points",
    "point",
    "partie",
    "section",
    "chapitre",
    "titre",
    "document",
    "sujet",
    "quizlet",
    "quizzlet",
}

GENERIC_LABEL_WORDS = {
    "partie",
    "section",
    "chapitre",
    "titre",
    "annexe",
    "question",
    "correction",
    "notes",
    "note",
    "bareme",
    "points",
    "devoir",
    "sujet",
    "document",
}

CONCEPT_MARKERS = (
    " est ",
    " designe ",
    " design",
    " definit ",
    " definition ",
    " principe ",
    " notion ",
    " implique ",
    " permet ",
    " vise ",
    " constitue ",
    " correspond ",
)


def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def ascii_lower(text: str) -> str:
    return strip_accents(text).lower()


def extract_topics(text: str, limit: int = 4) -> list[str]:
    words = re.findall(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'’-]{2,}", text.lower())
    topics: list[str] = []
    seen: set[str] = set()
    for raw in words:
        token = raw.replace("’", "'").strip("'")
        if len(token) < 3:
            continue
        if token in STOPWORDS:
            continue
        if token in seen:
            continue
        seen.add(token)
        topics.append(token)
        if len(topics) >= limit:
            break
    return topics


def sanitize_label(candidate: str) -> str:
    label = normalize_spaces(candidate)
    label = re.sub(r"^[\-\*\u2022]+", "", label).strip()
    label = re.sub(r"^\d+\)?\s*", "", label).strip()
    label = label.strip(" .,:;!?'\"-")
    return normalize_spaces(label)


def is_plausible_label(candidate: str) -> bool:
    label = sanitize_label(candidate)
    if len(label) < 6 or len(label) > 90:
        return False

    letters = [ch for ch in label if ch.isalpha()]
    digits = [ch for ch in label if ch.isdigit()]
    if len(letters) < 6:
        return False
    if digits and (len(digits) / max(1, len(letters) + len(digits))) > 0.15:
        return False

    lower_ascii = ascii_lower(label)
    words = re.findall(r"[a-z][a-z'-]{2,}", lower_ascii)
    if not words:
        return False
    if all(w in GENERIC_LABEL_WORDS for w in words):
        return False
    if not any(w not in STOPWORDS for w in words):
        return False
    return True


def extract_label_from_response(clean_response: str) -> str | None:
    quote_match = re.search(r"[\"'«“](.{4,100}?)[\"'»”]", clean_response)
    if quote_match:
        quoted = sanitize_label(quote_match.group(1))
        if is_plausible_label(quoted):
            return quoted

    prefix_match = re.match(r"^([^.!?]{4,100})\s*[:\-]\s+.+$", clean_response)
    if prefix_match:
        prefix = sanitize_label(prefix_match.group(1))
        if is_plausible_label(prefix):
            return prefix

    definition_match = re.search(
        r"\b(?:le|la|l'|l’)\s+([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'’ -]{3,70})\s+est\b",
        clean_response,
        flags=re.IGNORECASE,
    )
    if definition_match:
        candidate = sanitize_label(definition_match.group(1))
        if is_plausible_label(candidate):
            return candidate

    return None


def classify_reliability(clean_response: str) -> tuple[bool, str]:
    if len(clean_response) < 30:
        return False, "response_too_short"

    for pattern in STRONG_NOISE_PATTERNS:
        if pattern.search(clean_response):
            return False, "noise_pattern_detected"

    alnum = [ch for ch in clean_response if ch.isalnum()]
    letters = [ch for ch in clean_response if ch.isalpha()]
    digits = [ch for ch in clean_response if ch.isdigit()]
    if len(letters) < 18:
        return False, "not_enough_letters"
    if len(letters) / max(1, len(alnum)) < 0.55:
        return False, "low_letter_ratio"
    if len(digits) / max(1, len(alnum)) > 0.30:
        return False, "high_digit_ratio"

    uppercase_letters = [ch for ch in letters if ch.isupper()]
    if len(uppercase_letters) / max(1, len(letters)) > 0.70:
        return False, "mostly_uppercase"

    structure_hits = len(STRUCTURE_PATTERN.findall(clean_response))
    response_ascii = ascii_lower(clean_response)
    has_concept_marker = any(marker in response_ascii for marker in CONCEPT_MARKERS)
    if structure_hits >= 2 and not has_concept_marker:
        return False, "table_of_contents_like"

    topics = extract_topics(clean_response, limit=4)
    if len(topics) < 2:
        return False, "insufficient_topics"
    if not has_concept_marker and len(topics) < 3:
        return False, "insufficient_concept_signal"

    return True, "ok"


def build_notion_question(matiere_nom: str, label: str) -> str:
    subject = normalize_spaces(matiere_nom) or "cette matiere"
    notion = sanitize_label(label)
    if len(notion) > 92:
        notion = notion[:92].rstrip(" ,;:-")
    return f"En {subject}, quelle définition faut-il retenir à propos de {notion} ?"


def fix_generic_flashcards(
    db_path: Path,
    dry_run: bool,
    max_examples: int,
) -> dict:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        """
        SELECT f.id, f.question, f.reponse, COALESCE(m.nom, 'cette matiere') AS matiere_nom
        FROM flashcards f
        LEFT JOIN matieres m ON m.id = f.matiere_id
        WHERE f.question LIKE ?
        ORDER BY f.id ASC
        """,
        (f"{GENERIC_PREFIX}%",),
    ).fetchall()

    updated_rows: list[tuple[str, int]] = []
    skip_reasons: Counter[str] = Counter()
    examples: list[dict] = []

    for row in rows:
        before_question = row["question"] or ""
        response_text = normalize_spaces(row["reponse"] or "")

        reliable, reason = classify_reliability(response_text)
        if not reliable:
            skip_reasons[reason] += 1
            continue

        label = extract_label_from_response(response_text)
        if not label:
            skip_reasons["label_not_found"] += 1
            continue
        if not is_plausible_label(label):
            skip_reasons["label_not_plausible"] += 1
            continue

        new_question = build_notion_question(row["matiere_nom"], label)
        if len(new_question) < 24:
            skip_reasons["generated_question_too_short"] += 1
            continue
        if new_question == before_question:
            skip_reasons["already_normalized"] += 1
            continue

        updated_rows.append((new_question, row["id"]))
        if len(examples) < max_examples:
            examples.append(
                {
                    "id": row["id"],
                    "matiere": row["matiere_nom"],
                    "before": before_question,
                    "after": new_question,
                }
            )

    if not dry_run and updated_rows:
        conn.executemany("UPDATE flashcards SET question=? WHERE id=?", updated_rows)
        conn.commit()
    else:
        conn.rollback()

    conn.close()

    total_targeted = len(rows)
    corrected = len(updated_rows)
    skipped = total_targeted - corrected
    return {
        "db_path": str(db_path),
        "dry_run": dry_run,
        "total_targeted": total_targeted,
        "corrected": corrected,
        "skipped": skipped,
        "skip_reasons": skip_reasons,
        "examples": examples,
    }


def print_report(report: dict) -> None:
    print("fix_generic_flashcards.py report")
    print(f"database: {report['db_path']}")
    print(f"dry_run: {report['dry_run']}")
    print(f"targeted: {report['total_targeted']}")
    print(f"corrected: {report['corrected']}")
    print(f"skipped: {report['skipped']}")
    print("")
    print("skip_reasons:")
    if report["skip_reasons"]:
        for reason, count in report["skip_reasons"].most_common():
            print(f"- {reason}: {count}")
    else:
        print("- none")

    print("")
    print("examples_before_after:")
    examples = report.get("examples", [])
    if not examples:
        print("- none")
        return
    for idx, ex in enumerate(examples, start=1):
        print(f"{idx}. id={ex['id']} | matiere={ex['matiere']}")
        print(f"   before: {ex['before']}")
        print(f"   after:  {ex['after']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Transform generic flashcard questions (Consolidation ...) into "
            "notion-based questions using reponse + matiere with reliability guards."
        )
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB_PATH,
        help=f"SQLite database path (default: {DEFAULT_DB_PATH})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Analyze only, do not write changes to DB.",
    )
    parser.add_argument(
        "--examples",
        type=int,
        default=10,
        help="Number of before/after examples to print (default: 10).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = fix_generic_flashcards(
        db_path=args.db,
        dry_run=args.dry_run,
        max_examples=max(0, args.examples),
    )
    print_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
