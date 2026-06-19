from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings


class AnalyticsRepository:
    """Executes validated read-only SQL against the database.

    Safety measures:
    - READ ONLY transaction mode
    - Statement timeout
    - Row limit enforced at the caller level (sqlglot injection)
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute_readonly(self, sql: str) -> list[dict[str, Any]]:
        """Execute a pre-validated SELECT query in a read-only context.

        The caller (analytics tool) is responsible for SQL validation
        via sqlglot before calling this method.
        """
        timeout_ms = settings.query_timeout_seconds * 1000
        await self._session.execute(text(f"SET LOCAL statement_timeout = '{timeout_ms}'"))
        await self._session.execute(text("SET TRANSACTION READ ONLY"))

        result = await self._session.execute(text(sql))
        columns = list(result.keys())
        rows = result.fetchall()

        return [dict(zip(columns, row)) for row in rows]

    async def get_table_info(self) -> list[dict[str, Any]]:
        """Return schema metadata for all domain tables."""
        query = text("""
            SELECT
                t.table_name,
                c.column_name,
                c.data_type,
                c.is_nullable,
                c.column_default
            FROM information_schema.tables t
            JOIN information_schema.columns c
                ON c.table_schema = t.table_schema
                AND c.table_name = t.table_name
            WHERE t.table_schema = 'public'
                AND t.table_type = 'BASE TABLE'
                AND t.table_name NOT IN ('alembic_version', 'chat_session', 'chat_message', 'action_log')
            ORDER BY t.table_name, c.ordinal_position
        """)
        result = await self._session.execute(query)
        return [dict(zip(result.keys(), row)) for row in result.fetchall()]
