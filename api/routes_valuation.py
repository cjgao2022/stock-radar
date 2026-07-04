"""行业估值 API"""

from fastapi import APIRouter
from data.fetchers.valuation import fetch_industry_pe_cninfo
from data.cache import get_cached
from api import today_cst as _today, config as _cfg

router = APIRouter(prefix="/api/valuation")
_TTL = _cfg["cache"]["industry_pe_ttl_seconds"]


@router.get("/industry_pe")
def api_industry_pe():
    """证监会行业分类市盈率（巨潮）"""
    key = f"industry_pe_cninfo_{_today()}"
    return get_cached(key, _TTL, fetch_industry_pe_cninfo)
