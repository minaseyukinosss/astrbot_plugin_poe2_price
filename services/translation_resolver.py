from __future__ import annotations

from pathlib import Path

try:
    from ..models import ParsedItem
except ImportError:  # pragma: no cover - 兼容本地单元测试的顶层导入。
    from models import ParsedItem

try:
    from .item_translation import translate_base_type, translate_unique_name
    from .poe2db_client import DEFAULT_BASE_INDEX_PATHS, Poe2DbClient
    from .translation_cache import TranslationCache
except ImportError:  # pragma: no cover - 兼容本地单元测试的顶层导入。
    from services.item_translation import translate_base_type, translate_unique_name
    from services.poe2db_client import DEFAULT_BASE_INDEX_PATHS, Poe2DbClient
    from services.translation_cache import TranslationCache


BASE_INDEX_PATHS_BY_ITEM_CLASS_ZH_TW = {
    "單手錘": ("/tw/One_Hand_Mace",),
    "雙手錘": ("/tw/Two_Hand_Mace",),
    "細杖": ("/tw/Wand",),
    "法杖": ("/tw/Staff",),
    "權杖": ("/tw/Sceptre",),
    "長杖": ("/tw/Quarterstaff",),
    "弓": ("/tw/Bow",),
    "十字弓": ("/tw/Crossbow",),
    "箭袋": ("/tw/Quiver",),
    "盾": ("/tw/Shield", "/tw/Buckler"),
    "盾牌": ("/tw/Shield", "/tw/Buckler"),
    "法器": ("/tw/Focus",),
    "頭盔": ("/tw/Helmet",),
    "身體護甲": ("/tw/Body_Armour",),
    "胸甲": ("/tw/Body_Armour",),
    "手套": ("/tw/Gloves",),
    "鞋子": ("/tw/Boots",),
    "腰帶": ("/tw/Belt",),
    "項鍊": ("/tw/Amulet",),
    "護身符": ("/tw/Amulet",),
    "戒指": ("/tw/Ring",),
    "珠寶": ("/tw/Jewel",),
    "藥劑": ("/tw/Flask",),
    "聖物": ("/tw/Relic",),
}


class TranslationResolver:
    """把游戏繁中物品文本解析为 trade2 可识别的英文字段。"""

    def __init__(
        self,
        *,
        cache: TranslationCache,
        poe2db_client: Poe2DbClient,
        cache_path: Path | None = None,
    ) -> None:
        self.cache = cache
        self.poe2db_client = poe2db_client
        self.cache_path = cache_path
        self.dirty = False

    async def apply_to_item(self, item: ParsedItem) -> None:
        """原地填充 ParsedItem 的 trade2 英文字段。"""

        item.translation_warnings.clear()
        item.trade_name = ""
        item.trade_base_type = ""

        if item.rarity == "unique" and item.name:
            try:
                item.trade_name, detail_base_type = await self._resolve_unique_translation(item.name)
                if detail_base_type and item.base_type:
                    item.trade_base_type = detail_base_type
                    self.cache.set("base_type", item.base_type, detail_base_type, source="poe2db-detail")
                    self.dirty = True
            except Exception:
                _append_once(item.translation_warnings, "编年史翻译查询失败，已退回宽松查询")
            if not item.trade_name and _uses_cjk_text(item.name):
                item.translation_warnings.append(f"未能将繁中传奇名「{item.name}」翻译为 trade2 英文名")

        if item.base_type and not item.trade_base_type:
            try:
                item.trade_base_type = await self._resolve_base_type(item.base_type, item.item_class)
            except Exception:
                _append_once(item.translation_warnings, "编年史翻译查询失败，已退回宽松查询")
            if not item.trade_base_type and _uses_cjk_text(item.base_type):
                item.translation_warnings.append(f"未能将繁中底材「{item.base_type}」翻译为 trade2 英文底材")

    def save(self) -> None:
        """保存翻译缓存。"""

        if self.cache_path and self.dirty:
            self.cache.save(self.cache_path)
            self.dirty = False

    async def _resolve_unique_translation(self, name: str) -> tuple[str, str]:
        cached = self.cache.get("unique_name", name)
        if cached:
            return cached, ""

        static = translate_unique_name(name)
        if static:
            self.cache.set("unique_name", name, static, source="seed")
            self.dirty = True
            return static, ""

        translation = await self.poe2db_client.find_unique_translation(name)
        if not translation or not translation.name:
            return "", ""
        self.cache.set("unique_name", name, translation.name, source="poe2db")
        self.dirty = True
        return translation.name, translation.base_type

    async def _resolve_base_type(self, base_type: str, item_class: str = "") -> str:
        cached = self.cache.get("base_type", base_type)
        if cached:
            return cached

        static = translate_base_type(base_type)
        if static:
            self.cache.set("base_type", base_type, static, source="seed")
            self.dirty = True
            return static

        translated = await self.poe2db_client.find_base_type_translation(
            base_type,
            index_paths=_base_index_paths_for_item_class(item_class),
        )
        if not translated:
            return ""
        self.cache.set("base_type", base_type, translated, source="poe2db")
        self.dirty = True
        return translated


def _uses_cjk_text(text: str) -> bool:
    return any("\u3400" <= char <= "\u9fff" or "\uf900" <= char <= "\ufaff" for char in text)


def _append_once(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)


def _base_index_paths_for_item_class(item_class: str) -> tuple[str, ...]:
    normalized = item_class.strip()
    return BASE_INDEX_PATHS_BY_ITEM_CLASS_ZH_TW.get(normalized, DEFAULT_BASE_INDEX_PATHS)
