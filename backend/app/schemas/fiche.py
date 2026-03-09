from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class FicheSectionBase(BaseModel):
    titre: str
    contenu: str
    ordre: int = 0


class FicheSectionCreate(FicheSectionBase):
    pass


class FicheSectionResponse(FicheSectionBase):
    id: int
    fiche_id: int

    class Config:
        from_attributes = True


class FicheBase(BaseModel):
    titre: str
    resume: str = ""
    matiere_id: Optional[int] = None
    document_id: Optional[int] = None
    chapitre: str = ""
    tags: str = ""
    ordre: int = 0


class FicheCreate(FicheBase):
    sections: list[FicheSectionCreate] = []


class FicheResponse(FicheBase):
    id: int
    created_at: datetime
    sections: list[FicheSectionResponse] = []

    class Config:
        from_attributes = True


class FicheListItem(FicheBase):
    id: int
    created_at: datetime
    nb_sections: int = 0

    class Config:
        from_attributes = True
