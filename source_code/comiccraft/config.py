"""Central configuration for Comic Craft.

Model names change often, so they are never hard-wired into the logic.
Override them from the sidebar of the app or with environment variables.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

try:  # python-dotenv is optional; .env support is a convenience only
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover
    pass

DEFAULT_TEXT_MODEL = "gemini-2.5-flash"
DEFAULT_IMAGE_MODEL = "gemini-2.5-flash-image"

MIN_PANELS = 2
MAX_PANELS = 8


@dataclass(frozen=True)
class Settings:
    """Runtime settings used by the story and image generators."""

    api_key: str
    text_model: str = DEFAULT_TEXT_MODEL
    image_model: str = DEFAULT_IMAGE_MODEL


def load_settings(
    api_key: str | None = None,
    text_model: str | None = None,
    image_model: str | None = None,
) -> Settings:
    """Build Settings from explicit values, falling back to environment variables."""
    key = (
        api_key
        or os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
        or ""
    ).strip()
    if not key:
        raise ValueError(
            "Gemini API key is missing. Paste it in the sidebar or set "
            "GEMINI_API_KEY in your .env file."
        )
    return Settings(
        api_key=key,
        text_model=(text_model or os.getenv("COMICCRAFT_TEXT_MODEL") or DEFAULT_TEXT_MODEL).strip(),
        image_model=(image_model or os.getenv("COMICCRAFT_IMAGE_MODEL") or DEFAULT_IMAGE_MODEL).strip(),
    )
