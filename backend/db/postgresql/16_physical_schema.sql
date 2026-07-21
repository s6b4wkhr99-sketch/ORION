-- Ceragem CIOS Volume 16 — PostgreSQL 16 Physical Schema
-- Generated from docs/16_Database_ERD_Physical_Schema.md
-- Apply via: psql $DATABASE_URL -f backend/db/postgresql/16_physical_schema.sql
-- Runtime apply: app.schema.apply.apply_physical_schema(engine)

-- NOTE: Core ORM tables (customers, customer_intelligence, campaign, etc.) are
-- created by Alembic/SQLAlchemy. This script adds indexes, views, checks, and MVs.

\echo 'Applying Volume 16 indexes...'
CREATE INDEX IF NOT EXISTS idx_customer_email ON customers (email);
CREATE INDEX IF NOT EXISTS idx_customer_state ON customers (state);
CREATE INDEX IF NOT EXISTS idx_customer_zip ON customers (zip);
CREATE INDEX IF NOT EXISTS idx_customer_state_zip ON customers (state, zip);
CREATE INDEX IF NOT EXISTS idx_intelligence_segment ON customer_intelligence (ceragem_segment);
CREATE INDEX IF NOT EXISTS idx_intelligence_purchase_power ON customer_intelligence (purchase_power_index);
CREATE INDEX IF NOT EXISTS idx_intelligence_campaign_priority ON customer_intelligence (campaign_priority);
CREATE INDEX IF NOT EXISTS idx_intelligence_recommended_product ON customer_intelligence (recommended_product);
CREATE INDEX IF NOT EXISTS idx_intelligence_segment_purchase ON customer_intelligence (ceragem_segment, purchase_power_index);
CREATE INDEX IF NOT EXISTS idx_campaign_status ON campaign (status);
CREATE INDEX IF NOT EXISTS idx_campaign_type ON campaign (campaign_type);
CREATE INDEX IF NOT EXISTS idx_campaign_status_provider ON campaign (status, provider);
CREATE INDEX IF NOT EXISTS idx_campaign_target_campaign_customer ON campaign_target (campaign_id, customer_id);
CREATE INDEX IF NOT EXISTS idx_campaign_learning_score ON campaign_learning (learning_score);
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log (user_id);
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_log (entity_type);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_log (timestamp);

\echo 'Applying Volume 16 views...'
-- Views defined in backend/app/database/views.py (applied automatically on startup)

\echo 'Applying Volume 16 check constraints (PostgreSQL)...'
ALTER TABLE customer_intelligence DROP CONSTRAINT IF EXISTS chk_expected_conversion_range;
ALTER TABLE customer_intelligence ADD CONSTRAINT chk_expected_conversion_range
  CHECK (expected_conversion >= 0 AND expected_conversion <= 1);
ALTER TABLE customer_intelligence DROP CONSTRAINT IF EXISTS chk_expected_revenue_nonneg;
ALTER TABLE customer_intelligence ADD CONSTRAINT chk_expected_revenue_nonneg
  CHECK (expected_revenue >= 0);
ALTER TABLE campaign DROP CONSTRAINT IF EXISTS chk_forecast_revenue_nonneg;
ALTER TABLE campaign ADD CONSTRAINT chk_forecast_revenue_nonneg
  CHECK (forecast_revenue IS NULL OR forecast_revenue >= 0);
ALTER TABLE campaign DROP CONSTRAINT IF EXISTS chk_actual_revenue_nonneg;
ALTER TABLE campaign ADD CONSTRAINT chk_actual_revenue_nonneg
  CHECK (actual_revenue IS NULL OR actual_revenue >= 0);

\echo 'Volume 16 physical schema extensions applied.'
