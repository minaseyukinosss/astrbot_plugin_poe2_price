import unittest

from services.poe2scout_client import Poe2ScoutClient, normalize_currency_keyword


class FakePoe2ScoutClient(Poe2ScoutClient):
    def __init__(self):
        self.requests = []

    async def _get_cached(self, path, params=None):
        self.requests.append((path, params))
        return {
            "Items": [
                {
                    "Text": "Divine Orb",
                    "ApiId": "divine",
                    "CurrentPrice": 100,
                }
            ]
        }


class Poe2ScoutClientTest(unittest.IsolatedAsyncioTestCase):
    async def test_search_currency_accepts_simplified_chinese_alias(self):
        client = FakePoe2ScoutClient()

        item = await client.search_currency("Runes of Aldur", "神圣石")

        self.assertIsNotNone(item)
        self.assertEqual(item["Text"], "Divine Orb")
        self.assertEqual(client.requests[0][1]["Search"], "Divine Orb")

    async def test_search_currency_accepts_traditional_chinese_alias(self):
        client = FakePoe2ScoutClient()

        item = await client.search_currency("Runes of Aldur", "神聖石")

        self.assertIsNotNone(item)
        self.assertEqual(item["ApiId"], "divine")

    def test_normalize_currency_keyword_returns_known_english_name(self):
        self.assertEqual(normalize_currency_keyword("崇高石"), "Exalted Orb")


if __name__ == "__main__":
    unittest.main()
