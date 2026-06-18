from __future__ import annotations


BASE_TYPE_ALIASES_ZH_TW = {
    "鑽石": "Diamond",
}

UNIQUE_NAME_ALIASES_ZH_TW = {
    "水井之心": "Heart of the Well",
    "阿德爾的傳承": "Aldur's Legacy",
}


def translate_base_type(text: str) -> str | None:
    """将繁中底材名翻译为官方 trade2 英文底材名。"""

    return BASE_TYPE_ALIASES_ZH_TW.get(text.strip())


def translate_unique_name(text: str) -> str | None:
    """将繁中传奇名翻译为官方 trade2 英文传奇名。"""

    return UNIQUE_NAME_ALIASES_ZH_TW.get(text.strip())
