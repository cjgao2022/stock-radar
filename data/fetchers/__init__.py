import threading

# py_mini_racer (V8 engine) is not thread-safe. Only AKShare functions that
# internally instantiate py_mini_racer.MiniRacer (THS 系列接口、同花顺资金流、
# 乐咕乐股 PE、巨潮行业PE、新浪全量行情 stock_zh_a_spot) need this lock —
# confirmed by grepping the installed akshare package source for MiniRacer usage.
# Non-JS AKShare calls (东方财富、百度股市通、宏观等) must NOT wrap this lock,
# otherwise all concurrent requests queue behind slow (20-100s) calls unnecessarily.
_AK_LOCK = threading.Lock()


def parse_sina_hq_line(line: str) -> tuple[str, list[str]] | None:
    """解析新浪 hq.sinajs.cn 单行响应 `var hq_str_xxx="f1,f2,...";`
    返回 (代码, 字段列表)；无效行/停牌空值/字段不足返回 None。
    indices.py 和 stocks.py 的行情解析都基于同一响应格式，仅字段取用和错误处理不同。
    """
    if "=" not in line or '""' in line:
        return None
    raw_code = line.split("=")[0].split("_")[-1]
    val = line.split('"')[1]
    fields = val.split(",")
    if len(fields) < 10:
        return None
    return raw_code, fields
