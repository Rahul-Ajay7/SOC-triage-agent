"""LangGraph state machine wiring the triage nodes together.

    START
      -> ingest
      -> extract_iocs
      -> enrich  <-------------+
      -> assess --------------+|  (loop back if confidence is LOW)
           |                  ||
           +-- classify ------+
      -> summarize
      -> END

The enrich <-> assess loop (low-confidence -> dig more) is the agentic spine.
"""
from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from app.agent import nodes
from app.agent.state import AgentState, new_state


@lru_cache(maxsize=1)
def build_graph():
    """Compile the triage graph once and reuse it."""
    g = StateGraph(AgentState)

    g.add_node("ingest", nodes.ingest)
    g.add_node("extract_iocs", nodes.extract_iocs)
    g.add_node("enrich", nodes.enrich)
    g.add_node("assess", nodes.assess)
    g.add_node("classify", nodes.classify)
    g.add_node("summarize", nodes.summarize)

    g.add_edge(START, "ingest")
    g.add_edge("ingest", "extract_iocs")
    g.add_edge("extract_iocs", "enrich")
    g.add_edge("enrich", "assess")

    # The loop: assess decides whether to gather more or move on.
    g.add_conditional_edges(
        "assess",
        nodes.route_after_assess,
        {"enrich": "enrich", "classify": "classify"},
    )

    g.add_edge("classify", "summarize")
    g.add_edge("summarize", END)

    return g.compile()


def run_triage(raw_log: str = "", alert: dict | None = None) -> AgentState:
    """Run the full agent loop on one alert. Returns the final state."""
    graph = build_graph()
    initial = new_state(raw_log=raw_log, alert=alert)
    # recursion_limit guards against runaway loops (we also cap via iterations).
    return graph.invoke(initial, config={"recursion_limit": 25})
