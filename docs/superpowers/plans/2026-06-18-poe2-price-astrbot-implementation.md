# POE2 实时查价 AstrBot 插件 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个可加载的 AstrBot 插件骨架，并实现国际服繁体中文 POE2 物品文本解析、查询构建、估价和中文结果输出的核心逻辑。

**Architecture:** `main.py` 只负责 AstrBot 命令接入，核心逻辑放在 `services/`。解析流程先由 `item_text_normalizer.py` 归一化繁中字段，再由 `item_parser.py` 生成 `ParsedItem`，之后交给查询构建、客户端、估价器和格式化器。

**Tech Stack:** Python 3.12、AstrBot 插件 API、`httpx` 异步 HTTP 客户端、标准库 `unittest`。

---

### Task 1: 繁体中文物品文本归一化和解析

**Files:**
- Create: `models.py`
- Create: `services/item_text_normalizer.py`
- Create: `services/item_parser.py`
- Create: `services/__init__.py`
- Test: `tests/test_item_parser.py`

- [ ] **Step 1: Write failing parser tests**

测试用户提供的 `水井之心` 传奇珠宝样例，要求识别物品名、基底、稀有度、物品等级，并忽略风味文本和操作提示。

- [ ] **Step 2: Run tests and verify they fail**

Run: `python3 -m unittest tests.test_item_parser -v`
Expected: FAIL or ERROR because modules do not exist.

- [ ] **Step 3: Implement normalizer, models, and parser**

实现繁中字段别名、稀有度映射、分段解析、名称/基底识别、物品等级解析、展示文本过滤。

- [ ] **Step 4: Run tests and verify they pass**

Run: `python3 -m unittest tests.test_item_parser -v`
Expected: PASS.

### Task 2: 查询构建和繁中名称处理

**Files:**
- Create: `services/query_builder.py`
- Test: `tests/test_query_builder.py`

- [ ] **Step 1: Write failing query builder tests**

测试传奇物品使用原始繁中名称和基底构建 trade2 查询；测试黄装会加入 rarity、online、priced sale filters。

- [ ] **Step 2: Run tests and verify they fail**

Run: `python3 -m unittest tests.test_query_builder -v`
Expected: FAIL or ERROR because query builder does not exist.

- [ ] **Step 3: Implement query builder**

实现基础查询 JSON、传奇/黄装分支、priced 和 online filters。

- [ ] **Step 4: Run tests and verify they pass**

Run: `python3 -m unittest tests.test_query_builder -v`
Expected: PASS.

### Task 3: 价格估算和中文格式化

**Files:**
- Create: `services/price_estimator.py`
- Create: `services/formatter.py`
- Test: `tests/test_price_estimator.py`
- Test: `tests/test_formatter.py`

- [ ] **Step 1: Write failing estimator and formatter tests**

测试异常低价过滤、中位数估算、低样本低置信度、中文输出包含联盟/置信度/样本数。

- [ ] **Step 2: Run tests and verify they fail**

Run: `python3 -m unittest tests.test_price_estimator tests.test_formatter -v`
Expected: FAIL or ERROR because modules do not exist.

- [ ] **Step 3: Implement estimator and formatter**

实现价格归一化、异常价过滤、置信度判断和中文文本输出。

- [ ] **Step 4: Run tests and verify they pass**

Run: `python3 -m unittest tests.test_price_estimator tests.test_formatter -v`
Expected: PASS.

### Task 4: HTTP 客户端、插件骨架和配置

**Files:**
- Create: `services/trade_client.py`
- Create: `services/poe2scout_client.py`
- Create: `services/stat_catalog.py`
- Create: `main.py`
- Create: `metadata.yaml`
- Create: `_conf_schema.json`
- Create: `requirements.txt`

- [ ] **Step 1: Implement async service clients**

实现 `httpx.AsyncClient` 包装、trade2 search/fetch/leagues/stats、POE2 Scout 基础查询、简单缓存和限流错误模型。

- [ ] **Step 2: Implement AstrBot command wiring**

实现 `/poe2查价`、`/poe2price`、`/poe2联盟`、`/poe2通货` 命令入口，并保证所有用户可见输出为中文。

- [ ] **Step 3: Run all available tests**

Run: `python3 -m unittest discover -v`
Expected: PASS.

### Task 5: 收尾检查

**Files:**
- Modify as needed: all created files.

- [ ] **Step 1: Syntax check**

Run: `python3 -m compileall .`
Expected: all files compile.

- [ ] **Step 2: Git note**

Git init/commit 当前因环境权限阻塞，记录在最终回复中。
