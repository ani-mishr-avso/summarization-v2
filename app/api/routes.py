import logging
import os
import re

from fastapi import APIRouter, HTTPException

from app.api.schemas import RecomputeRequest, SummarizeRequest
from app.graph import app
from app.transcript_parser.parser import format_transcript, get_duration_mins

router = APIRouter()
logger = logging.getLogger(__name__)

EMAIL_DOMAIN_PATTERN = re.compile(r".+@(?P<domain>.+)$")


def get_email_domain(email):
    match = EMAIL_DOMAIN_PATTERN.match(email)
    if match:
        return match.groupdict()["domain"]
    return


def parse_user_map(user_map):
    speaker_labels = {}
    domains = set()
    for user_id, info in user_map.items():
        speaker_labels[user_id] = info["name"]
        email = info.get("email")
        if email:
            domains.add(get_email_domain(email))
    return speaker_labels, domains


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

    speaker_labels, domains = parse_user_map(body.metadata["user_map"])
    formatted_transcript = format_transcript(body.transcript, speaker_labels)
    duration_mins = get_duration_mins(body.transcript)
    metadata = {
        "meeting_title": body.metadata["topic"],
        "duration_mins": duration_mins,
        "participant_domains": domains,
        "internal_domains": body.metadata.get("internal_domains", []),
    }

    try:
        result = await app.ainvoke(
            {
                "transcript": formatted_transcript,
                "metadata": metadata,
                "org_config": body.org_config,
            }
        )
    except Exception as e:
        logger.error("Summarization failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=503,
            detail=f"Summarization failed: {str(e)}",
        ) from e
    call_type = result.get("call_type", "unknown")
    logger.info("Summarize completed, call_type=%s", call_type)
    out = {k: v for k, v in result.items() if v is not None}
    return out


@router.post("/recompute", response_model=None)
async def recompute(body: RecomputeRequest):
    """Re-run the summarizer graph with user-corrected L1/L2 classifications.

    When ``call_type`` is supplied the L1 classifier node will detect it and
    skip the LLM call entirely.  When ``ae_stage`` is additionally supplied
    (only relevant for AE/Sales calls) the L2 classifier node is also skipped.
    Both values flow through the graph unchanged into the expert agents.
    """
    transcript_len = len(body.transcript)
    logger.info(
        "Recompute request started, transcript_length=%d turns, call_type=%s, ae_stage=%s",
        transcript_len,
        body.call_type,
        body.ae_stage,
    )

    speaker_labels, domains = parse_user_map(body.metadata["user_map"])
    formatted_transcript = format_transcript(body.transcript, speaker_labels)
    duration_mins = get_duration_mins(body.transcript)
    metadata = {
        "meeting_title": body.metadata["topic"],
        "duration_mins": duration_mins,
        "participant_domains": domains,
        "internal_domains": body.metadata.get("internal_domains", []),
    }

    # Seed the initial state with user-provided overrides; the classifier nodes
    # will detect these and bypass their LLM calls.
    initial_state = {
        "transcript": formatted_transcript,
        "metadata": metadata,
        "org_config": body.org_config,
    }
    if body.call_type is not None:
        initial_state["call_type"] = body.call_type
    if body.ae_stage is not None:
        initial_state["ae_stage"] = body.ae_stage

    try:
        result = await app.ainvoke(initial_state)
    except Exception as e:
        logger.error("Recompute failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=503,
            detail=f"Recompute failed: {str(e)}",
        ) from e

    call_type = result.get("call_type", "unknown")
    logger.info("Recompute completed, call_type=%s", call_type)
    out = {k: v for k, v in result.items() if v is not None}
    return out
