"""申万一级/二级行业龙头：成分股 + 实时成交额排名"""

import time
import akshare as ak
from data.fetchers import _AK_LOCK

# 24小时模块级缓存：行业→成分股映射（变化极少），按级别（l1/l2）分开存
_map_caches: dict[str, tuple | None] = {"l1": None, "l2": None}
_MAP_TTL = 86400  # 24h


def _build_industry_map(info_fn) -> dict:
    """
    返回 {ind_code: {'name': str, 'stocks': [6位代码, ...]}}
    依次调用 info_fn（一级约31个/二级约100个行业）+ index_stock_cons，一级约30s/二级约100s。
    """
    info_df = info_fn()

    result = {}
    for _, row in info_df.iterrows():
        raw_code = str(row['行业代码']).replace('.SI', '')
        name = str(row['行业名称'])
        try:
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


def _get_industry_map(level: str, info_fn) -> dict:
    now = time.time()
    cached = _map_caches.get(level)
    if cached and now - cached[1] < _MAP_TTL:
        return cached[0]
    data = _build_industry_map(info_fn)
    _map_caches[level] = (data, now)
    return data


def _fetch_leaders(level: str, info_fn, sw_symbol: str) -> list[dict]:
    """
    每个申万行业（一级/二级）TOP5 龙头（按今日成交额降序）。

    耗时说明：
      - 首次（当天第一次调用）：_build_industry_map（一级约31s/二级约100s） + stock_zh_a_spot 约 33s
      - 之后：行业映射命中 24h 缓存，stock_zh_a_spot 约 33s
      - 路由层再缓存整体结果 30 分钟
    """
    industry_map = _get_industry_map(level, info_fn)

    # 行业实时涨跌幅（指数级别）
    try:
        rt_df = ak.index_realtime_sw(symbol=sw_symbol)
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


def fetch_leaders() -> list[dict]:
    """申万一级行业 TOP5 龙头（按今日成交额降序）"""
    return _fetch_leaders('l1', ak.sw_index_first_info, '一级行业')


def fetch_leaders_second() -> list[dict]:
    """申万二级行业 TOP5 龙头（按今日成交额降序）"""
    return _fetch_leaders('l2', ak.sw_index_second_info, '二级行业')
