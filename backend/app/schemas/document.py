from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DocumentBase(BaseModel):
    titre: str
    type_fichier: Optional[str] = None
    matiere_id: Optional[int] = None
    chapitre: str = ""
    tags: str = ""


class DocumentCreate(DocumentBase):
    fichier_path: str


class DocumentResponse(DocumentBase):
    id: int
    fichier_path: str
    contenu_extrait: str = ""
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentListItem(DocumentBase):
    """Schema léger pour la liste (sans contenu_extrait)."""
    id: int
    fichier_path: str
    created_at: datetime

    class Config:
        from_attributes = True
