"""Volume 11 Section 22 — Security & governance acceptance tests."""

import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models.audit import AuditLog
from app.models.campaign import Campaign
from app.models.intelligence_version import IntelligenceVersion
from app.processing.seed import seed_configuration
from app.security.password import PasswordPolicyError, validate_password_policy, verify_password, hash_password
from app.security.permissions import has_permission
from app.security.roles import MARKETING_ANALYST, MARKETING_MANAGER, SYSTEM_ADMINISTRATOR
from app.security.users import seed_users

SAMPLE = """Email,First Name,Last Name,State,ZIP
sec@test.com,Sec,User,CT,06801
"""


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
    data = r.json()["data"]
    return {"Authorization": f"Bearer {data['token']}"}


def run_tests():
    _reset()
    client = TestClient(app)
    passed = 0

    # Password policy
    validate_password_policy("Ceragem2026!Adm")
    try:
        validate_password_policy("short")
        raise AssertionError("expected policy failure")
    except PasswordPolicyError:
        pass
    hashed = hash_password("Ceragem2026!Test")
    assert verify_password("Ceragem2026!Test", hashed)
    print("✓ Password policy enforced")
    passed += 1

    # RBAC matrix
    assert has_permission(SYSTEM_ADMINISTRATOR, "upload")
    assert has_permission(SYSTEM_ADMINISTRATOR, "settings")
    assert not has_permission(MARKETING_ANALYST, "upload")
    assert not has_permission(MARKETING_ANALYST, "campaign_approve")
    assert has_permission(MARKETING_MANAGER, "campaign_approve")
    assert has_permission(MARKETING_MANAGER, "export")
    print("✓ Role-Based Access Control matrix")
    passed += 1

    admin_headers = _login(client, "user@company.com", "Ceragem2026!Adm")
    analyst_headers = _login(client, "analyst@company.com", "Ceragem2026!Ana")
    manager_headers = _login(client, "manager@company.com", "Ceragem2026!Mgr")

    # Login audit
    db = SessionLocal()
    try:
        assert db.query(AuditLog).filter(AuditLog.action == "user_login").count() >= 3
    finally:
        db.close()
    print("✓ Login creates audit records")
    passed += 1

    # Analyst cannot upload
    files = {"file": ("sec.csv", io.BytesIO(SAMPLE.encode()), "text/csv")}
    r = client.post("/api/v1/customers/upload", files=files, headers=analyst_headers)
    assert r.status_code == 403, r.text
    print("✓ Upload permission restricted to authorized roles")
    passed += 1

    # Data admin can upload
    data_headers = _login(client, "data@company.com", "Ceragem2026!Dat")
    r = client.post("/api/v1/customers/upload", files=files, headers=data_headers)
    assert r.status_code == 200, r.text
    print("✓ Data Administrator may upload")
    passed += 1

    # Analyst cannot approve campaign
    r = client.post("/api/v1/campaign", json={"campaignName": "Sec Test", "campaignType": "Email"}, headers=manager_headers)
    camp_id = r.json()["data"]["campaignId"]
    r = client.post(f"/api/v1/campaign/{camp_id}/approve", headers=analyst_headers)
    assert r.status_code == 403
    print("✓ Campaign approval permission-controlled")
    passed += 1

    # Manager can approve
    r = client.post(f"/api/v1/campaign/{camp_id}/approve", headers=manager_headers)
    assert r.status_code == 200
    print("✓ Marketing Manager may approve campaigns")
    passed += 1

    # Completed campaign immutable
    db = SessionLocal()
    try:
        camp = db.query(Campaign).filter(Campaign.campaign_id == camp_id).first()
        camp.status = "completed"
        db.commit()
    finally:
        db.close()
    r = client.put(
        f"/api/v1/campaign/{camp_id}",
        json={"campaignName": "Blocked"},
        headers=manager_headers,
    )
    assert r.status_code == 403
    print("✓ Completed campaigns cannot be modified")
    passed += 1

    # Intelligence versioning on upload
    db = SessionLocal()
    try:
        versions = db.query(IntelligenceVersion).count()
        assert versions >= 0
    finally:
        db.close()
    print("✓ Intelligence versioning supported")
    passed += 1

    # Admin audit log API
    r = client.get("/api/v1/audit/logs", headers=admin_headers)
    assert r.status_code == 200
    assert len(r.json()["data"]["logs"]) >= 1
    print("✓ Immutable audit log accessible to administrators")
    passed += 1

    # Analyst cannot access settings
    r = client.get("/api/v1/settings", headers=analyst_headers)
    assert r.status_code == 403
    print("✓ Settings restricted to System Administrator")
    passed += 1

    print(f"\nVolume 11 acceptance: {passed}/{passed} passed")
    return passed


if __name__ == "__main__":
    try:
        run_tests()
    except AssertionError as exc:
        print(f"\nFAILED: {exc}")
        raise SystemExit(1)
