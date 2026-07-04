"""SQLite 日快照 + 内存 TTL 缓存"""

import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable

import yaml

_cfg = yaml.safe_load(Path("config.yaml").read_text(encoding="utf-8"))
_DB_PATH = Path(_cfg["cache"]["db_path"])

_mem: dict[str, tuple[Any, float]] = {}
_key_locks: dict[str, threading.Lock] = {}
_key_locks_guard = threading.Lock()


def _lock_for(key: str) -> threading.Lock:
    with _key_locks_guard:
        lock = _key_locks.get(key)
        if lock is None:
            lock = threading.Lock()
            _key_locks[key] = lock
        return lock


def get_cached(key: str, ttl_seconds: int, fetch_fn: Callable) -> Any:
    now = time.time()
    if key in _mem and _mem[key][1] > now:
        return _mem[key][0]
    # single-flight：同一 key 并发首访时只有一个线程真正调用 fetch_fn，
    # 其余线程排队等待后直接复用结果，避免同时打 N 次上游
    with _lock_for(key):
        now = time.time()
        if key in _mem and _mem[key][1] > now:
            return _mem[key][0]
        data = fetch_fn()
        is_error = (isinstance(data, list) and data and "error" in data[0]) or (
            isinstance(data, dict) and "error" in data
        )
        if not is_error:
            _mem[key] = (data, now + ttl_seconds)
        return data


@contextmanager
def _conn():
    """连接用完即关；busy_timeout=10s 让并发写入排队重试而非立即报 database is locked。"""
    _DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(_DB_PATH, timeout=10)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with _conn() as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS board_snapshot (
                date TEXT NOT NULL,
                board_type TEXT NOT NULL,
                code TEXT NOT NULL,
                name TEXT NOT NULL,
                change_pct REAL,
                mkt_cap REAL,
                turnover_rate REAL,
                up_count INTEGER,
                down_count INTEGER,
                top_stock TEXT,
                top_stock_chg REAL,
                PRIMARY KEY (date, board_type, code)
            );
            CREATE INDEX IF NOT EXISTS idx_board_snapshot_type_date
                ON board_snapshot (board_type, date);
            CREATE TABLE IF NOT EXISTS index_snapshot (
                date TEXT NOT NULL,
                code TEXT NOT NULL,
                name TEXT NOT NULL,
                price REAL,
                change_pct REAL,
                PRIMARY KEY (date, code)
            );
            CREATE TABLE IF NOT EXISTS board_constituents (
                date TEXT NOT NULL,
                board_type TEXT NOT NULL,
                board_name TEXT NOT NULL,
                stock_code TEXT NOT NULL,
                stock_name TEXT,
                change_pct REAL,
                price REAL,
                volume REAL,
                PRIMARY KEY (date, board_type, board_name, stock_code)
            );
            CREATE TABLE IF NOT EXISTS market_breadth_history (
                date TEXT PRIMARY KEY,
                up INTEGER,
                down INTEGER,
                flat INTEGER,
                zt INTEGER,
                dt INTEGER,
                total INTEGER,
                activity REAL,
                amount REAL
            );
            CREATE TABLE IF NOT EXISTS zt_history (
                date TEXT NOT NULL,
                code TEXT NOT NULL,
                name TEXT,
                zt_days INTEGER,
                change_pct REAL,
                seal_amount REAL,
                industry TEXT,
                PRIMARY KEY (date, code)
            );
            CREATE TABLE IF NOT EXISTS lhb_history (
                date TEXT NOT NULL,
                code TEXT NOT NULL,
                name TEXT,
                price REAL,
                change_pct REAL,
                net_buy REAL,
                turnover REAL,
                free_mkt_cap REAL,
                reason TEXT,
                PRIMARY KEY (date, code)
            );
        """)
        # 迁移：为已有数据库补 amount 列
        try:
            c.execute("ALTER TABLE market_breadth_history ADD COLUMN amount REAL DEFAULT NULL")
        except sqlite3.OperationalError:
            pass  # 列已存在，忽略


def save_board_snapshot(date: str, board_type: str, rows: list[dict]) -> None:
    fields = ("code", "name", "change_pct", "mkt_cap", "turnover_rate",
              "up_count", "down_count", "top_stock", "top_stock_chg")
    normalized = []
    for r in rows:
        row = {f: r.get(f) for f in fields}
        row["code"] = row["code"] or row["name"]
        row["date"] = date
        row["board_type"] = board_type
        normalized.append(row)
    with _conn() as c:
        c.executemany(
            """INSERT OR REPLACE INTO board_snapshot
               (date, board_type, code, name, change_pct, mkt_cap, turnover_rate,
                up_count, down_count, top_stock, top_stock_chg)
               VALUES (:date, :board_type, :code, :name, :change_pct, :mkt_cap,
                       :turnover_rate, :up_count, :down_count, :top_stock, :top_stock_chg)""",
            normalized,
        )


def load_board_snapshot(date: str, board_type: str) -> list[dict]:
    with _conn() as c:
        c.row_factory = sqlite3.Row
        rows = c.execute(
            "SELECT * FROM board_snapshot WHERE date=? AND board_type=? ORDER BY change_pct DESC",
            (date, board_type),
        ).fetchall()
    return [dict(r) for r in rows]


def save_board_constituents(date: str, board_type: str, board_name: str, rows: list[dict]) -> None:
    with _conn() as c:
        c.executemany(
            """INSERT OR REPLACE INTO board_constituents
               (date, board_type, board_name, stock_code, stock_name, change_pct, price, volume)
               VALUES (:date, :board_type, :board_name, :stock_code, :stock_name, :change_pct, :price, :volume)""",
            [{**r, "date": date, "board_type": board_type, "board_name": board_name,
              "volume": r.get("volume")} for r in rows],
        )


def load_board_constituents(date: str, board_type: str, board_name: str) -> list[dict]:
    with _conn() as c:
        c.row_factory = sqlite3.Row
        rows = c.execute(
            """SELECT * FROM board_constituents
               WHERE date=? AND board_type=? AND board_name=?
               ORDER BY change_pct DESC""",
            (date, board_type, board_name),
        ).fetchall()
    return [dict(r) for r in rows]


# ── 市场情绪历史 ──────────────────────────────────────────────────

def save_breadth_history(date: str, data: dict) -> None:
    with _conn() as c:
        c.execute(
            """INSERT OR REPLACE INTO market_breadth_history
               (date, up, down, flat, zt, dt, total, activity, amount)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (date, data.get("up"), data.get("down"), data.get("flat"),
             data.get("zt"), data.get("dt"), data.get("total"), data.get("activity"),
             data.get("amount")),
        )


def load_breadth_history(days: int = 60) -> list[dict]:
    with _conn() as c:
        c.row_factory = sqlite3.Row
        rows = c.execute(
            "SELECT * FROM market_breadth_history ORDER BY date DESC LIMIT ?",
            (days,),
        ).fetchall()
    return [dict(r) for r in reversed(rows)]


# ── ZT 涨停板历史 ─────────────────────────────────────────────────

def save_zt_history(date: str, rows: list[dict]) -> None:
    with _conn() as c:
        c.executemany(
            """INSERT OR REPLACE INTO zt_history
               (date, code, name, zt_days, change_pct, seal_amount, industry)
               VALUES (:date, :code, :name, :zt_days, :change_pct, :seal_amount, :industry)""",
            [{**r, "date": date} for r in rows],
        )


def load_zt_history(date: str) -> list[dict]:
    with _conn() as c:
        c.row_factory = sqlite3.Row
        rows = c.execute(
            "SELECT * FROM zt_history WHERE date=? ORDER BY zt_days DESC",
            (date,),
        ).fetchall()
    return [dict(r) for r in rows]


def load_zt_dates(limit: int = 10) -> list[str]:
    """返回最近 N 个有记录的交易日（降序）"""
    with _conn() as c:
        rows = c.execute(
            "SELECT DISTINCT date FROM zt_history ORDER BY date DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [r[0] for r in rows]


# ── 龙虎榜历史 ───────────────────────────────────────────────────

def save_lhb_history(date: str, rows: list[dict]) -> None:
    with _conn() as c:
        c.executemany(
            """INSERT OR REPLACE INTO lhb_history
               (date, code, name, price, change_pct, net_buy, turnover, free_mkt_cap, reason)
               VALUES (:date, :code, :name, :price, :change_pct, :net_buy,
                       :turnover, :free_mkt_cap, :reason)""",
            [{**r, "date": date} for r in rows],
        )


def load_lhb_history(date: str) -> list[dict]:
    with _conn() as c:
        c.row_factory = sqlite3.Row
        rows = c.execute(
            "SELECT * FROM lhb_history WHERE date=? ORDER BY net_buy DESC",
            (date,),
        ).fetchall()
    return [dict(r) for r in rows]


def load_board_rotation(board_type: str = "industry") -> list[dict]:
    """从 board_snapshot 计算各板块多周期累计涨跌幅（5/20/60 日）。
    最长窗口是60个交易日，取近120个自然日兜底（覆盖春节等长假），
    避免快照累积后每次都全表扫描。
    """
    from datetime import datetime, timedelta
    cutoff = (datetime.now() - timedelta(days=120)).strftime("%Y-%m-%d")
    with _conn() as c:
        c.row_factory = sqlite3.Row
        rows = c.execute(
            "SELECT name, date, change_pct FROM board_snapshot WHERE board_type=? AND date>=? ORDER BY name, date ASC",
            (board_type, cutoff),
        ).fetchall()

    boards: dict[str, dict] = {}
    for row in rows:
        boards.setdefault(row["name"], {})[row["date"]] = row["change_pct"] or 0.0

    def compound(pcts: list[float]) -> float:
        r = 1.0
        for p in pcts:
            r *= 1 + p / 100
        return round((r - 1) * 100, 2)

    result = []
    for name, date_map in boards.items():
        dates = sorted(date_map)
        pcts = [date_map[d] for d in dates]
        n = len(pcts)
        result.append({
            "name": name,
            "d5":  compound(pcts[-5:])  if n >= 5  else None,
            "d20": compound(pcts[-20:]) if n >= 20 else None,
            "d60": compound(pcts[-60:]) if n >= 60 else None,
            "days": n,
        })
    return sorted(result, key=lambda x: (x["d20"] or 0), reverse=True)


def load_lhb_dates(limit: int = 10) -> list[str]:
    """返回最近 N 个有记录的交易日（降序）"""
    with _conn() as c:
        rows = c.execute(
            "SELECT DISTINCT date FROM lhb_history ORDER BY date DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [r[0] for r in rows]
