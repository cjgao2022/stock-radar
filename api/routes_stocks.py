"""个股相关 API"""

from datetime import date as _date
from fastapi import APIRouter
from data.fetchers.stocks import fetch_watchlist, fetch_etf_watchlist, search_stock, search_etf, fetch_stock_kline
from data.fetchers.flow import fetch_stock_flow
from data.watchlist_store import add_stock, remove_stock, add_etf, remove_etf
from data.cache import get_cached

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


@router.get("/{code}/flow")
def api_stock_flow(code: str):
    market = "sh" if code.startswith(("6", "9")) else "sz"
    return fetch_stock_flow(code, market)
