"""Tests for exactly-once execution of approval-gated actions.

These verify the CAS (compare-and-swap) status transitions on `action_log`
guarantee that an approved action executes exactly once, even if the approval
request is retried.
"""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.models import Base
from app.models.chat import ActionStatus
from app.repositories.chat_repo import ChatRepository


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        yield s
    await engine.dispose()


async def _seed_pending_action(repo: ChatRepository, action_id: str = "act-1") -> str:
    await repo.create_session("sess-1", title="Test")
    await repo.create_action_log(
        action_id=action_id,
        session_id="sess-1",
        tool_name="apply_credit",
        params={"lease_id": 1, "amount": 50, "reason": "test"},
        preview="Apply $50 credit to lease #1",
    )
    return action_id


@pytest.mark.asyncio
async def test_approve_then_execute_transitions(session: AsyncSession) -> None:
    repo = ChatRepository(session)
    action_id = await _seed_pending_action(repo)

    approved = await repo.approve_action(action_id)
    assert approved is not None
    assert approved.status == ActionStatus.APPROVED

    executed = await repo.mark_executed(action_id)
    assert executed is not None
    assert executed.status == ActionStatus.EXECUTED
    assert executed.executed_at is not None


@pytest.mark.asyncio
async def test_double_approve_is_noop(session: AsyncSession) -> None:
    """A retried approve must not re-open an already-approved action."""
    repo = ChatRepository(session)
    action_id = await _seed_pending_action(repo)

    first = await repo.approve_action(action_id)
    assert first is not None

    second = await repo.approve_action(action_id)
    assert second is None  # CAS only matches PENDING


@pytest.mark.asyncio
async def test_execute_runs_exactly_once(session: AsyncSession) -> None:
    """The core guarantee: mark_executed succeeds once, then is a no-op."""
    repo = ChatRepository(session)
    action_id = await _seed_pending_action(repo)

    await repo.approve_action(action_id)

    first_exec = await repo.mark_executed(action_id)
    assert first_exec is not None

    # A retried execution finds status=EXECUTED and does nothing.
    second_exec = await repo.mark_executed(action_id)
    assert second_exec is None


@pytest.mark.asyncio
async def test_cannot_execute_without_approval(session: AsyncSession) -> None:
    """A pending (never approved) action cannot be marked executed."""
    repo = ChatRepository(session)
    action_id = await _seed_pending_action(repo)

    result = await repo.mark_executed(action_id)
    assert result is None

    current = await repo.get_action_log(action_id)
    assert current is not None
    assert current.status == ActionStatus.PENDING


@pytest.mark.asyncio
async def test_reject_blocks_execution(session: AsyncSession) -> None:
    repo = ChatRepository(session)
    action_id = await _seed_pending_action(repo)

    rejected = await repo.reject_action(action_id)
    assert rejected is not None
    assert rejected.status == ActionStatus.REJECTED

    # Once rejected, it can never be approved or executed.
    assert await repo.approve_action(action_id) is None
    assert await repo.mark_executed(action_id) is None
