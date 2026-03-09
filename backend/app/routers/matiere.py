"""
Router pour la gestion des matières (CRUD).
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.matiere import Matiere
from app.models.document import Document
from app.models.flashcard import Flashcard
from app.models.fiche import Fiche
from app.schemas.matiere import MatiereCreate, MatiereResponse

router = APIRouter()


@router.post("", response_model=MatiereResponse, status_code=201)
async def create_matiere(
    matiere_in: MatiereCreate,
    db: AsyncSession = Depends(get_db),
):
    """Crée une nouvelle matière."""
    existing = await db.execute(select(Matiere).where(Matiere.nom == matiere_in.nom))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Une matière avec ce nom existe déjà")

    matiere = Matiere(
        nom=matiere_in.nom,
        description=matiere_in.description,
        couleur=matiere_in.couleur,
    )
    db.add(matiere)
    await db.commit()
    await db.refresh(matiere)
    return matiere


@router.get("", response_model=list[MatiereResponse])
async def list_matieres(db: AsyncSession = Depends(get_db)):
    """Liste toutes les matières avec compteurs documents/flashcards/fiches."""
    result = await db.execute(select(Matiere).order_by(Matiere.nom))
    matieres = result.scalars().all()

    enriched = []
    for m in matieres:
        doc_count = (await db.execute(
            select(func.count()).select_from(Document).where(Document.matiere_id == m.id)
        )).scalar() or 0
        fc_count = (await db.execute(
            select(func.count()).select_from(Flashcard).where(Flashcard.matiere_id == m.id)
        )).scalar() or 0
        fiche_count = (await db.execute(
            select(func.count()).select_from(Fiche).where(Fiche.matiere_id == m.id)
        )).scalar() or 0
        enriched.append({
            "id": m.id,
            "nom": m.nom,
            "description": m.description,
            "couleur": m.couleur,
            "created_at": m.created_at,
            "nb_documents": doc_count,
            "nb_flashcards": fc_count,
            "nb_fiches": fiche_count,
        })

    return enriched


@router.get("/{matiere_id}", response_model=MatiereResponse)
async def get_matiere(matiere_id: int, db: AsyncSession = Depends(get_db)):
    """Récupère une matière par son ID."""
    result = await db.execute(select(Matiere).where(Matiere.id == matiere_id))
    matiere = result.scalar_one_or_none()
    if matiere is None:
        raise HTTPException(status_code=404, detail="Matière non trouvée")
    return matiere


@router.put("/{matiere_id}", response_model=MatiereResponse)
async def update_matiere(
    matiere_id: int,
    matiere_in: MatiereCreate,
    db: AsyncSession = Depends(get_db),
):
    """Met à jour une matière."""
    result = await db.execute(select(Matiere).where(Matiere.id == matiere_id))
    matiere = result.scalar_one_or_none()
    if matiere is None:
        raise HTTPException(status_code=404, detail="Matière non trouvée")

    matiere.nom = matiere_in.nom
    matiere.description = matiere_in.description
    matiere.couleur = matiere_in.couleur

    await db.commit()
    await db.refresh(matiere)
    return matiere


@router.delete("/{matiere_id}")
async def delete_matiere(matiere_id: int, db: AsyncSession = Depends(get_db)):
    """Supprime une matière."""
    result = await db.execute(select(Matiere).where(Matiere.id == matiere_id))
    matiere = result.scalar_one_or_none()
    if matiere is None:
        raise HTTPException(status_code=404, detail="Matière non trouvée")

    await db.delete(matiere)
    await db.commit()
    return {"message": "Matière supprimée", "id": matiere_id}
