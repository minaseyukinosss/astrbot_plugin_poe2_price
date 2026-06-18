from __future__ import annotations

import re

try:
    from ..models import ItemModifier, ParsedItem
except ImportError:  # pragma: no cover - 兼容本地单元测试的顶层导入。
    from models import ItemModifier, ParsedItem

try:
    from .item_text_normalizer import (
        normalize_rarity,
        parse_key_value,
        should_ignore_line,
        split_sections,
    )
except ImportError:  # pragma: no cover - 兼容本地单元测试的顶层导入。
    from services.item_text_normalizer import (
        normalize_rarity,
        parse_key_value,
        should_ignore_line,
        split_sections,
    )


def parse_item_text(text: str) -> ParsedItem | None:
    """解析 POE2 复制出的物品文本。"""

    sections = split_sections(text)
    if not sections:
        return None

    header_fields = [parse_key_value(line) for line in sections[0]]
    if not any(field and field[0] == "rarity" for field in header_fields):
        return None

    item = ParsedItem(raw_text=text)
    _parse_header(sections[0], item)

    for section in sections[1:]:
        _parse_section(section, item)

    return item


def _parse_header(lines: list[str], item: ParsedItem) -> None:
    names: list[str] = []
    for line in lines:
        parsed = parse_key_value(line)
        if parsed:
            field, value = parsed
            if field == "item_class":
                item.item_class = value
            elif field == "rarity":
                item.rarity = normalize_rarity(value)
            continue
        if ":" not in line and not should_ignore_line(line):
            names.append(line)

    if item.rarity in {"rare", "unique"}:
        item.name = names[0] if names else ""
        item.base_type = names[1] if len(names) > 1 else ""
    elif names:
        item.base_type = names[0]


def _parse_section(lines: list[str], item: ParsedItem) -> None:
    if not lines:
        return

    if lines[0] in {"需求:", "Requirements:"}:
        for line in lines[1:]:
            _parse_property_line(line, item)
        return

    parsed_any_property = False
    mod_lines: list[str] = []

    for line in lines:
        if should_ignore_line(line):
            continue
        if _parse_property_line(line, item):
            parsed_any_property = True
            continue
        if line in {"已汙染", "已污染", "Corrupted"}:
            item.corrupted = True
            parsed_any_property = True
            continue
        if _looks_like_flavour_or_help(line):
            item.flavour_lines.append(line)
            continue
        mod_lines.append(line)

    if parsed_any_property and not mod_lines:
        return

    for line in mod_lines:
        if _looks_like_modifier(line):
            item.explicit_mods.append(ItemModifier(text=line, values=_extract_numbers(line)))
        else:
            item.flavour_lines.append(line)


def _parse_property_line(line: str, item: ParsedItem) -> bool:
    parsed = parse_key_value(line)
    if not parsed:
        return False

    field, value = parsed
    number = _extract_first_int(value)
    if number is None:
        return field == "requirements"

    if field == "item_level":
        item.item_level = number
    elif field == "limit":
        item.limit = number
    elif field == "quality":
        item.quality = number
    elif field == "required_level":
        item.required_level = number
    elif field == "required_str":
        item.required_str = number
    elif field == "required_dex":
        item.required_dex = number
    elif field == "required_int":
        item.required_int = number
    elif field == "armour":
        item.armour = number
    elif field == "evasion":
        item.evasion = number
    elif field == "energy_shield":
        item.energy_shield = number
    elif field == "block":
        item.block = number
    elif field == "spirit":
        item.spirit = number
    else:
        return False
    return True


def _extract_first_int(text: str) -> int | None:
    match = re.search(r"[+-]?\d+", text)
    if not match:
        return None
    return abs(int(match.group(0)))


def _extract_numbers(text: str) -> list[float]:
    return [float(match) for match in re.findall(r"[+-]?\d+(?:\.\d+)?", text)]


def _looks_like_modifier(line: str) -> bool:
    return bool(
        re.search(r"[+-]?\d", line)
        or "%" in line
        or any(keyword in line for keyword in ("增加", "最大", "抗性", "速度", "傷害", "暴擊", "生命"))
    )


def _looks_like_flavour_or_help(line: str) -> bool:
    return line.endswith("。") or line.endswith("，") or line.startswith('"')
