"""大盘指数实时行情 —— 新浪 hq.sinajs.cn（同 etf-radar sentiment.py 模式）"""

from pathlib import Path
import requests
import yaml

_cfg = yaml.safe_load(Path("config.yaml").read_text(encoding="utf-8"))
_INDEX_MAP = {item["code"]: item["name"] for item in _cfg["indices"]}


def fetch_indices() -> list[dict]:
    codes = ",".join(_INDEX_MAP.keys())
    url = f"https://hq.sinajs.cn/list={codes}"
    try:
        r = requests.get(url, timeout=10, headers={"Referer": "https://finance.sina.com.cn"})
        r.encoding = "gbk"
    except Exception as e:
        return [{"code": c, "name": n, "error": str(e)} for c, n in _INDEX_MAP.items()]

    result = []
    for line in r.text.strip().split("\n"):
        if "=" not in line or '""' in line:
            continue
        raw_code = line.split("=")[0].split("_")[-1]
        val = line.split('"')[1]
        fields = val.split(",")
        if len(fields) < 10:
            continue
        try:
            open_p = float(fields[1]) if fields[1] else 0
            prev = float(fields[2]) if fields[2] else 0
            price = float(fields[3]) if fields[3] else 0
            high = float(fields[4]) if fields[4] else 0
            low = float(fields[5]) if fields[5] else 0
            change_pct = round((price - prev) / prev * 100, 2) if prev else 0
            volume = float(fields[8]) if len(fields) > 8 and fields[8] else 0
            amount = float(fields[9]) if len(fields) > 9 and fields[9] else 0
            result.append({
                "code": raw_code,
                "name": _INDEX_MAP.get(raw_code, raw_code),
                "price": price,
                "change_pct": change_pct,
                "open": open_p,
                "high": high,
                "low": low,
                "prev_close": prev,
                "volume": volume,
                "amount": amount,
            })
        except (ValueError, IndexError):
            result.append({"code": raw_code, "name": _INDEX_MAP.get(raw_code, raw_code), "price": 0, "change_pct": 0})

    return result
