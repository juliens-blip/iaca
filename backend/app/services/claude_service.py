import asyncio
import json
import os
import re
from typing import Any


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


async def generer_flashcards(contenu: str, matiere: str, nb: int = 10) -> list[dict]:
    """Generate flashcards from document content using Claude."""
    source = _ensure_generation_source(contenu)
    prompt = f"""Tu es un expert en {matiere} pour la préparation aux concours administratifs français.

À partir du contenu suivant, génère exactement {nb} flashcards de révision.

CONTENU:
{source[:8000]}

Réponds UNIQUEMENT en JSON valide, sans texte avant ou après:
[
  {{
    "question": "...",
    "reponse": "...",
    "explication": "...",
    "difficulte": 1
  }}
]

Difficulté de 1 (basique) à 5 (expert). Les questions doivent tester la compréhension, pas juste la mémorisation."""

    result = await run_claude_cli(prompt)
    parsed = _extract_json_array(result)
    return [item for item in parsed if isinstance(item, dict)]


async def generer_qcm(contenu: str, matiere: str, nb: int = 5) -> list[dict]:
    """Generate QCM questions from document content using Claude."""
    source = _ensure_generation_source(contenu)
    prompt = f"""Tu es un expert en {matiere} pour la préparation aux concours administratifs français.

À partir du contenu suivant, génère exactement {nb} questions à choix multiples.

CONTENU:
{source[:8000]}

Réponds UNIQUEMENT en JSON valide, sans texte avant ou après:
[
  {{
    "question": "...",
    "choix": ["A. ...", "B. ...", "C. ...", "D. ..."],
    "reponse_correcte": 0,
    "explication": "...",
    "difficulte": 1
  }}
]

reponse_correcte = index (0-3) du bon choix. Difficulté de 1 à 5.
Inclus des cas pratiques juridiques quand pertinent."""

    result = await run_claude_cli(prompt)
    parsed = _extract_json_array(result)
    return [item for item in parsed if isinstance(item, dict)]


async def generer_fiche(contenu: str, matiere: str, titre_doc: str) -> dict:
    """Generate a structured revision sheet from document content using Claude."""
    source = _ensure_generation_source(contenu)
    prompt = f"""Tu es un redacteur pedagogique expert en {matiere} pour les concours administratifs francais.

Objectif: generer une fiche de revision de haute precision, exploitable sans ambiguite.

DOCUMENT: {titre_doc}

CONTENU SOURCE:
{source[:8000]}

Reponds UNIQUEMENT en JSON valide, sans markdown, sans texte avant/apres:
{{
  "titre": "Titre explicite de la fiche",
  "resume": "Resume operationnel en 140 a 240 mots",
  "sections": [
    {{
      "titre": "Titre specifique (pas generique)",
      "contenu": "120 a 260 mots incluant definitions, conditions, exceptions, methode, exemple ou point d'application"
    }}
  ]
}}

Contraintes obligatoires:
- 8 a 10 sections distinctes.
- Couvrir les grands themes du document (pas uniquement un angle).
- Interdits: sections vides, titres vagues (ex: Introduction, Divers, Section 1), phrases creuses.
- Chaque section doit contenir au moins un element actionnable (exemple, methode, point d'application, erreur frequente).
- Style clair, concret, pedagogique."""

    result = await run_claude_cli(prompt)
    payload = _extract_json_object(result)
    return _sanitize_fiche_payload(payload, source, titre_doc)


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
