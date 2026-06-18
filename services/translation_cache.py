from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    from .item_translation import BASE_TYPE_ALIASES_ZH_TW, UNIQUE_NAME_ALIASES_ZH_TW
except ImportError:  # pragma: no cover - 兼容本地单元测试的顶层导入。
    from services.item_translation import BASE_TYPE_ALIASES_ZH_TW, UNIQUE_NAME_ALIASES_ZH_TW


@dataclass(slots=True)
class TranslationCacheEntry:
    """单条繁中到 trade2 英文名的缓存记录。"""

    value: str
    source: str = "manual"
    updated_at: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "value": self.value,
            "source": self.source,
            "updated_at": self.updated_at,
        }


class TranslationCache:
    """本地翻译缓存，减少重复访问编年史。"""

    version = 1

    def __init__(self, entries: dict[str, TranslationCacheEntry] | None = None, *, seed_aliases: bool = True) -> None:
        self._entries: dict[str, TranslationCacheEntry] = entries or {}
        if seed_aliases:
            self._seed_static_aliases()

    @classmethod
    def load(cls, path: Path, *, seed_aliases: bool = True) -> "TranslationCache":
        """从磁盘加载缓存；文件不存在或损坏时返回仅带内置别名的缓存。"""

        if not path.exists():
            return cls(seed_aliases=seed_aliases)

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return cls(seed_aliases=seed_aliases)

        entries: dict[str, TranslationCacheEntry] = {}
        for key, value in (raw.get("entries") or {}).items():
            if isinstance(value, str):
                entries[key] = TranslationCacheEntry(value=value, source="legacy")
                continue
            if not isinstance(value, dict) or not value.get("value"):
                continue
            entries[key] = TranslationCacheEntry(
                value=str(value["value"]),
                source=str(value.get("source", "cache")),
                updated_at=str(value.get("updated_at", "")),
            )
        return cls(entries, seed_aliases=seed_aliases)

    def save(self, path: Path) -> None:
        """保存缓存到磁盘。"""

        path.parent.mkdir(parents=True, exist_ok=True)
        payload: dict[str, Any] = {
            "version": self.version,
            "entries": {key: entry.to_dict() for key, entry in sorted(self._entries.items())},
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def get(self, kind: str, text: str) -> str | None:
        """读取指定类型和繁中文本对应的英文 trade2 名称。"""

        entry = self._entries.get(_cache_key(kind, text))
        if not entry:
            return None
        return entry.value

    def set(self, kind: str, text: str, value: str, *, source: str = "poe2db") -> None:
        """写入指定类型和繁中文本对应的英文 trade2 名称。"""

        normalized_text = text.strip()
        normalized_value = value.strip()
        if not normalized_text or not normalized_value:
            return
        self._entries[_cache_key(kind, normalized_text)] = TranslationCacheEntry(
            value=normalized_value,
            source=source,
            updated_at=datetime.now(UTC).isoformat(timespec="seconds"),
        )

    def _seed_static_aliases(self) -> None:
        for text, value in BASE_TYPE_ALIASES_ZH_TW.items():
            self._entries.setdefault(_cache_key("base_type", text), TranslationCacheEntry(value=value, source="seed"))
        for text, value in UNIQUE_NAME_ALIASES_ZH_TW.items():
            self._entries.setdefault(_cache_key("unique_name", text), TranslationCacheEntry(value=value, source="seed"))


def _cache_key(kind: str, text: str) -> str:
    return f"{kind}:{text.strip()}"
