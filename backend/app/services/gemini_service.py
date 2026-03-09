import asyncio
import json
import re

from google import genai

from app.config import settings


def _get_client():
    return genai.Client(api_key=settings.google_api_key)


def _generate_sync(prompt: str) -> str:
    """Synchronous Gemini call, to be run in a thread."""
    client = _get_client()
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )
    return response.text


async def _generate(prompt: str) -> str:
    """Run Gemini generation in a thread to avoid blocking the event loop."""
    return await asyncio.to_thread(_generate_sync, prompt)


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

    text = await _generate(prompt)
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

    text = await _generate(prompt)
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

    text = await _generate(prompt)
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if not match:
        raise ValueError("Gemini n'a pas retourné un JSON valide")
    return json.loads(match.group())
