"""申万一级行业龙头：成分股 + 实时成交额排名"""

import time
import akshare as ak
from data.fetchers import _AK_LOCK

# 24小时模块级缓存：行业→成分股映射（变化极少）
_map_cache: tuple | None = None
_MAP_TTL = 86400  # 24h


def _build_industry_map() -> dict:
    """
    返回 {ind_code: {'name': str, 'stocks': [6位代码, ...]}}
    依次调用 sw_index_first_info + index_stock_cons × 31，约 30s。
    """
    with _AK_LOCK:
        info_df = ak.sw_index_first_info()

    result = {}
    for _, row in info_df.iterrows():
        raw_code = str(row['行业代码']).replace('.SI', '')
        name = str(row['行业名称'])
        try:
            with _AK_LOCK:
                cons_df = ak.index_stock_cons(symbol=raw_code)
            stocks = (
                cons_df['品种代码'].astype(str).str.zfill(6).tolist()
                if cons_df is not None and not cons_df.empty
                else []
            )
        except Exception:
            stocks = []
        result[raw_code] = {'name': name, 'stocks': stocks}
    return result


def _get_industry_map() -> dict:
    global _map_cache
    now = time.time()
    if _map_cache and now - _map_cache[1] < _MAP_TTL:
        return _map_cache[0]
    data = _build_industry_map()
    _map_cache = (data, now)
    return data


def fetch_leaders() -> list[dict]:
    """
    每个申万一级行业 TOP5 龙头（按今日成交额降序）。

    耗时说明：
      - 首次（当天第一次调用）：_build_industry_map 约 31s + stock_zh_a_spot 约 33s ≈ 64s
      - 之后：行业映射命中 24h 缓存，stock_zh_a_spot 约 33s
      - 路由层再缓存整体结果 30 分钟
    """
    industry_map = _get_industry_map()

    # 行业实时涨跌幅（指数级别）
    try:
        with _AK_LOCK:
            rt_df = ak.index_realtime_sw(symbol='一级行业')
        ind_rt: dict[str, dict] = {}
        for _, row in rt_df.iterrows():
            code = str(row['指数代码'])
            prev = float(row.get('昨收盘', 0) or 0)
            last = float(row.get('最新价', 0) or 0)
            chg = round((last - prev) / prev * 100, 2) if prev else 0.0
            ind_rt[code] = {'chg_pct': chg}
    except Exception:
        ind_rt = {}

    # 全量 A 股实时行情（新浪，约 33s）
    try:
        with _AK_LOCK:
            spot_df = ak.stock_zh_a_spot()
    except Exception as e:
        return [{'error': str(e)}]

    # code → {name, price, chg_pct, amount}
    quote_map: dict[str, dict] = {}
    for _, row in spot_df.iterrows():
        code_6 = str(row['代码'])[-6:]
        quote_map[code_6] = {
            'name':    str(row.get('名称', '')),
            'price':   float(row.get('最新价', 0) or 0),
            'chg_pct': float(row.get('涨跌幅', 0) or 0),
            'amount':  float(row.get('成交额', 0) or 0),
        }

    # 逐行业排名，取 TOP5
    result = []
    for ind_code, ind_info in industry_map.items():
        stocks: list[dict] = []
        for code in ind_info['stocks']:
            q = quote_map.get(code.zfill(6))
            if not q or q['amount'] <= 0:
                continue
            stocks.append({
                'code':      code,
                'name':      q['name'],
                'price':     q['price'],
                'chg_pct':   round(q['chg_pct'], 2),
                'amount_yi': round(q['amount'] / 1e8, 2),
            })
        stocks.sort(key=lambda x: x['amount_yi'], reverse=True)
        rt = ind_rt.get(ind_code, {})
        result.append({
            'industry_code': ind_code,
            'industry_name': ind_info['name'],
            'chg_pct':       rt.get('chg_pct', 0.0),
            'stocks':        stocks[:5],
        })

    result.sort(key=lambda x: x['chg_pct'], reverse=True)
    return result
