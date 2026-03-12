from typing import Any, Optional

from pydantic import BaseModel, Field


class SummarizeRequest(BaseModel):
    transcript: list[dict[str, Any]] = Field(
        ..., description="Transcript with speaker labels and timestamps"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional metadata (e.g. meeting_title, participant_domains, internal_domains)",
    )
    org_config: dict[str, Any] = Field(
        default_factory=dict, description="Optional org config (e.g. sales_methodology)"
    )


class RecomputeRequest(SummarizeRequest):
    """Identical to SummarizeRequest, but allows for manual classification overrides.

    If ``call_type`` is specified, the L1 classifier is bypassed.
    If ``ae_stage`` is also specified (relevant only for AE/Sales calls), the L2 classifier is bypassed as well.
    """

    call_type: Optional[str] = Field(
        None,
        description=(
            "User-corrected L1 classification."
            "Must be one of: AE/Sales, Internal, CSM/Post-Sale, SDR/Outbound, Unclassified."
        ),
    )
    ae_stage: Optional[str] = Field(
        None,
        description="User-corrected L2 AE stage (e.g. Discovery, Demo, Proposal, Close). Only relevant when call_type='AE/Sales'.",
    )


class SummarizeResponse(BaseModel):
    """Graph output with optional fields; only non-None values are included."""

    final_summary: dict[str, Any] | None = None
    voss_analysis: dict[str, Any] | None = None
    methodology_analysis: dict[str, Any] | None = None
    participant_roles: dict[str, Any] | None = None
    expert_insights: dict[str, Any] | None = None
    call_type: str | None = None
    ae_stage: str | None = None
    confidence_score: float | None = None

    model_config = {"extra": "allow"}
