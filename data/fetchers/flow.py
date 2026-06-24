"""资金流向 —— 同花顺为主（THS 独有价值数据）"""

import akshare as ak
from data.fetchers import _AK_LOCK


def fetch_industry_flow() -> list[dict]:
    """行业资金流向排行（同花顺）- 净额单位：亿元"""
    try:
        with _AK_LOCK:
            df = ak.stock_fund_flow_industry(symbol="即时")
        rename = {
            "序号": "rank",
            "行业": "name",
            "行业指数": "index_value",
            "行业-涨跌幅": "change_pct",
            "流入资金": "inflow",
            "流出资金": "outflow",
            "净额": "net",
            "公司家数": "company_count",
            "领涨股": "top_stock",
            "领涨股-涨跌幅": "top_stock_chg",
        }
        df = df.rename(columns=rename)
        keep = [c for c in ["rank", "name", "change_pct", "inflow", "outflow", "net",
                             "company_count", "top_stock", "top_stock_chg"] if c in df.columns]
        df = df[keep].sort_values("net", ascending=False)
        return df.to_dict(orient="records")
    except Exception as e:
        return [{"error": str(e)}]


def fetch_concept_flow() -> list[dict]:
    """概念板块资金流向排行（同花顺）- 净额单位：亿元"""
    try:
        with _AK_LOCK:
            df = ak.stock_fund_flow_concept(symbol="即时")
        rename = {
            "序号": "rank",
            "行业": "name",
            "行业指数": "index_value",
            "行业-涨跌幅": "change_pct",
            "流入资金": "inflow",
            "流出资金": "outflow",
            "净额": "net",
            "公司家数": "company_count",
            "领涨股": "top_stock",
            "领涨股-涨跌幅": "top_stock_chg",
        }
        df = df.rename(columns=rename)
        keep = [c for c in ["rank", "name", "change_pct", "inflow", "outflow", "net",
                             "company_count", "top_stock", "top_stock_chg"] if c in df.columns]
        df = df[keep].sort_values("net", ascending=False)
        return df.to_dict(orient="records")
    except Exception as e:
        return [{"error": str(e)}]


def fetch_stock_flow(code: str, market: str) -> list[dict]:
    """个股资金流向（同花顺）"""
    try:
        with _AK_LOCK:
            df = ak.stock_fund_flow_individual(stock=code, market=market)
        return df.to_dict(orient="records")
    except Exception as e:
        return [{"error": str(e)}]



def _rmb_to_yuan(s) -> float | None:
    """将 '亿'/'万' 字符串转为元（如 '16.15亿' → 1615000000）"""
    if s is None:
        return None
    s = str(s).strip()
    if s in ("-", "", "nan", "None"):
        return None
    try:
        if "亿" in s:
            return float(s.replace("亿", "").replace(",", "")) * 1e8
        if "万" in s:
            return float(s.replace("万", "").replace(",", "")) * 1e4
        return float(s.replace(",", ""))
    except Exception:
        return None


def _pct_to_float(s) -> float | None:
    """将 '12.34%' 字符串转为 12.34"""
    if s is None:
        return None
    try:
        return float(str(s).replace("%", "").replace(",", "").strip())
    except Exception:
        return None


def fetch_stock_flow_rank_all(indicator: str = "今日") -> list[dict]:
    """全市场个股主力资金净流入排行（同花顺 stock_fund_flow_individual）
    返回字段：code, name, price, change_pct(float), main_net(元), inflow(元), outflow(元)
    注：THS 此接口不区分超大单/散户，big_net/retail_net 返回 None
    """
    try:
        with _AK_LOCK:
            df = ak.stock_fund_flow_individual(symbol="即时")
        rows = df.to_dict(orient="records")
        result = []
        for r in rows:
            code = str(r.get("股票代码", r.get("代码", ""))).zfill(6)
            result.append({
                "code": code,
                "name": r.get("股票简称", r.get("名称", "")),
                "price": r.get("最新价"),
                "change_pct": _pct_to_float(r.get("涨跌幅")),
                "main_net": _rmb_to_yuan(r.get("净额")),
                "main_pct": _pct_to_float(r.get("净占比")),
                "big_net": None,
                "retail_net": None,
            })
        return sorted(result, key=lambda x: x.get("main_net") or -1e18, reverse=True)
    except Exception as e:
        return [{"error": str(e)}]


def fetch_market_flow() -> list[dict]:
    """大盘资金流向（东方财富，THS 无等价接口）"""
    try:
        with _AK_LOCK:
            df = ak.stock_market_fund_flow()
        return df.to_dict(orient="records")
    except Exception as e:
        return [{"error": str(e)}]


def fetch_zt_pool(date: str) -> list[dict]:
    """涨停板数据（东方财富，THS 无等价接口）"""
    try:
        with _AK_LOCK:
            df = ak.stock_zt_pool_em(date=date)
        rename = {
            "代码": "code",
            "名称": "name",
            "涨跌幅": "change_pct",
            "最新价": "price",
            "成交额": "amount",
            "换手率": "turnover",
            "封板资金": "seal_amount",
            "首次封板时间": "first_seal_time",
            "最后封板时间": "last_seal_time",
            "炸板次数": "open_count",
            "涨停统计": "zt_stat",
            "连板数": "zt_days",
            "所属行业": "industry",
        }
        df = df.rename(columns=rename)
        keep = [c for c in ["code", "name", "price", "change_pct", "amount", "turnover",
                             "seal_amount", "first_seal_time", "last_seal_time",
                             "open_count", "zt_stat", "zt_days", "industry"] if c in df.columns]
        return df[keep].to_dict(orient="records")
    except Exception as e:
        return [{"error": str(e)}]
