"""板块/行业列表 + 构成股

概念板块列表：THS stock_fund_flow_concept 即时（含领涨股）
行业板块列表：THS stock_fund_flow_industry 即时（含领涨股）
构成股：东方财富（RemoteDisconnected，已降级为 THS K 线图）
"""

import akshare as ak
import pandas as pd
from data.fetchers import _AK_LOCK


def _fetch_concept_list() -> list[dict]:
    """概念板块列表 —— THS 即时资金流（含领涨股）"""
    with _AK_LOCK:
        df = ak.stock_fund_flow_concept(symbol="即时")
    rename = {
        "序号": "rank",
        "行业": "name",
        "行业-涨跌幅": "change_pct",
        "流入资金": "inflow",
        "流出资金": "outflow",
        "净额": "net",
        "公司家数": "company_count",
        "领涨股": "top_stock",
        "领涨股-涨跌幅": "top_stock_chg",
    }
    df = df.rename(columns=rename)
    if "inflow" in df.columns and "outflow" in df.columns:
        df["mkt_cap"] = df["inflow"] + df["outflow"]
    keep = ["name", "change_pct", "mkt_cap", "company_count", "net", "top_stock", "top_stock_chg"]
    df = df[[c for c in keep if c in df.columns]]
    df = df.sort_values("change_pct", ascending=False)
    return df.to_dict(orient="records")


def _fetch_industry_list() -> list[dict]:
    """行业板块列表 —— THS 汇总接口（含上涨/下跌家数、领涨股）"""
    with _AK_LOCK:
        df = ak.stock_board_industry_summary_ths()
    rename = {
        "板块":       "name",
        "涨跌幅":     "change_pct",
        "总成交额":   "mkt_cap",
        "净流入":     "net",
        "上涨家数":   "up_count",
        "下跌家数":   "down_count",
        "领涨股":     "top_stock",
        "领涨股-涨跌幅": "top_stock_chg",
    }
    df = df.rename(columns=rename)
    keep = ["name", "change_pct", "mkt_cap", "up_count", "down_count", "top_stock", "top_stock_chg", "net"]
    df = df[[c for c in keep if c in df.columns]]
    df = df.sort_values("change_pct", ascending=False)
    return df.to_dict(orient="records")


def fetch_board_list(board_type: str) -> list[dict]:
    """board_type: 'concept' | 'industry'"""
    try:
        if board_type == "concept":
            return _fetch_concept_list()
        else:
            return _fetch_industry_list()
    except Exception as e:
        return [{"error": str(e)}]


def _sina_prefix(code: str) -> str:
    return "sh" if code.startswith(("6", "9")) else "sz"


def fetch_board_kline(board_type: str, board_name: str, days: int = 30) -> list[dict]:
    """板块指数近 N 日 K 线（THS）"""
    from datetime import datetime, timedelta, timezone
    _BEIJING = timezone(timedelta(hours=8))
    now = datetime.now(_BEIJING)
    today = now.strftime("%Y%m%d")
    start = (now - timedelta(days=days)).strftime("%Y%m%d")
    try:
        with _AK_LOCK:
            if board_type == "industry":
                df = ak.stock_board_industry_index_ths(symbol=board_name, start_date=start, end_date=today)
            else:
                df = ak.stock_board_concept_index_ths(symbol=board_name, start_date=start, end_date=today)
        rename = {"日期": "date", "开盘价": "open", "最高价": "high", "最低价": "low", "收盘价": "close", "成交量": "volume", "成交额": "amount"}
        df = df.rename(columns=rename)
        df["date"] = df["date"].astype(str)
        return df.to_dict(orient="records")
    except Exception as e:
        return [{"error": str(e)}]


def fetch_board_constituents(board_type: str, board_name: str) -> list[dict]:
    """
    按需拉取板块构成股 + 新浪实时行情
    board_type: 'concept' | 'industry'
    """
    import requests

    try:
        if board_type == "concept":
            with _AK_LOCK:
                df = ak.stock_board_concept_cons_em(symbol=board_name)
        else:
            with _AK_LOCK:
                df = ak.stock_board_industry_cons_em(symbol=board_name)
    except Exception as e:
        return [{"error": str(e)}]

    rename = {
        "代码": "stock_code",
        "名称": "stock_name",
        "最新价": "price",
        "涨跌幅": "change_pct",
        "成交量": "volume",
    }
    df = df.rename(columns=rename)
    keep = ["stock_code", "stock_name", "price", "change_pct", "volume"]
    df = df[[c for c in keep if c in df.columns]]
    df = df.sort_values("change_pct", ascending=False)

    return df.to_dict(orient="records")
