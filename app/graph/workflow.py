import logging

from langgraph.graph import END, StateGraph

from app.config import get_routing_config
from app.graph.nodes import (
    ae_expert_agent,
    csm_expert_agent,
    fallback_expert,
    internal_expert_agent,
    level_1_classifier,
    level_2_ae_classifier,
    sdr_expert_agent,
)
from app.graph.state import CallState

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
logger.addHandler(handler)


# --- Routing Logic ---
def routing_logic(state: CallState):
    """
    Determines the expert path based on confidence and call type.
    """
    logger.info(
        "Call Type: %s, Confidence Level: %s, Transcript Length: %s words",
        state["call_type"],
        state["confidence_level"],
        len(state["transcript"].split()),
    )
    cfg = get_routing_config()
    fallback_confidence_levels = cfg["fallback_confidence_levels"]
    min_word_count = cfg["min_word_count"]
    call_type_to_path = cfg["call_type_to_path"]

    if (
        state["confidence_level"] in fallback_confidence_levels
        or len(state["transcript"].split()) < min_word_count
    ):
        logger.info("Routing to fallback")
        path = "fallback"
    else:
        path = call_type_to_path.get(state["call_type"], "fallback")

    logger.info(
        "Routing logic: call_type=%s confidence_level=%s path=%s",
        state["call_type"],
        state["confidence_level"],
        path,
    )
    return path


# --- Graph Construction ---
workflow = StateGraph(CallState)

# Add Nodes
workflow.add_node("classify_l1", level_1_classifier)
workflow.add_node("classify_l2_ae", level_2_ae_classifier)
workflow.add_node("ae_expert", ae_expert_agent)
workflow.add_node("csm_expert", csm_expert_agent)
workflow.add_node("internal_expert", internal_expert_agent)
workflow.add_node("sdr_expert", sdr_expert_agent)
workflow.add_node("fallback", fallback_expert)

# Set Entry Point
workflow.set_entry_point("classify_l1")

# Define Conditional Edges
workflow.add_conditional_edges(
    "classify_l1",
    routing_logic,
    {
        "ae_path": "classify_l2_ae",
        "csm_path": "csm_expert",
        "internal_path": "internal_expert",
        "sdr_path": "sdr_expert",
        "fallback": "fallback",
    },
)

# AE Stage routing
workflow.add_edge("classify_l2_ae", "ae_expert")

# All expert paths lead to completion
workflow.add_edge("ae_expert", END)
workflow.add_edge("csm_expert", END)
workflow.add_edge("internal_expert", END)
workflow.add_edge("sdr_expert", END)
workflow.add_edge("fallback", END)

# Compile the application
app = workflow.compile()
