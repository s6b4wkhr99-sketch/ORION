"""Datalogix vendor-prefixed upload header auto-mapping."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.mapping.auto_engine import generate_mapping_report, strip_vendor_prefix
from app.processing.mapper import build_column_map


CERAGEM_HEADERS = [
    "Email Address",
    "State",
    "ZIP",
    "Datalogix - Age Range",
    "Datalogix - Bank Card",
    "Datalogix - Dwelling Type",
    "Datalogix - Estimated Income",
    "Datalogix - Gender",
    "Datalogix - Generation",
    "Datalogix - Home Value",
    "Datalogix - Household Composition",
    "Datalogix - Length of Residence",
    "Datalogix - Net Worth Indicator",
    "Datalogix - Number of Adults in Household",
    "Datalogix - Number of Children in Household",
    "Datalogix - Number of Persons in Household",
    "Datalogix - Online Access",
    "Datalogix - Retail Card",
    "Datalogix - DMA Code",
    "Datalogix - County Code",
]


def test_strip_vendor_prefix():
    assert strip_vendor_prefix("Datalogix - Net Worth Indicator") == "Net Worth Indicator"
    assert strip_vendor_prefix("datalogix: Gender") == "Gender"


def test_datalogix_prefixed_headers_map_to_internal_fields():
    db = SessionLocal()
    try:
        column_map = build_column_map(db, CERAGEM_HEADERS)
        expected = {
            "email_address": "Email Address",
            "state": "State",
            "zip_code": "ZIP",
            "age_range": "Datalogix - Age Range",
            "bank_card": "Datalogix - Bank Card",
            "dwelling_type": "Datalogix - Dwelling Type",
            "estimated_income": "Datalogix - Estimated Income",
            "gender": "Datalogix - Gender",
            "generation": "Datalogix - Generation",
            "home_value": "Datalogix - Home Value",
            "household_composition": "Datalogix - Household Composition",
            "length_of_residence": "Datalogix - Length of Residence",
            "net_worth_indicator": "Datalogix - Net Worth Indicator",
            "adults": "Datalogix - Number of Adults in Household",
            "children": "Datalogix - Number of Children in Household",
            "persons": "Datalogix - Number of Persons in Household",
            "online_access": "Datalogix - Online Access",
            "retail_card": "Datalogix - Retail Card",
            "dma_code": "Datalogix - DMA Code",
            "county_code": "Datalogix - County Code",
        }
        for internal, source in expected.items():
            assert column_map.get(internal) == source, f"{internal} -> {column_map.get(internal)}"
        report = generate_mapping_report(db, CERAGEM_HEADERS)
        datalogix_mapped = sum(
            1
            for row in report["mapping_report"]
            if row["uploaded_header"].startswith("Datalogix -") and row["status"] == "mapped"
        )
        assert datalogix_mapped == 17
    finally:
        db.close()


if __name__ == "__main__":
    test_strip_vendor_prefix()
    test_datalogix_prefixed_headers_map_to_internal_fields()
    print("PASS: Datalogix header mapping")
