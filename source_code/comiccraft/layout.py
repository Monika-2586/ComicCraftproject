"""Stage 3 - assemble panels, captions and speech bubbles into comic pages.

Text is drawn with Pillow instead of asking the image model to render it,
because AI-generated lettering is often garbled. This module only needs
Pillow, so it can be tested without any API key.
"""

from __future__ import annotations

import io
import math
from dataclasses import dataclass

from PIL import Image, ImageDraw, ImageFont, ImageOps

PANEL_SIZE = 640
GUTTER = 24
HEADER_HEIGHT = 120
BACKGROUND = (250, 246, 236)
INK = (20, 20, 20)
CAPTION_FILL = (255, 224, 130)
BUBBLE_FILL = (255, 255, 255)

_FONT_CANDIDATES = {
    False: [
        "DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "Arial.ttf",
        "/Library/Fonts/Arial.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ],
    True: [
        "DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "Arial Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ],
}


@dataclass
class PanelArt:
    """Everything needed to render one finished panel."""

    image: Image.Image | None
    caption: str = ""
    dialogue: str = ""


def load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    """Load a TrueType font, falling back to Pillow's built-in font."""
    for name in _FONT_CANDIDATES[bold]:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def wrap_text(
    draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int
) -> list[str]:
    """Greedy word wrap so every line fits inside ``max_width`` pixels."""
    words = text.split()
    if not words:
        return []
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        trial = f"{current} {word}"
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def placeholder_image(size: int = PANEL_SIZE, message: str = "Image unavailable") -> Image.Image:
    """Grey tile used when a panel could not be generated."""
    img = Image.new("RGB", (size, size), (225, 225, 225))
    draw = ImageDraw.Draw(img)
    font = load_font(size // 16, bold=True)
    width = draw.textlength(message, font=font)
    draw.text(((size - width) / 2, size / 2 - size // 32), message, fill=(110, 110, 110), font=font)
    return img


def _draw_text_box(
    canvas: Image.Image,
    text: str,
    *,
    top: int,
    left: int,
    max_width: int,
    fill: tuple[int, int, int],
    font: ImageFont.ImageFont,
    rounded: bool,
) -> None:
    """Draw a filled, outlined box containing wrapped text at (left, top)."""
    draw = ImageDraw.Draw(canvas)
    padding = 12
    lines = wrap_text(draw, text, font, max_width - 2 * padding)
    if not lines:
        return
    line_height = int(font.size * 1.3) if hasattr(font, "size") else 20
    box_width = max(int(draw.textlength(line, font=font)) for line in lines) + 2 * padding
    box_height = line_height * len(lines) + 2 * padding
    box = (left, top, left + box_width, top + box_height)
    if rounded:
        draw.rounded_rectangle(box, radius=18, fill=fill, outline=INK, width=3)
    else:
        draw.rectangle(box, fill=fill, outline=INK, width=3)
    y = top + padding
    for line in lines:
        draw.text((left + padding, y), line, fill=INK, font=font)
        y += line_height


def render_panel(art: PanelArt, size: int = PANEL_SIZE) -> Image.Image:
    """Render one panel: cropped image, narration box (top), speech bubble (bottom)."""
    image = art.image if art.image is not None else placeholder_image(size)
    tile = ImageOps.fit(image.convert("RGB"), (size, size), method=Image.LANCZOS)

    margin = 16
    font = load_font(max(16, size // 24))

    if art.caption.strip():
        _draw_text_box(
            tile,
            art.caption.strip(),
            top=margin,
            left=margin,
            max_width=int(size * 0.8),
            fill=CAPTION_FILL,
            font=font,
            rounded=False,
        )

    if art.dialogue.strip():
        draw = ImageDraw.Draw(tile)
        padding = 12
        lines = wrap_text(draw, art.dialogue.strip(), font, int(size * 0.7) - 2 * padding)
        line_height = int(font.size * 1.3)
        bubble_height = line_height * len(lines) + 2 * padding
        _draw_text_box(
            tile,
            art.dialogue.strip(),
            top=size - bubble_height - margin,
            left=margin,
            max_width=int(size * 0.7),
            fill=BUBBLE_FILL,
            font=font,
            rounded=True,
        )

    draw = ImageDraw.Draw(tile)
    draw.rectangle((0, 0, size - 1, size - 1), outline=INK, width=5)
    return tile


def compose_pages(
    panels: list[PanelArt],
    title: str,
    columns: int = 2,
    rows_per_page: int = 2,
    panel_size: int = PANEL_SIZE,
) -> list[Image.Image]:
    """Arrange panels into one or more comic pages (first page carries the title)."""
    if not panels:
        raise ValueError("No panels to lay out.")

    per_page = columns * rows_per_page
    page_count = math.ceil(len(panels) / per_page)
    page_width = columns * panel_size + (columns + 1) * GUTTER
    title_font = load_font(52, bold=True)

    pages: list[Image.Image] = []
    for page_index in range(page_count):
        chunk = panels[page_index * per_page : (page_index + 1) * per_page]
        rows = math.ceil(len(chunk) / columns)
        header = HEADER_HEIGHT if page_index == 0 else GUTTER
        page_height = header + rows * (panel_size + GUTTER)
        page = Image.new("RGB", (page_width, page_height), BACKGROUND)
        draw = ImageDraw.Draw(page)

        if page_index == 0:
            title_text = title.strip() or "Untitled Comic"
            width = draw.textlength(title_text, font=title_font)
            # Shrink very long titles so they stay inside the page
            while width > page_width - 2 * GUTTER and title_font.size > 20:
                title_font = load_font(title_font.size - 4, bold=True)
                width = draw.textlength(title_text, font=title_font)
            draw.text(((page_width - width) / 2, 30), title_text, fill=INK, font=title_font)

        for index, art in enumerate(chunk):
            row, col = divmod(index, columns)
            x = GUTTER + col * (panel_size + GUTTER)
            y = header + row * (panel_size + GUTTER)
            page.paste(render_panel(art, panel_size), (x, y))
        pages.append(page)
    return pages


def image_to_png_bytes(image: Image.Image) -> bytes:
    """Encode a PIL image as PNG bytes (for download buttons)."""
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def pages_to_pdf_bytes(pages: list[Image.Image]) -> bytes:
    """Combine comic pages into a single multi-page PDF."""
    if not pages:
        raise ValueError("No pages to export.")
    buffer = io.BytesIO()
    rgb_pages = [page.convert("RGB") for page in pages]
    rgb_pages[0].save(
        buffer, format="PDF", save_all=True, append_images=rgb_pages[1:], resolution=120.0
    )
    return buffer.getvalue()


def bytes_to_image(data: bytes | None) -> Image.Image | None:
    """Decode image bytes returned by Gemini; None stays None."""
    if not data:
        return None
    return Image.open(io.BytesIO(data)).convert("RGB")
