from app.config import get_csm_config
from app.graph.nodes.common import run_simple_expert
from app.graph.state import CallState


def csm_expert_agent(state: CallState):
    """
    Generates a JSON-constrained summary based on the detected CSM stage (QBR, Onboarding, Health Check, or Expansion).

    Args:
        state: The current state of the call.
    Returns:
        The updated state with the final summary.
    """
    cfg = get_csm_config()
    qbr_duration_minutes = cfg["qbr_duration_minutes"]
    qbr_template = cfg["qbr_template"]
    general_template = cfg["general_template"]

    is_qbr = (
        "QBR" in state["metadata"].get("meeting_title", "")
        or state["metadata"].get("duration", 0) > qbr_duration_minutes
    )
    template = qbr_template if is_qbr else general_template

    return run_simple_expert(state, "summarization/csm", template)

