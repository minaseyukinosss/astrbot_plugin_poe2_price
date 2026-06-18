from __future__ import annotations

import time
from typing import Any

import httpx


class Poe2ScoutClient:
    """POE2 Scout 辅助数据客户端。"""

    def __init__(self, *, timeout: float = 15.0, cache_ttl: int = 1800, base_url: str = "https://poe2scout.com/api") -> None:
        self.base_url = base_url.rstrip("/")
        self.cache_ttl = cache_ttl
        self._client = httpx.AsyncClient(timeout=timeout, headers={"Accept": "application/json"})
        self._cache: dict[str, tuple[float, Any]] = {}

    async def close(self) -> None:
        await self._client.aclose()

    async def get_realms(self) -> list[dict[str, Any]]:
        return await self._get_cached("/Realms")

    async def get_leagues(self, realm: str = "poe2") -> list[dict[str, Any]]:
        return await self._get_cached(f"/{realm}/Leagues")

    async def search_currency(self, league: str, keyword: str, realm: str = "poe2") -> dict[str, Any] | None:
        categories = ["currency", "essence", "rune", "fragment"]
        lowered = keyword.lower()
        for category in categories:
            data = await self._get_cached(
                f"/{realm}/Leagues/{league}/Currencies/ByCategory",
                params={"Category": category, "Search": keyword, "PerPage": 25},
            )
            for item in data.get("Items", []):
                text = str(item.get("Text", "")).lower()
                api_id = str(item.get("ApiId", "")).lower()
                if lowered in text or lowered in api_id:
                    return item
        return None

    async def _get_cached(self, path: str, params: dict[str, Any] | None = None) -> Any:
        key = f"{path}?{sorted((params or {}).items())}"
        cached = self._cache.get(key)
        now = time.time()
        if cached and now - cached[0] < self.cache_ttl:
            return cached[1]

        response = await self._client.get(f"{self.base_url}{path}", params=params)
        response.raise_for_status()
        data = response.json()
        self._cache[key] = (now, data)
        return data
