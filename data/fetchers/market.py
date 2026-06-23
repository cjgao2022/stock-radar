"""市场情绪数据：涨跌家数、北向资金、龙虎榜"""

import akshare as ak
from data.fetchers import _AK_LOCK


def fetch_market_breadth() -> dict:
    """全市场涨跌家数、涨停/跌停统计（乐咕乐股）"""
    try:
        with _AK_LOCK:
            df = ak.stock_market_activity_legu()
        mapping = {
            "上涨": "up", "涨停": "zt", "真实涨停": "zt_real",
            "下跌": "down", "跌停": "dt", "真实跌停": "dt_real",
            "平盘": "flat", "停牌": "suspended", "活跃度": "activity",
        }
        result = {}
        for _, row in df.iterrows():
            key = mapping.get(row["item"])
            if key:
                val = row["value"]
                if isinstance(val, str) and "%" in val:
                    val = float(val.replace("%", ""))
                result[key] = val
        return result
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
