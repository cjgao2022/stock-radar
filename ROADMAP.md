# Stock-Radar ROADMAP

## 项目状态

本地运行，FastAPI + Jinja2，数据源：新浪行情 + AKShare（THS/东方财富）。

最近验证：2026-06-23

---

## 已完成

### 基础架构
- [x] FastAPI + Jinja2 + SQLite 项目骨架
- [x] APScheduler 盘后自动刷新板块快照（16:35）
- [x] 内存 TTL 缓存（5 分钟）+ SQLite 日快照持久化
- [x] 全局 `threading.Lock`（`_AK_LOCK`）序列化 AKShare 调用，解决 py_mini_racer 并发崩溃

### 数据源
- [x] 新浪 `hq.sinajs.cn` 实时行情（指数、个股、ETF）
- [x] 新浪 suggest API 模糊搜索（type=11 个股 / type=22 ETF），名称完整不截断
- [x] AKShare `stock_fund_flow_concept(symbol='即时')`（THS 概念资金流，含领涨股）
- [x] AKShare `stock_board_industry_summary_ths()`（THS 行业板块汇总，含上涨/下跌家数）
- [x] AKShare `stock_zt_pool_em`（东方财富涨停板，含连板数）
- [x] AKShare `stock_hot_rank_em`（东方财富热门排行）
- [x] AKShare `stock_market_activity_legu`（全市场涨跌家数、涨停/跌停统计）
- [x] AKShare `stock_hsgt_fund_flow_summary_em`（沪深港通北向资金）
- [x] AKShare `stock_lhb_detail_em`（今日龙虎榜）

### 页面功能
- [x] **大盘首页**：市场情绪条、指数卡片、板块热力图、北向资金、行业资金流 TOP8、连板梯队、龙虎榜、THS 热门 TOP20
- [x] **板块页**：概念/行业双 Tab，涨跌幅 + 领涨股，净流入列，可排序
- [x] **板块详情**：构成股行情表（网络可达时展示，EM 接口被封时提示切换网络）
- [x] **个股页**：持仓列表（统计卡 + 全宽表格）+ 名称/代码模糊搜索（多结果展示）
- [x] **ETF 页**：持仓列表（统计卡 + 全宽表格）+ 名称/代码模糊搜索（多结果展示）

### 持仓管理
- [x] 动态持仓存储（`data/watchlist.json`，首次自动从 config.yaml 迁移）
- [x] 加入持仓（搜索结果 / 详情卡均可操作）
- [x] 移除持仓（持仓列表行内 × 按钮）
- [x] 口令确认弹框（操作时输入6位代码确认，防误触）
- [x] 加入时间字段（北京时间 `YYYY-MM-DD HH:MM`）

### 搜索体验
- [x] 中文名称整体匹配（防止 Sina suggest 拆字模糊匹配）
- [x] 个股/ETF 类型隔离（个股搜索不返回 ETF，ETF 搜索不返回个股）
- [x] 代码直查名称完整（修正 Sina hq 截断 + suggest `parts[4]` 取完整显示名）
- [x] 查询面板支持清空按钮

### 设计系统
- [x] 全站统一设计系统（CSS 变量、`panel`/`stat-card`/`chg-badge`/`data-table` 组件）
- [x] 深色 / 亮色双主题（localStorage 持久化）
- [x] 深色渐变导航栏，实时时钟（北京时间），当前页高亮
- [x] 红涨绿跌配色，数字等宽字体（tabular-nums）
- [x] 所有时间展示强制使用北京时间（`timeZone:'Asia/Shanghai'`）

---

## 已知问题 / 待确认

| 问题 | 状态 |
|------|------|
| 北向资金 `成交净买额` 盘中返回 0.0 | 待确认（可能是 AKShare 数据延迟） |
| 东方财富 `stock_board_concept_name_em` / `stock_board_industry_name_em` 在当前网络被封 | 已用 THS 接口替代，板块构成股接口同样被封，提示用户切换网络 |
| 概念板块无上涨/下跌家数 | THS 概念接口不提供该字段，显示 `-`，属接口限制 |

---

## 待办

- [ ] 个股主力资金净流入排行（大单追踪）
- [ ] ETF 规模/折溢价率（需补充数据源）
- [ ] 板块详情页增加资金流向趋势图（近5日）
- [ ] 移动端布局优化（当前在手机上表格较拥挤）
