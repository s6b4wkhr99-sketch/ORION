"""Layer 02 — Duplicate detection — Rule-004."""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.customer import Customer


def normalize_email_key(email: str | None) -> str | None:
    if not email:
        return None
    return email.strip().lower()


def find_in_file_duplicates(emails: list[str | None]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for email in emails:
        key = normalize_email_key(email)
        if key:
            counts[key] = counts.get(key, 0) + 1
    return {k: v for k, v in counts.items() if v > 1}


_session_email_cache: set[str] | None = None


def load_existing_email_keys(db: Session) -> set[str]:
    """All normalized emails already stored — used to skip re-imports."""
    keys: set[str] = set()
    for (email,) in db.query(func.lower(Customer.email)).filter(Customer.email.isnot(None)).yield_per(5000):
        if email:
            keys.add(email)
    return keys


def batch_existing_email_keys(db: Session, keys: set[str], *, chunk_size: int = 5000) -> set[str]:
    """Return normalized emails from *keys* that already exist in customers (file-scoped, fast)."""
    found: set[str] = set()
    if not keys:
        return found
    key_list = sorted(keys)
    for offset in range(0, len(key_list), chunk_size):
        chunk = key_list[offset : offset + chunk_size]
        rows = (
            db.query(func.lower(Customer.email))
            .filter(Customer.email.isnot(None), func.lower(Customer.email).in_(chunk))
            .all()
        )
        for (email,) in rows:
            if email:
                found.add(email)
    return found


def batch_customers_by_email_keys(db: Session, keys: set[str], *, chunk_size: int = 2000) -> dict[str, Customer]:
    """Preload customers for a file's email keys — avoids per-row lookups on Datalogix refresh."""
    by_key: dict[str, Customer] = {}
    if not keys:
        return by_key
    key_list = sorted(keys)
    for offset in range(0, len(key_list), chunk_size):
        chunk = key_list[offset : offset + chunk_size]
        for customer in db.query(Customer).filter(func.lower(Customer.email).in_(chunk)).all():
            key = normalize_email_key(customer.email)
            if key:
                by_key[key] = customer
    return by_key


def get_existing_email_keys(db: Session, *, force_reload: bool = False) -> set[str]:
    """Worker-session cache — avoids reloading 1M+ emails at the start of every upload."""
    global _session_email_cache
    if _session_email_cache is None or force_reload:
        _session_email_cache = load_existing_email_keys(db)
    return _session_email_cache


def remember_email_key(email_key: str | None) -> None:
    global _session_email_cache
    if email_key and _session_email_cache is not None:
        _session_email_cache.add(email_key)


def clear_email_key_cache() -> None:
    global _session_email_cache
    _session_email_cache = None


def find_customer_by_email(db: Session, email: str | None) -> Customer | None:
    key = normalize_email_key(email)
    if not key:
        return None
    return db.query(Customer).filter(func.lower(Customer.email) == key).first()


def classify_duplicate_in_file(email: str | None, seen_in_file: set[str]) -> bool:
    """True when this email already appeared earlier in the same file (skip row)."""
    key = normalize_email_key(email)
    if not key:
        return False
    if key in seen_in_file:
        return True
    seen_in_file.add(key)
    return False
