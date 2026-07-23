from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Volume 13 Section 8 — Runtime configuration via environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Application
    app_version: str = "1.2.0"
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    app_timezone: str = "America/New_York"

    # Database
    database_url: str = "sqlite:///./campaign_intelligence.db"
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Upload pipeline (Phase 2/3)
    upload_async: bool = False
    bulk_upload_mode: bool = False
    bulk_upload_row_threshold: int = 100_000
    bulk_upload_skip_raw_rows: bool = True
    bulk_upload_skip_full_trace: bool = True
    bulk_upload_skip_version_history: bool = True
    customer_analysis_only: bool = False
    upload_commit_rows_bulk: int = 5000
    upload_refresh_datalogix_on_duplicate: bool = True
    worker_poll_seconds: int = 5

    # Storage
    upload_dir: str = "uploads"
    export_path: str = "uploads"
    backup_path: str = "backups"
    archive_uploads_gzip: bool = True

    # Dashboard cache (Phase B)
    dashboard_cache_enabled: bool = True
    dashboard_cache_ttl_minutes: int = 60
    dashboard_cache_invalidate_on_startup: bool = False

    # Startup / local native performance
    skip_physical_schema: bool = False
    skip_startup_seed: bool = False
    opportunity_simulate_cache_enabled: bool = False
    opportunity_simulate_cache_ttl_seconds: int = 300

    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_max_requests: int = 180
    rate_limit_window_seconds: int = 60

    # Operations (Phase C)
    ops_report_dir: str = "reports"
    export_retention_days: int = 14
    temp_retention_hours: int = 24
    upload_archive_retention_days: int = 90
    audit_log_retention_days: int = 365

    # Security
    cors_origins: str = "http://localhost:3002,http://127.0.0.1:3002"
    jwt_secret: str = "cios-dev-secret-change-in-production"
    jwt_expire_minutes: int = 30
    auth_required: bool = False
    auth_user_email: str = "user@company.com"
    auth_user_password: str = "Ceragem2026!Adm"

    # SMTP / alerting (Section 14)
    smtp_server: str = ""
    smtp_username: str = ""
    smtp_password: str = ""
    alert_email: str = ""
    alert_slack_webhook: str = ""
    alert_webhook_url: str = ""

    # Geo intelligence — Data Commons ZIP income fallback
    datacommons_api_key: str = ""
    datacommons_zip_income_fallback: bool = True


settings = Settings()
