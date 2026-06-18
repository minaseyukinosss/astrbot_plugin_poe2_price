from __future__ import annotations

from models import ParsedItem


def build_item_query(item: ParsedItem) -> dict:
    """根据解析物品构建 trade2 查询。"""

    query: dict = {
        "query": {
            "status": {"option": "online"},
            "stats": [{"type": "and", "filters": []}],
            "filters": {
                "trade_filters": {"filters": {"sale_type": {"option": "priced"}}},
            },
        },
        "sort": {"price": "asc"},
    }

    if item.rarity == "unique" and item.name:
        query["query"]["name"] = item.name

    if item.base_type:
        query["query"]["type"] = item.base_type

    filters = query["query"]["filters"]
    type_filters = {"filters": {}}

    if item.rarity:
        type_filters["filters"]["rarity"] = {"option": item.rarity}
    if item.item_level and item.item_level > 1:
        type_filters["filters"]["ilvl"] = {"min": max(1, item.item_level - 10)}
    if item.quality and item.quality > 0:
        type_filters["filters"]["quality"] = {"min": max(0, item.quality - 5)}
    if type_filters["filters"]:
        filters["type_filters"] = type_filters

    equipment_filters = {"filters": {}}
    if item.energy_shield and item.energy_shield > 0:
        equipment_filters["filters"]["es"] = {"min": int(item.energy_shield * 0.7)}
    if item.armour and item.armour > 0:
        equipment_filters["filters"]["ar"] = {"min": int(item.armour * 0.7)}
    if item.evasion and item.evasion > 0:
        equipment_filters["filters"]["ev"] = {"min": int(item.evasion * 0.7)}
    if equipment_filters["filters"]:
        filters["equipment_filters"] = equipment_filters

    stat_filters = []
    for modifier in item.explicit_mods + item.implicit_mods + item.crafted_mods:
        if not modifier.enabled or not modifier.stat_id:
            continue
        stat_filter: dict = {"id": modifier.stat_id}
        if modifier.values:
            stat_filter["value"] = {"min": _relaxed_min(modifier.values[0])}
        stat_filters.append(stat_filter)

    query["query"]["stats"][0]["filters"] = stat_filters
    return query


def build_name_query(name: str) -> dict:
    """根据物品名构建基础查询。"""

    return {
        "query": {
            "status": {"option": "online"},
            "term": name,
            "filters": {
                "trade_filters": {"filters": {"sale_type": {"option": "priced"}}},
            },
            "stats": [{"type": "and", "filters": []}],
        },
        "sort": {"price": "asc"},
    }


def _relaxed_min(value: float) -> int | float:
    return int(value * 0.8)
