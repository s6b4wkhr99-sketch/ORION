"""Fast smoke tests — isolated SQLite DB (safe alongside local PostgreSQL)."""

import os
import sys

# Must set before app imports
os.environ.setdefault("DATABASE_URL", "sqlite:///./.test_smoke.db")
os.environ.setdefault("AUTH_REQUIRED", "true")
os.environ.setdefault("SKIP_PHYSICAL_SCHEMA", "true")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.main import app
from app.processing.seed import seed_configuration
from app.security.users import seed_users

ADMIN = ("user@company.com", "Ceragem2026!Adm")
READONLY = ("readonly@company.com", "Ceragem2026!Ro")


def _reset_db() -> None:
    if os.path.exists(".test_smoke.db"):
        os.remove(".test_smoke.db")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_configuration(db)
    seed_users(db)
    db.close()


def _login(client: TestClient, email: str, password: str) -> dict:
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    token = r.json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}


def run_tests() -> None:
    _reset_db()
    client = TestClient(app)

    admin_headers = _login(client, *ADMIN)
    readonly_headers = _login(client, *READONLY)

    r = client.get("/api/v1/auth/me", headers=admin_headers)
    assert r.status_code == 200, r.text
    me = r.json()["data"]
    assert me["role"] == "System Administrator"
    assert "user_administration" in me.get("modules", [])

    r = client.get("/api/v1/auth/me", headers=readonly_headers)
    assert r.status_code == 200, r.text
    ro = r.json()["data"]
    assert ro["role"] == "Read Only"
    assert "upload" not in ro.get("modules", [])

    r = client.get("/api/v1/admin/users", headers=admin_headers)
    assert r.status_code == 200, r.text
    assert any(u["email"] == READONLY[0] for u in r.json()["data"]["users"])

    r = client.get("/api/v1/uploads?dataset_type=prospect", headers=readonly_headers)
    assert r.status_code == 403, r.text

    create = client.post(
        "/api/v1/admin/users",
        headers=admin_headers,
        json={
            "email": "smoke-delete@company.com",
            "password": "Ceragem2026!Del",
            "name": "Smoke Delete",
            "role": "Read Only",
        },
    )
    assert create.status_code == 200, create.text

    delete = client.delete("/api/v1/admin/users/smoke-delete@company.com", headers=admin_headers)
    assert delete.status_code == 200, delete.text
    assert delete.json()["data"]["deleted"] is True

    r = client.get("/openapi.json")
    assert r.status_code == 200
    paths = r.json().get("paths", {})
    assert "delete" in paths.get("/api/v1/admin/users/{email}", {})

    print("✓ CIOS smoke tests passed (auth, RBAC, user admin, delete route)")


if __name__ == "__main__":
    run_tests()
