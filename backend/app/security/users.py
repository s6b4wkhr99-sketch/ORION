"""Volume 11 — Seed user accounts (dev/MVP)."""

from datetime import datetime

from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User
from app.security.password import hash_password
from app.security.roles import (
    DATA_ADMINISTRATOR,
    EXECUTIVE_VIEWER,
    MARKETING_ANALYST,
    MARKETING_MANAGER,
    READ_ONLY,
    SYSTEM_ADMINISTRATOR,
)

# Dev seed passwords — meet Volume 11 Section 13 policy
SEED_USERS: list[tuple[str, str, str, str]] = [
    (settings.auth_user_email, settings.auth_user_password, SYSTEM_ADMINISTRATOR, "CIOS Admin"),
    ("manager@company.com", "Ceragem2026!Mgr", MARKETING_MANAGER, "Marketing Manager"),
    ("analyst@company.com", "Ceragem2026!Ana", MARKETING_ANALYST, "Marketing Analyst"),
    ("data@company.com", "Ceragem2026!Dat", DATA_ADMINISTRATOR, "Data Administrator"),
    ("exec@company.com", "Ceragem2026!Exe", EXECUTIVE_VIEWER, "Executive Viewer"),
    ("readonly@company.com", "Ceragem2026!Ro", READ_ONLY, "Read Only User"),
]


def seed_users(db: Session) -> None:
    if db.query(User).count() > 0:
        return
    now = datetime.utcnow()
    for email, password, role, name in SEED_USERS:
        db.add(User(
            email=email,
            password_hash=hash_password(password),
            role=role,
            name=name,
            is_active=True,
            created_at=now,
        ))
    db.commit()
