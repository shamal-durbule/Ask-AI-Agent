"""Tests for the analytics SQL validation layer.

These tests verify that the sqlglot-based validation correctly:
- Allows valid SELECT statements
- Rejects DML/DDL (INSERT, UPDATE, DELETE, DROP)
- Injects LIMIT when missing
- Rejects multiple statements
"""

import pytest

from app.agent.tools.analytics_tools import validate_sql


class TestSQLValidation:
    """SQL validation tests for the analytics tool."""

    def test_valid_select(self) -> None:
        result = validate_sql("SELECT * FROM tenant")
        assert "SELECT" in result.upper()

    def test_select_with_join(self) -> None:
        sql = "SELECT t.name, l.rent_amount FROM tenant t JOIN lease l ON l.tenant_id = t.id"
        result = validate_sql(sql)
        assert "JOIN" in result.upper()

    def test_select_with_aggregation(self) -> None:
        sql = "SELECT SUM(amount_due) FROM charge WHERE status = 'overdue'"
        result = validate_sql(sql)
        assert "SUM" in result.upper()

    def test_injects_limit_when_missing(self) -> None:
        sql = "SELECT * FROM tenant"
        result = validate_sql(sql)
        assert "LIMIT" in result.upper()

    def test_preserves_existing_limit(self) -> None:
        sql = "SELECT * FROM tenant LIMIT 10"
        result = validate_sql(sql)
        assert "LIMIT 10" in result.upper() or "LIMIT\n  10" in result.upper()

    def test_rejects_insert(self) -> None:
        with pytest.raises(ValueError, match="SELECT"):
            validate_sql("INSERT INTO tenant (name) VALUES ('hacker')")

    def test_rejects_update(self) -> None:
        with pytest.raises(ValueError, match="SELECT"):
            validate_sql("UPDATE tenant SET name = 'hacked'")

    def test_rejects_delete(self) -> None:
        with pytest.raises(ValueError, match="SELECT"):
            validate_sql("DELETE FROM tenant")

    def test_rejects_drop(self) -> None:
        with pytest.raises(ValueError, match="SELECT"):
            validate_sql("DROP TABLE tenant")

    def test_rejects_multiple_statements(self) -> None:
        with pytest.raises(ValueError, match="single"):
            validate_sql("SELECT 1; DROP TABLE tenant")

    def test_rejects_invalid_syntax(self) -> None:
        with pytest.raises(ValueError):
            validate_sql("SELEC * FORM tenant")

    def test_select_with_subquery(self) -> None:
        sql = "SELECT * FROM tenant WHERE id IN (SELECT tenant_id FROM lease WHERE status = 'active')"
        result = validate_sql(sql)
        assert "SELECT" in result.upper()

    def test_select_with_cte(self) -> None:
        sql = """
        WITH overdue AS (
            SELECT lease_id, SUM(amount_due - amount_paid) as total
            FROM charge WHERE status = 'overdue'
            GROUP BY lease_id
        )
        SELECT t.name, o.total
        FROM overdue o JOIN lease l ON l.id = o.lease_id
        JOIN tenant t ON t.id = l.tenant_id
        """
        result = validate_sql(sql)
        assert "WITH" in result.upper()
