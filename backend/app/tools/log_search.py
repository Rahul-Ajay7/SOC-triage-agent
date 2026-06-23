"""Log search tool — query historical events for context.

Searches stored alerts (the SQLite DB) plus the seed log corpus for
related activity by IP or user. This is what the agent calls when it
needs MORE evidence (the loop-back-on-low-confidence path).
"""
from typing import Any

from app.config import HISTORY_DIR
from app.database import SessionLocal
from app.models.alert import Alert
from app.parsers import auth_log


def _load_seed_events() -> list[dict]:
    """Parse the historical .log corpus in data/history into auth events."""
    events: list[dict] = []
    if not HISTORY_DIR.exists():
        return events
    for path in HISTORY_DIR.glob("*.log"):
        try:
            events.extend(auth_log.parse_log(path.read_text(encoding="utf-8")))
        except OSError:
            continue
    return events


def search(ip: str | None = None, user: str | None = None,
           limit: int = 50) -> dict[str, Any]:
    """Find related events by IP and/or user across DB + seed corpus."""
    hits: list[dict] = []

    # 1) Seed corpus on disk
    for ev in _load_seed_events():
        if ip and ev.get("src_ip") != ip:
            continue
        if user and ev.get("user") != user:
            continue
        hits.append({**ev, "store": "seed_corpus"})

    # 2) Previously ingested alerts in the DB (best-effort — skip if no schema)
    db = SessionLocal()
    try:
        for alert in db.query(Alert).order_by(Alert.id.desc()).limit(200).all():
            p = alert.parsed or {}
            ips = p.get("src_ips") or ([p.get("src_ip")] if p.get("src_ip") else [])
            users = p.get("users") or ([p.get("user")] if p.get("user") else [])
            if ip and ip not in ips:
                continue
            if user and user not in users:
                continue
            hits.append({
                "store": "db",
                "alert_id": alert.id,
                "src_ip": ips[0] if ips else None,
                "user": users[0] if users else None,
                "status": p.get("status"),
                "timestamp": p.get("first_timestamp") or p.get("timestamp"),
            })
    except Exception:  # noqa: BLE001 — DB optional; seed corpus is enough
        pass
    finally:
        db.close()

    failures = sum(1 for h in hits if h.get("status") == "failure")
    successes = sum(1 for h in hits if h.get("status") == "success")
    return {
        "query": {"ip": ip, "user": user},
        "total_hits": len(hits),
        "failures": failures,
        "successes": successes,
        "results": hits[:limit],
    }
