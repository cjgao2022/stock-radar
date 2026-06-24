"""APScheduler 盘后任务：16:35 刷新板块日快照"""

from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from pathlib import Path
import yaml

_cfg = yaml.safe_load(Path("config.yaml").read_text(encoding="utf-8"))
_BEIJING = timezone(timedelta(hours=8))


def _today() -> str:
    return datetime.now(_BEIJING).strftime("%Y-%m-%d")


def refresh_board_snapshots() -> None:
    from data.fetchers.boards import fetch_board_list
    from data.cache import save_board_snapshot

    date = _today()
    for btype in ("concept", "industry"):
        rows = fetch_board_list(btype)
        if rows and "error" not in rows[0]:
            save_board_snapshot(date, btype, rows)
            print(f"[scheduler] {date} {btype} 板块快照已刷新，共 {len(rows)} 条")
        else:
            print(f"[scheduler] {date} {btype} 板块快照刷新失败: {rows}")


def save_breadth_snapshot() -> None:
    from data.fetchers.market import fetch_market_breadth
    from data.cache import save_breadth_history

    date = _today()
    data = fetch_market_breadth()
    if "error" not in data:
        save_breadth_history(date, data)
        print(f"[scheduler] {date} 市场情绪快照已保存 up={data.get('up')} down={data.get('down')}")
    else:
        print(f"[scheduler] {date} 市场情绪快照失败: {data}")


def save_zt_snapshot() -> None:
    from data.fetchers.flow import fetch_zt_pool
    from data.cache import save_zt_history

    date = _today()
    date_compact = date.replace("-", "")
    rows = fetch_zt_pool(date_compact)
    if rows and "error" not in rows[0]:
        normalized = [
            {
                "code": r.get("code", ""),
                "name": r.get("name", ""),
                "zt_days": r.get("zt_days"),
                "change_pct": r.get("change_pct"),
                "seal_amount": r.get("seal_amount"),
                "industry": r.get("industry", ""),
            }
            for r in rows
        ]
        save_zt_history(date, normalized)
        print(f"[scheduler] {date} 涨停板快照已保存，共 {len(normalized)} 条")
    else:
        print(f"[scheduler] {date} 涨停板快照失败: {rows[:1] if rows else 'empty'}")


def save_lhb_snapshot() -> None:
    from data.fetchers.market import fetch_lhb_today
    from data.cache import save_lhb_history

    date = _today()
    rows = fetch_lhb_today()
    if rows and "error" not in rows[0]:
        normalized = [
            {
                "code": r.get("code", ""),
                "name": r.get("name", ""),
                "price": r.get("price"),
                "change_pct": r.get("change_pct"),
                "net_buy": r.get("net_buy"),
                "turnover": r.get("turnover"),
                "free_mkt_cap": r.get("free_mkt_cap"),
                "reason": r.get("reason", ""),
            }
            for r in rows
        ]
        save_lhb_history(date, normalized)
        print(f"[scheduler] {date} 龙虎榜快照已保存，共 {len(normalized)} 条")
    else:
        print(f"[scheduler] {date} 龙虎榜快照失败: {rows[:1] if rows else 'empty'}")


def bootstrap_breadth_history(days: int = 60) -> dict:
    """一次性补齐近 N 个交易日的 ZT/DT 计数和 LHB 历史快照。
    up/down 家数无历史接口，breadth_history 仅补 zt/dt，up=down=0 作为占位。
    已有数据的日期自动跳过。
    """
    import akshare as ak
    from data.fetchers.flow import fetch_zt_pool
    from data.fetchers.market import fetch_lhb_today
    from data.cache import (
        save_breadth_history, load_breadth_history,
        save_zt_history, load_zt_dates,
        save_lhb_history, load_lhb_dates,
    )

    today_str = datetime.now(_BEIJING).strftime("%Y-%m-%d")

    df_cal = ak.tool_trade_date_hist_sina()
    trading_dates = (
        df_cal[df_cal["trade_date"].astype(str) <= today_str]["trade_date"]
        .astype(str)
        .tail(days + 5)
        .tolist()
    )[-days:]

    existing_breadth = {r["date"] for r in load_breadth_history(days + 10)}
    existing_zt = set(load_zt_dates(days + 10))
    existing_lhb = set(load_lhb_dates(days + 10))

    stats = {"zt_saved": 0, "lhb_saved": 0, "skipped": 0, "total": len(trading_dates)}

    for date_str in trading_dates:
        date_key = date_str.replace("-", "")
        need_zt = date_str not in existing_zt or date_str not in existing_breadth
        need_lhb = date_str not in existing_lhb

        if not need_zt and not need_lhb:
            stats["skipped"] += 1
            continue

        if need_zt:
            try:
                import akshare as ak
                from data.fetchers import _AK_LOCK
                zt_rows = fetch_zt_pool(date_key)
                zt_count = len(zt_rows) if (zt_rows and "error" not in zt_rows[0]) else 0

                # DT 接口仅支持最近30个交易日，超出范围单独容错
                dt_count = 0
                try:
                    with _AK_LOCK:
                        dt_df = ak.stock_zt_pool_dtgc_em(date=date_key)
                    dt_count = len(dt_df) if dt_df is not None and not dt_df.empty else 0
                except Exception:
                    pass  # 超出范围或无数据，dt_count 保持 0

                if date_str not in existing_breadth and zt_count > 0:
                    save_breadth_history(date_str, {
                        "up": 0, "down": 0, "flat": 0,
                        "zt": zt_count, "dt": dt_count,
                        "total": 0, "activity": 0.0,
                    })
                if date_str not in existing_zt and zt_rows and "error" not in zt_rows[0]:
                    normalized = [
                        {
                            "code": r.get("code", ""),
                            "name": r.get("name", ""),
                            "zt_days": r.get("zt_days"),
                            "change_pct": r.get("change_pct"),
                            "seal_amount": r.get("seal_amount"),
                            "industry": r.get("industry", ""),
                        }
                        for r in zt_rows
                    ]
                    save_zt_history(date_str, normalized)
                stats["zt_saved"] += 1
            except Exception as exc:
                print(f"[bootstrap] ZT {date_str} 失败: {exc}")

        if need_lhb:
            try:
                lhb_rows = fetch_lhb_today(date_key)
                if lhb_rows and "error" not in lhb_rows[0]:
                    normalized = [
                        {
                            "code": r.get("code", ""),
                            "name": r.get("name", ""),
                            "price": r.get("price"),
                            "change_pct": r.get("change_pct"),
                            "net_buy": r.get("net_buy"),
                            "turnover": r.get("turnover"),
                            "free_mkt_cap": r.get("free_mkt_cap"),
                            "reason": r.get("reason", ""),
                        }
                        for r in lhb_rows
                    ]
                    save_lhb_history(date_str, normalized)
                    stats["lhb_saved"] += 1
            except Exception as exc:
                print(f"[bootstrap] LHB {date_str} 失败: {exc}")

    print(f"[bootstrap] 完成: {stats}")
    return stats


def start_scheduler() -> None:
    refresh_time = _cfg["cache"].get("snapshot_refresh_time", "16:35")
    hour, minute = map(int, refresh_time.split(":"))

    def _offset(base_h, base_m, delta):
        total = base_h * 60 + base_m + delta
        return divmod(total, 60)

    h2, m2 = _offset(hour, minute, 2)
    h3, m3 = _offset(hour, minute, 3)
    h4, m4 = _offset(hour, minute, 4)

    scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
    scheduler.add_job(refresh_board_snapshots, "cron",
                      day_of_week="mon-fri", hour=hour, minute=minute,
                      id="board_snapshot")
    scheduler.add_job(save_breadth_snapshot, "cron",
                      day_of_week="mon-fri", hour=h2, minute=m2,
                      id="breadth_snapshot")
    scheduler.add_job(save_zt_snapshot, "cron",
                      day_of_week="mon-fri", hour=h3, minute=m3,
                      id="zt_snapshot")
    scheduler.add_job(save_lhb_snapshot, "cron",
                      day_of_week="mon-fri", hour=h4, minute=m4,
                      id="lhb_snapshot")
    scheduler.start()
    print(f"[scheduler] 已启动，盘后快照将在工作日 {refresh_time}（北京时间）自动刷新")
