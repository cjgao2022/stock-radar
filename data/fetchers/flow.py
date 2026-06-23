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
