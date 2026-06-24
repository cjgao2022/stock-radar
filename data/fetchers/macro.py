"""宏观数据：CPI、PPI、PMI、M2 历史走势 + 即将发布日历

历史走势用无后缀函数（降序，有 2026 年数据）：
  macro_china_cpi / ppi / pmi / money_supply
发布日历用 _yearly/_monthly 函数（有计划发布日期字段）。
"""

import math
import re
import akshare as ak
from datetime import date, datetime, timedelta
from data.fetchers import _AK_LOCK

# 历史走势用接口（降序，head=最新）
_HIST_INDICATORS = {
    "cpi": ("macro_china_cpi",          "全国-同比增长",            "CPI 年率(%)"),
    "ppi": ("macro_china_ppi",          "当月同比增长",              "PPI 年率(%)"),
    "pmi": ("macro_china_pmi",          "制造业-指数",              "PMI（制造业）"),
    "m2":  ("macro_china_money_supply", "货币和准货币(M2)-同比增长", "M2 年率(%)"),
}

# 发布日历用接口（升序，tail=最新，有 NaN 计划行）
_CAL_INDICATORS = {
    "cpi": ("macro_china_cpi_yearly",  "CPI 年率(%)"),
    "ppi": ("macro_china_ppi_yearly",  "PPI 年率(%)"),
    "pmi": ("macro_china_pmi_yearly",  "PMI（制造业）"),
    "m2":  ("macro_china_m2_yearly",   "M2 年率(%)"),
}


def _safe_float(v) -> float | None:
    if v is None:
        return None
    try:
        f = float(v)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except Exception:
        return None


def _parse_month(s: str) -> str:
    """'2026年05月份' → '2026-05'"""
    m = re.match(r'(\d{4})年(\d{2})月份?', str(s))
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    return str(s)[:7]


def _date_str(d) -> str:
    if hasattr(d, 'strftime'):
        return d.strftime('%Y-%m-%d')
    return str(d)[:10]


def _to_date(d) -> date | None:
    if hasattr(d, 'date'):
        return d.date()
    if isinstance(d, date):
        return d
    try:
        return datetime.strptime(str(d)[:10], '%Y-%m-%d').date()
    except Exception:
        return None


def fetch_macro_indicators() -> dict:
    """
    返回 {cpi, ppi, pmi, m2}，每项：
      {label, hist: [{date, value}], latest, prev, last_date}
    数据来自无后缀函数（降序），取 head(36) 后翻转为升序。
    """
    result = {}
    for key, (fn_name, col, label) in _HIST_INDICATORS.items():
        try:
            with _AK_LOCK:
                df = getattr(ak, fn_name)()
            if df is None or df.empty:
                result[key] = {"label": label, "hist": [], "latest": None, "prev": None, "last_date": None}
                continue
            # 降序，取最近 36 期，翻转为升序
            recent = df.head(36).iloc[::-1].reset_index(drop=True)
            hist = []
            for _, row in recent.iterrows():
                v = _safe_float(row[col])
                if v is not None:
                    hist.append({"date": _parse_month(row['月份']), "value": v})
            latest = hist[-1]["value"] if hist else None
            prev   = hist[-2]["value"] if len(hist) >= 2 else None
            last_d = hist[-1]["date"]  if hist else None
            result[key] = {"label": label, "hist": hist, "latest": latest, "prev": prev, "last_date": last_d}
        except Exception as e:
            result[key] = {"label": label, "hist": [], "latest": None, "prev": None, "last_date": None, "error": str(e)}
    return result


def fetch_macro_calendar() -> list[dict]:
    """
    从 _yearly/_monthly 接口提取今值为 NaN 的未来计划发布日：
    [{date, name, prev, forecast}]，按日期升序，90 天内
    """
    today = date.today()
    end   = today + timedelta(days=90)
    events = []
    for key, (fn_name, label) in _CAL_INDICATORS.items():
        try:
            with _AK_LOCK:
                df = getattr(ak, fn_name)()
            if df is None or df.empty:
                continue
            future = df[df['今值'].isna()].copy()
            for _, row in future.iterrows():
                d = _to_date(row['日期'])
                if d is None:
                    continue
                if today <= d <= end:
                    events.append({
                        "date":     d.strftime('%Y-%m-%d'),
                        "name":     label,
                        "prev":     _safe_float(row.get('前值')),
                        "forecast": _safe_float(row.get('预测值')),
                    })
        except Exception:
            continue
    events.sort(key=lambda x: x['date'])
    return events
