"""APScheduler bootstrap."""

import logging
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.jobs.tasks import (
    execute_queued_market_open_orders,
    publish_daily_reports,
    run_evening_scan,
    run_intraday_analysis,
)

logger = logging.getLogger(__name__)


class SchedulerService:
    def __init__(self) -> None:
        timezone = ZoneInfo(settings.market_timezone)
        self.scheduler = BackgroundScheduler(timezone=timezone)
        self._configured = False

    def configure(self) -> None:
        if self._configured:
            return
        self.scheduler.add_job(
            run_intraday_analysis,
            CronTrigger(day_of_week="mon-fri", hour="8-14", minute="*/15"),
            id="intraday_analysis",
            replace_existing=True,
        )
        self.scheduler.add_job(
            run_evening_scan,
            CronTrigger(day_of_week="mon-fri", hour="16,18,20", minute="0"),
            id="evening_scan",
            replace_existing=True,
        )
        self.scheduler.add_job(
            execute_queued_market_open_orders,
            CronTrigger(day_of_week="mon-fri", hour=settings.market_open_hour_ct, minute=settings.market_open_minute_ct),
            id="market_open_queue",
            replace_existing=True,
        )
        self.scheduler.add_job(
            publish_daily_reports,
            CronTrigger(day_of_week="mon-fri", hour=settings.daily_report_hour_ct, minute=settings.daily_report_minute_ct),
            id="daily_reports",
            replace_existing=True,
        )
        self._configured = True

    def start(self) -> None:
        self.configure()
        if not self.scheduler.running:
            logger.info("Starting APScheduler background jobs.")
            self.scheduler.start()

    def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)


scheduler_service = SchedulerService()
