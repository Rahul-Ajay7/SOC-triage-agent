"""Agent nodes — each function is one step in the triage loop.

Every node:
  - reads/writes the shared AgentState
  - appends a human-readable step to state["trace"] (the UI replay)
  - works WITHOUT an LLM (heuristics) and gets sharper WITH one

The loop-back-on-low-confidence between `enrich` and `assess` is what
makes this agentic rather than a single LLM call.
"""
import json
import logging
from datetime import datetime, timezone

from app.agent import prompts
from app.agent.llm import call_llm, json_llm
from app.agent.state import AgentState
from app.config import AGENT_CONFIDENCE_THRESHOLD, AGENT_MAX_ITERATIONS
from app.parsers import auth_log
from app.tools import geo_lookup, ioc_extractor, ip_reputation, log_search, mitre_mapper

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _trace(state: AgentState, step: str, label: str, detail: str, data=None) -> None:
    state.setdefault("trace", []).append({
        "step": step,
        "label": label,
        "detail": detail,
        "data": data or {},
        "iteration": state.get("iterations", 0),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


def _risk_signals(alert: dict, evidence: dict) -> dict:
    """Deterministic signal extraction shared by assess/classify/summarize."""
    rep = evidence.get("ip_reputation") or []
    geo = evidence.get("geo") or {}
    ls = evidence.get("log_search") or {}

    # Combine the alert's own counts with anything historical log search found.
    failures = max(alert.get("failures", 0) or 0, ls.get("failures", 0) or 0)
    success_after_failures = bool(alert.get("success_after_failures")) or (
        (ls.get("failures", 0) or 0) > 0 and (ls.get("successes", 0) or 0) > 0
    )
    return {
        "malicious_ip": any(r.get("is_malicious") for r in rep),
        "all_internal": bool(rep) and all(
            r.get("category") == "internal" for r in rep
        ),
        "impossible_travel": bool(geo.get("impossible")),
        "brute_force": failures >= 5,
        "success_after_failures": success_after_failures,
        "failures": failures,
    }


def _evidence_brief(state: AgentState) -> str:
    """Compact JSON context handed to the LLM nodes."""
    return json.dumps({
        "alert": state.get("alert", {}),
        "iocs": state.get("iocs", {}),
        "evidence": state.get("evidence", {}),
        "mitre": state.get("mitre", []),
    }, default=str)[:6000]


# --------------------------------------------------------------------------- #
# nodes
# --------------------------------------------------------------------------- #
def ingest(state: AgentState) -> AgentState:
    """Parse the raw log into a structured alert (if not already parsed)."""
    alert = dict(state.get("alert") or {})
    raw = state.get("raw_log") or ""

    if not alert and raw:
        events = auth_log.parse_log(raw)
        alert = auth_log.summarize(events)

    state["alert"] = alert
    _trace(
        state, "ingest", "Ingest alert",
        f"Parsed alert: {alert.get('total', 0)} event(s), "
        f"{alert.get('failures', 0)} failed / {alert.get('successes', 0)} ok "
        f"from {alert.get('src_ips') or alert.get('src_ip')}.",
        {"alert": alert},
    )
    return state


def extract_iocs(state: AgentState) -> AgentState:
    """Pull IPs/domains/hashes/users out of the alert."""
    iocs = ioc_extractor.extract_from_alert(
        state.get("alert", {}), state.get("raw_log", "")
    )
    state["iocs"] = iocs
    _trace(
        state, "extract_iocs", "Extract IOCs",
        f"Found {len(iocs.get('ips', []))} IP(s), "
        f"{len(iocs.get('users', []))} user(s), "
        f"{len(iocs.get('hashes', []))} hash(es).",
        iocs,
    )
    return state


def enrich(state: AgentState) -> AgentState:
    """Call tools to gather evidence. Iteration-aware: digs deeper on re-runs."""
    it = state.get("iterations", 0)
    evidence = dict(state.get("evidence") or {})
    iocs = state.get("iocs", {})
    ips = iocs.get("ips", [])

    if it == 0:
        # First pass: external reputation + geolocation / impossible travel.
        rep = ip_reputation.check_ips(ips)
        geo = geo_lookup.impossible_travel(ips)
        evidence["ip_reputation"] = rep
        evidence["geo"] = geo
        bad = [r["ip"] for r in rep if r.get("is_malicious")]
        _trace(
            state, "enrich", "Enrich — reputation & geo",
            f"Checked {len(ips)} IP(s). Malicious: {bad or 'none'}. "
            f"Impossible travel: {geo.get('impossible')} "
            f"(max {geo.get('max_distance_km', 0)} km).",
            {"ip_reputation": rep, "geo": geo},
        )
    else:
        # Deeper pass (triggered by low confidence): pivot on the source IP to
        # see EVERYTHING it did — surfaces brute force spread across usernames.
        primary_ip = ips[0] if ips else None
        ls = log_search.search(ip=primary_ip)
        evidence["log_search"] = ls
        _trace(
            state, "enrich", "Enrich — historical log search",
            f"Pivoted on ip={primary_ip}: {ls['total_hits']} related event(s) "
            f"({ls['failures']} failed, {ls['successes']} ok) across history.",
            ls,
        )

    state["evidence"] = evidence
    state["iterations"] = it + 1
    return state


def assess(state: AgentState) -> AgentState:
    """Decide confidence + whether to dig more. Sets state['confidence']."""
    alert = state.get("alert", {})
    evidence = state.get("evidence", {})
    sig = _risk_signals(alert, evidence)
    has_history = "log_search" in evidence

    # --- try LLM, fall back to heuristic ---
    parsed, source = json_llm(
        prompts.ANALYST_SYSTEM,
        f"{prompts.ASSESS_INSTRUCTIONS}\n\nEvidence:\n{_evidence_brief(state)}",
    )
    if parsed and "confidence" in parsed:
        confidence = float(parsed.get("confidence", 0.5))
        need_more = bool(parsed.get("need_more_evidence", False))
        reason = parsed.get("reasoning", "")
        state["llm_source"] = source
    else:
        # Heuristic: strong/clear signals = high confidence; thin = loop.
        strong = (sig["malicious_ip"] or sig["impossible_travel"]
                  or sig["all_internal"] or sig["brute_force"])
        if strong:
            confidence = 0.9
        elif has_history:
            confidence = 0.8
        else:
            confidence = 0.55
        need_more = confidence < AGENT_CONFIDENCE_THRESHOLD
        reason = "Heuristic assessment from gathered signals."

    state["confidence"] = confidence
    can_loop = state.get("iterations", 0) < AGENT_MAX_ITERATIONS
    will_loop = need_more and confidence < AGENT_CONFIDENCE_THRESHOLD and can_loop
    state["_route"] = "enrich" if will_loop else "classify"

    _trace(
        state, "assess", "Assess confidence",
        f"Confidence {confidence:.0%}. {reason} "
        + ("Need more evidence → looping back to enrich."
           if will_loop else "Sufficient → proceeding to classify."),
        {"confidence": confidence, "need_more": need_more, "route": state["_route"]},
    )
    return state


def route_after_assess(state: AgentState) -> str:
    """Conditional edge: loop back to enrich, or move on to classify."""
    return state.get("_route", "classify")


def classify(state: AgentState) -> AgentState:
    """Final verdict + MITRE ATT&CK mapping."""
    alert = state.get("alert", {})
    evidence = state.get("evidence", {})
    sig = _risk_signals(alert, evidence)

    mitre = mitre_mapper.map_techniques(alert, evidence)
    state["mitre"] = mitre

    parsed, source = json_llm(
        prompts.ANALYST_SYSTEM,
        f"{prompts.CLASSIFY_INSTRUCTIONS}\n\nEvidence:\n{_evidence_brief(state)}",
    )
    if parsed and parsed.get("verdict") in ("benign", "suspicious", "critical"):
        verdict = parsed["verdict"]
        state["confidence"] = float(parsed.get("confidence", state.get("confidence", 0.8)))
        reason = parsed.get("reasoning", "")
        state["llm_source"] = source
    else:
        # Heuristic verdict ladder.
        if sig["impossible_travel"] or (sig["malicious_ip"] and sig["success_after_failures"]):
            verdict = "critical"
        elif sig["brute_force"] and sig["success_after_failures"]:
            verdict = "critical"
        elif sig["brute_force"] or sig["malicious_ip"]:
            verdict = "suspicious"
        elif sig["all_internal"] and not sig["failures"]:
            verdict = "benign"
        else:
            verdict = "suspicious"
        reason = "Heuristic verdict from risk signals."

    state["verdict"] = verdict
    _trace(
        state, "classify", "Classify verdict",
        f"Verdict: {verdict.upper()}. {reason} "
        f"MITRE: {[m['id'] for m in mitre] or 'none'}.",
        {"verdict": verdict, "mitre": mitre},
    )
    return state


def summarize(state: AgentState) -> AgentState:
    """Write the incident report shown to the analyst."""
    alert = state.get("alert", {})
    evidence = state.get("evidence", {})
    verdict = state.get("verdict", "suspicious")
    sig = _risk_signals(alert, evidence)

    answer, source = call_llm(
        prompts.ANALYST_SYSTEM,
        f"{prompts.SUMMARIZE_INSTRUCTIONS}\n\n"
        f"Verdict: {verdict}\nEvidence:\n{_evidence_brief(state)}",
    )
    if answer:
        summary = answer
        state["llm_source"] = source
    else:
        ips = (state.get("iocs", {}).get("ips") or ["unknown"])
        geo = evidence.get("geo", {})
        parts = [
            f"Verdict: {verdict.upper()} (confidence {state.get('confidence', 0):.0%}).",
            f"Source IP(s): {', '.join(ips)}.",
            f"{sig['failures']} failed login(s); "
            f"{'success after failures' if sig['success_after_failures'] else 'no successful login'}.",
        ]
        if sig["malicious_ip"]:
            parts.append("At least one source IP has known-malicious reputation.")
        if sig["impossible_travel"]:
            parts.append(
                f"Impossible travel detected (~{geo.get('max_distance_km', 0)} km apart).")
        mitre_ids = [m["id"] for m in state.get("mitre", [])]
        if mitre_ids:
            parts.append(f"MITRE ATT&CK: {', '.join(mitre_ids)}.")
        parts.append(
            "Recommend human review and credential reset."
            if verdict != "benign" else "No action required.")
        summary = " ".join(parts)

    state["summary"] = summary
    _trace(state, "summarize", "Summarize incident", summary, {"summary": summary})
    return state
