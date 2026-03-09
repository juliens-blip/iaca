from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


class Flashcard(Base):
    __tablename__ = "flashcards"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    reponse = Column(Text, nullable=False)
    explication = Column(Text, default="")
    difficulte = Column(Integer, default=1)  # 1-5
    matiere_id = Column(Integer, ForeignKey("matieres.id"), nullable=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True, index=True)
    # Spaced repetition fields
    intervalle_jours = Column(Float, default=1.0)
    facteur_facilite = Column(Float, default=2.5)
    repetitions = Column(Integer, default=0)
    prochaine_revision = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    matiere = relationship("Matiere", back_populates="flashcards")
