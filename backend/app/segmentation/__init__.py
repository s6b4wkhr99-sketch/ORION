"""
Volume 08 Rule 005 — Intelligence / segmentation engine entry point.

Implementation lives in app.intelligence; this package is the approved module path.
"""

from app.intelligence.pipeline import run_intelligence_pipeline, run_segmentation
from app.intelligence.forecasting import compute_campaign_forecast, forecast_customer, le_frame_incentive

__all__ = [
    "run_intelligence_pipeline",
    "run_segmentation",
    "forecast_customer",
    "compute_campaign_forecast",
    "le_frame_incentive",
]
