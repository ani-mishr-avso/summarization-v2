import logging

from app.config import get_fallback_config, get_llm
from app.graph.state import CallState
from app.prompts.loader import load_prompt
from app.utils.logger import get_logger


logger = get_logger(__name__)


def fallback_expert(state: CallState):
    """
    Applies a type-neutral template (Template E) when classification is
    ambiguous or data is insufficient.
    """
    logger.info("Fallback expert called")
    cfg = get_fallback_config()
    prompt_category = cfg["prompt_category"]
    prompt_name = cfg["prompt_name"]
    expert_type_label = cfg["expert_type_label"]

    logger.info(
        "Fallback expert: Loading prompt with category: %s, name: %s",
        prompt_category,
        prompt_name,
    )
    prompt = load_prompt(prompt_category, prompt_name, transcript=state["transcript"])
    llm = get_llm("technical_llm")
    response = llm.invoke(prompt)

    attendees = state["metadata"].get("attendees", [])
    participant_roles = [
        {"name": name, "role": "Participant"} for name in attendees
    ]
    return {
        "summary": response.content,
        "seller_insights": None,
        "sales_methodology_analysis": None,
        "participant_roles": participant_roles,
        "expert_insights": {
            "type": expert_type_label,
            "show_prompt": True,
            "confidence": state["confidence_level"],
        },
    }
