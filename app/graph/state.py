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
    call_type_reasoning: Optional[str]
    ae_stage: Optional[str]
    ae_stage_reasoning: Optional[str]
    confidence_level: Literal["LOW", "MEDIUM", "HIGH", "VERY HIGH"]

    # Output Layers
    final_summary: Dict[str, Any]
    seller_insights: Optional[Dict[str, Any]] | None
    sales_methodology_analysis: Optional[Dict[str, Any]] | None
    participant_roles: list[Dict[str, Any]]
