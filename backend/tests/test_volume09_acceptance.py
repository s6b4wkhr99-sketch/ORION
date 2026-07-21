"""Volume 09 Section 24 — Data dictionary acceptance tests."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, SessionLocal, engine
from app.mapping.data_dictionary import (
    ALL_FIELDS,
    CAMPAIGN_REPORT_ALIASES,
    DASHBOARD_METRIC_MAP,
    EXPORT_PROVIDER_MAPPINGS,
    FIELD_REGISTRY,
    UPLOAD_SOURCE_MAPPINGS,
    apply_internal_to_model_data,
    db_column,
    detect_duplicate_source_mappings,
    internal_name,
)
from app.processing.campaign_mapper import build_campaign_column_map, validate_campaign_column_map
from app.processing.mapper import build_column_map, validate_column_map
from app.processing.seed import seed_configuration
from app.processing.validator import is_valid_email, normalize_zip, validate_revenue, validate_state


def _reset():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_configuration(db)
    db.close()


def run_tests():
    _reset()
    passed = 0

    # No duplicated internal field in registry
    assert len(FIELD_REGISTRY) == len(ALL_FIELDS)
    print("✓ No duplicated internal fields in registry")
    passed += 1

    # Upload mappings use canonical internal names
    targets = {t for _, t, _, _ in UPLOAD_SOURCE_MAPPINGS}
    assert "email_address" in targets
    assert "zip_code" in targets
    assert "net_worth_indicator" in targets
    assert "email" not in targets
    print("✓ Upload fields map to canonical internal names")
    passed += 1

    # DB backward compatibility bridge
    assert db_column("email_address") == "email"
    assert db_column("zip_code") == "zip"
    assert internal_name("email") == "email_address"
    model_data = apply_internal_to_model_data({"email_address": "a@b.com", "zip_code": "06801"})
    assert model_data["email"] == "a@b.com"
    assert model_data["zip"] == "06801"
    print("✓ Internal-to-DB mapping preserves backward compatibility")
    passed += 1

    # Section 21 validation rules
    assert is_valid_email("test@ceragem.com")
    assert not is_valid_email("bad-email")
    assert normalize_zip("06801-1234") == "06801"
    assert validate_state("CT")
    assert validate_revenue(1000.0)
    assert not validate_revenue(-1)
    print("✓ Data validation rules")
    passed += 1

    # Upload column mapping from seeded dictionary
    db = SessionLocal()
    try:
        headers = ["Email", "First Name", "Last Name", "State", "ZIP", "Estimated Income"]
        col_map = build_column_map(db, headers)
        validation = validate_column_map(db, col_map)
        assert validation["is_valid"] is True
        assert col_map.get("email_address") == "Email"
        assert col_map.get("zip_code") == "ZIP"
        assert len(detect_duplicate_source_mappings(col_map)) == 0
    finally:
        db.close()
    print("✓ Upload mapping from data dictionary")
    passed += 1

    # Campaign report normalization (Section 20)
    report_headers = ["Campaign Name", "Campaign ID", "State", "Sent", "Open", "Click", "Revenue"]
    report_map = build_campaign_column_map(report_headers)
    report_validation = validate_campaign_column_map(report_map)
    assert report_validation["is_valid"] is True
    assert report_map["total_sent"] == "Sent"
    assert report_map["opened"] == "Open"
    assert report_map["clicked"] == "Click"
    assert report_map["actual_revenue"] == "Revenue"
    print("✓ Campaign report provider field normalization")
    passed += 1

    # Export provider mappings use internal fields only
    export_fields = {f for _, f, _, _, _ in EXPORT_PROVIDER_MAPPINGS}
    assert "email_address" in export_fields
    assert "email" not in export_fields
    print("✓ Export mappings use internal field names")
    passed += 1

    # Dashboard metric mapping (Section 18)
    assert DASHBOARD_METRIC_MAP["le_frame_incentive"] == "expected_incentive"
    assert DASHBOARD_METRIC_MAP["zip_code"] == "zip_code"
    print("✓ Dashboard metric mapping defined")
    passed += 1

    # Campaign performance aliases cover Section 13 fields
    assert "total_sent" in CAMPAIGN_REPORT_ALIASES
    assert "actual_revenue" in CAMPAIGN_REPORT_ALIASES
    print("✓ Performance field aliases defined")
    passed += 1

    print(f"\nVolume 09 acceptance: {passed}/{passed} passed")
    return passed


if __name__ == "__main__":
    try:
        run_tests()
    except AssertionError as exc:
        print(f"\nFAILED: {exc}")
        raise SystemExit(1)
