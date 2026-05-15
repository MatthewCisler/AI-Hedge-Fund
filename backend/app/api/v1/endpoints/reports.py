"""Daily report endpoints."""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id, get_db
from app.schemas.report import DailyReportResponse
from app.services.portfolio_service import portfolio_service
from app.services.report_service import report_service

router = APIRouter()


@router.get("", response_model=list[DailyReportResponse])
def list_reports(
    db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)
) -> list[DailyReportResponse]:
    return report_service.list_reports(db, user_id)


@router.get("/{report_id}", response_model=DailyReportResponse)
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> DailyReportResponse:
    report = report_service.get_report(db, user_id, report_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")
    return report


@router.get("/{report_id}/csv")
def download_report_csv(
    report_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> FileResponse:
    report = report_service.get_report(db, user_id, report_id)
    if not report or not report.csv_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report CSV not found.")
    path = Path(report.csv_path)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report CSV file missing.")
    return FileResponse(path, media_type="text/csv", filename=path.name)


@router.post("/generate", response_model=DailyReportResponse, status_code=status.HTTP_201_CREATED)
def generate_report(
    portfolio_id: int = Query(...),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> DailyReportResponse:
    portfolio = portfolio_service.get_for_user(db, user_id, portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found.")
    try:
        return report_service.generate_daily_report(db, portfolio_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
