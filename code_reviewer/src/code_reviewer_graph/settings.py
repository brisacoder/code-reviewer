"""Load environment-backed runtime configuration for OpenAI requests.

This module centralizes how `.env` and process environment variables are read
for the code-review graph.

Example:
    >>> settings = get_settings()
    >>> settings.openai_model
    'gpt-4.1-mini'
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    """Represent runtime configuration used by OpenAI helper functions.

    Args:
        openrouter_api_key: API key used to authenticate OpenAI SDK requests.
        openai_model: Model name used for Responses API calls.

    Returns:
        None.

    Example:
        >>> config = Settings(
        ...     openrouter_api_key=None,
        ...     openai_model="gpt-4.1-mini",
        ... )
    """

    openrouter_api_key: str | None
    openai_model: str
    openrouter_base_url: str

    openai_reviewer_model: str
    gemini_reviewer_model: str
    anthropic_collator_model: str

    gemini_api_key: str | None
    gemini_base_url: str | None

    anthropic_api_key: str | None
    anthropic_base_url: str | None

    reviewer_rules_file: str
    writer_rules_file: str
    writer_model: str


def get_settings() -> Settings:
    """Resolve environment variables into a validated settings object.

    The function loads `.env` values first, then falls back to process
    environment values when keys are not present in `.env`.

    Returns:
        A populated `Settings` instance with defaults where needed.

    Example:
        >>> config = get_settings()
        >>> isinstance(config.openai_model, str)
        True
    """

    package_dir = Path(__file__).resolve().parent
    default_review_rules_file = str(package_dir / "review_rules.md")
    default_writer_rules_file = str(package_dir / "writer_rules.md")
    load_dotenv()
    return Settings(
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
        openai_model=os.getenv("OPENROUTER_OPENAI_MODEL", "openai/gpt-5.2-codex"),
        openrouter_base_url="https://openrouter.ai/api/v1",
        openai_reviewer_model=os.getenv(
            "OPENAI_REVIEWER_MODEL",
            "openai/gpt-5.2-codex",
        ),
        gemini_reviewer_model=os.getenv(
            "GEMINI_REVIEWER_MODEL",
            "google/gemini-3-flash-preview",
        ),
        anthropic_collator_model=os.getenv(
            "ANTHROPIC_COLLATOR_MODEL",
            "anthropic/claude-opus-4.6",
        ),
        gemini_api_key=os.getenv("OPENROUTER_OPENAI_MODEL"),
        gemini_base_url=os.getenv("GEMINI_BASE_URL", "https://openrouter.ai/api/v1"),
        anthropic_api_key=os.getenv("OPENROUTER_OPENAI_MODEL"),
        anthropic_base_url=os.getenv("ANTHROPIC_BASE_URL", "https://openrouter.ai/api/v1"),
        reviewer_rules_file=os.getenv(
            "REVIEWER_RULES_FILE",
            default_review_rules_file,
        ),
        writer_rules_file=os.getenv(
            "WRITER_RULES_FILE",
            default_writer_rules_file,
        ),
        writer_model=os.getenv(
            "WRITER_MODEL",
            "anthropic/claude-opus-4.6",
        ),
    )
