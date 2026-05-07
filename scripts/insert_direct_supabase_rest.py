#!/usr/bin/env python3
"""Insert assistant-authored fiches and flashcards into Supabase via REST.

Input is JSON on stdin:
{
  "documents": [
    {
      "document_id": 123,
      "fiche": {"titre": "...", "resume": "...", "sections": [...]},
      "flashcards": [{"question": "...", "reponse": "...", "explication": "...", "difficulte": 3}],
      "quiz": {
        "titre": "...",
        "questions": [
          {
            "question": "...",
            "choix": ["A. ...", "B. ...", "C. ...", "D. ..."],
            "reponse_correcte": 0,
            "explication": "...",
            "difficulte": 2
          }
        ]
      }
    }
  ]
}
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from typing import Any
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(REPO_ROOT, "backend")
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, REPO_ROOT)

from app.services.claude_service import _validate_fiche_payload, _validate_flashcard
from scripts.generate_full_coverage import _normalize_question
from scripts.generate_supabase_quality_coverage import normalized


SUPABASE_URL = (
    os.getenv("SUPABASE_URL")
    or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    or "https://hssjsvsvenfawegmhecx.supabase.co"
).rstrip("/")
SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
BASE_URL = f"{SUPABASE_URL}/rest/v1"


def request(
    method: str,
    path: str,
    *,
    body: Any | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, Any, dict[str, str]]:
    if not SERVICE_ROLE_KEY:
        raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY is required")
    data = None
    req_headers = {
        "apikey": SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
    }
    if headers:
        req_headers.update(headers)
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        req_headers.setdefault("Content-Type", "application/json")
    req = Request(f"{BASE_URL}/{path.lstrip('/')}", data=data, headers=req_headers, method=method)
    try:
        with urlopen(req) as resp:
            raw = resp.read()
            content_type = resp.headers.get("Content-Type", "")
            parsed: Any = raw.decode("utf-8") if raw else ""
            if raw and "json" in content_type:
                parsed = json.loads(raw)
            return resp.status, parsed, dict(resp.headers.items())
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path} failed: {exc.code} {raw}") from exc


def fetch_doc(document_id: int) -> dict[str, Any] | None:
    path = (
        "documents"
        f"?select=id,titre,matiere_id,chapitre&id=eq.{document_id}&limit=1"
    )
    _, payload, _ = request("GET", path)
    if not payload:
        return None
    doc = payload[0]
    fiche_count = fetch_count("fiches", f"document_id=eq.{document_id}")
    fc_count = fetch_count("flashcards", f"document_id=eq.{document_id}")
    matiere_nom = fetch_matiere_name(int(doc.get("matiere_id") or 0))
    doc["fiches"] = fiche_count
    doc["flashcards"] = fc_count
    doc["matiere"] = matiere_nom
    return doc


def fetch_count(table: str, filters: str) -> int:
    path = f"{table}?select=id&{filters}&limit=1"
    _, payload, headers = request("GET", path, headers={"Prefer": "count=exact"})
    content_range = headers.get("Content-Range", "")
    if "/" in content_range:
        return int(content_range.rsplit("/", 1)[1])
    return len(payload or [])


def fetch_matiere_name(matiere_id: int) -> str:
    if matiere_id <= 0:
        return "Documents divers"
    path = f"matieres?select=nom&id=eq.{matiere_id}&limit=1"
    _, payload, _ = request("GET", path)
    if not payload:
        return "Documents divers"
    return payload[0].get("nom") or "Documents divers"


def existing_questions(document_id: int) -> set[str]:
    path = f"flashcards?select=question&document_id=eq.{document_id}&limit=1000"
    _, payload, _ = request("GET", path)
    return {
        _normalize_question(row.get("question") or "")
        for row in (payload or [])
        if row.get("question")
    }


def _normalize_quiz_question(question: str) -> str:
    return normalized(str(question or "").strip())


def _validate_quiz_question(item: dict[str, Any]) -> bool:
    question = str(item.get("question") or "").strip()
    choix = item.get("choix")
    reponse_correcte = item.get("reponse_correcte")
    explication = str(item.get("explication") or "").strip()
    difficulte = int(item.get("difficulte") or 2)
    if len(question) < 20:
        return False
    if not isinstance(choix, list) or len(choix) != 4:
        return False
    if not all(len(str(choice or "").strip()) >= 8 for choice in choix):
        return False
    if not isinstance(reponse_correcte, int) or not 0 <= reponse_correcte <= 3:
        return False
    if len(explication) < 20:
        return False
    if not 1 <= difficulte <= 5:
        return False
    return True


def fetch_quiz_info(document_id: int) -> dict[str, Any]:
    path = f"quizzes?select=id,titre,created_at&document_id=eq.{document_id}&order=created_at.desc&limit=50"
    _, quizzes, _ = request("GET", path)
    quiz_ids = [int(row["id"]) for row in (quizzes or []) if row.get("id") is not None]
    if not quiz_ids:
        return {"quiz_id": None, "question_count": 0, "questions": set()}
    ids = ",".join(str(qid) for qid in quiz_ids)
    question_count = fetch_count("quiz_questions", f"quiz_id=in.({ids})")
    _, payload, _ = request("GET", f"quiz_questions?select=question&quiz_id=in.({ids})&limit=1000")
    seen = {
        _normalize_quiz_question(row.get("question") or "")
        for row in (payload or [])
        if row.get("question")
    }
    return {"quiz_id": quiz_ids[0], "question_count": question_count, "questions": seen}


def insert_fiche(doc: dict[str, Any], payload: dict[str, Any], dry_run: bool) -> int:
    if int(doc.get("fiches") or 0) > 0:
        return 0
    if not _validate_fiche_payload(payload):
        raise ValueError(f"fiche invalide document_id={doc['id']}")
    if dry_run:
        return 1
    now = datetime.now(UTC).replace(tzinfo=None).isoformat(sep=" ")
    fiche_payload = {
        "titre": str(payload.get("titre") or "").strip()[:180],
        "resume": str(payload.get("resume") or "").strip()[:1400],
        "matiere_id": doc["matiere_id"],
        "document_id": doc["id"],
        "chapitre": str(doc.get("chapitre") or "")[:180],
        "tags": "direct-assistant",
        "ordre": 0,
        "created_at": now,
    }
    _, inserted, _ = request(
        "POST",
        "fiches",
        body=fiche_payload,
        headers={"Prefer": "return=representation"},
    )
    fiche_id = inserted[0]["id"]
    sections = []
    for idx, section in enumerate(payload.get("sections") or []):
        sections.append(
            {
                "fiche_id": fiche_id,
                "titre": str(section.get("titre") or "").strip()[:180],
                "contenu": str(section.get("contenu") or "").strip()[:2400],
                "ordre": idx,
            }
        )
    if sections:
        request("POST", "fiche_sections", body=sections, headers={"Prefer": "return=minimal"})
    return 1


def insert_flashcards(
    doc: dict[str, Any],
    cards: list[dict[str, Any]],
    dry_run: bool,
    min_flashcards: int,
) -> int:
    current = int(doc.get("flashcards") or 0)
    missing = max(0, min_flashcards - current)
    if missing <= 0:
        return 0
    seen = existing_questions(int(doc["id"]))
    now = datetime.now(UTC).replace(tzinfo=None).isoformat(sep=" ")
    payload = []
    inserted = 0
    for card in cards:
        if inserted >= missing:
            break
        if not _validate_flashcard(card):
            raise ValueError(f"flashcard invalide document_id={doc['id']}: {card.get('question')!r}")
        question = str(card.get("question") or "").strip()
        norm = _normalize_question(question)
        if not question or norm in seen:
            continue
        seen.add(norm)
        payload.append(
            {
                "question": question[:280],
                "reponse": str(card.get("reponse") or "").strip()[:900],
                "explication": str(card.get("explication") or "").strip()[:600],
                "difficulte": min(max(int(card.get("difficulte") or 3), 1), 5),
                "matiere_id": doc["matiere_id"],
                "document_id": doc["id"],
                "intervalle_jours": 1.0,
                "facteur_facilite": 2.5,
                "repetitions": 0,
                "prochaine_revision": now,
                "created_at": now,
            }
        )
        inserted += 1
    if inserted and not dry_run:
        request("POST", "flashcards", body=payload, headers={"Prefer": "return=minimal"})
    return inserted


def ensure_quiz(doc: dict[str, Any], title: str, dry_run: bool) -> int | None:
    info = fetch_quiz_info(int(doc["id"]))
    if info["quiz_id"] is not None:
        return int(info["quiz_id"])
    if dry_run:
        return -1
    now = datetime.now(UTC).replace(tzinfo=None).isoformat(sep=" ")
    quiz_payload = {
        "titre": str(title or f"Quiz - {doc.get('titre') or 'Document'}").strip()[:220],
        "matiere_id": doc["matiere_id"],
        "document_id": doc["id"],
        "created_at": now,
    }
    _, inserted, _ = request(
        "POST",
        "quizzes",
        body=quiz_payload,
        headers={"Prefer": "return=representation"},
    )
    return int(inserted[0]["id"])


def insert_quiz_questions(
    doc: dict[str, Any],
    quiz_payload: dict[str, Any] | None,
    dry_run: bool,
    min_quiz_questions: int,
) -> int:
    if min_quiz_questions <= 0 or not quiz_payload:
        return 0
    info = fetch_quiz_info(int(doc["id"]))
    missing = max(0, min_quiz_questions - int(info["question_count"]))
    if missing <= 0:
        return 0
    quiz_id = info["quiz_id"]
    if quiz_id is None:
        quiz_id = ensure_quiz(doc, str(quiz_payload.get("titre") or ""), dry_run)
    seen = set(info["questions"])
    payload = []
    inserted = 0
    for item in quiz_payload.get("questions") or []:
        if inserted >= missing:
            break
        if not _validate_quiz_question(item):
            raise ValueError(f"quiz invalide document_id={doc['id']}: {item.get('question')!r}")
        question = str(item.get("question") or "").strip()
        norm = _normalize_quiz_question(question)
        if not question or norm in seen:
            continue
        seen.add(norm)
        payload.append(
            {
                "quiz_id": 0 if quiz_id == -1 else quiz_id,
                "question": question[:500],
                "choix": [str(choice).strip()[:300] for choice in item.get("choix") or []],
                "reponse_correcte": int(item.get("reponse_correcte") or 0),
                "explication": str(item.get("explication") or "").strip()[:1200],
                "difficulte": min(max(int(item.get("difficulte") or 2), 1), 5),
            }
        )
        inserted += 1
    if inserted and not dry_run:
        request("POST", "quiz_questions", body=payload, headers={"Prefer": "return=minimal"})
    return inserted


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--min-flashcards", type=int, default=10)
    parser.add_argument("--min-quiz-questions", type=int, default=0)
    args = parser.parse_args()

    raw = sys.stdin.read()
    payload = json.loads(raw)
    docs_payload = payload.get("documents") or []
    if not isinstance(docs_payload, list):
        raise ValueError("documents must be a list")

    dry_run = not args.apply
    totals = {"documents": 0, "fiches": 0, "flashcards": 0, "quiz_questions": 0, "skipped": 0}
    for item in docs_payload:
        document_id = int(item["document_id"])
        doc = fetch_doc(document_id)
        if not doc:
            totals["skipped"] += 1
            continue
        if "scolarite" in normalized(doc.get("matiere") or ""):
            totals["skipped"] += 1
            continue
        fiche_count = 0
        if item.get("fiche"):
            fiche_count = insert_fiche(doc, item["fiche"], dry_run)
            totals["fiches"] += fiche_count
            if fiche_count:
                doc["fiches"] = int(doc.get("fiches") or 0) + fiche_count
        cards_count = insert_flashcards(
            doc,
            item.get("flashcards") or [],
            dry_run,
            args.min_flashcards,
        )
        totals["flashcards"] += cards_count
        quiz_count = insert_quiz_questions(
            doc,
            item.get("quiz"),
            dry_run,
            args.min_quiz_questions,
        )
        totals["quiz_questions"] += quiz_count
        if fiche_count or cards_count or quiz_count:
            totals["documents"] += 1
    mode = "DRY-RUN" if dry_run else "APPLY"
    print(f"{mode}: {totals}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
