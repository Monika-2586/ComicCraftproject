"""Stage 1 - turn a short idea into a structured comic script with Gemini."""

from __future__ import annotations

from google.genai import types
from pydantic import BaseModel, Field

from .utils import with_retries


class Character(BaseModel):
    name: str = Field(description="Character name")
    appearance: str = Field(
        description=(
            "Detailed, fixed visual description: age, face, hair, clothes, "
            "colours, accessories. Reused in every panel for consistency."
        )
    )


class Panel(BaseModel):
    number: int = Field(description="Panel number starting at 1")
    scene: str = Field(
        description="What the artist should draw: setting, characters, action, camera angle, mood"
    )
    caption: str = Field(
        description="Short narration box text (max 20 words). Empty string if none."
    )
    dialogue: str = Field(
        description="One short spoken line in the form 'Name: text' (max 15 words). Empty string if none."
    )


class Story(BaseModel):
    title: str = Field(description="Catchy comic title")
    art_style: str = Field(description="One-line art style used for every panel")
    characters: list[Character]
    panels: list[Panel]


def build_story_prompt(
    idea: str, genre: str, tone: str, art_style: str, num_panels: int
) -> str:
    """Create the instruction sent to the Gemini text model."""
    return f"""You are a professional comic book writer.
Turn the idea below into a {num_panels}-panel comic script.

IDEA: {idea.strip()}
GENRE: {genre}
TONE: {tone}
ART STYLE: {art_style}

Rules:
- Return exactly {num_panels} panels with a clear beginning, middle and end.
- Define 1 to 3 characters. Give each a detailed, fixed visual description.
- Every panel 'scene' must be a purely visual description an illustrator can draw.
- Keep captions and dialogue very short so they fit inside a panel.
- Do NOT describe any lettering or speech bubbles inside the 'scene' field.
- Use empty strings for caption or dialogue when a panel does not need them.
- Keep the content suitable for all ages.
"""


def _normalise(story: Story, num_panels: int) -> Story:
    """Trim extra panels and renumber so downstream code can trust the data."""
    story.panels = story.panels[:num_panels]
    for index, panel in enumerate(story.panels, start=1):
        panel.number = index
    if not story.panels:
        raise ValueError("Gemini returned a story with no panels. Please try again.")
    return story


def generate_story(
    client,
    model: str,
    idea: str,
    genre: str,
    tone: str,
    art_style: str,
    num_panels: int,
) -> Story:
    """Ask Gemini for a structured story and return it as a validated ``Story``."""
    if not idea or not idea.strip():
        raise ValueError("Please describe your comic idea first.")

    prompt = build_story_prompt(idea, genre, tone, art_style, num_panels)

    def _call():
        return client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=Story,
                temperature=0.9,
            ),
        )

    response = with_retries(_call)

    story = response.parsed
    if not isinstance(story, Story):
        # Fallback: validate the raw JSON text ourselves
        story = Story.model_validate_json(response.text)
    return _normalise(story, num_panels)
