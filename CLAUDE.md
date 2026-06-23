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
│   └── fetchers/
│       ├── indices.py     # 新浪实时指数
│       ├── boards.py      # AKShare 板块/行业列表 + 构成股（东方财富）
│       ├── stocks.py      # 新浪 batch 个股行情
│       └── flow.py        # 同花顺资金流向（行业/概念/个股/热门）
├── api/
│   ├── routes_overview.py # GET /api/indices, /api/flow/market, /api/zt
│   ├── routes_boards.py   # GET /api/boards, /api/boards/{type}/{code}/constituents
│   └── routes_stocks.py   # GET /api/stocks/search, /api/stocks/hot
└── templates/
    ├── base.html          # Bootstrap 5 Navbar + 布局骨架
    ├── overview.html      # 首页：指数卡片 + 板块热力图 + 资金流向摘要
    ├── boards.html        # 板块列表（概念/行业 Tab）
    ├── board_detail.html  # 板块详情 + 构成股
    └── stocks.html        # 自选股 + 个股搜索
```

## 数据源分层

| 层级 | 数据源 | 用途 |
|------|--------|------|
| 基础行情 | 新浪 `hq.sinajs.cn` | 指数实时、个股批量（最稳定，无反爬） |
| 板块列表 | AKShare（东方财富） | 概念/行业板块列表、构成股 |
| 分析数据 | **同花顺（THS）** | 资金流向、板块资金排行、热门排行（THS 独有价值） |
| 补充 | 东方财富 | 大盘资金、涨停板（THS 无等价 AKShare 接口） |

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
- 所有时间以北京时间（UTC+8）为准

## 验证方式

```bash
# 启动开发服务器
uvicorn main:app --reload --host 127.0.0.1 --port 8000

# 单独测试 fetcher
python -c "from data.fetchers.indices import fetch_indices; import json; print(json.dumps(fetch_indices(), ensure_ascii=False, indent=2))"
python -c "from data.fetchers.flow import fetch_industry_flow; import json; print(json.dumps(fetch_industry_flow(), ensure_ascii=False, indent=2))"
```

## 禁止事项

- 不把密钥写进任何代码文件
- 不在未验证的情况下修改缓存逻辑（容易导致数据不刷新）
- 不添加未在计划中的功能（先跑通再扩展）
