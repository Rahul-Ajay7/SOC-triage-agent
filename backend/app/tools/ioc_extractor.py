"""IOC extractor — pull indicators of compromise from text/alert.

Returns IPs, domains, URLs, file hashes (md5/sha1/sha256), emails, usernames.
Pure regex, no network. First tool the agent runs.
"""
import re
from typing import Any

_IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_URL = re.compile(r"\bhttps?://[^\s\"'<>]+", re.IGNORECASE)
_DOMAIN = re.compile(
    r"\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"(?:com|net|org|io|ru|cn|info|biz|xyz|top|co|gov|edu|mil|dev|app)\b",
    re.IGNORECASE,
)
_MD5 = re.compile(r"\b[a-f0-9]{32}\b", re.IGNORECASE)
_SHA1 = re.compile(r"\b[a-f0-9]{40}\b", re.IGNORECASE)
_SHA256 = re.compile(r"\b[a-f0-9]{64}\b", re.IGNORECASE)
_EMAIL = re.compile(r"\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b", re.IGNORECASE)


def _valid_ipv4(ip: str) -> bool:
    parts = ip.split(".")
    return len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts)


def extract(text: str) -> dict[str, list[str]]:
    """Extract IOCs from a string."""
    text = text or ""
    ips = sorted({ip for ip in _IPV4.findall(text) if _valid_ipv4(ip)})
    return {
        "ips": ips,
        "urls": sorted(set(_URL.findall(text))),
        "domains": sorted(set(_DOMAIN.findall(text))),
        "hashes": sorted(
            set(_SHA256.findall(text))
            | set(_SHA1.findall(text))
            | set(_MD5.findall(text))
        ),
        "emails": sorted(set(_EMAIL.findall(text))),
    }


def extract_from_alert(parsed: dict[str, Any], raw_log: str = "") -> dict[str, list[str]]:
    """Extract IOCs from a parsed alert + its raw log.

    Merges regex hits over the raw text with structured fields the parser
    already isolated (src_ips, users) so nothing is missed.
    """
    blob = raw_log or ""
    blob += " " + str(parsed) if parsed else ""
    iocs = extract(blob)

    # Fold in structured fields the parser already extracted.
    structured_ips = parsed.get("src_ips") or (
        [parsed["src_ip"]] if parsed.get("src_ip") else []
    )
    iocs["ips"] = sorted(set(iocs["ips"]) | {ip for ip in structured_ips if ip})

    users = parsed.get("users") or ([parsed["user"]] if parsed.get("user") else [])
    iocs["users"] = sorted({u for u in users if u})
    return iocs
