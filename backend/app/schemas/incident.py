"""Response schemas for incidents + actions."""
from typing import Any, Optional

from pydantic import BaseModel, Field


class IncidentOut(BaseModel):
    id: int
    alert_id: int
    verdict: str
    confidence: float
    summary: str
    iocs: dict[str, Any]
    mitre: list[dict[str, Any]]
    action: str
    action_note: Optional[str]
    llm_source: str
    created_at: Optional[str]


class TriageResult(BaseModel):
    """Full result of running the agent on an alert."""

    alert: dict[str, Any]
    incident: dict[str, Any]
    trace: list[dict[str, Any]]


class ActionRequest(BaseModel):
    """Human approve/reject an incident verdict."""

    action: str = Field(description="approved | rejected")
    note: Optional[str] = Field(default=None, description="Analyst note")
