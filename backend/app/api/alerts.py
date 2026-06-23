"""Alert routes — push alerts in, pull the queue out."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.alert import Alert
from app.schemas.alert import AlertCreate
from app.services import triage_service

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.post("")
def create_and_triage(payload: AlertCreate, db: Session = Depends(get_db)):
    """Push an alert in — it is stored AND triaged by the agent immediately.

    Returns the alert, the agent's incident verdict, and the full trace.
    """
    if not payload.raw_log and not payload.parsed:
        raise HTTPException(400, "Provide raw_log and/or parsed fields.")
    return triage_service.ingest_and_triage(
        db,
        source=payload.source,
        title=payload.title,
        raw_log=payload.raw_log,
        parsed=payload.parsed,
    )


@router.get("")
def list_alerts(db: Session = Depends(get_db), limit: int = 100):
    """The alert queue (newest first)."""
    rows = db.query(Alert).order_by(Alert.id.desc()).limit(limit).all()
    return [a.to_dict() for a in rows]


@router.get("/{alert_id}")
def get_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(404, "Alert not found")
    return alert.to_dict()
