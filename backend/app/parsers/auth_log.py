"""SSH / Linux auth.log parser.

Turns a raw auth.log line into a clean structured alert:
    {timestamp, src_ip, user, event, status, port, raw}

Handles the common sshd lines:
    Failed password for invalid user admin from 1.2.3.4 port 55514 ssh2
    Failed password for root from 1.2.3.4 port 55514 ssh2
    Accepted password for alice from 10.0.0.5 port 4022 ssh2
    Accepted publickey for deploy from 10.0.0.5 port 4022 ssh2
"""
import re
from typing import Optional

# Example prefix: "Jan 10 13:55:36 web-01 sshd[1234]: ..."
_PREFIX = re.compile(
    r"^(?P<timestamp>[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+"
    r"(?P<host>\S+)\s+sshd\[\d+\]:\s+(?P<msg>.*)$"
)

_AUTH = re.compile(
    r"(?P<status>Failed|Accepted)\s+(?P<method>password|publickey)\s+for\s+"
    r"(?:(?P<invalid>invalid user)\s+)?(?P<user>\S+)\s+"
    r"from\s+(?P<src_ip>\d{1,3}(?:\.\d{1,3}){3})"
    r"(?:\s+port\s+(?P<port>\d+))?"
)


def parse_line(line: str) -> Optional[dict]:
    """Parse one auth.log line. Returns None if it is not an auth event."""
    line = (line or "").strip()
    if not line:
        return None

    msg = line
    timestamp = None
    host = None
    m = _PREFIX.match(line)
    if m:
        timestamp = m.group("timestamp")
        host = m.group("host")
        msg = m.group("msg")

    a = _AUTH.search(msg)
    if not a:
        return None

    status = "failure" if a.group("status") == "Failed" else "success"
    return {
        "timestamp": timestamp,
        "host": host,
        "src_ip": a.group("src_ip"),
        "user": a.group("user"),
        "method": a.group("method"),
        "event": "ssh_login",
        "status": status,
        "invalid_user": bool(a.group("invalid")),
        "port": int(a.group("port")) if a.group("port") else None,
        "raw": line,
    }


def parse_log(text: str) -> list[dict]:
    """Parse a multi-line blob. Returns all auth events found."""
    events = []
    for line in (text or "").splitlines():
        parsed = parse_line(line)
        if parsed:
            events.append(parsed)
    return events


def summarize(events: list[dict]) -> dict:
    """Roll a set of related auth events into one alert summary."""
    if not events:
        return {}
    failures = [e for e in events if e["status"] == "failure"]
    successes = [e for e in events if e["status"] == "success"]
    ips = sorted({e["src_ip"] for e in events})
    users = sorted({e["user"] for e in events})
    return {
        "event": "ssh_login",
        "total": len(events),
        "failures": len(failures),
        "successes": len(successes),
        "src_ips": ips,
        "src_ip": ips[0] if len(ips) == 1 else None,
        "users": users,
        "user": users[0] if len(users) == 1 else None,
        "success_after_failures": bool(failures and successes),
        "first_timestamp": events[0].get("timestamp"),
        "last_timestamp": events[-1].get("timestamp"),
        "events": events,
    }
