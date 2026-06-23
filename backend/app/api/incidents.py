"""Incident routes — verdicts and the agent reasoning trace."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.incident import Incident
from app.services import triage_service

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


@router.get("")
def list_incidents(db: Session = Depends(get_db), limit: int = 100):
    rows = db.query(Incident).order_by(Incident.id.desc()).limit(limit).all()
    return [i.to_dict() for i in rows]


@router.get("/{incident_id}")
def get_incident(incident_id: int, db: Session = Depends(get_db)):
    """Incident verdict + summary + full reasoning trace."""
    incident = db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(404, "Incident not found")
    return {
        **incident.to_dict(),
        "trace": triage_service.get_trace(db, incident_id),
    }


@router.get("/{incident_id}/trace")
def get_incident_trace(incident_id: int, db: Session = Depends(get_db)):
    """Just the agent's step-by-step reasoning trace (the star feature)."""
    incident = db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(404, "Incident not found")
    return {"incident_id": incident_id, "trace": triage_service.get_trace(db, incident_id)}
