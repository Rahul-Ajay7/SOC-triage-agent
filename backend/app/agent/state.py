"""Agent state — what flows through the LangGraph state machine.

One dict carried node-to-node. Each node reads what it needs, writes its
results, and appends to `trace` (the reasoning replay shown in the UI).
"""
from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    # --- input ---
    raw_log: str
    alert: dict[str, Any]          # parsed/structured alert

    # --- gathered during the run ---
    iocs: dict[str, list[str]]     # ips/domains/hashes/users...
    evidence: dict[str, Any]       # ip_reputation, geo, log_search results
    confidence: float              # 0..1, how sure the agent is
    verdict: str                   # benign | suspicious | critical
    mitre: list[dict[str, Any]]    # matched ATT&CK techniques
    summary: str                   # final incident report
    llm_source: str                # which provider answered (or "heuristic")

    # --- control / observability ---
    iterations: int                # enrich loops taken
    trace: list[dict[str, Any]]    # ordered reasoning steps
    _route: str                    # conditional-edge decision after assess


def new_state(raw_log: str = "", alert: dict | None = None) -> AgentState:
    return AgentState(
        raw_log=raw_log or "",
        alert=alert or {},
        iocs={},
        evidence={},
        confidence=0.0,
        verdict="suspicious",
        mitre=[],
        summary="",
        llm_source="heuristic",
        iterations=0,
        trace=[],
    )
