from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.document import Document
from app.models.flashcard import Flashcard
from app.models.matiere import Matiere
from app.models.quiz import Quiz, QuizQuestion
from app.models.fiche import Fiche, FicheSection
from app.services import claude_service, gemini_service, document_parser

router = APIRouter()
EXTRACTION_ERROR_PREFIX = "[Erreur d'extraction:"
MIN_EXTRACTED_CONTENT_CHARS = 120


def _contains_extraction_error_marker(content: str | None) -> bool:
    return EXTRACTION_ERROR_PREFIX in (content or "")


async def _resolve_document_content(doc: Document, db: AsyncSession) -> str:
    cached_content = (doc.contenu_extrait or "").strip()
    if cached_content and not _contains_extraction_error_marker(cached_content):
        if len(cached_content) >= MIN_EXTRACTED_CONTENT_CHARS:
            return cached_content

    try:
        extracted_content = (await document_parser.parse_document(doc.fichier_path)).strip()
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Extraction impossible pour ce document: {exc}",
        ) from exc

    if (
        not extracted_content
        or _contains_extraction_error_marker(extracted_content)
        or len(extracted_content) < MIN_EXTRACTED_CONTENT_CHARS
    ):
        raise HTTPException(
            status_code=422,
            detail="Le document ne contient pas assez de contenu exploitable pour la generation.",
        )

    doc.contenu_extrait = extracted_content
    await db.commit()
    return extracted_content


@router.post("/generer-flashcards/{document_id}")
async def pipeline_flashcards(
    document_id: int,
    nb: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """O10: Pipeline complet - Document → extraction → Claude → flashcards en DB."""
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Document non trouvé")

    contenu = await _resolve_document_content(doc, db)

    # Get matiere name
    matiere_nom = "droit public"
    if doc.matiere_id:
        mat_result = await db.execute(select(Matiere).where(Matiere.id == doc.matiere_id))
        mat = mat_result.scalar_one_or_none()
        if mat:
            matiere_nom = mat.nom

    # Generate flashcards via Claude
    try:
        flashcards_data = await claude_service.generer_flashcards(contenu, matiere_nom, nb)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # Save to DB
    created = []
    for fc in flashcards_data:
        flashcard = Flashcard(
            question=fc["question"],
            reponse=fc["reponse"],
            explication=fc.get("explication", ""),
            difficulte=fc.get("difficulte", 1),
            matiere_id=doc.matiere_id,
            document_id=doc.id,
        )
        db.add(flashcard)
        created.append(fc)

    await db.commit()
    return {"generated": len(created), "flashcards": created}


@router.post("/generer-qcm/{document_id}")
async def pipeline_qcm(
    document_id: int,
    nb: int = 5,
    db: AsyncSession = Depends(get_db),
):
    """Pipeline: Document → Claude → QCM en DB."""
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Document non trouvé")

    contenu = await _resolve_document_content(doc, db)

    matiere_nom = "droit public"
    if doc.matiere_id:
        mat_result = await db.execute(select(Matiere).where(Matiere.id == doc.matiere_id))
        mat = mat_result.scalar_one_or_none()
        if mat:
            matiere_nom = mat.nom

    try:
        qcm_data = await claude_service.generer_qcm(contenu, matiere_nom, nb)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    quiz = Quiz(
        titre=f"QCM - {doc.titre}",
        matiere_id=doc.matiere_id,
        document_id=doc.id,
    )
    db.add(quiz)
    await db.flush()

    for q in qcm_data:
        question = QuizQuestion(
            quiz_id=quiz.id,
            question=q["question"],
            choix=q["choix"],
            reponse_correcte=q["reponse_correcte"],
            explication=q.get("explication", ""),
            difficulte=q.get("difficulte", 1),
        )
        db.add(question)

    await db.commit()
    return {"quiz_id": quiz.id, "questions_generated": len(qcm_data)}


@router.post("/generer-fiche/{document_id}")
async def pipeline_fiche(
    document_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Pipeline: Document -> Claude -> Fiche de revision structuree en DB."""
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Document non trouve")

    contenu = await _resolve_document_content(doc, db)

    matiere_nom = "droit public"
    if doc.matiere_id:
        mat_result = await db.execute(select(Matiere).where(Matiere.id == doc.matiere_id))
        mat = mat_result.scalar_one_or_none()
        if mat:
            matiere_nom = mat.nom

    try:
        fiche_data = await claude_service.generer_fiche(contenu, matiere_nom, doc.titre)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    fiche = Fiche(
        titre=fiche_data.get("titre", f"Fiche - {doc.titre}"),
        resume=fiche_data.get("resume", ""),
        matiere_id=doc.matiere_id,
        document_id=doc.id,
        tags=matiere_nom,
    )
    db.add(fiche)
    await db.flush()

    sections = fiche_data.get("sections", [])
    inserted_sections = 0
    for i, s in enumerate(sections):
        sec_titre = s.get("titre", f"Section {i+1}")
        sec_contenu = s.get("contenu", "")
        if len(str(sec_contenu).strip()) < 40:
            continue
        section = FicheSection(
            fiche_id=fiche.id,
            titre=sec_titre,
            contenu=sec_contenu,
            ordre=inserted_sections,
        )
        db.add(section)
        inserted_sections += 1

    await db.commit()
    return {
        "fiche_id": fiche.id,
        "titre": fiche.titre,
        "sections_generated": inserted_sections,
    }


@router.get("/ressources/{matiere_id}")
async def pipeline_recommandations(
    matiere_id: int,
    sujet: str = "",
    db: AsyncSession = Depends(get_db),
):
    """O11: Pipeline recommandations externes via Gemini."""
    result = await db.execute(select(Matiere).where(Matiere.id == matiere_id))
    matiere = result.scalar_one_or_none()
    if not matiere:
        raise HTTPException(404, "Matière non trouvée")

    query = sujet if sujet else matiere.nom
    ressources = await gemini_service.rechercher_ressources(query, matiere.nom)
    return ressources


@router.get("/mindmap/{document_id}")
async def generer_mind_map(
    document_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Generate a mind map from document content via Gemini."""
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Document non trouvé")

    contenu = await _resolve_document_content(doc, db)

    try:
        mindmap = await gemini_service.generer_mind_map(contenu, doc.titre)
        return mindmap
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Generation mind map indisponible: {exc}",
        ) from exc
