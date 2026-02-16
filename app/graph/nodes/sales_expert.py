import asyncio

from app.config import get_config, get_llm
from app.graph.state import CallState
from app.prompts.loader import load_prompt
from app.utils.llm_response import ainvoke_and_decode_json


async def ae_expert_agent(state: CallState):
    """
    Parallel extraction of Summary, Voss, and Methodology.

    Args:
        state: The current state of the call.
    Returns:
        The updated state with the final summary, voss analysis, and methodology analysis.
    """
    cfg = get_config()
    default_methodology = cfg["methodology"]["default_sales_methodology"]
    stage = state["ae_stage"].split("/")[0].lower()
    meth_name = (
        state["org_config"].get("sales_methodology", default_methodology).lower()
    )

    llm = get_llm()

    summary_p = load_prompt("summarization/ae", stage, transcript=state["transcript"])
    voss_p = load_prompt("voss_framework", stage, transcript=state["transcript"])
    meth_p = load_prompt("methodologies", meth_name, transcript=state["transcript"])

    tasks = [
        ainvoke_and_decode_json(lambda: llm.ainvoke(summary_p)),
        ainvoke_and_decode_json(lambda: llm.ainvoke(voss_p)),
        ainvoke_and_decode_json(lambda: llm.ainvoke(meth_p)),
    ]
    results = await asyncio.gather(*tasks)

    state["final_summary"] = results[0]
    state["voss_analysis"] = results[1]
    state["methodology_analysis"] = results[2]
    return state
