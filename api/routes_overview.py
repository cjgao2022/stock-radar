"""首页相关 API"""

from datetime import datetime, timezone, timedelta
from fastapi import APIRouter
from data.fetchers.indices import fetch_indices
from data.fetchers.flow import fetch_market_flow, fetch_zt_pool, fetch_industry_flow
from data.fetchers.market import fetch_market_breadth, fetch_north_flow, fetch_lhb_today
from data.cache import get_cached, load_board_snapshot
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
    date = _today().replace("-", "")
    return get_cached(f"zt_{date}", _TTL, lambda: fetch_zt_pool(date))


@router.get("/api/market/breadth")
def api_market_breadth():
    return get_cached("market_breadth", 60, fetch_market_breadth)


@router.get("/api/market/north")
def api_north_flow():
    return get_cached("north_flow", 60, fetch_north_flow)


@router.get("/api/market/lhb")
def api_lhb():
    date = _today().replace("-", "")
    return get_cached(f"lhb_{date}", _TTL, fetch_lhb_today)


@router.get("/api/boards/snapshot")
def api_board_snapshot(board_type: str = "concept"):
    date = _today()
    rows = load_board_snapshot(date, board_type)
    return rows
