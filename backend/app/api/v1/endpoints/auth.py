"""Auth endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api.deps import get_current_user_id, get_db
from app.core.config import settings
from app.models.user import User
from app.schemas.auth import TokenResponse, UserLogin, UserRegister, UserSession
from app.services.auth_service import auth_service

router = APIRouter()


@router.post("/register", response_model=TokenResponse)
async def register(payload: UserRegister, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        return auth_service.register(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin, db: Session = Depends(get_db)) -> TokenResponse:
    try:
        return auth_service.login(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.get("/me", response_model=UserSession)
async def current_session(
    db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)
) -> UserSession:
    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")
    configured = settings.alpaca_api_key != "paper-key" and settings.alpaca_api_secret != "paper-secret"
    return UserSession(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        broker_mode="alpaca-paper" if configured else "demo-simulation",
    )
