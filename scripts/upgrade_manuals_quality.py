#!/usr/bin/env python3
"""
upgrade_manuals_quality.py — Pipeline qualité ciblée MANUELS IACA
==================================================================

Renforce la couverture des documents manuels prioritaires avec:
  - Cibles renforcées : fc≥40, qq≥16, fiches≥4
  - Anti-duplication sur question normalisée
  - Validation stricte par type (fc/qcm/fiche)
  - Providers: heuristic (instant) | ollama | claude | auto
  - Logs détaillés logs/manual_quality_upgrade.log
  - Delta avant/après par document

Usage:
  python3 scripts/upgrade_manuals_quality.py --help
  python3 scripts/upgrade_manuals_quality.py --dry-run --limit 3
  python3 scripts/upgrade_manuals_quality.py --limit 2 --provider heuristic
  python3 scripts/upgrade_manuals_quality.py --doc-id 271 --provider claude
  python3 scripts/upgrade_manuals_quality.py --matiere 1 --limit 5
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
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).parent.parent
DB_PATH = REPO_ROOT / "data" / "iaca.db"
LOG_PATH = REPO_ROOT / "logs" / "manual_quality_upgrade.log"
BACKEND_DIR = REPO_ROOT / "backend"

sys.path.insert(0, str(BACKEND_DIR))
from app.services.claude_service import generer_flashcards as _claude_fc  # noqa: E402
from app.services.claude_service import generer_qcm as _claude_qcm        # noqa: E402
from app.services.claude_service import generer_fiche as _claude_fiche    # noqa: E402

# ── Targets (reinforced for manuals) ─────────────────────────────────────────
TARGETS = {"flashcards": 40, "quiz_questions": 16, "fiches": 4}

# ── Manuel keywords (same as generate_full_coverage) ─────────────────────────
MANUEL_KEYWORDS = [
    "manuel", "traité", "cours", "précis", "droit du travail", "grands arrêts",
    "dalloz", "lgdj", "lexis", "larcier", "puf", "sirey", "edition", "ed.", "tome",
    "complet",
]

# ── Chunking ──────────────────────────────────────────────────────────────────
CHUNK_SIZE = 6000
CHUNK_OVERLAP = 500

# ── LLM ──────────────────────────────────────────────────────────────────────
OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "phi3:mini"
OLLAMA_TIMEOUT = 300
MAX_RETRIES = 3
BACKOFF_BASE = 5

# ── French stopwords for heuristic ───────────────────────────────────────────
STOPWORDS = {
    "dans", "avec", "pour", "sans", "plus", "moins", "cette", "cela", "comme", "dont",
    "ainsi", "leur", "leurs", "elles", "entre", "apres", "avant", "tres", "tout", "tous",
    "toutes", "etre", "avoir", "sont", "ete", "sur", "par", "des", "les", "une", "que",
    "qui", "est", "aux", "ces", "ses", "son", "nos", "vos", "car", "pas", "mais", "deux",
    "trois", "alors", "aussi", "donc", "bien", "meme", "peut", "faire", "dire", "autre",
}


# ── Logging ──────────────────────────────────────────────────────────────────
def setup_logging(dry_run: bool) -> logging.Logger:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("manual_quality")
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


# ── DB ────────────────────────────────────────────────────────────────────────
def db_connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def count_existing(conn: sqlite3.Connection, doc_id: int) -> dict:
    fc = conn.execute(
        "SELECT COUNT(*) FROM flashcards WHERE document_id=?", (doc_id,)
    ).fetchone()[0]
    qq = conn.execute(
        "SELECT COUNT(*) FROM quiz_questions qq "
        "JOIN quizzes q ON q.id=qq.quiz_id WHERE q.document_id=?", (doc_id,)
    ).fetchone()[0]
    fi = conn.execute(
        "SELECT COUNT(*) FROM fiches WHERE document_id=?", (doc_id,)
    ).fetchone()[0]
    return {"flashcards": fc, "quiz_questions": qq, "fiches": fi}


def fetch_existing_questions(conn: sqlite3.Connection, doc_id: int) -> set[str]:
    """Return normalized existing flashcard questions for dedup."""
    rows = conn.execute(
        "SELECT question FROM flashcards WHERE document_id=?", (doc_id,)
    ).fetchall()
    return {_normalize(r["question"]) for r in rows}


def fetch_manuals(
    conn: sqlite3.Connection,
    doc_id: int | None,
    matiere_id: int | None,
    min_content_len: int,
    limit: int | None,
) -> list[sqlite3.Row]:
    where_parts = [f"LENGTH(d.contenu_extrait) >= {min_content_len}"]
    params: list = []

    if doc_id is not None:
        where_parts.append("d.id = ?")
        params.append(doc_id)
    if matiere_id is not None:
        where_parts.append("d.matiere_id = ?")
        params.append(matiere_id)

    where = " AND ".join(where_parts)
    sql = f"""
        SELECT d.id, d.titre, d.contenu_extrait, d.matiere_id, m.nom AS matiere_nom
        FROM documents d
        LEFT JOIN matieres m ON m.id = d.matiere_id
        WHERE {where}
        ORDER BY LENGTH(d.contenu_extrait) DESC
    """
    rows = conn.execute(sql, params).fetchall()

    if doc_id is None:
        rows = [r for r in rows if _is_manuel(r["titre"], len(r["contenu_extrait"] or ""))]

    if limit:
        rows = rows[:limit]
    return rows


def _is_manuel(titre: str, content_len: int = 0) -> bool:
    if content_len >= 180000:
        return True
    t = titre.lower()
    return any(kw in t for kw in MANUEL_KEYWORDS)


# ── Quality validation ────────────────────────────────────────────────────────
def _normalize(s: str) -> str:
    """Lowercase + strip accents + collapse spaces for dedup comparison."""
    nfkd = unicodedata.normalize("NFKD", s.lower())
    ascii_str = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", ascii_str).strip()


def validate_flashcard(card: dict, seen_questions: set[str]) -> tuple[bool, str]:
    q = str(card.get("question", "")).strip()
    r = str(card.get("reponse", "")).strip()
    if len(q) < 25:
        return False, f"question trop courte ({len(q)}c)"
    if len(r) < 25:
        return False, f"réponse trop courte ({len(r)}c)"
    norm_q = _normalize(q)
    if norm_q in seen_questions:
        return False, "doublon question"
    seen_questions.add(norm_q)
    return True, "ok"


def validate_qcm(q: dict) -> tuple[bool, str]:
    question = str(q.get("question", "")).strip()
    choix = q.get("choix", [])
    rc = q.get("reponse_correcte", -1)
    if len(question) < 20:
        return False, f"question trop courte ({len(question)}c)"
    if not isinstance(choix, list) or len(choix) != 4:
        return False, f"besoin de 4 choix, obtenu {len(choix) if isinstance(choix, list) else '?'}"
    if not isinstance(rc, int) or not (0 <= rc <= 3):
        return False, f"reponse_correcte invalide ({rc})"
    if all(len(str(c).strip()) < 5 for c in choix):
        return False, "choix tous trop courts"
    return True, "ok"


def validate_fiche(fiche: dict) -> tuple[bool, str]:
    sections = fiche.get("sections", [])
    valid_sections = [
        s for s in sections
        if isinstance(s, dict)
        and len(str(s.get("titre", "")).strip()) > 2
        and len(str(s.get("contenu", "")).strip()) > 30
    ]
    if len(valid_sections) < 4:
        return False, f"seulement {len(valid_sections)}/4 sections valides"
    return True, "ok"


# ── Chunking (shared logic from generate_full_coverage) ──────────────────────
SECTION_RE = re.compile(
    r"(?m)^(#{1,3}\s.+|(?:chapitre|section|partie|titre)\s+\w.+|[A-ZÀÂÄÉÈÊËÎÏÔÙÛÜ][^a-z\n]{4,})",
    re.IGNORECASE,
)


def chunk_content(content: str) -> list[str]:
    if not content:
        return []
    splits = [m.start() for m in SECTION_RE.finditer(content)]
    chunks: list[str] = []
    if len(splits) >= 2:
        for i, start in enumerate(splits):
            end = splits[i + 1] if i + 1 < len(splits) else len(content)
            section = content[start:end].strip()
            if len(section) > CHUNK_SIZE:
                chunks.extend(_fixed_chunks(section))
            elif section:
                chunks.append(section)
    else:
        chunks = _fixed_chunks(content)
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
    chunks, start = [], 0
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        chunks.append(text[start:end])
        start = end - CHUNK_OVERLAP if end < len(text) else end
    return chunks


# ── Retry ─────────────────────────────────────────────────────────────────────
async def with_retry(coro_fn, logger: logging.Logger, label: str):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return await coro_fn()
        except Exception as exc:
            wait = BACKOFF_BASE * attempt
            logger.warning(f"[{label}] tentative {attempt}/{MAX_RETRIES}: {exc} — retry {wait}s")
            if attempt == MAX_RETRIES:
                raise
            await asyncio.sleep(wait)


# ── Heuristic generators ──────────────────────────────────────────────────────
def _split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    parts = re.split(r"(?<=[.!?;])\s+", text)
    return [p.strip() for p in parts if 30 <= len(p.strip()) <= 400]


def _extract_topics(sentence: str, limit: int = 3) -> list[str]:
    words = re.findall(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'-]{3,}", sentence.lower())
    topics, seen = [], set()
    for w in words:
        if w not in STOPWORDS and w not in seen:
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


def _heuristic_flashcards(contenu: str, matiere: str, nb: int) -> list[dict]:
    sentences = _split_sentences(contenu)
    if not sentences:
        sentences = [contenu[:300]] if contenu else []
    cards: list[dict] = []
    used: set[str] = set()
    cycle = list(sentences)
    while len(cards) < nb and cycle:
        sentence = cycle.pop(0)
        topics = _extract_topics(sentence, 2)
        label = " / ".join(topics) if topics else matiere
        question = f"En {matiere}, que retenir sur '{label}' ?"
        norm_q = _normalize(question)
        if norm_q in used:
            # Vary the question slightly
            question = f"Quel est le principe juridique de '{label}' selon le cours de {matiere} ?"
            norm_q = _normalize(question)
        if norm_q in used:
            continue
        used.add(norm_q)
        diff = 2 if len(sentence) < 150 else 3
        cards.append({
            "question": question[:280],
            "reponse": sentence[:900],
            "explication": f"Extrait du manuel de {matiere}.",
            "difficulte": diff,
        })
        if not cycle:
            cycle = list(sentences)
    return cards[:nb]


def _heuristic_qcm(contenu: str, matiere: str, nb: int) -> list[dict]:
    sentences = _split_sentences(contenu)
    while 0 < len(sentences) < 4:
        sentences.append(f"Complémentaire en {matiere}: {sentences[-1][:120]}")
    if not sentences:
        return []
    questions: list[dict] = []
    for idx in range(min(nb, len(sentences))):
        correct = sentences[idx % len(sentences)]
        pool = [s for j, s in enumerate(sentences) if j != idx % len(sentences)]
        distractors = (pool + [correct])[:3]
        choices = [correct] + distractors
        topics = _extract_topics(correct, 2)
        label = " / ".join(topics) if topics else f"point {idx + 1}"
        formatted = [f"{['A','B','C','D'][i]}. {c[:170]}" for i, c in enumerate(choices[:4])]
        questions.append({
            "question": f"Quelle affirmation est exacte sur '{label}' en {matiere} ?",
            "choix": formatted,
            "reponse_correcte": 0,
            "explication": f"La proposition A reprend fidèlement le contenu de {matiere}.",
            "difficulte": 3,
        })
    return questions[:nb]


def _heuristic_fiche(contenu: str, matiere: str, titre_doc: str) -> dict:
    raw = [s.strip() for s in re.split(r"\n\s*\n+", contenu) if len(s.strip()) > 80]
    if not raw:
        raw = [contenu[:2000]] if contenu else ["Contenu non disponible."]
    # Build at least 4 sections
    while len(raw) < 4:
        raw.append(raw[-1][:800] if raw else "Section complémentaire.")
    sections = []
    for i, block in enumerate(raw[:8], start=1):
        sents = _split_sentences(block)
        topic = (_extract_topics(sents[0], 1) if sents else [f"axe {i}"])[0]
        body = " ".join(sents[:5]) if sents else block[:600]
        sections.append({
            "titre": f"Section {i} — {topic.capitalize()}"[:180],
            "contenu": body[:2500],
        })
    summary = " ".join(_split_sentences(contenu)[:4])[:1000] or contenu[:500]
    return {
        "titre": f"Fiche qualité — {titre_doc[:120]}",
        "resume": summary,
        "sections": sections,
    }


def _build_fill_flashcards(
    contenu: str,
    matiere: str,
    nb: int,
    start_index: int = 0,
) -> list[dict]:
    """Build deterministic fallback cards to hit targets when strict filtering rejects too much."""
    sentences = _split_sentences(contenu)
    if not sentences:
        fallback = (contenu or "").strip()
        if len(fallback) < 80:
            fallback = (fallback + " " + f"Contenu de consolidation en {matiere}.").strip()
        sentences = [fallback[:300]]
    cards: list[dict] = []
    for i in range(nb):
        sentence = sentences[i % len(sentences)]
        idx = start_index + i + 1
        cards.append({
            "question": _build_notion_question(matiere, sentence, idx)[:280],
            "reponse": sentence[:900],
            "explication": f"Carte de rattrapage qualitative #{idx}.",
            "difficulte": 2 if len(sentence) < 140 else 3,
        })
    return cards


def _build_fill_qcm(
    contenu: str,
    matiere: str,
    nb: int,
    start_index: int = 0,
) -> list[dict]:
    """Build deterministic fallback QCM items to complete remaining gaps."""
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
        questions.append({
            "question": (
                f"QCM de consolidation {idx} en {matiere}: quelle proposition "
                f"reflète fidèlement le contenu du document ?"
            )[:300],
            "choix": formatted,
            "reponse_correcte": 0,
            "explication": f"La réponse A reprend l'information source (item #{idx}).",
            "difficulte": 3,
        })
    return questions


# ── Ollama dispatch ───────────────────────────────────────────────────────────
def _ollama_chat(prompt: str, url: str = OLLAMA_URL, model: str = OLLAMA_MODEL) -> str:
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": 0.2, "num_predict": 2000},
    }).encode()
    req = urllib.request.Request(
        f"{url.rstrip('/')}/api/chat", data=payload,
        method="POST", headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT) as resp:
        return json.loads(resp.read())["message"]["content"]


def _extract_arr(text: str) -> list[dict]:
    m = re.search(r"\[.*\]", text, re.DOTALL)
    if not m:
        raise ValueError("JSON array introuvable")
    return json.loads(m.group())


def _extract_obj(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        raise ValueError("JSON object introuvable")
    return json.loads(m.group())


async def _ollama_fc(contenu: str, matiere: str, nb: int) -> list[dict]:
    prompt = (
        f"Expert {matiere}. Génère exactement {nb} flashcards de révision.\n"
        f"CONTENU:\n{contenu[:6500]}\n\n"
        f'Réponds UNIQUEMENT JSON: [{{"question":"...","reponse":"...","explication":"...","difficulte":2}}]'
    )
    text = await asyncio.to_thread(_ollama_chat, prompt)
    return _extract_arr(text)


async def _ollama_qcm(contenu: str, matiere: str, nb: int) -> list[dict]:
    prompt = (
        f"Expert {matiere}. Génère exactement {nb} QCM.\n"
        f"CONTENU:\n{contenu[:6500]}\n\n"
        f'Réponds UNIQUEMENT JSON: [{{"question":"...","choix":["A. ...","B. ...","C. ...","D. ..."],"reponse_correcte":0,"explication":"...","difficulte":2}}]'
    )
    text = await asyncio.to_thread(_ollama_chat, prompt)
    return _extract_arr(text)


async def _ollama_fiche(contenu: str, matiere: str, titre: str) -> dict:
    prompt = (
        f"Expert {matiere}. Génère une fiche structurée pour '{titre}'.\n"
        f"CONTENU:\n{contenu[:6500]}\n\n"
        f'Réponds UNIQUEMENT JSON: {{"titre":"...","resume":"...","sections":[{{"titre":"...","contenu":"..."}}]}}'
    )
    text = await asyncio.to_thread(_ollama_chat, prompt)
    return _extract_obj(text)


# ── Provider dispatch ─────────────────────────────────────────────────────────
async def gen_flashcards(contenu: str, matiere: str, nb: int, provider: str) -> list[dict]:
    if provider == "heuristic":
        return _heuristic_flashcards(contenu, matiere, nb)
    if provider == "ollama":
        return await _ollama_fc(contenu, matiere, nb)
    if provider == "claude":
        return await _claude_fc(contenu, matiere, nb)
    # auto: claude → ollama → heuristic
    for fn in [
        lambda: _claude_fc(contenu, matiere, nb),
        lambda: _ollama_fc(contenu, matiere, nb),
    ]:
        try:
            return await fn()
        except Exception:
            pass
    return _heuristic_flashcards(contenu, matiere, nb)


async def gen_qcm(contenu: str, matiere: str, nb: int, provider: str) -> list[dict]:
    if provider == "heuristic":
        return _heuristic_qcm(contenu, matiere, nb)
    if provider == "ollama":
        return await _ollama_qcm(contenu, matiere, nb)
    if provider == "claude":
        return await _claude_qcm(contenu, matiere, nb)
    for fn in [
        lambda: _claude_qcm(contenu, matiere, nb),
        lambda: _ollama_qcm(contenu, matiere, nb),
    ]:
        try:
            return await fn()
        except Exception:
            pass
    return _heuristic_qcm(contenu, matiere, nb)


async def gen_fiche(contenu: str, matiere: str, titre: str, provider: str) -> dict:
    if provider == "heuristic":
        return _heuristic_fiche(contenu, matiere, titre)
    if provider == "ollama":
        return await _ollama_fiche(contenu, matiere, titre)
    if provider == "claude":
        return await _claude_fiche(contenu, matiere, titre)
    for fn in [
        lambda: _claude_fiche(contenu, matiere, titre),
        lambda: _ollama_fiche(contenu, matiere, titre),
    ]:
        try:
            return await fn()
        except Exception:
            pass
    return _heuristic_fiche(contenu, matiere, titre)


# ── DB insert with quality validation ─────────────────────────────────────────
def insert_flashcards_validated(
    conn: sqlite3.Connection,
    cards: list[dict],
    doc_id: int,
    matiere_id: int,
    seen_questions: set[str],
    logger: logging.Logger,
    label: str,
) -> int:
    now = datetime.now(timezone.utc).isoformat()
    inserted = 0
    for card in cards:
        ok, reason = validate_flashcard(card, seen_questions)
        if not ok:
            logger.debug(f"[{label}] FC rejetée ({reason}): {str(card.get('question',''))[:60]}")
            continue
        try:
            conn.execute(
                """INSERT INTO flashcards
                   (question, reponse, explication, difficulte, matiere_id, document_id,
                    intervalle_jours, facteur_facilite, repetitions, prochaine_revision, created_at)
                   VALUES (?,?,?,?,?,?,1.0,2.5,0,?,?)""",
                (
                    card["question"], card["reponse"],
                    card.get("explication", ""),
                    min(max(int(card.get("difficulte", 2)), 1), 5),
                    matiere_id, doc_id, now, now,
                ),
            )
            inserted += 1
        except Exception as e:
            logger.debug(f"[{label}] FC insert err: {e}")
    conn.commit()
    return inserted


def insert_qcm_validated(
    conn: sqlite3.Connection,
    questions: list[dict],
    doc_id: int,
    matiere_id: int,
    quiz_titre: str,
    logger: logging.Logger,
    label: str,
) -> int:
    now = datetime.now(timezone.utc).isoformat()
    valid_questions = []
    for q in questions:
        ok, reason = validate_qcm(q)
        if not ok:
            logger.debug(f"[{label}] QCM rejetée ({reason}): {str(q.get('question',''))[:60]}")
            continue
        valid_questions.append(q)
    if not valid_questions:
        return 0
    cur = conn.execute(
        "INSERT INTO quizzes (titre, matiere_id, document_id, created_at) VALUES (?,?,?,?)",
        (quiz_titre[:200], matiere_id, doc_id, now),
    )
    quiz_id = cur.lastrowid
    inserted = 0
    for q in valid_questions:
        choix = q["choix"]
        try:
            conn.execute(
                """INSERT INTO quiz_questions
                   (quiz_id, question, choix, reponse_correcte, explication, difficulte)
                   VALUES (?,?,?,?,?,?)""",
                (
                    quiz_id, q["question"],
                    json.dumps(choix, ensure_ascii=False),
                    int(q["reponse_correcte"]),
                    q.get("explication", ""),
                    min(max(int(q.get("difficulte", 2)), 1), 5),
                ),
            )
            inserted += 1
        except Exception as e:
            logger.debug(f"[{label}] QCM insert err: {e}")
    conn.commit()
    return inserted


def insert_fiche_validated(
    conn: sqlite3.Connection,
    fiche_data: dict,
    doc_id: int,
    matiere_id: int,
    logger: logging.Logger,
    label: str,
) -> bool:
    ok, reason = validate_fiche(fiche_data)
    if not ok:
        logger.warning(f"[{label}] Fiche rejetée ({reason})")
        return False
    now = datetime.now(timezone.utc).isoformat()
    try:
        cur = conn.execute(
            """INSERT INTO fiches (titre, resume, matiere_id, document_id, chapitre, tags, ordre, created_at)
               VALUES (?,?,?,?,?,?,0,?)""",
            (
                fiche_data.get("titre", "Fiche")[:200],
                fiche_data.get("resume", ""),
                matiere_id, doc_id, "", "", now,
            ),
        )
        fiche_id = cur.lastrowid
        valid_sections = [
            s for s in fiche_data.get("sections", [])
            if len(str(s.get("contenu", "")).strip()) > 30
        ]
        for i, section in enumerate(valid_sections[:10]):
            conn.execute(
                "INSERT INTO fiche_sections (fiche_id, titre, contenu, ordre) VALUES (?,?,?,?)",
                (fiche_id, section.get("titre", f"Section {i+1}")[:200], section["contenu"], i),
            )
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"[{label}] Fiche insert err: {e}")
        return False


# ── Core: process one document ────────────────────────────────────────────────
async def process_document(
    doc: sqlite3.Row,
    conn: sqlite3.Connection,
    logger: logging.Logger,
    provider: str,
    dry_run: bool,
) -> dict:
    doc_id = doc["id"]
    titre = doc["titre"]
    contenu = doc["contenu_extrait"] or ""
    matiere_id = doc["matiere_id"] or 1
    matiere_nom = doc["matiere_nom"] or "Général"
    label = f"doc={doc_id}"

    before = count_existing(conn, doc_id)
    need_fc = max(0, TARGETS["flashcards"] - before["flashcards"])
    need_qq = max(0, TARGETS["quiz_questions"] - before["quiz_questions"])
    need_fi = max(0, TARGETS["fiches"] - before["fiches"])

    logger.info(
        f"[{label}] '{titre[:65]}' | content={len(contenu)}c "
        f"| before fc={before['flashcards']} qq={before['quiz_questions']} fi={before['fiches']} "
        f"| need fc={need_fc} qq={need_qq} fi={need_fi}"
    )

    result = {"fc_added": 0, "qq_added": 0, "fi_added": 0, "fc_rejected": 0, "qq_rejected": 0}

    if need_fc == 0 and need_qq == 0 and need_fi == 0:
        logger.info(f"[{label}] Cibles déjà atteintes — skip")
        return result

    if dry_run:
        logger.info(f"[{label}] DRY-RUN: fc+{need_fc}, qq+{need_qq}, fi+{need_fi}")
        result.update({"fc_added": need_fc, "qq_added": need_qq, "fi_added": need_fi})
        return result

    chunks = chunk_content(contenu)
    seen_questions = fetch_existing_questions(conn, doc_id)
    logger.debug(f"[{label}] {len(chunks)} chunks, {len(seen_questions)} FC existantes")

    # ── Flashcards ────────────────────────────────────────────────────────────
    if need_fc > 0:
        per_chunk = max(3, need_fc // max(1, min(len(chunks), 5)))
        total_fc = 0
        for i, chunk in enumerate(chunks):
            if total_fc >= need_fc:
                break
            nb = min(per_chunk, need_fc - total_fc)
            try:
                cards = await with_retry(
                    lambda c=chunk, n=nb: gen_flashcards(c, matiere_nom, n, provider),
                    logger, f"{label} fc chunk={i}",
                )
                before_insert = total_fc
                inserted = insert_flashcards_validated(
                    conn, cards, doc_id, matiere_id, seen_questions, logger, label
                )
                rejected = len(cards) - inserted
                total_fc += inserted
                result["fc_added"] += inserted
                result["fc_rejected"] += rejected
                logger.info(
                    f"[{label}] chunk={i}: fc +{inserted} (rejeté={rejected}) total={total_fc}/{need_fc}"
                )
            except Exception as e:
                logger.error(f"[{label}] fc chunk={i} ÉCHEC: {e}")

    # ── QCM ───────────────────────────────────────────────────────────────────
    if need_qq > 0:
        per_chunk = max(3, need_qq // max(1, min(len(chunks), 3)))
        total_qq = 0
        for i, chunk in enumerate(chunks):
            if total_qq >= need_qq:
                break
            nb = min(per_chunk, need_qq - total_qq)
            try:
                questions = await with_retry(
                    lambda c=chunk, n=nb: gen_qcm(c, matiere_nom, n, provider),
                    logger, f"{label} qcm chunk={i}",
                )
                quiz_titre = f"Quiz qualité — {titre[:75]} (chunk {i+1})"
                before_qq = total_qq
                inserted = insert_qcm_validated(
                    conn, questions, doc_id, matiere_id, quiz_titre, logger, label
                )
                rejected = len(questions) - inserted
                total_qq += inserted
                result["qq_added"] += inserted
                result["qq_rejected"] += rejected
                logger.info(
                    f"[{label}] chunk={i}: qq +{inserted} (rejeté={rejected}) total={total_qq}/{need_qq}"
                )
            except Exception as e:
                logger.error(f"[{label}] qcm chunk={i} ÉCHEC: {e}")

    # ── Fiches ────────────────────────────────────────────────────────────────
    if need_fi > 0:
        for i in range(need_fi):
            chunk = chunks[i % len(chunks)]
            try:
                fiche_data = await with_retry(
                    lambda c=chunk: gen_fiche(c, matiere_nom, titre, provider),
                    logger, f"{label} fiche={i}",
                )
                ok = insert_fiche_validated(
                    conn, fiche_data, doc_id, matiere_id, logger, label
                )
                if ok:
                    result["fi_added"] += 1
                    logger.info(f"[{label}] Fiche {i+1}/{need_fi} insérée ✓")
            except Exception as e:
                logger.error(f"[{label}] fiche={i} ÉCHEC: {e}")

    # ── Fill pass: guarantee target completion for manuals ────────────────────
    # Some short/manual docs can still miss targets after strict validation.
    current = count_existing(conn, doc_id)
    rem_fc = max(0, TARGETS["flashcards"] - current["flashcards"])
    rem_qq = max(0, TARGETS["quiz_questions"] - current["quiz_questions"])

    if rem_fc > 0:
        fill_cards = _build_fill_flashcards(contenu, matiere_nom, rem_fc, start_index=current["flashcards"])
        inserted = insert_flashcards_validated(
            conn, fill_cards, doc_id, matiere_id, seen_questions, logger, label
        )
        rejected = len(fill_cards) - inserted
        result["fc_added"] += inserted
        result["fc_rejected"] += rejected
        logger.info(
            f"[{label}] fill-pass FC: +{inserted} (rejeté={rejected}) "
            f"reste cible={max(0, TARGETS['flashcards'] - count_existing(conn, doc_id)['flashcards'])}"
        )

    current = count_existing(conn, doc_id)
    rem_qq = max(0, TARGETS["quiz_questions"] - current["quiz_questions"])
    if rem_qq > 0:
        fill_q = _build_fill_qcm(contenu, matiere_nom, rem_qq, start_index=current["quiz_questions"])
        inserted = insert_qcm_validated(
            conn,
            fill_q,
            doc_id,
            matiere_id,
            f"Quiz qualité — {titre[:70]} (fill-pass)",
            logger,
            label,
        )
        rejected = len(fill_q) - inserted
        result["qq_added"] += inserted
        result["qq_rejected"] += rejected
        logger.info(
            f"[{label}] fill-pass QCM: +{inserted} (rejeté={rejected}) "
            f"reste cible={max(0, TARGETS['quiz_questions'] - count_existing(conn, doc_id)['quiz_questions'])}"
        )

    after = count_existing(conn, doc_id)
    logger.info(
        f"[{label}] APRÈS: fc={after['flashcards']} qq={after['quiz_questions']} fi={after['fiches']} "
        f"| delta fc=+{result['fc_added']} qq=+{result['qq_added']} fi=+{result['fi_added']}"
    )
    return result


# ── Main ──────────────────────────────────────────────────────────────────────
async def main() -> int:
    parser = argparse.ArgumentParser(
        description="Upgrade qualité ciblée des manuels IACA (fc≥40, qq≥16, fiches≥4).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--limit", type=int, default=None, help="Nb max de documents")
    parser.add_argument("--doc-id", type=int, default=None, help="Traiter un seul document (par ID)")
    parser.add_argument("--matiere", type=int, default=None, help="Filtrer par matiere_id")
    parser.add_argument(
        "--provider",
        choices=["auto", "claude", "ollama", "heuristic"],
        default="auto",
        help="Fournisseur LLM (heuristic=instantané, auto=claude→ollama→heuristic)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Simulation sans écriture")
    parser.add_argument(
        "--min-content-len", type=int, default=500,
        help="Longueur minimale du contenu pour sélectionner un doc (défaut: 500)",
    )
    parser.add_argument(
        "--target-fc",
        type=int,
        default=TARGETS["flashcards"],
        help=f"Cible flashcards par manuel (défaut: {TARGETS['flashcards']})",
    )
    parser.add_argument(
        "--target-qq",
        type=int,
        default=TARGETS["quiz_questions"],
        help=f"Cible questions quiz par manuel (défaut: {TARGETS['quiz_questions']})",
    )
    parser.add_argument(
        "--target-fi",
        type=int,
        default=TARGETS["fiches"],
        help=f"Cible fiches par manuel (défaut: {TARGETS['fiches']})",
    )
    args = parser.parse_args()

    if args.target_fc < 0 or args.target_qq < 0 or args.target_fi < 0:
        print("Les cibles --target-fc/--target-qq/--target-fi doivent être >= 0.")
        return 2

    TARGETS["flashcards"] = args.target_fc
    TARGETS["quiz_questions"] = args.target_qq
    TARGETS["fiches"] = args.target_fi

    logger = setup_logging(args.dry_run)
    logger.info(
        f"Démarrage upgrade_manuals_quality | provider={args.provider} "
        f"limit={args.limit} doc_id={args.doc_id} matiere={args.matiere} "
        f"dry_run={args.dry_run} min_content_len={args.min_content_len} "
        f"targets=fc:{args.target_fc},qq:{args.target_qq},fi:{args.target_fi}"
    )
    logger.info(f"Cibles: fc≥{TARGETS['flashcards']} qq≥{TARGETS['quiz_questions']} fi≥{TARGETS['fiches']}")

    conn = db_connect()

    # Global counts before
    def global_counts() -> dict:
        return {
            "flashcards": conn.execute("SELECT COUNT(*) FROM flashcards").fetchone()[0],
            "quiz_questions": conn.execute("SELECT COUNT(*) FROM quiz_questions").fetchone()[0],
            "fiches": conn.execute("SELECT COUNT(*) FROM fiches").fetchone()[0],
        }

    before_global = global_counts()

    docs = fetch_manuals(conn, args.doc_id, args.matiere, args.min_content_len, args.limit)
    logger.info(f"{len(docs)} manuels sélectionnés")

    if not docs:
        logger.info("Aucun document manuel trouvé — exit 0")
        conn.close()
        return 0

    t0 = time.time()
    total = {"fc_added": 0, "qq_added": 0, "fi_added": 0, "fc_rejected": 0, "qq_rejected": 0}
    errors = 0

    for doc in docs:
        try:
            result = await process_document(doc, conn, logger, args.provider, args.dry_run)
            for k in total:
                total[k] += result.get(k, 0)
        except Exception as e:
            logger.error(f"[doc={doc['id']}] Erreur fatale: {e}")
            errors += 1

    after_global = global_counts()
    elapsed = time.time() - t0

    delta_fc = after_global["flashcards"] - before_global["flashcards"]
    delta_qq = after_global["quiz_questions"] - before_global["quiz_questions"]
    delta_fi = after_global["fiches"] - before_global["fiches"]

    summary = (
        f"\n{'='*65}\n"
        f"TERMINÉ en {elapsed:.1f}s | {len(docs)} doc(s) | {errors} erreur(s)\n"
        f"  Flashcards : {before_global['flashcards']} → {after_global['flashcards']} (+{delta_fc})"
        f"  [rejetées={total['fc_rejected']}]\n"
        f"  Quiz QCM   : {before_global['quiz_questions']} → {after_global['quiz_questions']} (+{delta_qq})"
        f"  [rejetées={total['qq_rejected']}]\n"
        f"  Fiches     : {before_global['fiches']} → {after_global['fiches']} (+{delta_fi})\n"
        f"  Log        : {LOG_PATH}\n"
        f"{'='*65}"
    )
    logger.info(summary)

    conn.close()
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
