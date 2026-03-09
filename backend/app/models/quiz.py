from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    titre = Column(String, nullable=False)
    matiere_id = Column(Integer, ForeignKey("matieres.id"), nullable=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    matiere = relationship("Matiere", back_populates="quizzes")
    questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    question = Column(Text, nullable=False)
    choix = Column(JSON, nullable=False)  # ["A", "B", "C", "D"]
    reponse_correcte = Column(Integer, nullable=False)  # index in choix
    explication = Column(Text, default="")
    difficulte = Column(Integer, default=1)

    quiz = relationship("Quiz", back_populates="questions")
