"""个股估值历史分位：PE(TTM) / PB 近1年分位（百度股市通，非 push2，代理封锁下可用）"""
import re
import time

_cache: dict[str, tuple] = {}   # code -> (result, ts)
_TTL = 21600  # 6h — 估值日频更新


def _pure_code(code: str) -> str:
    """提取 6 位纯数字代码（兼容 sh600519 / 600519.SH 等格式）"""
    m = re.search(r"\d{6}", code or "")
    return m.group(0) if m else (code or "")


def _label(pct: float | None) -> tuple[str, str]:
    """按历史分位分档，与 market_state 口径一致（低/合理/高）"""
    if pct is None:
        return "数据不足", "orange"
    if pct < 30:
        return "低估区间", "green"
    if pct < 70:
        return "合理区间", "orange"
    return "高估区间", "red"


def fetch_stock_valuation(code: str) -> dict:
    """
    个股 PE(TTM) / PB 当前值 + 近1年历史分位。

    Returns dict:
      pe_ttm      — 当前 PE(TTM)
      pe_pct      — PE 近1年分位 (0-100，越低越便宜)
      pe_label / pe_color   — 低估/合理/高估 区间 + 颜色
      pb          — 当前 PB
      pb_pct      — PB 近1年分位
      pb_label / pb_color
      as_of       — 数据日期
    失败返回 {'error': str}
    """
    pure = _pure_code(code)
    now = time.time()
    hit = _cache.get(pure)
    if hit and now - hit[1] < _TTL:
        return hit[0]

    try:
        import akshare as ak
        import pandas as pd

        def _series(indicator: str) -> "pd.Series":
            df = ak.stock_zh_valuation_baidu(symbol=pure, indicator=indicator, period="近一年")
            df = df.copy()
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
            df["date"] = pd.to_datetime(df["date"])
            return df.dropna(subset=["value"]).set_index("date").sort_index()["value"]

        def _cur_pct(s: "pd.Series") -> tuple[float | None, float | None, str | None]:
            if s is None or len(s) < 2:
                return None, None, None
            cur = float(s.iloc[-1])
            pct = round(100 * (s < cur).sum() / len(s), 1)
            return round(cur, 2), pct, s.index[-1].strftime("%Y-%m-%d")

        pe_s = _series("市盈率(TTM)")
        pb_s = _series("市净率")

        pe_ttm, pe_pct, as_of = _cur_pct(pe_s)
        pb, pb_pct, pb_as_of = _cur_pct(pb_s)
        pe_label, pe_color = _label(pe_pct)
        pb_label, pb_color = _label(pb_pct)

        result = {
            "pe_ttm":   pe_ttm,
            "pe_pct":   pe_pct,
            "pe_label": pe_label,
            "pe_color": pe_color,
            "pb":       pb,
            "pb_pct":   pb_pct,
            "pb_label": pb_label,
            "pb_color": pb_color,
            "as_of":    as_of or pb_as_of,
        }
        _cache[pure] = (result, now)
        return result

    except Exception as e:
        return {"error": str(e)}
