"""Stage 2 - draw each comic panel with a Gemini image model."""

from __future__ import annotations

from typing import Callable

from google.genai import types

from .story import Panel, Story
from .utils import with_retries


class ImageGenerationError(RuntimeError):
    """Raised when Gemini returns no image for a panel."""


def build_image_prompt(story: Story, panel: Panel, has_reference: bool) -> str:
    """Compose the drawing prompt for one panel.

    Character descriptions are repeated in every prompt, and the previous
    panel can be attached as a reference image, to keep faces and outfits
    consistent across the whole comic.
    """
    characters = "\n".join(f"- {c.name}: {c.appearance}" for c in story.characters)
    reference_note = (
        "A reference image of the previous panel is attached. Keep every "
        "character looking exactly the same (face, hair, clothes, colours).\n"
        if has_reference
        else ""
    )
    return f"""Draw ONE comic book panel (square format).

ART STYLE: {story.art_style}

CHARACTERS (keep them consistent):
{characters}

{reference_note}SCENE: {panel.scene}

Important: do NOT draw any text, letters, captions, numbers, logos or speech
bubbles. Leave some empty space near the top and bottom of the image because
text will be added later.
"""


def _extract_image_bytes(response) -> bytes | None:
    """Return the first inline image found in a Gemini response, if any."""
    for candidate in getattr(response, "candidates", None) or []:
        content = getattr(candidate, "content", None)
        for part in getattr(content, "parts", None) or []:
            inline = getattr(part, "inline_data", None)
            if inline is not None and getattr(inline, "data", None):
                return inline.data
    return None


def generate_panel_image(
    client,
    model: str,
    story: Story,
    panel: Panel,
    reference_image: bytes | None = None,
) -> bytes:
    """Generate one panel image and return it as raw image bytes."""
    prompt = build_image_prompt(story, panel, has_reference=reference_image is not None)

    contents: list = [prompt]
    if reference_image:
        contents.append(types.Part.from_bytes(data=reference_image, mime_type="image/png"))

    def _call():
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
        )
        image = _extract_image_bytes(response)
        if image is None:
            raise ImageGenerationError(
                f"Gemini did not return an image for panel {panel.number}."
            )
        return image

    return with_retries(_call, attempts=3, base_delay=3.0)


def generate_all_panels(
    client,
    model: str,
    story: Story,
    progress: Callable[[int, int, str], None] | None = None,
) -> list[bytes | None]:
    """Generate every panel in order.

    A failed panel does not stop the run: its slot is ``None`` and the layout
    stage draws a placeholder, so the user always gets a complete comic page.
    """
    results: list[bytes | None] = []
    previous: bytes | None = None
    total = len(story.panels)

    for index, panel in enumerate(story.panels, start=1):
        if progress:
            progress(index - 1, total, f"Drawing panel {index} of {total}...")
        try:
            image = generate_panel_image(client, model, story, panel, previous)
            previous = image
            results.append(image)
        except Exception as exc:  # noqa: BLE001 - keep going, show placeholder
            results.append(None)
            if progress:
                progress(index - 1, total, f"Panel {index} failed: {exc}")

    if progress:
        progress(total, total, "Done!")
    return results
