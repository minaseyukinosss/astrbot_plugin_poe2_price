from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from typing import Any

import httpx

try:
    from .http_client import HttpRequestError, RateLimiter
except ImportError:  # pragma: no cover - 兼容本地单元测试的顶层导入。
    from services.http_client import HttpRequestError, RateLimiter


DEFAULT_BASE_INDEX_PATHS = (
    "/tw/One_Hand_Mace",
    "/tw/Two_Hand_Mace",
    "/tw/Quarterstaff",
    "/tw/Bow",
    "/tw/Crossbow",
    "/tw/Wand",
    "/tw/Sceptre",
    "/tw/Staff",
    "/tw/Focus",
    "/tw/Shield",
    "/tw/Buckler",
    "/tw/Helmet",
    "/tw/Body_Armour",
    "/tw/Gloves",
    "/tw/Boots",
    "/tw/Belt",
    "/tw/Amulet",
    "/tw/Ring",
    "/tw/Jewel",
    "/tw/Flask",
)


@dataclass(slots=True)
class ItemTranslation:
    """编年史解析出的 trade2 英文字段。"""

    name: str = ""
    base_type: str = ""
    source_path: str = ""


class Poe2DbClient:
    """POE2 编年史繁中页面客户端。"""

    def __init__(
        self,
        *,
        base_url: str = "https://poe2db.tw",
        user_agent: str = "astrbot-plugin-poe2-price/0.1.0",
        timeout: float = 15.0,
        limiter: RateLimiter | None = None,
        unique_index_paths: tuple[str, ...] = ("/tw/Unique_item",),
        base_index_paths: tuple[str, ...] | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.unique_index_paths = unique_index_paths
        self.base_index_paths = base_index_paths or DEFAULT_BASE_INDEX_PATHS
        self.limiter = limiter or RateLimiter(max_requests=12, window_seconds=60)
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "User-Agent": user_agent,
                "Accept": "text/html,application/xhtml+xml",
            },
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def fetch_text(self, path: str) -> str:
        """获取编年史 HTML 文本。"""

        await self.limiter.wait()
        response = await self._client.get(f"{self.base_url}{path}")
        if response.status_code >= 400:
            raise HttpRequestError("poe2db", response.status_code, response.text)
        return response.text

    async def find_unique_translation(self, zh_name: str) -> ItemTranslation | None:
        """按繁中传奇名查找官方英文名和底材。"""

        for index_path in self.unique_index_paths:
            link = await self._find_detail_link(index_path, zh_name)
            if not link:
                continue
            detail_html = await self.fetch_text(link)
            translation = _extract_item_translation(detail_html, source_path=link)
            if translation and translation.name:
                return translation
        return None

    async def find_base_type_translation(
        self,
        zh_base_type: str,
        *,
        index_paths: tuple[str, ...] | None = None,
    ) -> str | None:
        """按繁中底材查找官方英文底材。"""

        for index_path in index_paths or self.base_index_paths:
            link = await self._find_detail_link(index_path, zh_base_type)
            if not link:
                continue
            detail_html = await self.fetch_text(link)
            translation = _extract_item_translation(detail_html, source_path=link)
            if not translation:
                continue
            for candidate in (translation.base_type, translation.name):
                if _is_trade_text(candidate):
                    return candidate
        return None

    async def _find_detail_link(self, index_path: str, zh_text: str) -> str | None:
        index_html = await self.fetch_text(index_path)
        return _extract_link_near_text(index_html, zh_text)


def _extract_link_near_text(page_html: str, zh_text: str) -> str | None:
    """从列表页里找包含目标繁中文本的详情链接。"""

    target = _compact(zh_text)
    for match in re.finditer(r"<a\b(?P<attrs>[^>]*)>(?P<body>.*?)</a>", page_html, flags=re.IGNORECASE | re.DOTALL):
        label = _compact(_strip_tags(match.group("body")))
        if target not in label:
            continue
        href = _extract_href(match.group("attrs"))
        if href:
            return _normalize_path(href)

    plain_html = _compact(page_html)
    index = plain_html.find(target)
    if index < 0:
        return None
    window = page_html[max(0, index - 800) : index + 800]
    href_matches = list(re.finditer(r"href=[\"'](?P<href>/tw/[^\"']+)[\"']", window, flags=re.IGNORECASE))
    if not href_matches:
        return None
    return _normalize_path(href_matches[-1].group("href"))


def _extract_item_translation(page_html: str, *, source_path: str = "") -> ItemTranslation | None:
    """从详情页脚本数据里提取英文名和英文底材。"""

    objects = _extract_json_objects(page_html)
    for payload in objects:
        translation = _translation_from_payload(payload, source_path=source_path)
        if translation and (translation.name or translation.base_type):
            return translation

    name = _extract_json_string(page_html, "name")
    base_type = _extract_json_string(page_html, "baseType") or _extract_json_string(page_html, "typeLine")
    if _is_trade_text(name) or _is_trade_text(base_type):
        return ItemTranslation(
            name=name if _is_trade_text(name) else "",
            base_type=base_type if _is_trade_text(base_type) else "",
            source_path=source_path,
        )
    return None


def _translation_from_payload(payload: Any, *, source_path: str) -> ItemTranslation | None:
    if isinstance(payload, dict):
        name = _first_trade_value(payload, ("name", "Name", "en_name", "english_name"))
        base_type = _first_trade_value(payload, ("baseType", "base_type", "typeLine", "type_line"))
        if name or base_type:
            return ItemTranslation(name=name, base_type=base_type, source_path=source_path)
        for value in payload.values():
            translation = _translation_from_payload(value, source_path=source_path)
            if translation:
                return translation
    if isinstance(payload, list):
        for value in payload:
            translation = _translation_from_payload(value, source_path=source_path)
            if translation:
                return translation
    return None


def _extract_json_objects(page_html: str) -> list[Any]:
    objects: list[Any] = []
    for script_body in re.findall(r"<script\b[^>]*>(.*?)</script>", page_html, flags=re.IGNORECASE | re.DOTALL):
        decoded = html.unescape(script_body)
        for match in re.finditer(r"(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})", decoded, flags=re.DOTALL):
            text = match.group(1)
            if '"name"' not in text and '"baseType"' not in text and '"typeLine"' not in text:
                continue
            try:
                objects.append(json.loads(text))
            except json.JSONDecodeError:
                continue
    return objects


def _first_trade_value(payload: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and _is_trade_text(value):
            return value.strip()
    return ""


def _extract_json_string(page_html: str, key: str) -> str:
    pattern = rf'"{re.escape(key)}"\s*:\s*"(?P<value>(?:\\.|[^"\\])*)"'
    match = re.search(pattern, page_html)
    if not match:
        return ""
    try:
        value = json.loads(f'"{match.group("value")}"')
    except json.JSONDecodeError:
        value = match.group("value")
    return value.strip() if _is_trade_text(value) else ""


def _extract_href(attrs: str) -> str:
    match = re.search(r"href=[\"'](?P<href>[^\"']+)[\"']", attrs, flags=re.IGNORECASE)
    return html.unescape(match.group("href")) if match else ""


def _normalize_path(href: str) -> str:
    if href.startswith("http://") or href.startswith("https://"):
        match = re.search(r"https?://[^/]+(?P<path>/.*)", href)
        return match.group("path") if match else href
    return href


def _strip_tags(value: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", " ", value))


def _compact(value: str) -> str:
    return re.sub(r"\s+", "", _strip_tags(html.unescape(value))).strip()


def _is_trade_text(value: str | None) -> bool:
    if not value:
        return False
    return not re.search(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]", value)
