from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    titre = Column(String, nullable=False)
    fichier_path = Column(String, nullable=False)
    type_fichier = Column(String)  # pdf, pptx, docx
    contenu_extrait = Column(Text, default="")
    matiere_id = Column(Integer, ForeignKey("matieres.id"), nullable=True)
    chapitre = Column(String, default="")
    tags = Column(String, default="")  # comma-separated
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    matiere = relationship("Matiere", back_populates="documents")
