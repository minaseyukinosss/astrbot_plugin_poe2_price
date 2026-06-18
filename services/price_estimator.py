from __future__ import annotations

from statistics import median

try:
    from ..models import PriceEstimate, TradeListing
except ImportError:  # pragma: no cover - 兼容本地单元测试的顶层导入。
    from models import PriceEstimate, TradeListing


def estimate_price(
    item_name: str,
    league: str,
    listings: list[TradeListing],
    *,
    min_valid_listings: int = 5,
    source: str = "trade2",
    trade_url: str = "",
) -> PriceEstimate:
    """根据挂售记录估算价格。"""

    supported = [listing for listing in listings if listing.amount > 0 and listing.currency == "exalted"]
    filtered = _drop_low_outliers(supported)
    amounts = sorted(listing.amount for listing in filtered)

    warnings: list[str] = []
    if len(amounts) < min_valid_listings:
        warnings.append("样本不足")

    if not amounts:
        return PriceEstimate(
            item_name=item_name,
            league=league,
            median=None,
            low=None,
            high=None,
            currency="exalted",
            confidence="低",
            valid_count=0,
            total_count=len(listings),
            source=source,
            trade_url=trade_url,
            warnings=["没有有效挂售"],
        )

    mid = _clean_number(median(amounts))
    low = _clean_number(_percentile_nearest(amounts, 0.25))
    high = _clean_number(_percentile_nearest(amounts, 0.75))
    confidence = _confidence(amounts, min_valid_listings)

    if warnings:
        confidence = "低"

    return PriceEstimate(
        item_name=item_name,
        league=league,
        median=mid,
        low=low,
        high=high,
        currency="exalted",
        confidence=confidence,
        valid_count=len(amounts),
        total_count=len(listings),
        source=source,
        trade_url=trade_url,
        warnings=warnings,
        reference_listings=filtered[:5],
    )


def _drop_low_outliers(listings: list[TradeListing]) -> list[TradeListing]:
    if len(listings) < 5:
        return listings
    amounts = sorted(listing.amount for listing in listings)
    med = median(amounts)
    floor = med * 0.35
    return [listing for listing in listings if listing.amount >= floor]


def _percentile_nearest(values: list[float], percentile: float) -> float:
    index = round((len(values) - 1) * percentile)
    return values[index]


def _confidence(amounts: list[float], min_valid_listings: int) -> str:
    if len(amounts) < min_valid_listings:
        return "低"
    med = median(amounts)
    if not med:
        return "低"
    spread = (max(amounts) - min(amounts)) / med
    if len(amounts) >= min_valid_listings and spread <= 0.75:
        return "高"
    if spread <= 1.5:
        return "中"
    return "低"


def _clean_number(value: float) -> int | float:
    if float(value).is_integer():
        return int(value)
    return round(value, 2)
