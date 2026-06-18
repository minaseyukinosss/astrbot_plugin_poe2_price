import unittest

from models import ItemModifier, ParsedItem
from services.query_builder import build_item_query


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

        self.assertEqual(query["query"]["name"], "水井之心")
        self.assertEqual(query["query"]["type"], "鑽石")
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

        self.assertEqual(query["query"]["type"], "絲綢便鞋")
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


if __name__ == "__main__":
    unittest.main()
