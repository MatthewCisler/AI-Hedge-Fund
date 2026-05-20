"""Manual local job triggers for development and smoke testing."""

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user_id
from app.jobs.tasks import (
    execute_queued_market_open_orders,
    publish_daily_reports,
    run_evening_scan,
    run_intraday_analysis,
)

router = APIRouter()


@router.post("/intraday-analysis")
async def trigger_intraday_analysis(
    force: bool = Query(default=True),
    _: int = Depends(get_current_user_id),
) -> dict:
    return run_intraday_analysis(force=force)


@router.post("/evening-scan")
async def trigger_evening_scan(_: int = Depends(get_current_user_id)) -> dict:
    return run_evening_scan()


@router.post("/queued-orders")
async def trigger_queued_orders(
    force: bool = Query(default=True),
    _: int = Depends(get_current_user_id),
) -> dict:
    return execute_queued_market_open_orders(force=force)


@router.post("/daily-reports")
async def trigger_daily_reports(
    force: bool = Query(default=True),
    _: int = Depends(get_current_user_id),
) -> dict:
    return publish_daily_reports(force=force)
