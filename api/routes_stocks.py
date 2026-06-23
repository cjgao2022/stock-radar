"""个股相关 API"""

from fastapi import APIRouter
from data.fetchers.stocks import fetch_watchlist, fetch_etf_watchlist, search_stock, search_etf
from data.fetchers.flow import fetch_stock_flow
from data.watchlist_store import add_stock, remove_stock, add_etf, remove_etf

router = APIRouter(prefix="/api/stocks")


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


@router.get("/{code}/flow")
def api_stock_flow(code: str):
    market = "sh" if code.startswith(("6", "9")) else "sz"
    return fetch_stock_flow(code, market)
