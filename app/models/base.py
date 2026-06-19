import enum
import uuid
from datetime import datetime
from typing import TypeVar

from sqlalchemy import DateTime, Enum, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

EnumT = TypeVar("EnumT", bound=enum.Enum)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


def string_enum(enum_class: type[EnumT], *, length: int = 20) -> Enum:
    """Map a str Enum to VARCHAR using enum values (e.g. 'leased'), not names."""
    return Enum(
        enum_class,
        native_enum=False,
        length=length,
        values_callable=lambda members: [member.value for member in members],
    )


class TimestampMixin:
    """Adds created_at and updated_at columns to a model."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


def generate_uuid() -> str:
    return str(uuid.uuid4())
