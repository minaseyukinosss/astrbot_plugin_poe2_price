from __future__ import annotations

from typing import Any

try:
    from ..models import CurrencyPrice
except ImportError:  # pragma: no cover - 兼容本地单元测试的顶层导入。
    from models import CurrencyPrice

try:
    from .currency_aliases import iter_currency_search_terms
    from .http_client import HttpJsonClient, RateLimiter
except ImportError:  # pragma: no cover - 兼容本地单元测试的顶层导入。
    from services.currency_aliases import iter_currency_search_terms
    from services.http_client import HttpJsonClient, RateLimiter


class NinjaClient:
    """poe.ninja POE2 经济数据客户端。"""

    def __init__(
        self,
        *,
        timeout: float = 15.0,
        base_url: str = "https://poe.ninja",
        user_agent: str = "astrbot-plugin-poe2-price/0.1.0",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._http = HttpJsonClient(
            source="poe.ninja",
            base_url=self.base_url,
            user_agent=user_agent,
            timeout=timeout,
            limiter=RateLimiter(max_requests=10, window_seconds=300),
        )

    async def close(self) -> None:
        await self._http.close()

    async def search_currency(self, league: str, keyword: str) -> CurrencyPrice | None:
        search_terms = [term.lower() for term in iter_currency_search_terms(keyword)]
        data = await self._get_json(
            "/poe2/api/economy/exchange/current/overview",
            params={"league": league, "type": "Currency"},
        )

        core = data.get("core") or {}
        item_by_id = {str(item.get("id", "")).lower(): item for item in core.get("items", [])}
        item_by_name = {str(item.get("name", "")).lower(): item for item in core.get("items", [])}

        matched_item = None
        for term in search_terms:
            matched_item = item_by_name.get(term) or item_by_id.get(term)
            if matched_item:
                break
            matched_item = next(
                (
                    item
                    for item in core.get("items", [])
                    if term in str(item.get("name", "")).lower() or term in str(item.get("id", "")).lower()
                ),
                None,
            )
            if matched_item:
                break

        if not matched_item:
            return None

        item_id = str(matched_item.get("id", "")).lower()
        line = next((entry for entry in data.get("lines", []) if str(entry.get("id", "")).lower() == item_id), None)
        if not line:
            return None

        secondary = str(core.get("secondary") or "exalted")
        secondary_rate = float((core.get("rates") or {}).get(secondary, 1) or 1)
        amount = float(line.get("primaryValue") or 0) * secondary_rate
        return CurrencyPrice(
            name=str(matched_item.get("name") or matched_item.get("id") or keyword),
            amount=_clean_number(amount),
            currency=secondary,
            league=league,
            source="poe.ninja",
            volume=float(line.get("volumePrimaryValue") or 0),
            change_percent=_extract_change_percent(line),
            icon_url=str(matched_item.get("image") or ""),
            details_id=str(matched_item.get("detailsId") or matched_item.get("id") or ""),
        )

    async def _get_json(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self._http.get(path, params=params)


def _extract_change_percent(line: dict[str, Any]) -> float | None:
    sparkline = line.get("sparkline") or {}
    value = sparkline.get("totalChange")
    if value is None:
        return None
    return float(value)


def _clean_number(value: float) -> int | float:
    if float(value).is_integer():
        return int(value)
    return round(value, 4)
