"""个股相关 API"""

from typing import Optional
from api import today_cst as _today, config as _cfg
from fastapi import APIRouter, Path
from pydantic import BaseModel
from data.fetchers.stocks import fetch_watchlist, fetch_etf_watchlist, search_stock, search_etf, fetch_stock_kline, fetch_quotes, fetch_etf_meta
from data.fetchers.flow import fetch_stock_flow, fetch_stock_flow_rank_all
from data.fetchers.fundamentals import fetch_stock_fundamental, fetch_stock_financials_history
from data.fetchers.valuation_stock import fetch_stock_valuation
from data.watchlist_store import add_stock, remove_stock, add_etf, remove_etf, update_stock_cost, update_etf_cost
from data.cache import get_cached

_CodePath = Path(pattern=r"^\d{6}$")


class CostBody(BaseModel):
    cost_price: Optional[float] = None
    shares: Optional[float] = None

router = APIRouter(prefix="/api/stocks")
_KLINE_TTL = {"intraday": 60, "daily": 300, "weekly": 1800, "monthly": 3600, "yearly": 3600}
_VOL_STATS_TTL = _cfg["cache"]["vol_stats_ttl_seconds"]
_ETF_META_TTL = _cfg["cache"]["etf_meta_ttl_seconds"]
_FLOW_RANK_TTL = _cfg["cache"]["flow_rank_ttl_seconds"]
_FUNDAMENTALS_TTL = _cfg["cache"]["fundamentals_ttl_seconds"]


@router.get("/watchlist")
def api_watchlist():
    return fetch_watchlist()


@router.post("/watchlist/{code}")
def api_add_stock(code: str = _CodePath, name: str = ""):
    return {"ok": add_stock(code, name)}


@router.delete("/watchlist/{code}")
def api_remove_stock(code: str = _CodePath):
    return {"ok": remove_stock(code)}


@router.patch("/watchlist/{code}/cost")
def api_update_stock_cost(body: CostBody, code: str = _CodePath):
    return {"ok": update_stock_cost(code, body.cost_price, body.shares)}


@router.get("/search")
def api_search(q: str = ""):
    return search_stock(q)


@router.get("/etf/watchlist")
def api_etf_watchlist():
    return fetch_etf_watchlist()


@router.post("/etf/watchlist/{code}")
def api_add_etf(code: str = _CodePath, name: str = "", etf_type: str = ""):
    return {"ok": add_etf(code, name, etf_type)}


@router.delete("/etf/watchlist/{code}")
def api_remove_etf(code: str = _CodePath):
    return {"ok": remove_etf(code)}


@router.patch("/etf/watchlist/{code}/cost")
def api_update_etf_cost(body: CostBody, code: str = _CodePath):
    return {"ok": update_etf_cost(code, body.cost_price, body.shares)}


@router.get("/etf/search")
def api_etf_search(q: str = ""):
    return search_etf(q)


@router.get("/etf/{code}/kline")
def api_etf_kline(code: str, period: str = "daily"):
    ttl = _KLINE_TTL.get(period, _KLINE_TTL["daily"])
    key = f"kline_etf_{code}_{period}" + ("" if period == "intraday" else f"_{_today()}")
    return get_cached(key, ttl, lambda: fetch_stock_kline(code, period))


@router.get("/{code}/kline")
def api_stock_kline(code: str, period: str = "daily"):
    ttl = _KLINE_TTL.get(period, _KLINE_TTL["daily"])
    key = f"kline_{code}_{period}" + ("" if period == "intraday" else f"_{_today()}")
    return get_cached(key, ttl, lambda: fetch_stock_kline(code, period))


@router.get("/batch_quotes")
def api_batch_quotes(codes: str = ""):
    """批量查询任意股票/ETF 行情，codes 为逗号分隔的6位代码"""
    code_list = [c.strip() for c in codes.split(",") if c.strip() and len(c.strip()) == 6]
    if not code_list:
        return []
    return fetch_quotes(code_list)


def _vol_stat_from_kline(kdata: dict) -> Optional[dict]:
    if kdata.get("type") == "kline" and kdata.get("data"):
        vols = [d["v"] for d in kdata["data"] if d.get("v", 0) > 0]
        if len(vols) >= 5:
            avg_20 = sum(vols[-20:]) / min(len(vols), 20)
            today_v = vols[-1]
            ratio = round(today_v / avg_20, 2) if avg_20 > 0 else 1.0
            return {"ratio": ratio, "avg_vol": avg_20, "today_vol": today_v}
    return None


def _compute_vol_stats(codes: list[str], kkey_prefix: str) -> dict:
    """并发拉取多只股票/ETF的日K线计算量比，各请求相互独立（无需 _AK_LOCK）"""
    from concurrent.futures import ThreadPoolExecutor

    def _one(code: str):
        kkey = f"{kkey_prefix}_{code}_daily_{_today()}"
        kdata = get_cached(kkey, _KLINE_TTL["daily"], lambda: fetch_stock_kline(code, "daily"))
        return code, _vol_stat_from_kline(kdata)

    result = {}
    if not codes:
        return result
    with ThreadPoolExecutor(max_workers=min(8, len(codes))) as pool:
        for code, stat in pool.map(_one, codes):
            if stat is not None:
                result[code] = stat
    return result


@router.get("/vol_stats")
def api_vol_stats():
    """返回所有自选股今日量 / 20日均量比值，格式: {code: {ratio, avg_vol}}"""
    from data.watchlist_store import get_stocks
    key = f"vol_stats_{_today()}"
    codes = [item["code"] for item in get_stocks()]
    return get_cached(key, _VOL_STATS_TTL, lambda: _compute_vol_stats(codes, "kline"))


@router.get("/etf/vol_stats")
def api_etf_vol_stats():
    """返回所有自选 ETF 今日量 / 20日均量比值"""
    from data.watchlist_store import get_etfs
    key = f"etf_vol_stats_{_today()}"
    codes = [item["code"] for item in get_etfs()]
    return get_cached(key, _VOL_STATS_TTL, lambda: _compute_vol_stats(codes, "kline_etf"))


@router.get("/etf/meta")
def api_etf_meta():
    """ETF 规模(亿元)和折溢价率(%)，数据源：东方财富 fund_etf_spot_em。"""
    from data.watchlist_store import get_etfs
    etfs = get_etfs()
    codes = [item["code"] for item in etfs]
    if not codes:
        return {}
    key = f"etf_meta_{_today()}"
    return get_cached(key, _ETF_META_TTL, lambda: fetch_etf_meta(codes))


@router.get("/flow_rank")
def api_flow_rank():
    """自选股主力资金净流入排行（过滤全市场结果，仅返回持仓股）"""
    from data.watchlist_store import get_stocks
    key = f"flow_rank_{_today()}"
    codes = {item["code"] for item in get_stocks()}

    def _fetch():
        rows = fetch_stock_flow_rank_all()
        if rows and "error" in rows[0]:
            return rows
        return [r for r in rows if str(r.get("code", "")).zfill(6) in codes
                or str(r.get("code", "")) in codes]

    return get_cached(key, _FLOW_RANK_TTL, _fetch)


@router.get("/fundamentals")
def api_fundamentals(codes: str = ""):
    """返回个股基本面快照（eps/bvps/roe/profit_yoy），格式: {code: {...}}
    error 响应不缓存。
    """
    today = _today()
    code_list = [c.strip() for c in codes.split(",") if c.strip() and len(c.strip()) == 6]
    if not code_list:
        return {}
    result = {}
    for code in code_list:
        key = f"fund_{code}_{today}"
        result[code] = get_cached(key, _FUNDAMENTALS_TTL, lambda c=code: fetch_stock_fundamental(c))
    return result


@router.get("/{code}/financials")
def api_stock_financials(code: str):
    """个股近8期财务指标（THS）"""
    today = _today()
    key = f"financials_{code}_{today}"
    return get_cached(key, _FUNDAMENTALS_TTL, lambda: fetch_stock_financials_history(code))


@router.get("/{code}/valuation")
def api_stock_valuation(code: str):
    """个股 PE(TTM)/PB 当前值 + 近1年历史分位（百度股市通）"""
    today = _today()
    key = f"val_{code}_{today}"
    return get_cached(key, _FUNDAMENTALS_TTL, lambda: fetch_stock_valuation(code))


@router.get("/{code}/flow")
def api_stock_flow(code: str):
    if code.startswith(("83", "87", "43", "92")):
        market = "bj"
    elif code.startswith(("6", "9")):
        market = "sh"
    else:
        market = "sz"
    return fetch_stock_flow(code, market)
