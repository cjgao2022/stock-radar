"""行业龙头 API"""

from fastapi import APIRouter
from data.fetchers.leaders import fetch_leaders, fetch_leaders_second
from data.cache import get_cached
from api import today_cst as _today, config as _cfg

router = APIRouter(prefix="/api/leaders")
_TTL = _cfg["cache"]["leaders_ttl_seconds"]


@router.get("")
def api_leaders():
    key = f"leaders_{_today()}"
    return get_cached(key, _TTL, fetch_leaders)


@router.get("/level2")
def api_leaders_level2():
    key = f"leaders_l2_{_today()}"
    return get_cached(key, _TTL, fetch_leaders_second)
