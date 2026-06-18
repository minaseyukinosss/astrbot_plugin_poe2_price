import unittest

from services.http_client import HttpRequestError, RateLimiter


class HttpClientTest(unittest.IsolatedAsyncioTestCase):
    async def test_rate_limiter_waits_when_window_is_full(self):
        sleeps = []
        limiter = RateLimiter(max_requests=2, window_seconds=10, sleep=sleeps.append, clock=lambda: 100.0)

        await limiter.wait()
        await limiter.wait()
        await limiter.wait()

        self.assertEqual(len(sleeps), 1)
        self.assertGreaterEqual(sleeps[0], 10)

    def test_http_request_error_contains_status_and_body_preview(self):
        error = HttpRequestError("poe.ninja", 502, "bad gateway body that is useful")

        self.assertEqual(error.status_code, 502)
        self.assertIn("poe.ninja", str(error))
        self.assertIn("bad gateway body", str(error))


if __name__ == "__main__":
    unittest.main()
