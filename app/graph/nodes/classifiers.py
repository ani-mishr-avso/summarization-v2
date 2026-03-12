import logging
from typing import Any, Callable

from app.config import get_llm
from app.graph.state import CallState
from app.prompts.loader import load_prompt
from app.utils.llm_response import invoke_and_decode_json
from app.utils.logger import get_logger

logger = get_logger(__name__)


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

    If ``call_type`` is already set in the state (e.g. user-provided override
    via the /recompute endpoint) the LLM classification is skipped entirely and
    ``confidence_level`` is forced to ``"HIGH"`` so that the routing logic does
    not send the call to the fallback expert.
    """
    if state.get("call_type"):
        logger.info(
            "Level 1 classifier: call_type already set to '%s', bypassing LLM classification",
            state["call_type"],
        )
        # Force HIGH confidence so routing_logic does not divert to fallback
        return {
            "call_type": state["call_type"],
            "confidence_level": "HIGH",
            "call_type_reasoning": "As provided by user",
        }

    logger.info("Level 1 classifier: Calling _classify")
    out = _classify(
        prompt_name="level_1",
        prompt_kwargs={"transcript": state["transcript"]},
        result_mapper=lambda r: {
            "call_type": r["call_type"],
            "confidence_level": r["confidence_level"],
            "call_type_reasoning": r["call_type_reasoning"],
            "participant_roles": r["participant_roles"],
        },
        log_fmt="Level 1 classifier: call_type=%s confidence_level=%s call_type_reasoning=%s",
        log_keys=["call_type", "confidence_level", "call_type_reasoning"],
    )
    logger.info("Level 1 classifier: %s", out)
    return out


def level_2_ae_classifier(state: CallState):
    """
    Determines the AE stage (Discovery, Demo, Proposal, Close).

    If ``ae_stage`` is already set in the state (e.g. user-provided override
    via the /recompute endpoint) the LLM classification is skipped entirely.
    """
    if state.get("ae_stage"):
        logger.info(
            "Level 2 AE classifier: ae_stage already set to '%s', bypassing LLM classification",
            state["ae_stage"],
        )
        return {"ae_stage": state["ae_stage"]}

    logger.info("Level 2 AE classifier: Calling _classify")
    out = _classify(
        prompt_name="level_2",
        prompt_kwargs={
            "transcript": state["transcript"],
            "crm_stage": state["metadata"].get("crm_opportunity_stage"),
        },
        result_mapper=lambda r: {
            "ae_stage": r["ae_stage"],
            "ae_stage_reasoning": r["ae_stage_reasoning"],
            "confidence_level": r["confidence_level"],
        },
        log_fmt="Level 2 AE classifier: ae_stage=%s ae_stage_reasoning=%s confidence_level=%s",
        log_keys=["ae_stage", "ae_stage_reasoning", "confidence_level"],
    )
    logger.info("Level 2 AE classifier: %s", out)
    return out
