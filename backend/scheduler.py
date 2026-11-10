from __future__ import annotations

import datetime as dt
import logging
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from .batch import run_batch
from .db import connect, init_db

LOGGER = logging.getLogger(__name__)
SEOUL = ZoneInfo("Asia/Seoul")


def _last_success_date() -> dt.date | None:
    with connect() as db:
        row = db.execute(
            "SELECT finished_at FROM batch_runs WHERE status='success' ORDER BY id DESC LIMIT 1"
        ).fetchone()
    if not row:
        return None
    return dt.datetime.fromisoformat(row["finished_at"]).astimezone(SEOUL).date()


def start_scheduler(run_now: bool = True) -> BackgroundScheduler:
    init_db()
    now = dt.datetime.now(SEOUL)
    missed = _last_success_date() != now.date()
    if run_now and missed:
        try:
            run_batch()
        except Exception:
            LOGGER.exception("시작/catch-up 배치 실패: 기존 스냅샷을 유지합니다.")
    scheduler = BackgroundScheduler(timezone=SEOUL)
    scheduler.add_job(
        run_batch,
        CronTrigger(hour=15, minute=0, timezone=SEOUL),
        id="daily-batch",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )
    scheduler.start()
    return scheduler
