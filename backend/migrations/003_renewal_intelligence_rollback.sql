-- Rollback: 003_renewal_intelligence.sql
-- Drops all tables and objects created by the renewal intelligence migration

-- Drop triggers first
DROP TRIGGER IF EXISTS update_renewal_forecasts_updated_at ON renewal_forecasts;
DROP TRIGGER IF EXISTS update_renewal_alerts_updated_at ON renewal_alerts;
DROP TRIGGER IF EXISTS update_renewal_alert_configs_updated_at ON renewal_alert_configs;
DROP TRIGGER IF EXISTS update_market_contexts_updated_at ON market_contexts;
DROP TRIGGER IF EXISTS update_renewal_readiness_updated_at ON renewal_readiness;

-- Drop tables (in dependency order)
DROP TABLE IF EXISTS renewal_readiness CASCADE;
DROP TABLE IF EXISTS market_contexts CASCADE;
DROP TABLE IF EXISTS renewal_alert_configs CASCADE;
DROP TABLE IF EXISTS renewal_alerts CASCADE;
DROP TABLE IF EXISTS renewal_forecasts CASCADE;
