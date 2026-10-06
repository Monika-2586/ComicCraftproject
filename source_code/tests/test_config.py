import os
import unittest
from unittest import mock

from comiccraft.config import DEFAULT_IMAGE_MODEL, DEFAULT_TEXT_MODEL, load_settings


class ConfigTests(unittest.TestCase):
    def test_missing_key_raises(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                load_settings()

    def test_defaults_and_overrides(self):
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "abc"}, clear=True):
            s = load_settings()
            self.assertEqual(s.api_key, "abc")
            self.assertEqual(s.text_model, DEFAULT_TEXT_MODEL)
            self.assertEqual(s.image_model, DEFAULT_IMAGE_MODEL)
            s2 = load_settings(api_key="k", text_model="t", image_model="i")
            self.assertEqual((s2.api_key, s2.text_model, s2.image_model), ("k", "t", "i"))


if __name__ == "__main__":
    unittest.main()
