from __future__ import annotations

from dataclasses import dataclass

try:
    from ..models import ParsedItem
except ImportError:  # pragma: no cover - 兼容本地单元测试的顶层导入。
    from models import ParsedItem

try:
    from .query_builder import build_item_query
except ImportError:  # pragma: no cover - 兼容本地单元测试的顶层导入。
    from services.query_builder import build_item_query


@dataclass(slots=True)
class TradeQueryStep:
    """一次 trade2 查询尝试。"""

    level: int
    reason: str
    query: dict


def build_trade_query_ladder(item: ParsedItem) -> list[TradeQueryStep]:
    """为物品构建从严格到宽松的 trade2 查询阶梯。"""

    if item.rarity != "rare":
        return [TradeQueryStep(level=0, reason="精确查询", query=build_item_query(item))]

    steps = [TradeQueryStep(level=0, reason="精确查询", query=build_item_query(item))]

    core_item = _clone_for_query(item)
    core_item.explicit_mods = _core_modifiers(core_item.explicit_mods, max_count=1)
    core_item.implicit_mods = []
    core_item.crafted_mods = []
    if len(core_item.explicit_mods) < len(item.explicit_mods):
        steps.append(TradeQueryStep(level=len(steps), reason="核心词缀查询", query=build_item_query(core_item)))

    broad_item = _clone_for_query(item)
    broad_item.explicit_mods = []
    broad_item.implicit_mods = []
    broad_item.crafted_mods = []
    steps.append(TradeQueryStep(level=len(steps), reason="基底宽松查询", query=build_item_query(broad_item)))

    return steps


def _clone_for_query(item: ParsedItem) -> ParsedItem:
    clone = ParsedItem(
        raw_text=item.raw_text,
        item_class=item.item_class,
        rarity=item.rarity,
        name=item.name,
        base_type=item.base_type,
        item_level=item.item_level,
        limit=item.limit,
        quality=item.quality,
        required_level=item.required_level,
        required_str=item.required_str,
        required_dex=item.required_dex,
        required_int=item.required_int,
        armour=item.armour,
        evasion=item.evasion,
        energy_shield=item.energy_shield,
        block=item.block,
        spirit=item.spirit,
        corrupted=item.corrupted,
        implicit_mods=list(item.implicit_mods),
        explicit_mods=list(item.explicit_mods),
        crafted_mods=list(item.crafted_mods),
        flavour_lines=list(item.flavour_lines),
        trade_name=item.trade_name,
        trade_base_type=item.trade_base_type,
        translation_warnings=list(item.translation_warnings),
    )
    return clone


def _core_modifiers(modifiers: list, *, max_count: int = 2) -> list:
    scored = sorted(modifiers, key=_modifier_score, reverse=True)
    return scored[: max(1, min(max_count, len(scored)))]


def _modifier_score(modifier) -> tuple[int, float]:
    text = getattr(modifier, "text", "")
    value = max(getattr(modifier, "values", []) or [0])
    priority = 0
    for keyword in ("移動速度", "最大生命", "能量護盾", "抗性", "傷害", "暴擊", "技能"):
        if keyword in text:
            priority += 1
    return priority, value
