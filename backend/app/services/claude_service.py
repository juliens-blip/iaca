import asyncio
import difflib
import json
import logging
import os
import re
from typing import Any

log = logging.getLogger(__name__)


FICHE_MIN_SECTIONS = 6
FICHE_MAX_SECTIONS = 10
FICHE_MIN_SECTION_CHARS = 220
FICHE_MAX_SECTION_CHARS = 2400
FICHE_MIN_RESUME_CHARS = 220

GENERIC_SECTION_PATTERNS = (
    r"^section\s*\d*$",
    r"^partie\s*\d*$",
    r"^chapitre\s*\d*$",
    r"^introduction$",
    r"^conclusion$",
    r"^divers$",
    r"^synthese$",
)

ACTIONABLE_MARKERS = (
    "point d'application",
    "exemple",
    "methode",
    "méthode",
    "etape",
    "étape",
    "condition",
    "exception",
    "jurisprudence",
    "article",
    "procedure",
    "procédure",
)
EXTRACTION_ERROR_PREFIX = "[Erreur d'extraction:"
MIN_SOURCE_CONTENT_CHARS = 120


async def run_claude_cli(prompt: str, max_tokens: int = 4096) -> str:
    """Execute Claude via CLI (uses the user's Claude subscription)."""
    env = os.environ.copy()
    for key in list(env.keys()):
        if key.startswith("CLAUDE"):
            del env[key]
    cmd = ["claude", "--print", "--output-format", "text"]
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
    )
    stdout, stderr = await process.communicate(input=prompt.encode())
    if process.returncode != 0:
        raise RuntimeError(f"Claude CLI error: {stderr.decode()}")
    return stdout.decode().strip()


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _sanitize_source_content(contenu: str) -> str:
    lines = []
    for raw_line in (contenu or "").replace("\r", "").splitlines():
        if EXTRACTION_ERROR_PREFIX in raw_line:
            continue
        lines.append(raw_line)
    return _normalize_text("\n".join(lines))


def _ensure_generation_source(contenu: str) -> str:
    source = _sanitize_source_content(contenu)
    if len(source) < MIN_SOURCE_CONTENT_CHARS:
        raise ValueError("Contenu source insuffisant ou invalide pour la generation.")
    return source


def _strip_code_fences(value: str) -> str:
    text = value.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _balanced_json_candidates(text: str, open_char: str, close_char: str) -> list[str]:
    candidates: list[str] = []
    depth = 0
    start_index = -1

    for index, char in enumerate(text):
        if char == open_char:
            if depth == 0:
                start_index = index
            depth += 1
        elif char == close_char and depth > 0:
            depth -= 1
            if depth == 0 and start_index >= 0:
                candidates.append(text[start_index:index + 1])
                start_index = -1

    # Try larger candidates first to keep full payload if available.
    return sorted(candidates, key=len, reverse=True)


def _extract_json_array(raw_output: str) -> list[Any]:
    text = _strip_code_fences(raw_output)
    candidates = [text] + _balanced_json_candidates(text, "[", "]")
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            continue
    raise ValueError("Claude n'a pas retourné un JSON array valide")


def _extract_json_object(raw_output: str) -> dict[str, Any]:
    text = _strip_code_fences(raw_output)
    candidates = [text] + _balanced_json_candidates(text, "{", "}")
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue
    raise ValueError("Claude n'a pas retourné un JSON object valide")


def _is_generic_section_title(title: str) -> bool:
    lowered = _normalize_text(title).lower()
    if not lowered:
        return True
    return any(re.match(pattern, lowered) for pattern in GENERIC_SECTION_PATTERNS)


def _contains_actionable_marker(content: str) -> bool:
    lowered = content.lower()
    return any(marker in lowered for marker in ACTIONABLE_MARKERS)


def _derive_title_from_content(content: str, index: int) -> str:
    words = re.findall(r"[A-Za-zÀ-ÿ0-9][A-Za-zÀ-ÿ0-9'’\-]+", content)
    phrase = " ".join(words[:8]).strip()
    if len(phrase) < 12:
        return f"Axe clé {index + 1}"
    return phrase[0].upper() + phrase[1:90]


def _split_source_blocks(contenu: str) -> list[str]:
    if not contenu:
        return []

    raw_blocks = re.split(r"\n\s*\n+", contenu)
    blocks = [_normalize_text(block) for block in raw_blocks]
    blocks = [block for block in blocks if len(block) >= 120]

    if blocks:
        return blocks

    fallback_text = _normalize_text(contenu)
    if not fallback_text:
        return []

    chunk_size = 900
    return [fallback_text[i:i + chunk_size] for i in range(0, len(fallback_text), chunk_size)]


def _build_fallback_sections(
    contenu: str,
    needed: int,
    used_titles: set[str],
    start_index: int,
) -> list[dict[str, str]]:
    sections: list[dict[str, str]] = []
    for block in _split_source_blocks(contenu):
        if len(sections) >= needed:
            break

        content = _normalize_text(block)[:FICHE_MAX_SECTION_CHARS]
        if len(content) < FICHE_MIN_SECTION_CHARS:
            continue

        section_index = start_index + len(sections)
        title = _derive_title_from_content(content, section_index)
        if _is_generic_section_title(title) or title.lower() in used_titles:
            title = f"Axe clé {section_index + 1}"

        if not _contains_actionable_marker(content):
            content = (
                f"{content}\n\n"
                "Point d'application: identifiez la règle utile, ses conditions de mise en oeuvre "
                "et un cas pratique où l'appliquer."
            )

        used_titles.add(title.lower())
        sections.append({"titre": title, "contenu": content})

    return sections


def _sanitize_sections(raw_sections: Any, contenu: str) -> list[dict[str, str]]:
    sanitized: list[dict[str, str]] = []
    used_titles: set[str] = set()

    if isinstance(raw_sections, list):
        source_sections = raw_sections
    else:
        source_sections = []

    for raw_section in source_sections:
        if not isinstance(raw_section, dict):
            continue

        title = _normalize_text(str(raw_section.get("titre", "")))
        content = _normalize_text(str(raw_section.get("contenu", "")))

        if not content:
            continue
        if _is_generic_section_title(title):
            title = _derive_title_from_content(content, len(sanitized))

        content = content[:FICHE_MAX_SECTION_CHARS]
        if len(content) < FICHE_MIN_SECTION_CHARS:
            continue
        if title.lower() in used_titles:
            continue
        if not _contains_actionable_marker(content) and len(content) < 320:
            continue

        used_titles.add(title.lower())
        sanitized.append({"titre": title, "contenu": content})

        if len(sanitized) >= FICHE_MAX_SECTIONS:
            break

    if len(sanitized) < FICHE_MIN_SECTIONS:
        needed = FICHE_MIN_SECTIONS - len(sanitized)
        sanitized.extend(_build_fallback_sections(contenu, needed, used_titles, len(sanitized)))

    return sanitized[:FICHE_MAX_SECTIONS]


def _build_resume(raw_resume: Any, sections: list[dict[str, str]], contenu: str) -> str:
    resume = _normalize_text(str(raw_resume or ""))
    if len(resume) >= FICHE_MIN_RESUME_CHARS:
        return resume[:1400]

    if sections:
        merged = " ".join(section["contenu"] for section in sections[:2])
        resume = _normalize_text(merged)

    if len(resume) < FICHE_MIN_RESUME_CHARS:
        resume = _normalize_text(contenu)[:1400]

    return resume[:1400]


def _sanitize_fiche_payload(payload: Any, contenu: str, titre_doc: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        payload = {}

    title = _normalize_text(str(payload.get("titre", "")))
    if len(title) < 8:
        title = f"Fiche - {titre_doc}"

    sections = _sanitize_sections(payload.get("sections", []), contenu)
    if not sections:
        sections = _build_fallback_sections(contenu, FICHE_MIN_SECTIONS, set(), 0)

    resume = _build_resume(payload.get("resume", ""), sections, contenu)

    return {
        "titre": title[:180],
        "resume": resume,
        "sections": sections,
    }


def _validate_flashcard(card: dict) -> bool:
    """Reject cards with trivially short or self-identical fields."""
    question = _normalize_text(str(card.get("question", "")))
    reponse = _normalize_text(str(card.get("reponse", "")))
    if len(question) < 20:
        log.warning("[validate_flashcard] rejetee — question trop courte (%d chars): %r", len(question), question[:60])
        return False
    if len(reponse) < 30:
        log.warning("[validate_flashcard] rejetee — reponse trop courte (%d chars): %r", len(reponse), reponse[:60])
        return False
    if question.lower() == reponse.lower():
        log.warning("[validate_flashcard] rejetee — question == reponse: %r", question[:60])
        return False
    return True


def _validate_fiche_section(section: dict, source_chunk: str = "") -> bool:
    """Reject sections with generic titles, short content, or near-verbatim copy of source."""
    titre = _normalize_text(str(section.get("titre", "")))
    contenu = _normalize_text(str(section.get("contenu", "")))
    if _is_generic_section_title(titre):
        log.warning("[validate_section] rejetee — titre generique: %r", titre)
        return False
    if len(contenu) < 150:
        log.warning("[validate_section] rejetee — contenu trop court (%d chars): titre=%r", len(contenu), titre)
        return False
    if source_chunk:
        ratio = difflib.SequenceMatcher(None, contenu[:500], source_chunk[:500]).ratio()
        if ratio > 0.85:
            log.warning("[validate_section] rejetee — trop proche du source (ratio=%.2f): titre=%r", ratio, titre)
            return False
    return True


def chunk_content(markdown_text: str, max_chars: int = 4000) -> list[str]:
    """Split markdown text into chunks of ~max_chars by section headers (##, ###).

    If a section exceeds max_chars it is further split at paragraph boundaries.
    """
    if not markdown_text:
        return []

    section_pattern = re.compile(r"^#{1,3} .+", re.MULTILINE)
    matches = list(section_pattern.finditer(markdown_text))

    if not matches:
        raw_chunks = [
            markdown_text[i:i + max_chars]
            for i in range(0, len(markdown_text), max_chars)
        ]
        return [c.strip() for c in raw_chunks if c.strip()]

    boundaries = [m.start() for m in matches] + [len(markdown_text)]
    raw_sections = [
        markdown_text[boundaries[i]:boundaries[i + 1]].strip()
        for i in range(len(matches))
    ]

    chunks: list[str] = []
    current = ""
    for section in raw_sections:
        if len(section) > max_chars:
            if current:
                chunks.append(current.strip())
                current = ""
            paragraphs = re.split(r"\n\s*\n+", section)
            buf = ""
            for para in paragraphs:
                if len(buf) + len(para) + 2 > max_chars and buf:
                    chunks.append(buf.strip())
                    buf = para
                else:
                    buf = (buf + "\n\n" + para).strip() if buf else para
            if buf:
                chunks.append(buf.strip())
        elif len(current) + len(section) + 2 > max_chars:
            if current:
                chunks.append(current.strip())
            current = section
        else:
            current = (current + "\n\n" + section).strip() if current else section

    if current:
        chunks.append(current.strip())

    return [c for c in chunks if c]


async def generer_flashcards(contenu: str, matiere: str, nb: int = 10) -> list[dict]:
    """Generate flashcards from document content using Claude with chunking."""
    source = _ensure_generation_source(contenu)
    chunks = chunk_content(source, max_chars=4000)
    if not chunks:
        chunks = [source[:4000]]

    nb_chunks = len(chunks)
    nb_per_chunk = max(5, nb // nb_chunks)

    all_cards: list[dict] = []
    for chunk in chunks:
        prompt = f"""Tu es un expert en {matiere} pour la preparation aux concours administratifs francais.

A partir du contenu suivant, genere exactement {nb_per_chunk} flashcards de revision.

REGLES IMPERATIVES:
- REFORMULE et ADAPTE: ne copie pas le texte source mot pour mot.
- Chaque question doit tester la COMPREHENSION (application, raisonnement, distinction de notions).
- La reponse doit etre une synthese reformulee, pas un extrait brut.
- L'explication doit apporter un eclairage complementaire (exemple concret, jurisprudence, methode).

CONTENU:
{chunk}

Reponds UNIQUEMENT en JSON valide, sans texte avant ou apres:
[
  {{
    "question": "...",
    "reponse": "...",
    "explication": "...",
    "difficulte": 1
  }}
]

Difficulte de 1 (basique) a 5 (expert)."""

        result = await run_claude_cli(prompt)
        parsed = _extract_json_array(result)
        raw_cards = [item for item in parsed if isinstance(item, dict)]
        valid_cards = [c for c in raw_cards if _validate_flashcard(c)]
        if raw_cards and len(valid_cards) < len(raw_cards) * 0.5:
            log.warning(
                "[generer_flashcards] chunk %d/%d: seulement %d/%d cartes valides — regeneration",
                chunks.index(chunk) + 1, nb_chunks, len(valid_cards), len(raw_cards),
            )
            result2 = await run_claude_cli(prompt)
            parsed2 = _extract_json_array(result2)
            valid_cards2 = [c for c in parsed2 if isinstance(c, dict) and _validate_flashcard(c)]
            if len(valid_cards2) > len(valid_cards):
                valid_cards = valid_cards2
        all_cards.extend(valid_cards)

    return all_cards[:nb] if len(all_cards) > nb else all_cards


async def generer_qcm(contenu: str, matiere: str, nb: int = 5) -> list[dict]:
    """Generate QCM questions from document content using Claude with chunking."""
    source = _ensure_generation_source(contenu)
    chunks = chunk_content(source, max_chars=4000)
    if not chunks:
        chunks = [source[:4000]]

    nb_chunks = len(chunks)
    nb_per_chunk = max(2, nb // nb_chunks)

    all_qcm: list[dict] = []
    for chunk in chunks:
        prompt = f"""Tu es un expert en {matiere} pour la preparation aux concours administratifs francais.

A partir du contenu suivant, genere exactement {nb_per_chunk} questions a choix multiples.

REGLES IMPERATIVES:
- REFORMULE et ADAPTE: ne copie pas le texte source mot pour mot.
- Chaque question doit tester la COMPREHENSION (application, distinction de notions, cas pratique).
- Les choix incorrects doivent etre plausibles (erreurs classiques, confusions courantes).
- L'explication doit justifier le bon choix avec un eclairage pedagogique (exemple, jurisprudence, methode).

CONTENU:
{chunk}

Reponds UNIQUEMENT en JSON valide, sans texte avant ou apres:
[
  {{
    "question": "...",
    "choix": ["A. ...", "B. ...", "C. ...", "D. ..."],
    "reponse_correcte": 0,
    "explication": "...",
    "difficulte": 1
  }}
]

reponse_correcte = index (0-3) du bon choix. Difficulte de 1 a 5."""

        result = await run_claude_cli(prompt)
        parsed = _extract_json_array(result)
        all_qcm.extend(item for item in parsed if isinstance(item, dict))

    return all_qcm[:nb] if len(all_qcm) > nb else all_qcm


async def generer_fiche(contenu: str, matiere: str, titre_doc: str) -> dict:
    """Generate a structured revision sheet from document content using Claude with chunking."""
    source = _ensure_generation_source(contenu)
    chunks = chunk_content(source, max_chars=4000)
    if not chunks:
        chunks = [source[:4000]]

    all_sections: list[dict] = []
    resume_parts: list[str] = []

    for idx, chunk in enumerate(chunks):
        chunk_label = f"partie {idx + 1}/{len(chunks)}"
        prompt = f"""Tu es un redacteur pedagogique expert en {matiere} pour les concours administratifs francais.

Objectif: generer des sections de fiche de revision pedagogique a partir d'une {chunk_label} du document.

DOCUMENT: {titre_doc}

CONTENU SOURCE ({chunk_label}):
{chunk}

REGLES IMPERATIVES:
- REFORMULE completement: ne copie pas le texte source mot pour mot.
- Chaque section doit REFORMULER et SYNTHETISER les notions en langage pedagogique clair.
- Inclure obligatoirement pour chaque section: definition reformulee, conditions/exceptions, exemple concret ou jurisprudence, methode d'application.
- PAS d'extraction brute, PAS de copier-coller du source.

Reponds UNIQUEMENT en JSON valide, sans markdown, sans texte avant/apres:
{{
  "resume_partiel": "Synthese pedagogique de cette partie en 60-100 mots (pas un extrait brut)",
  "sections": [
    {{
      "titre": "Titre specifique et explicite (pas: Introduction, Divers, Section 1)",
      "contenu": "150 a 280 mots: definition reformulee + conditions/exceptions + exemple ou jurisprudence + point d'application"
    }}
  ]
}}

Contraintes: 2 a 4 sections pour cette partie. Titres distincts et precis. Aucune section vide."""

        result = await run_claude_cli(prompt)
        payload = _extract_json_object(result)
        raw_sections = [s for s in (payload.get("sections") or []) if isinstance(s, dict)]
        valid_sections = [s for s in raw_sections if _validate_fiche_section(s, chunk)]
        if raw_sections and not valid_sections:
            log.warning(
                "[generer_fiche] chunk %d/%d: 0 sections valides sur %d — regeneration",
                idx + 1, len(chunks), len(raw_sections),
            )
            result2 = await run_claude_cli(prompt)
            payload2 = _extract_json_object(result2)
            raw_sections2 = [s for s in (payload2.get("sections") or []) if isinstance(s, dict)]
            valid_sections2 = [s for s in raw_sections2 if _validate_fiche_section(s, chunk)]
            if valid_sections2:
                valid_sections = valid_sections2
                payload = payload2
        all_sections.extend(valid_sections)
        if payload.get("resume_partiel"):
            resume_parts.append(str(payload["resume_partiel"]).strip())

    assembled_resume = " ".join(resume_parts)
    assembled_payload = {
        "titre": f"Fiche - {titre_doc}",
        "resume": assembled_resume,
        "sections": all_sections,
    }
    return _sanitize_fiche_payload(assembled_payload, source, titre_doc)


async def analyser_document(contenu: str) -> dict:
    """Analyze a document to extract key concepts, summary, tags."""
    source = _ensure_generation_source(contenu)
    prompt = f"""Analyse ce document académique et extrais les informations structurées.

CONTENU:
{source[:6000]}

Réponds UNIQUEMENT en JSON valide:
{{
  "resume": "résumé en 3-5 phrases",
  "concepts_cles": ["concept1", "concept2", ...],
  "tags": ["tag1", "tag2", ...],
  "matiere_suggeree": "nom de la matière",
  "difficulte_estimee": 3
}}"""

    result = await run_claude_cli(prompt)
    return _extract_json_object(result)
