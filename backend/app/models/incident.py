"""Incident — the agent's verdict + summary for an alert."""
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String, Text

from app.database import Base


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False, index=True)

    # benign | suspicious | critical
    verdict = Column(String(32), default="suspicious", nullable=False)
    confidence = Column(Float, default=0.0, nullable=False)
    summary = Column(Text, default="", nullable=False)

    iocs = Column(JSON, default=dict, nullable=False)
    mitre = Column(JSON, default=list, nullable=False)

    # Human-in-the-loop
    action = Column(String(32), default="pending", nullable=False)  # pending|approved|rejected
    action_note = Column(Text, nullable=True)

    llm_source = Column(String(32), default="heuristic", nullable=False)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "alert_id": self.alert_id,
            "verdict": self.verdict,
            "confidence": self.confidence,
            "summary": self.summary,
            "iocs": self.iocs or {},
            "mitre": self.mitre or [],
            "action": self.action,
            "action_note": self.action_note,
            "llm_source": self.llm_source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
