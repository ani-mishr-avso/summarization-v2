from fastapi import FastAPI

from app.api.routes import router
from app.utils.logger import configure_logging

configure_logging()

app = FastAPI(
    title="Summarizer API",
    version="0.1.0",
    description="Transcript summarization and routing via LangGraph. Classifies calls and runs expert summarization.",
)
app.include_router(router, tags=["summarizer"])
