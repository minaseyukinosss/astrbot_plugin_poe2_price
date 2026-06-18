from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ItemModifier:
    """物品词缀。"""

    text: str
    kind: str = "explicit"
    values: list[float] = field(default_factory=list)
    stat_id: str | None = None
    enabled: bool = True


@dataclass(slots=True)
class ParsedItem:
    """从游戏复制文本中解析出的物品。"""

    raw_text: str
    item_class: str = ""
    rarity: str = "normal"
    name: str = ""
    base_type: str = ""
    item_level: int | None = None
    limit: int | None = None
    quality: int | None = None
    required_level: int | None = None
    required_str: int | None = None
    required_dex: int | None = None
    required_int: int | None = None
    armour: int | None = None
    evasion: int | None = None
    energy_shield: int | None = None
    block: int | None = None
    spirit: int | None = None
    corrupted: bool = False
    implicit_mods: list[ItemModifier] = field(default_factory=list)
    explicit_mods: list[ItemModifier] = field(default_factory=list)
    crafted_mods: list[ItemModifier] = field(default_factory=list)
    flavour_lines: list[str] = field(default_factory=list)
    trade_name: str = ""
    trade_base_type: str = ""
    translation_warnings: list[str] = field(default_factory=list)

    @property
    def display_name(self) -> str:
        if self.name and self.base_type:
            return f"{self.name} ({self.base_type})"
        return self.name or self.base_type


@dataclass(slots=True)
class TradeListing:
    """trade2 返回的单条挂售。"""

    amount: float
    currency: str
    account: str = ""
    character: str = ""
    online: bool = True
    indexed: str = ""
    whisper: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CurrencyPrice:
    """通货价格。"""

    name: str
    amount: float
    currency: str
    league: str
    source: str
    volume: float = 0
    change_percent: float | None = None
    icon_url: str = ""
    details_id: str = ""


@dataclass(slots=True)
class PriceEstimate:
    """估价结果。"""

    item_name: str
    league: str
    median: float | None
    low: float | None
    high: float | None
    currency: str
    confidence: str
    valid_count: int
    total_count: int
    source: str
    trade_url: str = ""
    warnings: list[str] = field(default_factory=list)
    reference_listings: list[TradeListing] = field(default_factory=list)
    relaxation_level: int = 0


@dataclass(slots=True)
class LookupContext:
    """一次查价请求的上下文。"""

    league: str
    realm: str = "poe2"
    max_fetch_results: int = 20
    min_valid_listings: int = 5


@dataclass(slots=True)
class RateLimitState:
    """远端限流状态。"""

    blocked_until: float = 0.0
    retry_after_seconds: int | None = None
