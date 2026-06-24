"""个股基本面数据：EPS、BVPS、ROE、净利润增速（THS 财务摘要）"""

import akshare as ak
from data.fetchers import _AK_LOCK


def _parse_pct(s) -> float | None:
    """'8.89%' → 8.89，'False' / None → None"""
    if s is None or s is False or str(s) == 'False':
        return None
    try:
        return float(str(s).rstrip('%'))
    except Exception:
        return None


def _parse_num(s) -> float | None:
    """'21.76' → 21.76，'False' / None → None"""
    if s is None or s is False or str(s) == 'False':
        return None
    try:
        return float(s)
    except Exception:
        return None


def fetch_stock_fundamental(code: str) -> dict:
    """
    返回单只股票的基本面快照：
      eps    - 最近年报基本每股收益（用于前端计算静态 PE）
      bvps   - 最新季报每股净资产（用于前端计算 PB）
      roe    - 最新季报净资产收益率（%）
      profit_yoy - 最新季报净利润同比增速（%）
    前端用实时价格计算 PE = price / eps，PB = price / bvps。
    任一字段取不到时为 null，不影响其他字段返回。
    """
    try:
        with _AK_LOCK:
            df = ak.stock_financial_abstract_ths(symbol=code, indicator='按报告期')
        if df is None or df.empty:
            return {"error": "no data"}

        # 最近年报（报告期末尾为 12-31）
        annual_rows = df[df['报告期'].str.endswith('12-31')]
        eps = _parse_num(annual_rows.iloc[-1]['基本每股收益']) if len(annual_rows) > 0 else None

        # 最新季报
        latest = df.iloc[-1]
        bvps       = _parse_num(latest['每股净资产'])
        roe        = _parse_pct(latest['净资产收益率'])
        profit_yoy = _parse_pct(latest['净利润同比增长率'])

        return {"eps": eps, "bvps": bvps, "roe": roe, "profit_yoy": profit_yoy}
    except Exception as e:
        return {"error": str(e)}


def fetch_fundamentals_batch(codes: list[str]) -> dict[str, dict]:
    """批量拉取，返回 {code: fundamental_dict}"""
    result = {}
    for code in codes:
        result[code] = fetch_stock_fundamental(code)
    return result
