import unittest

from services.trade_client import build_trade_search_url


class TradeClientTest(unittest.TestCase):
    def test_builds_official_trade2_search_url_with_encoded_league(self):
        url = build_trade_search_url("Runes of Aldur", "abc123")

        self.assertEqual(
            url,
            "https://www.pathofexile.com/trade2/search/poe2/Runes%20of%20Aldur/abc123",
        )


if __name__ == "__main__":
    unittest.main()
