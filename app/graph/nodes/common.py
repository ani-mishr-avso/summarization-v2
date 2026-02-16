"""Shared helpers for graph nodes."""

from app.config import get_llm
from app.graph.state import CallState
from app.prompts.loader import load_prompt
from app.utils.llm_response import invoke_and_decode_json


def run_simple_expert(
    state: CallState,
    category: str,
    filename: str,
    template_name: str | None = None,
) -> CallState:
    """
    Load prompt, invoke LLM, decode JSON, and set state for a single-summary expert.
    Mutates state["final_summary"], state["voss_analysis"], state["methodology_analysis"] and returns state.
    """
    prompt_name = template_name if template_name is not None else filename
    prompt = load_prompt(category, prompt_name, transcript=state["transcript"])
    llm = get_llm()
    state["final_summary"] = invoke_and_decode_json(lambda: llm.invoke(prompt))
    state["voss_analysis"] = None
    state["methodology_analysis"] = None
    return state
