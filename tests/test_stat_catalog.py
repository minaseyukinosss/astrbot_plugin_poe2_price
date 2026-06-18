import unittest

from services.stat_catalog import StatCatalog


class StatCatalogTest(unittest.TestCase):
    def test_resolves_common_traditional_chinese_mod_aliases(self):
        catalog = StatCatalog()

        self.assertEqual(catalog.resolve_stat_id("+24 最大生命"), "explicit.stat_3299347043")
        self.assertEqual(catalog.resolve_stat_id("+31% 火焰抗性"), "explicit.stat_4220027924")
        self.assertEqual(catalog.resolve_stat_id("+20% 移動速度"), "explicit.stat_3845215720")

    def test_loads_trade_stats_entries_and_normalizes_numbers(self):
        catalog = StatCatalog()
        catalog.load_from_trade_stats(
            {
                "result": [
                    {
                        "entries": [
                            {"id": "explicit.test_life", "text": "+# 最大生命"},
                        ]
                    }
                ]
            }
        )

        self.assertEqual(catalog.resolve_stat_id("+55 最大生命"), "explicit.test_life")


if __name__ == "__main__":
    unittest.main()
