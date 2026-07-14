
import ipaddress
from typing import Any

import requests

from app.config import ABUSEIPDB_API_KEY

# Hardcoded "known bad" set for offline demos (genuinely public addresses —
# TEST-NET doc ranges can't be used: Python treats them as private/internal).
_DEMO_BAD = {"45.155.205.233", "185.220.101.66"}


def _is_private(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
        return addr.is_private or addr.is_loopback or addr.is_link_local
    except ValueError:
        return False


def _heuristic(ip: str) -> dict[str, Any]:
    if _is_private(ip):
        return {
            "ip": ip,
            "source": "heuristic",
            "abuse_score": 0,
            "category": "internal",
            "is_malicious": False,
            "detail": "Private/internal address — trusted network range.",
        }
    if ip in _DEMO_BAD:
        return {
            "ip": ip,
            "source": "heuristic",
            "abuse_score": 92,
            "category": "malicious",
            "is_malicious": True,
            "detail": "Listed in known-bad indicator set.",
        }
    return {
        "ip": ip,
        "source": "heuristic",
        "abuse_score": 10,
        "category": "unknown",
        "is_malicious": False,
        "detail": "No reputation data available (offline heuristic).",
    }


def _abuseipdb(ip: str) -> dict[str, Any]:
    resp = requests.get(
        "https://api.abuseipdb.com/api/v2/check",
        params={"ipAddress": ip, "maxAgeInDays": 90},
        headers={"Key": ABUSEIPDB_API_KEY, "Accept": "application/json"},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json().get("data", {})
    score = int(data.get("abuseConfidenceScore", 0))
    return {
        "ip": ip,
        "source": "abuseipdb",
        "abuse_score": score,
        "category": "malicious" if score >= 50 else "suspicious" if score >= 15 else "clean",
        "is_malicious": score >= 50,
        "total_reports": data.get("totalReports", 0),
        "country": data.get("countryCode"),
        "isp": data.get("isp"),
        "detail": f"AbuseIPDB confidence {score}% over {data.get('totalReports', 0)} reports.",
    }


def check_ip(ip: str) -> dict[str, Any]:
    """Look up reputation for a single IP. Never raises — degrades gracefully."""
    if not ip:
        return {"ip": ip, "source": "none", "abuse_score": 0, "is_malicious": False}

    # Always treat internal IPs locally — don't waste API quota on them.
    if _is_private(ip):
        return _heuristic(ip)

    if ABUSEIPDB_API_KEY:
        try:
            return _abuseipdb(ip)
        except Exception as e:  # network/quota/parse — fall back, never crash triage
            result = _heuristic(ip)
            result["detail"] += f" (AbuseIPDB unavailable: {e})"
            return result

    return _heuristic(ip)


def check_ips(ips: list[str]) -> list[dict[str, Any]]:
    return [check_ip(ip) for ip in ips]
