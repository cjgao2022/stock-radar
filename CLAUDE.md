# Stock-Radar 项目规范

## 项目定位

A股行情研究网站：每日追踪大盘指数、板块/行业涨跌、资金流向、个股行情。本地运行，FastAPI + Jinja2 提供 Web 界面。

## 目录结构

```
stock-radar/
├── CLAUDE.md              # 项目规范（本文件）
├── ROADMAP.md             # 项目进度与待办
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
│       └── market.py      # 市场情绪（涨跌家数、龙虎榜）
├── api/
│   ├── routes_overview.py # GET /api/indices /api/flow/* /api/market/* /api/zt
│   ├── routes_boards.py   # GET /api/boards /api/boards/{type}/{name}/*
│   ├── routes_stocks.py   # GET/POST/DELETE /api/stocks/* /api/stocks/etf/* /api/stocks/{code}/kline
│   ├── routes_news.py     # GET /api/news/announcements /api/news/research
│   └── routes_leaders.py  # GET /api/leaders
└── templates/
    ├── base.html          # Bootstrap 5 Navbar（时钟 yyyy-mm-dd hh:mm:ss）+ 布局骨架 + 口令弹框 + K线弹框（全局）
    ├── overview.html      # 首页：指数卡片 + 市场情绪面板（涨跌家数/成交额/近60日历史图）+ 热力图 + 资金 + 涨停 + 龙虎榜
    ├── boards.html        # 板块列表（概念/行业 Tab）
    ├── board_detail.html  # 板块详情 + K 线（30/90/180/365日切换）+ 构成股
    ├── stocks.html        # 个股持仓 + 搜索
    ├── etf.html           # ETF 持仓 + 搜索
    ├── news.html          # 公告（持仓股/全市场）+ 研究报告，分页10条/页
    └── leaders.html       # 申万一级行业龙头（成交额 TOP5，支持排序）
```

## 数据源详细说明

### 1. 新浪 `hq.sinajs.cn` — 实时行情

**文件**：`fetchers/indices.py`、`fetchers/stocks.py`
**稳定性**：最稳定，无反爬，无需 AKShare

| 函数 | 用途 | 页面 |
|------|------|------|
| `fetch_indices()` | 大盘指数实时行情（价格、涨跌幅、开高低收、量额） | 首页指数卡片、情绪面板两市成交额合算 |
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
| `stock_fund_flow_industry(symbol="即时")` | 行业资金流向排行（净额降序） | 首页行业资金流 TOP10 |
| `stock_fund_flow_individual(stock, market)` | 个股资金流向明细 | 个股详情页（预留） |
| `stock_fund_flow_individual(symbol="即时")` | 全市场个股主力净流入排行（不区分超大单/散户） | 个股页主力资金面板 |
| `stock_board_industry_index_ths(symbol, start_date, end_date)` | 行业板块近 N 日 K 线 | 板块详情页 K 线图 |
| `stock_board_concept_index_ths(symbol, start_date, end_date)` | 概念板块近 N 日 K 线 | 板块详情页 K 线图 |

**注意**：
- 概念板块无"上涨/下跌家数"字段（THS 接口限制），板块列表中该列显示 `-`
- THS K 线函数无 `period` 参数，只返回日K；月K/年K 需在 Python 侧对日K做 resample

---

### 4. AKShare 东方财富（East Money） — 涨停/龙虎榜/构成股

**文件**：`fetchers/flow.py`、`fetchers/boards.py`、`fetchers/market.py`
**注意**：东方财富 `push2.eastmoney.com` 在当前网络环境被代理封锁，板块构成股已改用 THS HTML 接口替代

| AKShare 函数 | 用途 | 页面 | 网络依赖 |
|-------------|------|------|---------|
| `stock_zt_pool_em(date)` | 涨停板（连板数、封板资金、炸板次数、所属行业） | 首页涨停板 | 是 |
| `stock_board_concept_cons_em(symbol)` | 概念板块构成股行情 | 板块详情构成股表 | **易被封** |
| `stock_board_industry_cons_em(symbol)` | 行业板块构成股行情 | 板块详情构成股表 | **易被封** |
| `stock_lhb_detail_em(start_date, end_date)` | 今日龙虎榜 | 首页龙虎榜 | 是 |

**龙虎榜注意事项**：
- **必须传日期参数**：`start_date` 和 `end_date` 默认值硬编码为 2023 年，不传参会取旧数据
- 同一股票可能有多行（多个上榜原因），需按代码去重并合并原因
- 返回字段：`code`、`name`、`price`、`change_pct`、`net_buy`、`turnover`、`free_mkt_cap`

---

### 5. 新浪 `CN_MarketDataService` — 个股/ETF K 线

**文件**：`fetchers/stocks.py` → `fetch_stock_kline(code, period)`
**URL**：`https://quotes.sina.cn/cn/api/jsonp_v2.php/var%20_x=/CN_MarketDataService.getKLineData`
**稳定性**：稳定，无反爬，不走 push2.eastmoney.com

| period | scale | datalen | 说明 |
|--------|-------|---------|------|
| `intraday` | 1 | 300 | 1 分钟 K 线，过滤到最新交易日 09:30–15:00 |
| `daily` | 240 | 250 | 日 K，约 1 年 |
| `monthly` | 240 | 1500 | 拉取日线，Python pandas resample 到月 |
| `yearly` | 240 | 1800 | 拉取日线，Python pandas resample 到年 |

**注意**：
- Sina API `datalen` 上限约 1800，超过返回 null
- 月K/年K 由日线 resample 合成，`pandas.resample('ME'/'YE')`，旧版 pandas 降级用 `'M'/'Y'`
- 分时仅展示最新交易日数据（取 `items` 中 `day` 字段最大日期），过滤时间范围 `09:30 ≤ t ≤ 15:00`
- 路由：`GET /api/stocks/{code}/kline?period=` 和 `GET /api/stocks/etf/{code}/kline?period=`
- 缓存 TTL：intraday=60s，daily=300s，monthly/yearly=3600s；key 含日期（intraday 除外）

---

### 6. 新浪全量行情 — 市场情绪（涨跌家数）

**文件**：`fetchers/market.py` → `fetch_market_breadth()`
**数据源**：AKShare `stock_zh_a_spot()`，底层为新浪 A 股全量接口，与 `hq.sinajs.cn` 同源
**注意**：拉取全量 ~5500 支股票耗时约 20 秒，路由缓存 TTL 设为 300 秒（5 分钟）

| 字段 | 说明 |
|------|------|
| `up` / `down` / `flat` | 涨/跌/平盘家数（过滤停牌股，即成交量=0） |
| `zt` / `dt` | 涨停/跌停家数（按板块阈值精确判断） |
| `activity` | 活跃度：(涨+跌)/全量 × 100% |
| `total` | 有效股票数（停牌后） |

**涨跌停阈值（按板块）**：

| 板块 | 代码特征 | 阈值 |
|------|---------|------|
| 科创板 | 688xxx | ±20% |
| 创业板 | 300xxx / 301xxx | ±20% |
| 北交所 | 83xxxx / 87xxxx / 43xxxx | ±30% |
| ST 股 | 名称含 ST | ±5% |
| 主板（其余） | — | ±10% |

> 历史原因：曾用 `stock_market_activity_legu()`（乐咕乐股），数据偏少已废弃。北向资金模块因东财数据自 2024-08 起断档已整体移除。个股/ETF K 线曾尝试东财 `stock_zh_a_hist`（push2 被封），已改用新浪 `CN_MarketDataService`。

---

### 数据源对照速查

| 功能 | 数据源 | AKShare 函数 / URL |
|------|--------|-------------------|
| 大盘指数实时 | 新浪 hq | `hq.sinajs.cn/list=sh000001,...` |
| 个股/ETF 实时行情 | 新浪 hq | `hq.sinajs.cn/list=sh600519,...` |
| 个股/ETF 名称搜索 | 新浪 suggest | `suggest3.sinajs.cn/suggest/type=11/22` |
| 个股/ETF K 线（分时/日/月/年） | 新浪 CN_MarketDataService | `quotes.sina.cn/.../CN_MarketDataService.getKLineData` |
| 概念板块列表 | THS | `stock_fund_flow_concept(symbol="即时")` |
| 行业板块列表 | THS | `stock_board_industry_summary_ths()` |
| 行业资金流向 | THS | `stock_fund_flow_industry(symbol="即时")` |
| 个股资金流向（明细） | THS | `stock_fund_flow_individual(stock, market)` |
| 个股主力净流入排行 | THS | `stock_fund_flow_individual(symbol="即时")` |
| 板块 K 线（日K/月K/年K） | THS | `stock_board_industry/concept_index_ths()`；月K/年K 由 Python pandas resample 日线合成（1500/1800日）|
| ETF 规模/折溢价率 | 东方财富 | `fund_etf_spot_em()`；字段：`总市值`（÷1e8=亿元）、`基金折价率`（%，正为折价）；30分钟缓存 |
| 涨停板 | 东方财富 | `stock_zt_pool_em()` |
| 板块构成股 | THS HTML | `q.10jqka.com.cn/thshy/detail/code/{code}/`（行业）/ `gn/detail/code/{code}/`（概念）；解析涨跌幅前20只；板块代码通过 `stock_board_industry/concept_name_ths()` 获取，24h模块缓存 |
| 龙虎榜 | 东方财富 | `stock_lhb_detail_em(start_date, end_date)`（必传日期） |
| 市场情绪（涨跌家数） | 新浪（via AKShare） | `stock_zh_a_spot()` |
| A股公告（持仓股当日） | 东方财富 | `stock_individual_notice_report(security, symbol, begin_date, end_date)`；空结果时 AKShare 内部报 KeyError，已 try/except 兜底 |
| A股公告（全市场当日） | 东方财富 | `stock_notice_report(symbol="全部", date)`；symbol 为公告类型非股票代码；全量约 1000-2000 条/天，5-15 秒，30 分钟缓存 |
| 个股研报 | 东方财富 | `stock_research_report_em(symbol)`；返回字段：股票简称/报告名称/东财评级/机构/日期/报告PDF链接；无目标价 |
| 申万一级行业成分 | 申万 | `sw_index_first_info()` 返回行业代码（格式 `801010.SI`，去掉 `.SI` 后传入 `index_stock_cons()`）；31 个一级行业映射 24h 模块缓存 |
| 申万二级行业成分 | 申万 | `sw_index_second_info()` 同格式，约 100 个二级行业；`index_stock_cons()` 复用；映射 24h 模块缓存 |
| 申万行业实时指数 | 申万 | `index_realtime_sw(symbol='一级行业')` 或 `symbol='二级行业'`；字段：指数代码/昨收盘/最新价，涨跌幅需 Python 自算；指数代码为纯数字（无 `.SI`） |
| 全量 A 股成交额（行业龙头排名） | 新浪（via AKShare） | `stock_zh_a_spot()`；代码格式 `sh600519`，取后6位得纯数字代码；按成交额排名取各行业 TOP5 |
| 全A市场PE历史分位 + 股债比价（ERP） | 乐咕乐股 | `stock_index_pe_lg()`；返回 2005 至今日频全A市盈率（等权/静态/滚动，3类×中位数变体）；用于计算历史百分位；与 `bond_zh_us_rate()` 合算 ERP = (1/PE)×100 − 10年国债收益率；文件：`data/fetchers/market_state.py` |
| 10年期国债收益率 | 宏观（via AKShare） | `bond_zh_us_rate(start_date='YYYYMMDD')`；字段：`中国国债收益率10年`；与 PE倒数合算 ERP；文件：`data/fetchers/market_state.py` |
| 两融余额历史趋势 | 证券交易所（via AKShare） | `stock_margin_account_info()`；无参；返回全市场日频 融资余额/融券余额/融资买入额（亿元）；2013至今，约3300+行；文件：`data/fetchers/market_state.py` |

---

## 缓存机制

**内存缓存**（`data/cache.py` → `get_cached`）：
- TTL 5 分钟（板块/资金）/ 5 分钟（市场情绪，耗时长）
- **error 响应不缓存**：若 fetcher 返回 `[{"error": "..."}]`，不写入 `_mem`，下次请求重新拉取

**SQLite 日快照**（`board_snapshot` 表）：
- 由 APScheduler 在 16:35 写入，用于盘后快速加载
- 路由读取快照时若发现含 `error` 字段，跳过快照回退到实时拉取
- 调度器写入前校验：`rows` 非空且 `rows[0]` 不含 `error` 才写库

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
python -c "from data.fetchers.market import fetch_lhb_today; import json; print(json.dumps(fetch_lhb_today(), ensure_ascii=False, indent=2))"
python -c "from data.fetchers.stocks import search_etf; import json; print(json.dumps(search_etf('沪深300'), ensure_ascii=False, indent=2))"
```

## 禁止事项

- 不把密钥写进任何代码文件
- 不在未验证的情况下修改缓存逻辑（容易导致数据不刷新）
- 不添加未在计划中的功能（先跑通再扩展）
- 新增数据源前先在「数据源详细说明」章节补充文档，再写代码
- 调用 `stock_lhb_detail_em` 时必须传 `start_date` 和 `end_date`，禁止使用默认参数
- 深色主题下 `<select>` 的 `<option>` 必须同时设 `[data-theme="dark"] option { background:#111827; color:#e0e8f0; }` 和 `color-scheme:dark`，否则 Windows Chrome 下选项不可见
- 导航栏时钟格式：`now.toLocaleString('sv-SE', { timeZone:'Asia/Shanghai' })`，输出 `yyyy-mm-dd hh:mm:ss`
