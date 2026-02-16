"""Provide OpenAI Responses API helpers for graph nodes.

Args:
    None.

Returns:
    None.

Example:
    >>> client = get_openai_client()
"""

from __future__ import annotations

import logging
from typing import TypeVar

from openai import OpenAI
from pydantic import BaseModel

from code_reviewer_graph.settings import get_settings


ParsedResponseModel = TypeVar("ParsedResponseModel", bound=BaseModel)


def get_openai_client() -> OpenAI:
    """Build an authenticated OpenAI SDK client.

    Args:
        None.

    Returns:
        An initialized `OpenAI` client.

    Example:
        >>> client = get_openai_client()
        >>> isinstance(client, OpenAI)
        True
    """

    settings = get_settings()
    if not settings.openrouter_api_key:
        message = (
            "Operation failed: missing OPENROUTER_API_KEY while "
            "building OpenAI "
            "client in get_openai_client. Suggested action: set "
            "OPENROUTER_API_KEY in .env or shell environment and retry."
        )
        raise RuntimeError(
            message
        )
    logger = logging.getLogger(__name__)
    logger.info("Attempting to create OpenAI client in get_openai_client")
    client = OpenAI(
        base_url=settings.openrouter_base_url,
        api_key=settings.openrouter_api_key,
    )
    logger.info("Successfully created OpenAI client in get_openai_client")
    return client


def run_responses_prompt(
    prompt: str,
    response_schema: type[ParsedResponseModel],
) -> ParsedResponseModel:
    """Send a prompt using the OpenAI Responses API with typed parsing.

    Args:
        prompt: Prompt text to submit to the configured model.
        response_schema: Pydantic model used to enforce structured output.

    Returns:
        Parsed response object validated against response_schema.

    Example:
        >>> from pydantic import BaseModel
        >>> class Reply(BaseModel):
        ...     status: str
        >>> reply = run_responses_prompt("Respond with OK", Reply)
    """

    settings = get_settings()
    client = get_openai_client()
    logger = logging.getLogger(__name__)
    logger.info("Attempting Responses API request in run_responses_prompt")
    response = client.responses.parse(
        model=settings.openai_model,
        input=prompt,
        text_format=response_schema,
    )
    logger.info(
        "Successfully completed Responses API request in run_responses_prompt"
    )
    parsed_response = response.output_parsed
    if parsed_response is None:
        message = (
            "Operation failed: model returned no structured payload in "
            "run_responses_prompt. Suggested action: verify model "
            "structured-output support and retry."
        )
        raise RuntimeError(message)
    return parsed_response
