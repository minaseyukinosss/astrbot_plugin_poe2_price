import unittest

from models import CurrencyPrice, TradeListing
from services.market_router import MarketRouter


class MarketRouterTest(unittest.IsolatedAsyncioTestCase):
    async def test_plain_exchange_item_uses_ninja_before_trade(self):
        router = MarketRouter(
            trade_client=_FakeTradeClient(),
            ninja_client=_FakeNinjaClient(
                CurrencyPrice(
                    name="Aldur's Legacy",
                    amount=333,
                    currency="神聖石",
                    league="Runes of Aldur",
                    source="poe.ninja",
                )
            ),
            default_league="Runes of Aldur",
        )

        result = await router.price_text("阿德爾的傳承", translated_text="Aldur's Legacy")

        self.assertEqual(result.source, "poe.ninja")
        self.assertIn("Aldur's Legacy", result.item_name)
        self.assertEqual(result.median, 333)
        self.assertEqual(router.ninja_client.keywords, ["Aldur's Legacy"])
        self.assertEqual(router.trade_client.search_count, 0)

    async def test_trade_ladder_tries_next_query_when_first_query_has_no_results(self):
        router = MarketRouter(
            trade_client=_FakeTradeClient(empty_first=True),
            ninja_client=_FakeNinjaClient(None),
            default_league="Runes of Aldur",
        )
        item_text = """物品種類: 鞋子
稀有度: 稀有
風暴 行靴
絲綢便鞋
--------
物品等級: 72
--------
+24 最大生命
+20% 移動速度
"""

        result = await router.price_text(item_text)

        self.assertEqual(result.source, "trade2")
        self.assertEqual(result.relaxation_level, 1)
        self.assertEqual(router.trade_client.search_count, 2)


class _FakeNinjaClient:
    def __init__(self, result):
        self.result = result
        self.keywords = []

    async def search_currency(self, league, keyword):
        self.keywords.append(keyword)
        return self.result


class _FakeTradeClient:
    base_url = "https://www.pathofexile.com"

    def __init__(self, empty_first=False):
        self.empty_first = empty_first
        self.search_count = 0

    async def search(self, league, query):
        self.search_count += 1
        if self.empty_first and self.search_count == 1:
            return {"id": "empty", "result": []}
        return {"id": f"query-{self.search_count}", "result": ["a", "b", "c", "d", "e"]}

    async def fetch_listings(self, result_ids, query_id, *, limit=20):
        return [
            TradeListing(amount=10, currency="exalted"),
            TradeListing(amount=11, currency="exalted"),
            TradeListing(amount=12, currency="exalted"),
            TradeListing(amount=13, currency="exalted"),
            TradeListing(amount=14, currency="exalted"),
        ]


if __name__ == "__main__":
    unittest.main()
