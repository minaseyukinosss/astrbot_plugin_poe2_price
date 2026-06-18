import unittest

from models import ItemModifier, ParsedItem
from services.query_relaxer import build_trade_query_ladder


class QueryRelaxerTest(unittest.TestCase):
    def test_builds_relaxation_ladder_from_strict_to_broad(self):
        item = ParsedItem(
            raw_text="",
            rarity="rare",
            item_class="鞋子",
            name="風暴 行靴",
            base_type="絲綢便鞋",
            trade_base_type="Silk Slippers",
            item_level=72,
            quality=20,
            energy_shield=64,
            explicit_mods=[
                ItemModifier(text="+24 最大生命", stat_id="explicit.stat_3299347043", values=[24]),
                ItemModifier(text="+20% 移動速度", stat_id="explicit.stat_3845215720", values=[20]),
            ],
        )

        ladder = build_trade_query_ladder(item)

        self.assertGreaterEqual(len(ladder), 3)
        self.assertEqual([step.level for step in ladder], list(range(len(ladder))))
        self.assertEqual(ladder[0].reason, "精确查询")
        self.assertEqual(len(ladder[0].query["query"]["stats"][0]["filters"]), 2)
        self.assertEqual(ladder[1].reason, "核心词缀查询")
        self.assertEqual(len(ladder[1].query["query"]["stats"][0]["filters"]), 1)
        self.assertEqual(ladder[-1].reason, "基底宽松查询")
        self.assertNotIn("stats", ladder[-1].query["query"])

    def test_unique_item_keeps_single_precise_query(self):
        item = ParsedItem(
            raw_text="",
            rarity="unique",
            name="水井之心",
            base_type="鑽石",
            trade_name="Heart of the Well",
            trade_base_type="Diamond",
        )

        ladder = build_trade_query_ladder(item)

        self.assertEqual(len(ladder), 1)
        self.assertEqual(ladder[0].query["query"]["name"], "Heart of the Well")


if __name__ == "__main__":
    unittest.main()
