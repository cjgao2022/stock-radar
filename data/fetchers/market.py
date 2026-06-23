"""市场情绪数据：涨跌家数、龙虎榜"""

from datetime import datetime, timezone, timedelta

import akshare as ak
from data.fetchers import _AK_LOCK

_CST = timezone(timedelta(hours=8))


def fetch_market_breadth() -> dict:
    """全市场涨跌家数统计（AKShare 新浪全量行情）

    按板块使用正确涨跌停阈值：科创/创业板 ±20%，北交所 ±30%，ST ±5%，主板 ±10%。
    过滤停牌股（成交量=0），避免把停牌误计为平盘。
    耗时约 20 秒，调用方需配置 5 分钟以上缓存 TTL。
    """
    try:
        with _AK_LOCK:
            df = ak.stock_zh_a_spot()

        if '成交量' in df.columns:
            df = df[df['成交量'] > 0].copy()

        pct   = df['涨跌幅']
        codes = df['代码'].astype(str) if '代码' in df.columns else df.iloc[:, 0].astype(str)
        names = df['名称'].astype(str) if '名称' in df.columns else ''

        up   = int((pct > 0).sum())
        down = int((pct < 0).sum())
        flat = int((pct == 0).sum())

        is_kc  = codes.str.startswith('688')
        is_cyb = codes.str.startswith('300') | codes.str.startswith('301')
        is_bj  = codes.str.startswith('83') | codes.str.startswith('87') | codes.str.startswith('43')
        is_hi  = is_kc | is_cyb
        is_st  = names.str.contains('ST', na=False) if isinstance(names, type(pct)) else False
        is_main_nst = ~is_hi & ~is_bj & ~is_st

        zt = int((
            ((pct >= 19.9) & is_hi) |
            ((pct >= 29.9) & is_bj) |
            ((pct >=  4.9) & is_st & ~is_hi & ~is_bj) |
            ((pct >=  9.9) & is_main_nst)
        ).sum())
        dt = int((
            ((pct <= -19.9) & is_hi) |
            ((pct <= -29.9) & is_bj) |
            ((pct <=  -4.9) & is_st & ~is_hi & ~is_bj) |
            ((pct <=  -9.9) & is_main_nst)
        ).sum())

        total = len(df)
        activity = round((up + down) / total * 100, 1) if total else 0
        return {
            'up': up, 'down': down, 'flat': flat,
            'zt': zt, 'dt': dt,
            'total': total,
            'activity': activity,
            'ts': datetime.now(_CST).strftime('%H:%M'),
        }
    except Exception as e:
        return {'error': str(e)}


def fetch_lhb_today() -> list[dict]:
    """今日龙虎榜（上榜原因 + 净买额）"""
    try:
        today = datetime.now(_CST).strftime('%Y%m%d')
        with _AK_LOCK:
            df = ak.stock_lhb_detail_em(start_date=today, end_date=today)
        today_str = datetime.now(_CST).strftime('%Y-%m-%d')
        df = df[df['上榜日'].astype(str).str[:10] == today_str]
        # 同一只股票可能有多行（多个上榜原因），先聚合原因再去重
        reason_map = (
            df.groupby('代码')['上榜原因']
            .apply(lambda x: ' / '.join(x.dropna().unique()))
            .to_dict()
        )
        df = df.drop_duplicates(subset=['代码'])
        df['上榜原因'] = df['代码'].map(reason_map)
        rename = {
            '代码': 'code', '名称': 'name', '收盘价': 'price',
            '涨跌幅': 'change_pct', '龙虎榜净买额': 'net_buy',
            '换手率': 'turnover', '流通市值': 'free_mkt_cap',
        }
        df = df.rename(columns=rename)
        keep = [c for c in ['code', 'name', 'price', 'change_pct', 'net_buy', 'turnover', 'free_mkt_cap'] if c in df.columns]
        df = df[keep].sort_values('net_buy', ascending=False)
        return df.head(20).to_dict(orient='records')
    except Exception as e:
        return [{'error': str(e)}]
