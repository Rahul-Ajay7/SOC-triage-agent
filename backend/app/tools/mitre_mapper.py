"""MITRE ATT&CK mapper — map alert evidence to ATT&CK techniques.

Loads a local technique DB (data/mitre_attack.json) once. Matches on
keyword triggers against the alert + evidence. No network, fully free.
"""
import json
from functools import lru_cache
from typing import Any

from app.config import MITRE_DB_PATH


@lru_cache(maxsize=1)
def _load_db() -> list[dict]:
    try:
        with open(MITRE_DB_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _signals_from(alert: dict, evidence: dict) -> list[str]:
    """Build a lowercase keyword haystack from the alert + gathered evidence."""
    parts: list[str] = [str(alert)]
    if alert.get("failures", 0) and alert.get("failures") >= 5:
        parts.append("brute force multiple failed login attempts")
    if alert.get("success_after_failures"):
        parts.append("successful login after failures valid accounts")
    rep = evidence.get("ip_reputation") or []
    if any(r.get("is_malicious") for r in rep):
        parts.append("malicious ip external remote")
    geo = evidence.get("geo") or {}
    if geo.get("impossible"):
        parts.append("impossible travel anomalous location valid accounts")
    return [p.lower() for p in parts]


def map_techniques(alert: dict, evidence: dict | None = None) -> list[dict[str, Any]]:
    """Return matched ATT&CK techniques as [{id, name, tactic, reason}]."""
    evidence = evidence or {}
    haystack = " ".join(_signals_from(alert, evidence))

    matched: list[dict] = []
    for tech in _load_db():
        triggers = [t.lower() for t in tech.get("triggers", [])]
        hit = next((t for t in triggers if t in haystack), None)
        if hit:
            matched.append({
                "id": tech["id"],
                "name": tech["name"],
                "tactic": tech.get("tactic", ""),
                "url": tech.get("url", ""),
                "reason": f"Matched signal: '{hit}'",
            })
    return matched
