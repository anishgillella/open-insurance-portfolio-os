-- Open Insurance Schema Rollback
-- Run this to completely remove the schema
-- WARNING: This will delete ALL data!

-- Drop triggers first
DROP TRIGGER IF EXISTS update_organizations_updated_at ON organizations;
DROP TRIGGER IF EXISTS update_properties_updated_at ON properties;
DROP TRIGGER IF EXISTS update_buildings_updated_at ON buildings;
DROP TRIGGER IF EXISTS update_carriers_updated_at ON carriers;
DROP TRIGGER IF EXISTS update_lenders_updated_at ON lenders;
DROP TRIGGER IF EXISTS update_insured_entities_updated_at ON insured_entities;
DROP TRIGGER IF EXISTS update_documents_updated_at ON documents;
DROP TRIGGER IF EXISTS update_document_chunks_updated_at ON document_chunks;
DROP TRIGGER IF EXISTS update_insurance_programs_updated_at ON insurance_programs;
DROP TRIGGER IF EXISTS update_policies_updated_at ON policies;
DROP TRIGGER IF EXISTS update_coverages_updated_at ON coverages;
DROP TRIGGER IF EXISTS update_endorsements_updated_at ON endorsements;
DROP TRIGGER IF EXISTS update_certificates_updated_at ON certificates;
DROP TRIGGER IF EXISTS update_financials_updated_at ON financials;
DROP TRIGGER IF EXISTS update_claims_updated_at ON claims;
DROP TRIGGER IF EXISTS update_valuations_updated_at ON valuations;
DROP TRIGGER IF EXISTS update_lender_requirements_updated_at ON lender_requirements;
DROP TRIGGER IF EXISTS update_coverage_gaps_updated_at ON coverage_gaps;

-- Drop function
DROP FUNCTION IF EXISTS update_updated_at_column();

-- Drop tables in reverse dependency order
DROP TABLE IF EXISTS extracted_facts CASCADE;
DROP TABLE IF EXISTS coverage_gaps CASCADE;
DROP TABLE IF EXISTS lender_requirements CASCADE;
DROP TABLE IF EXISTS valuations CASCADE;
DROP TABLE IF EXISTS claims CASCADE;
DROP TABLE IF EXISTS financials CASCADE;
DROP TABLE IF EXISTS certificates CASCADE;
DROP TABLE IF EXISTS endorsements CASCADE;
DROP TABLE IF EXISTS coverages CASCADE;
DROP TABLE IF EXISTS policies CASCADE;
DROP TABLE IF EXISTS insurance_programs CASCADE;
DROP TABLE IF EXISTS document_chunks CASCADE;
DROP TABLE IF EXISTS documents CASCADE;
DROP TABLE IF EXISTS insured_entities CASCADE;
DROP TABLE IF EXISTS lenders CASCADE;
DROP TABLE IF EXISTS carriers CASCADE;
DROP TABLE IF EXISTS buildings CASCADE;
DROP TABLE IF EXISTS properties CASCADE;
DROP TABLE IF EXISTS organizations CASCADE;

-- Done!
