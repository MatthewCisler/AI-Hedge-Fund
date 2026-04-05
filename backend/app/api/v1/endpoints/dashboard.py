"""Dashboard endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id, get_db
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import dashboard_service

router = APIRouter()


@router.get("", response_model=DashboardResponse)
def get_dashboard(
    db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)
) -> DashboardResponse:
    return dashboard_service.build(db, user_id)
