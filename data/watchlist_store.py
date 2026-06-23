"""自选股/ETF 持仓动态存储（JSON 文件）

首次调用自动从 config.yaml 迁移初始数据，后续增删只操作此文件。
"""

import json
import threading
from datetime import datetime, timezone, timedelta
from pathlib import Path
import yaml

_CST = timezone(timedelta(hours=8))

def _now_cst() -> str:
    return datetime.now(_CST).strftime("%Y-%m-%d %H:%M")

_PATH = Path("data/watchlist.json")
_LOCK = threading.Lock()


def _load() -> dict:
    if _PATH.exists():
        try:
            return json.loads(_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    # 首次：从 config.yaml 迁移
    cfg = yaml.safe_load(Path("config.yaml").read_text(encoding="utf-8"))
    data = {
        "stocks": [
            {"code": item["code"], "name": item.get("name", "")}
            for item in cfg.get("watchlist", [])
        ],
        "etfs": [
            {"code": item["code"], "name": item.get("name", ""), "etf_type": item.get("type", "")}
            for item in cfg.get("etf_watchlist", [])
        ],
    }
    _save(data)
    return data


def _save(data: dict):
    _PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ── 个股 ──────────────────────────────────────────────────────────

def get_stocks() -> list[dict]:
    with _LOCK:
        return _load()["stocks"]


def add_stock(code: str, name: str) -> bool:
    with _LOCK:
        data = _load()
        if any(s["code"] == code for s in data["stocks"]):
            return False
        data["stocks"].append({"code": code, "name": name, "added_at": _now_cst()})
        _save(data)
        return True


def remove_stock(code: str) -> bool:
    with _LOCK:
        data = _load()
        before = len(data["stocks"])
        data["stocks"] = [s for s in data["stocks"] if s["code"] != code]
        if len(data["stocks"]) == before:
            return False
        _save(data)
        return True


# ── ETF ───────────────────────────────────────────────────────────

def get_etfs() -> list[dict]:
    with _LOCK:
        return _load()["etfs"]


def add_etf(code: str, name: str, etf_type: str = "") -> bool:
    with _LOCK:
        data = _load()
        if any(e["code"] == code for e in data["etfs"]):
            return False
        data["etfs"].append({"code": code, "name": name, "etf_type": etf_type, "added_at": _now_cst()})
        _save(data)
        return True


def remove_etf(code: str) -> bool:
    with _LOCK:
        data = _load()
        before = len(data["etfs"])
        data["etfs"] = [e for e in data["etfs"] if e["code"] != code]
        if len(data["etfs"]) == before:
            return False
        _save(data)
        return True
