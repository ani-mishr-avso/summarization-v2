import logging
import os
from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.schemas import RecomputeRequest, SummarizeRequest
from app.graph import app
from app.transcript_parser.parser import format_transcript, get_duration_mins
from app.utils.email_utils import parse_user_map

router = APIRouter()
logger = logging.getLogger(__name__)


def _prepare_transcript_context(
    body: SummarizeRequest | RecomputeRequest,
) -> dict[str, Any]:
    """Build transcript text and metadata shared by summarize/recompute."""
    speaker_labels, domains = parse_user_map(body.metadata["user_map"])
    formatted_transcript = format_transcript(body.transcript, speaker_labels)
    duration_mins = get_duration_mins(body.transcript)
    metadata = {
        "meeting_title": body.metadata["topic"],
        "duration_mins": duration_mins,
        "participant_domains": domains,
        "internal_domains": body.metadata.get("internal_domains", []),
    }
    return {
        "transcript": formatted_transcript,
        "metadata": metadata,
    }


async def _invoke_graph(
    initial_state: dict[str, Any], success_label: str, failure_label: str
):
    """Call the summarizer graph with standardized error handling and logging."""
    try:
        result = await app.ainvoke(initial_state)
    except Exception as e:
        logger.error("%s failed: %s", failure_label, e, exc_info=True)
        raise HTTPException(
            status_code=503,
            detail=f"{failure_label} failed: {str(e)}",
        ) from e

    call_type = result.get("call_type", "unknown")
    logger.info("%s completed, call_type=%s", success_label, call_type)
    return {k: v for k, v in result.items() if v is not None}


@router.get("/health")
async def health():
    """Health check for load balancers and readiness probes."""
    return {"status": "ok"}


@router.get("/health/ready")
async def ready():
    """Readiness: ok only if GROQ_API_KEY is set."""
    if not os.getenv("GROQ_API_KEY"):
        raise HTTPException(status_code=503, detail="GROQ_API_KEY not configured")
    return {"status": "ok"}


@router.post("/summarize", response_model=None)
async def summarize(body: SummarizeRequest):
    """Run the summarizer graph on the given transcript."""
    transcript_len = len(body.transcript)
    logger.info("Summarize request started, transcript_length=%d turns", transcript_len)

    context = _prepare_transcript_context(body)
    initial_state = {
        **context,
        "org_config": body.org_config,
    }
    return await _invoke_graph(initial_state, "Summarize", "Summarization")


@router.post("/recompute", response_model=None)
async def recompute(body: RecomputeRequest):
    """Re-execute the summarizer graph using user-specified L1 and/or L2 classification overrides.

    If ``call_type`` is provided, the L1 classifier node recognizes this and bypasses its LLM call.
    Likewise, if ``ae_stage`` is also provided (applicable only to AE/Sales calls), the L2 classifier node is skipped.
    In both cases, the supplied values are passed unchanged through the graph to the expert agents.
    """
    transcript_len = len(body.transcript)
    logger.info(
        "Recompute request started, transcript_length=%d turns, call_type=%s, ae_stage=%s",
        transcript_len,
        body.call_type,
        body.ae_stage,
    )

    context = _prepare_transcript_context(body)
    # Seed the initial state with user-provided overrides; the classifier nodes
    # will detect these and bypass their LLM calls.
    initial_state = {
        **context,
        "org_config": body.org_config,
    }
    if body.call_type is not None:
        initial_state["call_type"] = body.call_type
    if body.ae_stage is not None:
        initial_state["ae_stage"] = body.ae_stage

    return await _invoke_graph(initial_state, "Recompute", "Recompute")
