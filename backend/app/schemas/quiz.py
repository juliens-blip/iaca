from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class QuizQuestionBase(BaseModel):
    question: str
    choix: list[str]
    reponse_correcte: int
    explication: str = ""
    difficulte: int = Field(default=1, ge=1, le=5)


class QuizQuestionCreate(QuizQuestionBase):
    pass


class QuizQuestionResponse(QuizQuestionBase):
    id: int
    quiz_id: int

    class Config:
        from_attributes = True


class QuizBase(BaseModel):
    titre: str
    matiere_id: Optional[int] = None
    document_id: Optional[int] = None


class QuizCreate(QuizBase):
    questions: list[QuizQuestionCreate]


class QuizResponse(QuizBase):
    id: int
    created_at: datetime
    questions: list[QuizQuestionResponse] = []

    class Config:
        from_attributes = True


class QuizAnswer(BaseModel):
    question_id: int
    reponse: int


class QuizSubmission(BaseModel):
    reponses: list[QuizAnswer]


class QuizResult(BaseModel):
    score: int
    total: int
    details: list[dict]
