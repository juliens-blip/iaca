"""
Router pour la gestion des quiz et la soumission de reponses.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.document import Document
from app.models.quiz import Quiz, QuizQuestion
from app.query_ordering import quiz_progression_order
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
    Les resultats suivent un ordre pedagogique stable base sur le document source.
    """
    query = (
        select(Quiz)
        .options(selectinload(Quiz.questions))
        .outerjoin(Document, Quiz.document_id == Document.id)
        .order_by(*quiz_progression_order())
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
