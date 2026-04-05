from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.config import settings


def _build_async_url(url: str) -> str:
    """Convert a DATABASE_URL to its async driver variant."""
    if url.startswith("sqlite:///"):
        return url.replace("sqlite:///", "sqlite+aiosqlite:///")
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    # Already async-ready (postgresql+asyncpg://, sqlite+aiosqlite://, etc.)
    return url


DATABASE_URL = _build_async_url(settings.database_url)

engine_kwargs = {"echo": settings.debug}

if DATABASE_URL.startswith("postgresql+asyncpg://"):
    engine_kwargs["pool_pre_ping"] = True
    if settings.database_use_null_pool:
        engine_kwargs["poolclass"] = NullPool

engine = create_async_engine(DATABASE_URL, **engine_kwargs)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        yield session
