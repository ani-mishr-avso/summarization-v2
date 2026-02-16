from app.graph.nodes.common import run_simple_expert
from app.graph.state import CallState


def sdr_expert_agent(state: CallState):
    """
    Generates a JSON-constrained summary based on the detected SDR call.

    Args:
        state: The current state of the call.
    Returns:
        The updated state with the final summary.
    """
    return run_simple_expert(state, "summarization/sdr", "sdr")
