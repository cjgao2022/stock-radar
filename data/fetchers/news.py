"""公告 + 研报数据（东方财富 via AKShare）"""

import akshare as ak
from datetime import datetime, timezone, timedelta
from data.fetchers import _AK_LOCK
import data.watchlist_store as ws

_CST = timezone(timedelta(hours=8))


def _today_str() -> str:
    return datetime.now(_CST).strftime('%Y%m%d')


def _df_to_ann(df, fallback_code: str = "") -> list[dict]:
    results = []
    for _, row in df.iterrows():
        title = str(row.get("公告标题", ""))
        if not title or title == "nan":
            continue
        results.append({
            "code":  str(row.get("代码", fallback_code)),
            "name":  str(row.get("名称", "")),
            "title": title,
            "type":  str(row.get("公告类型", "")),
            "date":  str(row.get("公告日期", ""))[:10],
            "url":   str(row.get("网址", "")),
        })
    return results


def fetch_announcements_watchlist() -> list[dict]:
    """持仓股当日公告（东方财富 stock_individual_notice_report）"""
    today = _today_str()
    codes = [s["code"] for s in ws.get_stocks()]
    if not codes:
        return []

    results = []
    for code in codes[:20]:
        try:
            with _AK_LOCK:
                df = ak.stock_individual_notice_report(
                    security=code, symbol="全部",
                    begin_date=today, end_date=today,
                )
            if df is None or df.empty:
                continue
            results.extend(_df_to_ann(df, code))
        except Exception:
            continue

    results.sort(key=lambda x: x.get("date", ""), reverse=True)
    return results[:100]


def fetch_announcements_market() -> list[dict]:
    """全市场当日公告（东方财富 stock_notice_report）
    全量拉取约需 5-15 秒，路由缓存 30 分钟。
    """
    today = _today_str()
    try:
        with _AK_LOCK:
            df = ak.stock_notice_report(symbol="全部", date=today)
    except Exception as e:
        return [{"error": str(e)}]

    if df is None or df.empty:
        return []

    results = _df_to_ann(df)
    results.sort(key=lambda x: x.get("date", ""), reverse=True)
    return results[:300]


def fetch_research_reports(code: str = "") -> list[dict]:
    """东方财富个股研报
    code="":       合并所有持仓股研报，各取最新 20 条，按日期降序取前 60 条
    code="002050": 仅查该股全部历史研报
    """
    targets = [code] if code else [s["code"] for s in ws.get_stocks()]

    results = []
    for c in targets:
        try:
            with _AK_LOCK:
                df = ak.stock_research_report_em(symbol=c)
            if df is None or df.empty:
                continue
            limit = None if code else 20
            for _, row in (df if limit is None else df.head(limit)).iterrows():
                title = str(row.get("报告名称", ""))
                if not title or title == "nan":
                    continue
                results.append({
                    "code":        c,
                    "stock_name":  str(row.get("股票简称", "")),
                    "title":       title,
                    "rating":      str(row.get("东财评级", "")),
                    "institution": str(row.get("机构", "")),
                    "date":        str(row.get("日期", ""))[:10],
                    "url":         str(row.get("报告PDF链接", "")),
                })
        except Exception:
            continue

    results.sort(key=lambda x: x.get("date", ""), reverse=True)
    return results[:60] if not code else results
