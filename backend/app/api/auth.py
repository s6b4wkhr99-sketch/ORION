"""Volume 07 / 11 / 14 — JWT authentication with RBAC and account lockout."""

from datetime import datetime, timedelta, timezone

import jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User
from app.operations.user_admin import is_user_locked, record_failed_login
from app.schemas.auth import LoginRequest
from app.security.audit import record_audit
from app.security.password import verify_password

ALGORITHM = "HS256"

__all__ = ["LoginRequest", "TokenResponse", "login", "refresh", "authenticate_user", "decode_token"]


class TokenResponse(BaseModel):
    token: str
    expires: str
    role: str | None = None


def _fallback_user(email: str, password: str) -> dict | None:
    if email == settings.auth_user_email and password == settings.auth_user_password:
        from app.security.roles import SYSTEM_ADMINISTRATOR

        return {
            "email": email,
            "password_hash": "",
            "role": SYSTEM_ADMINISTRATOR,
            "name": "CIOS Admin",
        }
    return None


def authenticate_user(db: Session, email: str, password: str) -> dict | None:
    user = db.query(User).filter(User.email == email).first()
    if user:
        if not user.is_active:
            return None
        if is_user_locked(user):
            return None
        if verify_password(password, user.password_hash):
            user.failed_login_attempts = 0
            user.locked_at = None
            db.commit()
            return {"email": user.email, "role": user.role, "name": user.name}
        record_failed_login(db, email)
        record_audit(db, action="login_failed", user_id=email, status="failure")
        return None
    legacy = _fallback_user(email, password)
    if legacy:
        return legacy
    record_audit(db, action="login_failed", user_id=email, status="failure")
    return None


def create_access_token(subject: str, role: str, expires_minutes: int | None = None) -> tuple[str, datetime]:
    expire_minutes = expires_minutes or settings.jwt_expire_minutes
    expires = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    payload = {
        "sub": subject,
        "role": role,
        "exp": expires,
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)
    return token, expires


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])


def login(db: Session, email: str, password: str) -> TokenResponse | None:
    user = authenticate_user(db, email, password)
    if not user:
        return None
    token, expires = create_access_token(user["email"], user["role"])
    return TokenResponse(
        token=token,
        expires=expires.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        role=user["role"],
    )


def refresh(token: str) -> TokenResponse | None:
    try:
        payload = decode_token(token)
        subject = payload.get("sub")
        role = payload.get("role", "Read Only")
        if not subject:
            return None
        new_token, expires = create_access_token(subject, role)
        return TokenResponse(
            token=new_token,
            expires=expires.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            role=role,
        )
    except jwt.PyJWTError:
        return None
