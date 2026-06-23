# Stock-Radar 项目规范

## 项目定位

A股行情研究网站：每日追踪大盘指数、板块/行业涨跌、资金流向、个股行情。本地运行，FastAPI + Jinja2 提供 Web 界面。

## 目录结构

```
stock-radar/
├── CLAUDE.md              # 项目规范（本文件）
├── config.yaml            # 主配置：关注指数、自选股、调度时间
├── main.py                # FastAPI 入口 + 启动调度器
├── requirements.txt
├── .env.example
├── db/
│   └── snapshot.db        # SQLite 日快照（git 忽略）
├── data/
│   ├── cache.py           # SQLite 初始化 + 内存 TTL 缓存
│   ├── scheduler.py       # APScheduler 盘后任务
│   ├── watchlist_store.py # 持仓动态存储（JSON 文件）
│   └── fetchers/
│       ├── indices.py     # 新浪实时指数
│       ├── boards.py      # 板块列表 + 构成股 + K 线
│       ├── stocks.py      # 个股/ETF 行情、搜索、持仓
│       ├── flow.py        # 资金流向（THS + 东方财富）
│       └── market.py      # 市场情绪（涨跌家数、北向、龙虎榜）
├── api/
│   ├── routes_overview.py # GET /api/indices /api/flow/* /api/market/* /api/zt
│   ├── routes_boards.py   # GET /api/boards /api/boards/{type}/{name}/*
│   └── routes_stocks.py   # GET/POST/DELETE /api/stocks/* /api/stocks/etf/*
└── templates/
    ├── base.html          # Bootstrap 5 Navbar + 布局骨架 + 口令弹框
    ├── overview.html      # 首页：情绪条 + 指数 + 热力图 + 资金 + 涨停 + 龙虎榜
    ├── boards.html        # 板块列表（概念/行业 Tab）
    ├── board_detail.html  # 板块详情 + 构成股
    ├── stocks.html        # 个股持仓 + 搜索
    └── etf.html           # ETF 持仓 + 搜索
```

## 数据源详细说明

### 1. 新浪 `hq.sinajs.cn` — 实时行情

**文件**：`fetchers/indices.py`、`fetchers/stocks.py`
**稳定性**：最稳定，无反爬，无需 AKShare

| 函数 | 用途 | 页面 |
|------|------|------|
| `fetch_indices()` | 大盘指数实时行情（价格、涨跌幅、开高低收、量额） | 首页指数卡片、导航栏实时指数 |
| `fetch_quotes(codes)` | 个股/ETF 批量实时行情，100个/次 | 个股持仓、ETF 持仓、搜索结果 |

**注意**：Sina hq 返回的名称字段会被截断（尤其深交所 ETF），需配合 suggest 接口覆盖完整名称。

---

### 2. 新浪 suggest `suggest3.sinajs.cn` — 名称搜索

**文件**：`fetchers/stocks.py` → `_suggest_pairs()`

| 参数 | 用途 | 说明 |
|------|------|------|
| `type=11` | 个股名称/代码模糊搜索 | 返回 A 股，排除 ETF |
| `type=22` | ETF 名称/代码模糊搜索 | 返回基金，排除个股 |

**关键逻辑**：
- 按代码查询时 `parts[0]` 为 Sina 内部格式（`sh600519`），完整显示名在 `parts[4]`
- 含中文的查询强制要求输入串作为连续子串出现在候选名称中，防止拆字匹配
- 结果按 `_is_etf_code()` 二次过滤，确保类型隔离

---

### 3. AKShare 同花顺（THS） — 板块与资金

**文件**：`fetchers/boards.py`、`fetchers/flow.py`
**特点**：THS 独有价值数据，东方财富等价接口在当前网络被封时首选

| AKShare 函数 | 用途 | 页面 |
|-------------|------|------|
| `stock_fund_flow_concept(symbol="即时")` | 概念板块列表：涨跌幅、净流入、领涨股及涨跌幅 | 板块页概念 Tab |
| `stock_board_industry_summary_ths()` | 行业板块汇总：涨跌幅、上涨/下跌家数、领涨股、净流入 | 板块页行业 Tab |
| `stock_fund_flow_industry(symbol="即时")` | 行业资金流向排行（净额降序） | 首页行业资金流 TOP8 |
| `stock_fund_flow_individual(stock, market)` | 个股资金流向明细 | 个股详情页（预留） |
| `stock_board_industry_index_ths(symbol, start_date, end_date)` | 行业板块近 N 日 K 线 | 板块详情页 K 线图 |
| `stock_board_concept_index_ths(symbol, start_date, end_date)` | 概念板块近 N 日 K 线 | 板块详情页 K 线图 |

**注意**：概念板块无"上涨/下跌家数"字段（THS 接口限制），板块列表中该列显示 `-`。

---

### 4. AKShare 东方财富（East Money） — 涨停/龙虎榜/构成股

**文件**：`fetchers/flow.py`、`fetchers/boards.py`、`fetchers/market.py`
**注意**：东方财富系接口在部分网络环境（尤其国内企业/机房网络）会 RemoteDisconnected，板块构成股接口受此影响

| AKShare 函数 | 用途 | 页面 | 网络依赖 |
|-------------|------|------|---------|
| `stock_zt_pool_em(date)` | 涨停板（连板数、封板资金、炸板次数、所属行业） | 首页涨停板 | 是 |
| `stock_market_fund_flow()` | 大盘资金流向 | 首页（预留） | 是 |
| `stock_board_concept_cons_em(symbol)` | 概念板块构成股行情 | 板块详情构成股表 | **易被封** |
| `stock_board_industry_cons_em(symbol)` | 行业板块构成股行情 | 板块详情构成股表 | **易被封** |
| `stock_lhb_detail_em()` | 今日龙虎榜（净买额、上榜原因，取当日最新） | 首页龙虎榜 | 是 |

---

### 5. 新浪全量行情 — 市场情绪（涨跌家数）

**文件**：`fetchers/market.py` → `fetch_market_breadth()`
**数据源**：AKShare `stock_zh_a_spot()`，底层为新浪 A 股全量接口，与 `hq.sinajs.cn` 同源
**注意**：拉取全量 ~5500 支股票耗时约 20 秒，路由缓存 TTL 设为 300 秒（5 分钟）

| 字段 | 说明 |
|------|------|
| `up` / `down` / `flat` | 涨/跌/平盘家数（全 A 股含北交所） |
| `zt` / `dt` | 涨停/跌停家数（按涨跌幅 ±9.9% 阈值近似，精确值见 /api/zt 涨停板池） |
| `total` | 全量股票数 |

> 历史原因：曾用 `stock_market_activity_legu()`（乐咕乐股），数据偏少（不含北交所等）已废弃替换。

---

### 6. AKShare 东方财富沪深港通 — 北向资金

**文件**：`fetchers/market.py`

| AKShare 函数 | 用途 | 页面 |
|-------------|------|------|
| `stock_hsgt_fund_flow_summary_em()` | 北向资金净流入（沪股通/深股通上涨数、下跌数、净买额） | 首页北向资金面板 |

---

### 数据源对照速查

| 功能 | 数据源 | AKShare 函数 / URL |
|------|--------|-------------------|
| 大盘指数实时 | 新浪 hq | `hq.sinajs.cn/list=sh000001,...` |
| 个股/ETF 实时行情 | 新浪 hq | `hq.sinajs.cn/list=sh600519,...` |
| 个股/ETF 名称搜索 | 新浪 suggest | `suggest3.sinajs.cn/suggest/type=11/22` |
| 概念板块列表 | THS | `stock_fund_flow_concept(symbol="即时")` |
| 行业板块列表 | THS | `stock_board_industry_summary_ths()` |
| 行业资金流向 | THS | `stock_fund_flow_industry(symbol="即时")` |
| 个股资金流向 | THS | `stock_fund_flow_individual()` |
| 板块 K 线 | THS | `stock_board_industry/concept_index_ths()` |
| 涨停板 | 东方财富 | `stock_zt_pool_em()` |
| 板块构成股 | 东方财富 | `stock_board_concept/industry_cons_em()` |
| 龙虎榜 | 东方财富 | `stock_lhb_detail_em()` |
| 大盘资金流向 | 东方财富 | `stock_market_fund_flow()` |
| 市场情绪（涨跌家数） | 乐咕乐股 | `stock_market_activity_legu()` |
| 北向资金 | 东方财富沪深港通 | `stock_hsgt_fund_flow_summary_em()` |

---

## 命名约定

- 模块文件：全小写下划线（`boards.py`）
- 函数名：小写下划线（`fetch_board_list`）
- 配置读取：统一从 `config.yaml` 读，禁止在代码里硬编码股票代码/名称
- 密钥：只走 `.env`，禁止进代码和 commit

## 编码约定

- Python 3.11+
- 依赖管理：pip + requirements.txt
- 错误处理：每个 fetcher 独立 try/except，单模块失败返回空数据不崩整站
- 缓存策略：内存 dict TTL 5 分钟（盘中刷新）+ SQLite 日快照（盘后持久化）
- 所有时间以北京时间（UTC+8）为准，JS 侧加 `timeZone:'Asia/Shanghai'`，Python 侧用 `timezone(timedelta(hours=8))`

## 验证方式

```bash
# 启动开发服务器
uvicorn main:app --reload --host 127.0.0.1 --port 8000

# 单独测试 fetcher
python -c "from data.fetchers.indices import fetch_indices; import json; print(json.dumps(fetch_indices(), ensure_ascii=False, indent=2))"
python -c "from data.fetchers.flow import fetch_industry_flow; import json; print(json.dumps(fetch_industry_flow(), ensure_ascii=False, indent=2))"
python -c "from data.fetchers.stocks import search_etf; import json; print(json.dumps(search_etf('沪深300'), ensure_ascii=False, indent=2))"
```

## 禁止事项

- 不把密钥写进任何代码文件
- 不在未验证的情况下修改缓存逻辑（容易导致数据不刷新）
- 不添加未在计划中的功能（先跑通再扩展）
- 新增数据源前先在「数据源详细说明」章节补充文档，再写代码
