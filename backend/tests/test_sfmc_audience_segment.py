"""SFMC audience segment mapping tests."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.mapping.auto_engine import generate_mapping_report
from app.processing.mapper import build_column_map
from app.reference.sfmc_audience_segments import (
    BY_CIOS_KEY,
    SFMC_AUDIENCE_SEGMENTS,
    audience_segment_payload,
    resolve_audience_segment,
)


CERAGEM_HEADERS = [
    "Email Address",
    "State",
    "ZIP",
    "Segment ID",
    "Segment Code",
    "Segment Name",
    "Contact Permission",
]


def test_sfmc_catalog_has_five_segments():
    assert len(SFMC_AUDIENCE_SEGMENTS) == 5
    assert len(BY_CIOS_KEY) == 5


def test_resolve_by_segment_id():
    seg = resolve_audience_segment(segment_id="3596226")
    assert seg is not None
    assert seg.cios_key == "multi_channel_primary"
    assert seg.segment_name == "Email and Direct Mail - 1"


def test_resolve_by_segment_code_and_name():
    seg = resolve_audience_segment(segment_code="SEG1-2", segment_name="ignored")
    assert seg is not None
    assert seg.cios_key == "email_only_secondary"

    seg2 = resolve_audience_segment(segment_name="Email and Direct Mail - 3")
    assert seg2 is not None
    assert seg2.cios_key == "multi_channel_tertiary"


def test_audience_segment_payload_normalizes_catalog_values():
    payload = audience_segment_payload(segment_id="3596230", segment_code="WRONG", segment_name="WRONG")
    assert payload == {
        "sfmc_segment_id": "3596230",
        "sfmc_segment_code": "SEG6AB685C7-2",
        "sfmc_segment_name": "Email and Direct Mail - 2",
        "audience_segment": "multi_channel_secondary",
    }


def test_segment_headers_map_to_internal_fields():
    db = SessionLocal()
    try:
        column_map = build_column_map(db, CERAGEM_HEADERS)
        assert column_map.get("segment_id") == "Segment ID"
        assert column_map.get("segment_code") == "Segment Code"
        assert column_map.get("segment_name") == "Segment Name"
        report = generate_mapping_report(db, CERAGEM_HEADERS)
        mapped = [r for r in report["mapping_report"] if r["internal_field"].startswith("segment_")]
        assert len(mapped) == 3
        assert all(r["status"] == "mapped" for r in mapped)
    finally:
        db.close()


if __name__ == "__main__":
    test_sfmc_catalog_has_five_segments()
    test_resolve_by_segment_id()
    test_resolve_by_segment_code_and_name()
    test_audience_segment_payload_normalizes_catalog_values()
    test_segment_headers_map_to_internal_fields()
    print("PASS: SFMC audience segment mapping")
