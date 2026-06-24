"""公告 + 研报 API"""

from fastapi import APIRouter, Query
from data.fetchers.news import (
    fetch_announcements_watchlist,
    fetch_announcements_market,
    fetch_research_reports,
)
from data.cache import get_cached
from datetime import date as _date

router = APIRouter(prefix="/api/news")


@router.get("/announcements")
def api_announcements(scope: str = Query("watchlist", pattern="^(watchlist|market)$")):
    today = str(_date.today())
    key = f"ann_{scope}_{today}"
    ttl = 1800  # 30 分钟
    fn = fetch_announcements_watchlist if scope == "watchlist" else fetch_announcements_market
    return get_cached(key, ttl, fn)


@router.get("/research")
def api_research(code: str = Query("")):
    today = str(_date.today())
    key = f"research_{code or 'all'}_{today}"
    return get_cached(key, 3600, lambda: fetch_research_reports(code))
