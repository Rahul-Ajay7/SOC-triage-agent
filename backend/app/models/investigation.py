"""Investigation — the agent's full reasoning trace (the star feature).

Ordered list of steps so the frontend can replay exactly how the agent
thought: which tool it called, what it found, why it looped.
"""
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer

from app.database import Base


class Investigation(Base):
    __tablename__ = "investigations"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(
        Integer, ForeignKey("incidents.id"), nullable=False, index=True
    )

    # Each step: {step, label, detail, data, timestamp, iteration}
    trace = Column(JSON, default=list, nullable=False)

    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "incident_id": self.incident_id,
            "trace": self.trace or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
