from __future__ import annotations

from enum import StrEnum

try:
    from ..models import ParsedItem
except ImportError:  # pragma: no cover - 兼容本地单元测试的顶层导入。
    from models import ParsedItem

try:
    from .currency_aliases import normalize_currency_keyword
except ImportError:  # pragma: no cover - 兼容本地单元测试的顶层导入。
    from services.currency_aliases import normalize_currency_keyword


class MarketRoute(StrEnum):
    """市场查价路由。"""

    EXCHANGE = "exchange"
    UNIQUE_ITEM = "unique_item"
    RARE_ITEM = "rare_item"
    TRADE_SEARCH = "trade_search"


EXCHANGE_TEXT_ALIASES_ZH_TW = {
    "阿德爾的傳承",
}


def classify_text(text: str) -> MarketRoute:
    """根据直接输入文本判断优先数据源。"""

    keyword = text.strip()
    if not keyword:
        return MarketRoute.TRADE_SEARCH
    if normalize_currency_keyword(keyword) != keyword:
        return MarketRoute.EXCHANGE
    if keyword in EXCHANGE_TEXT_ALIASES_ZH_TW:
        return MarketRoute.EXCHANGE
    return MarketRoute.TRADE_SEARCH


def classify_item(item: ParsedItem) -> MarketRoute:
    """根据完整物品文本判断优先数据源。"""

    if item.rarity == "unique":
        return MarketRoute.UNIQUE_ITEM
    if item.rarity == "rare":
        return MarketRoute.RARE_ITEM
    if item.item_class in {"通貨", "可堆疊通貨", "碑牌", "靈魂核心"}:
        return MarketRoute.EXCHANGE
    return MarketRoute.TRADE_SEARCH
