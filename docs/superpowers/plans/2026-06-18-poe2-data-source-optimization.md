# POE2 Data Source Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将插件第一阶段优化为多数据源查价：统一 HTTP/限流，通货改走 poe.ninja，POE2 Scout 专注唯一物品辅助价格，并保留 trade2 实时挂售主流程。

**Architecture:** 新增轻量 HTTP 请求层和数据源客户端；`main.py` 只负责编排命令，不直接了解各数据源细节。通货查询走 `NinjaClient`，trade2 查询保留现有路径并接入主动限流。

**Tech Stack:** Python 3.12、httpx、unittest、AstrBot 插件 API。

---

### Task 1: 通用 HTTP 与限流

**Files:**
- Create: `services/http_client.py`
- Test: `tests/test_http_client.py`
- Modify: `services/trade_client.py`

- [ ] **Step 1: Write failing tests**

测试 `RateLimiter` 在窗口内达到请求上限后会调用睡眠函数；测试 HTTP 错误会暴露状态码和响应片段。

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_http_client -v`
Expected: FAIL because `services.http_client` does not exist.

- [ ] **Step 3: Implement minimal HTTP utilities**

实现 `RateLimiter`、`HttpRequestError`、`HttpJsonClient`，支持 GET/POST JSON、统一 User-Agent、主动限流、错误响应片段。

- [ ] **Step 4: Wire trade2 to limiter**

`TradeClient` 保留现有 429/403 行为，但构造时增加主动限流，避免高频 fetch 批量请求直接撞限流。

- [ ] **Step 5: Verify**

Run: `python3 -m unittest tests.test_http_client tests.test_trade_client -v`

### Task 2: poe.ninja 通货源

**Files:**
- Create: `services/ninja_client.py`
- Test: `tests/test_ninja_client.py`
- Modify: `main.py`, `services/currency_aliases.py`

- [ ] **Step 1: Write failing tests**

测试 `NinjaClient.search_currency()` 能从 poe.ninja exchange overview 的 `core.items`、`core.rates`、`lines` 组合出 `Divine Orb` 的价格、成交量、变化率。

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_ninja_client -v`
Expected: FAIL because `services.ninja_client` does not exist.

- [ ] **Step 3: Implement NinjaClient**

请求 `/poe2/api/economy/exchange/current/overview?league=...&type=Currency`，用中文别名归一化关键词，返回规范化通货价格模型。

- [ ] **Step 4: Wire command**

`/poe2通货` 优先使用 `NinjaClient`；失败时给出明确数据源错误，避免误报“没有找到”。

- [ ] **Step 5: Verify**

Run: `python3 -m unittest tests.test_ninja_client tests.test_poe2scout_client -v`

### Task 3: 输出与文档同步

**Files:**
- Modify: `README.md`
- Modify: `services/formatter.py` if needed
- Test: existing unit tests

- [ ] **Step 1: Update docs**

README 中说明通货价格来自 poe.ninja，唯一物品辅助价格来自 POE2 Scout，trade2 仍用于实时挂售。

- [ ] **Step 2: Full verification**

Run: `python3 -m unittest discover -v`
Run: `python3 -m compileall .`

- [ ] **Step 3: Commit**

Commit message: `feat: 优化 POE2 价格数据源`
