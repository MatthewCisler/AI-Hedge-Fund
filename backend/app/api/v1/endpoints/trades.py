"""Trade and order endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id, get_db
from app.schemas.trade import OrderCreate, OrderResponse, QueuedTradeResponse, TradeResponse
from app.services.trade_service import trade_service

router = APIRouter()


@router.get("/orders", response_model=list[OrderResponse])
async def list_orders(
    db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)
) -> list[OrderResponse]:
    return trade_service.list_orders(db, user_id)


@router.get("/queued", response_model=list[QueuedTradeResponse])
async def list_queued(
    db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)
) -> list[QueuedTradeResponse]:
    return trade_service.list_queued(db, user_id)


@router.get("", response_model=list[TradeResponse])
async def list_trades(
    db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)
) -> list[TradeResponse]:
    return trade_service.list_trades(db, user_id)


@router.post("/orders", response_model=OrderResponse | QueuedTradeResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> OrderResponse | QueuedTradeResponse:
    try:
        return trade_service.create_order(db, user_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
