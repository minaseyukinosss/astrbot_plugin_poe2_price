from __future__ import annotations

import inspect
import time
from collections.abc import Awaitable, Callable
from typing import Any

import httpx


SleepFn = Callable[[float], Awaitable[None] | None]
ClockFn = Callable[[], float]


class HttpRequestError(Exception):
    """HTTP 请求失败。"""

    def __init__(self, source: str, status_code: int, body: str = "") -> None:
        preview = body[:200].strip()
        message = f"{source} 请求失败：HTTP {status_code}"
        if preview:
            message = f"{message}：{preview}"
        super().__init__(message)
        self.source = source
        self.status_code = status_code
        self.body_preview = preview


class RateLimiter:
    """滑动窗口限流器。"""

    def __init__(
        self,
        *,
        max_requests: int,
        window_seconds: float,
        sleep: SleepFn | None = None,
        clock: ClockFn | None = None,
    ) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._sleep = sleep or _default_sleep
        self._clock = clock or time.monotonic
        self._timestamps: list[float] = []

    async def wait(self) -> None:
        now = self._clock()
        self._timestamps = [timestamp for timestamp in self._timestamps if now - timestamp < self.window_seconds]
        if len(self._timestamps) >= self.max_requests:
            delay = self.window_seconds - (now - self._timestamps[0])
            if delay > 0:
                result = self._sleep(delay)
                if inspect.isawaitable(result):
                    await result
        self._timestamps.append(self._clock())


class HttpJsonClient:
    """带统一请求头、限流和错误信息的 JSON 客户端。"""

    def __init__(
        self,
        *,
        source: str,
        base_url: str,
        user_agent: str,
        timeout: float = 15.0,
        limiter: RateLimiter | None = None,
    ) -> None:
        self.source = source
        self.base_url = base_url.rstrip("/")
        self.limiter = limiter
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "User-Agent": user_agent,
                "Accept": "application/json",
            },
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def get(self, path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self.request("GET", path, params=params)

    async def post(self, path: str, *, json: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self.request("POST", path, json=json)

    async def request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        if self.limiter:
            await self.limiter.wait()

        response = await self._client.request(method, f"{self.base_url}{path}", **kwargs)
        if response.status_code >= 400:
            body = await _response_text(response)
            raise HttpRequestError(self.source, response.status_code, body)
        return response.json()


async def _default_sleep(delay: float) -> None:
    import asyncio

    await asyncio.sleep(delay)


async def _response_text(response: httpx.Response) -> str:
    try:
        return response.text
    except Exception:
        return ""
