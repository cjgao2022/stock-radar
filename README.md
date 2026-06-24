# Stock-Radar

A股行情研究本地网站。每日追踪大盘情绪、板块涨跌、资金流向、个股与 ETF 行情。

## 功能概览

| 页面 | 内容 |
|------|------|
| **大盘** | 指数卡片（6只）、市场情绪面板（上涨/涨停/平盘/下跌/跌停/两市成交额 + 近60日涨停历史图）、板块热力图（概念/行业切换）、行业资金流 TOP10、连板梯队追踪、龙虎榜（支持历史日期切换） |
| **板块** | 概念/行业双 Tab，涨跌幅 + 领涨股 + 净流入，可排序 |
| **板块详情** | K 线图（30/90/180/365 日切换）+ 板块5日动量色块 + 构成股行情表 |
| **个股** | 持仓列表（成本价/盈亏/量比）+ K 线弹框（分时/日K/月K/年K）+ 名称/代码搜索 + 主力资金排行 |
| **ETF** | 持仓列表（成本价/盈亏/量比）+ K 线弹框（分时/日K/月K/年K）+ 名称/代码搜索 |
| **资讯** | A 股公告（持仓股/全市场 Tab，按类型筛选）+ 研究报告（东方财富，支持按持仓股筛选），分页10条/页 |
| **龙头** | 申万一级行业（31个）成交额 TOP5 龙头股，支持按行业涨跌幅/成交额/名称排序，点击代码弹 K 线 |

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
| 申万行业成分 + 实时指数 | 申万 `sw_index_first_info` / `index_stock_cons` / `index_realtime_sw` |

## 快速开始

**环境要求**：Python 3.11+

```bash
# 安装依赖
pip install -r requirements.txt

# 启动
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

浏览器访问 `http://127.0.0.1:8000`

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
│       ├── flow.py        # 资金流向
│       └── market.py      # 市场情绪、龙虎榜
├── api/
│   ├── routes_overview.py
│   ├── routes_boards.py
│   ├── routes_stocks.py
│   ├── routes_news.py     # 公告 + 研报
│   └── routes_leaders.py  # 行业龙头
├── templates/
│   ├── base.html          # 全局布局 + K 线弹框（个股/ETF 共用）
│   ├── overview.html
│   ├── boards.html
│   ├── board_detail.html
│   ├── stocks.html
│   ├── etf.html
│   ├── news.html          # 公告 + 研报
│   └── leaders.html       # 行业龙头
└── db/
    └── snapshot.db        # SQLite 日快照（运行时生成）
```

## 注意事项

- 东方财富 `push2.eastmoney.com` 在部分网络环境下不可达，板块详情构成股会提示切换网络；个股/ETF K 线已改用新浪接口规避
- 调用 `stock_lhb_detail_em` 必须传 `start_date`/`end_date`，默认参数硬编码为 2023 年旧数据
- 市场情绪历史（近60日）首次使用需点击「补齐历史」按钮回填，此后每日盘后自动快照；历史数据仅有涨停数，上涨/下跌家数只从当日起实时积累
- 密钥/token 通过 `.env` 管理，不进代码和提交
- 所有时间展示使用中国北京时间（UTC+8）
