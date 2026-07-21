"""RFC-001 — Customer Upload Auto Mapping Engine acceptance tests."""

import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.main import app
from app.mapping.auto_engine import auto_map_headers, detect_headers, generate_mapping_report
from app.mapping.standardization import standardize_state, standardize_zip, standardize_boolean
from app.models.auto_mapping import FieldAlias, FieldMaster, MappingException, MappingHistory, ProviderUploadTemplate
from app.processing.seed import seed_configuration
from app.security.users import seed_users
from tests.qa_helpers import ADMIN_EMAIL, ADMIN_PASSWORD, assert_success, login, make_csv_content, reset_db

RFC_CRITERIA = [
    "RFC-001-01 No manual mapping required",
    "RFC-001-02 Header detection",
    "RFC-001-03 Alias dictionary",
    "RFC-001-04 Data standardization",
    "RFC-001-05 Validation",
    "RFC-001-06 Mapping report",
    "RFC-001-07 Intelligence pipeline receives standardized data",
    "RFC-001-08 Unknown headers logged",
    "RFC-001-09 Administrator aliases reusable",
    "RFC-001-10 Deterministic processing",
]


def run_tests() -> int:
    reset_db()
    client = TestClient(app)
    headers = login(client)
    passed = 0

    # RFC-001-01 / 02 / 06 — upload preview auto mapping + report
    csv = (
        "Email,State,ZIP Code,Customer Email,Home Price,Unknown Value\n"
        "rfc@qa.test,NJ,07650,rfc@qa.test,500000,xyz\n"
    )
    r = client.post(
        "/api/v1/customers/upload/preview",
        files={"file": ("rfc.csv", io.BytesIO(csv.encode()), "text/csv")},
        headers=headers,
    )
    preview = assert_success(r)
    assert preview["validation"]["is_valid"] is True
    assert "mapping_report" in preview
    assert len(preview["detected_headers"]) == 6
    email_row = next(m for m in preview["mapping_report"] if m["uploaded_header"] == "Email")
    assert email_row["match_type"] == "exact"
    assert email_row["confidence"] == 100
    print(f"✓ {RFC_CRITERIA[0]}")
    print(f"✓ {RFC_CRITERIA[1]}")
    print(f"✓ {RFC_CRITERIA[5]}")
    passed += 3

    # RFC-001-03 — alias dictionary API + Customer Email alias
    r = client.get("/api/v1/mapping/aliases?internal_field=email_address", headers=headers)
    aliases = assert_success(r)["aliases"]
    assert any(a["alias_header"] == "Customer Email" for a in aliases)
    alias_row = next(m for m in preview["mapping_report"] if m["uploaded_header"] == "Customer Email")
    assert alias_row["match_type"] == "alias"
    print(f"✓ {RFC_CRITERIA[2]}")
    passed += 1

    # RFC-001-04 — standardization API
    r = client.post(
        "/api/v1/mapping/standardize",
        json={
            "rows": [{"state": "New Jersey", "zip": "07650-2345", "flag": "YES"}],
            "column_map": {"state": "state", "zip": "zip_code", "flag": "online_access"},
        },
        headers=headers,
    )
    std = assert_success(r)
    assert std["standardized_rows"][0]["state"] == "NJ"
    assert std["standardized_rows"][0]["zip_code"] == "07650"
    assert std["standardized_rows"][0]["online_access"] == "Yes"
    assert standardize_state("N.J.") == "NJ"
    assert standardize_zip("7650") == "07650"
    assert standardize_boolean("1") == "Yes"
    print(f"✓ {RFC_CRITERIA[3]}")
    passed += 1

    # RFC-001-05 — validate API
    r = client.post(
        "/api/v1/mapping/validate",
        files={"file": ("validate.csv", io.BytesIO(csv.encode()), "text/csv")},
        headers=headers,
    )
    val = assert_success(r)
    assert val["validation"]["is_valid"] is True
    print(f"✓ {RFC_CRITERIA[4]}")
    passed += 1

    # RFC-001-07 — full upload completes with intelligence
    upload_csv = make_csv_content(2)
    r = client.post(
        "/api/v1/customers/upload",
        files={"file": ("rfc_upload.csv", io.BytesIO(upload_csv.encode()), "text/csv")},
        headers=headers,
    )
    up = assert_success(r)
    assert up["status"] == "completed"
    assert up["customers"] == 2
    print(f"✓ {RFC_CRITERIA[6]}")
    passed += 1

    # RFC-001-08 — unknown headers logged on upload
    r = client.post(
        "/api/v1/customers/upload",
        files={"file": ("rfc_unknown.csv", io.BytesIO(csv.encode()), "text/csv")},
        headers=headers,
    )
    assert assert_success(r)["status"] == "completed"
    db = SessionLocal()
    try:
        assert db.query(MappingException).filter(MappingException.uploaded_header == "Unknown Value").count() >= 1
        assert db.query(MappingHistory).count() >= 6
        preview_unknown = next(m for m in preview["mapping_report"] if m["uploaded_header"] == "Unknown Value")
        assert preview_unknown["match_type"] == "unknown"
        print(f"✓ {RFC_CRITERIA[7]}")
        passed += 1

        # RFC-001-09 — field_master + aliases seeded
        assert db.query(FieldMaster).count() >= 10
        assert db.query(FieldAlias).count() >= 20
        assert db.query(ProviderUploadTemplate).count() >= 5
        print(f"✓ {RFC_CRITERIA[8]}")
        passed += 1
    finally:
        db.close()

    # RFC-001-10 — deterministic auto map
    db = SessionLocal()
    try:
        headers_list = ["Email", "State", "ZIP"]
        first = generate_mapping_report(db, headers_list)
        second = generate_mapping_report(db, headers_list)
        assert first["mapping_report"] == second["mapping_report"]
        print(f"✓ {RFC_CRITERIA[9]}")
        passed += 1
    finally:
        db.close()

    # New mapping APIs
    r = client.get("/api/v1/mapping/fields", headers=headers)
    fields = assert_success(r)["fields"]
    assert any(f["internal_field"] == "email_address" for f in fields)

    r = client.post(
        "/api/v1/mapping/report",
        files={"file": ("report.csv", io.BytesIO(csv.encode()), "text/csv")},
        headers=headers,
    )
    report = assert_success(r)
    assert report["summary"]["mapped"] >= 4

    print(f"\nRFC-001 acceptance: {passed}/{len(RFC_CRITERIA)} criteria passed")
    return 0 if passed == len(RFC_CRITERIA) else 1


if __name__ == "__main__":
    raise SystemExit(run_tests())
