"""Portfolio endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id, get_db
from app.schemas.portfolio import (
    PortfolioActionResponse,
    PortfolioCreate,
    PortfolioDetail,
    PortfolioRuleResponse,
    PortfolioRuleUpdate,
    PortfolioSummary,
    PortfolioUpdate,
)
from app.schemas.dashboard import BenchmarkSnapshotResponse
from app.services.benchmark_service import benchmark_service
from app.services.ai_decision_service import ai_decision_service
from app.services.portfolio_service import portfolio_service
from app.services.report_service import report_service

router = APIRouter()


@router.get("", response_model=list[PortfolioSummary])
async def list_portfolios(
    db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)
) -> list[PortfolioSummary]:
    return portfolio_service.list_for_user(db, user_id)


@router.post("", response_model=PortfolioDetail, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    payload: PortfolioCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> PortfolioDetail:
    return portfolio_service.create(db, user_id, payload)


@router.get("/{portfolio_id}", response_model=PortfolioDetail)
async def get_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> PortfolioDetail:
    portfolio = portfolio_service.get_for_user(db, user_id, portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found.")
    return portfolio


@router.patch("/{portfolio_id}", response_model=PortfolioDetail)
async def update_portfolio(
    portfolio_id: int,
    payload: PortfolioUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> PortfolioDetail:
    try:
        return portfolio_service.update(db, user_id, portfolio_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{portfolio_id}/rules", response_model=PortfolioRuleResponse)
async def get_rules(
    portfolio_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> PortfolioRuleResponse:
    try:
        return portfolio_service.get_rules(db, user_id, portfolio_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/{portfolio_id}/rules", response_model=PortfolioRuleResponse)
async def patch_rules(
    portfolio_id: int,
    payload: PortfolioRuleUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> PortfolioRuleResponse:
    try:
        return portfolio_service.update_rules(db, user_id, portfolio_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("/{portfolio_id}/rules", response_model=PortfolioRuleResponse)
async def update_rules(
    portfolio_id: int,
    payload: PortfolioRuleUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> PortfolioRuleResponse:
    try:
        return portfolio_service.update_rules(db, user_id, portfolio_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{portfolio_id}/run-analysis", response_model=PortfolioActionResponse)
async def run_portfolio_analysis(
    portfolio_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> PortfolioActionResponse:
    portfolio = portfolio_service.get_for_user(db, user_id, portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found.")
    decisions = ai_decision_service.run_analysis(db, portfolio_id)
    used_fallback = bool(decisions and decisions[0].provider == "deterministic_fallback")
    return PortfolioActionResponse(
        status="fallback" if used_fallback else "ok",
        message=(
            "Ollama was unavailable; a non-actionable deterministic safety result was recorded."
            if used_fallback else "Ollama analysis completed."
        ),
        result=[{"ticker": item.ticker, "action": item.action_suggestion, "confidence": item.confidence_score} for item in decisions],
    )


@router.post("/{portfolio_id}/rebalance", response_model=PortfolioActionResponse)
async def rebalance_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> PortfolioActionResponse:
    try:
        trade = portfolio_service.queue_demo_rebalance(db, user_id, portfolio_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return PortfolioActionResponse(
        status="queued",
        message="Demo rebalance queued for next market open. No live trade was submitted.",
        result={"queued_trade_id": trade.id, "ticker": trade.ticker, "side": trade.side, "quantity": trade.quantity},
    )


@router.post("/{portfolio_id}/generate-report", response_model=PortfolioActionResponse)
async def generate_portfolio_report(
    portfolio_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> PortfolioActionResponse:
    portfolio = portfolio_service.get_for_user(db, user_id, portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found.")
    report = report_service.generate_daily_report(db, portfolio_id)
    return PortfolioActionResponse(
        status="ok",
        message="Daily report generated.",
        result={"report_id": report.id, "csv_path": report.csv_path},
    )


@router.post("/{portfolio_id}/pause", response_model=PortfolioActionResponse)
async def pause_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> PortfolioActionResponse:
    try:
        portfolio_service.set_active(db, user_id, portfolio_id, False)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return PortfolioActionResponse(status="ok", message="Portfolio paused.")


@router.post("/{portfolio_id}/resume", response_model=PortfolioActionResponse)
async def resume_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> PortfolioActionResponse:
    try:
        portfolio_service.set_active(db, user_id, portfolio_id, True)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return PortfolioActionResponse(status="ok", message="Portfolio resumed.")


@router.delete("/{portfolio_id}/queued-trades", response_model=PortfolioActionResponse)
async def clear_queued_trades(
    portfolio_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> PortfolioActionResponse:
    try:
        deleted = portfolio_service.clear_queued_trades(db, user_id, portfolio_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return PortfolioActionResponse(status="ok", message=f"Cleared {deleted} queued trade(s).", result={"deleted": deleted})


@router.get("/{portfolio_id}/benchmarks", response_model=list[BenchmarkSnapshotResponse])
async def list_benchmarks(
    portfolio_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> list[BenchmarkSnapshotResponse]:
    portfolio = portfolio_service.get_for_user(db, user_id, portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found.")
    return benchmark_service.list_for_portfolio(db, portfolio_id)


@router.post("/{portfolio_id}/benchmarks/refresh", response_model=list[BenchmarkSnapshotResponse])
async def refresh_benchmarks(
    portfolio_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> list[BenchmarkSnapshotResponse]:
    portfolio = portfolio_service.get_for_user(db, user_id, portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found.")
    return benchmark_service.refresh_for_portfolio(db, portfolio)
