-- Align Database Schema with Extraction Models
-- Version: 002
-- Description: Adds missing fields to claims and certificates tables to capture
--              all data extracted from insurance documents
--
-- Run this after 001_initial_schema.sql

-- ============================================================================
-- CLAIMS TABLE ENHANCEMENTS
-- Add detailed financial breakdowns and additional claim information
-- to match the ClaimEntry Pydantic extraction schema
-- ============================================================================

-- Location information
ALTER TABLE claims ADD COLUMN IF NOT EXISTS location_address TEXT;
ALTER TABLE claims ADD COLUMN IF NOT EXISTS location_name TEXT;

-- Carrier and policy reference (for cross-referencing from loss runs)
ALTER TABLE claims ADD COLUMN IF NOT EXISTS carrier_name TEXT;

-- Detailed Paid Amounts (breaking down amount_paid)
ALTER TABLE claims ADD COLUMN IF NOT EXISTS paid_loss NUMERIC(15, 2);
ALTER TABLE claims ADD COLUMN IF NOT EXISTS paid_expense NUMERIC(15, 2);
ALTER TABLE claims ADD COLUMN IF NOT EXISTS paid_medical NUMERIC(15, 2);
ALTER TABLE claims ADD COLUMN IF NOT EXISTS paid_indemnity NUMERIC(15, 2);
ALTER TABLE claims ADD COLUMN IF NOT EXISTS total_paid NUMERIC(15, 2);

-- Detailed Reserve Amounts (breaking down amount_reserved)
ALTER TABLE claims ADD COLUMN IF NOT EXISTS reserve_loss NUMERIC(15, 2);
ALTER TABLE claims ADD COLUMN IF NOT EXISTS reserve_expense NUMERIC(15, 2);
ALTER TABLE claims ADD COLUMN IF NOT EXISTS reserve_medical NUMERIC(15, 2);
ALTER TABLE claims ADD COLUMN IF NOT EXISTS reserve_indemnity NUMERIC(15, 2);
ALTER TABLE claims ADD COLUMN IF NOT EXISTS total_reserve NUMERIC(15, 2);

-- Detailed Incurred Amounts (paid + reserve)
ALTER TABLE claims ADD COLUMN IF NOT EXISTS incurred_loss NUMERIC(15, 2);
ALTER TABLE claims ADD COLUMN IF NOT EXISTS incurred_expense NUMERIC(15, 2);
ALTER TABLE claims ADD COLUMN IF NOT EXISTS total_incurred NUMERIC(15, 2);

-- Recovery Information
ALTER TABLE claims ADD COLUMN IF NOT EXISTS deductible_recovered NUMERIC(15, 2);
ALTER TABLE claims ADD COLUMN IF NOT EXISTS salvage_amount NUMERIC(15, 2);
ALTER TABLE claims ADD COLUMN IF NOT EXISTS net_incurred NUMERIC(15, 2);

-- Additional Claim Details
ALTER TABLE claims ADD COLUMN IF NOT EXISTS litigation_status TEXT;
ALTER TABLE claims ADD COLUMN IF NOT EXISTS injury_description TEXT;
ALTER TABLE claims ADD COLUMN IF NOT EXISTS notes TEXT;

-- Add index for carrier name lookups
CREATE INDEX IF NOT EXISTS idx_claims_carrier ON claims(carrier_name) WHERE deleted_at IS NULL;

-- ============================================================================
-- CERTIFICATES TABLE ENHANCEMENTS
-- Add producer info, detailed policy references, and additional coverage fields
-- to match the COIExtraction Pydantic schema
-- ============================================================================

-- Certificate revisions
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS revision_number TEXT;

-- Producer/Broker Information
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS producer_name TEXT;
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS producer_address TEXT;
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS producer_phone TEXT;
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS producer_email TEXT;
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS producer_reference TEXT;

-- Insured Information (stored on certificate)
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS insured_name TEXT;
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS insured_address TEXT;

-- Certificate holder address
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS holder_address TEXT;

-- Insurers mapping (A, B, C, D, E, F)
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS insurers JSONB DEFAULT '{}';

-- Detailed policy references
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS policies JSONB DEFAULT '[]';

-- GL Coverage Details
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS gl_coverage_form TEXT;
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS gl_aggregate_limit_applies_per TEXT;

-- Auto Coverage Details
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS auto_bodily_injury_per_person NUMERIC(15, 2);
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS auto_bodily_injury_per_accident NUMERIC(15, 2);
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS auto_property_damage NUMERIC(15, 2);
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS auto_types TEXT[];

-- Umbrella Coverage Details
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS umbrella_aggregate NUMERIC(15, 2);
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS umbrella_retention NUMERIC(15, 2);
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS umbrella_coverage_form TEXT;

-- Workers Compensation Details
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS workers_comp_per_statute BOOLEAN;
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS workers_comp_other BOOLEAN;
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS workers_comp_disease_ea_employee NUMERIC(15, 2);
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS workers_comp_disease_policy_limit NUMERIC(15, 2);
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS workers_comp_excluded_partners BOOLEAN;

-- Operations Description
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS description_of_operations TEXT;

-- Additional Insureds
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS additional_insureds TEXT[];
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS subrogation_waiver_applies BOOLEAN DEFAULT FALSE;

-- Cancellation Terms
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS cancellation_notice_days INTEGER;
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS cancellation_terms TEXT;

-- Authorized Representative
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS authorized_representative TEXT;

-- ============================================================================
-- COVERAGES TABLE ENHANCEMENTS
-- Add coverage_code field (already present in schema but confirm)
-- ============================================================================

-- Ensure coverage_code column exists (it should from initial schema)
ALTER TABLE coverages ADD COLUMN IF NOT EXISTS coverage_code TEXT;

-- ============================================================================
-- Add useful indexes for new columns
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_certificates_producer ON certificates(producer_name) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_claims_litigation ON claims(litigation_status) WHERE deleted_at IS NULL AND litigation_status IS NOT NULL;

-- ============================================================================
-- Comments for documentation
-- ============================================================================

COMMENT ON COLUMN claims.location_address IS 'Street address where loss occurred';
COMMENT ON COLUMN claims.location_name IS 'Property/location name where loss occurred';
COMMENT ON COLUMN claims.paid_loss IS 'Total amount paid for the loss/damages (property damage, etc.)';
COMMENT ON COLUMN claims.paid_expense IS 'Paid allocated loss adjustment expense (ALAE)';
COMMENT ON COLUMN claims.paid_medical IS 'Paid medical expenses (workers comp/bodily injury)';
COMMENT ON COLUMN claims.paid_indemnity IS 'Paid indemnity amounts (workers comp)';
COMMENT ON COLUMN claims.total_paid IS 'Total paid = paid_loss + paid_expense + paid_medical + paid_indemnity';
COMMENT ON COLUMN claims.reserve_loss IS 'Outstanding reserve for loss/damages';
COMMENT ON COLUMN claims.reserve_expense IS 'Outstanding reserve for expenses';
COMMENT ON COLUMN claims.reserve_medical IS 'Outstanding reserve for medical (workers comp)';
COMMENT ON COLUMN claims.reserve_indemnity IS 'Outstanding reserve for indemnity (workers comp)';
COMMENT ON COLUMN claims.total_reserve IS 'Total outstanding reserve';
COMMENT ON COLUMN claims.incurred_loss IS 'Incurred loss = paid_loss + reserve_loss';
COMMENT ON COLUMN claims.incurred_expense IS 'Incurred expense = paid_expense + reserve_expense';
COMMENT ON COLUMN claims.total_incurred IS 'Total incurred = total_paid + total_reserve';
COMMENT ON COLUMN claims.net_incurred IS 'Net incurred = total_incurred - subrogation - salvage - deductible_recovered';
COMMENT ON COLUMN claims.litigation_status IS 'Litigation status if claim is in legal proceedings';
COMMENT ON COLUMN claims.injury_description IS 'Description of injuries for bodily injury claims';

COMMENT ON COLUMN certificates.insurers IS 'JSONB map of insurer letters (A-F) to carrier info {name, naic}';
COMMENT ON COLUMN certificates.policies IS 'JSONB array of policy references with detailed coverage info';
COMMENT ON COLUMN certificates.description_of_operations IS 'Description of operations/locations covered text from certificate';
COMMENT ON COLUMN certificates.additional_insureds IS 'Array of additional insured names listed on certificate';

-- ============================================================================
-- DONE!
-- ============================================================================
-- Migration adds comprehensive claim financial tracking and certificate details
-- to align with the Pydantic extraction schemas (ClaimEntry, COIExtraction)
