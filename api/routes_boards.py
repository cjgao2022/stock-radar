"""板块相关 API"""

from datetime import datetime, timezone, timedelta
from fastapi import APIRouter
from data.fetchers.boards import fetch_board_list, fetch_board_constituents, fetch_board_kline
from data.cache import get_cached, load_board_snapshot, save_board_constituents, load_board_constituents
from pathlib import Path
import yaml

router = APIRouter(prefix="/api/boards")
_cfg = yaml.safe_load(Path("config.yaml").read_text(encoding="utf-8"))
_BEIJING = timezone(timedelta(hours=8))
_TTL = _cfg["cache"]["board_ttl_minutes"] * 60


def _today() -> str:
    return datetime.now(_BEIJING).strftime("%Y-%m-%d")


@router.get("")
def api_board_list(board_type: str = "concept", sort: str = "change_pct", order: str = "desc"):
    date = _today()
    # 优先读 SQLite 日快照，无快照再实时拉
    rows = load_board_snapshot(date, board_type)
    if not rows or "error" in rows[0]:
        rows = get_cached(f"board_{board_type}", _TTL, lambda: fetch_board_list(board_type))

    reverse = order == "desc"
    try:
        rows = sorted(rows, key=lambda r: (r.get(sort) or 0), reverse=reverse)
    except Exception:
        pass
    return rows


@router.get("/{board_type}/{board_name}/kline")
def api_board_kline(board_type: str, board_name: str, days: int = 30, period: str = "daily"):
    date = _today()
    if period in ("monthly", "yearly"):
        key = f"kline_{board_type}_{board_name}_{period}_{date}"
        ttl = 3600
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
