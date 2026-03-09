#!/usr/bin/env python3
"""
generate_full_coverage.py — Pipeline bulk "full coverage" IACA
==============================================================

Génère massivement flashcards / quiz / fiches pour tous les documents
de la DB, avec:
  - Reprise incrémentale (checkpoint JSON)
  - Priorisation manuels
  - Chunking du contenu par sections/paragraphes
  - Cibles dynamiques (manuels vs docs standards)
  - Retries/backoff sur erreurs LLM
  - Logs détaillés

Usage:
  python3 scripts/generate_full_coverage.py --help
  python3 scripts/generate_full_coverage.py --dry-run --limit 5
  python3 scripts/generate_full_coverage.py --limit 2 --only-manuals
  python3 scripts/generate_full_coverage.py --matiere 1 --limit 10
"""

import argparse
import asyncio
import json
import logging
import re
import sqlite3
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).parent.parent
DB_PATH = REPO_ROOT / "data" / "iaca.db"
STATE_PATH = REPO_ROOT / "data" / "full_coverage_state.json"
LOG_PATH = REPO_ROOT / "logs" / "full_coverage.log"
BACKEND_DIR = REPO_ROOT / "backend"

# ── Add backend to sys.path so we can import claude_service ──────────────────
sys.path.insert(0, str(BACKEND_DIR))

from app.services.claude_service import generer_flashcards, generer_qcm, generer_fiche  # noqa: E402

# ── Coverage targets ──────────────────────────────────────────────────────────
MANUEL_KEYWORDS = [
    "manuel", "traité", "cours", "précis", "droit du travail", "grands arrêts",
    "dalloz", "lgdj", "lexis", "larcier", "puf", "sirey", "edition", "ed.", "tome",
]
TARGETS = {
    "manuel": {"flashcards": 50, "quiz_questions": 20, "fiches": 5},
    "standard": {"flashcards": 16, "quiz_questions": 8, "fiches": 2},
}

# ── Chunking ──────────────────────────────────────────────────────────────────
CHUNK_SIZE = 6000        # chars per chunk (fits in 8k LLM context)
CHUNK_OVERLAP = 500      # overlap between chunks

# ── Retry config ──────────────────────────────────────────────────────────────
MAX_RETRIES = 3
BACKOFF_BASE = 5         # seconds

# ── LLM provider defaults ─────────────────────────────────────────────────────
DEFAULT_PROVIDER = "auto"
DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "phi3:mini"
OLLAMA_TIMEOUT = 300

# Basic French stopwords for heuristic generation.
STOPWORDS = {
    "dans", "avec", "pour", "sans", "plus", "moins", "cette", "cela", "comme", "dont", "ainsi",
    "leur", "leurs", "elles", "entre", "apres", "avant", "tres", "tout", "tous", "toutes",
    "etre", "avoir", "sont", "ete", "sur", "par", "des", "les", "une", "que", "qui", "est",
    "aux", "ces", "ses", "son", "nos", "vos", "car", "pas", "mais", "dans", "deux", "trois",
}


# ── Logging setup ─────────────────────────────────────────────────────────────
def setup_logging(dry_run: bool) -> logging.Logger:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("full_coverage")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    fh = logging.FileHandler(LOG_PATH, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(ch)

    if dry_run:
        logger.info("=== DRY-RUN MODE — aucune écriture en DB ===")
    return logger


# ── State / checkpoint ─────────────────────────────────────────────────────────
def load_state() -> dict:
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text())
        except Exception:
            pass
    return {"completed_doc_ids": [], "stats": {"flashcards": 0, "quiz_questions": 0, "fiches": 0}}


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False))


# ── DB helpers ────────────────────────────────────────────────────────────────
def db_connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_matiere_name(conn: sqlite3.Connection, matiere_id: int) -> str:
    row = conn.execute("SELECT nom FROM matieres WHERE id=?", (matiere_id,)).fetchone()
    return row["nom"] if row else "Général"


def count_existing(conn: sqlite3.Connection, doc_id: int) -> dict:
    fc = conn.execute("SELECT COUNT(*) FROM flashcards WHERE document_id=?", (doc_id,)).fetchone()[0]
    qq = conn.execute(
        "SELECT COUNT(*) FROM quiz_questions qq "
        "JOIN quizzes q ON q.id=qq.quiz_id WHERE q.document_id=?", (doc_id,)
    ).fetchone()[0]
    fi = conn.execute("SELECT COUNT(*) FROM fiches WHERE document_id=?", (doc_id,)).fetchone()[0]
    return {"flashcards": fc, "quiz_questions": qq, "fiches": fi}


def _normalize_question(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.lower())
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def fetch_existing_flashcard_questions(conn: sqlite3.Connection, doc_id: int) -> set[str]:
    rows = conn.execute(
        "SELECT question FROM flashcards WHERE document_id=? AND question IS NOT NULL",
        (doc_id,),
    ).fetchall()
    return {_normalize_question(row["question"]) for row in rows if row["question"]}


def fetch_documents(
    conn: sqlite3.Connection,
    matiere_id: int | None,
    only_manuals: bool,
    limit: int | None,
    done_ids: list[int],
    max_content_len: int | None,
) -> list[sqlite3.Row]:
    where_parts = [
        "LENGTH(d.contenu_extrait) > 100",
        "d.contenu_extrait NOT LIKE ?",
    ]
    params: list = ["%[Erreur d'extraction:%"]

    if matiere_id is not None:
        where_parts.append("d.matiere_id = ?")
        params.append(matiere_id)
    if max_content_len is not None:
        where_parts.append("LENGTH(d.contenu_extrait) <= ?")
        params.append(max_content_len)
    if done_ids:
        placeholders = ",".join("?" * len(done_ids))
        where_parts.append(f"d.id NOT IN ({placeholders})")
        params.extend(done_ids)

    where = " AND ".join(where_parts)
    sql = f"""
        SELECT d.id, d.titre, d.contenu_extrait, d.matiere_id, m.nom AS matiere_nom
        FROM documents d
        LEFT JOIN matieres m ON m.id = d.matiere_id
        WHERE {where}
        ORDER BY LENGTH(d.contenu_extrait) DESC
    """
    rows = conn.execute(sql, params).fetchall()

    if only_manuals:
        rows = [r for r in rows if _is_manuel(r["titre"])]

    if limit:
        rows = rows[:limit]

    return rows


def _is_manuel(titre: str) -> bool:
    t = titre.lower()
    return any(kw in t for kw in MANUEL_KEYWORDS)


def classify_doc(titre: str) -> str:
    return "manuel" if _is_manuel(titre) else "standard"


def build_gap_report(
    conn: sqlite3.Connection,
    docs: list[sqlite3.Row],
    targets: dict[str, dict[str, int]],
    top_n: int = 10,
) -> dict:
    under_target_counts = {"standard": 0, "manuel": 0}
    gap_rows: list[dict] = []

    for doc in docs:
        doc_id = doc["id"]
        kind = classify_doc(doc["titre"])
        target = targets[kind]
        existing = count_existing(conn, doc_id)

        missing_fc = max(0, target["flashcards"] - existing["flashcards"])
        missing_qq = max(0, target["quiz_questions"] - existing["quiz_questions"])
        missing_fi = max(0, target["fiches"] - existing["fiches"])

        total_gap = missing_fc + missing_qq + missing_fi
        if total_gap == 0:
            continue

        under_target_counts[kind] += 1
        gap_rows.append(
            {
                "doc_id": doc_id,
                "titre": doc["titre"],
                "kind": kind,
                "missing_fc": missing_fc,
                "missing_qq": missing_qq,
                "missing_fi": missing_fi,
                "total_gap": total_gap,
            }
        )

    gap_rows.sort(key=lambda row: (-row["total_gap"], row["doc_id"]))
    return {
        "under_target_counts": under_target_counts,
        "under_target_total": under_target_counts["standard"] + under_target_counts["manuel"],
        "top_gaps": gap_rows[:top_n],
    }


# ── Chunking ──────────────────────────────────────────────────────────────────
SECTION_RE = re.compile(
    r'(?m)^(#{1,3}\s.+|(?:chapitre|section|partie|titre)\s+\w.+|[A-ZÀÂÄÉÈÊËÎÏÔÙÛÜ][^a-z\n]{4,})',
    re.IGNORECASE
)


def chunk_content(content: str) -> list[str]:
    """Split content into overlapping chunks, preferring section boundaries."""
    if not content:
        return []

    # Try to split on headings/sections first
    splits = [m.start() for m in SECTION_RE.finditer(content)]

    chunks: list[str] = []
    if len(splits) >= 2:
        for i, start in enumerate(splits):
            end = splits[i + 1] if i + 1 < len(splits) else len(content)
            section = content[start:end].strip()
            # If section is too big, sub-chunk it
            if len(section) > CHUNK_SIZE:
                chunks.extend(_fixed_chunks(section))
            elif section:
                chunks.append(section)
    else:
        chunks = _fixed_chunks(content)

    # Merge tiny chunks
    merged: list[str] = []
    buf = ""
    for chunk in chunks:
        if len(buf) + len(chunk) < CHUNK_SIZE:
            buf = (buf + "\n\n" + chunk).strip()
        else:
            if buf:
                merged.append(buf)
            buf = chunk
    if buf:
        merged.append(buf)

    return merged or [content[:CHUNK_SIZE]]


def _fixed_chunks(text: str) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        chunks.append(text[start:end])
        start = end - CHUNK_OVERLAP if end < len(text) else end
    return chunks


# ── Retry wrapper ─────────────────────────────────────────────────────────────
async def with_retry(coro_fn, logger: logging.Logger, label: str):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return await coro_fn()
        except Exception as exc:
            wait = BACKOFF_BASE * attempt
            logger.warning(f"[{label}] Erreur tentative {attempt}/{MAX_RETRIES}: {exc} — retry dans {wait}s")
            if attempt == MAX_RETRIES:
                raise
            await asyncio.sleep(wait)


# ── LLM generation helpers (Claude + Ollama fallback) ────────────────────────
def _extract_json_array(text: str) -> list[dict]:
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        raise ValueError("JSON array introuvable dans la réponse LLM")
    return json.loads(match.group())


def _extract_json_object(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("JSON object introuvable dans la réponse LLM")
    return json.loads(match.group())


def _split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    candidates = re.split(r"(?<=[.!?])\s+", text)
    return [c.strip() for c in candidates if 35 <= len(c.strip()) <= 260]


def _extract_topics(sentence: str, limit: int = 3) -> list[str]:
    words = re.findall(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'-]{3,}", sentence.lower())
    topics: list[str] = []
    seen: set[str] = set()
    for w in words:
        if w in STOPWORDS or w in seen:
            continue
        seen.add(w)
        topics.append(w)
        if len(topics) >= limit:
            break
    return topics


def _build_notion_question(matiere: str, sentence: str, idx: int) -> str:
    topics = _extract_topics(sentence, limit=3)
    if topics:
        label = " / ".join(topics)
        return f"En {matiere}, quelle notion explique le passage sur '{label}' ?"

    snippet = re.sub(r"\s+", " ", sentence or "").strip(" .,:;")
    if snippet:
        return f"En {matiere}, quelle notion est illustree par '{snippet[:80]}' ?"

    return f"En {matiere}, quelle notion cle faut-il maitriser (point {idx}) ?"


def _generate_flashcards_heuristic(
    contenu: str,
    matiere: str,
    nb: int,
    start_index: int = 0,
) -> list[dict]:
    sentences = _split_sentences(contenu)
    if not sentences:
        sentences = [contenu[:220]] if contenu else []
    cards: list[dict] = []
    used: set[str] = set()
    for sentence in sentences:
        if len(cards) >= nb:
            break
        topics = _extract_topics(sentence, limit=2)
        topic_label = " / ".join(topics) if topics else matiere
        question = f"Que faut-il retenir en {matiere} sur '{topic_label}' ?"
        if question in used:
            continue
        used.add(question)
        cards.append(
            {
                "question": question[:280],
                "reponse": sentence[:900],
                "explication": f"Point extrait du document de {matiere}.",
                "difficulte": 2 if len(sentence) < 130 else 3,
            }
        )
    while len(cards) < nb and sentences:
        seed = sentences[len(cards) % len(sentences)]
        idx = start_index + len(cards) + 1
        cards.append(
            {
                "question": _build_notion_question(matiere, seed, idx)[:280],
                "reponse": seed[:900],
                "explication": f"Carte de consolidation heuristique #{idx}.",
                "difficulte": 2,
            }
        )
    return cards[:nb]


def _generate_qcm_heuristic(contenu: str, matiere: str, nb: int) -> list[dict]:
    sentences = _split_sentences(contenu)
    if not sentences and contenu:
        sentences = [contenu[:220]]
    # Ensure we always have enough material to build 4 options.
    while 0 < len(sentences) < 4:
        seed = sentences[-1][:140]
        sentences.append(f"Formulation alternative en {matiere}: {seed}")
    if not sentences:
        return []
    questions: list[dict] = []
    for idx in range(nb):
        correct = sentences[idx % len(sentences)]
        distract_pool = [s for j, s in enumerate(sentences) if j != (idx % len(sentences))]
        distractors = distract_pool[:3] if len(distract_pool) >= 3 else (distract_pool + [correct])[:3]
        choices_raw = [correct] + distractors
        question_topics = _extract_topics(correct, limit=2)
        question_label = " / ".join(question_topics) if question_topics else f"point {idx + 1}"
        formatted = []
        for i, choice in enumerate(choices_raw[:4]):
            letter = ["A", "B", "C", "D"][i]
            formatted.append(f"{letter}. {choice[:170]}")
        questions.append(
            {
                "question": f"QCM {idx + 1}: quelle affirmation est correcte sur {question_label} en {matiere} ?",
                "choix": formatted,
                "reponse_correcte": 0,
                "explication": f"La bonne réponse reprend fidèlement le contenu source ({matiere}).",
                "difficulte": 3,
            }
        )
    return questions[:nb]


def _generate_fiche_heuristic(contenu: str, matiere: str, titre_doc: str) -> dict:
    raw_sections = [s.strip() for s in re.split(r"\n\s*\n+", contenu) if len(s.strip()) > 80]
    if not raw_sections:
        raw_sections = [contenu[:2400]] if contenu else []
    selected = raw_sections[:6]
    sections: list[dict] = []
    for i, section_text in enumerate(selected, start=1):
        sentences = _split_sentences(section_text)
        if not sentences:
            continue
        section_title = f"Section {i} - {(_extract_topics(sentences[0], 1) or [f'axe {i}'])[0]}"
        section_body = " ".join(sentences[:4])
        sections.append({"titre": section_title[:180], "contenu": section_body[:2500]})
    summary_sentences = _split_sentences(contenu)[:4]
    resume = " ".join(summary_sentences)[:1200] if summary_sentences else (contenu[:500] if contenu else "")
    return {
        "titre": f"Fiche - {titre_doc[:140]}",
        "resume": resume,
        "sections": sections[:8] if sections else [{"titre": "Synthèse", "contenu": resume}],
    }


def _build_fill_flashcards(
    contenu: str,
    matiere: str,
    nb: int,
    start_index: int = 0,
) -> list[dict]:
    sentences = _split_sentences(contenu)
    if not sentences:
        fallback = (contenu or "").strip()
        if len(fallback) < 80:
            fallback = (fallback + " " + f"Point de consolidation en {matiere}.").strip()
        sentences = [fallback[:300]]

    cards: list[dict] = []
    for i in range(nb):
        sentence = sentences[i % len(sentences)]
        idx = start_index + i + 1
        cards.append(
            {
                "question": _build_notion_question(matiere, sentence, idx)[:280],
                "reponse": sentence[:900],
                "explication": f"Carte de rattrapage qualitative #{idx}.",
                "difficulte": 2 if len(sentence) < 140 else 3,
            }
        )
    return cards


def _build_fill_qcm(
    contenu: str,
    matiere: str,
    nb: int,
    start_index: int = 0,
) -> list[dict]:
    sentences = _split_sentences(contenu)
    if not sentences:
        seed = (contenu or "").strip()
        if len(seed) < 60:
            seed = f"Point de consolidation en {matiere}."
        sentences = [seed[:220]]
    while 0 < len(sentences) < 4:
        sentences.append(f"Complément méthodologique en {matiere}: {sentences[-1][:130]}")

    questions: list[dict] = []
    for i in range(nb):
        idx = start_index + i + 1
        correct = sentences[i % len(sentences)]
        distractors = [
            f"Interprétation partielle en {matiere}: {sentences[(i + 1) % len(sentences)][:130]}",
            f"Lecture incomplète en {matiere}: {sentences[(i + 2) % len(sentences)][:130]}",
            f"Contresens fréquent en {matiere}: {sentences[(i + 3) % len(sentences)][:130]}",
        ]
        choices = [correct] + distractors
        formatted = [f"{['A', 'B', 'C', 'D'][j]}. {c[:170]}" for j, c in enumerate(choices)]
        questions.append(
            {
                "question": (
                    f"QCM de consolidation {idx} en {matiere}: quelle proposition "
                    f"reflète fidèlement le document ?"
                )[:300],
                "choix": formatted,
                "reponse_correcte": 0,
                "explication": f"La réponse A reprend l'information source (item #{idx}).",
                "difficulte": 3,
            }
        )
    return questions


def _ollama_chat(prompt: str, ollama_url: str, ollama_model: str, num_predict: int = 1600) -> str:
    payload = json.dumps(
        {
            "model": ollama_model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_predict": num_predict,
            },
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{ollama_url.rstrip('/')}/api/chat",
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT) as resp:
        raw = resp.read().decode("utf-8")
    data = json.loads(raw)
    return data["message"]["content"]


async def _generate_flashcards_ollama(
    contenu: str,
    matiere: str,
    nb: int,
    ollama_url: str,
    ollama_model: str,
) -> list[dict]:
    prompt = f"""Tu es un expert en {matiere} pour la preparation aux concours administratifs francais.
Genere exactement {nb} flashcards de revision basees uniquement sur le contenu ci-dessous.

CONTENU:
{contenu[:7000]}

Reponds UNIQUEMENT en JSON valide:
[
  {{
    "question": "...",
    "reponse": "...",
    "explication": "...",
    "difficulte": 2
  }}
]

difficulte doit etre un entier de 1 a 5."""
    text = await asyncio.to_thread(_ollama_chat, prompt, ollama_url, ollama_model, 1800)
    return _extract_json_array(text)


async def _generate_qcm_ollama(
    contenu: str,
    matiere: str,
    nb: int,
    ollama_url: str,
    ollama_model: str,
) -> list[dict]:
    prompt = f"""Tu es un expert en {matiere} pour la preparation aux concours administratifs francais.
Genere exactement {nb} questions QCM basees uniquement sur le contenu ci-dessous.

CONTENU:
{contenu[:7000]}

Reponds UNIQUEMENT en JSON valide:
[
  {{
    "question": "...",
    "choix": ["A. ...", "B. ...", "C. ...", "D. ..."],
    "reponse_correcte": 0,
    "explication": "...",
    "difficulte": 2
  }}
]

reponse_correcte doit etre un index entre 0 et 3."""
    text = await asyncio.to_thread(_ollama_chat, prompt, ollama_url, ollama_model, 1800)
    return _extract_json_array(text)


async def _generate_fiche_ollama(
    contenu: str,
    matiere: str,
    titre_doc: str,
    ollama_url: str,
    ollama_model: str,
) -> dict:
    prompt = f"""Tu es un expert en {matiere} pour la preparation aux concours administratifs francais.
Genere une fiche de revision structuree pour le document ci-dessous.

DOCUMENT: {titre_doc}
CONTENU:
{contenu[:7000]}

Reponds UNIQUEMENT en JSON valide:
{{
  "titre": "Titre de la fiche",
  "resume": "Resume en 3-5 phrases",
  "sections": [
    {{
      "titre": "Section 1",
      "contenu": "Contenu detaille et pedagogique"
    }}
  ]
}}

Genere entre 4 et 8 sections."""
    text = await asyncio.to_thread(_ollama_chat, prompt, ollama_url, ollama_model, 2200)
    return _extract_json_object(text)


async def generate_flashcards_with_provider(
    contenu: str,
    matiere: str,
    nb: int,
    provider: str,
    ollama_url: str,
    ollama_model: str,
) -> list[dict]:
    last_exc: Exception | None = None
    if provider in ("auto", "claude"):
        try:
            return await generer_flashcards(contenu, matiere, nb=nb)
        except Exception as exc:
            last_exc = exc
            if provider == "claude":
                raise
    if provider == "heuristic":
        return _generate_flashcards_heuristic(contenu, matiere, nb)
    if provider in ("auto", "ollama"):
        try:
            return await _generate_flashcards_ollama(contenu, matiere, nb, ollama_url, ollama_model)
        except Exception as exc:
            last_exc = exc
            if provider == "ollama":
                raise
    return _generate_flashcards_heuristic(contenu, matiere, nb)


async def generate_qcm_with_provider(
    contenu: str,
    matiere: str,
    nb: int,
    provider: str,
    ollama_url: str,
    ollama_model: str,
) -> list[dict]:
    last_exc: Exception | None = None
    if provider in ("auto", "claude"):
        try:
            return await generer_qcm(contenu, matiere, nb=nb)
        except Exception as exc:
            last_exc = exc
            if provider == "claude":
                raise
    if provider == "heuristic":
        return _generate_qcm_heuristic(contenu, matiere, nb)
    if provider in ("auto", "ollama"):
        try:
            return await _generate_qcm_ollama(contenu, matiere, nb, ollama_url, ollama_model)
        except Exception as exc:
            last_exc = exc
            if provider == "ollama":
                raise
    return _generate_qcm_heuristic(contenu, matiere, nb)


async def generate_fiche_with_provider(
    contenu: str,
    matiere: str,
    titre_doc: str,
    provider: str,
    ollama_url: str,
    ollama_model: str,
) -> dict:
    last_exc: Exception | None = None
    if provider in ("auto", "claude"):
        try:
            return await generer_fiche(contenu, matiere, titre_doc)
        except Exception as exc:
            last_exc = exc
            if provider == "claude":
                raise
    if provider == "heuristic":
        return _generate_fiche_heuristic(contenu, matiere, titre_doc)
    if provider in ("auto", "ollama"):
        try:
            return await _generate_fiche_ollama(contenu, matiere, titre_doc, ollama_url, ollama_model)
        except Exception as exc:
            last_exc = exc
            if provider == "ollama":
                raise
    return _generate_fiche_heuristic(contenu, matiere, titre_doc)


# ── DB insert helpers (raw sqlite3, no ORM needed) ────────────────────────────
def insert_flashcards(
    conn: sqlite3.Connection,
    cards: list[dict],
    doc_id: int,
    matiere_id: int,
    seen_questions: set[str] | None = None,
) -> int:
    now = datetime.now(timezone.utc).isoformat()
    inserted = 0
    for c in cards:
        question = str(c.get("question", "")).strip()
        reponse = str(c.get("reponse", "")).strip()
        if not question or not reponse:
            continue

        normalized_question = _normalize_question(question)
        if seen_questions is not None:
            if normalized_question in seen_questions:
                continue
            seen_questions.add(normalized_question)

        try:
            conn.execute(
                """INSERT INTO flashcards
                   (question, reponse, explication, difficulte, matiere_id, document_id,
                    intervalle_jours, facteur_facilite, repetitions, prochaine_revision, created_at)
                   VALUES (?,?,?,?,?,?,1.0,2.5,0,?,?)""",
                (
                    question,
                    reponse,
                    c.get("explication", ""),
                    min(max(int(c.get("difficulte", 2)), 1), 5),
                    matiere_id,
                    doc_id,
                    now, now,
                ),
            )
            inserted += 1
        except Exception:
            pass
    conn.commit()
    return inserted


def insert_quiz(conn: sqlite3.Connection, questions: list[dict], doc_id: int, matiere_id: int, titre: str) -> int:
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.execute(
        "INSERT INTO quizzes (titre, matiere_id, document_id, created_at) VALUES (?,?,?,?)",
        (titre[:200], matiere_id, doc_id, now),
    )
    quiz_id = cur.lastrowid
    inserted = 0
    for q in questions:
        choix = q.get("choix", [])
        if not choix:
            continue
        try:
            conn.execute(
                """INSERT INTO quiz_questions
                   (quiz_id, question, choix, reponse_correcte, explication, difficulte)
                   VALUES (?,?,?,?,?,?)""",
                (
                    quiz_id,
                    q.get("question", ""),
                    json.dumps(choix, ensure_ascii=False),
                    min(max(int(q.get("reponse_correcte", 0)), 0), len(choix) - 1),
                    q.get("explication", ""),
                    min(max(int(q.get("difficulte", 2)), 1), 5),
                ),
            )
            inserted += 1
        except Exception:
            pass
    conn.commit()
    return inserted


def insert_fiche(conn: sqlite3.Connection, fiche_data: dict, doc_id: int, matiere_id: int) -> bool:
    now = datetime.now(timezone.utc).isoformat()
    try:
        cur = conn.execute(
            """INSERT INTO fiches (titre, resume, matiere_id, document_id, chapitre, tags, ordre, created_at)
               VALUES (?,?,?,?,?,?,0,?)""",
            (
                fiche_data.get("titre", "Fiche")[:200],
                fiche_data.get("resume", ""),
                matiere_id,
                doc_id,
                "",
                "",
                now,
            ),
        )
        fiche_id = cur.lastrowid
        for i, section in enumerate(fiche_data.get("sections", [])):
            conn.execute(
                "INSERT INTO fiche_sections (fiche_id, titre, contenu, ordre) VALUES (?,?,?,?)",
                (fiche_id, section.get("titre", f"Section {i+1}")[:200], section.get("contenu", ""), i),
            )
        conn.commit()
        return True
    except Exception:
        return False


# ── Core generation logic ─────────────────────────────────────────────────────
async def process_document(
    doc: sqlite3.Row,
    conn: sqlite3.Connection,
    active_targets: dict[str, dict[str, int]],
    logger: logging.Logger,
    dry_run: bool,
    provider: str,
    ollama_url: str,
    ollama_model: str,
) -> dict:
    doc_id = doc["id"]
    titre = doc["titre"]
    contenu = doc["contenu_extrait"] or ""
    matiere_id = doc["matiere_id"] or 1
    matiere_nom = doc["matiere_nom"] or "Général"
    kind = classify_doc(titre)
    targets = active_targets[kind]

    existing = count_existing(conn, doc_id)
    need_fc = max(0, targets["flashcards"] - existing["flashcards"])
    need_qq = max(0, targets["quiz_questions"] - existing["quiz_questions"])
    need_fi = max(0, targets["fiches"] - existing["fiches"])

    logger.info(
        f"[doc={doc_id}] '{titre[:60]}' [{kind}] "
        f"need fc={need_fc} qq={need_qq} fi={need_fi} | content={len(contenu)}c"
    )

    result = {"flashcards": 0, "quiz_questions": 0, "fiches": 0, "skipped": False}

    if need_fc == 0 and need_qq == 0 and need_fi == 0:
        logger.info(f"[doc={doc_id}] Cibles déjà atteintes — skip")
        result["skipped"] = True
        return result

    if dry_run:
        logger.info(f"[doc={doc_id}] DRY-RUN — génération simulée: fc={need_fc}, qq={need_qq}, fi={need_fi}")
        result.update({"flashcards": need_fc, "quiz_questions": need_qq, "fiches": need_fi})
        return result

    chunks = chunk_content(contenu)
    logger.debug(f"[doc={doc_id}] {len(chunks)} chunks produits")
    seen_questions = fetch_existing_flashcard_questions(conn, doc_id)

    # ── Flashcards ────────────────────────────────────────────────────────────
    if need_fc > 0:
        per_chunk = max(2, need_fc // max(1, min(len(chunks), 4)))
        total_fc = 0
        for i, chunk in enumerate(chunks):
            if total_fc >= need_fc:
                break
            nb = min(per_chunk, need_fc - total_fc)
            try:
                cards = await with_retry(
                    lambda c=chunk, n=nb: generate_flashcards_with_provider(
                        c, matiere_nom, n, provider, ollama_url, ollama_model
                    ),
                    logger, f"doc={doc_id} flashcards chunk={i}"
                )
                inserted = insert_flashcards(conn, cards, doc_id, matiere_id, seen_questions)
                total_fc += inserted
                result["flashcards"] += inserted
                logger.info(f"[doc={doc_id}] Chunk {i}: +{inserted} flashcards (total={total_fc}/{need_fc})")
            except Exception as e:
                logger.error(f"[doc={doc_id}] Flashcards chunk={i} ÉCHEC: {e}")

    # ── Quiz ──────────────────────────────────────────────────────────────────
    if need_qq > 0:
        per_chunk = max(2, need_qq // max(1, min(len(chunks), 3)))
        total_qq = 0
        for i, chunk in enumerate(chunks):
            if total_qq >= need_qq:
                break
            nb = min(per_chunk, need_qq - total_qq)
            try:
                questions = await with_retry(
                    lambda c=chunk, n=nb: generate_qcm_with_provider(
                        c, matiere_nom, n, provider, ollama_url, ollama_model
                    ),
                    logger, f"doc={doc_id} quiz chunk={i}"
                )
                quiz_titre = f"Quiz — {titre[:80]} (chunk {i+1})"
                inserted = insert_quiz(conn, questions, doc_id, matiere_id, quiz_titre)
                total_qq += inserted
                result["quiz_questions"] += inserted
                logger.info(f"[doc={doc_id}] Chunk {i}: +{inserted} questions quiz (total={total_qq}/{need_qq})")
            except Exception as e:
                logger.error(f"[doc={doc_id}] Quiz chunk={i} ÉCHEC: {e}")

    # ── Fiches ────────────────────────────────────────────────────────────────
    if need_fi > 0:
        for i in range(need_fi):
            chunk = chunks[i % len(chunks)]
            try:
                fiche_data = await with_retry(
                    lambda c=chunk: generate_fiche_with_provider(
                        c, matiere_nom, titre, provider, ollama_url, ollama_model
                    ),
                    logger, f"doc={doc_id} fiche={i}"
                )
                ok = insert_fiche(conn, fiche_data, doc_id, matiere_id)
                if ok:
                    result["fiches"] += 1
                    logger.info(f"[doc={doc_id}] Fiche {i+1}/{need_fi} insérée")
            except Exception as e:
                logger.error(f"[doc={doc_id}] Fiche {i} ÉCHEC: {e}")

    # Fill pass to reduce residual gaps on short/noisy docs.
    current = count_existing(conn, doc_id)
    rem_fc = max(0, targets["flashcards"] - current["flashcards"])
    if rem_fc > 0:
        fill_cards = _build_fill_flashcards(
            contenu,
            matiere_nom,
            rem_fc,
            start_index=current["flashcards"],
        )
        inserted = insert_flashcards(conn, fill_cards, doc_id, matiere_id, seen_questions)
        result["flashcards"] += inserted
        logger.info(
            f"[doc={doc_id}] Fill-pass flashcards: +{inserted} (reste={max(0, rem_fc - inserted)})"
        )

    current = count_existing(conn, doc_id)
    rem_qq = max(0, targets["quiz_questions"] - current["quiz_questions"])
    if rem_qq > 0:
        fill_questions = _build_fill_qcm(
            contenu,
            matiere_nom,
            rem_qq,
            start_index=current["quiz_questions"],
        )
        inserted = insert_quiz(conn, fill_questions, doc_id, matiere_id, f"Quiz — {titre[:80]} (fill-pass)")
        result["quiz_questions"] += inserted
        logger.info(
            f"[doc={doc_id}] Fill-pass quiz: +{inserted} (reste={max(0, rem_qq - inserted)})"
        )

    return result


# ── Main ──────────────────────────────────────────────────────────────────────
async def main() -> int:
    parser = argparse.ArgumentParser(
        description="Pipeline bulk full-coverage: flashcards + quiz + fiches pour tous les documents IACA.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--limit", type=int, default=None, help="Nombre max de documents à traiter")
    parser.add_argument("--matiere", type=int, default=None, help="Filtrer par matiere_id")
    parser.add_argument("--only-manuals", action="store_true", help="Traiter uniquement les manuels")
    parser.add_argument("--dry-run", action="store_true", help="Simulation sans écriture en DB")
    parser.add_argument("--reset-state", action="store_true", help="Ignorer le checkpoint existant")
    parser.add_argument(
        "--provider",
        choices=["auto", "claude", "ollama", "heuristic"],
        default=DEFAULT_PROVIDER,
        help="Fournisseur: auto=Claude->Ollama->heuristic",
    )
    parser.add_argument("--ollama-url", default=DEFAULT_OLLAMA_URL, help="Base URL Ollama")
    parser.add_argument("--ollama-model", default=DEFAULT_OLLAMA_MODEL, help="Modele Ollama")
    parser.add_argument(
        "--target-standard-fc",
        type=int,
        default=TARGETS["standard"]["flashcards"],
        help=f"Cible flashcards docs standard (défaut: {TARGETS['standard']['flashcards']})",
    )
    parser.add_argument(
        "--target-standard-qq",
        type=int,
        default=TARGETS["standard"]["quiz_questions"],
        help=f"Cible questions quiz docs standard (défaut: {TARGETS['standard']['quiz_questions']})",
    )
    parser.add_argument(
        "--target-standard-fi",
        type=int,
        default=TARGETS["standard"]["fiches"],
        help=f"Cible fiches docs standard (défaut: {TARGETS['standard']['fiches']})",
    )
    parser.add_argument(
        "--target-manual-fc",
        type=int,
        default=TARGETS["manuel"]["flashcards"],
        help=f"Cible flashcards manuels (défaut: {TARGETS['manuel']['flashcards']})",
    )
    parser.add_argument(
        "--target-manual-qq",
        type=int,
        default=TARGETS["manuel"]["quiz_questions"],
        help=f"Cible questions quiz manuels (défaut: {TARGETS['manuel']['quiz_questions']})",
    )
    parser.add_argument(
        "--target-manual-fi",
        type=int,
        default=TARGETS["manuel"]["fiches"],
        help=f"Cible fiches manuels (défaut: {TARGETS['manuel']['fiches']})",
    )
    parser.add_argument(
        "--max-content-len",
        type=int,
        default=None,
        help="Exclure les documents dont le contenu dépasse cette longueur",
    )
    args = parser.parse_args()

    target_values = [
        args.target_standard_fc,
        args.target_standard_qq,
        args.target_standard_fi,
        args.target_manual_fc,
        args.target_manual_qq,
        args.target_manual_fi,
    ]
    if any(value < 0 for value in target_values):
        print("Toutes les cibles doivent être >= 0.")
        return 2

    active_targets = {
        "standard": {
            "flashcards": args.target_standard_fc,
            "quiz_questions": args.target_standard_qq,
            "fiches": args.target_standard_fi,
        },
        "manuel": {
            "flashcards": args.target_manual_fc,
            "quiz_questions": args.target_manual_qq,
            "fiches": args.target_manual_fi,
        },
    }

    logger = setup_logging(args.dry_run)
    logger.info(
        f"Démarrage generate_full_coverage | limit={args.limit} matiere={args.matiere} "
        f"only_manuals={args.only_manuals} dry_run={args.dry_run} "
        f"provider={args.provider} ollama_model={args.ollama_model} "
        f"max_content_len={args.max_content_len}"
    )
    logger.info(
        "Cibles actives | standard: fc>=%s qq>=%s fi>=%s | manuel: fc>=%s qq>=%s fi>=%s",
        active_targets["standard"]["flashcards"],
        active_targets["standard"]["quiz_questions"],
        active_targets["standard"]["fiches"],
        active_targets["manuel"]["flashcards"],
        active_targets["manuel"]["quiz_questions"],
        active_targets["manuel"]["fiches"],
    )

    state = {} if args.reset_state else load_state()
    done_ids: list[int] = state.get("completed_doc_ids", [])
    stats = state.get("stats", {"flashcards": 0, "quiz_questions": 0, "fiches": 0})

    conn = db_connect()
    docs = fetch_documents(
        conn,
        args.matiere,
        args.only_manuals,
        args.limit,
        done_ids,
        args.max_content_len,
    )

    logger.info(f"{len(docs)} documents à traiter (déjà complétés: {len(done_ids)})")

    if not docs:
        logger.info(
            "Résumé sous-cible (scope courant): total=0 (standard=0, manuel=0)"
        )
        logger.info("Top gaps: aucun (aucun document sélectionné dans le scope courant)")
        logger.info("Aucun document à traiter — exit 0")
        conn.close()
        return 0

    t0 = time.time()
    processed = 0
    errors = 0

    for doc in docs:
        doc_id = doc["id"]
        try:
            result = await process_document(
                doc,
                conn,
                active_targets,
                logger,
                args.dry_run,
                args.provider,
                args.ollama_url,
                args.ollama_model,
            )
            stats["flashcards"] += result["flashcards"]
            stats["quiz_questions"] += result["quiz_questions"]
            stats["fiches"] += result["fiches"]
            processed += 1

            if not args.dry_run and doc_id not in done_ids:
                done_ids.append(doc_id)
                save_state({"completed_doc_ids": done_ids, "stats": stats})

        except Exception as e:
            logger.error(f"[doc={doc_id}] Erreur fatale: {e}")
            errors += 1

    gap_report = build_gap_report(conn, docs, active_targets, top_n=10)
    top_gap_lines = []
    for row in gap_report["top_gaps"]:
        top_gap_lines.append(
            f"    - doc={row['doc_id']} [{row['kind']}] gap_total={row['total_gap']} "
            f"(fc={row['missing_fc']} qq={row['missing_qq']} fi={row['missing_fi']}) "
            f"titre='{row['titre'][:60]}'"
        )
    if not top_gap_lines:
        top_gap_lines = ["    - aucun (toutes les cibles atteintes dans le scope)"]

    elapsed = time.time() - t0
    logger.info(
        f"\n{'='*60}\n"
        f"TERMINÉ en {elapsed:.1f}s\n"
        f"  Documents traités : {processed}/{len(docs)} ({errors} erreurs)\n"
        f"  Flashcards générées: {stats['flashcards']}\n"
        f"  Questions quiz     : {stats['quiz_questions']}\n"
        f"  Fiches générées    : {stats['fiches']}\n"
        f"  Docs sous cible    : total={gap_report['under_target_total']} "
        f"(standard={gap_report['under_target_counts']['standard']}, "
        f"manuel={gap_report['under_target_counts']['manuel']})\n"
        f"  Top gaps:\n"
        f"{chr(10).join(top_gap_lines)}\n"
        f"  Checkpoint         : {STATE_PATH}\n"
        f"  Log                : {LOG_PATH}\n"
        f"{'='*60}"
    )

    conn.close()
    return 1 if errors and processed == 0 else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
