"""AI decision endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id, get_db
from app.schemas.dashboard import AIDecisionResponse
from app.services.ai_decision_service import ai_decision_service
from app.services.portfolio_service import portfolio_service

router = APIRouter()


@router.get("/decisions", response_model=list[AIDecisionResponse])
def list_ai_decisions(
    db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)
) -> list[AIDecisionResponse]:
    return ai_decision_service.list_for_user(db, user_id)


@router.post("/analyze", response_model=list[AIDecisionResponse], status_code=status.HTTP_201_CREATED)
def run_ai_analysis(
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
