"""Raw alert record — what comes IN before the agent touches it."""
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text

from app.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)

    source = Column(String(64), default="auth_log", nullable=False)
    title = Column(String(256), default="Untitled alert", nullable=False)
    raw_log = Column(Text, nullable=True)
    parsed = Column(JSON, default=dict, nullable=False)

    status = Column(String(32), default="new", nullable=False)  # new|triaged
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source": self.source,
            "title": self.title,
            "raw_log": self.raw_log,
            "parsed": self.parsed or {},
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
