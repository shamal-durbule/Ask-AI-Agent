"""Analytics tools for text-to-SQL query execution.

These tools support the analytics skill by providing schema information
and executing validated read-only SQL queries.
"""

import json
import logging
from typing import Any

import sqlglot
from sqlglot import exp
from strands import tool

from app.config import settings
from app.database import async_session_factory
from app.repositories.analytics_repo import AnalyticsRepository

logger = logging.getLogger(__name__)

FORBIDDEN_STATEMENTS = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Create,
    exp.Alter,
    exp.Command,
)


def validate_sql(sql: str) -> str:
    """Validate and sanitize SQL for read-only execution.

    Raises ValueError if the SQL is not a safe SELECT statement.
    Returns the validated (and potentially modified) SQL string.
    """
    try:
        parsed = sqlglot.parse(sql, dialect="postgres")
    except sqlglot.errors.ParseError as e:
        raise ValueError(f"Invalid SQL syntax: {e}") from e

    if len(parsed) != 1:
        raise ValueError("Only single SQL statements are allowed")

    statement = parsed[0]
    if statement is None:
        raise ValueError("Empty SQL statement")

    if isinstance(statement, FORBIDDEN_STATEMENTS):
        raise ValueError(f"Only SELECT statements are allowed. Got: {type(statement).__name__}")

    if not isinstance(statement, exp.Select):
        raise ValueError(f"Only SELECT statements are allowed. Got: {type(statement).__name__}")

    # Check for subqueries that modify data
    for node in statement.walk():
        if isinstance(node, FORBIDDEN_STATEMENTS):
            raise ValueError(f"Forbidden operation in subquery: {type(node).__name__}")

    # Inject LIMIT if not present
    if statement.args.get("limit") is None:
        statement = statement.limit(settings.max_query_rows)

    return statement.sql(dialect="postgres")


@tool
async def get_database_schema() -> str:
    """Get the database schema with all table names, columns, and data types.

    Use this before writing SQL queries to understand the available tables and
    their structure. Returns column names, types, and nullability for each table.
    """
    async with async_session_factory() as session:
        repo = AnalyticsRepository(session)
        info = await repo.get_table_info()

    tables: dict[str, list[dict[str, Any]]] = {}
    for row in info:
        table_name = row["table_name"]
        if table_name not in tables:
            tables[table_name] = []
        tables[table_name].append(
            {
                "column": row["column_name"],
                "type": row["data_type"],
                "nullable": row["is_nullable"],
            }
        )

    schema_text = "Database Schema:\n\n"
    for table_name, columns in sorted(tables.items()):
        schema_text += f"Table: {table_name}\n"
        for col in columns:
            nullable = " (nullable)" if col["nullable"] == "YES" else ""
            schema_text += f"  - {col['column']}: {col['type']}{nullable}\n"
        schema_text += "\n"

    schema_text += """Key relationships:
  - unit.property_id -> property.id
  - lease.unit_id -> unit.id
  - lease.tenant_id -> tenant.id
  - charge.lease_id -> lease.id
  - payment.charge_id -> charge.id
  - message.tenant_id -> tenant.id
  - scheduled_message.tenant_id -> tenant.id

Key enum values:
  - unit.status: 'available', 'leased'
  - lease.status: 'active', 'ended'
  - charge.status: 'open', 'paid', 'overdue'
  - charge.kind: 'rent', 'late_fee', 'credit'
  - message.direction: 'outbound', 'inbound'
  - payment.method: 'ach', 'check', 'credit_card', 'cash'
"""
    return schema_text


@tool
async def execute_readonly_query(sql: str) -> str:
    """Execute a read-only SQL SELECT query against the property management database.

    Args:
        sql: A valid PostgreSQL SELECT query. Only SELECT statements are allowed.
             The query will be validated and a LIMIT will be added if not present.

    Returns the query results as a JSON array of objects.
    Use get_database_schema first to understand the available tables and columns.
    """
    try:
        validated_sql = validate_sql(sql)
    except ValueError as e:
        return f"SQL validation error: {e}"

    logger.info("Executing validated SQL: %s", validated_sql)

    try:
        async with async_session_factory() as session:
            repo = AnalyticsRepository(session)
            rows = await repo.execute_readonly(validated_sql)
    except Exception as e:
        logger.warning("SQL execution error: %s", e)
        return f"Query execution error: {e}"

    if not rows:
        return "Query returned no results."

    return json.dumps(rows, default=str)
