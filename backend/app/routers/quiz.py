"""
Router pour la gestion des quiz et la soumission de reponses.
"""

import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.quiz import Quiz, QuizQuestion
from app.schemas.quiz import (
    QuizCreate,
    QuizResponse,
    QuizSubmission,
    QuizResult,
)

router = APIRouter()


@router.post("", response_model=QuizResponse)
async def create_quiz(
    quiz_in: QuizCreate,
    db: AsyncSession = Depends(get_db),
):
    """Cree un nouveau quiz avec ses questions."""
    quiz = Quiz(
        titre=quiz_in.titre,
        matiere_id=quiz_in.matiere_id,
        document_id=quiz_in.document_id,
    )

    # Creer les questions associees
    for q_data in quiz_in.questions:
        question = QuizQuestion(
            question=q_data.question,
            choix=q_data.choix,
            reponse_correcte=q_data.reponse_correcte,
            explication=q_data.explication,
            difficulte=q_data.difficulte,
        )
        quiz.questions.append(question)

    db.add(quiz)
    await db.commit()
    await db.refresh(quiz)

    # Recharger avec les questions (eager loading)
    result = await db.execute(
        select(Quiz)
        .options(selectinload(Quiz.questions))
        .where(Quiz.id == quiz.id)
    )
    quiz = result.scalar_one()

    return quiz


@router.get("", response_model=list[QuizResponse])
async def list_quizzes(
    matiere_id: Optional[int] = None,
    document_id: Optional[int] = None,
    limit: int = 200,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """Liste tous les quiz avec filtres optionnels.
    Quand aucune matiere_id n'est specifiee, applique un interleaving
    equilbre multi-matieres pour eviter le biais vers une seule matiere.
    """
    if matiere_id is not None or document_id is not None:
        # Filtre explicite : comportement normal
        query = (
            select(Quiz)
            .options(selectinload(Quiz.questions))
            .order_by(Quiz.created_at.desc())
        )
        if matiere_id is not None:
            query = query.where(Quiz.matiere_id == matiere_id)
        if document_id is not None:
            query = query.where(Quiz.document_id == document_id)
        if offset > 0:
            query = query.offset(offset)
        if limit > 0:
            query = query.limit(limit)
        result = await db.execute(query)
        return result.scalars().unique().all()

    # Mode equilbre : interleaving par matiere
    # Recuperer les matieres distinctes presentes
    matieres_result = await db.execute(
        select(Quiz.matiere_id).distinct()
    )
    matiere_ids = [row[0] for row in matieres_result.all()]

    if not matiere_ids:
        return []

    effective_limit = limit if limit > 0 else 200
    per_matiere = max(1, math.ceil(effective_limit / len(matiere_ids)))

    buckets: list[list[Quiz]] = []
    for mid in matiere_ids:
        q = (
            select(Quiz)
            .options(selectinload(Quiz.questions))
            .where(Quiz.matiere_id == mid)
            .order_by(func.random())
            .limit(per_matiere)
        )
        res = await db.execute(q)
        buckets.append(list(res.scalars().unique().all()))

    # Interleave : round-robin sur les buckets
    interleaved: list[Quiz] = []
    max_len = max(len(b) for b in buckets)
    for i in range(max_len):
        for bucket in buckets:
            if i < len(bucket):
                interleaved.append(bucket[i])

    # Appliquer offset + limit finaux
    start = offset if offset > 0 else 0
    return interleaved[start: start + effective_limit]


@router.get("/{quiz_id}", response_model=QuizResponse)
async def get_quiz(
    quiz_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Recupere un quiz par son ID avec ses questions."""
    result = await db.execute(
        select(Quiz)
        .options(selectinload(Quiz.questions))
        .where(Quiz.id == quiz_id)
    )
    quiz = result.scalar_one_or_none()

    if quiz is None:
        raise HTTPException(status_code=404, detail="Quiz non trouve")

    return quiz


@router.post("/{quiz_id}/submit", response_model=QuizResult)
async def submit_quiz(
    quiz_id: int,
    submission: QuizSubmission,
    db: AsyncSession = Depends(get_db),
):
    """
    Soumet les reponses a un quiz et calcule le score.

    Chaque reponse contient le question_id et l'index de la reponse choisie.
    Retourne le score, le total et les details par question.
    """
    # Charger le quiz avec ses questions
    result = await db.execute(
        select(Quiz)
        .options(selectinload(Quiz.questions))
        .where(Quiz.id == quiz_id)
    )
    quiz = result.scalar_one_or_none()

    if quiz is None:
        raise HTTPException(status_code=404, detail="Quiz non trouve")

    # Indexer les questions par ID pour un acces rapide
    questions_map = {q.id: q for q in quiz.questions}

    score = 0
    total = len(quiz.questions)
    details: list[dict] = []

    for answer in submission.reponses:
        question = questions_map.get(answer.question_id)
        if question is None:
            raise HTTPException(
                status_code=400,
                detail=f"Question {answer.question_id} n'appartient pas a ce quiz",
            )

        is_correct = answer.reponse == question.reponse_correcte
        if is_correct:
            score += 1

        details.append(
            {
                "question_id": question.id,
                "question": question.question,
                "reponse_donnee": answer.reponse,
                "reponse_correcte": question.reponse_correcte,
                "correct": is_correct,
                "explication": question.explication,
            }
        )

    return QuizResult(score=score, total=total, details=details)


@router.delete("/{quiz_id}")
async def delete_quiz(
    quiz_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Supprime un quiz et toutes ses questions (cascade)."""
    result = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = result.scalar_one_or_none()

    if quiz is None:
        raise HTTPException(status_code=404, detail="Quiz non trouve")

    await db.delete(quiz)
    await db.commit()

    return {"message": "Quiz supprime", "id": quiz_id}
