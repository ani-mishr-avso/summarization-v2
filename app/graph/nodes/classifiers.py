import logging
from typing import Any, Callable

from app.config import get_llm
from app.graph.state import CallState
from app.prompts.loader import load_prompt
from app.utils.llm_response import invoke_and_decode_json
from app.utils.logger import get_logger

logger = get_logger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
logger.addHandler(handler)


def _classify(
    prompt_name: str,
    prompt_kwargs: dict[str, Any],
    result_mapper: Callable[[dict], dict],
    log_fmt: str,
    log_keys: list[str],
) -> dict:
    """Load classifier prompt, invoke LLM, decode JSON, map to state update, and log."""
    llm = get_llm("strategic_llm")
    prompt = load_prompt("classifiers", prompt_name, **prompt_kwargs)
    result = invoke_and_decode_json(lambda: llm.invoke(prompt))
    out = result_mapper(result)
    logger.info(log_fmt, *[out[k] for k in log_keys])
    return out


def level_1_classifier(state: CallState):
    """
    Distinguishes between AE/Sales, Internal, CSM, and SDR calls.
    """
    # Logic for High-Confidence Internal Detection
    # is_internal_only = all(
    #     d in state["metadata"].get("internal_domains", [])
    #     for d in state["metadata"].get("participant_domains", [])
    # )

    # if is_internal_only:
    #     out = {
    #         "call_type": "Internal/Implementation",
    #         "confidence_level": "VERY HIGH",
    #         "reasoning": "All participants are from internal domains",
    #     }
    #     logger.info(
    #         "Level 1 classifier: call_type=%s confidence_level=%s reasoning=%s",
    #         out["call_type"],
    #         out["confidence_level"],
    #         out["reasoning"],
    #     )
    #     logger.info("Level 1 classifier: Internal/Implementation detected")
    #     return out

    logger.info("Level 1 classifier: Calling _classify")
    out = _classify(
        prompt_name="level_1",
        prompt_kwargs={"transcript": state["transcript"]},
        result_mapper=lambda r: {
            "call_type": r["call_type"],
            "confidence_level": r["confidence_level"],
            "reasoning": r["reasoning"],
        },
        log_fmt="Level 1 classifier: call_type=%s confidence_level=%s reasoning=%s",
        log_keys=["call_type", "confidence_level", "reasoning"],
    )
    logger.info("Level 1 classifier: %s", out)
    return out


def level_2_ae_classifier(state: CallState):
    """
    Determines the AE stage (Discovery, Demo, Proposal, Close).
    """
    logger.info("Level 2 AE classifier: Calling _classify")
    out = _classify(
        prompt_name="level_2",
        prompt_kwargs={
            "transcript": state["transcript"],
            "crm_stage": state["metadata"].get("crm_opportunity_stage"),
        },
        result_mapper=lambda r: {"ae_stage": r["ae_stage"]},
        log_fmt="Level 2 AE classifier: ae_stage=%s",
        log_keys=["ae_stage"],
    )
    logger.info("Level 2 AE classifier: %s", out)
    return out
