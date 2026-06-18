import unittest

from models import ItemModifier, ParsedItem
from services.query_builder import build_item_query, build_name_query


class QueryBuilderTest(unittest.TestCase):
    def test_unique_item_query_uses_traditional_chinese_name_and_base_type(self):
        item = ParsedItem(
            raw_text="",
            item_class="珠寶",
            rarity="unique",
            name="水井之心",
            base_type="鑽石",
            item_level=81,
        )

        query = build_item_query(item)

        self.assertNotIn("name", query["query"])
        self.assertEqual(query["query"]["type"], "Diamond")
        self.assertNotIn("term", query["query"])
        self.assertNotIn("stats", query["query"])
        self.assertEqual(query["query"]["status"]["option"], "online")
        self.assertEqual(query["query"]["filters"]["trade_filters"]["filters"]["sale_type"]["option"], "priced")
        self.assertEqual(query["sort"], {"price": "asc"})

    def test_rare_item_query_adds_rarity_quality_ilvl_and_stat_filters(self):
        item = ParsedItem(
            raw_text="",
            item_class="鞋子",
            rarity="rare",
            name="風暴 行靴",
            base_type="絲綢便鞋",
            item_level=72,
            quality=20,
            energy_shield=64,
            explicit_mods=[
                ItemModifier(text="+24 最大生命", stat_id="explicit.stat_3299347043", values=[24]),
                ItemModifier(text="+20% 移動速度", stat_id="explicit.stat_3845215720", values=[20]),
            ],
        )

        query = build_item_query(item)

        self.assertNotIn("type", query["query"])
        self.assertEqual(query["query"]["term"], "風暴 行靴 絲綢便鞋")
        self.assertEqual(
            query["query"]["filters"]["type_filters"]["filters"]["rarity"]["option"],
            "rare",
        )
        self.assertEqual(query["query"]["filters"]["type_filters"]["filters"]["ilvl"]["min"], 62)
        self.assertEqual(query["query"]["filters"]["type_filters"]["filters"]["quality"]["min"], 15)
        self.assertEqual(query["query"]["filters"]["equipment_filters"]["filters"]["es"]["min"], 44)
        stat_filters = query["query"]["stats"][0]["filters"]
        self.assertEqual([entry["id"] for entry in stat_filters], ["explicit.stat_3299347043", "explicit.stat_3845215720"])
        self.assertEqual(stat_filters[0]["value"]["min"], 19)
        self.assertEqual(stat_filters[1]["value"]["min"], 16)

    def test_name_query_uses_free_text_term_without_empty_stats(self):
        query = build_name_query("水井之心")

        self.assertEqual(query["query"]["term"], "水井之心")
        self.assertNotIn("name", query["query"])
        self.assertNotIn("stats", query["query"])

    def test_name_query_uses_free_text_term_for_english_keywords(self):
        query = build_name_query("Divine Orb")

        self.assertEqual(query["query"]["term"], "Divine Orb")
        self.assertNotIn("name", query["query"])
        self.assertNotIn("stats", query["query"])


if __name__ == "__main__":
    unittest.main()
