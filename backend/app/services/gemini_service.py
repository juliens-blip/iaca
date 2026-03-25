import asyncio
import json
import logging
import re
import time

from google import genai

from app.config import settings

log = logging.getLogger(__name__)


def _get_client():
    return genai.Client(api_key=settings.google_api_key)


def _generate_sync(prompt: str) -> str:
    """Synchronous Gemini call with retry on 429, to be run in a thread."""
    client = _get_client()
    for attempt in range(1, 4):
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
            )
            return response.text
        except Exception as exc:
            if "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc):
                wait = 30 * attempt
                log.warning("Gemini 429 (attempt %d/3) — retry in %ds", attempt, wait)
                if attempt == 3:
                    raise
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("Gemini: max retries exceeded")


async def _generate(prompt: str) -> str:
    """Run Gemini generation in a thread to avoid blocking the event loop."""
    return await asyncio.to_thread(_generate_sync, prompt)


async def generate_text(prompt: str) -> str:
    """Generate plain text with Gemini for generic LLM fallback flows."""
    text = await _generate(prompt)
    if text is None:
        raise ValueError("Gemini n'a pas retourne de texte exploitable")
    return str(text).strip()


async def rechercher_ressources(sujet: str, matiere: str) -> dict:
    """Search for external learning resources related to a topic."""
    prompt = f"""Tu es un conseiller pédagogique spécialisé en {matiere} pour la préparation aux concours administratifs français.

Pour le sujet "{sujet}", recommande des ressources d'apprentissage complémentaires.

Réponds UNIQUEMENT en JSON valide:
{{
  "podcasts": [
    {{"titre": "...", "url": "...", "description": "..."}}
  ],
  "videos_youtube": [
    {{"titre": "...", "url": "https://youtube.com/...", "description": "..."}}
  ],
  "articles": [
    {{"titre": "...", "url": "...", "description": "..."}}
  ],
  "livres": [
    {{"titre": "...", "auteur": "...", "description": "..."}}
  ]
}}

Donne 2-3 ressources par catégorie. Privilégie les sources françaises et académiques."""

    text = await generate_text(prompt)
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if not match:
        raise ValueError("Gemini n'a pas retourné un JSON valide")
    return json.loads(match.group())


async def generer_mind_map(contenu: str, sujet: str) -> dict:
    """Generate a mind map structure from content."""
    prompt = f"""Crée une mind map structurée pour le sujet "{sujet}" à partir du contenu suivant.

CONTENU:
{contenu[:4000]}

Réponds UNIQUEMENT en JSON valide:
{{
  "centre": "{sujet}",
  "branches": [
    {{
      "nom": "...",
      "sous_branches": ["...", "..."],
      "details": "..."
    }}
  ]
}}

Maximum 6 branches principales, chacune avec 2-4 sous-branches."""

    text = await generate_text(prompt)
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if not match:
        raise ValueError("Gemini n'a pas retourné un JSON valide")
    return json.loads(match.group())


async def generer_chronologie(contenu: str, sujet: str) -> list[dict]:
    """Generate a timeline from content."""
    prompt = f"""Extrais une chronologie des événements importants liés à "{sujet}" depuis le contenu.

CONTENU:
{contenu[:4000]}

Réponds UNIQUEMENT en JSON valide:
[
  {{"date": "...", "evenement": "...", "importance": "haute/moyenne/basse"}}
]

Ordonne chronologiquement."""

    text = await generate_text(prompt)
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if not match:
        raise ValueError("Gemini n'a pas retourné un JSON valide")
    return json.loads(match.group())
