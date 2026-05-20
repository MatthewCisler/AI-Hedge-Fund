"""Settings and rules endpoints."""

from fastapi import APIRouter

from app.services.defaults import RISK_PROFILE_DEFAULTS

router = APIRouter()


@router.get("/risk-profile-defaults")
async def risk_profile_defaults() -> dict:
    return RISK_PROFILE_DEFAULTS
