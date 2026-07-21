"""Volume 16 Sections 10–11 — Dashboard views and materialized views."""

VIEW_DDL: dict[str, str] = {
    "vw_customer_summary": """
        CREATE OR REPLACE VIEW vw_customer_summary AS
        SELECT
            c.customer_id,
            c.email AS email_address,
            c.first_name,
            c.last_name,
            c.state,
            c.zip AS zip_code,
            ci.ceragem_segment,
            ci.prizm_proxy_segment,
            ci.purchase_power_index AS purchase_power,
            ci.pain_index,
            ci.recommended_product,
            ci.expected_revenue,
            ci.campaign_priority,
            ci.generated_at
        FROM customers c
        LEFT JOIN customer_intelligence ci ON ci.customer_id = c.customer_id
    """,
    "vw_campaign_summary": """
        CREATE OR REPLACE VIEW vw_campaign_summary AS
        SELECT
            camp.campaign_id,
            camp.campaign_name,
            camp.campaign_type,
            camp.status AS campaign_status,
            camp.provider,
            camp.budget,
            camp.forecast_revenue,
            camp.actual_revenue,
            camp.forecast_orders,
            camp.actual_orders,
            camp.created_at,
            camp.updated_at
        FROM campaign camp
    """,
    "vw_state_summary": """
        CREATE OR REPLACE VIEW vw_state_summary AS
        SELECT
            c.state,
            COUNT(c.customer_id) AS customer_count,
            AVG(ci.expected_revenue) AS avg_expected_revenue,
            SUM(ci.expected_revenue) AS total_expected_revenue
        FROM customers c
        LEFT JOIN customer_intelligence ci ON ci.customer_id = c.customer_id
        WHERE c.state IS NOT NULL
        GROUP BY c.state
    """,
    "vw_zip_summary": """
        CREATE OR REPLACE VIEW vw_zip_summary AS
        SELECT
            c.zip AS zip_code,
            c.state,
            COUNT(c.customer_id) AS customer_count,
            AVG(ci.purchase_power_index) AS avg_purchase_power,
            SUM(ci.expected_revenue) AS total_expected_revenue
        FROM customers c
        LEFT JOIN customer_intelligence ci ON ci.customer_id = c.customer_id
        WHERE c.zip IS NOT NULL
        GROUP BY c.zip, c.state
    """,
    "vw_product_summary": """
        CREATE OR REPLACE VIEW vw_product_summary AS
        SELECT
            ci.recommended_product,
            COUNT(c.customer_id) AS customer_count,
            AVG(ci.expected_conversion) AS avg_expected_conversion,
            SUM(ci.expected_revenue) AS total_expected_revenue
        FROM customers c
        JOIN customer_intelligence ci ON ci.customer_id = c.customer_id
        WHERE ci.recommended_product IS NOT NULL
        GROUP BY ci.recommended_product
    """,
    "vw_roi_summary": """
        CREATE OR REPLACE VIEW vw_roi_summary AS
        SELECT
            cs.campaign_id,
            SUM(cs.revenue) AS actual_revenue,
            SUM(cs.cost) AS total_cost,
            CASE WHEN SUM(cs.cost) > 0 THEN (SUM(cs.revenue) - SUM(cs.cost)) / SUM(cs.cost) ELSE NULL END AS roi
        FROM campaign_state cs
        GROUP BY cs.campaign_id
    """,
}

MATERIALIZED_VIEW_DDL: dict[str, str] = {
    "mv_campaign_forecast": """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_campaign_forecast AS
        SELECT campaign_id, campaign_name, campaign_type, status AS campaign_status,
               forecast_revenue, actual_revenue, forecast_orders, actual_orders, provider, updated_at
        FROM campaign
    """,
    "mv_state_revenue": """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_state_revenue AS
        SELECT * FROM vw_state_summary
    """,
    "mv_product_performance": """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_product_performance AS
        SELECT * FROM vw_product_summary
    """,
}

INDEX_DDL: list[str] = [
    "CREATE INDEX IF NOT EXISTS idx_customer_upload_id ON customers (upload_id)",
    "CREATE INDEX IF NOT EXISTS idx_customer_email ON customers (email)",
    "CREATE INDEX IF NOT EXISTS idx_customer_state ON customers (state)",
    "CREATE INDEX IF NOT EXISTS idx_customer_zip ON customers (zip)",
    "CREATE INDEX IF NOT EXISTS idx_customer_state_zip ON customers (state, zip)",
    "CREATE INDEX IF NOT EXISTS idx_intelligence_segment ON customer_intelligence (ceragem_segment)",
    "CREATE INDEX IF NOT EXISTS idx_intelligence_purchase_power ON customer_intelligence (purchase_power_index)",
    "CREATE INDEX IF NOT EXISTS idx_intelligence_campaign_priority ON customer_intelligence (campaign_priority)",
    "CREATE INDEX IF NOT EXISTS idx_intelligence_recommended_product ON customer_intelligence (recommended_product)",
    "CREATE INDEX IF NOT EXISTS idx_customer_upload_state ON customers (upload_id, state)",
    "CREATE INDEX IF NOT EXISTS idx_upload_rollup_upload_dim ON upload_rollup (upload_id, dimension)",
    "CREATE INDEX IF NOT EXISTS idx_upload_rollup_dim_scope ON upload_rollup (dimension, scope)",
    "CREATE INDEX IF NOT EXISTS idx_intelligence_segment_purchase ON customer_intelligence (ceragem_segment, purchase_power_index)",
    "CREATE INDEX IF NOT EXISTS idx_campaign_status ON campaign (status)",
    "CREATE INDEX IF NOT EXISTS idx_campaign_type ON campaign (campaign_type)",
    "CREATE INDEX IF NOT EXISTS idx_campaign_status_provider ON campaign (status, provider)",
    "CREATE INDEX IF NOT EXISTS idx_campaign_target_campaign_customer ON campaign_target (campaign_id, customer_id)",
    "CREATE INDEX IF NOT EXISTS idx_campaign_learning_score ON campaign_learning (learning_score)",
    "CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log (user_id)",
    "CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_log (entity_type)",
    "CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_log (timestamp)",
]
