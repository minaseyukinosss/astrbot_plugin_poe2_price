from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


DEFAULT_ZH_TW_STAT_ALIASES = {
    "最大生命": "explicit.stat_3299347043",
    "火焰抗性": "explicit.stat_4220027924",
    "冰冷抗性": "explicit.stat_4220027924",
    "閃電抗性": "explicit.stat_4220027924",
    "混沌抗性": "explicit.stat_3372524247",
    "移動速度": "explicit.stat_3845215720",
    "攻擊速度": "explicit.stat_210067635",
    "施法速度": "explicit.stat_2891184298",
    "暴擊加成": "explicit.stat_3556824919",
    "暴擊率": "explicit.stat_4080418644",
}


class StatCatalog:
    """trade2 stat id 目录。"""

    def __init__(self) -> None:
        self._patterns: dict[str, str] = {}
        self._aliases = DEFAULT_ZH_TW_STAT_ALIASES.copy()

    def load_from_trade_stats(self, data: dict[str, Any]) -> None:
        """从 trade2 stats 响应加载 stat 文本。"""

        for group in data.get("result", []):
            for entry in group.get("entries", []):
                stat_id = entry.get("id")
                text = entry.get("text")
                if not stat_id or not text:
                    continue
                self._patterns[self.normalize_text(text)] = stat_id

    def resolve_stat_id(self, modifier_text: str) -> str | None:
        """解析词缀对应的 stat id。"""

        normalized = self.normalize_text(modifier_text)
        if normalized in self._patterns:
            return self._patterns[normalized]

        for key, stat_id in self._aliases.items():
            if key in modifier_text:
                return stat_id
        return None

    def apply_to_modifiers(self, modifiers: list) -> None:
        """原地填充词缀 stat id。"""

        for modifier in modifiers:
            if not getattr(modifier, "stat_id", None):
                modifier.stat_id = self.resolve_stat_id(modifier.text)

    def save(self, path: Path) -> None:
        """保存动态 stat cache。"""

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self._patterns, ensure_ascii=False, indent=2), encoding="utf-8")

    def load(self, path: Path) -> None:
        """加载动态 stat cache。"""

        if not path.exists():
            return
        self._patterns.update(json.loads(path.read_text(encoding="utf-8")))

    @staticmethod
    def normalize_text(text: str) -> str:
        """将具体数值归一为 `#`，便于匹配。"""

        normalized = text.strip().lower()
        normalized = re.sub(r"[+-]?\d+(?:\.\d+)?%?", "#", normalized)
        normalized = normalized.replace("+#", "#").replace("-#", "#")
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized
