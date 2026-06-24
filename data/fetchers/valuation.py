"""行业估值数据：巨潮资讯证监会行业分类市盈率"""

import math
from datetime import date
import akshare as ak
from data.fetchers import _AK_LOCK


def fetch_industry_pe_cninfo() -> list[dict]:
    """
    返回证监会行业分类（层级 1+2）的 PE 数据，来源：巨潮资讯。
    失败时返回 [{"error": "..."}]，不抛异常。
    """
    try:
        today = date.today().strftime('%Y%m%d')
        with _AK_LOCK:
            df = ak.stock_industry_pe_ratio_cninfo(symbol='证监会行业分类', date=today)

        df = df[df['行业层级'].isin([1.0, 2.0])].copy()

        def safe_float(v):
            try:
                f = float(v)
                return None if math.isnan(f) or math.isinf(f) else round(f, 2)
            except Exception:
                return None

        def safe_int(v):
            try:
                return int(float(v)) if not math.isnan(float(v)) else 0
            except Exception:
                return 0

        result = []
        for _, row in df.iterrows():
            result.append({
                "name":       str(row['行业名称']),
                "level":      int(row['行业层级']),
                "code":       str(row['行业编码']),
                "pe_weighted": safe_float(row.get('静态市盈率-加权平均')),
                "pe_median":   safe_float(row.get('静态市盈率-中位数')),
                "company_count": safe_int(row.get('纳入计算公司数量')),
                "mkt_cap":    safe_float(row.get('总市值-静态')),
            })
        return result
    except Exception as e:
        return [{"error": str(e)}]
