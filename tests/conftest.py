"""Shared test fixtures."""

from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """Mock async database session for unit tests."""
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.flush = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def test_client() -> Generator[TestClient, None, None]:
    """FastAPI test client backed by a hermetic in-memory SQLite database.

    Overrides the `get_db` dependency so API tests never touch PostgreSQL,
    making them deterministic across platforms. A StaticPool keeps a single
    shared connection so all sessions see the same in-memory schema.
    """
    from app.database import get_db
    from app.main import app
    from app.models import Base

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    schema_ready = False

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        nonlocal schema_ready
        if not schema_ready:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            schema_ready = True
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = _override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
