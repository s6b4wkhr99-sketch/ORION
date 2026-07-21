"""Phase 2 — Async upload job acceptance tests."""

import io
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app.acquisition.upload_queue import run_worker_cycle
from app.database import Base, SessionLocal, engine
from app.main import app
from app.models import *  # noqa: F401, F403
from app.models.raw import RawUpload
from app.processing.seed import seed_configuration
from app.schema.apply import apply_physical_schema
from app.schema.seed_v16 import seed_v16_reference_schema
from app.security.users import seed_users
from tests.qa_helpers import ADMIN_EMAIL, ADMIN_PASSWORD


def _reset():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    apply_physical_schema(engine)
    db = SessionLocal()
    seed_configuration(db)
    seed_users(db)
    seed_v16_reference_schema(db)
    db.close()


def run_tests() -> int:
    os.environ["UPLOAD_ASYNC"] = "true"
    from app.config import settings

    settings.upload_async = True

    _reset()
    client = TestClient(app)
    login_resp = client.post("/api/v1/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    headers = {"Authorization": f"Bearer {login_resp.json()['data']['token']}"}
    passed = 0

    csv = "Email,State,ZIP Code\nasync1@test.com,NJ,07650\nasync2@test.com,NJ,07651\n"
    upload_resp = client.post(
        "/api/v1/customers/upload",
        files={"file": ("async.csv", io.BytesIO(csv.encode()), "text/csv")},
        headers=headers,
    )
    assert upload_resp.status_code == 200, upload_resp.text
    enqueue = upload_resp.json()["data"]
    assert enqueue["status"] == "pending"
    assert enqueue.get("async") is True
    upload_id = enqueue["uploadId"]
    print("✓ Upload enqueue returns pending immediately")
    passed += 1

    status_resp = client.get(f"/api/v1/upload/{upload_id}", headers=headers)
    assert status_resp.status_code == 200
    assert status_resp.json()["data"]["status"] == "pending"
    print("✓ Upload status endpoint available while pending")
    passed += 1

    db = SessionLocal()
    try:
        assert run_worker_cycle(db) is True
        upload = db.query(RawUpload).filter(RawUpload.upload_id == uuid.UUID(upload_id)).first()
        assert upload is not None
        assert upload.status == "completed"
    finally:
        db.close()

    done_resp = client.get(f"/api/v1/upload/{upload_id}", headers=headers)
    done = done_resp.json()["data"]
    assert done["status"] == "completed"
    assert done["customers"] >= 2
    assert done["progressPct"] == 100.0
    print("✓ Worker completes async upload job")
    passed += 1

    sync_resp = client.post(
        "/api/v1/customers/upload?sync=true",
        files={"file": ("sync.csv", io.BytesIO(b"Email,State\nsync@test.com,CT\n"), "text/csv")},
        headers=headers,
    )
    assert sync_resp.status_code == 200
    assert sync_resp.json()["data"]["status"] == "completed"
    print("✓ sync=true keeps inline processing for tests")
    passed += 1

    print(f"\nPhase 2 Async Upload: {passed}/{passed} acceptance checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_tests())
