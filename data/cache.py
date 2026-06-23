"""SQLite 日快照 + 内存 TTL 缓存"""

import sqlite3
import time
from pathlib import Path
from typing import Any, Callable

import yaml

_cfg = yaml.safe_load(Path("config.yaml").read_text(encoding="utf-8"))
_DB_PATH = Path(_cfg["cache"]["db_path"])

_mem: dict[str, tuple[Any, float]] = {}


def get_cached(key: str, ttl_seconds: int, fetch_fn: Callable) -> Any:
    now = time.time()
    if key in _mem and _mem[key][1] > now:
        return _mem[key][0]
    data = fetch_fn()
    _mem[key] = (data, now + ttl_seconds)
    return data


def _conn() -> sqlite3.Connection:
    _DB_PATH.parent.mkdir(exist_ok=True)
    return sqlite3.connect(_DB_PATH)


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
        """)


def save_board_snapshot(date: str, board_type: str, rows: list[dict]) -> None:
    with _conn() as c:
        c.executemany(
            """INSERT OR REPLACE INTO board_snapshot
               (date, board_type, code, name, change_pct, mkt_cap, turnover_rate,
                up_count, down_count, top_stock, top_stock_chg)
               VALUES (:date, :board_type, :code, :name, :change_pct, :mkt_cap,
                       :turnover_rate, :up_count, :down_count, :top_stock, :top_stock_chg)""",
            [{**r, "date": date, "board_type": board_type} for r in rows],
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
            [{**r, "date": date, "board_type": board_type, "board_name": board_name} for r in rows],
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
