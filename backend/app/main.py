import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
from app.middleware.rate_limit import RateLimitMiddleware
from app.routers import documents, flashcards, quiz, vocal, recommandations, matiere, fiches
from app.security import BearerAuthMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create directories and DB tables
    os.makedirs(settings.upload_path, exist_ok=True)
    os.makedirs(os.path.dirname(settings.database_url.replace("sqlite:///", "")), exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown: dispose engine
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    description="IA pour la revision de concours administratifs",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(BearerAuthMiddleware)
app.add_middleware(
    RateLimitMiddleware,
    enabled=settings.rate_limit_enabled,
    requests=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window_seconds,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(matiere.router, prefix="/api/matieres", tags=["matieres"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(flashcards.router, prefix="/api/flashcards", tags=["flashcards"])
app.include_router(quiz.router, prefix="/api/quiz", tags=["quiz"])
app.include_router(vocal.router, prefix="/api/vocal", tags=["vocal"])
app.include_router(recommandations.router, prefix="/api/recommandations", tags=["recommandations"])
app.include_router(fiches.router, prefix="/api/fiches", tags=["fiches"])


@app.get("/")
async def root():
    return {"app": settings.app_name, "status": "running"}


@app.get("/health")
async def health():
    return {"status": "ok"}
