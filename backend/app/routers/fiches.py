"""
Router pour la gestion des fiches de revision structurees.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.document import Document
from app.models.fiche import Fiche, FicheSection
from app.models.flashcard import Flashcard
from app.models.quiz import Quiz
from app.query_ordering import fiche_progression_order
from app.schemas.fiche import FicheCreate, FicheResponse, FicheListItem

router = APIRouter()
EXTRACTION_ERROR_MARKER = "[Erreur d'extraction:"


def _contains_extraction_error(text: str | None) -> bool:
    return EXTRACTION_ERROR_MARKER in (text or "")


def _serialize_clean_fiche(fiche: Fiche) -> FicheResponse:
    clean_resume = "" if _contains_extraction_error(fiche.resume) else fiche.resume
    clean_sections = [
        section for section in fiche.sections if not _contains_extraction_error(section.contenu)
    ]
    return FicheResponse(
        id=fiche.id,
        titre=fiche.titre,
        resume=clean_resume,
        matiere_id=fiche.matiere_id,
        document_id=fiche.document_id,
        chapitre=fiche.chapitre,
        tags=fiche.tags,
        ordre=fiche.ordre,
        created_at=fiche.created_at,
        sections=clean_sections,
    )


@router.post("", response_model=FicheResponse)
async def create_fiche(
    fiche_in: FicheCreate,
    db: AsyncSession = Depends(get_db),
):
    """Cree une nouvelle fiche de revision avec ses sections."""
    fiche = Fiche(
        titre=fiche_in.titre,
        resume=fiche_in.resume,
        matiere_id=fiche_in.matiere_id,
        document_id=fiche_in.document_id,
        chapitre=fiche_in.chapitre,
        tags=fiche_in.tags,
        ordre=fiche_in.ordre,
    )
    db.add(fiche)
    await db.flush()

    for i, section_in in enumerate(fiche_in.sections):
        section = FicheSection(
            fiche_id=fiche.id,
            titre=section_in.titre,
            contenu=section_in.contenu,
            ordre=section_in.ordre if section_in.ordre else i,
        )
        db.add(section)

    await db.commit()

    # Reload with sections
    result = await db.execute(
        select(Fiche).options(selectinload(Fiche.sections)).where(Fiche.id == fiche.id)
    )
    return result.scalar_one()


@router.get("", response_model=list[FicheListItem])
async def list_fiches(
    matiere_id: Optional[int] = None,
    document_id: Optional[int] = None,
    limit: int = 200,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """Liste les fiches avec filtres optionnels.
    Les resultats suivent un ordre pedagogique stable base sur le document source.
    """
    error_filter = ~func.coalesce(Fiche.resume, "").like("%[Erreur d'extraction:%")
    query = (
        select(Fiche)
        .outerjoin(Document, Fiche.document_id == Document.id)
        .where(error_filter)
        .order_by(*fiche_progression_order())
    )
    if matiere_id is not None:
        query = query.where(Fiche.matiere_id == matiere_id)
    if document_id is not None:
        query = query.where(Fiche.document_id == document_id)
    if offset > 0:
        query = query.offset(offset)
    if limit > 0:
        query = query.limit(limit)
    result = await db.execute(query)
    fiches = result.scalars().all()

    # Count sections in one query (avoid N+1).
    section_counts: dict[int, int] = {}
    fiche_ids = [f.id for f in fiches]
    if fiche_ids:
        counts_result = await db.execute(
            select(FicheSection.fiche_id, func.count(FicheSection.id))
            .where(FicheSection.fiche_id.in_(fiche_ids))
            .group_by(FicheSection.fiche_id)
        )
        section_counts = {fiche_id: count for fiche_id, count in counts_result.all()}

    items = []
    for f in fiches:
        nb_sections = section_counts.get(f.id, 0)
        items.append(FicheListItem(
            id=f.id,
            titre=f.titre,
            resume=f.resume,
            matiere_id=f.matiere_id,
            document_id=f.document_id,
            chapitre=f.chapitre,
            tags=f.tags,
            ordre=f.ordre,
            created_at=f.created_at,
            nb_sections=nb_sections,
        ))

    return items


@router.get("/{fiche_id}", response_model=FicheResponse)
async def get_fiche(
    fiche_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Recupere une fiche avec ses sections."""
    result = await db.execute(
        select(Fiche).options(selectinload(Fiche.sections)).where(Fiche.id == fiche_id)
    )
    fiche = result.scalar_one_or_none()

    if fiche is None:
        raise HTTPException(status_code=404, detail="Fiche non trouvee")

    return _serialize_clean_fiche(fiche)


@router.put("/{fiche_id}", response_model=FicheResponse)
async def update_fiche(
    fiche_id: int,
    fiche_in: FicheCreate,
    db: AsyncSession = Depends(get_db),
):
    """Met a jour une fiche et remplace ses sections."""
    result = await db.execute(
        select(Fiche).options(selectinload(Fiche.sections)).where(Fiche.id == fiche_id)
    )
    fiche = result.scalar_one_or_none()

    if fiche is None:
        raise HTTPException(status_code=404, detail="Fiche non trouvee")

    fiche.titre = fiche_in.titre
    fiche.resume = fiche_in.resume
    fiche.matiere_id = fiche_in.matiere_id
    fiche.document_id = fiche_in.document_id
    fiche.chapitre = fiche_in.chapitre
    fiche.tags = fiche_in.tags
    fiche.ordre = fiche_in.ordre

    # Delete old sections
    for section in fiche.sections:
        await db.delete(section)

    # Create new sections
    for i, section_in in enumerate(fiche_in.sections):
        section = FicheSection(
            fiche_id=fiche.id,
            titre=section_in.titre,
            contenu=section_in.contenu,
            ordre=section_in.ordre if section_in.ordre else i,
        )
        db.add(section)

    await db.commit()

    # Reload
    result = await db.execute(
        select(Fiche).options(selectinload(Fiche.sections)).where(Fiche.id == fiche.id)
    )
    return _serialize_clean_fiche(result.scalar_one())


@router.delete("/{fiche_id}")
async def delete_fiche(
    fiche_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Supprime une fiche et ses sections."""
    result = await db.execute(
        select(Fiche).where(Fiche.id == fiche_id)
    )
    fiche = result.scalar_one_or_none()

    if fiche is None:
        raise HTTPException(status_code=404, detail="Fiche non trouvee")

    await db.delete(fiche)
    await db.commit()

    return {"message": "Fiche supprimee", "id": fiche_id}


@router.get("/{fiche_id}/next")
async def get_fiche_next(
    fiche_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Retourne les flashcards et quiz lies au meme document que la fiche."""
    result = await db.execute(
        select(Fiche).where(Fiche.id == fiche_id)
    )
    fiche = result.scalar_one_or_none()

    if fiche is None:
        raise HTTPException(status_code=404, detail="Fiche non trouvee")

    flashcards = []
    quizzes = []

    if fiche.document_id:
        fc_result = await db.execute(
            select(Flashcard).where(
                Flashcard.document_id == fiche.document_id,
                ~func.coalesce(Flashcard.question, "").like("%[Erreur d'extraction:%"),
                ~func.coalesce(Flashcard.reponse, "").like("%[Erreur d'extraction:%"),
            )
        )
        flashcards = [{"id": f.id, "question": f.question} for f in fc_result.scalars().all()]

        qz_result = await db.execute(
            select(Quiz).where(Quiz.document_id == fiche.document_id)
        )
        quizzes = [{"id": q.id, "titre": q.titre} for q in qz_result.scalars().all()]

    if fiche.matiere_id and not flashcards:
        fc_result = await db.execute(
            select(Flashcard).where(
                Flashcard.matiere_id == fiche.matiere_id,
                ~func.coalesce(Flashcard.question, "").like("%[Erreur d'extraction:%"),
                ~func.coalesce(Flashcard.reponse, "").like("%[Erreur d'extraction:%"),
            ).limit(10)
        )
        flashcards = [{"id": f.id, "question": f.question} for f in fc_result.scalars().all()]

    if fiche.matiere_id and not quizzes:
        qz_result = await db.execute(
            select(Quiz).where(Quiz.matiere_id == fiche.matiere_id).limit(5)
        )
        quizzes = [{"id": q.id, "titre": q.titre} for q in qz_result.scalars().all()]

    return {
        "fiche_id": fiche_id,
        "flashcards": flashcards,
        "quizzes": quizzes,
    }
