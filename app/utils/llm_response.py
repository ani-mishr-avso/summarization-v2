import json
import logging
import re
from collections.abc import Callable, Coroutine
from typing import Any

from tenacity import (
    AsyncRetrying,
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
)
from tenacity import before_sleep_log

logger = logging.getLogger(__name__)


def _parse_json_from_llm(raw: str) -> dict:
    """
    Parse JSON from LLM response text. Strips markdown code blocks and
    pre/post-amble. Raises on failure.

    Args:
        raw: The raw response from the LLM.
    Returns:
        The parsed JSON as a dict.
    Raises:
        json.JSONDecodeError: If the response is not valid JSON.
        ValueError: If the response is not valid JSON.
    """
    # Use regex to find text between ```json and ```
    json_match = re.search(r"```json\s*(.*?)\s*```", raw, re.DOTALL)
    if json_match:
        return json.loads(json_match.group(1))

    # Fallback: find the first { and last }
    start_index = raw.find("{")
    end_index = raw.rfind("}")
    if start_index != -1 and end_index != -1:
        return json.loads(raw[start_index : end_index + 1])

    # Final attempt: load raw
    return json.loads(raw)


def clean_json_response(raw_response: str) -> dict:
    """
    Strips markdown code blocks and pre/post-amble text
    to prevent JSONDecodeError. Returns an error dict on failure (no raise).

    Args:
        raw_response: The raw response from the LLM.
    Returns:
        The cleaned JSON response, or {"error": "...", "raw": raw_response} on failure.
    """
    try:
        return _parse_json_from_llm(raw_response)
    except (json.JSONDecodeError, ValueError):
        logger.warning("Failed to parse JSON from LLM response")
        return {"error": "Invalid JSON returned", "raw": raw_response}


def invoke_and_decode_json(
    invoke_fn: Callable[[], Any],
    max_retries: int = 3,
) -> dict:
    """
    Invoke the LLM (via invoke_fn), decode response as JSON. Retries the
    LLM call only when JSON decoding fails (json.JSONDecodeError or ValueError).

    Args:
        invoke_fn: Callable that returns an LLM response with a .content attribute (e.g. lambda: llm.invoke(prompt)).
        max_retries: Maximum number of attempts (LLM invocations). Default 3.
    Returns:
        Decoded JSON dict.
    Raises:
        json.JSONDecodeError: If decode still fails after all retries.
        ValueError: If decode still fails after all retries.
    """

    def _do() -> dict:
        response = invoke_fn()
        return _parse_json_from_llm(response.content)

    retryer = Retrying(
        retry=retry_if_exception_type((json.JSONDecodeError, ValueError)),
        stop=stop_after_attempt(max_retries),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    return retryer(_do)


async def ainvoke_and_decode_json(
    ainvoke_fn: Callable[[], Coroutine[Any, Any, Any]],
    max_retries: int = 3,
) -> dict:
    """
    Await the LLM (via ainvoke_fn), decode response as JSON. Retries the
    LLM call only when JSON decoding fails (json.JSONDecodeError or ValueError).

    Args:
        ainvoke_fn: Callable that returns a coroutine yielding an LLM response with .content (e.g. lambda: llm.ainvoke(prompt)).
        max_retries: Maximum number of attempts (LLM invocations). Default 3.
    Returns:
        Decoded JSON dict.
    Raises:
        json.JSONDecodeError: If decode still fails after all retries.
        ValueError: If decode still fails after all retries.
    """

    async def _do() -> dict:
        response = await ainvoke_fn()
        return _parse_json_from_llm(response.content)

    retryer = AsyncRetrying(
        retry=retry_if_exception_type((json.JSONDecodeError, ValueError)),
        stop=stop_after_attempt(max_retries),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    return await retryer(_do)
