# 代码审查问题清单（2026-07-03 全面体检）

三路并行代码审查（数据层/API 层/前端模板）+ 人工验证的结果。按严重程度排列，修复后移入 ROADMAP「已完成」。

> **P0/P1 已全部修复并验证，详见 `ROADMAP.md` →「代码审查修复（2026-07-03）」。** 本文件保留作记录，P2 仍待单独立项。

总体结论：架构与设计系统成熟（数据源选型绕开被封接口、双层缓存思路正确、红涨绿跌全站一致、导航分组合理），功能基本无冗余；但存在 3 个已实锤严重 bug + 1 个安全问题。

---

## P0 严重（已实锤，待修复）

### P0-1 板块快照从未写入成功 → 行业轮动功能实际不可用
- 位置：`data/cache.py:108-117`、`data/fetchers/boards.py:74,95`、`data/scheduler.py`
- `save_board_snapshot` 用命名参数 `:code/:turnover_rate/:up_count/:down_count`，但概念板块记录缺 `code/turnover_rate/up_count/down_count`，行业板块缺 `code/turnover_rate`。`executemany` 命名绑定缺键必抛 `sqlite3.ProgrammingError`，调度器无捕获。
- **已验证**：`db/snapshot.db` 的 `board_snapshot` 表为 0 行。`/api/boards/rotation` 永远返回空。
- 修法：save 层对缺失字段兜底（`code` 缺失时用 `name` 替代主键）；scheduler 写入处加 try/except 日志。

### P0-2 dict 型 error 响应污染内存缓存
- 位置：`data/cache.py:21`
- `get_cached` 只跳过「list 且首元素含 error」的错误；`fetch_stock_fundamental/valuation/kline/market_breadth/market_valuation/margin_trend` 等失败时返回 `{"error":...}` dict，被当正常数据缓存（基本面/估值 6 小时、宏观 1 小时、情绪 5 分钟）。一次瞬时失败让页面持续报错数小时。
- `api/routes_stocks.py:178` 注释「error 响应不缓存」与实际行为矛盾。
- 修法：`get_cached` 增加 `isinstance(data, dict) and "error" in data` 也跳过缓存。

### P0-3 watchlist.json 解析失败静默覆盖用户持仓数据
- 位置：`data/watchlist_store.py:21-40, 43-44`
- `_load` 中 JSON 解析异常被吞 → 回退 config.yaml 迁移 → `_save` 直接覆盖原文件，手工录入的成本价/持仓数量全部丢失且无告警。`_save` 非原子写入（直接 `write_text`），进程中途崩溃产生截断文件即触发此路径。
- 修法：`_save` 改临时文件 + `os.replace` 原子替换；`_load` 解析失败先备份损坏文件（`watchlist.json.corrupt-<ts>`）再迁移并告警。

### P0-4 news 页 XSS（第三方数据注入）
- 位置：`templates/news.html:253-264, 312-324`、`templates/overview.html:594-597`
- 东财公告标题/研报名称/机构名/`d.url` 直接拼 `innerHTML` 未转义，第三方数据含 HTML 即可注入执行；`d.url` 未转义可从 `href` 属性逃逸。龙虎榜 reason 仅去引号未转义 `<`。
- 修法：`base.html` 加全局 `escHtml()`（转义 `&<>"'`），第三方文本与 URL 统一走它。

---

## P1 高价值（待修复）

### P1-1 时区不一致
- `api/routes_stocks.py`、`routes_news.py`、`routes_leaders.py`、`routes_valuation.py`、`routes_macro.py` 用 `date.today()`（服务器本地时区），与 `routes_overview.py`/`routes_boards.py` 的北京时区 `_today()` 不一致。服务器非 UTC+8 时「今天」和缓存 key 日期跨模块错乱。
- `templates/base.html:556-566`：开盘状态判断用浏览器本地时区 `getHours()`，设备不在 CST 时状态灯错误。
- 修法：抽公共北京时区 `_today()` 各路由统一引用；base.html 从 Shanghai 格式化字符串取时分。

### P1-2 连板判断 9.9% 阈值误判 20cm 标的
- 位置：`templates/overview.html:654-658, 674`
- `chgPct>=9.9` 判「继续涨停」，创业板/科创板标的涨 10%~19%（未涨停）被误判，晋级率虚高。对打板研究是实质性口径错误。
- 修法：按代码前缀取阈值（688/30x→19.9，8x/4x/920→29.9，其余 9.9），与后端 `market.py` 板块阈值口径一致。

### P1-3 北交所资金流交易所误判
- 位置：`api/routes_stocks.py:209`
- `"sh" if code.startswith(("6","9")) else "sz"`，北交所（4/8/920 开头）被误判为 sz。且与 `data/fetchers/stocks.py:17` 已有 `_market` 助手逻辑分叉。
- 修法：复用 `_market` 并覆盖北交所。

### P1-4 核心面板 fetch 无 .catch，失败永久停「加载中」
- 位置：`overview.html:350/441/471/510/524/607`、`stock_detail.html:133/155/172`、`board_detail.html:244`、`stocks.html:750`
- 请求失败对应区域永远显示 `--` 或「加载中...」，无任何提示。boards/leaders/macro/news 的主请求有 catch，是正确写法。
- 修法：统一补 `.catch` 显示「加载失败」。

### P1-5 board_detail 无数据时 innerHTML 覆盖 ECharts 容器
- 位置：`templates/board_detail.html:140-143`
- 无数据时把 ECharts 的 canvas DOM 整体替换为文本，此后切换周期图表不再渲染。
- 修法：改用 `graphic` 文本占位（与 `base.html:713-716` 弹框写法一致）。

---

## P2 遗留（记录在案，单独立项）

### 后端 / 存储
- [x] ~~全局 `_AK_LOCK` 粒度过粗~~（2026-07-03 已修复，见 ROADMAP）
- [x] ~~`get_cached` 无锁无 single-flight~~（2026-07-03 已修复，见 ROADMAP）
- [x] ~~SQLite 连接从不 close、无 `busy_timeout`~~（2026-07-03 已修复，见 ROADMAP）
- [x] ~~瞬时失败返回 `[]` 被长 TTL 缓存，与「真没数据」无法区分~~（2026-07-03 已修复 macro.py 日历 + news.py 公告/研报三处，见 ROADMAP；market.py LHB 经排查已是正确设计未改动；stocks.py 行情当前无长 TTL 缓存包装，暂不适用）
- [x] ~~`fetch_market_breadth` 缺「名称」列时 ST 判定退化为 False，涨跌停家数偏差~~（2026-07-03 已修复，见 ROADMAP）
- [x] ~~`load_board_rotation` 全表扫描无时间下限，随快照累积变慢~~（2026-07-03 已修复，见 ROADMAP）
- [x] ~~`board_{type}` 实时兜底缓存 key 不带日期，跨日可能短暂读到昨日数据~~（2026-07-03 已修复，见 ROADMAP）
- [x] ~~调度偏移 `+2/+3/+4` 分钟在配置接近午夜时产生非法 `hour=24`~~（2026-07-03 已修复，见 ROADMAP）
- [x] ~~scheduler 全程用 print，应改 logging~~（2026-07-03 已修复，见 ROADMAP）

### API 设计
- [x] ~~`/api/admin/bootstrap_history` 用 GET 触发 60-120s 写操作、无鉴权~~（2026-07-03 已修复，见 ROADMAP；本地单人使用未加鉴权，仅改 GET→POST）
- [x] ~~死接口：`/api/flow/market`、`/api/boards/snapshot`，前端从未调用~~（2026-07-03 已删除，见 ROADMAP）
- 全层无 `HTTPException`，错误一律 HTTP 200 + error 载荷，且 list/dict 两种结构并存（**已评估暂缓**：跨 7 个路由文件 + 30+ 前端消费点的架构级改动，风险远高于其他 P2 项，用户 2026-07-03 决定跳过，单独排期时再做）
- [x] ~~写接口 code 无格式校验~~；~~`board_list` sort/order 无白名单~~（2026-07-03 已修复，见 ROADMAP）
- [x] ~~`api_zt`/`api_lhb` 命中缓存仍每次写库~~（2026-07-03 已修复，见 ROADMAP；顺带修了同类的 `api_market_breadth`）
- [x] ~~`vol_stats` 循环串行 N 次 kline 请求，自选股多时首次很慢~~（2026-07-03 已修复，见 ROADMAP）
- [x] ~~TTL 魔法数字散落各路由，未走 config~~（2026-07-03 已修复，见 ROADMAP）

### 前端
- ECharts 图表颜色硬编码深色系（轴 `#5a6a8a`、网格 `#1e2c48`、tooltip 深底），浅色主题下系统性不适配（**跨多个模板的图表配置改造，规模接近全层HTTPException改造，暂缓**）
- [x] ~~主题脚本在 body 底部执行，首屏 FOUC 闪烁~~（2026-07-03 已修复，见 ROADMAP）
- JS 工具函数重复：`fmtPct/fmtAmt/pctClass/fmtMoney` 等在 7-8 个页面各写一份，且 `fmtAmt` 跨页语义不一致（`overview` 小额原样返回 vs `stocks/etf` 四舍五入到万）；应下沉 base.html（**跨页面重构+行为微差异，缺乏浏览器验证手段，暂缓**）
- CSS 重复：`range-bar`、`#cost-overlay`、`.btn-rm/.btn-cost/.btn-add` 在 stocks/etf 逐行重复（**跨页面重构，缺乏浏览器验证手段，暂缓**）
- 移动端：导航 8 链接无折叠/换行，`macro` 5 列 KPI 不换行，stocks(14列)/etf(12列) 宽表拥挤（已有待办）
- [x] ~~`stock_detail` 同一 `batch_quotes` 请求发两次~~（2026-07-03 已修复，见 ROADMAP）
- [x] ~~`news.html` 字段缺失显示字面 "undefined"~~（2026-07-03 确认已随 P0-4 escHtml 改造间接修复+补齐视觉一致性，见 ROADMAP）
- [x] ~~stocks/etf 默认排序方向相反（desc:true vs false）；PE 缺失回退 `Infinity` 降序排最前~~（2026-07-03 已修复，见 ROADMAP）
- [x] ~~`escQ` 只转义单引号，`leaders.html:243` onclick 完全未转义~~（2026-07-03 已修复，见 ROADMAP；顺带发现并修了 `boards.html:310` 同类未转义问题）
- [x] ~~`maxAmount` 计算后未使用的死代码~~（2026-07-03 已删除，见 ROADMAP）
- [x] ~~加载/错误态文案 5 种混用；`n板` 与 `n板+` 标签不一致~~（2026-07-03 已修复，见 ROADMAP）
- [x] ~~`valuation.html:148-152` 手动高亮导航与 base.html 逻辑冗余~~（2026-07-03 已删除，见 ROADMAP）
- [x] ~~「补齐历史」管理按钮暴露在首页主视图，建议移出~~（2026-07-03 已修复，见 ROADMAP）

### 代码重复（重构项）
- [x] ~~`leaders.py` 一级/二级龙头三对函数几乎完全重复~~（2026-07-03 已修复，见 ROADMAP）
- [x] ~~`stocks.py` `fetch_watchlist`/`fetch_etf_watchlist`、`search_stock`/`search_etf` 高度重复~~（2026-07-03 已修复，见 ROADMAP）
- [x] ~~`indices.py:29-51` 与 `stocks.py:45-65` 新浪行情解析逻辑重复~~（2026-07-03 已修复，见 ROADMAP）
- [x] ~~`_today()`/`_BEIJING`/config 读取在多个路由文件各写一份~~（2026-07-03 已修复，见 ROADMAP；`_today`/`_BEIJING` 部分随 P1-1 已解决，本次补齐 config 读取的收拢）

**「代码重复」类别 4 项已全部修复完成。**
