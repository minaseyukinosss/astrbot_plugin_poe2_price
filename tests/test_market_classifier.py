import unittest

from models import ParsedItem
from services.market_classifier import MarketRoute, classify_item, classify_text


class MarketClassifierTest(unittest.TestCase):
    def test_currency_text_routes_to_exchange_source(self):
        self.assertEqual(classify_text("神聖石"), MarketRoute.EXCHANGE)
        self.assertEqual(classify_text("崇高石"), MarketRoute.EXCHANGE)

    def test_seasonal_exchange_text_routes_to_exchange_source(self):
        self.assertEqual(classify_text("阿德爾的傳承"), MarketRoute.EXCHANGE)

    def test_unique_item_routes_to_unique_then_trade(self):
        item = ParsedItem(raw_text="", rarity="unique", name="水井之心", base_type="鑽石")

        self.assertEqual(classify_item(item), MarketRoute.UNIQUE_ITEM)

    def test_rare_item_routes_to_trade_ladder(self):
        item = ParsedItem(raw_text="", rarity="rare", item_class="鞋子", name="風暴 行靴", base_type="絲綢便鞋")

        self.assertEqual(classify_item(item), MarketRoute.RARE_ITEM)


if __name__ == "__main__":
    unittest.main()
