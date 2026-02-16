from app.config import get_config, get_llm
from app.graph.state import CallState
from app.prompts.loader import load_prompt
from app.utils.llm_response import invoke_and_decode_json


def csm_expert_agent(state: CallState):
    """
    Generates a JSON-constrained summary based on the detected CSM stage (QBR, Onboarding, Health Check, or Expansion).

    Args:
        state: The current state of the call.
    Returns:
        The updated state with the final summary.
    """
    cfg = get_config()["csm"]
    qbr_duration_minutes = cfg["qbr_duration_minutes"]
    qbr_template = cfg["qbr_template"]
    general_template = cfg["general_template"]

    is_qbr = (
        "QBR" in state["metadata"].get("meeting_title", "")
        or state["metadata"].get("duration", 0) > qbr_duration_minutes
    )
    template = qbr_template if is_qbr else general_template

    prompt = load_prompt("summarization/csm", template, transcript=state["transcript"])
    llm = get_llm()
    state["final_summary"] = invoke_and_decode_json(lambda: llm.invoke(prompt))
    state["voss_analysis"] = None
    state["methodology_analysis"] = None
    return state
