# Stock-Radar ROADMAP

## 项目状态

本地运行，FastAPI + Jinja2，数据源：新浪行情 + AKShare（THS/东方财富）。

最近验证：2026-07-03（全面代码审查 P0/P1/P2 修复完成 + 全站体验改造4阶段：删除页面头说明、板块/估值列表分页、首页指数与板块列表服务端直出、行业龙头与市场情绪骨架屏，见下方对应章节）

---

## 已完成

### 基础架构
- [x] FastAPI + Jinja2 + SQLite 项目骨架
- [x] APScheduler 盘后自动刷新板块快照（16:35）
- [x] 内存 TTL 缓存（5 分钟）+ SQLite 日快照持久化
- [x] 全局 `threading.Lock`（`_AK_LOCK`）序列化 AKShare 调用，解决 py_mini_racer 并发崩溃
- [x] `get_cached` 不缓存 error 响应，避免错误结果污染内存缓存
- [x] 板块路由跳过含 error 的 SQLite 日快照，回退到实时拉取

### 环境与运维
- [x] `.venv` 虚拟环境（Python 3.14）+ `requirements.txt` 依赖安装验证通过（akshare 1.18.64 / fastapi 0.139.0）
- [x] `requirements.txt` 顶部显式声明 `setuptools`/`wheel`：修复 Python 3.12+ venv 默认不预装 setuptools 导致 akshare 传递依赖 `jsonpath`（setup.py 老式包）构建失败
- [x] `start.sh` 一键启动脚本：首次自动建 venv + 装依赖，之后激活 venv 并启动 uvicorn
- [x] README「快速开始」补充 venv / start.sh / setuptools 说明
- [x] **CDN 资源本地化**：echarts / bootstrap(JS+CSS) 下载到 `static/vendor/`，`base.html` 改为本地引用；修复系统代理（Clash 7897）拦截 jsdelivr 返回 HTML、浏览器报 `Unexpected token '<'` 导致的白屏（commit 0b80668）

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

### 视觉系统刷新 + 信息架构（2026-07-02）
- [x] **中英字体栈**：`PingFang SC + SF Pro` 系统字体（零 CDN 依赖）、抗锯齿、行高/字距
- [x] **设计 token 全站接入**：四级字号 `--fs-*`、8 倍数间距 `--sp-*`、统一圆角 `--radius`
- [x] **全站统一页面头**：`page_title/page_subtitle/page_meta` 块，8 页各设标题+用途副标题
- [x] **导航按逻辑分组重排**：大盘 ｜ 宏观·估值 ｜ 板块·龙头 ｜ 个股·ETF·资讯，组间分隔符
- [x] **首页面板主次分层**：市场情绪/热力图深色主锚点 + `.panel-hd.subtle` 次级头
- [x] **CDN 本地化**：echarts/bootstrap 下载到 `static/vendor/`，修复系统代理拦截白屏

### 内容增强（投资者视角，2026-07-02）
- [x] **阶段1 零成本快赢**：龙虎榜「上榜原因」、个股主表「利润增速」(profit_yoy)、宏观「5日日均融资买入」
- [x] **阶段2 口径修正**：估值页副标题去「分位」承诺、PE 列标注「静」
- [x] **阶段3 估值深化**：新增 `valuation_stock.py`（百度股市通个股 PE(TTM)/PB 近1年分位，非 push2）+ `/api/stocks/{code}/valuation`，stock_detail 展示分位分档；`market_state` 并入全A股息率+近5年分位，macro 估值温度加 KPI
- [x] **阶段4 主线与赚钱效应**：涨停按行业聚合（主线代理，题材源不可得）、涨跌停比、连板晋级率

### 代码审查修复（2026-07-03，源自 ISSUES.md 全面体检）
- [x] **P0-1 板块快照写入失败**：`save_board_snapshot` 对缺失字段兜底（`code` 缺失时用 `name` 顶替），`scheduler.py` 写库处加 try/except；实跑验证 `board_snapshot` 表已正常写入
- [x] **P0-2 error 响应污染缓存**：`get_cached` 增加 dict 型 `{"error":...}` 判断，不再被长 TTL 缓存
- [x] **P0-3 watchlist 数据丢失**：`_save` 改临时文件 + `os.replace` 原子写；`_load` 解析失败先备份为 `.corrupt-<ts>` 再迁移，不再静默覆盖；已用损坏文件模拟验证
- [x] **P0-4 news/overview XSS**：`base.html` 新增全局 `escHtml()`，news 公告/研报表与首页龙虎榜第三方文本+URL 统一转义
- [x] **P1-1 时区不一致**：新增 `api/__init__.py` 的 `today_cst()`，`routes_stocks/news/leaders/valuation/macro/overview/boards` 统一改用北京时区；`base.html` 时钟状态判断改用北京时间字符串而非浏览器本地时区
- [x] **P1-2 连板阈值误判**：首页连板追踪按代码前缀取涨跌停阈值（688/30x→19.9%，83/87/43→29.9%，ST→4.9%，其余9.9%），与后端 `market.py` 口径一致
- [x] **P1-3 北交所资金流交易所误判**：`/api/stocks/{code}/flow` 补北交所判断（83/87/43/92 开头 → bj）
- [x] **P1-4 核心面板无 .catch**：overview/stock_detail/board_detail/stocks 补齐失败态提示（「加载失败」）
- [x] **P1-5 board_detail 无数据覆盖 ECharts 容器**：改用 `graphic` 文本占位，不再破坏 canvas DOM
- [x] **附带发现1：`fetch_stock_flow` 调用不存在的函数签名**：`ak.stock_fund_flow_individual(stock=, market=)` 实际只接受 `symbol` 参数，个股资金流接口此前必抛 `TypeError`；改用正确的 `ak.stock_individual_fund_flow(stock, market)`（东方财富 push2his），取最新一日并映射为 `main_net/super_big_net/big_net/mid_net/retail_net`，与前端 `stock_detail.html` 期望的字典结构对齐（此前返回整个 DataFrame 转的 list，与前端按单一对象取值的写法本就不匹配）。当前网络下 push2his 被代理拦截，返回规范 `{"error":...}`，非代码问题，已同步记入「已知问题」
- [x] **附带发现2：`_sina_prefix` 未处理北交所前缀**：`data/fetchers/stocks.py` 补齐 83/87/43/92 开头 → `bj` 前缀判断；此前北交所个股/ETF 用 `sz` 前缀查询新浪 `hq.sinajs.cn` 恒为空。已用 `430047`/`833575` 实测验证前后差异。`boards.py` 内同名但未被调用的 `_sina_prefix` 为死代码，未清理（原样保留待确认是否删除）

### P2 修复：全局 _AK_LOCK 粒度过粗（2026-07-03）
- [x] 逐个 grep 已安装 akshare 包源码确认哪些函数真正内部实例化 `py_mini_racer.MiniRacer`（而非猜测），据此把 `_AK_LOCK` 从「全局串行所有 AKShare 调用」收窄为「只锁真正用到 MiniRacer 的调用」
- 仍持锁（确认用 MiniRacer）：`boards.py`（THS 板块名称/汇总/K线/资金流×5处）、`flow.py`（`stock_fund_flow_industry`/`stock_fund_flow_individual`）、`leaders.py`（`stock_zh_a_spot`×2）、`market.py`（`stock_zh_a_spot`）、`market_state.py`（`stock_index_pe_lg`）、`valuation.py`（`stock_industry_pe_ratio_cninfo`）
- 移除锁（确认不用 MiniRacer）：`market.py`（龙虎榜）、`flow.py`（个股资金流/大盘资金流/涨停池）、`fundamentals.py`（THS财务摘要）、`leaders.py`（申万成分股映射×2 + 行业实时指数×2，原本 31/100 次串行成分股请求全程占锁，是本次收益最大的一处）、`macro.py`（CPI/PPI/PMI/M2 全部4个）、`market_state.py`（国债收益率/股息率/两融余额）、`news.py`（公告×2 + 研报）、`stocks.py`（ETF规模折溢价）、`valuation_stock.py`（百度股市通个股估值）、`scheduler.py`（跌停池补历史）
- 验证：11 个受影响 fetcher 逐一单独真实调用验证有真实返回；7 个函数（含仍持锁的 THS 调用）并发跑无崩溃；3 个新解锁函数的并发耗时（0.4s）明显低于串行耗时之和（0.7s），证明确实不再相互阻塞；起测试服务器验证 14 个相关路由全部 200

### P2 修复：get_cached 无 single-flight（2026-07-03）
- [x] `data/cache.py` 新增按 key 的锁字典 `_key_locks`（`_key_locks_guard` 保护字典本身的并发创建），`get_cached` 在锁内做二次 TTL 校验（double-checked locking）：同一 key 并发首访时只有一个线程真正调用 `fetch_fn`，其余线程排队后直接复用结果；不同 key 互不阻塞
- 验证：10 个线程并发请求同一 key（`fetch_fn` 内 `sleep(0.3)`），修复前预期打 10 次上游，修复后 `fetch_fn` 仅调用 1 次、总耗时 0.3s（而非 3s），10 个线程拿到的结果一致；5 个不同 key 并发耗时仍为 0.3s，确认未引入无关阻塞；真实服务器对 `/api/indices` 并发 5 次请求全部 200 无异常

### P2 修复：SQLite 连接从不 close、无 busy_timeout（2026-07-03）
- [x] `data/cache.py::_conn()` 由普通函数改为 `@contextmanager`：成功时 `commit()`、异常时 `rollback()`、无论如何 `finally: close()`；新增 `sqlite3.connect(..., timeout=10)` 设置 busy_timeout，让并发写入排队重试而非立即报 `database is locked`。14 处 `with _conn() as c:` 调用点写法不变，无需改动调用方
- 验证：14 个读写函数（板块快照/情绪历史/涨停/龙虎榜/构成股/行业轮动）全部真实调用通过；200 次连续开关连接无异常（确认不再依赖 GC 回收连接）；模拟异常验证 rollback 生效（插入后抛异常，重新查询确认数据未落库）；8 线程并发写入 400 行 board_snapshot 零 `database is locked` 报错；真实服务器 `/api/boards`、`/api/boards/rotation`、`/api/market/zt_history` 全部 200

### P2 修复：瞬时失败被当「真无数据」长期缓存（2026-07-03）
- [x] `macro.py::fetch_macro_calendar`：4 个宏观日历指标全部请求失败时返回 `[{"error":...}]`（原先全失败会静默返回 `[]`，被 24h TTL 缓存成"未来90天无事件"）；只要有一个指标成功，空结果就是真实的，正常返回。`macro.html::renderCalendar` 补上 `error` 分支渲染
- [x] `news.py::fetch_announcements_watchlist`：持仓股全部请求失败时返回 error 而非 `[]`（原先 30 分钟 TTL 会误缓存"今日无公告"）
- [x] `news.py::fetch_research_reports`：同上逻辑用于研报（1 小时 TTL）
- **过程中发现的关键坑**：`ak.stock_individual_notice_report`/`stock_notice_report`/`stock_research_report_em` 三个 AKShare 函数在**查询结果为 0 条时会内部抛 `KeyError('代码')`**（读了 akshare 源码确认：`big_df` 为空 DataFrame 时列从未被赋值就被访问）。这意味着"真无数据"和"真的报错"在这三个接口里都表现为异常，不能用"是否抛异常"简单二分。已在三处都加 `except KeyError: continue`（视为真无数据的正常路径）+ `except Exception` 才计入失败计数，用真实网络异常模拟验证两种场景都返回正确结果，避免了把"今天确实没有公告"误判成故障
- `news.html::loadResearch` 补上 `data[0].error` 分支渲染（原先 error 载荷会被当成正常数据渲染成一行空白）
- `market.py::fetch_lhb_today` 排查后确认已经是正确设计（真异常返回 error，AKShare 空结果的 TypeError 有注释说明），未改动；`stocks.py` 的行情函数当前没有被 `get_cached` 长 TTL 包装，此问题暂不适用
- 验证：4 个函数真实调用全部返回合理结果；`fetch_announcements_watchlist` 真实调用中实际触发了上述 KeyError 坑并验证修复前后行为差异；用 monkeypatch 模拟"全部失败"和"部分失败"两种场景，确认只有真实网络异常才返回 error、真无数据仍返回 `[]`；`/news`、`/macro` 页面完整脚本语法检查通过，路由 200

### P2 修复：fetch_market_breadth 缺「名称」列时 ST 判定退化（2026-07-03）
- [x] 原代码 `names = '' if 缺列` 后 `is_st = False`（标量），后续 `~is_hi & ~is_bj & ~is_st` 依赖 Python `~False == -1` 恰好是 AND 单位元这一巧合才算对，且触发 `DeprecationWarning`（Python 3.16 起 bool 按位取反将报错，届时该函数会直接崩溃）。改为缺列时显式构造与 `pct` 等长的 `pd.Series(False, index=pct.index)`，避免标量参与 Series 布尔运算
- 验证：`-W always` 运行确认不再产生 bool/bitwise 相关 DeprecationWarning；用不含「名称」列的构造数据验证降级路径正常工作且不崩溃（含一只模拟 ST 股票 6% 涨幅，缺列时按主板 9.9% 阈值处理未误判涨停，行为符合"无法识别 ST 时保守处理"的设计意图）；真实服务器 `/api/market/breadth` 200

### P2 修复：load_board_rotation 全表扫描无时间下限（2026-07-03）
- [x] 最长窗口只需 60 个交易日，加 `date >= 今日-120天`（覆盖春节等长假的自然日缓冲）过滤；`init_db()` 新增 `idx_board_snapshot_type_date (board_type, date)` 索引支撑该查询
- 验证：`EXPLAIN QUERY PLAN` 确认查询计划从潜在全表扫描变为 `SEARCH board_snapshot USING INDEX idx_board_snapshot_type_date`；真实数据下 `load_board_rotation('industry')` 仍正确返回 90 个板块；服务器 `/api/boards/rotation`、`/boards` 页面 200

### P2 修复：board_{type} 实时兜底缓存 key 不带日期（2026-07-03）
- [x] `routes_boards.py::api_board_list` 的兜底缓存 key 从 `board_{board_type}` 改为 `board_{board_type}_{date}`，与本文件其余缓存 key（kline 等）的日期后缀写法保持一致，跨日后旧 key 自然失效不会被复用
- 验证：路由 `/api/boards?board_type=concept` 200

### P2 修复：调度偏移在接近午夜时产生非法 hour=24（2026-07-03）
- [x] `scheduler.py::_offset` 的 `divmod(total, 60)` 在 `snapshot_refresh_time` 配置为 23:57~23:59 时会算出 `hour=24`，APScheduler 的 `CronTrigger` 会直接抛 `ValueError` 导致启动崩溃。改为先对 1440（24×60）取模再 `divmod`，跨午夜正确环绕到次日 00:xx
- 验证：用 `23:58` 复现修复前 `CronTrigger(hour=24,...)` 确实抛 `ValueError`；修复后同样入参算出 `(0, 2)` 且 `CronTrigger` 正常接受；默认配置 `16:35` 下 `start_scheduler()` 实跑无异常

### P2 修复：scheduler 全程用 print 改 logging（2026-07-03）
- [x] `data/scheduler.py` 新增 `logging.basicConfig(level=INFO)` + 模块级 `logger`，13 处 `print(...)` 全部替换为 `logger.info`（成功路径）/ `logger.warning`（失败路径），消息文本不变（去掉冗余的 `[scheduler]` 前缀，logger name 已带出处）
- 副作用（有益）：basicConfig 应用于 root logger 后，APScheduler 自身的内部日志（加任务/启动等）也第一次变得可见，此前完全没有输出
- 验证：`start_scheduler()` + `save_zt_snapshot()` 实跑，日志正确输出带时间戳；真实服务器启动、请求首页 200，日志无异常

---

**「后端 / 存储」P2 类别 8 项已全部修复完成。**

### P2 修复：/api/admin/bootstrap_history 用 GET 触发写操作（2026-07-03）
- [x] `routes_overview.py` 该路由 `@router.get` 改 `@router.post`：这是一个 60-120 秒的昂贵写操作，GET 语义上应该幂等/无副作用，用 GET 暴露给浏览器预取、爬虫、代理等意外触发的风险。本地单人使用场景下未加鉴权（与 issue 原文风险评估一致），只修正 HTTP 方法语义
- `overview.html::runBootstrap` 的 `fetch` 调用同步加 `{method:'POST'}`
- 验证：GET 请求现在返回 405 Method Not Allowed；POST 请求 200 正常执行；首页脚本语法检查通过，确认前端按钮改动生效

### P2 修复：删除死接口 /api/flow/market、/api/boards/snapshot（2026-07-03）
- [x] 确认全部模板文件都未调用这两个路由后删除；`/api/flow/market` 唯一的后端支撑函数 `fetch_market_flow`（`data/fetchers/flow.py`）删除后也无其他调用方，一并清理（孤儿代码）；`/api/boards/snapshot` 用到的 `load_board_snapshot` 仍被 `routes_boards.py` 使用，只删路由和该文件里变成多余的 import，保留函数本体
- 验证：两个路由现在 404；`/api/indices`、`/api/boards`、首页仍 200，确认删除未影响其他功能

### P2 修复：写接口 code 无格式校验 + board_list sort/order 无白名单（2026-07-03）
- [x] `routes_stocks.py` 6 个写接口（stock/etf 的 add/remove/update-cost）path 参数 `code` 统一用 `fastapi.Path(pattern=r"^\d{6}$")` 校验，非法格式直接 422，不再有机会把垃圾数据写进 `watchlist.json`
- [x] `routes_boards.py::api_board_list` 新增 `_SORT_WHITELIST`（9 个真实存在的可排序字段），`sort` 传入白名单外的值时静默 fallback 到 `change_pct`，不再是"传什么都能当 dict key 用"
- 全层 `HTTPException` 改造评估后决定暂缓（见上方 P2 遗留说明）
- 验证：非法 6 位数字外的 code（如 `abc123`）→ 422；合法 code 增删改全部 200 且行为正常（含 PATCH cost 因参数重排序后仍正确工作）；`sort` 传入任意字符串不再报错，安全 fallback；`/stocks`、`/etf`、`/boards`、首页页面全部 200 无回归

### P2 修复：api_zt/api_lhb/api_market_breadth 命中缓存仍每次写库（2026-07-03）
- [x] `get_cached` 本身不暴露"是否命中缓存"，改在路由层用一个 `fetched` 标志位包一层 `_fetch()` 闭包（`fetch_fn` 真正被调用时才置位），只有 `fetched=True`（即这次是缓存未命中、真的打了上游）才调用 `save_*_history` 写 SQLite；命中缓存时数据和上次写的完全一样，不再重复 INSERT。三处（`api_zt`/`api_lhb`/`api_market_breadth`）用同一模式修复
- 验证：mock 掉底层 fetch 和 save 函数，连续调用 3 次每个路由，`save_*_history` 均只触发 1 次（而非 3 次）；真实服务器对三个端点各请求 2 次，全部 200 无异常

### P2 修复：vol_stats 循环串行 N 次 kline 请求（2026-07-03）
- [x] `api_vol_stats`/`api_etf_vol_stats` 抽出公共 `_compute_vol_stats(codes, kkey_prefix)`，用 `ThreadPoolExecutor`（`max_workers=min(8,len(codes))`）并发拉取各股票日K线；`fetch_stock_kline` 本身不经过 `_AK_LOCK`（新浪 quotes API，非 AKShare/MiniRacer），确认可以安全并发。缓存 key 格式保持不变（`kline_{code}_daily_{date}` / `kline_etf_{code}_daily_{date}`），与个股详情页 K 线接口共享同一缓存条目
- 验证：6 只股票无缓存时，串行 2.47s → 并发 0.92s（约 2.7 倍）；真实服务器 `/api/stocks/vol_stats`、`/api/stocks/etf/vol_stats` 返回数据与重构前格式完全一致；`/stocks` 页面 200

### P2 修复：TTL 魔法数字散落各路由（2026-07-03）
- [x] `config.yaml::cache` 新增 13 个具名 TTL（单位秒）：`indices/market_breadth/vol_stats/flow_rank/leaders/etf_meta/announcements/research/industry_pe/board_kline_long/macro_valuation/margin/fundamentals/macro_indicators/macro_calendar_ttl_seconds`
- 7 个路由文件（`routes_overview/leaders/macro/valuation/news/stocks/boards`）里原来直接写 `60`/`300`/`1800`/`3600`/`21600`/`86400` 等裸数字的 `get_cached(...)` 调用全部改用上述具名常量；K 线相关的 `_KLINE_TTL` 字典（`intraday/daily/weekly/monthly/yearly`）本身已语义清晰予以保留，只把兜底 fallback 值 `300` 也改成引用 `_KLINE_TTL["daily"]` 消除重复字面量
- 顺手清理：`routes_stocks.py` 里 `_CodePath = Path(...)` 误插在 import 语句中间的问题一并归位
- 验证：`yaml.safe_load` 确认新增 13 个配置键全部可读；20 个受影响的路由端点逐一真实请求全部 200（含冷启动约 100s 的 `/api/leaders`、板块月K线）

---

**「API 设计」P2 类别 7 项中 6 项已修复，1 项（全层 HTTPException 改造）经评估后用户决定暂缓单独排期。**

### P2 修复：escQ 转义不完整 + leaders.html onclick 完全未转义（2026-07-03）
- [x] `base.html` 新增 `escJsAttr()`：专门处理"值作为 `onclick=\"fn('...')\"` 里单引号 JS 字符串参数，同时又嵌在双引号 HTML 属性里"这种双层转义场景——`escHtml()` 把 `'` 转成 HTML 实体 `&#39;` 不够用，浏览器先做 HTML 实体解码再交给 JS 解析器，解码后 `&#39;` 变回字面 `'` 照样能提前闭合 JS 字符串；`escJsAttr` 对 `'` 用 JS 转义 `\'`（真正阻止字符串提前结束），对 `"`/`&`/`<`/`>` 才用 HTML 实体转义（防止破坏外层属性和防御性转义标签注入）
- 删除 `stocks.html`/`etf.html` 里只转义单引号的本地 `escQ`，改用共享的 `escJsAttr`，順带把此前遗漏未转义的 `code` 参数也补上转义
- `leaders.html:243` 的 `onclick="openKline('${s.code}','${s.name}')"` 完全未转义（HTML 文本节点和 JS 属性双重暴露）已修复
- 顺带发现同类问题：`boards.html:310` 行业轮动表格的 `onclick` 用 `.replace(/'/g,'')`（直接删除引号，非正确转义）且 `${r.name}` 原样进 `innerHTML`，一并按同样方式修复
- 验证：用 Node 模拟浏览器"HTML 属性解码→JS 解析"两阶段过程，验证含单引号/双引号/`</script><img onerror>` 的恶意股票名称转义后不会提前闭合字符串、不会残留可执行的 `<script>`/`<img>` 标签；真实服务器渲染 `/`、`/boards`、`/stocks`、`/etf`、`/leaders`（含冷启动~100s）全部 200，脚本语法检查无误

### P2 修复：主题脚本在 body 底部执行导致 FOUC（2026-07-03）
- [x] 把 `data-theme` 属性设置从 body 底部的 IIFE 挪到 `<head>` 顶部一段极简同步内联脚本（只设置属性，不碰任何 DOM 元素，因为此时 body 还没解析），首屏渲染前就应用正确主题，不再有"先亮色画一帧再切暗色"的闪烁；body 底部原脚本保留，只做主题按钮图标同步 + 供 `toggleTheme()` 运行时调用的 `applyTheme()` 定义
- 验证：解析响应 HTML 确认 `<head>` 内确实包含 `setAttribute('data-theme'...)`；脚本语法检查通过；首页 200

---

**以下前端项经评估为跨文件/跨页面的较大改动且缺乏浏览器可视化验证手段，暂缓：ECharts 图表颜色主题适配、JS 工具函数下沉去重、CSS 重复消除。**

### P2 修复：stock_detail 同一 batch_quotes 请求发两次（2026-07-03）
- [x] 把 `fetch(...).then(r=>r.json())` 提到顶层存成 `_quotePromise`，价格展示区块和基本面区块（算 PE/PB 需要实时价）都改成消费同一个 Promise（JS Promise 只会真正发一次网络请求，多次 `.then()` 只是排队消费已缓存的结果），两块各自的错误处理逻辑保持不变
- 验证：解析渲染出的 HTML 确认 `batch_quotes?codes=` 只出现 1 次（此前 2 次）；页面 200，脚本语法检查无误

### P2 修复：news.html 字段缺失显示字面 "undefined"（2026-07-03）
- [x] 排查发现：P0-4 引入的 `escHtml()` 内部用 `String(s ?? '')`（`??` 空值合并），`escHtml(undefined)` 已经返回空字符串而非字面量 `"undefined"`——核心 bug 已随 XSS 修复间接消失。本次补齐视觉一致性：公告表 `code`/`name`、研报表 `code`/`stock_name`/`institution` 统一加 `|| '—'` 兜底（此前只有 `type`/`rating`/`date` 有），字段缺失时显示统一的「—」而不是空白单元格
- 验证：Node 验证 `escHtml(undefined) === ''`（而非 `"undefined"`）；`/news` 页面 200，脚本语法检查无误

### P2 修复：stocks/etf 默认排序方向相反 + PE/PB/折溢价缺失回退 Infinity（2026-07-03）
- [x] `etf.html` 默认 `sortState={key:'change_pct',desc:false}` 改成 `desc:true`，与 `stocks.html` 一致，也与两个文件内部"点击切换列时默认降序"（`sortState.desc=(key!=='code')`）的既有约定一致
- [x] `stocks.html` 的 `pe`/`pb` 排序取值、`etf.html` 的 `premium`（折溢价）排序取值，缺失时的回退值从 `Infinity` 改成 `-Infinity`，与同文件里其余所有字段（`roe`/`profit_yoy`/`scale`/通用 `d[key]`）"缺失=最小值"的一致约定对齐——此前用 `Infinity` 会让"没有基本面数据"的股票在 PE 降序榜单里排在最前面，误导成"估值最高"
- 验证：Node 模拟排序，缺失 PE 数据的行不再排在真实 PE=10 的行前面；`/stocks`、`/etf` 页面 200，脚本语法检查无误

### P2 修复：maxAmount 计算后未使用的死代码（2026-07-03）
- [x] 确认 `maxAmount` 在 `stocks.html`/`etf.html` 里赋值后从未被读取（无任何渲染逻辑消费），删除变量声明和赋值语句
- 验证：全局搜索确认无残留引用；`/stocks`、`/etf` 页面 200，脚本语法检查无误

### P2 修复：valuation.html 手动高亮导航与 base.html 逻辑冗余（2026-07-03）
- [x] `base.html` 已有全站统一的导航高亮 IIFE（按路径映射 nav id，同步执行不依赖 DOMContentLoaded），`valuation.html` 自己又在 `DOMContentLoaded` 里重复"先移除全部active再加回nav-valuation"，净效果相同但白做一遍，删除
- 验证：确认 base.html 的路径映射本就包含 `/valuation → nav-valuation`；`/valuation` 页面 200，脚本语法检查无误

### P2 修复：「补齐历史」按钮暴露在首页主视图（2026-07-03）
- [x] 按钮默认 `display:none`，只有在 `renderBreadthHist` 判定"确实需要补历史"（无数据，或 `hasFullCount=false` 即只有涨停数没有完整涨跌家数）时才显示——这正是图表提示文案"点击「补齐历史」"出现的同一判断条件，按钮可见性和提示文案现在保持一致；本地未开发环境不删除功能本身（本地单人工具，仍需要有入口手动补齐），只是不再无条件常驻主视图
- 验证：真实数据库当前已有完整历史（`hasFullCount=True`），确认修复后按钮默认隐藏；渲染 HTML 确认初始 `style="display:none"`；首页 200，脚本语法检查无误

---

### P2 修复：加载/错误态文案混用 + n板/n板+标签不一致（2026-07-03）
- [x] 统一 10 个文件里的错误态文案："请求失败"/"加载失败，请刷新"/"数据加载失败"/"数据加载失败：{error}" 全部统一成"加载失败"（带详情的保留 `加载失败：${err.message}` 形式）——纯文案改动不涉及逻辑，风险低
- [x] `overview.html` 连板梯队/涨停表/连板追踪三处生成 `n板`/`n板+`/`首板` 标签的逻辑此前互相不一致（涨停表缺 `+` 后缀、连板追踪缺"首板"特判），统一成同一套规则：`n>=4→'n板+'`，`n===1→'首板'`，其余`'n板'`
- 验证：全局搜索确认旧文案变体清零；8 个相关页面全部 200，脚本语法检查无误

---

**「前端」P2 类别 13 项中 10 项已修复，3 项（ECharts 主题适配、JS 工具函数去重、CSS 重复消除）经评估后暂缓，移动端宽表此前已在 ROADMAP 待办中单独记录。**

### P2 修复：_today()/_BEIJING/config 读取在多个路由文件各写一份（2026-07-03）
- [x] `_today()`/`_BEIJING` 重复问题已随 P1-1 时区统一修复顺带解决（抽到 `api/__init__.py::today_cst()`）。本次补齐剩下的 config 读取重复：`api/__init__.py` 新增模块级 `config`（一次性 `yaml.safe_load`），`routes_overview/boards/valuation/news/leaders/macro/stocks` 7 个文件全部改成 `from api import today_cst as _today, config as _cfg`，删除各自重复的 `yaml.safe_load(Path("config.yaml")...)` 及多余的 `import yaml`/`from pathlib import Path`
- `data/` 包下（`cache.py`/`scheduler.py`/`stocks.py`/`watchlist_store.py`/`indices.py`）各自读取 config 的部分未动——这些模块同时被 API 路由和调度器/命令行脚本调用，跟 `api/__init__.py` 不是同一层级，不适合共用同一个单例，issue 原文也只点名"路由文件"，未扩大范围
- 验证：8 个文件全部 `py_compile` 通过；16 个受影响的路由端点 + 页面实测全部 200

### P2 修复：leaders.py 一级/二级龙头三对函数重复（2026-07-03）
- [x] `_build_industry_map`/`_build_l2_industry_map`、`_get_industry_map`/`_get_l2_industry_map`、`fetch_leaders`/`fetch_leaders_second` 三对函数体几乎逐字重复（仅 `sw_index_first_info` vs `second_info`、`'一级行业'` vs `'二级行业'` 不同），参数化合并成 `_build_industry_map(info_fn)`/`_get_industry_map(level, info_fn)`/`_fetch_leaders(level, info_fn, sw_symbol)`，`fetch_leaders`/`fetch_leaders_second` 保留原函数名做薄封装（供 `routes_leaders.py` 直接 import，外部接口不变）；模块级缓存从两个独立变量改成 `_map_caches` 字典按 `level` 区分，确认一级/二级互不干扰
- 验证：真实调用 `fetch_leaders()` 两次，确认 `_map_caches['l1']` 命中缓存后二次调用从 38.2s 降到 24.6s（少了约31s的行业成分股拉取），`_map_caches['l2']` 全程未被污染；两个 API 端点 + 页面全部 200

### P2 修复：stocks.py fetch_watchlist/fetch_etf_watchlist、search_stock/search_etf 重复（2026-07-03）
- [x] `fetch_watchlist`/`fetch_etf_watchlist` 合并成 `_fetch_watchlist_quotes(items, extra_fields)`，ETF 特有的 `etf_type` 字段通过 `extra_fields=("etf_type",)` 参数化，个股场景不传则完全不产生该字段（行为不变）
- [x] `search_stock`/`search_etf` 合并成 `_search(query, suggest_type, want_etf)`，用 `_is_etf_code(x) != want_etf` 统一表达此前两份代码里方向相反的过滤条件（`if _is_etf_code(query): return []` vs `if not _is_etf_code(query): return []`）
- 验证：真实调用覆盖 6 种场景——持仓股/ETF 行情合并字段正确、按名称搜个股、用 ETF 代码搜个股正确返回空、按代码搜 ETF 正确返回全名、用个股代码搜 ETF 正确返回空；4 个相关 API 端点 + 页面全部 200

### P2 修复：indices.py 与 stocks.py 新浪行情解析逻辑重复（2026-07-03）
- [x] 两文件解析 `hq.sinajs.cn` 响应的逻辑字段取用和错误处理完全不同（indices 用配置里的名称覆盖、失败时给每个指数返回带 error 的占位；stocks 信任 fields[0] 做名称、按 100 个一批处理、单条失败直接丢弃），不适合整体合并，只抽出两边完全相同的"一行文本→(代码,字段列表)"解析原语 `parse_sina_hq_line()` 放进 `data/fetchers/__init__.py`，两个文件各自的业务逻辑保持不变
- 验证：真实调用 `fetch_indices()`/`fetch_quotes()`，输出结构与重构前完全一致；`/api/indices`、`/api/stocks/watchlist`、首页、`/stocks` 全部 200

---

**「代码重复」P2 类别 4 项已全部修复完成。**

---

## P2 全面完成总结（2026-07-03）

全部 30 项 P2 中，**26 项已修复**，**4 项经评估后暂缓**（均已在用户参与决策下明确记录原因，非遗漏）：
- 全层 `HTTPException` 改造（用户决定跳过，风险/收益不匹配当前阶段）
- ECharts 图表颜色主题适配（跨5文件/8-10图表，缺乏浏览器可视化验证手段）
- JS 工具函数下沉去重（跨7-8页面，`fmtAmt` 等存在行为微差异需要仔细验证）
- CSS 重复消除（跨页面，同样缺乏视觉验证手段）

这 4 项暂缓项如果之后要做，建议先补上截图/浏览器自动化验证手段，再动手改，避免凭代码逻辑推断视觉效果。

---

## 全站体验改造（2026-07-03）

用户反馈"要极致丝滑、页面不要老显示加载中、开头说明文字多余、长列表没分页"，按 4 个阶段实施：

### 阶段1：删除页面头说明文字
- [x] `base.html` 的 `page-head` 移除 `page_subtitle` block 及其容器 `.ph-sub`（连带清理 CSS），8 个页面（overview/boards/stocks/etf/valuation/macro/news/leaders）各自的 `{% block page_subtitle %}` 一并删除，页面头只保留标题
- 验证：8 个页面 200，确认渲染出的 HTML 里 `page-head` 只剩 `<h1 class="ph-title">` + `<div class="ph-meta">` 两个 flex 子元素，无孤儿空 div

### 阶段2：长列表补分页
- [x] 把 `news.html` 原本自用的 `renderPagination()`（含 CSS：`.pg-bar/.pg-btn/.pg-info/.pg-total`）下沉到 `base.html` 做全站共享，增加 `pageSize` 参数使其可配置（此前硬编码 `PAGE_SIZE=10`），`news.html` 两处调用改传参数，顺带解决了这两个函数的重复问题
- [x] `boards.html`：概念板块最多386行、行业板块~90行，此前全量渲染无分页。加 `BOARD_PAGE_SIZE=30`，`renderTable()` 按当前排序/搜索结果分页，行号显示改为全局排名（`start+i+1`）而非页内序号
- [x] `valuation.html`：~110行（19个一级+91个二级行业），二级行业挂在一级下面显示，不能按平铺行分页（会把子项和父级拆到不同页）。改为**按一级行业分组分页**（`VAL_GROUP_PAGE_SIZE=15`，每组含其全部二级子项），只有勾选"展开二级行业"时才分页，默认视图（~19行一级行业）全部展示不分页
- 验证：Node 模拟分页数学（386/30=13页、110行分组后68+42=110无缺无重）；真实服务器渲染两页面 200，脚本语法检查无误

### 阶段3：服务端直出（消除首屏"加载中"）
- [x] 首页指数卡片（`fetch_indices`，新浪实时 <1s）+ 板块列表默认视图（`boards.html` 概念板块，优先读 SQLite 当日快照 <1s）：`main.py` 路由直接调用 `api_indices()`/`api_board_list()`（FastAPI 路由函数本质是普通 Python 函数，可直接调用复用同一套逻辑和缓存），失败/error 时传空列表兜底，通过 `{{ data | tojson }}` 嵌入 `window.__INITIAL_INDICES__` / `window.__INITIAL_BOARDS__`
- [x] `overview.html`/`boards.html` 的 JS 改为：有预置数据就直接渲染（跳过首次 `fetch`），仍保留原有的定时刷新/切换 tab 逻辑不变
- 未做 SSR 的部分（保持骨架屏+异步）：市场情绪、资金流、涨停、龙虎榜等耗时不稳定或依赖用户交互（切换板块类型）的接口，SSR 反而可能让整页等待意外变慢的接口，不划算
- 验证：**真实执行页面 JS**（Node + 手写最小 DOM stub，不依赖真实浏览器）确认两页面加载时 `fetch` 全程未被调用、数据正确渲染（6张指数卡片、386行板块表格首页30行+分页1/13、概览统计386）——不是只测语法，是测真实渲染路径

### 阶段4：慢接口骨架屏 + 进度感
- [x] `base.html` 新增全站共享 `.skeleton`（渐变+shimmer动画）样式
- [x] `leaders.html`（行业龙头，冷启动一级~60s/二级~2-3分钟）：把原来的转圈 spinner 换成贴合最终卡片布局的骨架屏网格（`skeletonCard()`生成8张仿真卡片：标题栏+5行仿真表格），配合已有的"首次约X秒/分钟，之后30分钟缓存"进度文案（挪到独立的 `#leaders-progress` 提示位，与卡片区分离）
- [x] `overview.html` 市场情绪面板（`fetch_market_breadth` 冷启动~20s）：涨跌家数/涨停/跌停/涨跌停比 6 个数字从静态"--"占位改成骨架屏 shimmer 块；成交额（`b-amount`）不需要骨架屏，因为它由阶段3已 SSR 的指数数据算出，几乎瞬间可用
- 验证：真实渲染确认骨架屏 HTML 结构正确生成（8张仿真卡片、shimmer占位存在）；Node 模拟确认 `textContent` 赋值能正确清除骨架屏子元素换上真实数据，不需要额外改动现有的数据渲染逻辑

**4 个阶段全部完成并验证，全站页面（8个列表页 + 2个详情页）最终回归测试全部 200，无 JS 语法错误，无服务端异常。**

## 已移除功能

| 功能 | 原因 |
|------|------|
| 北向资金（沪深港通） | 东方财富 `成交净买额` 数据自 2024-08 起全部断档（NaN/null），AKShare 所有 hsgt 接口均受影响，无可用替代数据源 |
| 事件日历（`/calendar`） | 解禁接口走东方财富 push2（被代理封锁），宏观日历因 AKShare 数据截止 2025-08 为空，三块内容均无法展示，已整体移除 |

---

## 已知问题

| 问题 | 状态 |
|------|------|
| 东方财富 `push2.eastmoney.com`/`push2his.eastmoney.com` 在当前网络被代理封锁 | 板块构成股、个股资金流向明细（`/api/stocks/{code}/flow`）接口受影响，返回 `{"error":...}`，提示用户切换网络；板块 K 线已改用 THS 接口规避；个股/ETF K 线已改用新浪 `CN_MarketDataService` 接口规避 |
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
| 涨停「题材」归类 | `stock_zt_pool_em` 仅有「所属行业」无题材字段，AKShare 无可靠涨停原因源；已改用「涨停按行业聚合」作主线代理 |
| 行业级 PE 历史分位 / PB / 股息率 | 巨潮 `stock_industry_pe_ratio_cninfo` 仅当期 PE、无 PB/股息，历史分位需跨日期反复调用成本高；个股级已用百度股市通实现 |
| ETF 跟踪指数估值分位 | `stock_zh_index_value_csindex` 仅返回约20行不足算分位；仅宽基 ETF 可经乐咕乐股指数PE近似，后置 |
