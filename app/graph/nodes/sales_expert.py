import asyncio
import logging

from app.config import get_llm, get_methodology_config, get_seller_insights_config
from app.graph.state import CallState
from app.prompts.loader import load_prompt
from app.utils.llm_response import ainvoke_and_decode_json
from app.utils.logger import get_logger
from app.utils.ae_stage import normalize_ae_stage


logger = get_logger(__name__)


async def ae_expert_agent(state: CallState):
    """
    Parallel extraction of Summary, Seller Insights, and Sales Methodology.

    Args:
        state: The current state of the call.
    Returns:
        The updated state with the final summary, seller insights, and sales methodology analysis.
    """
    logger.info("AE expert agent called")
    default_methodology = get_methodology_config()["default_sales_methodology"]
    stage = normalize_ae_stage(state["ae_stage"])
    sales_methodology_name = (
        state["org_config"].get("sales_methodology", default_methodology).lower()
    )
    logger.info("Normalizing AE stage: %s", stage)
    llm = get_llm("technical_llm")

    logger.info("Loading summary prompt: %s", stage)
    summary_p = load_prompt("summarization/ae", stage, transcript=state["transcript"])

    logger.info("Loading Seller Insights prompt: %s", stage)
    stage_cfg = get_seller_insights_config().get(stage, {})
    role_title = stage_cfg.get("role_title", "")
    role_goal = stage_cfg.get("role_goal", "")
    primary_dimensions = stage_cfg.get("primary_dimensions", [])
    secondary_dimensions = stage_cfg.get("secondary_dimensions", [])
    seller_insights_p = load_prompt(
        "seller_insights",
        "base",
        transcript=state["transcript"],
        role_title=role_title,
        role_goal=role_goal,
        primary_dimensions=primary_dimensions,
        secondary_dimensions=secondary_dimensions,
    )

    logger.info("Loading Sales Methodology prompt: %s", sales_methodology_name)
    sales_methodology_p = load_prompt("methodologies", sales_methodology_name, transcript=state["transcript"])

    tasks = [
        ainvoke_and_decode_json(lambda: llm.ainvoke(summary_p)),
        ainvoke_and_decode_json(lambda: llm.ainvoke(seller_insights_p)),
        ainvoke_and_decode_json(lambda: llm.ainvoke(sales_methodology_p)),
    ]
    logger.info("Invoking tasks")
    results = await asyncio.gather(*tasks)
    logger.info("Tasks completed")

    state["summary"] = results[0]
    state["seller_insights"] = results[1]
    state["sales_methodology_analysis"] = results[2]
    return state
