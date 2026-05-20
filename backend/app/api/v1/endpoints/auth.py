"""Auth endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.auth import TokenResponse, UserLogin, UserRegister
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
