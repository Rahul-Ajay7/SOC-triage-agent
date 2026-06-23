"""Request/response schemas for alerts."""
from typing import Any, Optional

from pydantic import BaseModel, Field


class AlertCreate(BaseModel):
    """Push an alert in. Provide raw_log OR pre-parsed dict (or both)."""

    source: str = Field(default="auth_log", description="Log source type")
    title: Optional[str] = Field(default=None, description="Optional human title")
    raw_log: Optional[str] = Field(default=None, description="Raw log line(s)")
    parsed: Optional[dict[str, Any]] = Field(
        default=None, description="Pre-parsed structured fields"
    )


class AlertOut(BaseModel):
    id: int
    source: str
    title: str
    raw_log: Optional[str]
    parsed: dict[str, Any]
    status: str
    created_at: Optional[str]
