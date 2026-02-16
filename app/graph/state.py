from typing import Any, Dict, Literal, Optional, TypedDict


class CallState(TypedDict):
    # Inputs
    transcript: str
    metadata: Dict[str, Any]
    org_config: Dict[str, Any]

    # Classifiers (call_type values must match config.yaml routing.call_type_to_path / call_types)
    call_type: Literal[
        "AE/Sales", "Internal", "CSM/Post-Sale", "SDR/Outbound", "Unclassified"
    ]
    ae_stage: Optional[str]
    confidence_score: float

    # Output Layers
    final_summary: Dict[str, Any]
    voss_analysis: Optional[Dict[str, Any]] | None
    methodology_analysis: Optional[Dict[str, Any]] | None
    participant_roles: Dict[str, Any]
    expert_insights: Optional[Dict[str, Any]]
