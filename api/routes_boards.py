"""板块相关 API"""

from fastapi import APIRouter
from api import today_cst as _today, config as _cfg
from data.fetchers.boards import fetch_board_list, fetch_board_constituents, fetch_board_kline
from data.cache import get_cached, load_board_snapshot, save_board_constituents, load_board_constituents, load_board_rotation

router = APIRouter(prefix="/api/boards")
_TTL = _cfg["cache"]["board_ttl_minutes"] * 60
_LONG_KLINE_TTL = _cfg["cache"]["board_kline_long_ttl_seconds"]

_SORT_WHITELIST = {
    "name", "change_pct", "mkt_cap", "net", "up_count", "down_count",
    "top_stock_chg", "company_count", "turnover_rate",
}


@router.get("")
def api_board_list(board_type: str = "concept", sort: str = "change_pct", order: str = "desc"):
    date = _today()
    # 优先读 SQLite 日快照，无快照再实时拉
    rows = load_board_snapshot(date, board_type)
    if not rows or "error" in rows[0]:
        rows = get_cached(f"board_{board_type}_{date}", _TTL, lambda: fetch_board_list(board_type))

    sort_key = sort if sort in _SORT_WHITELIST else "change_pct"
    reverse = order == "desc"
    try:
        rows = sorted(rows, key=lambda r: (r.get(sort_key) or 0), reverse=reverse)
    except Exception:
        pass
    return rows


@router.get("/rotation")
def api_board_rotation(board_type: str = "industry"):
    """板块多周期轮动数据（从 board_snapshot 历史快照计算）"""
    return load_board_rotation(board_type)


@router.get("/{board_type}/{board_name}/kline")
def api_board_kline(board_type: str, board_name: str, days: int = 30, period: str = "daily"):
    date = _today()
    if period in ("monthly", "yearly"):
        key = f"kline_{board_type}_{board_name}_{period}_{date}"
        ttl = _LONG_KLINE_TTL
    else:
        key = f"kline_{board_type}_{board_name}_{days}_{date}"
        ttl = _TTL
    return get_cached(key, ttl, lambda: fetch_board_kline(board_type, board_name, days, period))


@router.get("/{board_type}/{board_name}/constituents")
def api_constituents(board_type: str, board_name: str):
    date = _today()
    # 当日 SQLite 缓存
    cached = load_board_constituents(date, board_type, board_name)
    if cached:
        return cached

    rows = fetch_board_constituents(board_type, board_name)
    if rows and "error" not in rows[0]:
        save_board_constituents(date, board_type, board_name, rows)
    return rows
