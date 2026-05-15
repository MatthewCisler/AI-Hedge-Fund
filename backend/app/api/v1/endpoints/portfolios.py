"""Portfolio endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id, get_db
from app.schemas.portfolio import (
    PortfolioCreate,
    PortfolioDetail,
    PortfolioRuleResponse,
    PortfolioRuleUpdate,
    PortfolioSummary,
)
from app.schemas.dashboard import BenchmarkSnapshotResponse
from app.services.benchmark_service import benchmark_service
from app.services.portfolio_service import portfolio_service

router = APIRouter()


@router.get("", response_model=list[PortfolioSummary])
def list_portfolios(
    db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)
) -> list[PortfolioSummary]:
    return portfolio_service.list_for_user(db, user_id)


@router.post("", response_model=PortfolioDetail, status_code=status.HTTP_201_CREATED)
def create_portfolio(
    payload: PortfolioCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> PortfolioDetail:
    return portfolio_service.create(db, user_id, payload)


@router.get("/{portfolio_id}", response_model=PortfolioDetail)
def get_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> PortfolioDetail:
    portfolio = portfolio_service.get_for_user(db, user_id, portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found.")
    return portfolio


@router.put("/{portfolio_id}/rules", response_model=PortfolioRuleResponse)
def update_rules(
    portfolio_id: int,
    payload: PortfolioRuleUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> PortfolioRuleResponse:
    try:
        return portfolio_service.update_rules(db, user_id, portfolio_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{portfolio_id}/benchmarks", response_model=list[BenchmarkSnapshotResponse])
def list_benchmarks(
    portfolio_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> list[BenchmarkSnapshotResponse]:
    portfolio = portfolio_service.get_for_user(db, user_id, portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found.")
    return benchmark_service.list_for_portfolio(db, portfolio_id)


@router.post("/{portfolio_id}/benchmarks/refresh", response_model=list[BenchmarkSnapshotResponse])
def refresh_benchmarks(
    portfolio_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> list[BenchmarkSnapshotResponse]:
    portfolio = portfolio_service.get_for_user(db, user_id, portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found.")
    return benchmark_service.refresh_for_portfolio(db, portfolio)
