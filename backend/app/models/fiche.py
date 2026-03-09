from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


class Fiche(Base):
    __tablename__ = "fiches"

    id = Column(Integer, primary_key=True, index=True)
    titre = Column(String, nullable=False)
    resume = Column(Text, default="")
    matiere_id = Column(Integer, ForeignKey("matieres.id"), nullable=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    chapitre = Column(String, default="")
    tags = Column(String, default="")
    ordre = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    matiere = relationship("Matiere", back_populates="fiches")
    sections = relationship("FicheSection", back_populates="fiche", cascade="all, delete-orphan", order_by="FicheSection.ordre")


class FicheSection(Base):
    __tablename__ = "fiche_sections"

    id = Column(Integer, primary_key=True, index=True)
    fiche_id = Column(Integer, ForeignKey("fiches.id", ondelete="CASCADE"), nullable=False)
    titre = Column(String, nullable=False)
    contenu = Column(Text, nullable=False)
    ordre = Column(Integer, default=0)

    fiche = relationship("Fiche", back_populates="sections")
