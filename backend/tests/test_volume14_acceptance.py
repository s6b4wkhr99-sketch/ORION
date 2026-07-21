"""Volume 14 Section 27 — System administration acceptance tests."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models.audit import AuditLog
from app.models.user import User
from app.processing.seed import seed_configuration
from app.security.users import seed_users

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _reset():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_configuration(db)
    seed_users(db)
    db.close()


def _login(client, email: str, password: str) -> dict:
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['data']['token']}"}


def run_tests():
    _reset()
    client = TestClient(app)
    admin = _login(client, "user@company.com", "Ceragem2026!Adm")
    analyst = _login(client, "analyst@company.com", "Ceragem2026!Ana")
    passed = 0

    # Section 3 — Administrator dashboard
    r = client.get("/api/v1/admin/dashboard", headers=admin)
    assert r.status_code == 200, r.text
    dash = r.json()["data"]
    for key in (
        "systemStatus",
        "cpuUsagePercent",
        "memoryUsagePercent",
        "databaseStatus",
        "storageUsage",
        "apiHealth",
        "runningCampaigns",
        "uploadQueue",
        "scheduledJobs",
        "notificationCenter",
        "operationalMetrics",
    ):
        assert key in dash, key
    print("✓ Section 3 Administrator dashboard API")
    passed += 1

    # Section 4 & 26 — Checklists
    r = client.get("/api/v1/admin/checklists/daily", headers=admin)
    daily = r.json()["data"]
    assert daily["checklist"] == "daily"
    assert len(daily["items"]) == 8
    r = client.get("/api/v1/admin/checklists/end-of-day", headers=admin)
    eod = r.json()["data"]
    assert eod["checklist"] == "end_of_day"
    assert len(eod["items"]) == 8
    print("✓ Sections 4 & 26 Daily and end-of-day checklists")
    passed += 1

    # Section 13 — User administration
    r = client.post(
        "/api/v1/admin/users",
        headers=admin,
        json={
            "email": "ops@company.com",
            "password": "Ceragem2026!Ops",
            "name": "Ops User",
            "role": "Marketing Analyst",
        },
    )
    assert r.status_code == 200, r.text
    r = client.put(
        "/api/v1/admin/users/ops@company.com/role",
        headers=admin,
        json={"role": "Data Administrator"},
    )
    assert r.json()["data"]["role"] == "Data Administrator"
    r = client.post(
        "/api/v1/admin/users/ops@company.com/reset-password",
        headers=admin,
        json={"password": "Ceragem2026!New"},
    )
    assert r.json()["data"]["reset"] is True
    r = client.post("/api/v1/admin/users/ops@company.com/disable", headers=admin)
    assert r.json()["data"]["isActive"] is False
    r = client.post("/api/v1/admin/users/ops@company.com/activate", headers=admin)
    assert r.json()["data"]["isActive"] is True
    db = SessionLocal()
    audit_actions = [a.action for a in db.query(AuditLog).filter(AuditLog.entity_id == "ops@company.com").all()]
    db.close()
    assert "user_create" in audit_actions
    assert "user_assign_role" in audit_actions
    print("✓ Section 13 User administration with audit trail")
    passed += 1

    # Section 14 — RBAC on admin routes
    r = client.get("/api/v1/admin/dashboard", headers=analyst)
    assert r.status_code == 403
    print("✓ Section 14 Role administration — admin routes restricted")
    passed += 1

    # Section 15 & 16 — Rules read-only, providers
    r = client.get("/api/v1/admin/providers", headers=admin)
    providers = r.json()["data"]["providers"]
    assert any(p["providerName"] == "Klaviyo" for p in providers)
    assert r.json()["data"]["readOnlyRules"] is True
    print("✓ Sections 15 & 16 Rule and provider administration")
    passed += 1

    # Section 25 — Operational KPIs
    r = client.get("/api/v1/admin/metrics", headers=admin)
    metrics = r.json()["data"]
    assert metrics["targets"]["dashboardResponseMs"] == 2000
    assert metrics["targets"]["uploadProcessingMs"] == 15000
    print("✓ Section 25 Operational KPI targets")
    passed += 1

    # Documentation
    doc = os.path.join(ROOT, "docs", "14_System_Administration_Operations_Manual.md")
    assert os.path.isfile(doc)
    print("✓ Section 27 Operations manual documented")
    passed += 1

    # Account lock / unlock
    db = SessionLocal()
    user = db.query(User).filter(User.email == "ops@company.com").first()
    user.failed_login_attempts = 5
    from datetime import datetime

    user.locked_at = datetime.utcnow()
    db.commit()
    db.close()
    r = client.post("/api/v1/auth/login", json={"email": "ops@company.com", "password": "Ceragem2026!New"})
    assert r.status_code == 401
    r = client.post("/api/v1/admin/users/ops@company.com/unlock", headers=admin)
    assert r.json()["data"]["isLocked"] is False
    r = client.post("/api/v1/auth/login", json={"email": "ops@company.com", "password": "Ceragem2026!New"})
    assert r.status_code == 200
    print("✓ Section 13 Unlock account")
    passed += 1

    print(f"\nVolume 14 Operations: {passed}/{passed} acceptance checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_tests())
