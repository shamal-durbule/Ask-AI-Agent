"""Initial schema with all domain and chat tables.

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "property",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("address", sa.String(500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "unit",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("property_id", sa.Integer, sa.ForeignKey("property.id"), nullable=False),
        sa.Column("label", sa.String(50), nullable=False),
        sa.Column("bedrooms", sa.SmallInteger, nullable=False),
        sa.Column("monthly_rent", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="available"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_unit_property_status", "unit", ["property_id", "status"])

    op.create_table(
        "tenant",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("phone", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "lease",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("unit_id", sa.Integer, sa.ForeignKey("unit.id"), nullable=False),
        sa.Column("tenant_id", sa.Integer, sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("rent_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_lease_unit_status", "lease", ["unit_id", "status"])
    op.create_index("ix_lease_tenant", "lease", ["tenant_id"])

    op.create_table(
        "charge",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("lease_id", sa.Integer, sa.ForeignKey("lease.id"), nullable=False),
        sa.Column("period_month", sa.String(7), nullable=False),
        sa.Column("amount_due", sa.Numeric(10, 2), nullable=False),
        sa.Column("amount_paid", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("due_date", sa.Date, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("kind", sa.String(20), nullable=False, server_default="rent"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_charge_lease_status", "charge", ["lease_id", "status"])
    op.create_index("ix_charge_due_status", "charge", ["due_date", "status"])

    op.create_table(
        "payment",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("charge_id", sa.Integer, sa.ForeignKey("charge.id"), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("method", sa.String(20), nullable=False),
    )
    op.create_index("ix_payment_charge", "payment", ["charge_id"])

    op.create_table(
        "message",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.Integer, sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("direction", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="sent"),
        sa.Column("sent_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_message_tenant_direction", "message", ["tenant_id", "direction"])

    op.create_table(
        "scheduled_message",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.Integer, sa.ForeignKey("tenant.id"), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("send_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="scheduled"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("tenant_name", sa.String(255), nullable=True),
    )
    op.create_index("ix_scheduled_message_tenant", "scheduled_message", ["tenant_id"])

    op.create_table(
        "chat_session",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False, server_default="New Chat"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "chat_message",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("chat_session.id"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("metadata_json", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_chat_message_session", "chat_message", ["session_id"])

    op.create_table(
        "action_log",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("chat_session.id"), nullable=False),
        sa.Column("tool_name", sa.String(100), nullable=False),
        sa.Column("params_json", sa.Text, nullable=False),
        sa.Column("preview", sa.Text, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_action_log_session_status", "action_log", ["session_id", "status"])


def downgrade() -> None:
    op.drop_table("action_log")
    op.drop_table("chat_message")
    op.drop_table("chat_session")
    op.drop_table("scheduled_message")
    op.drop_table("message")
    op.drop_table("payment")
    op.drop_table("charge")
    op.drop_table("lease")
    op.drop_table("tenant")
    op.drop_table("unit")
    op.drop_table("property")
