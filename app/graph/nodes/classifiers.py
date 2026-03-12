from typing import Any, Callable

from app.config import get_llm
from app.graph.state import CallState
from app.prompts.loader import load_prompt
from app.utils.llm_response import invoke_and_decode_json
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _maybe_override(
    state: CallState,
    key: str,
    override_payload_builder: Callable[[Any], dict[str, Any]],
    log_message: str,
) -> dict[str, Any] | None:
    """
    Return an override payload if the given ``key`` is present in ``state``.

    If the key is set, logs ``log_message`` with the corresponding value and
    returns the result of ``override_payload_builder``. Otherwise returns ``None``.
    """
    if key not in state:
        return None

    value = state[key]
    logger.info(log_message, value)
    return override_payload_builder(value)


def _classify(
    prompt_name: str,
    prompt_kwargs: dict[str, Any],
    result_mapper: Callable[[dict[str, Any]], dict[str, Any]],
    log_fmt: str,
    log_keys: list[str],
) -> dict[str, Any]:
    """
    Load classifier prompt, invoke LLM, decode JSON, map to state update, and log.

    The ``result_mapper`` must return a dictionary containing at least the keys
    listed in ``log_keys`` so they can be safely interpolated into ``log_fmt``.
    """
    llm = get_llm("strategic_llm")
    prompt = load_prompt("classifiers", prompt_name, **prompt_kwargs)
    result = invoke_and_decode_json(lambda: llm.invoke(prompt))
    out = result_mapper(result)
    logger.info(log_fmt, *[out[k] for k in log_keys])
    return out


def _map_level_1_result(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "call_type": result["call_type"],
        "confidence_level": result["confidence_level"],
        "call_type_reasoning": result["call_type_reasoning"],
        "participant_roles": result["participant_roles"],
    }


def _map_level_2_result(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "ae_stage": result["ae_stage"],
        "ae_stage_reasoning": result["ae_stage_reasoning"],
        "confidence_level": result["confidence_level"],
    }


def level_1_classifier(state: CallState):
    """
    Determines whether the call is AE/Sales, Internal, CSM, or SDR.

    If the state already includes a ``call_type`` (such as when a user sets an override
    through the /recompute endpoint), the LLM is not called and ``confidence_level``
    is automatically set to ``"HIGH"`` to ensure the routing logic does not redirect to a fallback expert.
    """
    override = _maybe_override(
        state=state,
        key="call_type",
        override_payload_builder=lambda call_type: {
            "call_type": call_type,
            # Force HIGH confidence so routing_logic does not divert to fallback
            "confidence_level": "HIGH",
            "call_type_reasoning": "As provided by user",
        },
        log_message=(
            "Level 1 classifier: call_type already set to '%s', bypassing LLM classification"
        ),
    )
    if override is not None:
        return override

    logger.info("Level 1 classifier: Calling _classify")
    out = _classify(
        prompt_name="level_1",
        prompt_kwargs={"transcript": state["transcript"]},
        result_mapper=_map_level_1_result,
        log_fmt="Level 1 classifier: call_type=%s confidence_level=%s call_type_reasoning=%s",
        log_keys=["call_type", "confidence_level", "call_type_reasoning"],
    )
    logger.info("Level 1 classifier: %s", out)
    return out


def level_2_ae_classifier(state: CallState):
    """
    Determines which AE stage the call corresponds to (such as Discovery, Demo, Proposal, or Close).

    If the state already contains an ``ae_stage`` value (for example, when set by the user through the /recompute endpoint), the LLM classification step is completely bypassed.
    """
    override = _maybe_override(
        state=state,
        key="ae_stage",
        override_payload_builder=lambda ae_stage: {"ae_stage": ae_stage},
        log_message=(
            "Level 2 AE classifier: ae_stage already set to '%s', bypassing LLM classification"
        ),
    )
    if override is not None:
        return override

    logger.info("Level 2 AE classifier: Calling _classify")
    out = _classify(
        prompt_name="level_2",
        prompt_kwargs={
            "transcript": state["transcript"],
            "crm_stage": state["metadata"].get("crm_opportunity_stage"),
        },
        result_mapper=_map_level_2_result,
        log_fmt="Level 2 AE classifier: ae_stage=%s ae_stage_reasoning=%s confidence_level=%s",
        log_keys=["ae_stage", "ae_stage_reasoning", "confidence_level"],
    )
    logger.info("Level 2 AE classifier: %s", out)
    return out
