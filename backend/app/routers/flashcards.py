"""
Router pour la gestion des flashcards avec revision espacee (algorithme SM-2).
"""

import math
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.flashcard import Flashcard
from app.schemas.flashcard import FlashcardCreate, FlashcardResponse, FlashcardReview

router = APIRouter()


@router.post("", response_model=FlashcardResponse)
async def create_flashcard(
    flashcard_in: FlashcardCreate,
    db: AsyncSession = Depends(get_db),
):
    """Cree une nouvelle flashcard."""
    flashcard = Flashcard(
        question=flashcard_in.question,
        reponse=flashcard_in.reponse,
        explication=flashcard_in.explication,
        difficulte=flashcard_in.difficulte,
        matiere_id=flashcard_in.matiere_id,
        document_id=flashcard_in.document_id,
    )

    db.add(flashcard)
    await db.commit()
    await db.refresh(flashcard)

    return flashcard


@router.get("", response_model=list[FlashcardResponse])
async def list_flashcards(
    matiere_id: Optional[int] = None,
    document_id: Optional[int] = None,
    limit: int = 200,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """Liste les flashcards avec filtres optionnels par matiere et/ou document.
    Sans filtre de matiere, applique un interleaving equilivre multi-matieres.
    """
    if matiere_id is not None or document_id is not None:
        query = select(Flashcard).order_by(Flashcard.created_at.desc())
        if matiere_id is not None:
            query = query.where(Flashcard.matiere_id == matiere_id)
        if document_id is not None:
            query = query.where(Flashcard.document_id == document_id)
        if offset > 0:
            query = query.offset(offset)
        if limit > 0:
            query = query.limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    # Mode equilivre : interleaving par matiere
    matieres_result = await db.execute(
        select(Flashcard.matiere_id).distinct()
    )
    matiere_ids = [row[0] for row in matieres_result.all()]

    if not matiere_ids:
        return []

    effective_limit = limit if limit > 0 else 200
    per_matiere = max(1, math.ceil(effective_limit / len(matiere_ids)))

    buckets: list[list[Flashcard]] = []
    for mid in matiere_ids:
        q = (
            select(Flashcard)
            .where(Flashcard.matiere_id == mid)
            .order_by(func.random())
            .limit(per_matiere)
        )
        res = await db.execute(q)
        buckets.append(list(res.scalars().all()))

    interleaved: list[Flashcard] = []
    max_len = max(len(b) for b in buckets)
    for i in range(max_len):
        for bucket in buckets:
            if i < len(bucket):
                interleaved.append(bucket[i])

    start = offset if offset > 0 else 0
    return interleaved[start: start + effective_limit]


@router.get("/revision", response_model=list[FlashcardResponse])
async def get_revision_flashcards(
    matiere_id: Optional[int] = None,
    limit: int = 200,
    db: AsyncSession = Depends(get_db),
):
    """
    Recupere les flashcards dont la prochaine revision est passee ou aujourd'hui.
    Triees par date de revision la plus ancienne en premier (les plus urgentes).
    """
    now = datetime.now(timezone.utc)
    query = (
        select(Flashcard)
        .where(Flashcard.prochaine_revision <= now)
        .order_by(Flashcard.prochaine_revision.asc())
        .limit(limit)
    )

    if matiere_id is not None:
        query = query.where(Flashcard.matiere_id == matiere_id)

    result = await db.execute(query)
    flashcards = result.scalars().all()
    return flashcards


@router.post("/{flashcard_id}/review", response_model=FlashcardResponse)
async def review_flashcard(
    flashcard_id: int,
    review: FlashcardReview,
    db: AsyncSession = Depends(get_db),
):
    """
    Met a jour une flashcard apres revision en utilisant l'algorithme SM-2.

    Le champ `qualite` (0-5) represente la qualite de la reponse:
        - 0: Aucun souvenir
        - 1: Mauvaise reponse, mais reconnait la bonne
        - 2: Mauvaise reponse, mais la bonne semble facile a retenir
        - 3: Bonne reponse avec difficulte importante
        - 4: Bonne reponse apres hesitation
        - 5: Reponse parfaite
    """
    if not 0 <= review.qualite <= 5:
        raise HTTPException(
            status_code=400, detail="La qualite doit etre entre 0 et 5"
        )

    result = await db.execute(
        select(Flashcard).where(Flashcard.id == flashcard_id)
    )
    flashcard = result.scalar_one_or_none()

    if flashcard is None:
        raise HTTPException(status_code=404, detail="Flashcard non trouvee")

    # --- Algorithme SM-2 ---
    q = review.qualite
    ef = flashcard.facteur_facilite
    reps = flashcard.repetitions
    interval = flashcard.intervalle_jours

    # Nouveau facteur de facilite (EF)
    # EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    new_ef = ef + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    # EF ne doit jamais descendre en dessous de 1.3
    new_ef = max(1.3, new_ef)

    if q < 3:
        # Reponse incorrecte : on recommence les repetitions
        new_reps = 0
        new_interval = 1.0
    else:
        # Reponse correcte
        if reps == 0:
            new_interval = 1.0
        elif reps == 1:
            new_interval = 6.0
        else:
            new_interval = interval * new_ef

        new_reps = reps + 1

    # Calculer la prochaine date de revision
    prochaine_revision = datetime.now(timezone.utc) + timedelta(days=new_interval)

    # Mettre a jour la flashcard
    flashcard.facteur_facilite = round(new_ef, 2)
    flashcard.repetitions = new_reps
    flashcard.intervalle_jours = round(new_interval, 1)
    flashcard.prochaine_revision = prochaine_revision

    await db.commit()
    await db.refresh(flashcard)

    return flashcard


@router.get("/{flashcard_id}", response_model=FlashcardResponse)
async def get_flashcard(
    flashcard_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Recupere une flashcard par son ID."""
    result = await db.execute(
        select(Flashcard).where(Flashcard.id == flashcard_id)
    )
    flashcard = result.scalar_one_or_none()

    if flashcard is None:
        raise HTTPException(status_code=404, detail="Flashcard non trouvee")

    return flashcard


@router.delete("/{flashcard_id}")
async def delete_flashcard(
    flashcard_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Supprime une flashcard."""
    result = await db.execute(
        select(Flashcard).where(Flashcard.id == flashcard_id)
    )
    flashcard = result.scalar_one_or_none()

    if flashcard is None:
        raise HTTPException(status_code=404, detail="Flashcard non trouvee")

    await db.delete(flashcard)
    await db.commit()

    return {"message": "Flashcard supprimee", "id": flashcard_id}
