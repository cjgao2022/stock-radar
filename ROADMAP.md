# Stock-Radar ROADMAP

## 项目状态

本地运行，FastAPI + Jinja2，数据源：新浪行情 + AKShare（THS/东方财富）。

最近验证：2026-06-24（板块月K/年K、ETF规模折溢价、板块成交额趋势图、市场估值温度、两融余额趋势）

---

## 已完成

### 基础架构
- [x] FastAPI + Jinja2 + SQLite 项目骨架
- [x] APScheduler 盘后自动刷新板块快照（16:35）
- [x] 内存 TTL 缓存（5 分钟）+ SQLite 日快照持久化
- [x] 全局 `threading.Lock`（`_AK_LOCK`）序列化 AKShare 调用，解决 py_mini_racer 并发崩溃
- [x] `get_cached` 不缓存 error 响应，避免错误结果污染内存缓存
- [x] 板块路由跳过含 error 的 SQLite 日快照，回退到实时拉取

### 数据源
- [x] 新浪 `hq.sinajs.cn` 实时行情（指数、个股、ETF）
- [x] 新浪 suggest API 模糊搜索（type=11 个股 / type=22 ETF），名称完整不截断
- [x] AKShare `stock_fund_flow_concept(symbol='即时')`（THS 概念资金流，含领涨股）
- [x] AKShare `stock_board_industry_summary_ths()`（THS 行业板块汇总，含上涨/下跌家数）
- [x] AKShare `stock_zt_pool_em`（东方财富涨停板，含连板数）
- [x] AKShare `stock_lhb_detail_em(start_date, end_date)`（今日龙虎榜，必须传日期参数，默认参数为 2023 年旧数据）
- [x] AKShare `stock_zh_a_spot()`（新浪全量行情，用于市场情绪涨跌家数统计，耗时约 20 秒）

### 市场情绪
- [x] 按板块使用正确涨跌停阈值：科创/创业板 ±20%，北交所 ±30%，ST ±5%，主板 ±10%
- [x] 过滤停牌股（成交量 = 0），避免误计为平盘
- [x] 活跃度字段（(涨+跌)/total × 100%）
- [x] 涨% / 跌% 标签使用 up/(up+dn) 计算，确保两者相加为 100%

### 页面功能
- [x] **大盘首页**：指数卡片、市场情绪面板（涨跌家数 + 两市成交额 + 近60日历史图）、板块热力图、行业资金流 TOP10、连板梯队、龙虎榜
- [x] **板块热力图**：色块大小按涨跌幅绝对值排列，tooltip 正确显示涨跌幅（修正了 value/rawValue 混用 bug）
- [x] **板块页**：概念/行业双 Tab，涨跌幅 + 领涨股，净流入列，可排序
- [x] **板块详情**：K 线图支持 30/90/180/365 日 + 月K/年K 切换（`?days=` 或 `?period=monthly/yearly`，月K/年K 由 Python pandas resample 日线合成，1h缓存）；K 线图底部加成交额趋势柱（与 K 线共用数据，按涨跌着色）
- [x] **板块详情**：构成股行情表（网络可达时展示，EM 接口被封时提示切换网络）
- [x] **个股页**：持仓列表（统计卡 + 全宽表格）+ 名称/代码模糊搜索（多结果展示）
- [x] **ETF 页**：持仓列表（统计卡 + 全宽表格）+ 名称/代码模糊搜索（多结果展示）；新增规模(亿元)和折溢价率(%)列，数据源：东方财富 `fund_etf_spot_em`，30分钟缓存
- [x] **个股/ETF K线弹框**：持仓列表行内 K线按钮，点击弹出 ECharts 图；支持分时/日K/月K/年K 四档切换；数据源：新浪 `CN_MarketDataService.getKLineData`（scale=1/240），月K/年K 由 Python pandas resample 日线合成；分时仅展示最新交易日 09:30–15:00 窗口；`base.html` 全局共用弹框
- [x] **首页布局**：今日涨停板 / 今日龙虎榜各占横向 50%（col-lg-6）
- [x] **板块热力图**：名称与涨跌幅水平 + 垂直居中（`position:'inside'` + 纯文本，放弃 rich text 绕过 ECharts treemap verticalAlign 失效问题）

### 龙虎榜
- [x] 传今日日期参数（不传则取 AKShare 硬编码的 2023 年旧数据）
- [x] 同一股票多条上榜原因合并展示（` / ` 分隔），并按代码去重
- [x] 展示字段：代码、名称、涨跌幅、净买额、换手率、流通市值
- [x] **龙虎榜历史切换**：首页 LHB 面板支持日期下拉切换（最近10个交易日），盘后自动快照

### 持仓管理
- [x] 动态持仓存储（`data/watchlist.json`，首次自动从 config.yaml 迁移）
- [x] 加入持仓（搜索结果 / 详情卡均可操作）
- [x] 移除持仓（持仓列表行内 × 按钮）
- [x] 口令确认弹框（操作时输入6位代码确认，防误触）
- [x] 加入时间字段（北京时间 `YYYY-MM-DD HH:MM`）
- [x] **成本价 + 实时盈亏**：个股/ETF 持仓行内 ✏ 按钮设置成本均价+持仓数量；实时显示持仓盈亏%、盈亏金额；持仓总盈亏统计卡

### 行情分析增强
- [x] **K线均线 Toggle**：蜡烛图头部加 MA5/MA10/MA20 切换按钮，点击可显隐对应均线
- [x] **量比列**：个股/ETF 持仓表新增今日量/20日均量比值列，超量用橙/红色标注
- [x] **主力资金净流入排行**：个股页新增面板，使用 THS `stock_individual_fund_flow_rank` 过滤持仓股，显示主力净额/占比/超大单/散户
- [x] **板块5日动量**：板块详情页板块摘要区展示最近5个交易日的涨跌幅色块
- [x] **市场情绪面板**：情绪条与近60日历史图合并为单一面板；左列竖排今日涨跌家数 + 两市合计成交额（从指数数据实时合算）；右侧 ECharts 历史图（涨停折线 + 涨跌柱 + 成交额蓝色面积线，三轴），盘后自动快照（SQLite），支持「补齐历史」一键回填
- [x] **历史图成交额曲线**：`breadth_history` 表新增 `amount` 字段（含 ALTER TABLE 自动迁移）；每次情绪 API 响应及盘后快照均合算沪深两市成交额存库；历史回填数据 amount 为 NULL（折线自动跳过）
- [x] **连板次日追踪**：首页展示昨日2板+涨停股今日表现（继续涨停/回调/触及跌停），从历史快照 + 实时行情合并
- [x] **批量行情接口**：`GET /api/stocks/batch_quotes?codes=` 支持任意代码批量查询

### 搜索体验
- [x] 中文名称整体匹配（防止 Sina suggest 拆字模糊匹配）
- [x] 个股/ETF 类型隔离（个股搜索不返回 ETF，ETF 搜索不返回个股）
- [x] 代码直查名称完整（修正 Sina hq 截断 + suggest `parts[4]` 取完整显示名）
- [x] 查询面板支持清空按钮

### 基本面与宏观研究（P0/P1）
- [x] **个股基本面快照**：持仓表格新增 PE（静态）/ PB / ROE 三列；THS `stock_financial_abstract_ths` 取年报 EPS + 最新季报 BVPS/ROE，PE/PB 由前端用实时价格计算；6h 缓存
- [x] **行业估值扫描**：新增 `/valuation` 页，展示巨潮资讯（证监会行业分类）19 个一级行业 PE 加权/中位数，可展开二级行业，1h 缓存
- [x] **宏观数据面板**：新增 `/macro` 页，展示 CPI 月率 / PPI 年率 / PMI 制造业 / M2 年率近 36 期历史折线图（ECharts 2×2 布局）；PMI 标注 50 荣枯线；24h 缓存；数据源：东方财富宏观日历（AKShare）
- [x] **市场估值温度**：`/macro` 页顶部新增面板，展示全A滚动PE、近5年/10年历史分位（低估/合理/高估 信号灯）、股债利差ERP（PE倒数 - 10年国债收益率）、PE+ERP双轴历史走势图（近5年）；首页情绪面板底部加一行估值状态条（全A PE · 分位 · ERP · 估值区间 · 一键跳转）；数据源：`stock_index_pe_lg()` + `bond_zh_us_rate()`；1h 缓存；文件：`data/fetchers/market_state.py`
- [x] **两融余额趋势**：`/macro` 页新增面板，展示全市场融资余额近120日历史折线 + MA20；顶部显示当前余额、5日变化额/变化率、20日变化额；数据源：`stock_margin_account_info()`；1h 缓存；文件：`data/fetchers/market_state.py`
- [x] **公告 + 研报页**：新增 `/news` 页；公告分持仓股/全市场 Tab，支持按公告类型筛选，点击标题跳东方财富原文；研报支持按持仓股下拉筛选，PDF 链接可直接打开；数据源：东方财富 `stock_individual_notice_report` / `stock_notice_report` / `stock_research_report_em`；公告 30 分钟缓存，研报 1 小时缓存
- [x] **行业龙头页**：新增 `/leaders` 页，申万一级行业（31个）每行业展示成交额 TOP5 龙头股；排序支持行业涨跌幅/成交额/名称；点击股票代码弹 K 线；数据源：`sw_index_first_info` + `index_stock_cons` × 31 + `stock_zh_a_spot`；行业成分股映射 24h 模块缓存，整体结果 30 分钟路由缓存；首次加载约 60s，之后命中缓存秒级响应
- [x] **二级行业龙头**：同页面 Tab 切换（一级行业 / 二级行业），点击二级 Tab 时懒加载；申万二级行业（约 100 个）每行业展示成交额 TOP5；数据源：`sw_index_second_info` + `index_stock_cons` × ~100 + `stock_zh_a_spot`；行业成分股映射 24h 模块缓存，路由 30 分钟缓存；首次约 2-3 分钟，之后命中缓存秒级响应

### 设计系统
- [x] 全站统一设计系统（CSS 变量、`panel`/`stat-card`/`chg-badge`/`data-table` 组件）
- [x] 深色 / 亮色双主题（localStorage 持久化）
- [x] 深色渐变导航栏，实时时钟（`yyyy-mm-dd hh:mm:ss` 北京时间，`sv-SE` locale），当前页高亮
- [x] 红涨绿跌配色，数字等宽字体（tabular-nums）
- [x] 所有时间展示强制使用北京时间（`timeZone:'Asia/Shanghai'`）
- [x] 深色主题 `<select>` option 可见性修复：`color-scheme:dark` + `option { background:#111827; color:#e0e8f0 }`

---

## 已移除功能

| 功能 | 原因 |
|------|------|
| 北向资金（沪深港通） | 东方财富 `成交净买额` 数据自 2024-08 起全部断档（NaN/null），AKShare 所有 hsgt 接口均受影响，无可用替代数据源 |
| 事件日历（`/calendar`） | 解禁接口走东方财富 push2（被代理封锁），宏观日历因 AKShare 数据截止 2025-08 为空，三块内容均无法展示，已整体移除 |

---

## 已知问题

| 问题 | 状态 |
|------|------|
| 东方财富 `push2.eastmoney.com` 在当前网络被代理封锁 | 板块构成股接口受影响，提示用户切换网络；板块 K 线已改用 THS 接口规避；个股/ETF K 线已改用新浪 `CN_MarketDataService` 接口规避 |
| AKShare 宏观数据截止 2025-08 | `macro_china_cpi_monthly` 等 4 个函数数据仅到 2025-08；属 AKShare 数据源更新滞后，历史趋势图仍有参考价值 |
| 概念板块无上涨/下跌家数 | THS 概念接口不提供该字段，显示 `-`，属接口限制 |
| 板块 K 线仅有日 K | THS 接口无 period 参数，东财月K接口走 push2 被封；当前以拉取日数据（最多365日）代替 |

---

## 待办

- [ ] 移动端布局优化（当前在手机上表格较拥挤）

---

## 已调研不可实现的需求

| 需求 | 原因 |
|------|------|
| 持仓股解禁预警 | AKShare `stock_restricted_release_queue_em/sina` 数据截止 2020 年，无未来解禁日历数据 |
| 高管/大股东增减持 | `stock_hold_num_cninfo` 接口参数已变更，`stock_zh_a_alerts_cls` 函数不存在，暂无可用接口 |
| 定增/配股事件 | AKShare 无稳定接口 |
