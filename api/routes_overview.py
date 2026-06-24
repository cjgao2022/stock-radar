"""首页相关 API"""

from datetime import datetime, timezone, timedelta
from fastapi import APIRouter
from data.fetchers.indices import fetch_indices
from data.fetchers.flow import fetch_market_flow, fetch_zt_pool, fetch_industry_flow
from data.fetchers.market import fetch_market_breadth, fetch_lhb_today
from data.cache import (get_cached, load_board_snapshot,
                         load_breadth_history, load_zt_history, load_zt_dates,
                         load_lhb_history, load_lhb_dates,
                         save_breadth_history, save_zt_history, save_lhb_history)
import yaml
from pathlib import Path

router = APIRouter()
_cfg = yaml.safe_load(Path("config.yaml").read_text(encoding="utf-8"))
_BEIJING = timezone(timedelta(hours=8))
_TTL = _cfg["cache"]["flow_ttl_minutes"] * 60


def _today() -> str:
    return datetime.now(_BEIJING).strftime("%Y-%m-%d")


@router.get("/api/indices")
def api_indices():
    return get_cached("indices", 60, fetch_indices)


@router.get("/api/flow/market")
def api_flow_market():
    return get_cached("flow_market", _TTL, fetch_market_flow)


@router.get("/api/flow/industry")
def api_flow_industry():
    return get_cached("flow_industry", _TTL, fetch_industry_flow)



@router.get("/api/zt")
def api_zt():
    date_str = _today().replace("-", "")
    rows = get_cached(f"zt_{date_str}", _TTL, lambda: fetch_zt_pool(date_str))
    if rows and isinstance(rows, list) and "error" not in rows[0]:
        save_zt_history(_today(), rows)
    return rows


@router.get("/api/market/breadth")
def api_market_breadth():
    data = get_cached("market_breadth", 300, fetch_market_breadth)  # 全量拉取耗时~20s，5分钟缓存
    if isinstance(data, dict) and "error" not in data:
        save_breadth_history(_today(), data)
    return data


@router.get("/api/market/lhb")
def api_lhb():
    date_str = _today().replace("-", "")
    rows = get_cached(f"lhb_{date_str}", _TTL, lambda: fetch_lhb_today(date_str))
    if rows and isinstance(rows, list) and "error" not in rows[0]:
        save_lhb_history(_today(), rows)
    return rows


@router.get("/api/boards/snapshot")
def api_board_snapshot(board_type: str = "concept"):
    date = _today()
    rows = load_board_snapshot(date, board_type)
    return rows


@router.get("/api/market/breadth_history")
def api_breadth_history(days: int = 60):
    return load_breadth_history(days)


@router.get("/api/admin/bootstrap_history")
def api_bootstrap_history(days: int = 60):
    """一次性补齐历史快照（ZT/DT 计数 + LHB），耗时约 60-120 秒"""
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
