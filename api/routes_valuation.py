"""行业估值 API"""

from fastapi import APIRouter
from data.fetchers.valuation import fetch_industry_pe_cninfo
from data.cache import get_cached
from datetime import date as _date

router = APIRouter(prefix="/api/valuation")


@router.get("/industry_pe")
def api_industry_pe():
    """证监会行业分类市盈率（巨潮），按日缓存 1 小时"""
    key = f"industry_pe_cninfo_{_date.today()}"
    return get_cached(key, 3600, fetch_industry_pe_cninfo)
