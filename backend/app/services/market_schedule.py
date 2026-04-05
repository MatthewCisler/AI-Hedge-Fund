"""Market-hours helpers using Central Time display rules."""

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.core.config import settings


class MarketScheduleService:
    def __init__(self) -> None:
        self.tz = ZoneInfo(settings.market_timezone)

    def now_ct(self) -> datetime:
        return datetime.now(self.tz)

    def is_trading_day(self, current: datetime | None = None) -> bool:
        current = current or self.now_ct()
        return current.weekday() < 5

    def is_market_open(self, current: datetime | None = None) -> bool:
        current = current or self.now_ct()
        if not self.is_trading_day(current):
            return False
        open_time = time(settings.market_open_hour_ct, settings.market_open_minute_ct)
        close_time = time(settings.market_close_hour_ct, settings.market_close_minute_ct)
        return open_time <= current.time() <= close_time

    def next_market_open(self, current: datetime | None = None) -> datetime:
        current = current or self.now_ct()
        candidate = current.replace(
            hour=settings.market_open_hour_ct,
            minute=settings.market_open_minute_ct,
            second=0,
            microsecond=0,
        )
        if current.time() < candidate.time() and self.is_trading_day(current):
            return candidate
        candidate = candidate + timedelta(days=1)
        while candidate.weekday() >= 5:
            candidate += timedelta(days=1)
        return candidate


market_schedule_service = MarketScheduleService()
