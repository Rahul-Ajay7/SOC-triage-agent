"""Triage orchestration — glue between API, agent, and DB.

Flow: receive alert -> run agent graph -> persist incident + trace -> return.
"""
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.agent.graph import run_triage
from app.models.alert import Alert
from app.models.incident import Incident
from app.models.investigation import Investigation
from app.parsers import auth_log

logger = logging.getLogger(__name__)


def create_alert(
    db: Session,
    *,
    source: str = "auth_log",
    title: str | None = None,
    raw_log: str | None = None,
    parsed: dict | None = None,
) -> Alert:
    """Persist an incoming alert. Parses raw_log if no parsed dict given."""
    if parsed is None and raw_log:
        events = auth_log.parse_log(raw_log)
        parsed = auth_log.summarize(events)
    parsed = parsed or {}

    if not title:
        ip = parsed.get("src_ip") or (parsed.get("src_ips") or ["?"])[0]
        title = (
            f"{parsed.get('failures', 0)} failed / {parsed.get('successes', 0)} ok "
            f"SSH login(s) from {ip}"
        )

    alert = Alert(source=source, title=title, raw_log=raw_log, parsed=parsed)
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def triage_alert(db: Session, alert: Alert) -> dict:
    """Run the agent on a stored alert; persist incident + trace."""
    logger.info("Triaging alert id=%s", alert.id)
    final = run_triage(raw_log=alert.raw_log or "", alert=alert.parsed or {})

    incident = Incident(
        alert_id=alert.id,
        verdict=final.get("verdict", "suspicious"),
        confidence=float(final.get("confidence", 0.0)),
        summary=final.get("summary", ""),
        iocs=final.get("iocs", {}),
        mitre=final.get("mitre", []),
        llm_source=final.get("llm_source", "heuristic"),
        action="pending",
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)

    investigation = Investigation(
        incident_id=incident.id, trace=final.get("trace", [])
    )
    db.add(investigation)

    alert.status = "triaged"
    db.commit()
    db.refresh(incident)

    return {
        "alert": alert.to_dict(),
        "incident": incident.to_dict(),
        "trace": final.get("trace", []),
    }


def ingest_and_triage(
    db: Session,
    *,
    source: str = "auth_log",
    title: str | None = None,
    raw_log: str | None = None,
    parsed: dict | None = None,
) -> dict:
    """One-shot: store the alert then immediately triage it."""
    alert = create_alert(
        db, source=source, title=title, raw_log=raw_log, parsed=parsed
    )
    return triage_alert(db, alert)


def get_trace(db: Session, incident_id: int) -> list[dict]:
    inv = (
        db.query(Investigation)
        .filter(Investigation.incident_id == incident_id)
        .order_by(Investigation.id.desc())
        .first()
    )
    return inv.trace if inv else []


def set_action(db: Session, incident: Incident, action: str, note: str | None) -> Incident:
    incident.action = action
    incident.action_note = note
    db.commit()
    db.refresh(incident)
    logger.info(
        "Incident %s marked %s at %s", incident.id, action,
        datetime.now(timezone.utc).isoformat(),
    )
    return incident
