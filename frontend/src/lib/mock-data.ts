import type {
  Property as PropertyType,
  Gap,
  Alert,
  HealthGrade,
  Severity,
  RenewalForecast,
  RenewalTimeline,
  RenewalMilestone,
  MarketIntelligence,
} from '@/types/api';

// Re-export Property type for convenience
export type Property = PropertyType;

// ============ DASHBOARD SUMMARY ============
export const mockDashboardSummary = {
  totalProperties: 12,
  totalInsuredValue: 245000000,
  totalPremium: 2450000,
  averageHealthScore: 78,
};

export const mockProperties: Property[] = [
  {
    id: 'prop-1',
    name: 'Shoaff Park Apartments',
    address: { street: '2500 Shoaff Park Dr', city: 'Fort Wayne', state: 'IN', zip: '46825' },
    property_type: 'Multi-Family',
    total_units: 156,
    total_buildings: 8,
    year_built: 1998,
    total_insured_value: 32500000,
    total_premium: 285000,
    health_score: 72,
    health_grade: 'C',
    gaps_count: { critical: 2, warning: 1, info: 0 },
    next_expiration: '2026-01-20',
    days_until_expiration: 16,
    compliance_status: 'non_compliant',
    completeness_percentage: 75,
    created_at: '2024-01-15',
    updated_at: '2026-01-03',
  },
  {
    id: 'prop-2',
    name: 'Buffalo Run Estates',
    address: { street: '1200 Buffalo Run Blvd', city: 'Fort Wayne', state: 'IN', zip: '46804' },
    property_type: 'Multi-Family',
    total_units: 220,
    total_buildings: 12,
    year_built: 2005,
    total_insured_value: 45000000,
    total_premium: 412000,
    health_score: 85,
    health_grade: 'B',
    gaps_count: { critical: 0, warning: 2, info: 1 },
    next_expiration: '2026-02-18',
    days_until_expiration: 45,
    compliance_status: 'compliant',
    completeness_percentage: 92,
    created_at: '2024-02-01',
    updated_at: '2026-01-02',
  },
  {
    id: 'prop-3',
    name: 'Lake Sheri Villas',
    address: { street: '800 Lake Sheri Dr', city: 'Fort Wayne', state: 'IN', zip: '46815' },
    property_type: 'Multi-Family',
    total_units: 88,
    total_buildings: 4,
    year_built: 2012,
    total_insured_value: 22000000,
    total_premium: 178000,
    health_score: 91,
    health_grade: 'A',
    gaps_count: { critical: 0, warning: 0, info: 2 },
    next_expiration: '2026-03-22',
    days_until_expiration: 77,
    compliance_status: 'compliant',
    completeness_percentage: 98,
    created_at: '2024-01-20',
    updated_at: '2026-01-01',
  },
  {
    id: 'prop-4',
    name: 'Riverside Commons',
    address: { street: '450 Riverside Dr', city: 'Indianapolis', state: 'IN', zip: '46202' },
    property_type: 'Mixed-Use',
    total_units: 180,
    total_buildings: 6,
    year_built: 2018,
    total_insured_value: 55000000,
    total_premium: 485000,
    health_score: 88,
    health_grade: 'B',
    gaps_count: { critical: 0, warning: 1, info: 1 },
    next_expiration: '2026-04-15',
    days_until_expiration: 101,
    compliance_status: 'compliant',
    completeness_percentage: 95,
    created_at: '2024-03-01',
    updated_at: '2025-12-28',
  },
  {
    id: 'prop-5',
    name: 'Maple Grove Apartments',
    address: { street: '3200 Maple Grove Ln', city: 'Carmel', state: 'IN', zip: '46032' },
    property_type: 'Multi-Family',
    total_units: 144,
    total_buildings: 6,
    year_built: 2015,
    total_insured_value: 38000000,
    total_premium: 325000,
    health_score: 94,
    health_grade: 'A',
    gaps_count: { critical: 0, warning: 0, info: 1 },
    next_expiration: '2026-05-10',
    days_until_expiration: 126,
    compliance_status: 'compliant',
    completeness_percentage: 100,
    created_at: '2024-02-15',
    updated_at: '2025-12-20',
  },
  {
    id: 'prop-6',
    name: 'Downtown Lofts',
    address: { street: '100 Main St', city: 'Fort Wayne', state: 'IN', zip: '46802' },
    property_type: 'Multi-Family',
    total_units: 64,
    total_buildings: 1,
    year_built: 1920,
    total_insured_value: 18000000,
    total_premium: 195000,
    health_score: 65,
    health_grade: 'D',
    gaps_count: { critical: 1, warning: 2, info: 1 },
    next_expiration: '2026-06-30',
    days_until_expiration: 177,
    compliance_status: 'non_compliant',
    completeness_percentage: 68,
    created_at: '2024-01-10',
    updated_at: '2025-12-15',
  },
  {
    id: 'prop-7',
    name: 'Eastwood Manor',
    address: { street: '5500 Eastwood Rd', city: 'Fort Wayne', state: 'IN', zip: '46816' },
    property_type: 'Multi-Family',
    total_units: 200,
    total_buildings: 10,
    year_built: 2008,
    total_insured_value: 42000000,
    total_premium: 375000,
    health_score: 79,
    health_grade: 'C',
    gaps_count: { critical: 0, warning: 2, info: 2 },
    next_expiration: '2026-02-08',
    days_until_expiration: 35,
    compliance_status: 'compliant',
    completeness_percentage: 85,
    created_at: '2024-02-20',
    updated_at: '2026-01-02',
  },
];

// ============ HEALTH SCORE COMPONENTS ============
export interface HealthComponent {
  name: string;
  score: number;
  weight: number;
  max_score: number;
  percentage: number;
  details: string;
  issues: string[];
}

export const mockHealthComponents: HealthComponent[] = [
  {
    name: 'Coverage Adequacy',
    score: 80,
    weight: 25,
    max_score: 100,
    percentage: 80,
    details: 'Property coverage is 92% of replacement cost',
    issues: ['Underinsured by $2.1M on main building'],
  },
  {
    name: 'Policy Currency',
    score: 90,
    weight: 20,
    max_score: 100,
    percentage: 90,
    details: 'All policies are current and active',
    issues: [],
  },
  {
    name: 'Deductible Risk',
    score: 67,
    weight: 15,
    max_score: 100,
    percentage: 67,
    details: 'Current deductible is 3% of TIV',
    issues: ['Deductible exceeds lender requirement of 2%'],
  },
  {
    name: 'Coverage Breadth',
    score: 80,
    weight: 15,
    max_score: 100,
    percentage: 80,
    details: 'Most required coverages in place',
    issues: ['Missing flood coverage in Zone AE'],
  },
  {
    name: 'Lender Compliance',
    score: 100,
    weight: 15,
    max_score: 100,
    percentage: 100,
    details: 'All lender requirements satisfied',
    issues: [],
  },
  {
    name: 'Documentation',
    score: 70,
    weight: 10,
    max_score: 100,
    percentage: 70,
    details: 'Most documents uploaded',
    issues: ['Missing current Evidence of Property insurance'],
  },
];

// ============ RECOMMENDATIONS ============
export interface Recommendation {
  priority: 'high' | 'medium' | 'low';
  title: string;
  description: string;
  potential_improvement: number;
  action_type: 'fix_gap' | 'upload_document' | 'update_coverage' | 'other';
}

export const mockRecommendations: Recommendation[] = [
  {
    priority: 'high',
    title: 'Reduce deductible from 3% to 2%',
    description: 'Current deductible exceeds lender requirement. Reducing to 2% will improve compliance.',
    potential_improvement: 8,
    action_type: 'update_coverage',
  },
  {
    priority: 'high',
    title: 'Address $2.1M underinsurance gap',
    description: 'Main building is underinsured. Request updated appraisal and increase coverage.',
    potential_improvement: 12,
    action_type: 'fix_gap',
  },
  {
    priority: 'medium',
    title: 'Upload Evidence of Property insurance',
    description: 'Current EOP document is missing from the system.',
    potential_improvement: 5,
    action_type: 'upload_document',
  },
  {
    priority: 'medium',
    title: 'Add flood coverage for Zone AE',
    description: 'Property is in FEMA flood zone AE and requires flood insurance.',
    potential_improvement: 6,
    action_type: 'fix_gap',
  },
  {
    priority: 'low',
    title: 'Review umbrella coverage limits',
    description: 'Consider increasing umbrella coverage from $5M to $10M.',
    potential_improvement: 3,
    action_type: 'update_coverage',
  },
];

// ============ SCORE HISTORY ============
export interface ScoreHistoryPoint {
  date: string;
  score: number;
  grade: HealthGrade;
}

export const mockScoreHistory: ScoreHistoryPoint[] = [
  { date: '2025-07-01', score: 65, grade: 'D' },
  { date: '2025-08-01', score: 68, grade: 'D' },
  { date: '2025-09-01', score: 72, grade: 'C' },
  { date: '2025-10-01', score: 74, grade: 'C' },
  { date: '2025-11-01', score: 76, grade: 'C' },
  { date: '2025-12-01', score: 78, grade: 'C' },
  { date: '2026-01-01', score: 78, grade: 'C' },
];

// ============ ALERTS ============
export const mockAlerts: Alert[] = [
  {
    id: 'alert-1',
    type: 'gap',
    severity: 'critical',
    title: 'Underinsurance Gap Detected',
    description: 'Main building underinsured by $2.1M based on latest appraisal',
    property_id: 'prop-1',
    property_name: 'Shoaff Park Apartments',
    created_at: '2026-01-02',
    acknowledged: false,
  },
  {
    id: 'alert-2',
    type: 'expiration',
    severity: 'critical',
    title: 'Policy Expiring Soon',
    description: 'Property policy expires in 16 days',
    property_id: 'prop-1',
    property_name: 'Shoaff Park Apartments',
    created_at: '2026-01-01',
    acknowledged: false,
  },
  {
    id: 'alert-3',
    type: 'gap',
    severity: 'warning',
    title: 'Missing Flood Coverage',
    description: 'Property in FEMA Zone AE requires flood insurance',
    property_id: 'prop-2',
    property_name: 'Buffalo Run Estates',
    created_at: '2025-12-28',
    acknowledged: true,
  },
  {
    id: 'alert-4',
    type: 'compliance',
    severity: 'warning',
    title: 'Deductible Exceeds Limit',
    description: 'Current 3% deductible exceeds lender requirement of 2%',
    property_id: 'prop-1',
    property_name: 'Shoaff Park Apartments',
    created_at: '2025-12-20',
    acknowledged: false,
  },
];

// ============ GAPS ============
export const mockGaps: Gap[] = [
  {
    id: 'gap-1',
    property_id: 'prop-1',
    property_name: 'Shoaff Park Apartments',
    policy_id: 'pol-1',
    policy_number: 'PROP-2024-001',
    gap_type: 'underinsurance',
    severity: 'critical',
    title: 'Underinsurance - Main Building',
    description: 'Current coverage is $2.1M below the replacement cost value',
    current_value: '$30,400,000',
    recommended_value: '$32,500,000',
    gap_amount: 2100000,
    status: 'open',
    created_at: '2026-01-02',
    updated_at: '2026-01-02',
  },
  {
    id: 'gap-2',
    property_id: 'prop-1',
    property_name: 'Shoaff Park Apartments',
    policy_id: 'pol-1',
    policy_number: 'PROP-2024-001',
    gap_type: 'high_deductible',
    severity: 'critical',
    title: 'Deductible Exceeds Lender Requirement',
    description: 'Current deductible of 3% exceeds the lender maximum of 2%',
    current_value: '3%',
    recommended_value: '2%',
    status: 'open',
    created_at: '2025-12-20',
    updated_at: '2025-12-20',
  },
  {
    id: 'gap-3',
    property_id: 'prop-2',
    property_name: 'Buffalo Run Estates',
    gap_type: 'missing_flood',
    severity: 'warning',
    title: 'Missing Flood Coverage',
    description: 'Property is in FEMA Zone AE and requires flood insurance',
    current_value: 'None',
    recommended_value: '$5,000,000',
    status: 'acknowledged',
    acknowledged_by: 'John Smith',
    acknowledged_at: '2025-12-29',
    created_at: '2025-12-28',
    updated_at: '2025-12-29',
  },
  {
    id: 'gap-4',
    property_id: 'prop-6',
    property_name: 'Downtown Lofts',
    gap_type: 'outdated_valuation',
    severity: 'critical',
    title: 'Outdated Property Valuation',
    description: 'Last appraisal was conducted over 3 years ago',
    current_value: '2022-03-15',
    recommended_value: 'Within 12 months',
    status: 'open',
    created_at: '2025-11-01',
    updated_at: '2025-11-01',
  },
  {
    id: 'gap-5',
    property_id: 'prop-7',
    property_name: 'Eastwood Manor',
    gap_type: 'missing_document',
    severity: 'warning',
    title: 'Missing Certificate of Insurance',
    description: 'Current COI has not been uploaded to the system',
    status: 'open',
    created_at: '2025-12-15',
    updated_at: '2025-12-15',
  },
];

// ============ COMPLIANCE ============
export interface ComplianceTemplate {
  id: string;
  name: string;
  lender_name: string;
  requirements: {
    property_coverage_limit: number;
    gl_per_occurrence: number;
    umbrella_limit?: number;
    max_deductible_percentage: number;
    max_deductible_flat: number;
    flood_required: boolean;
  };
}

export const mockComplianceTemplates: ComplianceTemplate[] = [
  {
    id: 'template-1',
    name: 'Standard Fannie Mae',
    lender_name: 'Fannie Mae',
    requirements: {
      property_coverage_limit: 100,
      gl_per_occurrence: 1000000,
      umbrella_limit: 5000000,
      max_deductible_percentage: 2,
      max_deductible_flat: 50000,
      flood_required: true,
    },
  },
  {
    id: 'template-2',
    name: 'Freddie Mac Conventional',
    lender_name: 'Freddie Mac',
    requirements: {
      property_coverage_limit: 100,
      gl_per_occurrence: 1000000,
      umbrella_limit: 5000000,
      max_deductible_percentage: 2.5,
      max_deductible_flat: 75000,
      flood_required: true,
    },
  },
  {
    id: 'template-3',
    name: 'HUD/FHA Requirements',
    lender_name: 'HUD',
    requirements: {
      property_coverage_limit: 100,
      gl_per_occurrence: 1000000,
      umbrella_limit: 10000000,
      max_deductible_percentage: 1,
      max_deductible_flat: 25000,
      flood_required: true,
    },
  },
];

export interface ComplianceCheckResult {
  property_id: string;
  property_name: string;
  template_id: string;
  template_name: string;
  is_compliant: boolean;
  checks: Array<{
    requirement: string;
    status: 'pass' | 'fail' | 'not_required';
    current_value?: string;
    required_value?: string;
    gap_amount?: number;
  }>;
  last_checked: string;
}

export const mockComplianceResults: ComplianceCheckResult[] = [
  {
    property_id: 'prop-1',
    property_name: 'Shoaff Park Apartments',
    template_id: 'template-1',
    template_name: 'Standard Fannie Mae',
    is_compliant: false,
    checks: [
      { requirement: 'Property Coverage', status: 'fail', current_value: '94%', required_value: '100%', gap_amount: 2100000 },
      { requirement: 'GL Per Occurrence', status: 'pass', current_value: '$1,000,000', required_value: '$1,000,000' },
      { requirement: 'Umbrella Limit', status: 'pass', current_value: '$5,000,000', required_value: '$5,000,000' },
      { requirement: 'Max Deductible', status: 'fail', current_value: '3%', required_value: '2%' },
      { requirement: 'Flood Coverage', status: 'pass', current_value: 'Active', required_value: 'Required' },
    ],
    last_checked: '2026-01-03',
  },
  {
    property_id: 'prop-2',
    property_name: 'Buffalo Run Estates',
    template_id: 'template-1',
    template_name: 'Standard Fannie Mae',
    is_compliant: true,
    checks: [
      { requirement: 'Property Coverage', status: 'pass', current_value: '100%', required_value: '100%' },
      { requirement: 'GL Per Occurrence', status: 'pass', current_value: '$1,000,000', required_value: '$1,000,000' },
      { requirement: 'Umbrella Limit', status: 'pass', current_value: '$5,000,000', required_value: '$5,000,000' },
      { requirement: 'Max Deductible', status: 'pass', current_value: '1.5%', required_value: '2%' },
      { requirement: 'Flood Coverage', status: 'fail', current_value: 'None', required_value: 'Required' },
    ],
    last_checked: '2026-01-02',
  },
];

// Compliance Statuses for each property
export const mockComplianceStatuses: ComplianceCheckResult[] = mockComplianceResults;

// Coverage Types for display
export const mockCoverageTypes = [
  { id: 'property', name: 'Property', icon: 'Building2' },
  { id: 'gl', name: 'General Liability', icon: 'Shield' },
  { id: 'umbrella', name: 'Umbrella', icon: 'Umbrella' },
  { id: 'flood', name: 'Flood', icon: 'Droplets' },
  { id: 'earthquake', name: 'Earthquake', icon: 'Activity' },
  { id: 'crime', name: 'Crime', icon: 'Lock' },
];

// ============ RENEWALS - NEW FOR PHASE 5 ============

// Renewal Alerts (with LLM-enhanced fields)
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
  status: 'pending' | 'acknowledged' | 'resolved' | 'expired';
  llm_priority_score: number;
  llm_renewal_strategy: string;
  llm_key_actions: string[];
  created_at: string;
  acknowledged_at?: string;
  resolved_at?: string;
}

export const mockRenewalAlerts: RenewalAlert[] = [
  {
    id: 'renewal-alert-1',
    property_id: 'prop-1',
    property_name: 'Shoaff Park Apartments',
    policy_id: 'pol-1',
    policy_number: 'PROP-2024-001',
    threshold_days: 30,
    days_until_expiration: 16,
    expiration_date: '2026-01-20',
    severity: 'critical',
    title: 'Critical: Policy expires in 16 days',
    message: 'Immediate action required. Begin renewal negotiations now to avoid coverage gap.',
    status: 'pending',
    llm_priority_score: 95,
    llm_renewal_strategy: 'Given the underinsurance gap and deductible issues, negotiate a comprehensive renewal that addresses both. Consider bundling with umbrella for better rates.',
    llm_key_actions: [
      'Contact current carrier for renewal quote by Jan 8',
      'Request competing quotes from 2-3 alternative carriers',
      'Update property valuation before renewal',
      'Negotiate deductible reduction to meet lender requirements',
    ],
    created_at: '2026-01-04',
  },
  {
    id: 'renewal-alert-2',
    property_id: 'prop-7',
    property_name: 'Eastwood Manor',
    policy_id: 'pol-7',
    policy_number: 'PROP-2024-007',
    threshold_days: 45,
    days_until_expiration: 35,
    expiration_date: '2026-02-08',
    severity: 'warning',
    title: 'Renewal approaching in 35 days',
    message: 'Start gathering documents and requesting quotes for renewal.',
    status: 'acknowledged',
    llm_priority_score: 72,
    llm_renewal_strategy: 'Property is in good standing. Focus on securing competitive rates and consider increasing coverage to match recent property improvements.',
    llm_key_actions: [
      'Request renewal terms from current carrier',
      'Compile loss run reports for past 5 years',
      'Document recent property improvements for rate negotiation',
    ],
    created_at: '2026-01-02',
    acknowledged_at: '2026-01-03',
  },
  {
    id: 'renewal-alert-3',
    property_id: 'prop-2',
    property_name: 'Buffalo Run Estates',
    policy_id: 'pol-2',
    policy_number: 'PROP-2024-002',
    threshold_days: 60,
    days_until_expiration: 45,
    expiration_date: '2026-02-18',
    severity: 'warning',
    title: 'Renewal window opening - 45 days',
    message: 'Good time to begin the renewal process and address outstanding gaps.',
    status: 'pending',
    llm_priority_score: 65,
    llm_renewal_strategy: 'Address the missing flood coverage gap during renewal. The property is in Zone AE and this is a compliance requirement.',
    llm_key_actions: [
      'Obtain flood insurance quote before renewal',
      'Bundle flood with property for potential discount',
      'Review current coverage limits against updated TIV',
    ],
    created_at: '2026-01-01',
  },
  {
    id: 'renewal-alert-4',
    property_id: 'prop-3',
    property_name: 'Lake Sheri Villas',
    policy_id: 'pol-3',
    policy_number: 'PROP-2024-003',
    threshold_days: 90,
    days_until_expiration: 77,
    expiration_date: '2026-03-22',
    severity: 'info',
    title: 'Early renewal notification - 77 days',
    message: 'Property in excellent standing. Consider early renewal for rate lock.',
    status: 'pending',
    llm_priority_score: 45,
    llm_renewal_strategy: 'Excellent health score and compliance status. Leverage this for rate reduction or enhanced coverage at same premium.',
    llm_key_actions: [
      'Request early renewal discount from carrier',
      'Explore multi-year policy options for rate stability',
    ],
    created_at: '2025-12-28',
  },
];

// Renewal Alert Configuration
export interface AlertConfig {
  property_id: string;
  enabled: boolean;
  thresholds: Array<{
    days: number;
    severity: Severity;
    notify_email: boolean;
    notify_dashboard: boolean;
  }>;
  recipients: string[];
  updated_at: string;
}

export const mockAlertConfigs: AlertConfig[] = [
  {
    property_id: 'prop-1',
    enabled: true,
    thresholds: [
      { days: 90, severity: 'info', notify_email: false, notify_dashboard: true },
      { days: 60, severity: 'warning', notify_email: true, notify_dashboard: true },
      { days: 30, severity: 'critical', notify_email: true, notify_dashboard: true },
      { days: 14, severity: 'critical', notify_email: true, notify_dashboard: true },
    ],
    recipients: ['john.smith@company.com', 'insurance@company.com'],
    updated_at: '2025-12-01',
  },
  {
    property_id: 'prop-2',
    enabled: true,
    thresholds: [
      { days: 90, severity: 'info', notify_email: false, notify_dashboard: true },
      { days: 60, severity: 'warning', notify_email: true, notify_dashboard: true },
      { days: 30, severity: 'critical', notify_email: true, notify_dashboard: true },
    ],
    recipients: ['john.smith@company.com'],
    updated_at: '2025-11-15',
  },
];

// Renewal Forecasts (with LLM predictions)
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

export const mockRenewalForecasts: RenewalForecastExtended[] = [
  {
    id: 'forecast-1',
    property_id: 'prop-1',
    property_name: 'Shoaff Park Apartments',
    current_premium: 285000,
    current_expiration_date: '2026-01-20',
    status: 'active',
    rule_based_estimate: 310000,
    rule_based_change_pct: 8.8,
    forecast: {
      low: 295000,
      mid: 315000,
      high: 342000,
      low_change_percent: 3.5,
      mid_change_percent: 10.5,
      high_change_percent: 20.0,
    },
    confidence: 78,
    factors: [
      { name: 'Market Rate Trend', impact_percent: 5.2, direction: 'increase', description: 'Commercial property rates up 5-7% YoY' },
      { name: 'Claims History', impact_percent: 2.1, direction: 'increase', description: '2 claims in past 3 years affecting experience rating' },
      { name: 'Property Age', impact_percent: 1.5, direction: 'increase', description: 'Building over 25 years old, increased maintenance risk' },
      { name: 'Coverage Gap Resolution', impact_percent: 3.5, direction: 'increase', description: 'Increasing coverage to meet valuation will raise premium' },
      { name: 'Multi-Year Discount', impact_percent: -2.0, direction: 'decrease', description: 'Potential 2% discount for 3-year commitment' },
    ],
    llm_analysis: 'Given the combination of market conditions and property-specific factors, expect a 8-12% increase. The underinsurance gap resolution will add approximately 3-4% but is necessary for proper coverage. Consider negotiating a multi-year policy to lock in rates before further market increases.',
    negotiation_points: [
      'Highlight 25+ year relationship with carrier',
      'Emphasize proactive risk management improvements',
      'Bundle with other properties for portfolio discount',
      'Request premium credit for installing new fire suppression system',
    ],
    calculated_at: '2026-01-03',
    model_used: 'claude-3-opus',
  },
  {
    id: 'forecast-2',
    property_id: 'prop-7',
    property_name: 'Eastwood Manor',
    current_premium: 375000,
    current_expiration_date: '2026-02-08',
    status: 'active',
    rule_based_estimate: 390000,
    rule_based_change_pct: 4.0,
    forecast: {
      low: 378000,
      mid: 395000,
      high: 420000,
      low_change_percent: 0.8,
      mid_change_percent: 5.3,
      high_change_percent: 12.0,
    },
    confidence: 82,
    factors: [
      { name: 'Market Rate Trend', impact_percent: 4.5, direction: 'increase', description: 'Commercial property rates trending up' },
      { name: 'Clean Claims History', impact_percent: -1.5, direction: 'decrease', description: 'No claims in 5 years provides rate credit' },
      { name: 'Property Improvements', impact_percent: -0.8, direction: 'decrease', description: 'Recent roof replacement reduces risk' },
    ],
    llm_analysis: 'Strong property fundamentals support a favorable renewal. The clean claims history is a significant negotiating advantage. Recommend pursuing rate reduction or enhanced coverage at flat premium.',
    negotiation_points: [
      'Leverage clean claims history for rate credit',
      'Present documentation of recent improvements',
      'Request enhanced coverage at current premium',
    ],
    calculated_at: '2026-01-02',
    model_used: 'claude-3-opus',
  },
  {
    id: 'forecast-3',
    property_id: 'prop-2',
    property_name: 'Buffalo Run Estates',
    current_premium: 412000,
    current_expiration_date: '2026-02-18',
    status: 'active',
    rule_based_estimate: 435000,
    rule_based_change_pct: 5.6,
    forecast: {
      low: 420000,
      mid: 445000,
      high: 475000,
      low_change_percent: 1.9,
      mid_change_percent: 8.0,
      high_change_percent: 15.3,
    },
    confidence: 75,
    factors: [
      { name: 'Market Rate Trend', impact_percent: 5.0, direction: 'increase', description: 'Market conditions pushing rates higher' },
      { name: 'Flood Zone Exposure', impact_percent: 3.5, direction: 'increase', description: 'Zone AE location increases flood risk premium' },
      { name: 'Portfolio Size', impact_percent: -1.8, direction: 'decrease', description: 'Large portfolio discount available' },
    ],
    llm_analysis: 'The missing flood coverage is a concern that must be addressed. Adding flood will increase total cost by approximately $25-35K but is required for Zone AE compliance. Overall renewal expected in 5-10% range.',
    negotiation_points: [
      'Bundle flood coverage for package discount',
      'Negotiate separate flood policy if better rates available',
      'Highlight excellent maintenance and risk mitigation',
    ],
    calculated_at: '2026-01-01',
    model_used: 'claude-3-opus',
  },
];

// Renewal Timelines with Milestones
export interface RenewalTimelineExtended extends RenewalTimeline {
  summary: {
    total_milestones: number;
    completed: number;
    in_progress: number;
    upcoming: number;
    overdue: number;
  };
}

export const mockRenewalTimelines: RenewalTimelineExtended[] = [
  {
    property_id: 'prop-1',
    expiration_date: '2026-01-20',
    days_until_expiration: 16,
    milestones: [
      {
        name: 'Initial Renewal Notice',
        target_date: '2025-10-22',
        days_before_expiration: 90,
        status: 'completed',
        action_items: ['Review current policy terms', 'Identify coverage gaps'],
        documents_ready: { 'Current Policy': true, 'Loss Runs': true },
      },
      {
        name: 'Gather Documents',
        target_date: '2025-11-21',
        days_before_expiration: 60,
        status: 'completed',
        action_items: ['Collect SOVs', 'Update property valuations', 'Compile loss history'],
        documents_ready: { 'SOV': true, 'Appraisal': false, 'Loss History': true },
      },
      {
        name: 'Request Quotes',
        target_date: '2025-12-21',
        days_before_expiration: 30,
        status: 'overdue',
        action_items: ['Submit to current carrier', 'Request 2-3 competitive quotes', 'Engage broker'],
        documents_ready: { 'Application': false, 'Submission Package': false },
      },
      {
        name: 'Review & Negotiate',
        target_date: '2026-01-06',
        days_before_expiration: 14,
        status: 'upcoming',
        action_items: ['Compare quote options', 'Negotiate terms', 'Select carrier'],
        documents_ready: {},
      },
      {
        name: 'Bind Coverage',
        target_date: '2026-01-13',
        days_before_expiration: 7,
        status: 'upcoming',
        action_items: ['Execute binder', 'Provide payment', 'Confirm coverage in force'],
        documents_ready: {},
      },
    ],
    summary: {
      total_milestones: 5,
      completed: 2,
      in_progress: 0,
      upcoming: 2,
      overdue: 1,
    },
  },
  {
    property_id: 'prop-7',
    expiration_date: '2026-02-08',
    days_until_expiration: 35,
    milestones: [
      {
        name: 'Initial Renewal Notice',
        target_date: '2025-11-10',
        days_before_expiration: 90,
        status: 'completed',
        action_items: ['Review current policy terms', 'Identify coverage gaps'],
        documents_ready: { 'Current Policy': true, 'Loss Runs': true },
      },
      {
        name: 'Gather Documents',
        target_date: '2025-12-10',
        days_before_expiration: 60,
        status: 'completed',
        action_items: ['Collect SOVs', 'Update property valuations'],
        documents_ready: { 'SOV': true, 'Appraisal': true, 'Loss History': true },
      },
      {
        name: 'Request Quotes',
        target_date: '2026-01-09',
        days_before_expiration: 30,
        status: 'in_progress',
        action_items: ['Submit to current carrier', 'Request competitive quotes'],
        documents_ready: { 'Application': true, 'Submission Package': true },
      },
      {
        name: 'Review & Negotiate',
        target_date: '2026-01-25',
        days_before_expiration: 14,
        status: 'upcoming',
        action_items: ['Compare quote options', 'Negotiate terms'],
        documents_ready: {},
      },
      {
        name: 'Bind Coverage',
        target_date: '2026-02-01',
        days_before_expiration: 7,
        status: 'upcoming',
        action_items: ['Execute binder', 'Confirm coverage'],
        documents_ready: {},
      },
    ],
    summary: {
      total_milestones: 5,
      completed: 2,
      in_progress: 1,
      upcoming: 2,
      overdue: 0,
    },
  },
  {
    property_id: 'prop-2',
    expiration_date: '2026-02-18',
    days_until_expiration: 45,
    milestones: [
      {
        name: 'Initial Renewal Notice',
        target_date: '2025-11-20',
        days_before_expiration: 90,
        status: 'completed',
        action_items: ['Review current policy', 'Note flood coverage gap'],
        documents_ready: { 'Current Policy': true, 'Loss Runs': true },
      },
      {
        name: 'Gather Documents',
        target_date: '2025-12-20',
        days_before_expiration: 60,
        status: 'in_progress',
        action_items: ['Collect SOVs', 'Obtain flood zone documentation'],
        documents_ready: { 'SOV': true, 'FEMA Map': true, 'Appraisal': false },
      },
      {
        name: 'Request Quotes',
        target_date: '2026-01-19',
        days_before_expiration: 30,
        status: 'upcoming',
        action_items: ['Submit renewal', 'Include flood coverage request'],
        documents_ready: {},
      },
      {
        name: 'Review & Negotiate',
        target_date: '2026-02-04',
        days_before_expiration: 14,
        status: 'upcoming',
        action_items: ['Compare options', 'Negotiate flood terms'],
        documents_ready: {},
      },
      {
        name: 'Bind Coverage',
        target_date: '2026-02-11',
        days_before_expiration: 7,
        status: 'upcoming',
        action_items: ['Execute binder', 'Confirm flood coverage'],
        documents_ready: {},
      },
    ],
    summary: {
      total_milestones: 5,
      completed: 1,
      in_progress: 1,
      upcoming: 3,
      overdue: 0,
    },
  },
];

// Document Readiness
export interface DocumentReadiness {
  property_id: string;
  property_name: string;
  overall_score: number;
  grade: HealthGrade;
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

export const mockDocumentReadiness: DocumentReadiness[] = [
  {
    property_id: 'prop-1',
    property_name: 'Shoaff Park Apartments',
    overall_score: 65,
    grade: 'D',
    documents: [
      { type: 'current_policy', label: 'Current Policy Declaration', status: 'found', document_id: 'doc-1', filename: 'Shoaff_Policy_2024.pdf', age_days: 340, verified: true },
      { type: 'loss_runs', label: 'Loss Run Report (5yr)', status: 'found', document_id: 'doc-2', filename: 'Loss_Runs_2020-2024.pdf', age_days: 45, verified: true },
      { type: 'sov', label: 'Statement of Values', status: 'found', document_id: 'doc-3', filename: 'SOV_Shoaff_2024.xlsx', age_days: 180, verified: true },
      { type: 'appraisal', label: 'Property Appraisal', status: 'stale', document_id: 'doc-4', filename: 'Appraisal_2022.pdf', age_days: 650, verified: false, issues: ['Appraisal over 18 months old'] },
      { type: 'eop', label: 'Evidence of Property Insurance', status: 'missing', verified: false, issues: ['Required for lender compliance'] },
      { type: 'coi', label: 'Certificate of Insurance', status: 'found', document_id: 'doc-5', filename: 'COI_Current.pdf', age_days: 30, verified: true },
      { type: 'flood_cert', label: 'Flood Zone Determination', status: 'found', document_id: 'doc-6', filename: 'FEMA_Cert.pdf', age_days: 400, verified: true },
    ],
    last_assessed: '2026-01-03',
  },
  {
    property_id: 'prop-7',
    property_name: 'Eastwood Manor',
    overall_score: 90,
    grade: 'A',
    documents: [
      { type: 'current_policy', label: 'Current Policy Declaration', status: 'found', document_id: 'doc-10', filename: 'Eastwood_Policy_2024.pdf', age_days: 300, verified: true },
      { type: 'loss_runs', label: 'Loss Run Report (5yr)', status: 'found', document_id: 'doc-11', filename: 'Loss_Runs_Eastwood.pdf', age_days: 30, verified: true },
      { type: 'sov', label: 'Statement of Values', status: 'found', document_id: 'doc-12', filename: 'SOV_Eastwood_2025.xlsx', age_days: 60, verified: true },
      { type: 'appraisal', label: 'Property Appraisal', status: 'found', document_id: 'doc-13', filename: 'Appraisal_Eastwood_2025.pdf', age_days: 90, verified: true },
      { type: 'coi', label: 'Certificate of Insurance', status: 'missing', verified: false, issues: ['COI needs to be updated'] },
      { type: 'flood_cert', label: 'Flood Zone Determination', status: 'found', document_id: 'doc-14', filename: 'FEMA_Eastwood.pdf', age_days: 365, verified: true },
    ],
    last_assessed: '2026-01-02',
  },
];

// Market Context
export interface MarketContext extends MarketIntelligence {
  id: string;
  property_name: string;
  competitive_position: 'strong' | 'moderate' | 'weak';
  recommended_actions: string[];
}

export const mockMarketContext: MarketContext[] = [
  {
    id: 'market-1',
    property_id: 'prop-1',
    property_name: 'Shoaff Park Apartments',
    rate_trend: 'Increasing',
    rate_change_percent: 6.5,
    key_factors: [
      'Commercial property rates up 5-8% nationally',
      'Indiana market seeing moderate increases',
      'Multi-family sector remains competitive',
      'Reinsurance costs affecting all carriers',
    ],
    carrier_appetite: 'stable',
    carrier_notes: 'Current carrier (Hartford) maintaining appetite for multi-family. Interested in retention but expect rate increase.',
    six_month_forecast: 'Expect continued upward pressure through H1 2026. Consider locking in rates with multi-year policy if available.',
    opportunities: [
      'Multi-year policy for rate stability',
      'Bundle with other portfolio properties',
      'Negotiate deductible buyback options',
      'Explore parametric coverage for specific risks',
    ],
    competitive_position: 'moderate',
    recommended_actions: [
      'Engage 2-3 alternative carriers for quotes',
      'Prepare comprehensive submission with loss control improvements',
      'Consider higher deductible for rate reduction',
    ],
    sources: ['MarketScout Commercial Index', 'CIAB Q4 2025 Report', 'Carrier Appetite Survey'],
    fetched_at: '2026-01-03',
  },
  {
    id: 'market-2',
    property_id: 'prop-7',
    property_name: 'Eastwood Manor',
    rate_trend: 'Stable to Increasing',
    rate_change_percent: 4.2,
    key_factors: [
      'Clean loss history supports favorable positioning',
      'Recent property improvements reduce risk profile',
      'Strong carrier relationships in place',
    ],
    carrier_appetite: 'growing',
    carrier_notes: 'Multiple carriers showing interest due to favorable risk profile. Good opportunity for competitive bidding.',
    six_month_forecast: 'Flat to modest increases expected. Strong negotiating position given property fundamentals.',
    opportunities: [
      'Leverage clean loss history for credits',
      'Request enhanced coverage at flat premium',
      'Explore additional coverage options (cyber, E&O)',
    ],
    competitive_position: 'strong',
    recommended_actions: [
      'Request early renewal with current carrier',
      'Document recent improvements for underwriting',
      'Negotiate multi-year commitment for rate lock',
    ],
    sources: ['MarketScout Commercial Index', 'Carrier Discussions'],
    fetched_at: '2026-01-02',
  },
];

// Policy Comparison (YoY)
export interface PolicyComparison {
  property_id: string;
  property_name: string;
  current_policy: {
    policy_number: string;
    effective_date: string;
    expiration_date: string;
    premium: number;
    carrier: string;
    coverages: Array<{
      type: string;
      limit: number;
      deductible: number;
    }>;
  };
  prior_policy: {
    policy_number: string;
    effective_date: string;
    expiration_date: string;
    premium: number;
    carrier: string;
    coverages: Array<{
      type: string;
      limit: number;
      deductible: number;
    }>;
  };
  changes: Array<{
    field: string;
    prior_value: string;
    current_value: string;
    change_type: 'increase' | 'decrease' | 'same' | 'new' | 'removed';
    impact: 'positive' | 'negative' | 'neutral';
  }>;
  premium_change_pct: number;
}

export const mockPolicyComparisons: PolicyComparison[] = [
  {
    property_id: 'prop-1',
    property_name: 'Shoaff Park Apartments',
    current_policy: {
      policy_number: 'PROP-2024-001',
      effective_date: '2025-01-20',
      expiration_date: '2026-01-20',
      premium: 285000,
      carrier: 'Hartford',
      coverages: [
        { type: 'Property', limit: 30400000, deductible: 912000 },
        { type: 'General Liability', limit: 1000000, deductible: 0 },
        { type: 'Umbrella', limit: 5000000, deductible: 10000 },
      ],
    },
    prior_policy: {
      policy_number: 'PROP-2023-001',
      effective_date: '2024-01-20',
      expiration_date: '2025-01-20',
      premium: 265000,
      carrier: 'Hartford',
      coverages: [
        { type: 'Property', limit: 29000000, deductible: 580000 },
        { type: 'General Liability', limit: 1000000, deductible: 0 },
        { type: 'Umbrella', limit: 5000000, deductible: 10000 },
      ],
    },
    changes: [
      { field: 'Premium', prior_value: '$265,000', current_value: '$285,000', change_type: 'increase', impact: 'negative' },
      { field: 'Property Limit', prior_value: '$29,000,000', current_value: '$30,400,000', change_type: 'increase', impact: 'positive' },
      { field: 'Property Deductible', prior_value: '2% ($580K)', current_value: '3% ($912K)', change_type: 'increase', impact: 'negative' },
      { field: 'GL Limit', prior_value: '$1,000,000', current_value: '$1,000,000', change_type: 'same', impact: 'neutral' },
      { field: 'Umbrella Limit', prior_value: '$5,000,000', current_value: '$5,000,000', change_type: 'same', impact: 'neutral' },
    ],
    premium_change_pct: 7.5,
  },
];

// Portfolio Renewal Summary
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

export const mockPortfolioRenewalSummary: PortfolioRenewalSummary = {
  total_properties: 7,
  total_upcoming_renewals: 4,
  total_premium_at_risk: 1357000,
  by_urgency: {
    critical: 1,
    warning: 2,
    info: 1,
  },
  by_status: {
    on_track: 2,
    needs_attention: 1,
    overdue: 1,
  },
  avg_forecast_change_pct: 7.8,
  projected_total_premium: 1463000,
};
