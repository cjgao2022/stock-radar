"""全A市场估值温度：PE历史分位 + 股债比价（ERP）+ 融资余额趋势"""
import time
from data.fetchers import _AK_LOCK

_cache: tuple | None = None
_TTL = 3600  # 1h — PE数据每日更新，1h足够


def fetch_market_valuation() -> dict:
    """
    全A滚动PE历史分位 + 权益风险溢价（ERP）

    Returns dict:
      pe          — 当前全A滚动市盈率
      date        — PE数据日期
      pe_5y_pct   — 近5年历史分位 (0-100)
      pe_10y_pct  — 近10年历史分位 (0-100)
      label       — 低估区间 / 合理区间 / 高估区间
      label_color — green / orange / red
      bond_yield  — 10年期国债收益率 (%)
      erp         — 权益风险溢价 = (1/PE)*100 - bond_yield (%)
      chart_dates — 历史日期列表（近5年每5日采样）
      chart_pe    — 历史PE值列表
      chart_erp   — 历史ERP值列表（与bond数据能对齐时填充，否则 null）
    """
    global _cache
    now = time.time()
    if _cache and now - _cache[1] < _TTL:
        return _cache[0]

    try:
        import akshare as ak
        import pandas as pd
        from datetime import datetime, timedelta

        # ── 全A PE历史（2005至今，日频） ───────────────────────────────
        with _AK_LOCK:
            pe_raw = ak.stock_index_pe_lg()

        pe_df = pe_raw[['日期', '滚动市盈率']].copy()
        pe_df.columns = ['date', 'pe']
        pe_df['pe'] = pd.to_numeric(pe_df['pe'], errors='coerce')
        pe_df['date'] = pd.to_datetime(pe_df['date'])
        pe_df = pe_df.dropna().set_index('date').sort_index()

        current_pe = float(pe_df['pe'].iloc[-1])
        current_date = pe_df.index[-1].strftime('%Y-%m-%d')

        # ── 历史分位（5年、10年） ──────────────────────────────────────
        def pct_rank(years: int, val: float) -> float | None:
            cutoff = pd.Timestamp.now() - pd.Timedelta(days=365 * years)
            s = pe_df.loc[pe_df.index >= cutoff, 'pe']
            return round(100 * (s < val).sum() / len(s), 1) if len(s) >= 2 else None

        pct_5y = pct_rank(5, current_pe)
        pct_10y = pct_rank(10, current_pe)

        ref = pct_10y if pct_10y is not None else pct_5y
        if ref is None or ref < 30:
            label, label_color = '低估区间', 'green'
        elif ref < 70:
            label, label_color = '合理区间', 'orange'
        else:
            label, label_color = '高估区间', 'red'

        # ── 10年国债收益率（日频） ─────────────────────────────────────
        start_dt = (datetime.now() - timedelta(days=365 * 5 + 60)).strftime('%Y%m%d')
        bond_yield: float | None = None
        bond_series: dict = {}
        try:
            with _AK_LOCK:
                bond_raw = ak.bond_zh_us_rate(start_date=start_dt)
            bond_df = bond_raw[['日期', '中国国债收益率10年']].copy()
            bond_df.columns = ['date', 'yield']
            bond_df['yield'] = pd.to_numeric(bond_df['yield'], errors='coerce')
            bond_df['date'] = pd.to_datetime(bond_df['date'])
            bond_df = bond_df.dropna().set_index('date').sort_index()
            bond_yield = float(bond_df['yield'].iloc[-1])
            bond_series = bond_df['yield'].to_dict()  # Timestamp → float
        except Exception:
            pass

        current_erp: float | None = None
        if bond_yield is not None and current_pe > 0:
            current_erp = round(100 / current_pe - bond_yield, 2)

        # ── 历史图表（近5年，每5日采样 → ~260点） ─────────────────────
        cutoff_5y = pd.Timestamp.now() - pd.Timedelta(days=365 * 5)
        pe_chart = pe_df.loc[pe_df.index >= cutoff_5y, 'pe'].iloc[::5]

        chart_dates, chart_pe, chart_erp = [], [], []
        for ts, pe_val in pe_chart.items():
            if pe_val <= 0:
                continue
            # 找最近5日内的债券收益率
            by: float | None = None
            for delta in range(6):
                cand = ts - pd.Timedelta(days=delta)
                if cand in bond_series:
                    by = float(bond_series[cand])
                    break
            chart_dates.append(ts.strftime('%Y-%m-%d'))
            chart_pe.append(round(float(pe_val), 2))
            chart_erp.append(round(100 / pe_val - by, 2) if by else None)

        result = {
            'pe':           round(current_pe, 2),
            'date':         current_date,
            'pe_5y_pct':    pct_5y,
            'pe_10y_pct':   pct_10y,
            'label':        label,
            'label_color':  label_color,
            'bond_yield':   round(bond_yield, 4) if bond_yield is not None else None,
            'erp':          current_erp,
            'chart_dates':  chart_dates,
            'chart_pe':     chart_pe,
            'chart_erp':    chart_erp,
        }
        _cache = (result, now)
        return result

    except Exception as e:
        return {'error': str(e)}


# ── 融资余额趋势 ─────────────────────────────────────────────────────────────
_margin_cache: tuple | None = None
_MARGIN_TTL = 3600  # 1h


def fetch_margin_trend() -> dict:
    """
    全市场融资余额趋势（股票数据，每日更新）

    Returns dict:
      current   — 最新融资余额（亿元）
      date      — 数据日期
      chg_5d    — 近5日变化（亿元）
      chg_5d_pct— 近5日变化率（%）
      chg_20d   — 近20日变化（亿元）
      history   — 近120日 [{date, balance, buy}, ...]
    """
    global _margin_cache
    now = time.time()
    if _margin_cache and now - _margin_cache[1] < _MARGIN_TTL:
        return _margin_cache[0]

    try:
        import akshare as ak
        import pandas as pd

        with _AK_LOCK:
            df = ak.stock_margin_account_info()

        df = df.rename(columns={'日期': 'date', '融资余额': 'balance', '融资买入额': 'buy'})
        df['date'] = pd.to_datetime(df['date'])
        df['balance'] = pd.to_numeric(df['balance'], errors='coerce')
        df['buy'] = pd.to_numeric(df.get('buy', pd.Series()), errors='coerce')
        df = df.dropna(subset=['balance']).set_index('date').sort_index()

        current = float(df['balance'].iloc[-1])
        current_date = df.index[-1].strftime('%Y-%m-%d')

        def chg(n):
            if len(df) <= n:
                return None
            prev = float(df['balance'].iloc[-1 - n])
            return round(current - prev, 2)

        chg5 = chg(5)
        chg20 = chg(20)
        chg5_pct = round(chg5 / (current - chg5) * 100, 2) if chg5 is not None and (current - chg5) else None

        recent = df.tail(120)
        history = [
            {
                'date': ts.strftime('%Y-%m-%d'),
                'balance': round(float(row['balance']), 2),
                'buy': round(float(row['buy']), 2) if pd.notna(row.get('buy')) else None,
            }
            for ts, row in recent.iterrows()
        ]

        result = {
            'current':    round(current, 2),
            'date':       current_date,
            'chg_5d':     chg5,
            'chg_5d_pct': chg5_pct,
            'chg_20d':    chg20,
            'history':    history,
        }
        _margin_cache = (result, now)
        return result

    except Exception as e:
        return {'error': str(e)}
