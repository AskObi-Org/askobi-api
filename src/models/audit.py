from datetime import datetime
from sqlalchemy import String, Integer, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from src.models.utils import IDModel, utc_now

class AccessLog(IDModel):
    __tablename__ = "access_logs"

    user_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    session_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    endpoint: Mapped[str] = mapped_column(String, nullable=False)
    method: Mapped[str] = mapped_column(String, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String, nullable=True)
    action_type: Mapped[str | None] = mapped_column(String, nullable=True)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=utc_now)
    extra: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
