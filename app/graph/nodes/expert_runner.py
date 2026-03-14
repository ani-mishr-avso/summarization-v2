"""Shared helpers for running single-summary expert nodes."""

import logging

from app.config import get_llm
from app.graph.state import CallState
from app.prompts.loader import load_prompt
from app.utils.llm_response import invoke_and_decode_json


logger = logging.getLogger(__name__)


def run_simple_expert(
    state: CallState,
    category: str,
    filename: str,
    template_name: str | None = None,
) -> CallState:
    """
    Load prompt, invoke LLM, decode JSON, and set state for a single-summary expert.
    Mutates state["final_summary"], state["seller_insights"], state["sales_methodology_analysis"] and returns state.
    """
    prompt_name = template_name or filename
    logger.info(
        "Running simple expert with category: %s, filename: %s, template_name: %s",
        category,
        filename,
        template_name,
    )
    prompt = load_prompt(category, prompt_name, transcript=state["transcript"])
    llm = get_llm("technical_llm")
    state["final_summary"] = invoke_and_decode_json(lambda: llm.invoke(prompt))
    state["seller_insights"] = None
    state["sales_methodology_analysis"] = None
    return state
