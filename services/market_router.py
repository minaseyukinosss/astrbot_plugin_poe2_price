from __future__ import annotations

from typing import Any

try:
    from ..models import CurrencyPrice, PriceEstimate
except ImportError:  # pragma: no cover - 兼容本地单元测试的顶层导入。
    from models import CurrencyPrice, PriceEstimate

try:
    from .item_parser import parse_item_text
    from .market_classifier import MarketRoute, classify_item, classify_text
    from .price_estimator import estimate_price
    from .query_builder import build_name_query
    from .query_relaxer import build_trade_query_ladder
    from .trade_client import build_trade_search_url
except ImportError:  # pragma: no cover - 兼容本地单元测试的顶层导入。
    from services.item_parser import parse_item_text
    from services.market_classifier import MarketRoute, classify_item, classify_text
    from services.price_estimator import estimate_price
    from services.query_builder import build_name_query
    from services.query_relaxer import build_trade_query_ladder
    from services.trade_client import build_trade_search_url


class MarketRouter:
    """统一市场查价路由。"""

    def __init__(
        self,
        *,
        trade_client: Any,
        ninja_client: Any,
        default_league: str,
        max_fetch_results: int = 20,
        min_valid_listings: int = 5,
    ) -> None:
        self.trade_client = trade_client
        self.ninja_client = ninja_client
        self.default_league = default_league
        self.max_fetch_results = max_fetch_results
        self.min_valid_listings = min_valid_listings

    async def price_text(self, text: str, *, translated_text: str | None = None, item=None) -> PriceEstimate:
        """根据文本或已解析物品选择数据源并返回估价。"""

        parsed_item = item or parse_item_text(text)
        if parsed_item:
            route = classify_item(parsed_item)
            if route == MarketRoute.EXCHANGE:
                return await self._price_exchange(parsed_item.display_name, parsed_item.display_name)
            return await self._price_trade_item(parsed_item)

        query_text = translated_text or text.strip()
        if classify_text(text) == MarketRoute.EXCHANGE:
            return await self._price_exchange(text.strip(), query_text)
        return await self._price_trade_name(text.strip(), query_text)

    async def _price_exchange(self, display_name: str, keyword: str) -> PriceEstimate:
        price = await self.ninja_client.search_currency(self.default_league, keyword)
        if price:
            return _estimate_from_currency_price(display_name, price)
        return await self._price_trade_name(display_name, keyword)

    async def _price_trade_name(self, display_name: str, keyword: str) -> PriceEstimate:
        query = build_name_query(keyword)
        search_result = await self.trade_client.search(self.default_league, query)
        return await self._estimate_from_search(display_name, search_result, relaxation_level=0)

    async def _price_trade_item(self, item) -> PriceEstimate:
        last_empty_query_id = ""
        for step in build_trade_query_ladder(item):
            search_result = await self.trade_client.search(self.default_league, step.query)
            result_ids = search_result.get("result", [])
            if not result_ids:
                last_empty_query_id = str(search_result.get("id") or "")
                continue
            estimate = await self._estimate_from_search(item.display_name, search_result, relaxation_level=step.level)
            if step.level > 0:
                estimate.warnings.append(f"已使用{step.reason}")
            return estimate
        return PriceEstimate(
            item_name=item.display_name,
            league=self.default_league,
            median=None,
            low=None,
            high=None,
            currency="exalted",
            confidence="低",
            valid_count=0,
            total_count=0,
            source="trade2",
            trade_url=_trade_url(self.trade_client, self.default_league, last_empty_query_id),
            warnings=["没有找到可比挂售"],
        )

    async def _estimate_from_search(self, display_name: str, search_result: dict, *, relaxation_level: int) -> PriceEstimate:
        result_ids = search_result.get("result", [])
        query_id = str(search_result.get("id") or "")
        if not query_id or not result_ids:
            return PriceEstimate(
                item_name=display_name,
                league=self.default_league,
                median=None,
                low=None,
                high=None,
                currency="exalted",
                confidence="低",
                valid_count=0,
                total_count=0,
                source="trade2",
                trade_url=_trade_url(self.trade_client, self.default_league, query_id),
                warnings=["没有找到可比挂售"],
            )

        listings = await self.trade_client.fetch_listings(result_ids, query_id, limit=self.max_fetch_results)
        estimate = estimate_price(
            display_name,
            self.default_league,
            listings,
            min_valid_listings=self.min_valid_listings,
            trade_url=_trade_url(self.trade_client, self.default_league, query_id),
        )
        estimate.relaxation_level = relaxation_level
        return estimate


def _estimate_from_currency_price(display_name: str, price: CurrencyPrice) -> PriceEstimate:
    return PriceEstimate(
        item_name=f"{display_name} ({price.name})" if display_name != price.name else price.name,
        league=price.league,
        median=price.amount,
        low=price.amount,
        high=price.amount,
        currency=price.currency,
        confidence="中",
        valid_count=1,
        total_count=1,
        source=price.source,
        warnings=[],
    )


def _trade_url(trade_client: Any, league: str, query_id: str) -> str:
    if not query_id:
        return ""
    return build_trade_search_url(league, query_id, base_url=getattr(trade_client, "base_url", "https://www.pathofexile.com"))
