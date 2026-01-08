/**
 * API Client for Open Insurance Backend
 * Base URL: http://localhost:8000/v1
 */

import type { Gap, GapAnalysis, RenewalAlert } from '@/types/api';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/v1';
const DEFAULT_ORG_ID = '00000000-0000-0000-0000-000000000001';

export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public data?: unknown
  ) {
    super(`API Error: ${status} ${statusText}`);
    this.name = 'ApiError';
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let data;
    try {
      data = await response.json();
    } catch {
      data = null;
    }
    throw new ApiError(response.status, response.statusText, data);
  }

  // Handle empty responses
  const text = await response.text();
  if (!text) {
    return {} as T;
  }

  return JSON.parse(text) as T;
}

// ============ GENERIC FETCH HELPERS ============

export async function apiGet<T>(endpoint: string, params?: Record<string, string | undefined>): Promise<T> {
  const url = new URL(`${API_BASE_URL}${endpoint}`);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        url.searchParams.append(key, value);
      }
    });
  }

  const response = await fetch(url.toString(), {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  return handleResponse<T>(response);
}

export async function apiPost<T>(endpoint: string, body?: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  return handleResponse<T>(response);
}

export async function apiPostFormData<T>(endpoint: string, formData: FormData): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: 'POST',
    body: formData,
  });

  return handleResponse<T>(response);
}

export async function apiDelete(endpoint: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    let data;
    try {
      data = await response.json();
    } catch {
      data = null;
    }
    throw new ApiError(response.status, response.statusText, data);
  }
  // DELETE returns 204 No Content, so don't try to parse response
}

export async function apiPatch<T>(endpoint: string, body?: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  return handleResponse<T>(response);
}

// ============ DASHBOARD API ============

// Nested structures matching backend response
export interface PortfolioStats {
  total_properties: number;
  total_buildings: number;
  total_units: number;
  total_insured_value: number | string;
  total_annual_premium: number | string;
}

export interface ExpirationStats {
  expiring_30_days: number;
  expiring_60_days: number;
  expiring_90_days: number;
  next_expiration: {
    property_name: string;
    policy_type: string;
    expiration_date: string;
    days_until_expiration: number;
  } | null;
}

export interface GapStats {
  total_open_gaps: number;
  critical_gaps: number;
  warning_gaps: number;
  info_gaps: number;
  properties_with_gaps: number;
}

export interface ComplianceStats {
  compliant_properties: number;
  non_compliant_properties: number;
  properties_without_requirements: number;
}

export interface CompletenessStats {
  average_completeness: number;
  fully_complete_properties: number;
  properties_missing_required_docs: number;
}

export interface HealthScoreStats {
  portfolio_average: number;
  trend: string;
  trend_delta: number;
}

export interface DashboardSummary {
  portfolio_stats: PortfolioStats;
  expiration_stats: ExpirationStats;
  gap_stats: GapStats;
  compliance_stats: ComplianceStats;
  completeness_stats: CompletenessStats;
  health_score: HealthScoreStats;
  generated_at: string;
}

export interface ExpirationItem {
  property_id: string;
  property_name: string;
  policy_id: string;
  policy_number: string;
  expiration_date: string;
  days_until_expiration: number;
  premium: number;
  coverage_type: string;
}

export interface DashboardAlert {
  id: string;
  type: 'gap' | 'expiration' | 'compliance' | 'document';
  severity: 'critical' | 'warning' | 'info';
  title: string;
  description: string;
  property_id?: string;
  property_name?: string;
  created_at: string;
  acknowledged: boolean;
}

export const dashboardApi = {
  getSummary: (orgId = DEFAULT_ORG_ID) =>
    apiGet<DashboardSummary>('/dashboard/summary', { organization_id: orgId }),

  getExpirations: (orgId = DEFAULT_ORG_ID, days = '90') =>
    apiGet<ExpirationItem[]>('/dashboard/expirations', { organization_id: orgId, days }),

  getAlerts: (orgId = DEFAULT_ORG_ID, severity?: string) =>
    apiGet<DashboardAlert[]>('/dashboard/alerts', { organization_id: orgId, ...(severity && { severity }) }),
};

// ============ PROPERTIES API ============

export interface PropertyAddress {
  street: string;
  city: string;
  state: string;
  zip: string;
}

// Property for list view (flat structure from /properties)
export interface Property {
  id: string;
  name: string;
  address: PropertyAddress;
  latitude?: number;
  longitude?: number;
  property_type: string | null;
  total_units: number | null;
  total_buildings: number;
  year_built: number | null;
  total_insured_value: number | string;
  total_premium: number | string;
  health_score: number;
  health_grade: 'A' | 'B' | 'C' | 'D' | 'F';
  gaps_count: {
    critical: number;
    warning: number;
    info: number;
  };
  next_expiration: string | null;
  days_until_expiration: number | null;
  compliance_status: 'compliant' | 'non_compliant' | 'no_requirements';
  completeness_percentage: number;
  coverage_types?: string[];
  created_at: string;
  updated_at: string;
}

// Insurance summary nested in PropertyDetail
export interface InsuranceSummary {
  total_insured_value: number | string;
  total_annual_premium: number | string;
  policy_count: number;
  next_expiration: string | null;
  days_until_expiration: number | null;
  coverage_types: string[];
}

// Health score nested in PropertyDetail
export interface HealthScoreDetail {
  score: number;
  grade: 'A' | 'B' | 'C' | 'D' | 'F';
  components: {
    coverage_adequacy: number;
    policy_currency: number;
    deductible_risk: number;
    coverage_breadth: number;
    lender_compliance: number;
    documentation_quality: number;
  };
  trend: string;
  calculated_at: string | null;
}

// Gaps summary nested in PropertyDetail
export interface GapsSummary {
  total_open: number;
  critical: number;
  warning: number;
  info: number;
}

// Document checklist item for completeness tracking
export interface DocumentChecklistItem {
  document_type: string;
  display_name: string;
  description: string;
  is_required: boolean;
  is_present: boolean;
  fields_provided: string[];
  uploaded_file: string | null;
}

// Property detail from /properties/{id} (nested structure)
export interface PropertyDetail {
  id: string;
  name: string;
  external_id: string | null;
  address: PropertyAddress;
  property_type: string | null;
  year_built: number | null;
  construction_type: string | null;
  total_units: number | null;
  total_buildings: number;
  total_sqft: number | null;
  has_sprinklers: boolean | null;
  protection_class: string | null;
  flood_zone: string | null;
  earthquake_zone: string | null;
  wind_zone: string | null;
  buildings: Building[];
  insurance_summary: InsuranceSummary;
  health_score: HealthScoreDetail;
  gaps_summary: GapsSummary;
  compliance_summary: {
    status: string;
    lender_name: string | null;
    issues_count: number;
  };
  completeness: {
    percentage: number;
    required_present: number;
    required_total: number;
    optional_present: number;
    optional_total: number;
    checklist: DocumentChecklistItem[];
  };
  policies?: Policy[];
  documents?: DocumentSummary[];
  document_count: number;
  created_at: string;
  updated_at: string;
}

export interface Policy {
  id: string;
  policy_number: string | null;
  policy_type: string;
  carrier: string | null;
  effective_date: string | null;
  expiration_date: string | null;
  premium: number | null;
  limit: number | null;
  deductible: number | null;
  status: 'active' | 'expired' | 'pending';
}

export interface Building {
  id: string;
  name: string;
  address: string;
  year_built: number;
  square_footage: number;
  construction_type: string;
  occupancy_type: string;
  insured_value: number;
}

export interface DocumentSummary {
  id: string;
  file_name: string;
  document_type: string;
  upload_status: string;
  created_at: string;
}

// ============ EXTRACTED DATA TYPES ============

export interface ExtractedFieldValue {
  value: string | number | boolean | null;
  source_document_id: string;
  source_document_name: string;
  source_document_type: string | null;
  extraction_confidence: number | null;
  extracted_at: string | null;
}

export interface ExtractedFieldWithSources {
  field_name: string;
  display_name: string;
  category: string;
  values: ExtractedFieldValue[];
  consolidated_value: string | number | boolean | null;
}

export interface DocumentExtractionSummary {
  document_id: string;
  document_name: string;
  document_type: string | null;
  uploaded_at: string;
  extraction_confidence: number | null;
  extracted_fields: Record<string, string | number | boolean | null>;
}

export interface ValuationSummary {
  id: string;
  valuation_date: string | null;
  valuation_source: string | null;
  building_value: string | null;
  contents_value: string | null;
  business_income_value: string | null;
  total_insured_value: string | null;
  price_per_sqft: string | null;
  sq_ft_used: number | null;
  source_document_id: string | null;
  source_document_name: string | null;
}

export interface CoverageExtractionSummary {
  coverage_name: string;
  coverage_category: string | null;
  limit_amount: string | null;
  limit_type: string | null;
  deductible_amount: string | null;
  deductible_type: string | null;
  source_document_id: string | null;
  source_document_name: string | null;
}

export interface PolicyExtractionSummary {
  id: string;
  policy_type: string;
  policy_number: string | null;
  carrier_name: string | null;
  effective_date: string | null;
  expiration_date: string | null;
  premium: string | null;
  coverages: CoverageExtractionSummary[];
  source_document_id: string | null;
  source_document_name: string | null;
}

export interface CertificateExtractionSummary {
  id: string;
  certificate_type: string;
  certificate_number: string | null;
  producer_name: string | null;
  insured_name: string | null;
  holder_name: string | null;
  effective_date: string | null;
  expiration_date: string | null;
  gl_each_occurrence: string | null;
  gl_general_aggregate: string | null;
  property_limit: string | null;
  umbrella_limit: string | null;
  source_document_id: string | null;
  source_document_name: string | null;
}

export interface FinancialExtractionSummary {
  id: string;
  record_type: string;
  total: string | null;
  taxes: string | null;
  fees: string | null;
  invoice_date: string | null;
  due_date: string | null;
  source_document_id: string | null;
  source_document_name: string | null;
}

export interface PropertyExtractedDataResponse {
  property_id: string;
  property_name: string;
  extracted_fields: ExtractedFieldWithSources[];
  valuations: ValuationSummary[];
  policies: PolicyExtractionSummary[];
  certificates: CertificateExtractionSummary[];
  financials: FinancialExtractionSummary[];
  document_extractions: DocumentExtractionSummary[];
  total_documents: number;
  documents_with_extractions: number;
  last_extraction_at: string | null;
}

export const propertiesApi = {
  list: (orgId = DEFAULT_ORG_ID) =>
    apiGet<Property[]>('/properties', { organization_id: orgId }),

  get: (propertyId: string) =>
    apiGet<PropertyDetail>(`/properties/${propertyId}`),

  getPolicies: (propertyId: string) =>
    apiGet<Policy[]>(`/properties/${propertyId}/policies`),

  getExtractedData: (propertyId: string) =>
    apiGet<PropertyExtractedDataResponse>(`/properties/${propertyId}/extracted-data`),

  delete: (propertyId: string) =>
    apiDelete(`/properties/${propertyId}`),
};

// ============ HEALTH SCORE API ============

export interface HealthScoreComponent {
  name: string;
  score: number;
  weight: number;
  max_score: number;
  percentage: number;
  details: string;
  issues: string[];
}

export interface HealthScoreResponse {
  property_id: string;
  property_name: string;
  overall_score: number;
  grade: 'A' | 'B' | 'C' | 'D' | 'F';
  components: HealthScoreComponent[];
  recommendations: HealthRecommendation[];
  calculated_at: string;
}

export interface HealthRecommendation {
  priority: 'high' | 'medium' | 'low';
  title: string;
  description: string;
  potential_improvement: number;
  action_type: string;
}

export interface HealthScoreHistoryPoint {
  date: string;
  score: number;
  grade: 'A' | 'B' | 'C' | 'D' | 'F';
  event?: string;
}

export const healthScoreApi = {
  get: (propertyId: string) =>
    apiGet<HealthScoreResponse>(`/health-score/properties/${propertyId}`),

  getHistory: (propertyId: string) =>
    apiGet<HealthScoreHistoryPoint[]>(`/health-score/properties/${propertyId}/history`),

  recalculate: (propertyId: string) =>
    apiPost<HealthScoreResponse>(`/health-score/properties/${propertyId}/recalculate`),
};

// ============ GAPS API ============

// Re-export Gap types from types/api.ts for compatibility
export type { Gap, GapAnalysis, GapType, GapStatus, Severity } from '@/types/api';

export const gapsApi = {
  list: (orgId = DEFAULT_ORG_ID, params?: { severity?: string; status?: string; property_id?: string }) =>
    apiGet<Gap[]>('/gaps', { organization_id: orgId, ...params }),

  get: (gapId: string) =>
    apiGet<Gap>(`/gaps/${gapId}`),

  analyze: (gapId: string) =>
    apiPost<GapAnalysis>(`/gaps/${gapId}/analyze`),

  acknowledge: (gapId: string, notes?: string) =>
    apiPost<Gap>(`/gaps/${gapId}/acknowledge`, { notes }),

  resolve: (gapId: string, resolution_notes: string) =>
    apiPost<Gap>(`/gaps/${gapId}/resolve`, { resolution_notes }),

  detect: (propertyId: string) =>
    apiPost<Gap[]>('/gaps/detect', { property_id: propertyId }),
};

// ============ COMPLIANCE API ============

export interface ComplianceCheck {
  requirement: string;
  status: 'pass' | 'fail' | 'not_applicable';
  current_value?: string;
  required_value?: string;
  gap_amount?: number;
}

export interface ComplianceResult {
  property_id: string;
  property_name: string;
  template_id: string;
  template_name: string;
  lender_name: string;
  is_compliant: boolean;
  checks: ComplianceCheck[];
  last_checked: string;
}

export interface ComplianceTemplate {
  id: string;
  name: string;
  lender_name: string;
  description?: string;
  requirements: Record<string, unknown>;
}

// Backend template format (from /compliance/templates)
export interface ComplianceTemplateBackend {
  name: string;
  display_name: string;
  description: string;
}

// Batch compliance types
export interface ComplianceIssue {
  check_name: string;
  severity: string;
  message: string;
  current_value?: string;
  required_value?: string;
}

export interface ComplianceCheckBackend {
  property_id: string;
  lender_requirement_id?: string;
  lender_name?: string;
  template_name: string;
  status: string;
  is_compliant: boolean;
  issues: ComplianceIssue[];
  checked_at?: string;
}

export interface BatchComplianceItem {
  property_id: string;
  property_name: string;
  overall_status: 'compliant' | 'non_compliant' | 'partial' | 'no_requirements';
  total_issues: number;
  compliance_checks: ComplianceCheckBackend[];
}

export interface BatchComplianceResponse {
  results: BatchComplianceItem[];
  total_properties: number;
  compliant_count: number;
  non_compliant_count: number;
  no_requirements_count: number;
}

export const complianceApi = {
  getPropertyCompliance: (propertyId: string, templateId?: string) =>
    apiGet<ComplianceResult>(`/compliance/properties/${propertyId}`, templateId ? { template_id: templateId } : undefined),

  listTemplates: async (): Promise<ComplianceTemplate[]> => {
    const response = await apiGet<{ templates: ComplianceTemplateBackend[] }>('/compliance/templates');
    // Map backend format to frontend format
    return (response.templates || []).map((t) => ({
      id: t.name,
      name: t.display_name,
      lender_name: t.display_name, // Use display_name as lender_name for display
      description: t.description,
      requirements: {},
    }));
  },

  checkCompliance: (propertyId: string, templateId: string) =>
    apiPost<ComplianceResult>('/compliance/check', { property_id: propertyId, template_id: templateId }),

  // Batch endpoint - much more efficient for portfolio-wide compliance views
  batchCheckCompliance: (propertyIds: string[], createGaps = false) =>
    apiPost<BatchComplianceResponse>('/compliance/batch', { property_ids: propertyIds, create_gaps: createGaps }),
};

// ============ RENEWALS API ============

// Re-export renewal types from types/api.ts for compatibility
export type { RenewalAlert, RenewalAlertStatus } from '@/types/api';

export interface RenewalForecast {
  id: string;
  property_id: string;
  property_name: string;
  current_premium: number;
  current_expiration_date: string;
  days_until_expiration: number;
  forecast: {
    low: number;
    mid: number;
    high: number;
    low_change_percent: number;
    mid_change_percent: number;
    high_change_percent: number;
  };
  confidence: number;
  factors: Array<{
    name: string;
    impact_percent: number;
    direction: 'increase' | 'decrease' | 'neutral';
    description: string;
  }>;
  llm_analysis?: string;
  negotiation_points: string[];
  calculated_at: string;
}

export interface RenewalMilestone {
  name: string;
  target_date: string;
  days_before_expiration: number;
  status: 'completed' | 'in_progress' | 'upcoming' | 'overdue';
  action_items: string[];
  documents_ready: Record<string, boolean>;
}

// Timeline item from backend - matches TimelineItemSchema
export interface RenewalTimelineItem {
  property_id: string;
  property_name: string;
  policy_id: string;
  policy_number: string | null;
  policy_type: string;
  carrier_name: string | null;
  expiration_date: string;
  days_until_expiration: number;
  severity: 'info' | 'warning' | 'critical';
  current_premium: number | null;
  predicted_premium: number | null;
  has_forecast: boolean;
  has_active_alerts: boolean;
  alert_count: number;
}

// Timeline summary from backend - matches TimelineSummarySchema
export interface RenewalTimelineSummary {
  total_renewals: number;
  expiring_30_days: number;
  expiring_60_days: number;
  expiring_90_days: number;
  total_premium_at_risk: number;
}

// Full timeline response from backend - matches RenewalTimelineResponse
export interface RenewalTimelineResponse {
  timeline: RenewalTimelineItem[];
  summary: RenewalTimelineSummary;
}

// Legacy type kept for backwards compatibility
export interface RenewalTimeline {
  property_id: string;
  property_name: string;
  expiration_date: string;
  days_until_expiration: number;
  milestones: RenewalMilestone[];
  summary: {
    total_milestones: number;
    completed: number;
    in_progress: number;
    upcoming: number;
    overdue: number;
  };
}

export interface DocumentReadiness {
  property_id: string;
  property_name: string;
  overall_score: number;
  grade: 'A' | 'B' | 'C' | 'D' | 'F';
  documents: Array<{
    type: string;
    label: string;
    status: 'found' | 'missing' | 'stale' | 'not_applicable';
    document_id?: string;
    filename?: string;
    age_days?: number;
    verified: boolean;
    issues?: string[];
  }>;
  last_assessed: string;
}

export interface MarketContext {
  property_id: string;
  property_name: string;
  rate_trend: string;
  rate_change_percent: number;
  key_factors: string[];
  carrier_appetite: 'growing' | 'stable' | 'shrinking';
  carrier_notes: string;
  six_month_forecast: string;
  opportunities: string[];
  competitive_position: 'strong' | 'moderate' | 'weak';
  recommended_actions: string[];
  sources: string[];
  fetched_at: string;
}

// Batch forecast types
export interface BatchForecastItem {
  property_id: string;
  property_name: string;
  has_forecast: boolean;
  current_premium: number | null;
  current_expiration_date: string | null;
  days_until_expiration: number | null;
  forecast_low: number | null;
  forecast_mid: number | null;
  forecast_high: number | null;
  forecast_change_pct: number | null;
  confidence_score: number | null;
  forecast_date: string | null;
}

export interface BatchForecastResponse {
  forecasts: BatchForecastItem[];
  total_properties: number;
  properties_with_forecasts: number;
  total_premium_at_risk: number | null;
  avg_forecast_change_pct: number | null;
}

export const renewalsApi = {
  getForecast: (propertyId: string) =>
    apiGet<RenewalForecast>(`/renewals/forecast/${propertyId}`),

  generateForecast: (propertyId: string) =>
    apiPost<RenewalForecast>(`/renewals/forecast/${propertyId}`),

  // Batch endpoint - much more efficient for portfolio-wide renewal views
  batchGetForecasts: (propertyIds: string[]) =>
    apiPost<BatchForecastResponse>('/renewals/forecasts/batch', { property_ids: propertyIds }),

  getTimeline: (orgId = DEFAULT_ORG_ID, daysAhead = 90) =>
    apiGet<RenewalTimelineResponse>('/renewals/timeline', { organization_id: orgId, days_ahead: String(daysAhead) }),

  getAlerts: (orgId = DEFAULT_ORG_ID, status?: string, severity?: string) =>
    apiGet<RenewalAlert[]>('/renewals/alerts', { organization_id: orgId, ...(status && { status }), ...(severity && { severity }) }),

  acknowledgeAlert: (alertId: string) =>
    apiPost<RenewalAlert>(`/renewals/alerts/${alertId}/acknowledge`),

  resolveAlert: (alertId: string) =>
    apiPost<RenewalAlert>(`/renewals/alerts/${alertId}/resolve`),

  getReadiness: (propertyId: string) =>
    apiGet<DocumentReadiness>(`/renewals/readiness/${propertyId}`),

  getMarketContext: (propertyId: string) =>
    apiGet<MarketContext>(`/renewals/market-context/${propertyId}`),
};

// ============ DOCUMENTS API ============

export interface Document {
  id: string;
  file_name: string;
  file_url: string;
  document_type: string;
  document_subtype?: string;
  carrier?: string;
  policy_number?: string;
  effective_date?: string;
  expiration_date?: string;
  upload_status: 'pending' | 'processing' | 'completed' | 'failed';
  ocr_status?: string;
  extraction_status?: string;
  extraction_confidence?: number;
  needs_human_review: boolean;
  property_id?: string;
  property_name?: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentExtraction {
  document_id: string;
  classification: {
    document_type: string;
    document_subtype?: string;
    policy_type?: string;
    confidence: number;
    carrier_name?: string;
    policy_number?: string;
    effective_date?: string;
    expiration_date?: string;
    insured_name?: string;
  };
  extraction_data: Record<string, unknown>;
  overall_confidence: number;
}

export interface DocumentText {
  document_id: string;
  file_name: string;
  page_count: number;
  text: string;
}

export interface UploadResponse {
  document_id: string;
  file_name: string;
  status: string;
  classification?: {
    document_type: string;
    confidence: number;
  };
  extraction_summary?: string;
  errors?: string[];
}

export interface AsyncUploadResponse {
  document_id: string;
  file_name: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  message: string;
}

export interface DirectoryUploadResponse {
  directory_path: string;
  total_files: number;
  successful: number;
  failed: number;
  skipped: number;
  results: UploadResponse[];
}

export interface DocumentListResponse {
  documents: Document[];
  total: number;
}

export const documentsApi = {
  list: (orgId = DEFAULT_ORG_ID, propertyId?: string) =>
    apiGet<DocumentListResponse>('/documents', { organization_id: orgId, ...(propertyId && { property_id: propertyId }) }),

  get: (documentId: string) =>
    apiGet<Document>(`/documents/${documentId}`),

  getExtraction: (documentId: string) =>
    apiGet<DocumentExtraction>(`/documents/${documentId}/extraction`),

  getText: (documentId: string) =>
    apiGet<DocumentText>(`/documents/${documentId}/text`),

  upload: (file: File, propertyName: string, orgId = DEFAULT_ORG_ID, propertyId?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('organization_id', orgId);
    formData.append('property_name', propertyName);
    if (propertyId) {
      formData.append('property_id', propertyId);
    }
    return apiPostFormData<UploadResponse>('/documents/upload', formData);
  },

  // Async upload - returns immediately, processing happens in background
  uploadAsync: (file: File, propertyName: string, orgId = DEFAULT_ORG_ID, propertyId?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('organization_id', orgId);
    formData.append('property_name', propertyName);
    if (propertyId) {
      formData.append('property_id', propertyId);
    }
    return apiPostFormData<AsyncUploadResponse>('/documents/upload/async', formData);
  },

  uploadDirectory: (directoryPath: string, propertyName: string, orgId = DEFAULT_ORG_ID, propertyId?: string) =>
    apiPost<DirectoryUploadResponse>('/documents/ingest-directory', {
      directory_path: directoryPath,
      organization_id: orgId,
      property_name: propertyName,
      property_id: propertyId,
      force_reprocess: true,
    }),
};

// ============ CHAT API ============

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: ChatSource[];
  created_at: string;
}

export interface ChatSource {
  document_id: string;
  document_name: string;
  page: number;
  page_end?: number;
  snippet: string;
  score: number;
}

export interface ChatResponse {
  conversation_id: string;
  message_id: string;
  content: string;
  sources: ChatSource[];
  confidence: number;
  tokens_used: number;
  latency_ms: number;
}

export interface Conversation {
  conversation_id: string;
  messages: ChatMessage[];
  message_count: number;
}

export const chatApi = {
  // Non-streaming chat
  send: (message: string, conversationId?: string, propertyId?: string, documentType?: string) =>
    apiPost<ChatResponse>('/chat/', {
      message,
      conversation_id: conversationId,
      property_id: propertyId,
      document_type: documentType,
      stream: false,
    }),

  // Streaming chat - returns EventSource URL
  getStreamUrl: () => `${API_BASE_URL}/chat/`,

  // Create streaming request body
  createStreamBody: (message: string, conversationId?: string, propertyId?: string, documentType?: string) => ({
    message,
    conversation_id: conversationId,
    property_id: propertyId,
    document_type: documentType,
    stream: true,
  }),

  getConversation: (conversationId: string, limit = 50) =>
    apiGet<Conversation>(`/chat/conversations/${conversationId}`, { limit: String(limit) }),

  embedDocument: (documentId: string, forceReprocess = false) =>
    apiPost<{ document_id: string; status: string; chunks_created: number }>('/chat/embed', {
      document_id: documentId,
      force_reprocess: forceReprocess,
    }),

  embedAll: (limit = 10) =>
    apiPost<Array<{ document_id: string; status: string }>>(`/chat/embed-all?limit=${limit}`),
};

// ============ HELPER FOR STREAMING CHAT ============

export interface StreamCallbacks {
  onContent: (content: string) => void;
  onSources: (sources: ChatSource[]) => void;
  onDone: (conversationId: string, confidence: number) => void;
  onError: (error: string) => void;
}

export async function streamChat(
  message: string,
  callbacks: StreamCallbacks,
  conversationId?: string,
  propertyId?: string,
  documentType?: string
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/chat/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message,
      conversation_id: conversationId,
      property_id: propertyId,
      document_type: documentType,
      stream: true,
    }),
  });

  if (!response.ok) {
    throw new ApiError(response.status, response.statusText);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error('No response body');
  }

  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    let currentEvent = '';
    for (const line of lines) {
      if (line.startsWith('event: ')) {
        currentEvent = line.slice(7).trim();
        continue;
      }
      if (line.startsWith('data: ')) {
        const data = line.slice(6);
        try {
          const parsed = JSON.parse(data);

          // Handle based on event type
          if (currentEvent === 'content' && parsed.text !== undefined) {
            callbacks.onContent(parsed.text);
          } else if (currentEvent === 'sources' || Array.isArray(parsed)) {
            callbacks.onSources(Array.isArray(parsed) ? parsed : parsed.sources || []);
          } else if (currentEvent === 'done' || parsed.conversation_id) {
            callbacks.onDone(parsed.conversation_id, parsed.confidence || 0);
          } else if (parsed.error) {
            callbacks.onError(parsed.error);
          } else if (parsed.text !== undefined) {
            // Fallback for content without event type
            callbacks.onContent(parsed.text);
          }
        } catch {
          // Not JSON, treat as raw content
          callbacks.onContent(data);
        }
        currentEvent = '';
      }
    }
  }
}

// ============ ENRICHMENT API (Parallel AI) ============

// Market Intelligence Types
export interface MarketTrend {
  rate_change_pct: number | null;
  rate_change_range: string | null;
  direction: string;
  confidence: string;
}

export interface CarrierAppetite {
  carrier_name: string;
  appetite: string;
  notes: string | null;
}

export interface MarketIntelligenceResponse {
  property_id: string;
  property_type: string;
  state: string;
  research_date: string;
  rate_trend: MarketTrend;
  rate_trend_reasoning: string | null;
  key_factors: string[];
  factor_details: Record<string, string> | null;
  carrier_appetite: CarrierAppetite[];
  carrier_summary: string | null;
  forecast_6mo: string | null;
  forecast_12mo: string | null;
  regulatory_changes: string[];
  market_developments: string[];
  premium_benchmark: string | null;
  rate_per_sqft: number | null;
  sources: string[];
  parallel_latency_ms: number;
  gemini_latency_ms: number;
  total_latency_ms: number;
  raw_research?: string | null;
}

// Property Risk Types
export interface FloodRisk {
  zone: string | null;
  zone_description: string | null;
  risk_level: string;
  source: string | null;
}

export interface FireProtection {
  protection_class: string | null;
  fire_station_distance_miles: number | null;
  hydrant_distance_feet: number | null;
  source: string | null;
}

export interface WeatherRisk {
  hurricane_risk: string;
  tornado_risk: string;
  hail_risk: string;
  wildfire_risk: string;
  earthquake_risk: string;
  historical_events: string[];
}

export interface CrimeRisk {
  crime_index: number | null;
  crime_grade: string | null;
  risk_level: string;
  notes: string | null;
}

export interface EnvironmentalRisk {
  hazards: string[];
  superfund_nearby: boolean;
  industrial_nearby: boolean;
  risk_level: string;
}

export interface PropertyRiskResponse {
  property_id: string;
  address: string;
  enrichment_date: string;
  flood_risk: FloodRisk;
  fire_protection: FireProtection;
  weather_risk: WeatherRisk;
  crime_risk: CrimeRisk;
  environmental_risk: EnvironmentalRisk;
  recent_permits: string[];
  violations: string[];
  infrastructure_issues: string[];
  overall_risk_score: number | null;
  risk_summary: string | null;
  insurance_implications: string[];
  sources: string[];
  parallel_latency_ms: number;
  gemini_latency_ms: number;
  total_latency_ms: number;
  raw_research?: string | null;
  property_updated: boolean;
}

// Carrier Research Types
export interface CarrierRatings {
  am_best_rating: string | null;
  am_best_outlook: string | null;
  sp_rating: string | null;
  moodys_rating: string | null;
  rating_date: string | null;
}

export interface CarrierSpecialty {
  line_of_business: string;
  expertise_level: string;
  notes: string | null;
}

export interface CarrierNews {
  date: string | null;
  headline: string;
  summary: string | null;
  sentiment: string;
  source: string | null;
}

export interface CarrierResearchResponse {
  carrier_name: string;
  research_date: string;
  ratings: CarrierRatings;
  financial_strength: string;
  financial_summary: string | null;
  specialty_areas: CarrierSpecialty[];
  primary_lines: string[];
  market_position: string | null;
  geographic_focus: string[];
  target_segments: string[];
  commercial_property_appetite: string;
  appetite_notes: string | null;
  recent_news: CarrierNews[];
  news_summary: string | null;
  customer_satisfaction: string | null;
  claims_reputation: string | null;
  concerns: string[];
  regulatory_issues: string[];
  sources: string[];
  parallel_latency_ms: number;
  gemini_latency_ms: number;
  total_latency_ms: number;
  raw_research?: string | null;
}

// Lender Requirements Types
export interface CoverageRequirement {
  coverage_type: string;
  minimum_limit: number | null;
  limit_description: string | null;
  required: boolean;
  notes: string | null;
}

export interface DeductibleRequirement {
  coverage_type: string;
  maximum_amount: number | null;
  maximum_percentage: number | null;
  description: string | null;
}

export interface EndorsementRequirement {
  endorsement_name: string;
  description: string | null;
  required: boolean;
}

export interface LenderRequirementsResponse {
  lender_name: string;
  loan_type: string | null;
  research_date: string;
  property_coverage: CoverageRequirement | null;
  liability_coverage: CoverageRequirement | null;
  umbrella_coverage: CoverageRequirement | null;
  flood_coverage: CoverageRequirement | null;
  wind_coverage: CoverageRequirement | null;
  other_coverages: CoverageRequirement[];
  deductible_requirements: DeductibleRequirement[];
  max_property_deductible_pct: number | null;
  max_property_deductible_flat: number | null;
  required_endorsements: EndorsementRequirement[];
  mortgagee_clause_required: boolean;
  notice_of_cancellation_days: number | null;
  waiver_of_subrogation_required: boolean;
  minimum_carrier_rating: string | null;
  acceptable_rating_agencies: string[];
  special_requirements: string[];
  coastal_requirements: string | null;
  earthquake_requirements: string | null;
  source_document: string | null;
  source_section: string | null;
  sources: string[];
  parallel_latency_ms: number;
  gemini_latency_ms: number;
  total_latency_ms: number;
  raw_research?: string | null;
}

export const enrichmentApi = {
  // Market Intelligence
  getMarketIntelligence: (propertyId: string, includeRaw = false) =>
    apiGet<MarketIntelligenceResponse>(`/enrichment/market-intelligence/${propertyId}`, { include_raw_research: String(includeRaw) }),

  // Property Risk
  enrichPropertyRisk: (propertyId: string, updateProperty = false, includeRaw = false) =>
    apiPost<PropertyRiskResponse>(`/enrichment/properties/${propertyId}/enrich-risk`, {
      include_raw_research: includeRaw,
      update_property: updateProperty,
    }),

  // Carrier Research
  researchCarrier: (carrierName: string, propertyType?: string, includeRaw = false) =>
    apiGet<CarrierResearchResponse>(`/enrichment/carriers/${encodeURIComponent(carrierName)}/research`, {
      property_type: propertyType,
      include_raw_research: String(includeRaw),
    }),

  // Lender Requirements
  getLenderRequirements: (lenderName: string, loanType?: string, includeRaw = false) =>
    apiGet<LenderRequirementsResponse>(`/enrichment/lenders/${encodeURIComponent(lenderName)}/requirements`, {
      loan_type: loanType,
      include_raw_research: String(includeRaw),
    }),
};

// ============ ADMIN API ============

export interface ResetResponse {
  success: boolean;
  message: string;
  tables_cleared: string[];
  vectors_deleted: boolean;
  vector_count_before: number | null;
}

export interface SystemStats {
  database_stats: Record<string, number>;
  vector_stats: Record<string, number | string> | null;
}

export const adminApi = {
  getStats: () => apiGet<SystemStats>('/admin/stats'),
  resetAllData: () => apiPost<ResetResponse>('/admin/reset'),
};

// ============ CLAIMS API ============

export type ClaimStatus = 'open' | 'in_review' | 'processing' | 'closed' | 'pending' | 'denied';

export interface ClaimContact {
  role: string;
  name: string;
  email: string | null;
  phone: string | null;
}

export interface ClaimAttachmentGroup {
  category: string;
  display_name: string;
  count: number;
  attachments: Array<{
    id: string;
    filename: string;
    file_size: number | null;
  }>;
}

export interface ClaimTimelineStep {
  status: ClaimStatus;
  label: string;
  step_date: string | null;
  is_current: boolean;
  is_completed: boolean;
}

export interface ClaimListItem {
  id: string;
  claim_number: string | null;
  property_id: string;
  property_name: string | null;
  status: string | null;
  claim_type: string | null;
  date_of_loss: string | null;
  date_reported: string | null;
  total_incurred: number | null;
  attachment_count: number;
  days_open: number | null;
  has_alert: boolean;
  created_at: string;
}

export interface ClaimDetail extends ClaimListItem {
  policy_id: string | null;
  litigation_status: string | null;
  date_closed: string | null;
  description: string | null;
  cause_of_loss: string | null;
  location_description: string | null;
  location_address: string | null;
  location_name: string | null;
  carrier_name: string | null;
  paid_loss: number | null;
  paid_expense: number | null;
  paid_medical: number | null;
  paid_indemnity: number | null;
  total_paid: number | null;
  reserve_loss: number | null;
  reserve_expense: number | null;
  reserve_medical: number | null;
  reserve_indemnity: number | null;
  total_reserve: number | null;
  incurred_loss: number | null;
  incurred_expense: number | null;
  total_incurred: number | null;
  deductible_applied: number | null;
  deductible_recovered: number | null;
  salvage_amount: number | null;
  subrogation_amount: number | null;
  net_incurred: number | null;
  claimant_name: string | null;
  claimant_type: string | null;
  injury_description: string | null;
  notes: string | null;
  timeline: ClaimTimelineStep[];
  contacts: ClaimContact[];
  attachment_groups: ClaimAttachmentGroup[];
  updated_at: string | null;
}

export interface ClaimListResponse {
  claims: ClaimListItem[];
  total: number;
  by_status: Record<string, number>;
}

export interface ClaimKanbanResponse {
  open: ClaimListItem[];
  in_review: ClaimListItem[];
  processing: ClaimListItem[];
  closed: ClaimListItem[];
  total: number;
}

export interface ClaimSummary {
  total_claims: number;
  open_claims: number;
  closed_claims: number;
  total_incurred: number;
  total_paid: number;
  total_reserved: number;
  avg_days_to_close: number | null;
}

export interface ClaimCreateRequest {
  property_id: string;
  claim_number?: string;
  claim_type?: string;
  status?: ClaimStatus;
  date_of_loss?: string;
  date_reported?: string;
  description?: string;
  cause_of_loss?: string;
  carrier_name?: string;
  location_address?: string;
  claimant_name?: string;
  notes?: string;
}

export interface ClaimUpdateRequest {
  status?: ClaimStatus;
  notes?: string;
  description?: string;
}

export const claimsApi = {
  list: (params?: { property_id?: string; status?: string; year?: number; limit?: number; offset?: number }) =>
    apiGet<ClaimListResponse>('/claims', params as Record<string, string | undefined>),

  getKanban: (params?: { property_id?: string; year?: number }) =>
    apiGet<ClaimKanbanResponse>('/claims/kanban', params as Record<string, string | undefined>),

  getSummary: (propertyId?: string) =>
    apiGet<ClaimSummary>('/claims/summary', propertyId ? { property_id: propertyId } : undefined),

  get: (claimId: string) => apiGet<ClaimDetail>(`/claims/${claimId}`),

  create: (data: ClaimCreateRequest) => apiPost<ClaimDetail>('/claims', data),

  update: (claimId: string, data: ClaimUpdateRequest) =>
    apiPatch<ClaimDetail>(`/claims/${claimId}`, data),

  delete: (claimId: string) => apiDelete(`/claims/${claimId}`),
};

// ============ ACQUISITIONS API ============

export interface AcquisitionRequest {
  address: string;
  link?: string;
  unit_count: number;
  vintage: number;
  stories: number;
  total_buildings: number;
  total_sf: number;
  current_occupancy_pct: number;
  estimated_annual_income: number;
  notes?: string;
}

export interface PremiumRange {
  low: number;
  mid: number;
  high: number;
}

export interface ComparableProperty {
  property_id: string;
  name: string;
  address: string;
  premium_per_unit: number;
  premium_date: string;
  similarity_score: number;
  similarity_reason?: string;
}

export interface RiskFactor {
  name: string;
  severity: 'info' | 'warning' | 'critical';
  reason?: string;
}

export interface AcquisitionResult {
  is_unique: boolean;
  uniqueness_reason?: string;
  confidence: 'high' | 'medium' | 'low';
  premium_range?: PremiumRange;
  premium_range_label?: string;
  preliminary_estimate?: PremiumRange;
  message?: string;
  comparables: ComparableProperty[];
  risk_factors: RiskFactor[];
  llm_explanation?: string;
}

export const acquisitionsApi = {
  calculate: (data: AcquisitionRequest) =>
    apiPost<AcquisitionResult>('/acquisitions/calculate', data),
};

export default {
  dashboard: dashboardApi,
  properties: propertiesApi,
  healthScore: healthScoreApi,
  gaps: gapsApi,
  compliance: complianceApi,
  renewals: renewalsApi,
  documents: documentsApi,
  chat: chatApi,
  enrichment: enrichmentApi,
  admin: adminApi,
  claims: claimsApi,
  acquisitions: acquisitionsApi,
  streamChat,
};
