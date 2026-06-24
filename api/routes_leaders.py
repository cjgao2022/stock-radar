"""行业龙头 API"""

from fastapi import APIRouter
from data.fetchers.leaders import fetch_leaders
from data.cache import get_cached
from datetime import date as _date

router = APIRouter(prefix="/api/leaders")


@router.get("")
def api_leaders():
    key = f"leaders_{_date.today()}"
    return get_cached(key, 1800, fetch_leaders)  # 30分钟缓存
