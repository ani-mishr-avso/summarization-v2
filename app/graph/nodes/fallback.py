from app.config import get_fallback_config, get_llm
from app.graph.state import CallState
from app.prompts.loader import load_prompt


def fallback_expert(state: CallState):
    """
    Applies a type-neutral template (Template E) when classification is
    ambiguous or data is insufficient.
    """
    cfg = get_fallback_config()
    prompt_category = cfg["prompt_category"]
    prompt_name = cfg["prompt_name"]
    expert_type_label = cfg["expert_type_label"]

    prompt = load_prompt(prompt_category, prompt_name, transcript=state["transcript"])
    llm = get_llm()
    response = llm.invoke(prompt)

    return {
        "final_summary": response.content,
        "voss_analysis": None,
        "methodology_analysis": None,
        "participant_roles": {
            name: "Participant" for name in state["metadata"].get("attendees", [])
        },
        "expert_insights": {
            "type": expert_type_label,
            "show_prompt": True,
            "confidence": state["confidence_score"],
        },
    }
