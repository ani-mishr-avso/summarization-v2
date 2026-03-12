import logging

from app.graph.nodes.common import run_simple_expert
from app.graph.state import CallState
from app.utils.logger import get_logger


logger = get_logger(__name__)


def internal_expert_agent(state: CallState):
    """
    Generates a JSON-constrained summary based on the detected Internal stage.

    Args:
        state: The current state of the call.
    Returns:
        The updated state with the final summary.
    """
    logger.info("Internal expert agent called")
    out = run_simple_expert(state, "summarization", "internal")
    return out
