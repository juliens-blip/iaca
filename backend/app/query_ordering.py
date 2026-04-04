"""
Helpers de tri pour servir les contenus dans un ordre pedagogique stable.
"""

from sqlalchemy import case, func

from app.models.document import Document
from app.models.fiche import Fiche
from app.models.flashcard import Flashcard
from app.models.quiz import Quiz

NULL_MATIERE_ORDER = 10**9


def fiche_progression_order():
    """Trie par matiere puis progression du document, puis ordre interne."""
    return (
        func.coalesce(Fiche.matiere_id, NULL_MATIERE_ORDER).asc(),
        case((Document.id.is_(None), 1), else_=0).asc(),
        func.lower(func.trim(func.coalesce(Document.chapitre, Fiche.chapitre, ""))).asc(),
        func.lower(func.trim(func.coalesce(Document.titre, Fiche.titre, ""))).asc(),
        Fiche.ordre.asc(),
        Fiche.id.asc(),
    )


def flashcard_progression_order():
    """Trie par matiere puis document; l'ordre interne suit l'insertion."""
    return (
        func.coalesce(Flashcard.matiere_id, NULL_MATIERE_ORDER).asc(),
        case((Document.id.is_(None), 1), else_=0).asc(),
        func.lower(func.trim(func.coalesce(Document.chapitre, ""))).asc(),
        func.lower(func.trim(func.coalesce(Document.titre, ""))).asc(),
        Flashcard.created_at.asc(),
        Flashcard.id.asc(),
    )


def quiz_progression_order():
    """Trie par matiere puis document; l'ordre interne suit l'insertion."""
    return (
        func.coalesce(Quiz.matiere_id, NULL_MATIERE_ORDER).asc(),
        case((Document.id.is_(None), 1), else_=0).asc(),
        func.lower(func.trim(func.coalesce(Document.chapitre, ""))).asc(),
        func.lower(func.trim(func.coalesce(Document.titre, Quiz.titre, ""))).asc(),
        Quiz.created_at.asc(),
        Quiz.id.asc(),
    )
