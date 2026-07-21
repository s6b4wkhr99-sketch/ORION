"""Volume 14 Section 13 — User administration with audit trail."""

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.user import User
from app.security.audit import record_audit
from app.security.password import PasswordPolicyError, hash_password, validate_password_policy
from app.security.roles import ALL_ROLES

MAX_FAILED_LOGINS = 5


def list_users(db: Session) -> list[dict]:
    return [
        {
            "email": u.email,
            "name": u.name,
            "role": u.role,
            "isActive": u.is_active,
            "isLocked": u.locked_at is not None,
            "failedLoginAttempts": u.failed_login_attempts,
            "createdAt": u.created_at.isoformat() if u.created_at else None,
        }
        for u in db.query(User).order_by(User.created_at.desc()).all()
    ]


def create_user(
    db: Session,
    *,
    email: str,
    password: str,
    name: str,
    role: str,
    actor: dict,
) -> dict:
    if role not in ALL_ROLES:
        raise ValueError(f"Invalid role: {role}")
    if db.query(User).filter(User.email == email).first():
        raise ValueError("User already exists")
    try:
        password_hash = hash_password(password)
    except PasswordPolicyError as exc:
        raise ValueError(str(exc)) from exc
    user = User(
        email=email.lower().strip(),
        password_hash=password_hash,
        name=name,
        role=role,
        is_active=True,
        created_at=datetime.utcnow(),
    )
    db.add(user)
    db.commit()
    record_audit(
        db,
        action="user_create",
        user_id=actor.get("email"),
        role=actor.get("role"),
        entity_type="user",
        entity_id=email,
        after_value={"email": email, "role": role, "name": name},
        ip_address=actor.get("ip_address"),
        browser=actor.get("browser"),
    )
    return {"email": user.email, "name": user.name, "role": user.role, "isActive": user.is_active}


def assign_role(db: Session, email: str, role: str, actor: dict) -> dict:
    if role not in ALL_ROLES:
        raise ValueError(f"Invalid role: {role}")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise ValueError("User not found")
    before = user.role
    user.role = role
    db.commit()
    record_audit(
        db,
        action="user_assign_role",
        user_id=actor.get("email"),
        role=actor.get("role"),
        entity_type="user",
        entity_id=email,
        before_value={"role": before},
        after_value={"role": role},
        ip_address=actor.get("ip_address"),
        browser=actor.get("browser"),
    )
    return {"email": user.email, "role": user.role}


def reset_password(db: Session, email: str, password: str, actor: dict) -> dict:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise ValueError("User not found")
    try:
        user.password_hash = hash_password(password)
    except PasswordPolicyError as exc:
        raise ValueError(str(exc)) from exc
    user.failed_login_attempts = 0
    user.locked_at = None
    db.commit()
    record_audit(
        db,
        action="user_reset_password",
        user_id=actor.get("email"),
        role=actor.get("role"),
        entity_type="user",
        entity_id=email,
        ip_address=actor.get("ip_address"),
        browser=actor.get("browser"),
    )
    return {"email": user.email, "reset": True}


def set_user_active(db: Session, email: str, active: bool, actor: dict) -> dict:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise ValueError("User not found")
    before = user.is_active
    user.is_active = active
    if active:
        user.failed_login_attempts = 0
        user.locked_at = None
    db.commit()
    record_audit(
        db,
        action="user_activate" if active else "user_deactivate",
        user_id=actor.get("email"),
        role=actor.get("role"),
        entity_type="user",
        entity_id=email,
        before_value={"isActive": before},
        after_value={"isActive": active},
        ip_address=actor.get("ip_address"),
        browser=actor.get("browser"),
    )
    return {"email": user.email, "isActive": user.is_active}


def unlock_user(db: Session, email: str, actor: dict) -> dict:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise ValueError("User not found")
    user.failed_login_attempts = 0
    user.locked_at = None
    db.commit()
    record_audit(
        db,
        action="user_unlock",
        user_id=actor.get("email"),
        role=actor.get("role"),
        entity_type="user",
        entity_id=email,
        ip_address=actor.get("ip_address"),
        browser=actor.get("browser"),
    )
    return {"email": user.email, "isLocked": False}


def record_failed_login(db: Session, email: str) -> None:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return
    user.failed_login_attempts += 1
    if user.failed_login_attempts >= MAX_FAILED_LOGINS:
        user.locked_at = datetime.utcnow()
    db.commit()


def is_user_locked(user: User) -> bool:
    return user.locked_at is not None
