from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


def is_postgres_url(url: str | None = None) -> bool:
    target = (url or settings.database_url).lower()
    return target.startswith("postgresql") or target.startswith("postgres+")


def is_sqlite_url(url: str | None = None) -> bool:
    return (url or settings.database_url).startswith("sqlite")


connect_args = {"check_same_thread": False} if is_sqlite_url() else {}
engine_kwargs: dict = {"pool_pre_ping": True, "connect_args": connect_args}
if is_postgres_url():
    engine_kwargs["pool_size"] = settings.database_pool_size
    engine_kwargs["max_overflow"] = settings.database_max_overflow

engine = create_engine(settings.database_url, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
