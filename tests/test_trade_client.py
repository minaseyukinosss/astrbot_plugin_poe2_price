import unittest

import httpx

from services.http_client import RateLimiter
from services.trade_client import build_trade_search_url
from services.trade_client import TradeClient


class FakeAsyncClient:
    def __init__(self):
        self.calls = 0

    async def request(self, method, url, **kwargs):
        self.calls += 1
        return httpx.Response(200, json={"ok": True})


class TradeClientTest(unittest.TestCase):
    def test_builds_official_trade2_search_url_with_encoded_league(self):
        url = build_trade_search_url("Runes of Aldur", "abc123")

        self.assertEqual(
            url,
            "https://www.pathofexile.com/trade2/search/poe2/Runes%20of%20Aldur/abc123",
        )


class TradeClientAsyncTest(unittest.IsolatedAsyncioTestCase):
    async def test_request_waits_for_active_rate_limiter(self):
        waits = []
        limiter = RateLimiter(max_requests=1, window_seconds=60, sleep=waits.append, clock=lambda: 100.0)
        client = TradeClient(user_agent="test", rate_limiter=limiter)
        fake_http = FakeAsyncClient()
        client._client = fake_http

        await client._request_json("GET", "/first")
        await client._request_json("GET", "/second")

        self.assertEqual(fake_http.calls, 2)
        self.assertEqual(len(waits), 1)


if __name__ == "__main__":
    unittest.main()
