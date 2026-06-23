"""市场情绪数据：涨跌家数、北向资金、龙虎榜"""

import akshare as ak
from data.fetchers import _AK_LOCK


def fetch_market_breadth() -> dict:
    """全市场涨跌家数统计（新浪全量行情）+ 涨停/跌停数（东方财富涨停板池）

    新浪 stock_zh_a_spot 拉取全量 A 股（沪深北 ~5500 支），与行情数据同源，准确。
    耗时约 20 秒，调用方需配置 5 分钟以上缓存 TTL。
    """
    from datetime import datetime, timezone, timedelta
    _CST = timezone(timedelta(hours=8))

    try:
        with _AK_LOCK:
            df = ak.stock_zh_a_spot()
        up   = int((df["涨跌幅"] > 0).sum())
        down = int((df["涨跌幅"] < 0).sum())
        flat = int((df["涨跌幅"] == 0).sum())

        # 涨停/跌停：用涨跌幅阈值近似（ST≤5%、科创/创业≤20%；主板≤10%）
        # 涨停池精确值另由 /api/zt 提供，此处仅作情绪条参考
        zt = int((df["涨跌幅"] >= 9.9).sum())
        dt = int((df["涨跌幅"] <= -9.9).sum())

        return {
            "up": up, "down": down, "flat": flat,
            "zt": zt, "dt": dt,
            "total": len(df),
            "ts": datetime.now(_CST).strftime("%H:%M"),
        }
    except Exception as e:
        return {"error": str(e)}


def fetch_north_flow() -> dict:
    """北向资金（沪深港通）实时净流入"""
    try:
        with _AK_LOCK:
            df = ak.stock_hsgt_fund_flow_summary_em()
        north = df[df["资金方向"] == "北向"]
        sh = north[north["板块"] == "沪股通"].iloc[0] if len(north[north["板块"] == "沪股通"]) else None
        sz = north[north["板块"] == "深股通"].iloc[0] if len(north[north["板块"] == "深股通"]) else None
        return {
            "sh_net":    float(sh["成交净买额"]) if sh is not None else None,
            "sz_net":    float(sz["成交净买额"]) if sz is not None else None,
            "sh_up":     int(sh["上涨数"])   if sh is not None else None,
            "sh_down":   int(sh["下跌数"])   if sh is not None else None,
            "sz_up":     int(sz["上涨数"])   if sz is not None else None,
            "sz_down":   int(sz["下跌数"])   if sz is not None else None,
        }
    except Exception as e:
        return {"error": str(e)}


def fetch_lhb_today() -> list[dict]:
    """今日龙虎榜（上榜原因 + 净买额）"""
    try:
        with _AK_LOCK:
            df = ak.stock_lhb_detail_em()
        today = df["上榜日"].astype(str).str[:10].max()
        df = df[df["上榜日"].astype(str).str[:10] == today]
        rename = {
            "代码": "code", "名称": "name", "收盘价": "price",
            "涨跌幅": "change_pct", "龙虎榜净买额": "net_buy",
            "上榜原因": "reason",
        }
        df = df.rename(columns=rename)
        keep = [c for c in ["code", "name", "price", "change_pct", "net_buy", "reason"] if c in df.columns]
        df = df[keep].sort_values("net_buy", ascending=False)
        return df.head(20).to_dict(orient="records")
    except Exception as e:
        return [{"error": str(e)}]
