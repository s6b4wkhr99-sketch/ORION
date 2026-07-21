"""Upload processing profile API."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.acquisition.upload_options import resolve_upload_options
from app.acquisition.upload_profile import get_upload_processing_profile
from app.config import settings


def test_customer_analysis_only_forces_slim_storage():
    settings.customer_analysis_only = True
    settings.bulk_upload_mode = False
    options = resolve_upload_options(10)
    assert options.store_raw_rows is False
    assert options.store_full_trace is False
    assert options.record_intelligence_versions is False
    assert options.sync_recommendation is False
    assert options.commit_every_rows == settings.upload_commit_rows_bulk
    settings.customer_analysis_only = False


def test_processing_profile_endpoint_shape():
    profile = get_upload_processing_profile(2500000)
    assert "upload_async" in profile
    assert profile["bulk_active_for_estimate"] is True
    assert "recommended_for_2_5m" in profile
    print("PASS: upload processing profile")


if __name__ == "__main__":
    test_customer_analysis_only_forces_slim_storage()
    test_processing_profile_endpoint_shape()
