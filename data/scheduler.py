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


def start_scheduler() -> None:
    refresh_time = _cfg["cache"].get("snapshot_refresh_time", "16:35")
    hour, minute = map(int, refresh_time.split(":"))

    scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
    scheduler.add_job(refresh_board_snapshots, "cron",
                      day_of_week="mon-fri", hour=hour, minute=minute,
                      id="board_snapshot")
    scheduler.start()
    print(f"[scheduler] 已启动，板块快照将在工作日 {refresh_time}（北京时间）自动刷新")
