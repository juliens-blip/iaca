from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class FlashcardBase(BaseModel):
    question: str
    reponse: str
    explication: str = ""
    difficulte: int = Field(default=1, ge=1, le=5)
    matiere_id: Optional[int] = None
    document_id: Optional[int] = None


class FlashcardCreate(FlashcardBase):
    pass


class FlashcardResponse(FlashcardBase):
    id: int
    intervalle_jours: float = 1.0
    facteur_facilite: float = 2.5
    repetitions: int = 0
    prochaine_revision: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class FlashcardReview(BaseModel):
    qualite: int = Field(ge=0, le=5)  # SM-2 algorithm
