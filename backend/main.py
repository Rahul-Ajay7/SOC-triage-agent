"""SOC Triage Agent — FastAPI entry point.

Run:  uvicorn main:app --reload --port 8001
Docs: http://localhost:8001/docs
UI:   Next.js frontend (separate, http://localhost:3000)
"""
import logging

from fastapi import Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.api import actions, alerts, incidents
from app.config import (
    APP_NAME,
    CORS_ORIGINS,
    SAMPLE_ALERTS_DIR,
    llm_available,
)
from app.database import get_db, init_db
from app.services import triage_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("soc")

from fastapi import FastAPI  # noqa: E402

app = FastAPI(title=APP_NAME, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(alerts.router)
app.include_router(incidents.router)
app.include_router(actions.router)


@app.on_event("startup")
def _startup() -> None:
    init_db()
    logger.info("DB ready. LLM configured: %s (heuristics used otherwise).", llm_available())


@app.get("/api/health")
def health():
    return {"status": "ok", "app": APP_NAME, "llm_configured": llm_available()}


@app.post("/api/seed")
def seed(db: Session = Depends(get_db)):
    """Load the demo alerts from data/sample_alerts/*.log and triage each.

    Great for the demo: one call populates the queue with a benign login,
    a brute-force attempt, and an impossible-travel compromise.
    """
    results = []
    for path in sorted(SAMPLE_ALERTS_DIR.glob("*.log")):
        raw = path.read_text(encoding="utf-8")
        res = triage_service.ingest_and_triage(
            db, source="auth_log", title=path.stem.replace("_", " ").title(), raw_log=raw
        )
        results.append({
            "scenario": path.stem,
            "verdict": res["incident"]["verdict"],
            "confidence": res["incident"]["confidence"],
            "incident_id": res["incident"]["id"],
        })
    return {"seeded": len(results), "results": results}


@app.get("/")
def root():
    return {"app": APP_NAME, "docs": "/docs", "frontend": "http://localhost:3000"}
