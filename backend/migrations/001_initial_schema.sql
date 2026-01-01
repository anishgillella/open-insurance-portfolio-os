-- Open Insurance Initial Schema Migration
-- Run this directly in Supabase SQL Editor
-- Version: 001
-- Description: Creates all tables for the Open Insurance platform with RLS

-- Enable UUID extension (usually already enabled in Supabase)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- ORGANIZATIONS
-- Multi-tenancy support. Each organization is a separate customer.
-- ============================================================================
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Identity
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,

    -- Contact
    primary_email TEXT,
    phone TEXT,

    -- Settings
    settings JSONB DEFAULT '{}',

    -- Subscription
    plan TEXT DEFAULT 'free',
    trial_ends_at TIMESTAMP WITH TIME ZONE,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_organizations_slug ON organizations(slug) WHERE deleted_at IS NULL;

-- ============================================================================
-- PROPERTIES
-- Real estate properties that need insurance.
-- ============================================================================
CREATE TABLE properties (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Identity
    name TEXT NOT NULL,
    external_id TEXT,

    -- Address
    address TEXT,
    address_line_2 TEXT,
    city TEXT,
    state TEXT,
    zip TEXT,
    county TEXT,
    country TEXT DEFAULT 'US',

    -- Property Characteristics
    property_type TEXT,
    units INTEGER,
    sq_ft INTEGER,
    year_built INTEGER,
    stories INTEGER,

    -- Construction
    construction_type TEXT,
    roof_type TEXT,
    roof_year INTEGER,

    -- Protection
    has_sprinklers BOOLEAN,
    sprinkler_type TEXT,
    protection_class TEXT,
    alarm_type TEXT,

    -- Risk Factors
    flood_zone TEXT,
    earthquake_zone TEXT,
    wind_zone TEXT,
    crime_score INTEGER,

    -- Status
    status TEXT DEFAULT 'active',

    -- Data Quality
    completeness_pct FLOAT DEFAULT 0,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_properties_org ON properties(organization_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_properties_state ON properties(state) WHERE deleted_at IS NULL;

-- ============================================================================
-- BUILDINGS
-- For properties with multiple buildings.
-- ============================================================================
CREATE TABLE buildings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,

    -- Identity
    name TEXT,
    building_number TEXT,

    -- Characteristics
    sq_ft INTEGER,
    stories INTEGER,
    year_built INTEGER,
    construction_type TEXT,
    occupancy_type TEXT,

    -- Values
    building_value NUMERIC(15, 2),
    contents_value NUMERIC(15, 2),

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_buildings_property ON buildings(property_id) WHERE deleted_at IS NULL;

-- ============================================================================
-- CARRIERS
-- Insurance companies that issue policies.
-- ============================================================================
CREATE TABLE carriers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Identity
    name TEXT NOT NULL UNIQUE,
    short_name TEXT,
    naic_code TEXT,

    -- Ratings
    am_best_rating TEXT,
    am_best_outlook TEXT,
    sp_rating TEXT,

    -- Status
    admitted_states TEXT[],
    surplus_lines_states TEXT[],

    -- Contact
    website TEXT,
    claims_phone TEXT,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_carriers_name ON carriers(LOWER(name));

-- ============================================================================
-- LENDERS
-- Banks and mortgage companies that require insurance.
-- ============================================================================
CREATE TABLE lenders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Identity
    name TEXT NOT NULL UNIQUE,
    short_name TEXT,

    -- Requirements (standard/default)
    min_property_limit NUMERIC(15, 2),
    min_gl_limit NUMERIC(15, 2),
    max_deductible_amount NUMERIC(15, 2),
    max_deductible_pct FLOAT,
    requires_flood BOOLEAN DEFAULT FALSE,
    requires_earthquake BOOLEAN DEFAULT FALSE,
    requires_umbrella BOOLEAN DEFAULT FALSE,
    min_umbrella_limit NUMERIC(15, 2),

    -- Mortgagee Clause
    mortgagee_clause TEXT,

    -- Contact
    address TEXT,
    city TEXT,
    state TEXT,
    zip TEXT,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_lenders_name ON lenders(LOWER(name));

-- ============================================================================
-- INSURED ENTITIES
-- LLCs, LPs, and other legal entities that are named insureds.
-- ============================================================================
CREATE TABLE insured_entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    parent_entity_id UUID REFERENCES insured_entities(id) ON DELETE SET NULL,

    -- Identity
    name TEXT NOT NULL,
    entity_type TEXT,

    -- Contact
    address TEXT,
    city TEXT,
    state TEXT,
    zip TEXT,

    -- Tax
    ein TEXT,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_entities_org ON insured_entities(organization_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_entities_parent ON insured_entities(parent_entity_id);

-- ============================================================================
-- DOCUMENTS
-- Source documents uploaded to the system.
-- ============================================================================
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    property_id UUID REFERENCES properties(id) ON DELETE SET NULL,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- File Information
    file_name TEXT NOT NULL,
    file_url TEXT NOT NULL,
    file_size_bytes INTEGER,
    file_type TEXT,
    mime_type TEXT,
    page_count INTEGER,

    -- Classification
    document_type TEXT,
    document_subtype TEXT,

    -- Key Metadata (extracted)
    carrier TEXT,
    policy_number TEXT,
    effective_date DATE,
    expiration_date DATE,

    -- Processing Status
    upload_status TEXT DEFAULT 'pending',
    ocr_status TEXT DEFAULT 'pending',
    ocr_started_at TIMESTAMP WITH TIME ZONE,
    ocr_completed_at TIMESTAMP WITH TIME ZONE,
    extraction_status TEXT DEFAULT 'pending',
    extraction_started_at TIMESTAMP WITH TIME ZONE,
    extraction_completed_at TIMESTAMP WITH TIME ZONE,

    -- Processing Outputs
    ocr_markdown TEXT,
    ocr_error TEXT,
    extraction_json JSONB,
    extraction_error TEXT,

    -- Quality Metrics
    extraction_confidence FLOAT,
    needs_human_review BOOLEAN DEFAULT FALSE,
    human_reviewed_at TIMESTAMP WITH TIME ZONE,
    human_reviewed_by UUID,

    -- Upload Context
    uploaded_by UUID,
    upload_source TEXT,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_documents_property ON documents(property_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_documents_org ON documents(organization_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_documents_type ON documents(document_type) WHERE deleted_at IS NULL;
CREATE INDEX idx_documents_status ON documents(extraction_status) WHERE deleted_at IS NULL;

-- ============================================================================
-- DOCUMENT CHUNKS
-- Chunks of documents for RAG semantic search.
-- ============================================================================
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    property_id UUID REFERENCES properties(id) ON DELETE SET NULL,

    -- Content
    chunk_text TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,

    -- Classification
    chunk_type TEXT,
    section_title TEXT,

    -- Position
    page_start INTEGER,
    page_end INTEGER,
    char_start INTEGER,
    char_end INTEGER,

    -- Vector Reference
    pinecone_id TEXT,
    embedding_model TEXT,
    embedded_at TIMESTAMP WITH TIME ZONE,

    -- Metadata for Filtering (denormalized)
    document_type TEXT,
    policy_type TEXT,
    carrier TEXT,
    effective_date DATE,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_chunks_document ON document_chunks(document_id);
CREATE INDEX idx_chunks_property ON document_chunks(property_id);
CREATE INDEX idx_chunks_type ON document_chunks(chunk_type);
CREATE INDEX idx_chunks_pinecone ON document_chunks(pinecone_id);

-- ============================================================================
-- INSURANCE PROGRAMS
-- Yearly insurance "program" for a property — a collection of policies.
-- ============================================================================
CREATE TABLE insurance_programs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,

    -- Period
    program_year INTEGER NOT NULL,
    effective_date DATE,
    expiration_date DATE,

    -- Aggregated Values (computed from policies)
    total_premium NUMERIC(15, 2),
    total_insured_value NUMERIC(15, 2),
    total_liability_limit NUMERIC(15, 2),

    -- Status
    status TEXT DEFAULT 'active',

    -- Data Quality
    completeness_pct FLOAT DEFAULT 0,
    policies_count INTEGER DEFAULT 0,
    documents_count INTEGER DEFAULT 0,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,

    -- Constraints
    CONSTRAINT uq_program_year UNIQUE (property_id, program_year)
);

CREATE INDEX idx_programs_property ON insurance_programs(property_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_programs_status ON insurance_programs(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_programs_expiration ON insurance_programs(expiration_date) WHERE deleted_at IS NULL;

-- ============================================================================
-- POLICIES
-- Insurance policies.
-- ============================================================================
CREATE TABLE policies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    program_id UUID NOT NULL REFERENCES insurance_programs(id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    carrier_id UUID REFERENCES carriers(id) ON DELETE SET NULL,
    named_insured_id UUID REFERENCES insured_entities(id) ON DELETE SET NULL,

    -- Policy Identity
    policy_type TEXT NOT NULL,
    policy_number TEXT,
    carrier_name TEXT,

    -- Dates
    effective_date DATE,
    expiration_date DATE,

    -- Premium
    premium NUMERIC(15, 2),
    taxes NUMERIC(15, 2),
    fees NUMERIC(15, 2),
    total_cost NUMERIC(15, 2),

    -- Policy Characteristics
    admitted BOOLEAN,
    form_type TEXT,
    policy_form TEXT,

    -- Named Insured
    named_insured_text TEXT,

    -- Extraction Quality
    extraction_confidence FLOAT,
    source_pages INTEGER[],
    needs_review BOOLEAN DEFAULT FALSE,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_policies_program ON policies(program_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_policies_type ON policies(policy_type) WHERE deleted_at IS NULL;
CREATE INDEX idx_policies_carrier ON policies(carrier_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_policies_expiration ON policies(expiration_date) WHERE deleted_at IS NULL;

-- ============================================================================
-- COVERAGES
-- Specific coverages within a policy.
-- ============================================================================
CREATE TABLE coverages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    policy_id UUID NOT NULL REFERENCES policies(id) ON DELETE CASCADE,
    source_document_id UUID REFERENCES documents(id) ON DELETE SET NULL,

    -- Coverage Identity
    coverage_name TEXT NOT NULL,
    coverage_category TEXT,
    coverage_code TEXT,

    -- Limits
    limit_amount NUMERIC(15, 2),
    limit_type TEXT,
    sublimit NUMERIC(15, 2),
    sublimit_applies_to TEXT,

    -- Deductibles
    deductible_amount NUMERIC(15, 2),
    deductible_type TEXT,
    deductible_pct FLOAT,
    deductible_minimum NUMERIC(15, 2),
    deductible_maximum NUMERIC(15, 2),
    deductible_applies_to TEXT,

    -- Special Conditions
    waiting_period_hours INTEGER,
    coinsurance_pct FLOAT,
    valuation_type TEXT,
    margin_clause_pct FLOAT,

    -- Exclusions/Limitations
    exclusions_text TEXT,
    conditions_text TEXT,

    -- Provenance
    source_page INTEGER,
    extraction_confidence FLOAT,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_coverages_policy ON coverages(policy_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_coverages_name ON coverages(coverage_name) WHERE deleted_at IS NULL;
CREATE INDEX idx_coverages_category ON coverages(coverage_category) WHERE deleted_at IS NULL;

-- ============================================================================
-- ENDORSEMENTS
-- Modifications to base policies.
-- ============================================================================
CREATE TABLE endorsements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    policy_id UUID NOT NULL REFERENCES policies(id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,

    -- Endorsement Identity
    endorsement_number TEXT,
    endorsement_name TEXT,
    endorsement_type TEXT,

    -- Dates
    effective_date DATE,

    -- Content
    description TEXT,
    full_text TEXT,

    -- Impact
    affects_coverage TEXT,
    adds_exclusion BOOLEAN DEFAULT FALSE,
    adds_coverage BOOLEAN DEFAULT FALSE,
    modifies_limit BOOLEAN DEFAULT FALSE,
    modifies_deductible BOOLEAN DEFAULT FALSE,

    -- Provenance
    source_page INTEGER,
    extraction_confidence FLOAT,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_endorsements_policy ON endorsements(policy_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_endorsements_type ON endorsements(endorsement_type) WHERE deleted_at IS NULL;

-- ============================================================================
-- CERTIFICATES
-- Certificates of Insurance (COIs) and Evidence of Property (EOPs).
-- ============================================================================
CREATE TABLE certificates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    program_id UUID NOT NULL REFERENCES insurance_programs(id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    lender_id UUID REFERENCES lenders(id) ON DELETE SET NULL,

    -- Certificate Identity
    certificate_type TEXT NOT NULL,
    certificate_number TEXT,

    -- Who It's For
    holder_name TEXT,
    holder_type TEXT,

    -- Coverage Summary
    property_limit NUMERIC(15, 2),
    gl_each_occurrence NUMERIC(15, 2),
    gl_general_aggregate NUMERIC(15, 2),
    gl_products_completed NUMERIC(15, 2),
    gl_personal_advertising NUMERIC(15, 2),
    gl_damage_to_rented NUMERIC(15, 2),
    gl_medical_expense NUMERIC(15, 2),
    umbrella_limit NUMERIC(15, 2),
    umbrella_deductible NUMERIC(15, 2),
    auto_combined_single NUMERIC(15, 2),
    workers_comp_each_accident NUMERIC(15, 2),

    -- Dates
    effective_date DATE,
    expiration_date DATE,
    issue_date DATE,

    -- Lender-Specific
    loan_number TEXT,
    mortgagee_clause TEXT,
    loss_payee_clause TEXT,

    -- Provenance
    extraction_confidence FLOAT,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_certificates_program ON certificates(program_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_certificates_type ON certificates(certificate_type) WHERE deleted_at IS NULL;
CREATE INDEX idx_certificates_lender ON certificates(lender_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_certificates_expiration ON certificates(expiration_date) WHERE deleted_at IS NULL;

-- ============================================================================
-- FINANCIALS
-- Invoices, quotes, and payments.
-- ============================================================================
CREATE TABLE financials (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    program_id UUID NOT NULL REFERENCES insurance_programs(id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,

    -- Record Type
    record_type TEXT NOT NULL,

    -- Line Items
    base_premium NUMERIC(15, 2),
    taxes NUMERIC(15, 2),
    fees NUMERIC(15, 2),
    broker_commission NUMERIC(15, 2),
    surplus_lines_tax NUMERIC(15, 2),
    stamping_fee NUMERIC(15, 2),
    policy_fee NUMERIC(15, 2),
    total NUMERIC(15, 2),

    -- Dates
    invoice_date DATE,
    due_date DATE,
    paid_date DATE,

    -- Payment Details
    payment_method TEXT,
    payment_reference TEXT,

    -- Status
    status TEXT DEFAULT 'pending',

    -- Provenance
    extraction_confidence FLOAT,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_financials_program ON financials(program_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_financials_type ON financials(record_type) WHERE deleted_at IS NULL;
CREATE INDEX idx_financials_status ON financials(status) WHERE deleted_at IS NULL;

-- ============================================================================
-- CLAIMS
-- Claims history from loss runs.
-- ============================================================================
CREATE TABLE claims (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    policy_id UUID REFERENCES policies(id) ON DELETE SET NULL,
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,

    -- Claim Identity
    claim_number TEXT,
    claim_type TEXT,

    -- Dates
    date_of_loss DATE,
    date_reported DATE,
    date_closed DATE,

    -- Description
    description TEXT,
    cause_of_loss TEXT,
    location_description TEXT,

    -- Financials
    amount_paid NUMERIC(15, 2),
    amount_reserved NUMERIC(15, 2),
    amount_incurred NUMERIC(15, 2),
    deductible_applied NUMERIC(15, 2),
    subrogation_amount NUMERIC(15, 2),

    -- Status
    status TEXT,

    -- Claimant
    claimant_name TEXT,
    claimant_type TEXT,

    -- Provenance
    extraction_confidence FLOAT,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_claims_property ON claims(property_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_claims_policy ON claims(policy_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_claims_status ON claims(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_claims_date ON claims(date_of_loss) WHERE deleted_at IS NULL;

-- ============================================================================
-- VALUATIONS
-- Property valuations from SOVs and appraisals.
-- ============================================================================
CREATE TABLE valuations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    building_id UUID REFERENCES buildings(id) ON DELETE SET NULL,
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,

    -- Valuation Context
    valuation_date DATE,
    valuation_method TEXT,
    valuation_source TEXT,

    -- Values
    building_value NUMERIC(15, 2),
    contents_value NUMERIC(15, 2),
    business_income_value NUMERIC(15, 2),
    rental_income_value NUMERIC(15, 2),
    extra_expense_value NUMERIC(15, 2),
    total_insured_value NUMERIC(15, 2),

    -- Supporting Data
    price_per_sqft NUMERIC(10, 2),
    sq_ft_used INTEGER,

    -- Provenance
    extraction_confidence FLOAT,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_valuations_property ON valuations(property_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_valuations_date ON valuations(valuation_date) WHERE deleted_at IS NULL;

-- ============================================================================
-- LENDER REQUIREMENTS
-- Specific requirements for a loan.
-- ============================================================================
CREATE TABLE lender_requirements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    lender_id UUID REFERENCES lenders(id) ON DELETE SET NULL,

    -- Loan Details
    loan_number TEXT,
    loan_amount NUMERIC(15, 2),
    maturity_date DATE,

    -- Requirements
    min_property_limit NUMERIC(15, 2),
    min_gl_limit NUMERIC(15, 2),
    min_umbrella_limit NUMERIC(15, 2),
    max_deductible_amount NUMERIC(15, 2),
    max_deductible_pct FLOAT,
    requires_flood BOOLEAN DEFAULT FALSE,
    requires_earthquake BOOLEAN DEFAULT FALSE,
    requires_terrorism BOOLEAN DEFAULT FALSE,
    additional_requirements TEXT,

    -- Compliance Status (computed)
    compliance_status TEXT,
    compliance_checked_at TIMESTAMP WITH TIME ZONE,
    compliance_issues JSONB,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_lender_req_property ON lender_requirements(property_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_lender_req_status ON lender_requirements(compliance_status) WHERE deleted_at IS NULL;

-- ============================================================================
-- COVERAGE GAPS
-- Detected coverage gaps and issues.
-- ============================================================================
CREATE TABLE coverage_gaps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    property_id UUID NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    program_id UUID REFERENCES insurance_programs(id) ON DELETE SET NULL,
    policy_id UUID REFERENCES policies(id) ON DELETE SET NULL,

    -- Gap Details
    gap_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,

    -- Specifics
    coverage_name TEXT,
    current_value TEXT,
    recommended_value TEXT,
    gap_amount NUMERIC(15, 2),

    -- Status
    status TEXT DEFAULT 'open',
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by UUID,
    resolution_notes TEXT,

    -- Detection
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    detection_method TEXT,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_gaps_property ON coverage_gaps(property_id);
CREATE INDEX idx_gaps_status ON coverage_gaps(status);
CREATE INDEX idx_gaps_severity ON coverage_gaps(severity);
CREATE INDEX idx_gaps_type ON coverage_gaps(gap_type);

-- ============================================================================
-- EXTRACTED FACTS
-- Raw extracted facts before normalization. Audit trail for extraction.
-- ============================================================================
CREATE TABLE extracted_facts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,

    -- What Was Extracted
    fact_type TEXT NOT NULL,
    field_name TEXT NOT NULL,
    extracted_value TEXT,
    normalized_value TEXT,
    data_type TEXT,

    -- Confidence & Source
    confidence FLOAT NOT NULL,
    source_page INTEGER,
    source_text TEXT,
    bounding_box JSONB,

    -- Status
    status TEXT DEFAULT 'auto_accepted',
    reviewed_by UUID,
    reviewed_at TIMESTAMP WITH TIME ZONE,

    -- Where It Went
    target_table TEXT,
    target_record_id UUID,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_facts_document ON extracted_facts(document_id);
CREATE INDEX idx_facts_type ON extracted_facts(fact_type);
CREATE INDEX idx_facts_status ON extracted_facts(status);
CREATE INDEX idx_facts_confidence ON extracted_facts(confidence);

-- ============================================================================
-- UPDATED_AT TRIGGER FUNCTION
-- Automatically updates the updated_at column on row modification.
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to all tables with updated_at column
CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_properties_updated_at BEFORE UPDATE ON properties FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_buildings_updated_at BEFORE UPDATE ON buildings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_carriers_updated_at BEFORE UPDATE ON carriers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_lenders_updated_at BEFORE UPDATE ON lenders FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_insured_entities_updated_at BEFORE UPDATE ON insured_entities FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_document_chunks_updated_at BEFORE UPDATE ON document_chunks FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_insurance_programs_updated_at BEFORE UPDATE ON insurance_programs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_policies_updated_at BEFORE UPDATE ON policies FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_coverages_updated_at BEFORE UPDATE ON coverages FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_endorsements_updated_at BEFORE UPDATE ON endorsements FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_certificates_updated_at BEFORE UPDATE ON certificates FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_financials_updated_at BEFORE UPDATE ON financials FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_claims_updated_at BEFORE UPDATE ON claims FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_valuations_updated_at BEFORE UPDATE ON valuations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_lender_requirements_updated_at BEFORE UPDATE ON lender_requirements FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_coverage_gaps_updated_at BEFORE UPDATE ON coverage_gaps FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- Enable RLS on all tables and create policies
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE properties ENABLE ROW LEVEL SECURITY;
ALTER TABLE buildings ENABLE ROW LEVEL SECURITY;
ALTER TABLE carriers ENABLE ROW LEVEL SECURITY;
ALTER TABLE lenders ENABLE ROW LEVEL SECURITY;
ALTER TABLE insured_entities ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE insurance_programs ENABLE ROW LEVEL SECURITY;
ALTER TABLE policies ENABLE ROW LEVEL SECURITY;
ALTER TABLE coverages ENABLE ROW LEVEL SECURITY;
ALTER TABLE endorsements ENABLE ROW LEVEL SECURITY;
ALTER TABLE certificates ENABLE ROW LEVEL SECURITY;
ALTER TABLE financials ENABLE ROW LEVEL SECURITY;
ALTER TABLE claims ENABLE ROW LEVEL SECURITY;
ALTER TABLE valuations ENABLE ROW LEVEL SECURITY;
ALTER TABLE lender_requirements ENABLE ROW LEVEL SECURITY;
ALTER TABLE coverage_gaps ENABLE ROW LEVEL SECURITY;
ALTER TABLE extracted_facts ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- RLS POLICIES FOR SERVICE ROLE (Backend API)
-- The service role bypasses RLS, but we create explicit policies for clarity
-- These policies allow the backend (using service_role key) full access
-- ============================================================================

-- Organizations: Service role has full access
CREATE POLICY "Service role has full access to organizations"
    ON organizations FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- Properties: Service role has full access
CREATE POLICY "Service role has full access to properties"
    ON properties FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- Buildings: Service role has full access
CREATE POLICY "Service role has full access to buildings"
    ON buildings FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- Carriers: Service role has full access (carriers are shared/public data)
CREATE POLICY "Service role has full access to carriers"
    ON carriers FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- Lenders: Service role has full access (lenders are shared/public data)
CREATE POLICY "Service role has full access to lenders"
    ON lenders FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- Insured Entities: Service role has full access
CREATE POLICY "Service role has full access to insured_entities"
    ON insured_entities FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- Documents: Service role has full access
CREATE POLICY "Service role has full access to documents"
    ON documents FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- Document Chunks: Service role has full access
CREATE POLICY "Service role has full access to document_chunks"
    ON document_chunks FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- Insurance Programs: Service role has full access
CREATE POLICY "Service role has full access to insurance_programs"
    ON insurance_programs FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- Policies: Service role has full access
CREATE POLICY "Service role has full access to policies"
    ON policies FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- Coverages: Service role has full access
CREATE POLICY "Service role has full access to coverages"
    ON coverages FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- Endorsements: Service role has full access
CREATE POLICY "Service role has full access to endorsements"
    ON endorsements FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- Certificates: Service role has full access
CREATE POLICY "Service role has full access to certificates"
    ON certificates FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- Financials: Service role has full access
CREATE POLICY "Service role has full access to financials"
    ON financials FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- Claims: Service role has full access
CREATE POLICY "Service role has full access to claims"
    ON claims FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- Valuations: Service role has full access
CREATE POLICY "Service role has full access to valuations"
    ON valuations FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- Lender Requirements: Service role has full access
CREATE POLICY "Service role has full access to lender_requirements"
    ON lender_requirements FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- Coverage Gaps: Service role has full access
CREATE POLICY "Service role has full access to coverage_gaps"
    ON coverage_gaps FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- Extracted Facts: Service role has full access
CREATE POLICY "Service role has full access to extracted_facts"
    ON extracted_facts FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- ============================================================================
-- RLS POLICIES FOR AUTHENTICATED USERS (Future: when adding user auth)
-- These policies restrict access based on organization membership
-- Uncomment and customize when implementing user authentication
-- ============================================================================

/*
-- Example: Users can only see their organization's properties
CREATE POLICY "Users can view own organization properties"
    ON properties FOR SELECT
    USING (
        organization_id IN (
            SELECT organization_id FROM user_organizations
            WHERE user_id = auth.uid()
        )
    );

-- Example: Users can only insert to their organization
CREATE POLICY "Users can insert to own organization"
    ON properties FOR INSERT
    WITH CHECK (
        organization_id IN (
            SELECT organization_id FROM user_organizations
            WHERE user_id = auth.uid()
        )
    );
*/

-- ============================================================================
-- PUBLIC READ ACCESS FOR REFERENCE TABLES
-- Carriers and Lenders are reference data - allow authenticated users to read
-- ============================================================================

CREATE POLICY "Authenticated users can read carriers"
    ON carriers FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "Authenticated users can read lenders"
    ON lenders FOR SELECT
    USING (auth.role() = 'authenticated');

-- ============================================================================
-- SEED DATA: Default Organization
-- ============================================================================
INSERT INTO organizations (name, slug, plan)
VALUES ('Default Organization', 'default', 'free');

-- ============================================================================
-- DONE!
-- ============================================================================
-- Migration complete. Tables created:
-- 1.  organizations
-- 2.  properties
-- 3.  buildings
-- 4.  carriers
-- 5.  lenders
-- 6.  insured_entities
-- 7.  documents
-- 8.  document_chunks
-- 9.  insurance_programs
-- 10. policies
-- 11. coverages
-- 12. endorsements
-- 13. certificates
-- 14. financials
-- 15. claims
-- 16. valuations
-- 17. lender_requirements
-- 18. coverage_gaps
-- 19. extracted_facts
--
-- RLS enabled on all tables with service_role full access policies.
-- Reference tables (carriers, lenders) readable by authenticated users.
