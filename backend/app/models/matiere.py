from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


class Matiere(Base):
    __tablename__ = "matieres"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, nullable=False, unique=True)
    description = Column(String, default="")
    couleur = Column(String, default="#2563eb")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    documents = relationship("Document", back_populates="matiere")
    flashcards = relationship("Flashcard", back_populates="matiere")
    quizzes = relationship("Quiz", back_populates="matiere")
    fiches = relationship("Fiche", back_populates="matiere")
