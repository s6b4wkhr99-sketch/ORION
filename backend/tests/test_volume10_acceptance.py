"""Volume 10 Section 21 — Business Rule Library acceptance tests."""

import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

from app.campaign.forecast import forecast_accuracy
from app.database import Base, SessionLocal, engine
from app.intelligence.datalogix_engine import preserve_datalogix_value
from app.intelligence.forecasting import rule_068_expected_orders, rule_069_expected_revenue, rule_070_le_frame_incentive
from app.intelligence.pipeline import run_segmentation
from app.main import app
from app.processing.seed import seed_configuration
from app.rules.library import (
    DASHBOARD_RULE_MAP,
    DEPENDENCY_MATRIX,
    EXECUTION_ORDER,
    RULE_REGISTRY,
    RULES,
    get_rule,
    resolve_business_rule_id,
)
from app.rules.upload import MAX_UPLOAD_BYTES, UploadRuleError, validate_file_size, validate_file_type, validate_upload_file


def _reset():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_configuration(db)
    db.close()


def run_tests():
    passed = 0

    # Unique Rule IDs
    assert len(RULE_REGISTRY) == len(RULES)
    assert all(r.rule_id.startswith("RULE-") for r in RULES)
    print("✓ Every business rule has a unique Rule ID")
    passed += 1

    # Upload rules
    validate_file_type("customers.csv")
    try:
        validate_file_type("customers.pdf")
        raise AssertionError("expected rejection")
    except UploadRuleError as e:
        assert e.rule_id == "RULE-UP-001"
    try:
        validate_file_size(b"x" * (MAX_UPLOAD_BYTES + 1))
        raise AssertionError("expected size rejection")
    except UploadRuleError as e:
        assert e.rule_id == "RULE-UP-002"
    print("✓ Upload rules UP-001 and UP-002 enforced")
    passed += 1

    # API upload rejects oversized file
    _reset()
    client = TestClient(app)
    big = b"x" * (MAX_UPLOAD_BYTES + 1)
    r = client.post(
        "/api/v1/customers/upload",
        files={"file": ("big.csv", io.BytesIO(big), "text/csv")},
    )
    assert r.status_code == 400
    assert r.json().get("success") is False
    print("✓ Oversized upload rejected via API")
    passed += 1

    # Datalogix RULE-DAT-001
    assert preserve_datalogix_value("estimated_income", "X") == "X"
    rule = get_rule("RULE-DAT-001")
    assert rule is not None
    assert "Rule-005" in rule.implementation_refs
    print("✓ Datalogix preservation traceable to RULE-DAT-001")
    passed += 1

    # Forecast rules documented
    orders = rule_068_expected_orders(target_customers=1000, conversion_rate=0.01)
    revenue = rule_069_expected_revenue(expected_orders=orders["expected_orders"], product_price=5499.0)
    incentive = rule_070_le_frame_incentive(expected_orders=orders["expected_orders"], product="Master S4")
    assert resolve_business_rule_id("Rule-068") == "RULE-FOR-001"
    assert resolve_business_rule_id("Rule-069") == "RULE-FOR-002"
    assert resolve_business_rule_id("Rule-070") == "RULE-FOR-003"
    accuracy = forecast_accuracy(6000, revenue["expected_revenue"])
    assert accuracy is not None
    assert get_rule("RULE-FOR-004") is not None
    print("✓ Forecast calculations documented and traceable")
    passed += 1

    # Intelligence trace includes business rule IDs
    result = run_segmentation(
        {"state": "CT", "zip": "06801"},
        {
            "estimated_income_code": "150000",
            "home_value_code": "500000",
            "net_worth_indicator": "X",
            "online_access_code": "Yes",
            "retail_card_code": "Yes",
            "age_range": "45-54",
            "generation": "Baby Boomer",
        },
        None,
    )
    trace = result.get("rule_trace", [])
    assert trace, "expected rule trace"
    assert any(t.get("business_rule_id") for t in trace)
    print("✓ Recommendations and intelligence traceable to business rules")
    passed += 1

    # Dashboard metrics traceable
    assert DASHBOARD_RULE_MAP["expected_revenue"] == "RULE-FOR-002"
    assert DASHBOARD_RULE_MAP["le_frame_incentive"] == "RULE-FOR-003"
    print("✓ Dashboard metrics traceable to rules")
    passed += 1

    # Execution order and dependencies
    assert "Upload" in EXECUTION_ORDER
    assert EXECUTION_ORDER.index("Learning") > EXECUTION_ORDER.index("Campaign Report")
    assert DEPENDENCY_MATRIX["Forecast"] == ("Campaign",)
    assert DEPENDENCY_MATRIX["Learning"] == ("Campaign Report",)
    print("✓ Rule execution order and dependencies documented")
    passed += 1

    # Governance metadata on rules
    sample = get_rule("RULE-REC-002")
    assert sample.version == "1.0"
    assert sample.approval_status == "Approved"
    print("✓ Rule governance metadata present")
    passed += 1

    print(f"\nVolume 10 acceptance: {passed}/{passed} passed")
    return passed


if __name__ == "__main__":
    try:
        run_tests()
    except AssertionError as exc:
        print(f"\nFAILED: {exc}")
        raise SystemExit(1)
