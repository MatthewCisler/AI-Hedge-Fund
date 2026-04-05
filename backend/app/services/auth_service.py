"""Authentication service."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import TokenResponse, UserLogin, UserRegister


class AuthService:
    def register(self, db: Session, payload: UserRegister) -> TokenResponse:
        existing = db.scalar(select(User).where(User.email == payload.email))
        if existing:
            raise ValueError("Email already registered.")

        user = User(
            email=payload.email,
            password_hash=hash_password(payload.password),
            full_name=payload.full_name,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return TokenResponse(access_token=create_access_token(str(user.id)), user_id=user.id)

    def login(self, db: Session, payload: UserLogin) -> TokenResponse:
        user = db.scalar(select(User).where(User.email == payload.email))
        if not user or not verify_password(payload.password, user.password_hash):
            raise ValueError("Invalid credentials.")
        return TokenResponse(access_token=create_access_token(str(user.id)), user_id=user.id)


auth_service = AuthService()
