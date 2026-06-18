from __future__ import annotations

FIELD_ALIASES = {
    "物品種類": "item_class",
    "Item Class": "item_class",
    "稀有度": "rarity",
    "Rarity": "rarity",
    "物品等級": "item_level",
    "Item Level": "item_level",
    "僅限": "limit",
    "Limited to": "limit",
    "品質": "quality",
    "Quality": "quality",
    "需求": "requirements",
    "Requirements": "requirements",
    "等級": "required_level",
    "Level": "required_level",
    "力量": "required_str",
    "敏捷": "required_dex",
    "智慧": "required_int",
    "Str": "required_str",
    "Dex": "required_dex",
    "Int": "required_int",
    "護甲": "armour",
    "Armour": "armour",
    "閃避值": "evasion",
    "Evasion Rating": "evasion",
    "能量護盾": "energy_shield",
    "Energy Shield": "energy_shield",
    "格擋": "block",
    "Block": "block",
    "精神": "spirit",
    "Spirit": "spirit",
}

RARITY_ALIASES = {
    "普通": "normal",
    "normal": "normal",
    "魔法": "magic",
    "magic": "magic",
    "稀有": "rare",
    "rare": "rare",
    "傳奇": "unique",
    "传奇": "unique",
    "unique": "unique",
    "通貨": "currency",
    "通货": "currency",
    "currency": "currency",
    "寶石": "gem",
    "宝石": "gem",
    "gem": "gem",
}

SECTION_SEPARATOR = "--------"
MOD_TAG_PREFIXES = ("{ 前綴", "{ 後綴", "{ Prefix", "{ Suffix")
DESECRATED_MARKERS = {"褻瀆前綴", "褻瀆後綴", "Desecrated Prefix", "Desecrated Suffix"}
IGNORED_LINE_PREFIXES = (
    "放置到",
    "右鍵點擊",
    "右键点击",
    "Place into",
    "Right click",
)


def split_sections(text: str) -> list[list[str]]:
    """按 POE2 物品分隔线切分文本。"""

    sections: list[list[str]] = []
    current: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line == SECTION_SEPARATOR:
            if current:
                sections.append(current)
                current = []
            continue
        current.append(line)
    if current:
        sections.append(current)
    return sections


def parse_key_value(line: str) -> tuple[str, str] | None:
    """解析 `键: 值` 行，并返回内部字段名。"""

    if ":" not in line:
        return None
    key, value = line.split(":", 1)
    field = FIELD_ALIASES.get(key.strip())
    if not field:
        return None
    return field, value.strip()


def normalize_rarity(value: str) -> str:
    """将繁中或英文稀有度归一为内部枚举。"""

    return RARITY_ALIASES.get(value.strip().lower(), RARITY_ALIASES.get(value.strip(), "normal"))


def should_ignore_line(line: str) -> bool:
    """判断一行是否不应参与物品属性或词缀解析。"""

    if line.startswith(MOD_TAG_PREFIXES):
        return True
    if line in DESECRATED_MARKERS:
        return True
    return any(line.startswith(prefix) for prefix in IGNORED_LINE_PREFIXES)

