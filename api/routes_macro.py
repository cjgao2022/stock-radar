"""宏观数据 API"""

from fastapi import APIRouter
from data.fetchers.macro import fetch_macro_indicators, fetch_macro_calendar
from data.fetchers.market_state import fetch_market_valuation, fetch_margin_trend
from data.cache import get_cached
from api import today_cst as _today, config as _cfg

router = APIRouter(prefix="/api/macro")
_IND_TTL = _cfg["cache"]["macro_indicators_ttl_seconds"]
_CAL_TTL = _cfg["cache"]["macro_calendar_ttl_seconds"]
_VAL_TTL = _cfg["cache"]["macro_valuation_ttl_seconds"]
_MARGIN_TTL = _cfg["cache"]["margin_ttl_seconds"]


@router.get("/indicators")
def api_macro_indicators():
    key = f"macro_ind_{_today()}"
    return get_cached(key, _IND_TTL, fetch_macro_indicators)


@router.get("/calendar")
def api_macro_calendar():
    key = f"macro_cal_{_today()}"
    return get_cached(key, _CAL_TTL, fetch_macro_calendar)


@router.get("/valuation")
def api_macro_valuation():
    key = f"mkt_val_{_today()}"
    return get_cached(key, _VAL_TTL, fetch_market_valuation)


@router.get("/margin")
def api_macro_margin():
    key = f"margin_{_today()}"
    return get_cached(key, _MARGIN_TTL, fetch_margin_trend)
