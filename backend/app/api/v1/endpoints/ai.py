"""AI decision endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id, get_db
from app.schemas.dashboard import AIDecisionResponse
from app.services.ai_service import ai_service
from app.services.ai_decision_service import ai_decision_service
from app.services.portfolio_service import portfolio_service

router = APIRouter()


@router.get("/status")
async def ai_status(_: int = Depends(get_current_user_id)) -> dict:
    """Return a safe operational status without running analysis."""
    return ai_service.status()


@router.get("/decisions", response_model=list[AIDecisionResponse])
async def list_ai_decisions(
    db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)
) -> list[AIDecisionResponse]:
    return ai_decision_service.list_for_user(db, user_id)


@router.post("/analyze", response_model=list[AIDecisionResponse], status_code=status.HTTP_201_CREATED)
async def run_ai_analysis(
    portfolio_id: int = Query(...),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> list[AIDecisionResponse]:
    portfolio = portfolio_service.get_for_user(db, user_id, portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found.")
    try:
        return ai_decision_service.run_analysis(db, portfolio_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/debug-sample")
async def debug_sample_analysis(_: int = Depends(get_current_user_id)) -> dict:
    """Exercise the local AI adapter with deterministic sample context."""
    result = ai_service.analyze(
        portfolio_state={
            "name": "Demo Paper Portfolio",
            "risk_profile": "balanced",
            "cash_balance": 86500,
            "current_value": 100800,
            "holdings": [{"ticker": "SPY", "quantity": 10, "market_value": 4550}],
        },
        candidate_universe=["SPY", "QQQ", "MSFT", "AAPL"],
        recent_news=[
            {
                "headline": "Broad market ETFs edge higher as technology shares stabilize",
                "url": "local-demo://market-etfs",
                "tickers": ["SPY", "QQQ", "MSFT"],
            }
        ],
        price_context={"source": "debug-sample"},
    )
    return {
        "provider": result.provider,
        "analysis_status": result.analysis_status,
        "failure_category": result.failure_category,
        "model_name": result.model_name,
        "operational_message": result.operational_message,
        "suggestions": [suggestion.__dict__ for suggestion in result.suggestions],
    }
