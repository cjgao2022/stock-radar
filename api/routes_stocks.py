"""个股相关 API"""

from datetime import date as _date
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel
from data.fetchers.stocks import fetch_watchlist, fetch_etf_watchlist, search_stock, search_etf, fetch_stock_kline, fetch_quotes
from data.fetchers.flow import fetch_stock_flow, fetch_stock_flow_rank_all
from data.watchlist_store import add_stock, remove_stock, add_etf, remove_etf, update_stock_cost, update_etf_cost
from data.cache import get_cached


class CostBody(BaseModel):
    cost_price: Optional[float] = None
    shares: Optional[float] = None

router = APIRouter(prefix="/api/stocks")
_KLINE_TTL = {"intraday": 60, "daily": 300, "monthly": 3600, "yearly": 3600}


@router.get("/watchlist")
def api_watchlist():
    return fetch_watchlist()


@router.post("/watchlist/{code}")
def api_add_stock(code: str, name: str = ""):
    return {"ok": add_stock(code, name)}


@router.delete("/watchlist/{code}")
def api_remove_stock(code: str):
    return {"ok": remove_stock(code)}


@router.patch("/watchlist/{code}/cost")
def api_update_stock_cost(code: str, body: CostBody):
    return {"ok": update_stock_cost(code, body.cost_price, body.shares)}


@router.get("/search")
def api_search(q: str = ""):
    return search_stock(q)


@router.get("/etf/watchlist")
def api_etf_watchlist():
    return fetch_etf_watchlist()


@router.post("/etf/watchlist/{code}")
def api_add_etf(code: str, name: str = "", etf_type: str = ""):
    return {"ok": add_etf(code, name, etf_type)}


@router.delete("/etf/watchlist/{code}")
def api_remove_etf(code: str):
    return {"ok": remove_etf(code)}


@router.patch("/etf/watchlist/{code}/cost")
def api_update_etf_cost(code: str, body: CostBody):
    return {"ok": update_etf_cost(code, body.cost_price, body.shares)}


@router.get("/etf/search")
def api_etf_search(q: str = ""):
    return search_etf(q)


@router.get("/etf/{code}/kline")
def api_etf_kline(code: str, period: str = "daily"):
    ttl = _KLINE_TTL.get(period, 300)
    key = f"kline_etf_{code}_{period}" + ("" if period == "intraday" else f"_{_date.today()}")
    return get_cached(key, ttl, lambda: fetch_stock_kline(code, period))


@router.get("/{code}/kline")
def api_stock_kline(code: str, period: str = "daily"):
    ttl = _KLINE_TTL.get(period, 300)
    key = f"kline_{code}_{period}" + ("" if period == "intraday" else f"_{_date.today()}")
    return get_cached(key, ttl, lambda: fetch_stock_kline(code, period))


@router.get("/batch_quotes")
def api_batch_quotes(codes: str = ""):
    """批量查询任意股票/ETF 行情，codes 为逗号分隔的6位代码"""
    code_list = [c.strip() for c in codes.split(",") if c.strip() and len(c.strip()) == 6]
    if not code_list:
        return []
    return fetch_quotes(code_list)


@router.get("/vol_stats")
def api_vol_stats():
    """返回所有自选股今日量 / 20日均量比值，格式: {code: {ratio, avg_vol}}"""
    from data.watchlist_store import get_stocks
    key = f"vol_stats_{_date.today()}"

    def _compute():
        stocks = get_stocks()
        result = {}
        for item in stocks:
            code = item["code"]
            kkey = f"kline_{code}_daily_{_date.today()}"
            kdata = get_cached(kkey, 300, lambda c=code: fetch_stock_kline(c, "daily"))
            if kdata.get("type") == "kline" and kdata.get("data"):
                vols = [d["v"] for d in kdata["data"] if d.get("v", 0) > 0]
                if len(vols) >= 5:
                    avg_20 = sum(vols[-20:]) / min(len(vols), 20)
                    today_v = vols[-1]
                    ratio = round(today_v / avg_20, 2) if avg_20 > 0 else 1.0
                    result[code] = {"ratio": ratio, "avg_vol": avg_20, "today_vol": today_v}
        return result

    return get_cached(key, 300, _compute)


@router.get("/etf/vol_stats")
def api_etf_vol_stats():
    """返回所有自选 ETF 今日量 / 20日均量比值"""
    from data.watchlist_store import get_etfs
    key = f"etf_vol_stats_{_date.today()}"

    def _compute():
        etfs = get_etfs()
        result = {}
        for item in etfs:
            code = item["code"]
            kkey = f"kline_etf_{code}_daily_{_date.today()}"
            kdata = get_cached(kkey, 300, lambda c=code: fetch_stock_kline(c, "daily"))
            if kdata.get("type") == "kline" and kdata.get("data"):
                vols = [d["v"] for d in kdata["data"] if d.get("v", 0) > 0]
                if len(vols) >= 5:
                    avg_20 = sum(vols[-20:]) / min(len(vols), 20)
                    today_v = vols[-1]
                    ratio = round(today_v / avg_20, 2) if avg_20 > 0 else 1.0
                    result[code] = {"ratio": ratio, "avg_vol": avg_20, "today_vol": today_v}
        return result

    return get_cached(key, 300, _compute)


@router.get("/flow_rank")
def api_flow_rank():
    """自选股主力资金净流入排行（过滤全市场结果，仅返回持仓股）"""
    from data.watchlist_store import get_stocks
    key = f"flow_rank_{_date.today()}"
    codes = {item["code"] for item in get_stocks()}

    def _fetch():
        rows = fetch_stock_flow_rank_all("今日")
        if rows and "error" in rows[0]:
            return rows
        return [r for r in rows if str(r.get("code", "")).zfill(6) in codes
                or str(r.get("code", "")) in codes]

    return get_cached(key, 300, _fetch)


@router.get("/{code}/flow")
def api_stock_flow(code: str):
    market = "sh" if code.startswith(("6", "9")) else "sz"
    return fetch_stock_flow(code, market)
