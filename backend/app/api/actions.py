"""Action routes — human-in-the-loop approve/reject of agent verdicts."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.incident import Incident
from app.schemas.incident import ActionRequest
from app.services import triage_service

router = APIRouter(prefix="/api/incidents", tags=["actions"])


@router.post("/{incident_id}/action")
def take_action(
    incident_id: int, payload: ActionRequest, db: Session = Depends(get_db)
):
    """Analyst approves or rejects the agent's verdict."""
    if payload.action not in ("approved", "rejected"):
        raise HTTPException(400, "action must be 'approved' or 'rejected'")
    incident = db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(404, "Incident not found")
    updated = triage_service.set_action(db, incident, payload.action, payload.note)
    return updated.to_dict()
