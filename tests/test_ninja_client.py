import unittest

from services.ninja_client import NinjaClient


class FakeNinjaClient(NinjaClient):
    def __init__(self, payload):
        self.payload = payload
        self.requests = []

    async def _get_json(self, path, params=None):
        self.requests.append((path, params))
        return self.payload


class NinjaClientTest(unittest.IsolatedAsyncioTestCase):
    async def test_search_currency_uses_chinese_alias_and_core_rates(self):
        client = FakeNinjaClient(
            {
                "core": {
                    "items": [
                        {"id": "divine", "name": "Divine Orb", "image": "divine.png"},
                        {"id": "exalted", "name": "Exalted Orb", "image": "exalted.png"},
                    ],
                    "rates": {"exalted": 1},
                    "primary": "divine",
                    "secondary": "exalted",
                },
                "lines": [
                    {
                        "id": "divine",
                        "primaryValue": 120,
                        "volumePrimaryValue": 42,
                        "sparkline": {"totalChange": 5.5, "data": []},
                    }
                ],
            }
        )

        price = await client.search_currency("Runes of Aldur", "神圣石")

        self.assertIsNotNone(price)
        self.assertEqual(price.name, "Divine Orb")
        self.assertEqual(price.amount, 120)
        self.assertEqual(price.currency, "崇高石")
        self.assertEqual(price.volume, 42)
        self.assertEqual(price.change_percent, 5.5)
        self.assertEqual(client.requests[0][1]["type"], "Currency")

    async def test_search_currency_returns_none_when_item_is_absent(self):
        client = FakeNinjaClient({"core": {"items": [], "rates": {}}, "lines": []})

        price = await client.search_currency("Runes of Aldur", "神圣石")

        self.assertIsNone(price)

    async def test_search_currency_converts_primary_value_to_exalted_currency(self):
        client = FakeNinjaClient(
            {
                "core": {
                    "items": [{"id": "divine", "name": "Divine Orb"}],
                    "rates": {"chaos": 2.45, "exalted": 0.5},
                    "primary": "divine",
                    "secondary": "chaos",
                },
                "lines": [{"id": "divine", "primaryValue": 1, "volumePrimaryValue": 10, "sparkline": {}}],
            }
        )

        price = await client.search_currency("Standard", "神圣石")

        self.assertEqual(price.amount, 0.5)
        self.assertEqual(price.currency, "崇高石")


if __name__ == "__main__":
    unittest.main()
