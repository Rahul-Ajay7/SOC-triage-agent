"""End-to-end agent loop tests (heuristic mode — no LLM keys needed)."""
from app.agent.graph import run_triage


def test_benign_internal_login():
    raw = "Jun 19 09:14:02 web-01 sshd[2041]: Accepted publickey for alice from 10.0.0.42 port 51022 ssh2"
    final = run_triage(raw_log=raw)
    assert final["verdict"] == "benign"
    assert final["trace"]  # trace populated
    assert any(s["step"] == "summarize" for s in final["trace"])


def test_impossible_travel_is_critical():
    raw = (
        "Jun 19 14:02:10 web-01 sshd[9001]: Accepted password for bob from 159.89.113.10 port 49002 ssh2\n"
        "Jun 19 14:08:55 web-01 sshd[9015]: Accepted password for bob from 185.220.101.66 port 50112 ssh2\n"
    )
    final = run_triage(raw_log=raw)
    assert final["verdict"] == "critical"
    assert any(m["id"].startswith("T1078") for m in final["mitre"])


def test_low_confidence_triggers_enrich_loop():
    # Thin alert (2 failures, unknown external IP) should loop back to enrich.
    raw = (
        "Jun 19 03:42:55 web-01 sshd[8801]: Failed password for deploy from 185.220.101.45 port 40122 ssh2\n"
        "Jun 19 03:43:01 web-01 sshd[8802]: Failed password for deploy from 185.220.101.45 port 40130 ssh2\n"
    )
    final = run_triage(raw_log=raw)
    enrich_steps = [s for s in final["trace"] if s["step"] == "enrich"]
    assert len(enrich_steps) >= 2  # looped at least once
    # Pivoting on the IP reveals the full brute force -> escalate to critical.
    assert final["verdict"] == "critical"
