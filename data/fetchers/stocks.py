"""个股实时行情 —— 新浪 hq.sinajs.cn batch（100 个/次）"""

import re
import requests
from pathlib import Path
import yaml

_cfg = yaml.safe_load(Path("config.yaml").read_text(encoding="utf-8"))
_HEADERS = {"Referer": "https://finance.sina.com.cn"}


def _sina_prefix(code: str) -> str:
    # 上交所：股票6/9开头，ETF 5开头；深交所：其余
    return "sh" if code.startswith(("6", "9", "5")) else "sz"


def fetch_quotes(codes: list[str]) -> list[dict]:
    """批量拉取个股实时行情，codes 为纯数字代码列表（如 ['600519', '000001']）"""
    if not codes:
        return []

    result = []
    for i in range(0, len(codes), 100):
        chunk = codes[i:i + 100]
        sina_codes = [f"{_sina_prefix(c)}{c}" for c in chunk]
        url = "https://hq.sinajs.cn/list=" + ",".join(sina_codes)
        try:
            r = requests.get(url, timeout=10, headers=_HEADERS)
            r.encoding = "gbk"
        except Exception:
            continue

        for line in r.text.strip().split("\n"):
            if "=" not in line or '""' in line:
                continue
            raw_code = line.split("=")[0].split("_")[-1]
            code = raw_code[2:]
            val = line.split('"')[1]
            fields = val.split(",")
            if len(fields) < 10:
                continue
            try:
                prev = float(fields[2]) if fields[2] else 0
                price = float(fields[3]) if fields[3] else 0
                high = float(fields[4]) if fields[4] else 0
                low = float(fields[5]) if fields[5] else 0
                volume = float(fields[8]) if fields[8] else 0
                amount = float(fields[9]) if fields[9] else 0
                change_pct = round((price - prev) / prev * 100, 2) if prev else 0
                result.append({
                    "code": code,
                    "name": fields[0],
                    "price": price,
                    "change_pct": change_pct,
                    "high": high,
                    "low": low,
                    "prev_close": prev,
                    "volume": volume,
                    "amount": amount,
                })
            except (ValueError, IndexError):
                continue

    return result


def fetch_watchlist() -> list[dict]:
    """拉取持仓个股行情（数据源：data/watchlist.json）"""
    from data.watchlist_store import get_stocks
    items = get_stocks()
    codes = [item["code"] for item in items]
    name_map = {item["code"]: item["name"] for item in items}
    quotes = fetch_quotes(codes)
    for q in quotes:
        item = {i["code"]: i for i in items}.get(q["code"], {})
        if item.get("name"):
            q["name"] = item["name"]
        q["added_at"] = item.get("added_at", "")
    return quotes


def fetch_etf_watchlist() -> list[dict]:
    """拉取持仓 ETF 行情（数据源：data/watchlist.json）"""
    from data.watchlist_store import get_etfs
    items = get_etfs()
    codes = [item["code"] for item in items]
    meta = {item["code"]: item for item in items}
    quotes = fetch_quotes(codes)
    for q in quotes:
        m = meta.get(q["code"], {})
        if m.get("name"):
            q["name"] = m["name"]
        q["etf_type"] = m.get("etf_type", "")
        q["added_at"] = m.get("added_at", "")
    return quotes


def _is_etf_code(code: str) -> bool:
    """ETF 代码识别：上交所 ETF 以 5 开头；深交所 ETF 为 159xxx。"""
    return code[0] == "5" or code.startswith("159")


_SINA_CODE_RE = re.compile(r"^(sh|sz|of)\d+$")


def _suggest_pairs(query: str, suggest_type: str = "11") -> list[tuple[str, str]]:
    """新浪 suggest 接口 → [(code, full_name), ...]。type=11 股票，type=22 ETF

    含中文的查询要求完整 query 作为连续子串出现在候选名称中，防止 suggest 拆字模糊匹配。
    按代码搜索时 parts[0] 是内部格式（sh600519），优先取 parts[4] 作为显示名。
    """
    url = f"https://suggest3.sinajs.cn/suggest/type={suggest_type}&key={query}&token="
    has_chinese = any("一" <= c <= "鿿" for c in query)
    try:
        r = requests.get(url, timeout=8, headers=_HEADERS)
        r.encoding = "gbk"
        m = re.search(r'"(.+?)"', r.text)
        if not m or not m.group(1):
            return []
        pairs = []
        for entry in m.group(1).split(";"):
            parts = entry.split(",")
            if len(parts) < 3 or not re.match(r"^\d{6}$", parts[2]):
                continue
            name = parts[0]
            # 代码直查时 parts[0] 是 Sina 内部格式，改用 parts[4]（显示名）
            if _SINA_CODE_RE.match(name):
                name = parts[4] if len(parts) > 4 and parts[4] else ""
            if not name:
                continue
            if has_chinese and query not in name:
                continue
            pairs.append((parts[2], name))
        return pairs
    except Exception:
        return []


def _enrich_names(quotes: list[dict], suggest_type: str) -> list[dict]:
    """用 suggest 接口的完整名称覆盖 Sina hq 截断的名称。"""
    if not quotes:
        return quotes
    codes = [q["code"] for q in quotes]
    name_map: dict[str, str] = {}
    for code in codes:
        pairs = _suggest_pairs(code, suggest_type)
        for c, n in pairs:
            if c == code:
                name_map[c] = n
                break
    for q in quotes:
        if q["code"] in name_map:
            q["name"] = name_map[q["code"]]
    return quotes


def search_stock(query: str) -> list[dict]:
    """按代码或名称查询个股（不含 ETF）。6位代码直接查，名称走 suggest type=11。"""
    query = query.strip()
    if not query:
        return []
    if re.match(r"^\d{6}$", query):
        if _is_etf_code(query):
            return []
        return _enrich_names(fetch_quotes([query]), "11")
    pairs = _suggest_pairs(query, "11")
    pairs = [(c, n) for c, n in pairs if not _is_etf_code(c)]
    if not pairs:
        return []
    name_map = {code: name for code, name in pairs}
    quotes = fetch_quotes([code for code, _ in pairs])
    for q in quotes:
        if q["code"] in name_map:
            q["name"] = name_map[q["code"]]
    return quotes


def search_etf(query: str) -> list[dict]:
    """按代码或名称查询 ETF（不含个股）。6位代码直接查，名称走 suggest type=22。"""
    query = query.strip()
    if not query:
        return []
    if re.match(r"^\d{6}$", query):
        if not _is_etf_code(query):
            return []
        return _enrich_names(fetch_quotes([query]), "22")
    pairs = _suggest_pairs(query, "22")
    pairs = [(c, n) for c, n in pairs if _is_etf_code(c)]
    if not pairs:
        return []
    name_map = {code: name for code, name in pairs}
    quotes = fetch_quotes([code for code, _ in pairs])
    for q in quotes:
        if q["code"] in name_map:
            q["name"] = name_map[q["code"]]
    return quotes
