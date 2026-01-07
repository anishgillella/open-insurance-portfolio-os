// ============ COMMON ============
export type Severity = 'critical' | 'warning' | 'info';
export type GapStatus = 'open' | 'acknowledged' | 'resolved';
export type GapType =
  | 'underinsurance'
  | 'missing_coverage'
  | 'high_deductible'
  | 'expiring'
  | 'expiration'
  | 'non_compliant'
  | 'outdated_valuation'
  | 'missing_document'
  | 'missing_flood';

export type HealthGrade = 'A' | 'B' | 'C' | 'D' | 'F';

// ============ DASHBOARD ============
export interface DashboardSummary {
  total_properties: number;
  total_buildings: number;
  total_units: number;
  total_insured_value: number;
  total_premium: number;
  expirations: {
    within_30_days: number;
    within_60_days: number;
    within_90_days: number;
  };
  gaps: {
    total_open: number;
    critical: number;
    warning: number;
    info: number;
  };
  compliance: {
    compliant: number;
    non_compliant: number;
    no_requirements: number;
  };
  completeness: {
    average_percentage: number;
    properties_complete: number;
    properties_incomplete: number;
  };
  health_score: {
    average: number;
    grade: HealthGrade;
    trend: 'improving' | 'stable' | 'declining';
    change: number;
  };
}

export interface ExpirationItem {
  property_id: string;
  property_name: string;
  policy_id: string;
  policy_type: string;
  carrier: string;
  expiration_date: string;
  days_until_expiration: number;
  severity: Severity;
  premium: number;
}

export interface Alert {
  id: string;
  type: 'gap' | 'expiration' | 'compliance' | 'renewal';
  severity: Severity;
  title: string;
  description: string;
  property_id: string;
  property_name: string;
  created_at: string;
  acknowledged: boolean;
  action_url?: string;
}

// ============ PROPERTIES ============
export interface Property {
  id: string;
  name: string;
  address: {
    street: string;
    city: string;
    state: string;
    zip: string;
  };
  latitude?: number;
  longitude?: number;
  property_type: string;
  total_units: number;
  total_buildings: number;
  year_built: number;
  total_insured_value: number;
  total_premium: number;
  health_score: number;
  health_grade: HealthGrade;
  gaps_count: {
    critical: number;
    warning: number;
    info: number;
  };
  next_expiration: string | null;
  days_until_expiration: number | null;
  compliance_status: 'compliant' | 'non_compliant' | 'no_requirements';
  completeness_percentage: number;
  created_at: string;
  updated_at: string;
}

export interface PropertyDetail extends Property {
  buildings: Building[];
  policies: PolicySummary[];
  lender_requirements: LenderRequirement[];
  risk_factors: {
    flood_zone: string;
    earthquake_zone: string;
    wind_zone: string;
  };
}

export interface Building {
  id: string;
  name: string;
  construction_type: string;
  year_built: number;
  stories: number;
  units: number;
  square_footage: number;
  replacement_cost: number;
  sprinklered: boolean;
  fire_alarm: boolean;
}

// ============ POLICIES ============
export interface PolicySummary {
  id: string;
  policy_number: string;
  policy_type: string;
  carrier: string;
  effective_date: string;
  expiration_date: string;
  premium: number;
  limit: number;
  deductible: number;
}

export interface PolicyDetail extends PolicySummary {
  coverages: Coverage[];
  endorsements: Endorsement[];
  additional_insureds: AdditionalInsured[];
  source_documents: DocumentSummary[];
}

export interface Coverage {
  id: string;
  coverage_type: string;
  limit: number;
  deductible: number;
  coinsurance?: number;
  sublimits?: Record<string, number>;
}

export interface Endorsement {
  id: string;
  number: string;
  title: string;
  description: string;
}

export interface AdditionalInsured {
  id: string;
  name: string;
  relationship: string;
}

// ============ GAPS ============
export interface Gap {
  id: string;
  property_id: string;
  property_name: string;
  policy_id?: string;
  policy_number?: string;
  gap_type: GapType;
  severity: Severity;
  title: string;
  description: string;
  current_value?: string;
  recommended_value?: string;
  gap_amount?: number;
  status: GapStatus;
  acknowledged_by?: string;
  acknowledged_at?: string;
  resolved_by?: string;
  resolved_at?: string;
  resolution_notes?: string;
  created_at: string;
  updated_at: string;
}

export interface GapAnalysis {
  gap_id: string;
  risk_assessment: string;
  potential_impact: string;
  recommendation: string;
  estimated_cost_to_resolve?: number;
  related_gaps: string[];
  llm_analysis: string;
}

// ============ HEALTH SCORE ============
export interface HealthScore {
  property_id: string;
  score: number;
  grade: HealthGrade;
  trend: 'improving' | 'stable' | 'declining';
  previous_score?: number;
  change?: number;
  components: HealthScoreComponent[];
  recommendations: HealthScoreRecommendation[];
  calculated_at: string;
}

export interface HealthScoreComponent {
  name: string;
  weight: number;
  score: number;
  max_score: number;
  percentage: number;
  details: string;
  issues: string[];
}

export interface HealthScoreRecommendation {
  priority: 'high' | 'medium' | 'low';
  title: string;
  description: string;
  potential_improvement: number;
  action_type: 'fix_gap' | 'upload_document' | 'update_coverage' | 'other';
  action_url?: string;
}

export interface HealthScoreHistory {
  property_id: string;
  history: Array<{
    date: string;
    score: number;
    grade: HealthGrade;
  }>;
}

// ============ COMPLIANCE ============
export interface ComplianceStatus {
  property_id: string;
  is_compliant: boolean;
  lender_name?: string;
  loan_number?: string;
  template_used: string;
  checks: ComplianceCheck[];
  last_checked: string;
}

export interface ComplianceCheck {
  requirement: string;
  status: 'pass' | 'fail' | 'not_required';
  current_value?: string;
  required_value?: string;
  gap_amount?: number;
  issue_message?: string;
}

export interface LenderRequirement {
  id: string;
  lender_name: string;
  loan_number: string;
  property_coverage_limit: number;
  gl_per_occurrence: number;
  umbrella_limit?: number;
  max_deductible_percentage: number;
  max_deductible_flat: number;
  flood_required: boolean;
  mortgagee_name: string;
}

// ============ RENEWALS ============
export interface RenewalForecast {
  property_id: string;
  current_premium: number;
  forecast: {
    low: number;
    mid: number;
    high: number;
    low_change_percent: number;
    mid_change_percent: number;
    high_change_percent: number;
  };
  confidence: number;
  factors: RenewalFactor[];
  llm_analysis?: string;
  calculated_at: string;
}

export interface RenewalFactor {
  name: string;
  impact_percent: number;
  direction: 'increase' | 'decrease' | 'neutral';
  description: string;
}

export interface RenewalTimeline {
  property_id: string;
  expiration_date: string;
  days_until_expiration: number;
  milestones: RenewalMilestone[];
}

export interface RenewalMilestone {
  name: string;
  target_date: string;
  days_before_expiration: number;
  status: 'completed' | 'in_progress' | 'upcoming' | 'overdue';
  action_items: string[];
  documents_ready: Record<string, boolean>;
}

export interface MarketIntelligence {
  property_id: string;
  rate_trend: string;
  rate_change_percent: number;
  key_factors: string[];
  carrier_appetite: 'growing' | 'stable' | 'shrinking';
  carrier_notes: string;
  six_month_forecast: string;
  opportunities: string[];
  sources: string[];
  fetched_at: string;
}

// ============ DOCUMENTS ============
export interface DocumentSummary {
  id: string;
  filename: string;
  document_type: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  confidence?: number;
  property_id?: string;
  uploaded_at: string;
}

export interface DocumentDetail extends DocumentSummary {
  file_url: string;
  file_size: number;
  mime_type: string;
  extraction_result?: Record<string, unknown>;
  ocr_text?: string;
  processed_at?: string;
  error_message?: string;
}

// ============ COMPLETENESS ============
export interface DocumentCompleteness {
  property_id: string;
  overall_percentage: number;
  grade: HealthGrade;
  required: DocumentCompletenessItem[];
  optional: DocumentCompletenessItem[];
}

export interface DocumentCompletenessItem {
  document_type: string;
  status: 'present' | 'missing' | 'not_applicable';
  document_id?: string;
  filename?: string;
  uploaded_at?: string;
  importance: string;
}

// ============ CHAT ============
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
  page_number?: number;
  section?: string;
  relevance_score: number;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  property_id?: string;
  document_type?: string;
  stream?: boolean;
}

// ============ RENEWAL ALERTS ============
export type RenewalAlertStatus = 'pending' | 'acknowledged' | 'resolved' | 'expired';

export interface RenewalAlert {
  id: string;
  property_id: string;
  property_name: string;
  policy_id: string;
  policy_number: string;
  threshold_days: number;
  days_until_expiration: number;
  expiration_date: string;
  severity: Severity;
  title: string;
  message: string;
  status: RenewalAlertStatus;
  llm_priority_score: number;
  llm_renewal_strategy: string;
  llm_key_actions: string[];
  created_at: string;
  acknowledged_at?: string;
  resolved_at?: string;
}

// ============ ALERT CONFIGURATION ============
export interface AlertThreshold {
  days: number;
  severity: Severity;
  notify_email: boolean;
  notify_dashboard: boolean;
}

export interface AlertConfig {
  property_id: string;
  enabled: boolean;
  thresholds: AlertThreshold[];
  recipients: string[];
  updated_at: string;
}

// ============ RENEWAL FORECASTS (Extended) ============
export interface RenewalForecastExtended extends RenewalForecast {
  id: string;
  property_name: string;
  current_expiration_date: string;
  status: 'active' | 'superseded' | 'expired';
  rule_based_estimate: number;
  rule_based_change_pct: number;
  negotiation_points: string[];
  model_used: string;
}

// ============ RENEWAL TIMELINES (Extended) ============
export interface RenewalTimelineSummary {
  total_milestones: number;
  completed: number;
  in_progress: number;
  upcoming: number;
  overdue: number;
}

export interface RenewalTimelineExtended extends RenewalTimeline {
  summary: RenewalTimelineSummary;
}

// ============ DOCUMENT READINESS ============
export type DocumentStatus = 'found' | 'missing' | 'stale' | 'not_applicable';

export interface DocumentReadinessItem {
  type: string;
  label: string;
  status: DocumentStatus;
  document_id?: string;
  filename?: string;
  age_days?: number;
  verified: boolean;
  issues?: string[];
}

export interface DocumentReadiness {
  property_id: string;
  property_name: string;
  overall_score: number;
  grade: HealthGrade;
  documents: DocumentReadinessItem[];
  last_assessed: string;
}

// ============ MARKET CONTEXT ============
export type CompetitivePosition = 'strong' | 'moderate' | 'weak';

export interface MarketContext extends MarketIntelligence {
  id: string;
  property_name: string;
  competitive_position: CompetitivePosition;
  recommended_actions: string[];
}

// ============ POLICY COMPARISON ============
export interface PolicyCoverage {
  type: string;
  limit: number;
  deductible: number;
}

export interface PolicySnapshot {
  policy_number: string;
  effective_date: string;
  expiration_date: string;
  premium: number;
  carrier: string;
  coverages: PolicyCoverage[];
}

export type ChangeType = 'increase' | 'decrease' | 'same' | 'new' | 'removed';
export type ChangeImpact = 'positive' | 'negative' | 'neutral';

export interface PolicyChange {
  field: string;
  prior_value: string;
  current_value: string;
  change_type: ChangeType;
  impact: ChangeImpact;
}

export interface PolicyComparison {
  property_id: string;
  property_name: string;
  current_policy: PolicySnapshot;
  prior_policy: PolicySnapshot;
  changes: PolicyChange[];
  premium_change_pct: number;
}

// ============ PORTFOLIO RENEWAL SUMMARY ============
export interface PortfolioRenewalSummary {
  total_properties: number;
  total_upcoming_renewals: number;
  total_premium_at_risk: number;
  by_urgency: {
    critical: number;
    warning: number;
    info: number;
  };
  by_status: {
    on_track: number;
    needs_attention: number;
    overdue: number;
  };
  avg_forecast_change_pct: number;
  projected_total_premium: number;
}
