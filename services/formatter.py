from __future__ import annotations

from models import PriceEstimate


def format_price_estimate(estimate: PriceEstimate) -> str:
    """格式化中文估价结果。"""

    lines = [
        f"物品：{estimate.item_name}",
        f"联盟：{estimate.league}",
    ]

    if estimate.median is None or estimate.low is None or estimate.high is None:
        lines.append("估价：暂无有效样本")
    else:
        lines.append(f"估价：{estimate.low} - {estimate.high} {estimate.currency}")
        lines.append(f"中位数：{estimate.median} {estimate.currency}")

    lines.extend(
        [
            f"置信度：{estimate.confidence}",
            f"有效样本：{estimate.valid_count}/{estimate.total_count}",
            f"数据源：{estimate.source}",
        ]
    )
    if estimate.trade_url:
        lines.append(f"官方链接：{estimate.trade_url}")

    if "样本不足" in estimate.warnings:
        lines.append("警告：样本不足，仅供参考")
    else:
        for warning in estimate.warnings:
            lines.append(f"警告：{warning}")

    if estimate.reference_listings:
        lines.append("参考挂售：")
        for index, listing in enumerate(estimate.reference_listings[:3], start=1):
            seller = f" @{listing.account}" if listing.account else ""
            lines.append(f"{index}. {listing.amount:g} {listing.currency}{seller}")

    return "\n".join(lines)
