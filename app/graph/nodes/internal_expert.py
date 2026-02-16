from app.config import get_llm
from app.graph.state import CallState
from app.prompts.loader import load_prompt
from app.utils.llm_response import invoke_and_decode_json


def internal_expert_agent(state: CallState):
    """
    Generates a JSON-constrained summary based on the detected Internal stage.

    Args:
        state: The current state of the call.
    Returns:
        The updated state with the final summary.
    """
    prompt = load_prompt("summarization", "internal", transcript=state["transcript"])
    llm = get_llm()
    state["final_summary"] = invoke_and_decode_json(lambda: llm.invoke(prompt))
    state["voss_analysis"] = None
    state["methodology_analysis"] = None
    return state
