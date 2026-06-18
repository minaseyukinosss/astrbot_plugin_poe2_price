import unittest

from services.item_parser import parse_item_text


WELL_HEART_SAMPLE = """物品種類: 珠寶
稀有度: 傳奇
水井之心
鑽石
--------
僅限: 1
--------
物品等級: 81
--------
{ 前綴 "" }
褻瀆前綴
{ 前綴 "" }
褻瀆前綴
{ 後綴 "" }
褻瀆後綴
{ 後綴 "" }
褻瀆後綴
--------
無數靈魂在痛苦中齊聲哀嚎，
永遠沉沒在新亡者的重壓之下。
--------
放置到一個天賦樹的珠寶插槽中以產生效果。右鍵點擊以移出插槽。"""


RARE_BOOTS_SAMPLE = """物品種類: 鞋子
稀有度: 稀有
風暴 行靴
絲綢便鞋
--------
品質: +20%
能量護盾: 64
--------
需求:
等級: 55
智慧: 95
--------
物品等級: 72
--------
+24 最大生命
+31% 火焰抗性
+28% 冰冷抗性
+20% 移動速度
--------
已汙染"""


class ItemParserTest(unittest.TestCase):
    def test_parses_traditional_chinese_unique_jewel_sample(self):
        item = parse_item_text(WELL_HEART_SAMPLE)

        self.assertIsNotNone(item)
        self.assertEqual(item.item_class, "珠寶")
        self.assertEqual(item.rarity, "unique")
        self.assertEqual(item.name, "水井之心")
        self.assertEqual(item.base_type, "鑽石")
        self.assertEqual(item.item_level, 81)
        self.assertEqual(item.limit, 1)
        self.assertEqual(item.explicit_mods, [])
        self.assertNotIn("放置到", " ".join(item.flavour_lines))

    def test_parses_traditional_chinese_rare_boots_mods_and_properties(self):
        item = parse_item_text(RARE_BOOTS_SAMPLE)

        self.assertIsNotNone(item)
        self.assertEqual(item.item_class, "鞋子")
        self.assertEqual(item.rarity, "rare")
        self.assertEqual(item.name, "風暴 行靴")
        self.assertEqual(item.base_type, "絲綢便鞋")
        self.assertEqual(item.quality, 20)
        self.assertEqual(item.energy_shield, 64)
        self.assertEqual(item.required_level, 55)
        self.assertEqual(item.required_int, 95)
        self.assertEqual(item.item_level, 72)
        self.assertTrue(item.corrupted)
        self.assertEqual(
            [mod.text for mod in item.explicit_mods],
            ["+24 最大生命", "+31% 火焰抗性", "+28% 冰冷抗性", "+20% 移動速度"],
        )

    def test_returns_none_for_plain_name_query(self):
        self.assertIsNone(parse_item_text("水井之心"))


if __name__ == "__main__":
    unittest.main()
