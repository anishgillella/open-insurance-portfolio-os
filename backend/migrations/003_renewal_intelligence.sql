-- Migration: 003_renewal_intelligence.sql
-- Phase 4.4: Renewal Intelligence Engine
-- Creates tables for premium forecasting, renewal alerts, market context, and document readiness

-- =============================================================================
-- Renewal Forecasts Table
-- =============================================================================
CREATE TABLE IF NOT EXISTS renewal_forecasts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign Keys
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    program_id UUID REFERENCES insurance_programs(id) ON DELETE SET NULL,
    policy_id UUID REFERENCES policies(id) ON DELETE SET NULL,

    -- Renewal Context
    renewal_year INTEGER NOT NULL,
    current_expiration_date DATE NOT NULL,
    current_premium NUMERIC(15, 2),

    -- Rule-Based Estimate
    rule_based_estimate NUMERIC(15, 2),
    rule_based_change_pct NUMERIC(5, 2),

    -- LLM Predictions
    llm_predicted_low NUMERIC(15, 2),
    llm_predicted_mid NUMERIC(15, 2),
    llm_predicted_high NUMERIC(15, 2),
    llm_confidence_score INTEGER CHECK (llm_confidence_score >= 0 AND llm_confidence_score <= 100),

    -- Factor Breakdown (JSONB)
    factor_breakdown JSONB,

    -- LLM Analysis
    llm_reasoning TEXT,
    llm_market_context TEXT,
    llm_negotiation_points JSONB,

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'active',

    -- Metadata
    forecast_date TIMESTAMP WITH TIME ZONE NOT NULL,
    forecast_trigger VARCHAR(50),
    llm_model_used VARCHAR(100),
    llm_latency_ms INTEGER,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for renewal_forecasts
CREATE INDEX IF NOT EXISTS ix_renewal_forecasts_property_id ON renewal_forecasts(property_id);
CREATE INDEX IF NOT EXISTS ix_renewal_forecasts_program_id ON renewal_forecasts(program_id);
CREATE INDEX IF NOT EXISTS ix_renewal_forecasts_policy_id ON renewal_forecasts(policy_id);
CREATE INDEX IF NOT EXISTS ix_renewal_forecasts_status ON renewal_forecasts(status);
CREATE INDEX IF NOT EXISTS ix_renewal_forecasts_expiration ON renewal_forecasts(current_expiration_date);

-- =============================================================================
-- Renewal Alerts Table
-- =============================================================================
CREATE TABLE IF NOT EXISTS renewal_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign Keys
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    policy_id UUID NOT NULL REFERENCES policies(id) ON DELETE CASCADE,

    -- Alert Details
    threshold_days INTEGER NOT NULL,
    days_until_expiration INTEGER NOT NULL,
    expiration_date TIMESTAMP WITH TIME ZONE NOT NULL,
    severity VARCHAR(20) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT,

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    triggered_at TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Acknowledgement
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    acknowledged_by VARCHAR(255),
    acknowledgement_notes TEXT,

    -- Resolution
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by VARCHAR(255),
    resolution_notes TEXT,

    -- LLM Enhancement
    llm_priority_score INTEGER CHECK (llm_priority_score >= 1 AND llm_priority_score <= 10),
    llm_renewal_strategy TEXT,
    llm_key_actions JSONB,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for renewal_alerts
CREATE INDEX IF NOT EXISTS ix_renewal_alerts_property_id ON renewal_alerts(property_id);
CREATE INDEX IF NOT EXISTS ix_renewal_alerts_policy_id ON renewal_alerts(policy_id);
CREATE INDEX IF NOT EXISTS ix_renewal_alerts_status ON renewal_alerts(status);
CREATE INDEX IF NOT EXISTS ix_renewal_alerts_severity ON renewal_alerts(severity);
CREATE INDEX IF NOT EXISTS ix_renewal_alerts_expiration ON renewal_alerts(expiration_date);

-- =============================================================================
-- Renewal Alert Configs Table
-- =============================================================================
CREATE TABLE IF NOT EXISTS renewal_alert_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign Key (unique per property)
    property_id UUID NOT NULL UNIQUE REFERENCES properties(id) ON DELETE CASCADE,

    -- Configuration
    thresholds INTEGER[] NOT NULL DEFAULT ARRAY[90, 60, 30],
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    severity_mapping JSONB,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Index for renewal_alert_configs
CREATE INDEX IF NOT EXISTS ix_renewal_alert_configs_property_id ON renewal_alert_configs(property_id);

-- =============================================================================
-- Market Contexts Table
-- =============================================================================
CREATE TABLE IF NOT EXISTS market_contexts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign Key
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,

    -- Analysis Period
    analysis_date TIMESTAMP WITH TIME ZONE NOT NULL,
    valid_until TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Market Condition Assessment
    market_condition VARCHAR(50) NOT NULL,
    market_condition_reasoning TEXT,

    -- Property-Specific Analysis
    property_risk_profile TEXT,
    carrier_relationship_assessment TEXT,

    -- Policy Analysis (JSONB)
    policy_analysis JSONB,
    yoy_changes JSONB,

    -- Negotiation Intelligence (JSONB)
    negotiation_leverage JSONB,
    negotiation_recommendations JSONB,

    -- Risk Insights
    risk_insights JSONB,

    -- Executive Summary
    executive_summary TEXT,

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'current',

    -- LLM Metadata
    llm_model_used VARCHAR(100),
    llm_latency_ms INTEGER,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for market_contexts
CREATE INDEX IF NOT EXISTS ix_market_contexts_property_id ON market_contexts(property_id);
CREATE INDEX IF NOT EXISTS ix_market_contexts_status ON market_contexts(status);
CREATE INDEX IF NOT EXISTS ix_market_contexts_analysis_date ON market_contexts(analysis_date);

-- =============================================================================
-- Renewal Readiness Table
-- =============================================================================
CREATE TABLE IF NOT EXISTS renewal_readiness (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign Key
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,

    -- Renewal Context
    target_renewal_date TIMESTAMP WITH TIME ZONE NOT NULL,
    assessment_date TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Readiness Score
    readiness_score INTEGER NOT NULL CHECK (readiness_score >= 0 AND readiness_score <= 100),
    readiness_grade VARCHAR(1) NOT NULL,

    -- Document Status (JSONB)
    document_status JSONB NOT NULL,

    -- LLM Verification (JSONB)
    llm_verification JSONB,

    -- Issues & Recommendations (JSONB)
    issues JSONB,
    recommendations JSONB,

    -- Timeline Integration (JSONB)
    renewal_timeline JSONB,

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'current',

    -- LLM Metadata
    llm_model_used VARCHAR(100),
    llm_latency_ms INTEGER,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for renewal_readiness
CREATE INDEX IF NOT EXISTS ix_renewal_readiness_property_id ON renewal_readiness(property_id);
CREATE INDEX IF NOT EXISTS ix_renewal_readiness_status ON renewal_readiness(status);
CREATE INDEX IF NOT EXISTS ix_renewal_readiness_target_date ON renewal_readiness(target_renewal_date);

-- =============================================================================
-- Updated_at Triggers
-- =============================================================================

-- Create trigger function if not exists
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers to new tables
DROP TRIGGER IF EXISTS update_renewal_forecasts_updated_at ON renewal_forecasts;
CREATE TRIGGER update_renewal_forecasts_updated_at
    BEFORE UPDATE ON renewal_forecasts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_renewal_alerts_updated_at ON renewal_alerts;
CREATE TRIGGER update_renewal_alerts_updated_at
    BEFORE UPDATE ON renewal_alerts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_renewal_alert_configs_updated_at ON renewal_alert_configs;
CREATE TRIGGER update_renewal_alert_configs_updated_at
    BEFORE UPDATE ON renewal_alert_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_market_contexts_updated_at ON market_contexts;
CREATE TRIGGER update_market_contexts_updated_at
    BEFORE UPDATE ON market_contexts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_renewal_readiness_updated_at ON renewal_readiness;
CREATE TRIGGER update_renewal_readiness_updated_at
    BEFORE UPDATE ON renewal_readiness
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- Comments
-- =============================================================================

COMMENT ON TABLE renewal_forecasts IS 'Premium predictions with rule-based and LLM analysis for renewal planning';
COMMENT ON TABLE renewal_alerts IS 'Configurable alerts for upcoming policy expirations';
COMMENT ON TABLE renewal_alert_configs IS 'Per-property alert threshold configuration';
COMMENT ON TABLE market_contexts IS 'LLM-synthesized market intelligence and negotiation recommendations';
COMMENT ON TABLE renewal_readiness IS 'Document readiness assessment for renewal preparation';
