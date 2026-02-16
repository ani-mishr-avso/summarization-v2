import logging

from app.config import get_llm
from app.graph.state import CallState
from app.prompts.loader import load_prompt
from app.utils.llm_response import invoke_and_decode_json

logger = logging.getLogger(__name__)


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
        logger.info("level_1_classifier: call_type=%s confidence_score=%s", out["call_type"], out["confidence_score"])
        return out

    llm = get_llm()
    prompt = load_prompt("classifiers", "level_1", transcript=state["transcript"])
    result = invoke_and_decode_json(lambda: llm.invoke(prompt))
    out = {
        "call_type": result["call_type"],
        "confidence_score": result["confidence_score"],
    }
    logger.info("level_1_classifier: call_type=%s confidence_score=%s", out["call_type"], out["confidence_score"])
    return out


def level_2_ae_classifier(state: CallState):
    """
    Determines the AE stage (Discovery, Demo, Proposal, Close).
    """
    crm_stage = state["metadata"].get("crm_opportunity_stage")
    llm = get_llm()
    prompt = load_prompt(
        "classifiers", "level_2", transcript=state["transcript"], crm_stage=crm_stage
    )

    result = invoke_and_decode_json(lambda: llm.invoke(prompt))
    ae_stage = result["ae_stage"]
    logger.info("level_2_ae_classifier: ae_stage=%s", ae_stage)
    return {"ae_stage": ae_stage}
