# astrbot_plugin_poe2_price

POE2 国际服实时查价 AstrBot 插件，面向使用繁体中文客户端的玩家。插件可以识别游戏内复制出的繁体中文物品文本，通过官方 trade2 查询可比挂售，并在回复中返回估价区间、样本数量、置信度和官方 trade2 搜索链接。

## 功能

- 支持 `/poe2查价` 粘贴物品文本查价。
- 支持 `/poe2price` 英文别名。
- 支持繁体中文物品字段，例如 `物品種類`、`稀有度`、`物品等級`、`已汙染`。
- 支持传奇物品、稀有装备的基础属性与常见词缀解析。
- 通过官方 trade2 API 查询挂售，并返回官方搜索结果页链接。
- 对异常低价样本做基础过滤，输出低价位、高价位、中位数与置信度。
- 支持 `/poe2联盟` 查看或设置默认联盟。
- 支持 `/poe2通货` 通过 POE2 Scout 查询通货参考价。

## 安装

1. 将本仓库放入 AstrBot 的插件目录。
2. 安装依赖：

```bash
pip install -r requirements.txt
```

3. 在 AstrBot 中启用插件。
4. 在插件配置中填写 `user_agent_contact`，建议使用邮箱或项目地址，便于负责任地访问 Path of Exile API。

## 使用

查价完整物品文本：

```text
/poe2查价 物品種類: 珠寶
稀有度: 傳奇
水井之心
鑽石
--------
物品等級: 81
```

也可以直接查物品名：

```text
/poe2查价 水井之心
```

查看当前联盟：

```text
/poe2联盟
```

设置默认联盟：

```text
/poe2联盟 Runes of Aldur
```

查询通货：

```text
/poe2通货 divine
```

## 配置

| 配置项 | 默认值 | 说明 |
| --- | --- | --- |
| `default_league` | `Runes of Aldur` | 默认查询联盟。 |
| `realm` | `poe2` | POE2 Scout 使用的 realm。 |
| `max_fetch_results` | `20` | 每次最多拉取的 trade2 挂售数量。 |
| `min_valid_listings` | `5` | 低于该有效样本数时标记为低置信度。 |
| `request_timeout_seconds` | `15` | HTTP 请求超时时间。 |
| `scout_cache_ttl_seconds` | `1800` | POE2 Scout 缓存时间。 |
| `user_agent_contact` | 空 | 建议填写联系信息。 |
| `poesessid` | 空 | 预留字段，默认不需要。 |

## 返回示例

```text
物品：水井之心 (鑽石)
联盟：Runes of Aldur
估价：3 - 5 exalted
中位数：4 exalted
置信度：中
有效样本：12/20
数据源：trade2
官方链接：https://www.pathofexile.com/trade2/search/poe2/Runes%20of%20Aldur/abc123
参考挂售：
1. 3 exalted @account
2. 4 exalted @account
3. 5 exalted @account
```

## 开发

运行单元测试：

```bash
python3 -m unittest discover -v
```

语法检查：

```bash
python3 -m compileall .
```

## 注意事项

- 本插件优先使用官方 trade2 数据，价格仅代表当前挂售参考，不等同于成交价。
- trade2 有限流策略，频繁查询可能会被临时限制。
- 繁体中文词缀到官方 stat id 的映射会逐步补齐；未命中的词缀会降级为较宽松的查询条件。
- POE2 Scout 仅作为通货或辅助价格来源。

