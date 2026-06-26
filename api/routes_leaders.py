"""行业龙头 API"""

from fastapi import APIRouter
from data.fetchers.leaders import fetch_leaders, fetch_leaders_second
from data.cache import get_cached
from datetime import date as _date

router = APIRouter(prefix="/api/leaders")


@router.get("")
def api_leaders():
    key = f"leaders_{_date.today()}"
    return get_cached(key, 1800, fetch_leaders)  # 30分钟缓存


@router.get("/level2")
def api_leaders_level2():
    key = f"leaders_l2_{_date.today()}"
    return get_cached(key, 1800, fetch_leaders_second)  # 30分钟缓存
