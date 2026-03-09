"""
Router pour la gestion des documents (upload, liste, detail, suppression).
"""

import os
import shutil
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import select
from sqlalchemy.orm import defer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.models.document import Document
from app.schemas.document import DocumentResponse, DocumentListItem
from app.config import settings
from app.services.document_parser import parse_document

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".pptx", ".docx"}


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    titre: Optional[str] = Form(None),
    matiere_id: Optional[int] = Form(None),
    chapitre: str = Form(""),
    tags: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    """Upload un fichier PDF, PPTX ou DOCX, extrait le texte et sauvegarde."""
    # Verifier l'extension
    filename = file.filename or "document"
    extension = os.path.splitext(filename)[1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Type de fichier non supporte: {extension}. "
            f"Formats acceptes: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Creer le dossier d'upload si necessaire
    upload_dir = settings.upload_path
    os.makedirs(upload_dir, exist_ok=True)

    # Generer un nom de fichier unique
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{filename}"
    file_path = os.path.join(upload_dir, safe_filename)

    # Sauvegarder le fichier
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la sauvegarde: {str(e)}")
    finally:
        await file.close()

    # Extraire le texte
    try:
        contenu_extrait = (await parse_document(file_path)).strip()
    except Exception:
        # En cas d'erreur d'extraction, on garde le document mais sans contenu
        # pour eviter d'injecter un message d'erreur dans les generations IA.
        contenu_extrait = ""

    # Creer l'enregistrement en base
    document = Document(
        titre=titre or os.path.splitext(filename)[0],
        fichier_path=file_path,
        type_fichier=extension.lstrip("."),
        contenu_extrait=contenu_extrait,
        matiere_id=matiere_id,
        chapitre=chapitre,
        tags=tags,
    )

    db.add(document)
    await db.commit()
    await db.refresh(document)

    return document


@router.get("/count")
async def count_documents(
    matiere_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """Retourne le nombre total de documents."""
    from sqlalchemy import func
    query = select(func.count()).select_from(Document)
    if matiere_id is not None:
        query = query.where(Document.matiere_id == matiere_id)
    result = await db.execute(query)
    return {"count": result.scalar() or 0}


@router.get("", response_model=list[DocumentListItem])
async def list_documents(
    matiere_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """Liste les documents (sans contenu_extrait), avec pagination et filtre optionnel."""
    query = select(Document).options(defer(Document.contenu_extrait)).order_by(Document.created_at.desc()).limit(limit).offset(offset)
    if matiere_id is not None:
        query = query.where(Document.matiere_id == matiere_id)

    result = await db.execute(query)
    documents = result.scalars().all()
    return documents


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Recupere un document par son ID."""
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()

    if document is None:
        raise HTTPException(status_code=404, detail="Document non trouve")

    return document


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Supprime un document et son fichier associe."""
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()

    if document is None:
        raise HTTPException(status_code=404, detail="Document non trouve")

    # Supprimer le fichier physique
    if os.path.exists(document.fichier_path):
        try:
            os.remove(document.fichier_path)
        except OSError:
            pass  # Le fichier n'existe plus, on continue

    await db.delete(document)
    await db.commit()

    return {"message": "Document supprime", "id": document_id}
