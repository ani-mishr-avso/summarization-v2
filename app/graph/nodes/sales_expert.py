import asyncio
import logging

from app.config import get_llm, get_methodology_config
from app.graph.state import CallState
from app.prompts.loader import load_prompt
from app.utils.llm_response import ainvoke_and_decode_json
from app.utils.logger import get_logger
from app.utils.stage import normalize_ae_stage


logger = get_logger(__name__)


async def ae_expert_agent(state: CallState):
    """
    Parallel extraction of Summary, Voss, and Methodology.

    Args:
        state: The current state of the call.
    Returns:
        The updated state with the final summary, voss analysis, and methodology analysis.
    """
    logger.info("AE expert agent called")
    default_methodology = get_methodology_config()["default_sales_methodology"]
    stage = normalize_ae_stage(state["ae_stage"])
    meth_name = (
        state["org_config"].get("sales_methodology", default_methodology).lower()
    )
    logger.info("Normalizing AE stage: %s", stage)
    llm = get_llm("technical_llm")

    logger.info("Loading summary prompt: %s", stage)
    summary_p = load_prompt("summarization/ae", stage, transcript=state["transcript"])

    logger.info("Loading VOSS prompt: %s", stage)
    voss_p = load_prompt("voss_framework", stage, transcript=state["transcript"])

    logger.info("Loading Sales Methodology prompt: %s", meth_name)
    meth_p = load_prompt("methodologies", meth_name, transcript=state["transcript"])

    tasks = [
        ainvoke_and_decode_json(lambda: llm.ainvoke(summary_p)),
        ainvoke_and_decode_json(lambda: llm.ainvoke(voss_p)),
        ainvoke_and_decode_json(lambda: llm.ainvoke(meth_p)),
    ]
    logger.info("Invoking tasks")
    results = await asyncio.gather(*tasks)
    logger.info("Tasks completed")

    state["final_summary"] = results[0]
    state["voss_analysis"] = results[1]
    state["methodology_analysis"] = results[2]
    return state
