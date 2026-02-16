from typing import Any

from pydantic import BaseModel, Field


class SummarizeRequest(BaseModel):
    transcript: str = Field(..., description="Plain text transcript to summarize")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Optional metadata (e.g. meeting_title, participant_domains, internal_domains)")
    org_config: dict[str, Any] = Field(default_factory=dict, description="Optional org config (e.g. sales_methodology)")


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
