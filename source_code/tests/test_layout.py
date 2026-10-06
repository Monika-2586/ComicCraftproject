"""Offline tests for the layout stage (needs only Pillow, no API key)."""

import unittest

from PIL import Image, ImageDraw

from comiccraft.layout import (
    PanelArt,
    compose_pages,
    image_to_png_bytes,
    pages_to_pdf_bytes,
    placeholder_image,
    render_panel,
    wrap_text,
    load_font,
)


def _sample_image(colour=(80, 140, 220)):
    return Image.new("RGB", (900, 700), colour)


class LayoutTests(unittest.TestCase):
    def test_wrap_text_respects_width(self):
        img = Image.new("RGB", (10, 10))
        draw = ImageDraw.Draw(img)
        font = load_font(20)
        lines = wrap_text(draw, "one two three four five six seven eight nine ten", font, 150)
        self.assertGreater(len(lines), 1)
        for line in lines:
            self.assertLessEqual(draw.textlength(line, font=font), 150 + 1)

    def test_wrap_text_empty(self):
        img = Image.new("RGB", (10, 10))
        self.assertEqual(wrap_text(ImageDraw.Draw(img), "   ", load_font(20), 100), [])

    def test_render_panel_is_square(self):
        art = PanelArt(_sample_image(), caption="Meanwhile in the city...", dialogue="Hero: We must hurry!")
        tile = render_panel(art, size=400)
        self.assertEqual(tile.size, (400, 400))

    def test_missing_image_uses_placeholder(self):
        tile = render_panel(PanelArt(None, caption="No picture"), size=300)
        self.assertEqual(tile.size, (300, 300))
        self.assertEqual(placeholder_image(200).size, (200, 200))

    def test_compose_pages_paginates(self):
        panels = [PanelArt(_sample_image(), caption=f"Panel {i}") for i in range(5)]
        pages = compose_pages(panels, "My Comic", columns=2, rows_per_page=2, panel_size=300)
        self.assertEqual(len(pages), 2)  # 4 panels + 1 panel
        self.assertGreater(pages[0].height, pages[1].height)  # first page has title header

    def test_compose_requires_panels(self):
        with self.assertRaises(ValueError):
            compose_pages([], "Empty")

    def test_exports(self):
        pages = compose_pages([PanelArt(_sample_image())] * 2, "T", panel_size=300)
        self.assertTrue(image_to_png_bytes(pages[0]).startswith(b"\x89PNG"))
        self.assertTrue(pages_to_pdf_bytes(pages).startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
