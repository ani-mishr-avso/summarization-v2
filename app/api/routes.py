import logging
import os

from fastapi import APIRouter, HTTPException

from app.api.schemas import SummarizeRequest
from app.graph import app

router = APIRouter()
logger = logging.getLogger(__name__)


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
    transcript_len = len(body.transcript.split())
    logger.info("Summarize request started, transcript_length=%d", transcript_len)
    try:
        result = await app.ainvoke({
            "transcript": body.transcript,
            "metadata": body.metadata,
            "org_config": body.org_config,
        })
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
