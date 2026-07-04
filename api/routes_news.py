"""公告 + 研报 API"""

from fastapi import APIRouter, Query
from data.fetchers.news import (
    fetch_announcements_watchlist,
    fetch_announcements_market,
    fetch_research_reports,
)
from data.cache import get_cached
from api import today_cst as _today, config as _cfg

router = APIRouter(prefix="/api/news")
_ANN_TTL = _cfg["cache"]["announcements_ttl_seconds"]
_RESEARCH_TTL = _cfg["cache"]["research_ttl_seconds"]


@router.get("/announcements")
def api_announcements(scope: str = Query("watchlist", pattern="^(watchlist|market)$")):
    today = _today()
    key = f"ann_{scope}_{today}"
    fn = fetch_announcements_watchlist if scope == "watchlist" else fetch_announcements_market
    return get_cached(key, _ANN_TTL, fn)


@router.get("/research")
def api_research(code: str = Query("")):
    today = _today()
    key = f"research_{code or 'all'}_{today}"
    return get_cached(key, _RESEARCH_TTL, lambda: fetch_research_reports(code))
