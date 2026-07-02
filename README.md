# Stock-Radar

A股行情研究本地网站。每日追踪大盘情绪、板块涨跌、资金流向、个股与 ETF 行情。

## 功能概览

导航按「从宏观到微观」分组：**大盘 ｜ 宏观 · 估值 ｜ 板块 · 龙头 ｜ 个股 · ETF · 资讯**。每页顶部有统一页面头（标题 + 用途副标题）。

| 页面 | 内容 |
|------|------|
| **大盘** | 指数卡片、市场情绪面板（涨跌家数/涨停跌停/**涨跌停比**/两市成交额 + 近60日历史图 + 全A估值状态条）、板块热力图（概念/行业切换）、行业资金流 TOP10、连板梯队 + **涨停行业分布**（主线代理）、龙虎榜（含**上榜原因**、历史日期切换）、连板次日追踪（含**晋级率**） |
| **宏观** | 市场估值温度（全A滚动PE + 近5/10年分位 + 股债利差 ERP + 10年国债 + **全A股息率**）、CPI/PPI/PMI/M2 历史图、融资余额趋势（含**5日日均买入**） |
| **估值** | 证监会行业分类 PE 加权/中位数 + 高低估分档，支持一级/二级行业展开、多列排序 |
| **板块** | 概念/行业双 Tab（涨跌幅 + 领涨股 + 净流入，可排序）+ 行业轮动（5/20/60日累计涨跌）+ 概览统计条 |
| **板块详情** | K 线图（30/90/180/365 日 + 月K/年K 切换）+ 成交额趋势 + 板块5日动量 + 构成股行情表 |
| **龙头** | 申万一级/二级行业成交额 TOP5 龙头股，按行业涨跌幅/成交额/名称排序，点击代码弹 K 线 |
| **个股** | 持仓列表（现价/盈亏/量比/PE静/PB/ROE/**利润增速**）+ K 线弹框 + 名称代码搜索 + 主力资金排行 |
| **个股详情** | 顶部信息栏（含 **PE(TTM)/PB 近1年估值分位** + 分档）、K 线（分时/日/周/月/年 + MA + MACD/KDJ/RSI）、个股资金流、财务趋势图（ROE/利润增速/营收增速） |
| **ETF** | 持仓列表（现价/盈亏/量比/规模/折溢价）+ K 线弹框 + 名称代码搜索 |
| **资讯** | A 股公告（持仓股/全市场 Tab，按类型筛选）+ 研究报告（评级/机构，支持按持仓股筛选），分页10条/页 |

## 数据源

| 数据 | 来源 |
|------|------|
| 实时行情（指数/个股/ETF） | 新浪 `hq.sinajs.cn` |
| 名称搜索 | 新浪 suggest API |
| 个股/ETF K 线（分时/日/月/年） | 新浪 `CN_MarketDataService.getKLineData` |
| 概念板块资金流 | AKShare THS `stock_fund_flow_concept` |
| 行业板块汇总 | AKShare THS `stock_board_industry_summary_ths` |
| 板块 K 线（日K） | AKShare THS `stock_board_industry/concept_index_ths` |
| 涨停板 | AKShare 东方财富 `stock_zt_pool_em` |
| 龙虎榜 | AKShare 东方财富 `stock_lhb_detail_em`（必传日期） |
| 市场情绪（涨跌家数） | AKShare 新浪 `stock_zh_a_spot` |
| A 股公告 | 东方财富 `stock_individual_notice_report` / `stock_notice_report` |
| 研究报告 | 东方财富 `stock_research_report_em` |
| 申万行业成分 + 实时指数 | 申万 `sw_index_first_info` / `sw_index_second_info` / `index_stock_cons` / `index_realtime_sw` |
| 个股基本面（EPS/BVPS/ROE/利润增速） | THS `stock_financial_abstract_ths` |
| 个股估值分位（PE-TTM/PB 近1年） | 百度股市通 `stock_zh_valuation_baidu`（非 push2，代理封锁下可用） |
| 全A市场估值温度（PE分位 + ERP + 股息率） | 乐咕乐股 `stock_index_pe_lg` / `stock_a_gxl_lg` + 宏观 `bond_zh_us_rate` |
| 两融余额趋势 | 交易所 `stock_margin_account_info` |
| 行业估值（PE 加权/中位数） | 巨潮 `stock_industry_pe_ratio_cninfo` |
| 宏观指标（CPI/PPI/PMI/M2） | 东方财富宏观日历 |
| ETF 规模/折溢价 | 东方财富 `fund_etf_spot_em` |

## 快速开始

**环境要求**：Python 3.11+（已在 3.14 验证）

一键启动（首次自动建虚拟环境并装依赖）：

```bash
./start.sh
```

或手动：

```bash
python3 -m venv .venv
source .venv/bin/activate          # 每次新开终端启动前都要先执行
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

浏览器访问 `http://127.0.0.1:8000`

> **注意**：Python 3.12+ 的 venv 默认不预装 setuptools，而 akshare 的传递依赖 `jsonpath` 是 setup.py 老式包、构建时需要它，因此 `requirements.txt` 顶部显式声明了 `setuptools`/`wheel`。

## 配置

编辑 `config.yaml` 设置关注指数和初始自选股/ETF：

```yaml
indices:
  - code: "sh000001"
    name: "上证指数"

watchlist:
  - code: "600519"
    name: "贵州茅台"

etf_watchlist:
  - code: "510300"
    name: "沪深300ETF"
    type: "宽基"
```

自选股/ETF 在页面上加入/移除后，持仓数据保存至 `data/watchlist.json`（自动从 config.yaml 迁移初始数据）。

## 目录结构

```
stock-radar/
├── start.sh               # 一键启动（首次自动建 venv + 装依赖）
├── main.py                # FastAPI 入口 + 调度器
├── config.yaml            # 关注指数、初始自选股/ETF、缓存配置
├── requirements.txt
├── data/
│   ├── watchlist.json     # 动态持仓（运行时生成）
│   ├── cache.py           # 内存 TTL 缓存 + SQLite 初始化
│   ├── scheduler.py       # 盘后快照任务（16:35）
│   ├── watchlist_store.py # 持仓增删存储
│   └── fetchers/
│       ├── indices.py     # 指数行情
│       ├── boards.py      # 板块列表 + 构成股 + K 线
│       ├── stocks.py      # 个股/ETF 行情、搜索、K 线
│       ├── flow.py        # 资金流向、涨停板
│       ├── market.py      # 市场情绪、龙虎榜
│       ├── fundamentals.py    # 个股基本面 + 财务趋势（THS）
│       ├── valuation_stock.py # 个股 PE(TTM)/PB 历史分位（百度）
│       ├── valuation.py       # 行业估值（巨潮）
│       ├── market_state.py    # 市场估值温度 + 股息率 + 两融
│       ├── macro.py           # 宏观指标 + 日历
│       ├── news.py            # 公告 + 研报
│       └── leaders.py         # 申万行业龙头
├── api/
│   ├── routes_overview.py
│   ├── routes_boards.py
│   ├── routes_stocks.py   # 含 /{code}/valuation 估值分位
│   ├── routes_news.py     # 公告 + 研报
│   ├── routes_leaders.py  # 行业龙头
│   ├── routes_valuation.py # 行业估值
│   └── routes_macro.py    # 宏观 + 估值温度 + 两融
├── templates/
│   ├── base.html          # 全局布局 + 页面头 + K 线弹框（个股/ETF 共用）
│   ├── overview.html      # 大盘
│   ├── boards.html / board_detail.html
│   ├── stocks.html / stock_detail.html / etf.html
│   ├── valuation.html     # 行业估值
│   ├── macro.html         # 宏观 + 估值温度
│   ├── news.html          # 公告 + 研报
│   └── leaders.html       # 行业龙头
├── static/
│   └── vendor/            # echarts / bootstrap 本地化（规避 CDN 被代理拦截）
└── db/
    └── snapshot.db        # SQLite 日快照（运行时生成）
```

## 注意事项

- 东方财富 `push2.eastmoney.com` 在部分网络环境下不可达，板块详情构成股会提示切换网络；个股/ETF K 线已改用新浪接口规避
- 调用 `stock_lhb_detail_em` 必须传 `start_date`/`end_date`，默认参数硬编码为 2023 年旧数据
- 市场情绪历史（近60日）首次使用需点击「补齐历史」按钮回填，此后每日盘后自动快照；历史数据仅有涨停数，上涨/下跌家数只从当日起实时积累
- 前端 echarts/bootstrap 已本地化到 `static/vendor/`，规避系统代理（如 Clash）拦截 CDN 返回 HTML 导致的白屏；勿改回 CDN 引用
- 个股估值分位走百度股市通、板块 K 线走 THS、个股 K 线走新浪，均为规避东方财富 push2 封锁的替代源
- 密钥/token 通过 `.env` 管理，不进代码和提交
- 所有时间展示使用中国北京时间（UTC+8）
