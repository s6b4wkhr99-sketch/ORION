"""Volume 17 Section 20 — Executive KPI library with rule traceability."""

from app.rules.library import DASHBOARD_RULE_MAP

EXECUTIVE_KPI_KEYS: tuple[str, ...] = (
    "total_customers",
    "target_customers",
    "campaigns",
    "campaign_success_rate",
    "forecast_accuracy",
    "expected_revenue",
    "actual_revenue",
    "revenue_gap",
    "roi",
    "average_conversion",
    "le_frame_incentive",
    "customer_growth",
    "average_order_value",
    "campaign_conversion",
    "provider_performance",
    "state_performance",
    "zip_performance",
    "product_performance",
    "learning_score",
    "recommendation_accuracy",
)


def kpi_with_rule(key: str, value) -> dict:
    return {
        "key": key,
        "value": value,
        "business_rule_id": DASHBOARD_RULE_MAP.get(key),
    }


def build_kpi_library(values: dict) -> list[dict]:
    return [kpi_with_rule(key, values.get(key)) for key in EXECUTIVE_KPI_KEYS if key in values]
