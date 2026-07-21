"""Volume 16 — Spec table/column registry (logical → physical mapping)."""

from __future__ import annotations

# Spec table name → physical SQLAlchemy __tablename__
TABLE_MAP: dict[str, str] = {
    "customer": "customers",
    "customer_intelligence": "customer_intelligence",
    "upload_file": "raw_upload",
    "upload_history": "upload_history",
    "campaign": "campaign",
    "campaign_target": "campaign_target",
    "campaign_report": "campaign_report",
    "campaign_learning": "campaign_learning",
    "recommendation": "recommendation",
    "provider": "provider",
    "provider_mapping": "provider_field_mapping",
    "user_account": "users",
    "role": "role",
    "permission": "permission",
    "audit_log": "audit_log",
    "export_history": "export_job",
    "product_master": "product_master",
    "state_master": "state_master",
    "zip_master": "zip_master",
    "ceragem_segment_master": "ceragem_segment_master",
    "purchase_power_master": "purchase_power_master",
}

COLUMN_ALIASES: dict[str, dict[str, str]] = {
    "customer": {
        "email_address": "email",
        "zip_code": "zip",
    },
    "customer_intelligence": {
        "intelligence_id": "id",
        "purchase_power": "purchase_power_index",
        "pain_index": "pain_index",
        "lifestyle_index": "lifestyle_index",
        "campaign_priority": "campaign_priority",
        "generated_at": "generated_at",
        "rule_version": "rule_version",
    },
    "campaign": {
        "campaign_status": "status",
    },
    "upload_file": {
        "upload_id": "upload_id",
        "filename": "filename",
        "uploaded_at": "uploaded_date",
        "processing_status": "status",
    },
    "user_account": {
        "user_id": "email",
        "email": "email",
        "status": "is_active",
    },
    "audit_log": {
        "entity": "entity_type",
        "user_agent": "browser",
        "created_at": "timestamp",
    },
}

FOREIGN_KEYS: list[tuple[str, str, str, str]] = [
    ("customer_intelligence", "customer_id", "customers", "customer_id"),
    ("campaign_target", "customer_id", "customers", "customer_id"),
    ("campaign_target", "campaign_id", "campaign", "campaign_id"),
    ("campaign_report", "campaign_id", "campaign", "campaign_id"),
    ("campaign_learning", "campaign_id", "campaign", "campaign_id"),
    ("recommendation", "customer_id", "customers", "customer_id"),
    ("provider_field_mapping", "provider_id", "provider", "provider_id"),
    ("upload_history", "upload_id", "raw_upload", "upload_id"),
]

INDEXES: list[tuple[str, str, bool]] = [
    ("customers", "idx_customer_email", False),
    ("customers", "idx_customer_state", False),
    ("customers", "idx_customer_zip", False),
    ("customers", "idx_customer_state_zip", True),
    ("customer_intelligence", "idx_intelligence_segment", False),
    ("customer_intelligence", "idx_intelligence_purchase_power", False),
    ("customer_intelligence", "idx_intelligence_campaign_priority", False),
    ("customer_intelligence", "idx_intelligence_recommended_product", False),
    ("customer_intelligence", "idx_intelligence_segment_purchase", True),
    ("campaign", "idx_campaign_status", False),
    ("campaign", "idx_campaign_type", False),
    ("campaign", "idx_campaign_status_provider", True),
    ("campaign_target", "idx_campaign_target_campaign_customer", True),
    ("campaign_learning", "idx_campaign_learning_score", False),
    ("audit_log", "idx_audit_user", False),
    ("audit_log", "idx_audit_entity", False),
    ("audit_log", "idx_audit_created", False),
]

UNIQUE_CONSTRAINTS: list[tuple[str, str]] = [
    ("customers", "uk_customer_email"),
    ("provider", "uk_provider_name"),
    ("provider_field_mapping", "uk_provider_internal_field"),
]

CHECK_CONSTRAINTS: list[tuple[str, str]] = [
    (
        "customer_intelligence",
        "chk_expected_conversion_range",
        "expected_conversion >= 0 AND expected_conversion <= 1",
    ),
    ("customer_intelligence", "chk_expected_revenue_nonneg", "expected_revenue >= 0"),
    ("campaign", "chk_forecast_revenue_nonneg", "forecast_revenue IS NULL OR forecast_revenue >= 0"),
    ("campaign", "chk_actual_revenue_nonneg", "actual_revenue IS NULL OR actual_revenue >= 0"),
]

VIEWS: tuple[str, ...] = (
    "vw_customer_summary",
    "vw_campaign_summary",
    "vw_state_summary",
    "vw_zip_summary",
    "vw_product_summary",
    "vw_roi_summary",
)

MATERIALIZED_VIEWS: tuple[str, ...] = (
    "mv_campaign_forecast",
    "mv_state_revenue",
    "mv_product_performance",
)

TRIGGERS: tuple[str, ...] = (
    "trg_upload_history",
    "trg_intelligence_timestamp",
    "trg_campaign_learning",
    "trg_refresh_dashboard_views",
)

SPEC_TABLES: tuple[str, ...] = tuple(TABLE_MAP.keys())
