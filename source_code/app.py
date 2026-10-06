"""Comic Craft - Streamlit web app.

Run with:  streamlit run app.py
"""

from __future__ import annotations

import streamlit as st
from google import genai

from comiccraft.config import (
    DEFAULT_IMAGE_MODEL,
    DEFAULT_TEXT_MODEL,
    MAX_PANELS,
    MIN_PANELS,
    load_settings,
)
from comiccraft.images import generate_all_panels
from comiccraft.layout import (
    PanelArt,
    bytes_to_image,
    compose_pages,
    image_to_png_bytes,
    pages_to_pdf_bytes,
)
from comiccraft.story import generate_story

ART_STYLES = [
    "Classic American superhero comic, bold ink lines, vibrant colours",
    "Japanese manga style, expressive eyes, clean line art",
    "Cute cartoon style, soft pastel colours, rounded shapes",
    "Watercolour storybook illustration, gentle and dreamy",
    "Retro 1960s pop-art comic with halftone dots",
    "Noir comic, high-contrast black and white with red accents",
]
GENRES = ["Adventure", "Comedy", "Sci-Fi", "Fantasy", "Mystery", "Slice of life", "Superhero"]
TONES = ["Fun and light", "Inspiring", "Mysterious", "Dramatic", "Heartwarming"]

st.set_page_config(page_title="Comic Craft", page_icon="🎨", layout="wide")

# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.title("🎨 Comic Craft")
    st.caption("AI comic story creator powered by Google Gemini")

    api_key = st.text_input(
        "Gemini API key",
        type="password",
        help="Free key from https://aistudio.google.com/apikey (or set GEMINI_API_KEY in .env)",
    )
    with st.expander("Model settings"):
        text_model = st.text_input("Story model", value=DEFAULT_TEXT_MODEL)
        image_model = st.text_input("Image model", value=DEFAULT_IMAGE_MODEL)

    st.divider()
    num_panels = st.slider("Number of panels", MIN_PANELS, MAX_PANELS, 4)
    genre = st.selectbox("Genre", GENRES)
    tone = st.selectbox("Tone", TONES)
    art_style = st.selectbox("Art style", ART_STYLES)


def get_client():
    """Create a Gemini client from the sidebar key or the environment."""
    settings = load_settings(api_key, text_model, image_model)
    return genai.Client(api_key=settings.api_key), settings


# ---------------------------------------------------------------- main page
st.header("Turn your idea into a comic")
idea = st.text_area(
    "Your story idea",
    placeholder="A shy girl builds a tiny robot that helps her make friends at school...",
    height=110,
)

if st.button("✍️ 1. Write the story", type="primary"):
    try:
        client, settings = get_client()
        with st.spinner("Gemini is writing your script..."):
            st.session_state["story"] = generate_story(
                client, settings.text_model, idea, genre, tone, art_style, num_panels
            )
        st.session_state.pop("images", None)  # a new story invalidates old art
        st.session_state["story_id"] = st.session_state.get("story_id", 0) + 1  # fresh widget keys
    except Exception as exc:  # noqa: BLE001 - show any API/validation problem to the user
        st.error(f"Could not write the story: {exc}")

story = st.session_state.get("story")

if story:
    st.subheader(f"📖 {story.title}")
    st.caption(f"Art style: {story.art_style}")

    with st.expander("Characters", expanded=False):
        for character in story.characters:
            st.markdown(f"**{character.name}** - {character.appearance}")

    st.markdown("Review and edit the script. Your edits are used when the comic is drawn.")
    sid = st.session_state.get("story_id", 0)
    for panel in story.panels:
        with st.expander(f"Panel {panel.number}", expanded=False):
            panel.scene = st.text_area("Scene", panel.scene, key=f"scene_{sid}_{panel.number}")
            panel.caption = st.text_input("Narration", panel.caption, key=f"cap_{sid}_{panel.number}")
            panel.dialogue = st.text_input("Dialogue", panel.dialogue, key=f"dlg_{sid}_{panel.number}")

    if st.button("🎨 2. Draw the comic", type="primary"):
        try:
            client, settings = get_client()
            bar = st.progress(0.0, text="Starting...")

            def on_progress(done: int, total: int, message: str) -> None:
                bar.progress(min(done / total, 1.0), text=message)

            st.session_state["images"] = generate_all_panels(
                client, settings.image_model, story, on_progress
            )
            bar.empty()
        except Exception as exc:  # noqa: BLE001
            st.error(f"Could not draw the comic: {exc}")

images = st.session_state.get("images")

if story and images:
    arts = [
        PanelArt(bytes_to_image(data), panel.caption, panel.dialogue)
        for data, panel in zip(images, story.panels)
    ]
    failed = sum(1 for data in images if data is None)
    if failed:
        st.warning(f"{failed} panel(s) could not be drawn. Press 'Draw the comic' to try again.")

    pages = compose_pages(arts, story.title)
    st.subheader("Your comic")
    for number, page in enumerate(pages, start=1):
        st.image(page, use_container_width=True)
        st.download_button(
            f"⬇️ Download page {number} (PNG)",
            data=image_to_png_bytes(page),
            file_name=f"comic_page_{number}.png",
            mime="image/png",
            key=f"png_{number}",
        )
    st.download_button(
        "⬇️ Download full comic (PDF)",
        data=pages_to_pdf_bytes(pages),
        file_name="comic_craft.pdf",
        mime="application/pdf",
    )

st.divider()
st.caption("Images are AI-generated. Review the content before sharing.")
