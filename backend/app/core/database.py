"""
Database connection and session management.
"""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from app.core.config import settings

# Create engines based on database URL
if "sqlite" in settings.database_url:
    # SQLite specific configuration
    async_engine = create_async_engine(
        settings.database_url,
        echo=settings.debug,
        future=True,
        connect_args={"check_same_thread": False},
    )
    sync_engine = create_engine(
        settings.database_url_sync,
        echo=settings.debug,
        future=True,
        connect_args={"check_same_thread": False},
    )
else:
    # PostgreSQL configuration
    async_engine = create_async_engine(
        settings.database_url,
        echo=settings.debug,
        future=True,
    )
    sync_engine = create_engine(
        settings.database_url_sync,
        echo=settings.debug,
        future=True,
    )

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# Sync session factory for Celery
SyncSessionLocal = sessionmaker(
    sync_engine,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_sync_session():
    """Get sync database session for Celery tasks."""
    session = SyncSessionLocal()
    try:
        yield session
    finally:
        session.close()


async def init_db():
    """Initialize database tables."""
    from app.models.base import Base
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
