from __future__ import annotations

import time
from typing import Any
from urllib.parse import quote

import httpx

from models import RateLimitState, TradeListing


class TradeApiError(Exception):
    """trade2 请求失败。"""

    def __init__(self, message: str, status_code: int | None = None, retry_after: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = retry_after


class TradeClient:
    """Path of Exile trade2 异步客户端。"""

    def __init__(self, *, user_agent: str, timeout: float = 15.0, base_url: str = "https://www.pathofexile.com") -> None:
        self.base_url = base_url.rstrip("/")
        self.rate_limit = RateLimitState()
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "User-Agent": user_agent,
                "Accept": "application/json",
            },
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def fetch_leagues(self) -> list[dict[str, Any]]:
        data = await self._request_json("GET", "/api/trade2/data/leagues")
        return data.get("result", [])

    async def fetch_stats(self) -> dict[str, Any]:
        return await self._request_json("GET", "/api/trade2/data/stats")

    async def search(self, league: str, query: dict[str, Any]) -> dict[str, Any]:
        encoded_league = quote(league, safe="")
        return await self._request_json("POST", f"/api/trade2/search/poe2/{encoded_league}", json=query)

    async def fetch_listings(self, result_ids: list[str], query_id: str, *, limit: int = 20) -> list[TradeListing]:
        listings: list[TradeListing] = []
        selected = result_ids[:limit]
        for start in range(0, len(selected), 10):
            batch = selected[start : start + 10]
            if not batch:
                continue
            ids = ",".join(batch)
            data = await self._request_json("GET", f"/api/trade2/fetch/{ids}", params={"query": query_id})
            listings.extend(_parse_listing(entry) for entry in data.get("result", []) if entry)
        return [listing for listing in listings if listing is not None]

    async def _request_json(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        now = time.time()
        if self.rate_limit.blocked_until > now:
            retry_after = max(1, int(self.rate_limit.blocked_until - now))
            raise TradeApiError(f"trade2 正在限流，请 {retry_after} 秒后重试", 429, retry_after)

        response = await self._client.request(method, f"{self.base_url}{path}", **kwargs)
        self._update_rate_limit(response)

        if response.status_code == 429:
            retry_after = _parse_retry_after(response)
            self.rate_limit.retry_after_seconds = retry_after
            self.rate_limit.blocked_until = time.time() + retry_after
            raise TradeApiError(f"trade2 请求被限流，请 {retry_after} 秒后重试", 429, retry_after)
        if response.status_code == 403:
            self.rate_limit.blocked_until = time.time() + 60
            raise TradeApiError("trade2 当前拒绝访问，已临时停止重试", 403)
        if response.status_code >= 400:
            raise TradeApiError(f"trade2 请求失败：HTTP {response.status_code}", response.status_code)

        return response.json()

    def _update_rate_limit(self, response: httpx.Response) -> None:
        retry_after = response.headers.get("Retry-After")
        if retry_after and response.status_code == 429:
            seconds = _safe_int(retry_after, 10)
            self.rate_limit.retry_after_seconds = seconds
            self.rate_limit.blocked_until = time.time() + seconds


def build_trade_search_url(league: str, query_id: str, *, base_url: str = "https://www.pathofexile.com") -> str:
    """构造官方 trade2 搜索结果页链接。"""

    encoded_league = quote(league, safe="")
    return f"{base_url.rstrip('/')}/trade2/search/poe2/{encoded_league}/{query_id}"


def _parse_listing(entry: dict[str, Any]) -> TradeListing | None:
    listing = entry.get("listing", {})
    price = listing.get("price") or {}
    amount = price.get("amount")
    currency = price.get("currency")
    if amount is None or not currency:
        return None

    account = listing.get("account") or {}
    online = account.get("online")
    return TradeListing(
        amount=float(amount),
        currency=str(currency),
        account=account.get("name", ""),
        character=account.get("lastCharacterName", ""),
        online=bool(online),
        indexed=listing.get("indexed", ""),
        whisper=listing.get("whisper", ""),
        raw=entry,
    )


def _parse_retry_after(response: httpx.Response) -> int:
    return _safe_int(response.headers.get("Retry-After"), 10)


def _safe_int(value: str | None, default: int) -> int:
    try:
        return int(value or default)
    except ValueError:
        return default
