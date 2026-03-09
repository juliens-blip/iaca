from pydantic import BaseModel
from datetime import datetime


class MatiereBase(BaseModel):
    nom: str
    description: str = ""
    couleur: str = "#2563eb"


class MatiereCreate(MatiereBase):
    pass


class MatiereResponse(MatiereBase):
    id: int
    created_at: datetime
    nb_documents: int = 0
    nb_flashcards: int = 0
    nb_fiches: int = 0

    class Config:
        from_attributes = True
