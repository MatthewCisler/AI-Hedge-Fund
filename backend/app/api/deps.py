"""Shared API dependencies."""

from collections.abc import AsyncGenerator

from fastapi import Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import SessionLocal


async def get_db() -> AsyncGenerator[Session, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user_id(
    x_user_id: str | None = Header(default=None),
    user_id: str | None = Query(default=None),
) -> int:
    """Stub auth dependency until JWT auth is wired in."""
    raw_user_id = x_user_id or user_id
    if not raw_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-User-Id header or user_id query parameter for demo authentication.",
        )
    try:
        return int(raw_user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-User-Id must be an integer.",
        ) from exc
