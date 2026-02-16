#!/usr/bin/env python3
"""Run the Summarizer API with uvicorn."""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
