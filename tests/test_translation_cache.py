import tempfile
import unittest
from pathlib import Path

from services.translation_cache import TranslationCache


class TranslationCacheTest(unittest.TestCase):
    def test_seed_aliases_are_available_without_cache_file(self):
        cache = TranslationCache.load(Path("/tmp/not-exists-poe2-price-cache.json"))

        self.assertEqual(cache.get("base_type", "鑽石"), "Diamond")
        self.assertEqual(cache.get("unique_name", "水井之心"), "Heart of the Well")

    def test_set_save_and_load_translation_entry(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "translations.json"
            cache = TranslationCache.load(path)
            cache.set("unique_name", "水井之心", "The Wellspring")
            cache.save(path)

            reloaded = TranslationCache.load(path)

        self.assertEqual(reloaded.get("unique_name", "水井之心"), "The Wellspring")


if __name__ == "__main__":
    unittest.main()
