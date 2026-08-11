"""Settings and rules endpoints."""

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user_id
from app.services.defaults import RISK_PROFILE_DEFAULTS
from app.services.ai_service import ai_service
from app.services.broker_service import broker_service
from app.services.market_schedule import market_schedule_service

router = APIRouter()


@router.get("/risk-profile-defaults")
async def risk_profile_defaults(_: int = Depends(get_current_user_id)) -> dict:
    return RISK_PROFILE_DEFAULTS


@router.get("/system-status")
async def system_status(_: int = Depends(get_current_user_id)) -> dict:
    broker = broker_service.account_snapshot()
    return {
        "ai": ai_service.status(),
        "broker": {key: broker.get(key) for key in ("status", "connected", "mode", "buying_power", "cash", "portfolio_value", "failure_category") if key in broker},
        "market": {
            "status": "open" if market_schedule_service.is_market_open() else "closed",
            "timezone": "America/Chicago",
            "checked_at": market_schedule_service.now_ct().isoformat(),
        },
    }
