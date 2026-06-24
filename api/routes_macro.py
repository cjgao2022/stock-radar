"""宏观数据 API"""

from fastapi import APIRouter
from data.fetchers.macro import fetch_macro_indicators, fetch_macro_calendar
from data.cache import get_cached
from datetime import date as _date

router = APIRouter(prefix="/api/macro")


@router.get("/indicators")
def api_macro_indicators():
    key = f"macro_ind_{_date.today()}"
    return get_cached(key, 86400, fetch_macro_indicators)


@router.get("/calendar")
def api_macro_calendar():
    key = f"macro_cal_{_date.today()}"
    return get_cached(key, 86400, fetch_macro_calendar)
