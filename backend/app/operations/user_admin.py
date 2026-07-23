"""Volume 14 Section 13 — User administration with audit trail."""

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.user import User
from app.security.audit import record_audit
from app.security.password import PasswordPolicyError, hash_password, validate_password_policy
from app.security.permissions import menu_modules_for_role, normalize_allowed_modules
from app.security.roles import ALL_ROLES, SYSTEM_ADMINISTRATOR

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
            "allowedModules": u.allowed_modules,
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
    allowed_modules: list[str] | None = None,
) -> dict:
    if role not in ALL_ROLES:
        raise ValueError(f"Invalid role: {role}")
    if db.query(User).filter(User.email == email).first():
        raise ValueError("User already exists")
    try:
        password_hash = hash_password(password)
    except PasswordPolicyError as exc:
        raise ValueError(str(exc)) from exc
    normalized_modules = normalize_allowed_modules(role, allowed_modules)
    user = User(
        email=email.lower().strip(),
        password_hash=password_hash,
        name=name,
        role=role,
        is_active=True,
        created_at=datetime.utcnow(),
        allowed_modules=normalized_modules,
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
        after_value={"email": email, "role": role, "name": name, "allowedModules": normalized_modules},
        ip_address=actor.get("ip_address"),
        browser=actor.get("browser"),
    )
    return {
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "isActive": user.is_active,
        "allowedModules": user.allowed_modules,
    }


def update_user(
    db: Session,
    email: str,
    *,
    new_email: str | None,
    name: str | None,
    role: str | None,
    allowed_modules: list[str] | None,
    menu_access_mode: str | None,
    actor: dict,
) -> dict:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise ValueError("User not found")

    target_email = (new_email or user.email).lower().strip()
    target_name = (name if name is not None else user.name).strip()
    target_role = role if role is not None else user.role
    if not target_name:
        raise ValueError("Name is required")
    if target_role not in ALL_ROLES:
        raise ValueError(f"Invalid role: {target_role}")

    target_allowed = user.allowed_modules
    if menu_access_mode == "role":
        target_allowed = None
    elif menu_access_mode == "custom":
        target_allowed = normalize_allowed_modules(target_role, allowed_modules or [])
    elif allowed_modules is not None:
        target_allowed = normalize_allowed_modules(target_role, allowed_modules)

    before = {
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "allowedModules": user.allowed_modules,
    }
    unchanged = (
        target_email == user.email
        and target_name == user.name
        and target_role == user.role
        and target_allowed == user.allowed_modules
    )
    if unchanged:
        return {
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "isActive": user.is_active,
            "allowedModules": user.allowed_modules,
        }

    if target_email != user.email and db.query(User).filter(User.email == target_email).first():
        raise ValueError("Email already in use")

    if target_email != user.email:
        replacement = User(
            email=target_email,
            password_hash=user.password_hash,
            role=target_role,
            name=target_name,
            is_active=user.is_active,
            failed_login_attempts=user.failed_login_attempts,
            locked_at=user.locked_at,
            created_at=user.created_at,
            allowed_modules=target_allowed,
        )
        db.delete(user)
        db.add(replacement)
        db.commit()
        user = replacement
    else:
        user.name = target_name
        user.role = target_role
        user.allowed_modules = target_allowed
        db.commit()

    record_audit(
        db,
        action="user_update",
        user_id=actor.get("email"),
        role=actor.get("role"),
        entity_type="user",
        entity_id=user.email,
        before_value=before,
        after_value={
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "allowedModules": user.allowed_modules,
        },
        ip_address=actor.get("ip_address"),
        browser=actor.get("browser"),
    )
    return {
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "isActive": user.is_active,
        "allowedModules": user.allowed_modules,
    }


def update_user_profile(
    db: Session,
    email: str,
    *,
    new_email: str | None,
    name: str | None,
    actor: dict,
) -> dict:
    return update_user(
        db,
        email,
        new_email=new_email,
        name=name,
        role=None,
        allowed_modules=None,
        menu_access_mode=None,
        actor=actor,
    )


def assign_role(db: Session, email: str, role: str, actor: dict) -> dict:
    if role not in ALL_ROLES:
        raise ValueError(f"Invalid role: {role}")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise ValueError("User not found")
    before = user.role
    user.role = role
    if user.allowed_modules is not None:
        user.allowed_modules = normalize_allowed_modules(role, user.allowed_modules)
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


def delete_user(db: Session, email: str, actor: dict) -> dict:
    actor_email = (actor.get("email") or "").lower().strip()
    target_email = email.lower().strip()
    if actor_email == target_email:
        raise ValueError("You cannot delete your own account")

    user = db.query(User).filter(User.email == target_email).first()
    if not user:
        raise ValueError("User not found")

    if user.role == SYSTEM_ADMINISTRATOR:
        admin_count = db.query(User).filter(User.role == SYSTEM_ADMINISTRATOR).count()
        if admin_count <= 1:
            raise ValueError("Cannot delete the last System Administrator")

    before = {
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "isActive": user.is_active,
        "allowedModules": user.allowed_modules,
    }
    db.delete(user)
    db.commit()
    record_audit(
        db,
        action="user_delete",
        user_id=actor.get("email"),
        role=actor.get("role"),
        entity_type="user",
        entity_id=target_email,
        before_value=before,
        ip_address=actor.get("ip_address"),
        browser=actor.get("browser"),
    )
    return {"email": target_email, "deleted": True}


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
