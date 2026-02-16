import logging

from langgraph.graph import END, StateGraph

from app.config import get_config
from app.graph.nodes.classifiers import level_1_classifier, level_2_ae_classifier
from app.graph.nodes.csm_expert import csm_expert_agent
from app.graph.nodes.fallback import fallback_expert
from app.graph.nodes.internal_expert import internal_expert_agent
from app.graph.nodes.sales_expert import ae_expert_agent
from app.graph.nodes.sdr import sdr_expert_agent
from app.graph.state import CallState

logger = logging.getLogger(__name__)


# --- Routing Logic ---
def routing_logic(state: CallState):
    """
    Determines the expert path based on confidence and call type.
    """
    cfg = get_config()["routing"]
    threshold = cfg["confidence_threshold"]
    min_words = cfg["min_word_count"]
    call_type_to_path = cfg["call_type_to_path"]

    if (
        state["confidence_score"] < threshold
        or len(state["transcript"].split()) < min_words
    ):
        path = "fallback"
    else:
        path = call_type_to_path.get(state["call_type"], "fallback")

    logger.info(
        "routing_logic: call_type=%s confidence_score=%s path=%s",
        state["call_type"],
        state["confidence_score"],
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
