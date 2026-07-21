"""Volume 12 — Shared QA test utilities."""

import io
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, SessionLocal, engine
from app.processing.seed import seed_configuration
from app.security.users import seed_users

ADMIN_EMAIL = "user@company.com"
ADMIN_PASSWORD = "Ceragem2026!Adm"

CSV_HEADER = (
    "Email,First Name,Last Name,State,ZIP,Age Range,Generation,Gender,"
    "Estimated Income,Home Value,Household,Length of Residence,Net Worth,"
    "Online Access,Retail Card,Dwelling,Bank Card,Adults,Children,Persons"
)


def reset_db() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_configuration(db)
        seed_users(db)
    finally:
        db.close()


def login(client, email: str = ADMIN_EMAIL, password: str = ADMIN_PASSWORD) -> dict:
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    token = r.json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}


def assert_success(resp):
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body.get("success") is True, body
    return body["data"]


def make_csv_row(i: int, *, email: str | None = None, zip_code: str = "06801", income: str = "150000") -> str:
    em = email or f"customer{i}@qa.test"
    return (
        f"{em},First{i},Last{i},CT,{zip_code},45-54,Baby Boomer,M,"
        f"{income},500000,2,10,750000,Yes,Yes,Single Family,Yes,2,0,2"
    )


def make_csv_content(rows: int, **kwargs) -> str:
    lines = [CSV_HEADER] + [make_csv_row(i, **kwargs) for i in range(rows)]
    return "\n".join(lines) + "\n"


def make_xlsx_file(rows: int = 1) -> tuple[str, io.BytesIO]:
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    headers = CSV_HEADER.split(",")
    ws.append(headers)
    for i in range(rows):
        ws.append(make_csv_row(i).split(","))
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return "qa_upload.xlsx", buf


def timed(seconds_limit: float):
    """Context manager that asserts elapsed time is within limit."""

    class _Timer:
        def __enter__(self):
            self.start = time.perf_counter()
            return self

        def __exit__(self, *args):
            self.elapsed = time.perf_counter() - self.start
            assert self.elapsed <= seconds_limit, f"Exceeded {seconds_limit}s (took {self.elapsed:.2f}s)"

    return _Timer()
