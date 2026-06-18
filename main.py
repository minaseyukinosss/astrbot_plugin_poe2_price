from __future__ import annotations

from pathlib import Path

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star
from astrbot.core.utils.astrbot_path import get_astrbot_data_path

try:
    from .services.formatter import format_price_estimate
    from .services.item_parser import parse_item_text
    from .services.ninja_client import NinjaClient
    from .services.poe2scout_client import Poe2ScoutClient
    from .services.price_estimator import estimate_price
    from .services.query_builder import build_item_query, build_name_query
    from .services.stat_catalog import StatCatalog
    from .services.trade_client import TradeApiError, TradeClient, build_trade_search_url
except ImportError:  # pragma: no cover - 兼容本地单元测试的顶层导入。
    from services.formatter import format_price_estimate
    from services.item_parser import parse_item_text
    from services.ninja_client import NinjaClient
    from services.poe2scout_client import Poe2ScoutClient
    from services.price_estimator import estimate_price
    from services.query_builder import build_item_query, build_name_query
    from services.stat_catalog import StatCatalog
    from services.trade_client import TradeApiError, TradeClient, build_trade_search_url


class Poe2PricePlugin(Star):
    """POE2 国际服实时查价插件。"""

    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.default_league = str(config.get("default_league", "Runes of Aldur"))
        self.realm = str(config.get("realm", "poe2"))
        self.max_fetch_results = int(config.get("max_fetch_results", 20))
        self.min_valid_listings = int(config.get("min_valid_listings", 5))
        timeout = float(config.get("request_timeout_seconds", 15))
        contact = str(config.get("user_agent_contact", "")).strip() or "unset-contact"
        user_agent = f"OAuth astrbot-plugin-poe2-price/0.1.0 (contact: {contact})"

        self.trade_client = TradeClient(user_agent=user_agent, timeout=timeout)
        self.ninja_client = NinjaClient(timeout=timeout, user_agent=user_agent)
        self.scout_client = Poe2ScoutClient(timeout=timeout, cache_ttl=int(config.get("scout_cache_ttl_seconds", 1800)))
        self.stat_catalog = StatCatalog()

        data_dir = Path(get_astrbot_data_path()) / "plugin_data" / self.name
        self.stat_cache_path = data_dir / "trade_stats.json"
        self.stat_catalog.load(self.stat_cache_path)

        if contact == "unset-contact":
            logger.warning("POE2 查价插件未配置 user_agent_contact，建议在插件配置中填写联系信息。")

    @filter.command("poe2查价")
    async def price_zh(self, event: AstrMessageEvent):
        """查询 POE2 国际服物品价格。"""

        query_text = _strip_command(event.message_str, "poe2查价")
        result = await self._handle_price_check(query_text)
        yield event.plain_result(result)

    @filter.command("poe2price")
    async def price_en_alias(self, event: AstrMessageEvent):
        """查询 POE2 国际服物品价格。"""

        query_text = _strip_command(event.message_str, "poe2price")
        result = await self._handle_price_check(query_text)
        yield event.plain_result(result)

    @filter.command("poe2联盟")
    async def league(self, event: AstrMessageEvent):
        """查看或设置 POE2 默认联盟。"""

        arg = _strip_command(event.message_str, "poe2联盟")
        if arg:
            self.default_league = arg
            self.config["default_league"] = arg
            save_config = getattr(self.config, "save_config", None)
            if callable(save_config):
                save_config()
            yield event.plain_result(f"已设置默认联盟：{arg}")
            return

        try:
            leagues = await self.trade_client.fetch_leagues()
            names = "、".join(item.get("text") or item.get("id", "") for item in leagues)
            yield event.plain_result(f"当前默认联盟：{self.default_league}\n可用联盟：{names}")
        except Exception as exc:
            logger.warning(f"获取 POE2 联盟失败：{exc}")
            yield event.plain_result(f"当前默认联盟：{self.default_league}\n获取可用联盟失败，请稍后再试。")

    @filter.command("poe2通货")
    async def currency(self, event: AstrMessageEvent):
        """查询 POE2 通货价格。"""

        keyword = _strip_command(event.message_str, "poe2通货")
        if not keyword:
            yield event.plain_result("请输入通货名，例如：/poe2通货 divine")
            return

        try:
            item = await self.ninja_client.search_currency(self.default_league, keyword)
        except Exception as exc:
            logger.warning(f"poe.ninja 通货查询失败：{exc}")
            item = None

        if not item:
            yield event.plain_result("没有找到该通货的 poe.ninja 价格。")
            return

        change = "" if item.change_percent is None else f"\n近况变化：{item.change_percent:g}%"
        yield event.plain_result(
            f"通货：{item.name}\n"
            f"联盟：{self.default_league}\n"
            f"当前价格：{item.amount:g} {item.currency}\n"
            f"成交量：{item.volume:g}"
            f"{change}\n"
            f"数据源：{item.source}"
        )

    async def _handle_price_check(self, query_text: str) -> str:
        if not query_text:
            return "请粘贴物品文本或输入物品名，例如：/poe2查价 水井之心"

        item = parse_item_text(query_text)
        if item:
            await self._ensure_stats_loaded()
            self.stat_catalog.apply_to_modifiers(item.explicit_mods + item.implicit_mods + item.crafted_mods)
            trade_query = build_item_query(item)
            display_name = item.display_name
        else:
            trade_query = build_name_query(query_text)
            display_name = query_text

        try:
            search_result = await self.trade_client.search(self.default_league, trade_query)
            result_ids = search_result.get("result", [])
            query_id = search_result.get("id")
            if not query_id or not result_ids:
                return f"没有找到可比挂售。\n物品：{display_name}\n联盟：{self.default_league}"
            trade_url = build_trade_search_url(self.default_league, query_id, base_url=self.trade_client.base_url)
            listings = await self.trade_client.fetch_listings(result_ids, query_id, limit=self.max_fetch_results)
        except TradeApiError as exc:
            return str(exc)
        except Exception as exc:
            logger.warning(f"POE2 查价失败：{exc}")
            return "查价失败：远端服务暂时不可用，请稍后再试。"

        estimate = estimate_price(
            display_name,
            self.default_league,
            listings,
            min_valid_listings=self.min_valid_listings,
            trade_url=trade_url,
        )
        return format_price_estimate(estimate)

    async def _ensure_stats_loaded(self) -> None:
        if self.stat_catalog._patterns:
            return
        try:
            data = await self.trade_client.fetch_stats()
            self.stat_catalog.load_from_trade_stats(data)
            self.stat_catalog.save(self.stat_cache_path)
        except Exception as exc:
            logger.warning(f"加载 trade stats 失败，将仅使用内置繁中词缀映射：{exc}")

    async def terminate(self):
        """插件停用时关闭网络客户端。"""

        await self.trade_client.close()
        await self.ninja_client.close()
        await self.scout_client.close()


def _strip_command(message: str, command: str) -> str:
    text = (message or "").strip()
    for prefix in (f"/{command}", command):
        if text.startswith(prefix):
            return text[len(prefix) :].strip()
    return text
