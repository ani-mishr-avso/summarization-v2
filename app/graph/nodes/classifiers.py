import logging
from typing import Any, Callable

from app.config import get_llm
from app.graph.state import CallState
from app.prompts.loader import load_prompt
from app.utils.llm_response import invoke_and_decode_json

logger = logging.getLogger(__name__)


def _classify(
    state: CallState,
    prompt_name: str,
    prompt_kwargs: dict[str, Any],
    result_mapper: Callable[[dict], dict],
    log_fmt: str,
    log_keys: list[str],
) -> dict:
    """Load classifier prompt, invoke LLM, decode JSON, map to state update, and log."""
    llm = get_llm()
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
    is_internal_only = all(
        d in state["metadata"].get("internal_domains", [])
        for d in state["metadata"].get("participant_domains", [])
    )

    if is_internal_only:
        out = {"call_type": "Internal", "confidence_score": 1.0}
        logger.info(
            "level_1_classifier: call_type=%s confidence_score=%s",
            out["call_type"],
            out["confidence_score"],
        )
        return out

    return _classify(
        state,
        prompt_name="level_1",
        prompt_kwargs={"transcript": state["transcript"]},
        result_mapper=lambda r: {
            "call_type": r["call_type"],
            "confidence_score": r["confidence_score"],
        },
        log_fmt="level_1_classifier: call_type=%s confidence_score=%s",
        log_keys=["call_type", "confidence_score"],
    )


def level_2_ae_classifier(state: CallState):
    """
    Determines the AE stage (Discovery, Demo, Proposal, Close).
    """
    return _classify(
        state,
        prompt_name="level_2",
        prompt_kwargs={
            "transcript": state["transcript"],
            "crm_stage": state["metadata"].get("crm_opportunity_stage"),
        },
        result_mapper=lambda r: {"ae_stage": r["ae_stage"]},
        log_fmt="level_2_ae_classifier: ae_stage=%s",
        log_keys=["ae_stage"],
    )
