import tempfile
import unittest
from pathlib import Path

from models import ParsedItem
from services.translation_cache import TranslationCache
from services.translation_resolver import TranslationResolver


class TranslationResolverTest(unittest.IsolatedAsyncioTestCase):
    async def test_applies_cached_base_type_to_parsed_item(self):
        cache = TranslationCache()
        cache.set("base_type", "絲綢便鞋", "Silk Slippers")
        resolver = TranslationResolver(cache=cache, poe2db_client=_MissingPoe2DbClient())
        item = ParsedItem(raw_text="", rarity="rare", name="風暴 行靴", base_type="絲綢便鞋")

        await resolver.apply_to_item(item)

        self.assertEqual(item.trade_base_type, "Silk Slippers")
        self.assertEqual(item.trade_name, "")
        self.assertEqual(item.translation_warnings, [])

    async def test_uses_item_class_to_limit_base_type_lookup_pages(self):
        cache = TranslationCache(seed_aliases=False)
        poe2db_client = _RecordingPoe2DbClient()
        resolver = TranslationResolver(cache=cache, poe2db_client=poe2db_client)
        item = ParsedItem(raw_text="", item_class="鞋子", rarity="rare", name="風暴 行靴", base_type="絲綢便鞋")

        await resolver.apply_to_item(item)

        self.assertEqual(item.trade_base_type, "Silk Slippers")
        self.assertEqual(poe2db_client.received_index_paths, ("/tw/Boots",))

    async def test_resolves_plain_chinese_name_query_to_trade2_english_term(self):
        cache = TranslationCache(seed_aliases=False)
        resolver = TranslationResolver(cache=cache, poe2db_client=_KnownPlainNamePoe2DbClient())

        translated, warnings = await resolver.resolve_search_text("阿德爾的傳承")

        self.assertEqual(translated, "Aldur's Legacy")
        self.assertEqual(warnings, [])
        self.assertEqual(cache.get("unique_name", "阿德爾的傳承"), "Aldur's Legacy")

    async def test_applies_poe2db_unique_translation_and_saves_to_cache(self):
        cache = TranslationCache(seed_aliases=False)
        resolver = TranslationResolver(cache=cache, poe2db_client=_KnownPoe2DbClient())
        item = ParsedItem(raw_text="", rarity="unique", name="測試傳奇", base_type="鑽石")

        await resolver.apply_to_item(item)

        self.assertEqual(item.trade_name, "The Test Unique")
        self.assertEqual(item.trade_base_type, "Diamond")
        self.assertEqual(cache.get("unique_name", "測試傳奇"), "The Test Unique")
        self.assertEqual(cache.get("base_type", "鑽石"), "Diamond")

    async def test_unique_detail_base_type_is_used_when_base_lookup_misses(self):
        cache = TranslationCache(seed_aliases=False)
        resolver = TranslationResolver(cache=cache, poe2db_client=_KnownUniqueOnlyPoe2DbClient())
        item = ParsedItem(raw_text="", rarity="unique", name="測試傳奇", base_type="未知底材")

        await resolver.apply_to_item(item)

        self.assertEqual(item.trade_name, "The Test Unique")
        self.assertEqual(item.trade_base_type, "Diamond")
        self.assertEqual(cache.get("base_type", "未知底材"), "Diamond")

    async def test_unresolved_chinese_item_keeps_trade_fields_empty_and_adds_warning(self):
        cache = TranslationCache(seed_aliases=False)
        resolver = TranslationResolver(cache=cache, poe2db_client=_MissingPoe2DbClient())
        item = ParsedItem(raw_text="", rarity="rare", name="風暴 行靴", base_type="未知底材")

        await resolver.apply_to_item(item)

        self.assertEqual(item.trade_base_type, "")
        self.assertIn("未能将繁中底材「未知底材」翻译为 trade2 英文底材", item.translation_warnings)

    async def test_poe2db_failure_adds_warning_without_raising(self):
        cache = TranslationCache(seed_aliases=False)
        resolver = TranslationResolver(cache=cache, poe2db_client=_FailingPoe2DbClient())
        item = ParsedItem(raw_text="", rarity="rare", name="風暴 行靴", base_type="未知底材")

        await resolver.apply_to_item(item)

        self.assertEqual(item.trade_base_type, "")
        self.assertIn("编年史翻译查询失败，已退回宽松查询", item.translation_warnings)

    async def test_save_writes_updated_cache_to_disk(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "translations.json"
            cache = TranslationCache.load(path, seed_aliases=False)
            resolver = TranslationResolver(cache=cache, poe2db_client=_KnownPoe2DbClient(), cache_path=path)
            item = ParsedItem(raw_text="", rarity="unique", name="測試傳奇", base_type="鑽石")

            await resolver.apply_to_item(item)
            resolver.save()

            reloaded = TranslationCache.load(path, seed_aliases=False)

        self.assertEqual(reloaded.get("unique_name", "測試傳奇"), "The Test Unique")


class _KnownPoe2DbClient:
    async def find_unique_translation(self, name: str):
        from services.poe2db_client import ItemTranslation

        if name == "測試傳奇":
            return ItemTranslation(name="The Test Unique", base_type="Diamond", source_path="/tw/The_Test_Unique")
        return None

    async def find_base_type_translation(self, base_type: str, *, index_paths=None):
        if base_type == "鑽石":
            return "Diamond"
        return None


class _KnownUniqueOnlyPoe2DbClient:
    async def find_unique_translation(self, name: str):
        from services.poe2db_client import ItemTranslation

        if name == "測試傳奇":
            return ItemTranslation(name="The Test Unique", base_type="Diamond", source_path="/tw/The_Test_Unique")
        return None

    async def find_base_type_translation(self, base_type: str, *, index_paths=None):
        return None


class _MissingPoe2DbClient:
    async def find_unique_translation(self, name: str):
        return None

    async def find_base_type_translation(self, base_type: str, *, index_paths=None):
        return None


class _FailingPoe2DbClient:
    async def find_unique_translation(self, name: str):
        raise RuntimeError("poe2db unavailable")

    async def find_base_type_translation(self, base_type: str, *, index_paths=None):
        raise RuntimeError("poe2db unavailable")


class _RecordingPoe2DbClient:
    def __init__(self) -> None:
        self.received_index_paths = None

    async def find_unique_translation(self, name: str):
        return None

    async def find_base_type_translation(self, base_type: str, *, index_paths=None):
        self.received_index_paths = index_paths
        return "Silk Slippers"


class _KnownPlainNamePoe2DbClient:
    async def find_unique_translation(self, name: str):
        from services.poe2db_client import ItemTranslation

        if name == "阿德爾的傳承":
            return ItemTranslation(name="Aldur's Legacy", source_path="/tw/Aldurs_Legacy")
        return None

    async def find_base_type_translation(self, base_type: str, *, index_paths=None):
        return None


if __name__ == "__main__":
    unittest.main()
