import secrets
from datetime import datetime
from typing import Any

from advanced_alchemy.base import SQLQuery
from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    Column,
    Integer,
    String,
    MetaData,
    ForeignKey,
    UniqueConstraint,
    inspect,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship
from sqlalchemy.ext.mutable import MutableDict, MutableList


from src.schemas.users import UserPreferences
from src.schemas.base import Schema
from src.utils.time import now as time_now
from src.utils.common import unique_id
from src.models.utils import *
from src.utils.sqltypes import MutableModel


class User(RecordModel):
    __tablename__ = "users"

    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(
        String, unique=True, index=True, nullable=True
    )
    is_verified: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    is_superuser: Mapped[bool] = mapped_column(default=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    token_version: Mapped[int] = mapped_column(default=0)

    preferences: Mapped[UserPreferences] = mapped_column(
        "preferences",
        MutableModel(UserPreferences),
        default=UserPreferences,
        server_default='{"theme": "system", "notifications": {"reminders": true, "health_tips": true}}',
    )

    sessions: Mapped[list["UserSession"]] = relationship(
        "UserSession",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class UserSession(RecordModel):
    """
    Tracks refresh-token sessions per device.

    Redis stores the active session for fast lookup (< 1ms).
    This table is the source of truth for device management UI
    and allows enumeration of all sessions for a user.
    """

    __tablename__ = "user_sessions"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"), index=True, nullable=False
    )
    user: Mapped["User"] = relationship("User", back_populates="sessions")
    session_id: Mapped[str] = mapped_column(
        String, unique=True, index=True, nullable=False
    )
    refresh_token_hash: Mapped[str] = mapped_column(String, index=True, nullable=False)
    # Device metadata for "My Devices" UI
    device_name: Mapped[str | None] = mapped_column(String, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
