from __future__ import annotations

_CURRENCY_ALIASES = {
    "神圣石": "Divine Orb",
    "神聖石": "Divine Orb",
    "divine石": "Divine Orb",
    "神圣": "Divine Orb",
    "神聖": "Divine Orb",
    "崇高石": "Exalted Orb",
    "混沌石": "Chaos Orb",
    "磨刀石": "Blacksmith's Whetstone",
    "遗忘石": "Orb of Annulment",
    "遺忘石": "Orb of Annulment",
}


def normalize_currency_keyword(keyword: str) -> str:
    """将常见中英文通货别名归一为官方搜索关键词。"""

    text = keyword.strip()
    if not text:
        return text

    normalized = _compact(text)
    return _CURRENCY_ALIASES.get(normalized, text)


def iter_currency_search_terms(keyword: str) -> list[str]:
    """生成通货搜索时的候选关键词。"""

    normalized = normalize_currency_keyword(keyword)
    candidates: list[str] = []
    for value in (normalized, keyword.strip()):
        if value and value not in candidates:
            candidates.append(value)
    return candidates


def _compact(text: str) -> str:
    return "".join(ch for ch in text.strip().lower() if not ch.isspace())
