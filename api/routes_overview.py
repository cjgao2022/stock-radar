"""首页相关 API"""

from fastapi import APIRouter
from api import today_cst as _today, config as _cfg
from data.fetchers.indices import fetch_indices
from data.fetchers.flow import fetch_zt_pool, fetch_industry_flow
from data.fetchers.market import fetch_market_breadth, fetch_lhb_today
from data.cache import (get_cached,
                         load_breadth_history, load_zt_history, load_zt_dates,
                         load_lhb_history, load_lhb_dates,
                         save_breadth_history, save_zt_history, save_lhb_history)

router = APIRouter()
_TTL = _cfg["cache"]["flow_ttl_minutes"] * 60
_INDICES_TTL = _cfg["cache"]["indices_ttl_seconds"]
_BREADTH_TTL = _cfg["cache"]["market_breadth_ttl_seconds"]


@router.get("/api/indices")
def api_indices():
    return get_cached("indices", _INDICES_TTL, fetch_indices)


@router.get("/api/flow/industry")
def api_flow_industry():
    return get_cached("flow_industry", _TTL, fetch_industry_flow)



@router.get("/api/zt")
def api_zt():
    date_str = _today().replace("-", "")
    fetched = False

    def _fetch():
        nonlocal fetched
        fetched = True
        return fetch_zt_pool(date_str)

    rows = get_cached(f"zt_{date_str}", _TTL, _fetch)
    # 只在真正触发了上游请求（缓存未命中）时才写库，命中缓存时数据未变无需重复写入
    if fetched and rows and isinstance(rows, list) and "error" not in rows[0]:
        save_zt_history(_today(), rows)
    return rows


@router.get("/api/market/breadth")
def api_market_breadth():
    fetched = False

    def _fetch():
        nonlocal fetched
        fetched = True
        return fetch_market_breadth()

    data = get_cached("market_breadth", _BREADTH_TTL, _fetch)  # 全量拉取耗时~20s
    if fetched and isinstance(data, dict) and "error" not in data:
        indices = get_cached("indices", _INDICES_TTL, fetch_indices)
        amount = None
        if isinstance(indices, list):
            amount = sum(
                d.get("amount", 0) for d in indices
                if any(k in d.get("name", "") for k in ("上证", "深证"))
                and (d.get("amount") or 0) > 0
            ) or None
        save_breadth_history(_today(), {**data, "amount": amount})
    return data


@router.get("/api/market/lhb")
def api_lhb():
    date_str = _today().replace("-", "")
    fetched = False

    def _fetch():
        nonlocal fetched
        fetched = True
        return fetch_lhb_today(date_str)

    rows = get_cached(f"lhb_{date_str}", _TTL, _fetch)
    if fetched and rows and isinstance(rows, list) and "error" not in rows[0]:
        save_lhb_history(_today(), rows)
    return rows


@router.get("/api/market/breadth_history")
def api_breadth_history(days: int = 60):
    return load_breadth_history(days)


@router.post("/api/admin/bootstrap_history")
def api_bootstrap_history(days: int = 60):
    """一次性补齐历史快照（ZT/DT 计数 + LHB），耗时约 60-120 秒。
    用 POST 而非 GET：这是一个昂贵的写操作，GET 可能被浏览器预取/爬虫/代理意外触发。
    """
    from data.scheduler import bootstrap_breadth_history
    result = bootstrap_breadth_history(days)
    return result


@router.get("/api/market/zt_history")
def api_zt_history(date: str = ""):
    if not date:
        dates = load_zt_dates(1)
        date = dates[0] if dates else _today()
    return {"date": date, "dates": load_zt_dates(10), "rows": load_zt_history(date)}


@router.get("/api/market/lhb_history")
def api_lhb_history(date: str = ""):
    if not date:
        dates = load_lhb_dates(1)
        date = dates[0] if dates else _today()
    return {"date": date, "dates": load_lhb_dates(10), "rows": load_lhb_history(date)}
