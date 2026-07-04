from datetime import datetime, timezone, timedelta
from pathlib import Path

import yaml

_BEIJING = timezone(timedelta(hours=8))

# 各路由文件此前各自重复 yaml.safe_load(config.yaml)，收拢到这里加载一次
config = yaml.safe_load(Path("config.yaml").read_text(encoding="utf-8"))


def today_cst() -> str:
    return datetime.now(_BEIJING).strftime("%Y-%m-%d")
