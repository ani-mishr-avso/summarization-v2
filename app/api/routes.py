import logging
import os
import re

from fastapi import APIRouter, HTTPException

from app.api.schemas import SummarizeRequest
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


def parse_metadata(metadata):
    user_map = metadata["user_map"]
    speaker_labels, domains = parse_user_map(user_map)
    # formatted_transcript = format_transcript(data["transcript"], speaker_labels)
    # duration_mins = get_duration_mins(data["transcript"])
    meeting_title = metadata["topic"]

    metadata = {
        "meeting_title": meeting_title,
        "duration_mins": duration_mins,
        "participant_domains": domains,
        "internal_domains": data["metadata"].get("internal_domains", []),
    }

    return formatted_transcript, metadata


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
