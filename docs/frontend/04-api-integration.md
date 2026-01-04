# API Integration

Complete guide to data fetching with React Query, API client setup, TypeScript types, and real-time features.

---

## Setup & Configuration

### Install Dependencies

```bash
npm install @tanstack/react-query @tanstack/react-query-devtools
```

### Query Client Configuration

```tsx
// lib/query-client.ts
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Data considered fresh for 5 minutes
      staleTime: 1000 * 60 * 5,
      // Keep unused data in cache for 30 minutes
      gcTime: 1000 * 60 * 30,
      // Retry failed requests 3 times
      retry: 3,
      // Don't refetch when window regains focus (can be noisy)
      refetchOnWindowFocus: false,
      // Refetch when network reconnects
      refetchOnReconnect: true,
    },
    mutations: {
      // Retry mutations once
      retry: 1,
    },
  },
});
```

### Provider Setup

```tsx
// components/Providers.tsx
'use client';

import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { queryClient } from '@/lib/query-client';

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
```

---

## API Client

### Base Client

```tsx
// lib/api/client.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/v1';

export class APIError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public details?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'APIError';
  }
}

interface APIResponse<T> {
  success: boolean;
  data: T;
  pagination?: {
    page: number;
    page_size: number;
    total_items: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
  meta: {
    request_id: string;
    timestamp: string;
  };
}

interface APIErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
  meta: {
    request_id: string;
    timestamp: string;
  };
}

export async function apiClient<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  const json = await response.json();

  if (!response.ok || !json.success) {
    const error = json as APIErrorResponse;
    throw new APIError(
      response.status,
      error.error?.code || 'UNKNOWN_ERROR',
      error.error?.message || 'An unknown error occurred',
      error.error?.details
    );
  }

  return (json as APIResponse<T>).data;
}

// Convenience methods
export const api = {
  get: <T>(endpoint: string) => apiClient<T>(endpoint, { method: 'GET' }),

  post: <T>(endpoint: string, body?: unknown) =>
    apiClient<T>(endpoint, {
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    }),

  put: <T>(endpoint: string, body: unknown) =>
    apiClient<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(body),
    }),

  patch: <T>(endpoint: string, body: unknown) =>
    apiClient<T>(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),

  delete: <T>(endpoint: string) =>
    apiClient<T>(endpoint, { method: 'DELETE' }),
};
```

---

## TypeScript Types

### Core Types

```tsx
// types/api.ts

// ============ COMMON ============
export type Severity = 'critical' | 'warning' | 'info';
export type GapStatus = 'open' | 'acknowledged' | 'resolved';
export type GapType =
  | 'underinsurance'
  | 'missing_coverage'
  | 'high_deductible'
  | 'expiring'
  | 'non_compliant'
  | 'outdated_valuation'
  | 'missing_document';

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
```

---

## Query Hooks

### Dashboard Hooks

```tsx
// hooks/queries/useDashboard.ts
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api/client';
import type { DashboardSummary, ExpirationItem, Alert } from '@/types/api';

export const dashboardKeys = {
  all: ['dashboard'] as const,
  summary: () => [...dashboardKeys.all, 'summary'] as const,
  expirations: (days: number) => [...dashboardKeys.all, 'expirations', days] as const,
  alerts: (filters?: AlertFilters) => [...dashboardKeys.all, 'alerts', filters] as const,
};

export function useDashboardSummary() {
  return useQuery({
    queryKey: dashboardKeys.summary(),
    queryFn: () => api.get<DashboardSummary>('/dashboard/summary'),
  });
}

export function useExpirations(daysAhead = 90) {
  return useQuery({
    queryKey: dashboardKeys.expirations(daysAhead),
    queryFn: () =>
      api.get<ExpirationItem[]>(`/dashboard/expirations?days_ahead=${daysAhead}`),
  });
}

interface AlertFilters {
  severity?: Severity;
  type?: string;
  acknowledged?: boolean;
}

export function useAlerts(filters?: AlertFilters) {
  const params = new URLSearchParams();
  if (filters?.severity) params.set('severity', filters.severity);
  if (filters?.type) params.set('type', filters.type);
  if (filters?.acknowledged !== undefined)
    params.set('acknowledged', String(filters.acknowledged));

  return useQuery({
    queryKey: dashboardKeys.alerts(filters),
    queryFn: () => api.get<Alert[]>(`/dashboard/alerts?${params}`),
  });
}
```

### Property Hooks

```tsx
// hooks/queries/useProperties.ts
import { useQuery, useInfiniteQuery } from '@tanstack/react-query';
import { api } from '@/lib/api/client';
import type { Property, PropertyDetail } from '@/types/api';

export const propertyKeys = {
  all: ['properties'] as const,
  lists: () => [...propertyKeys.all, 'list'] as const,
  list: (filters?: PropertyFilters) => [...propertyKeys.lists(), filters] as const,
  details: () => [...propertyKeys.all, 'detail'] as const,
  detail: (id: string) => [...propertyKeys.details(), id] as const,
  policies: (id: string) => [...propertyKeys.detail(id), 'policies'] as const,
  documents: (id: string) => [...propertyKeys.detail(id), 'documents'] as const,
};

interface PropertyFilters {
  search?: string;
  property_type?: string;
  min_health_score?: number;
  max_health_score?: number;
  has_gaps?: boolean;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export function useProperties(filters?: PropertyFilters) {
  const params = new URLSearchParams();
  if (filters?.search) params.set('search', filters.search);
  if (filters?.property_type) params.set('property_type', filters.property_type);
  if (filters?.sort_by) params.set('sort_by', filters.sort_by);
  if (filters?.sort_order) params.set('sort_order', filters.sort_order);

  return useQuery({
    queryKey: propertyKeys.list(filters),
    queryFn: () => api.get<Property[]>(`/properties?${params}`),
  });
}

export function useProperty(id: string) {
  return useQuery({
    queryKey: propertyKeys.detail(id),
    queryFn: () => api.get<PropertyDetail>(`/properties/${id}`),
    enabled: !!id,
  });
}

export function usePropertyPolicies(propertyId: string) {
  return useQuery({
    queryKey: propertyKeys.policies(propertyId),
    queryFn: () => api.get<PolicySummary[]>(`/properties/${propertyId}/policies`),
    enabled: !!propertyId,
  });
}
```

### Health Score Hooks

```tsx
// hooks/queries/useHealthScore.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api/client';
import type { HealthScore, HealthScoreHistory } from '@/types/api';
import { propertyKeys } from './useProperties';

export const healthScoreKeys = {
  all: ['health-score'] as const,
  property: (id: string) => [...healthScoreKeys.all, 'property', id] as const,
  history: (id: string) => [...healthScoreKeys.property(id), 'history'] as const,
  portfolio: () => [...healthScoreKeys.all, 'portfolio'] as const,
};

export function useHealthScore(propertyId: string) {
  return useQuery({
    queryKey: healthScoreKeys.property(propertyId),
    queryFn: () => api.get<HealthScore>(`/health-score/properties/${propertyId}`),
    enabled: !!propertyId,
  });
}

export function useHealthScoreHistory(propertyId: string, days = 90) {
  return useQuery({
    queryKey: healthScoreKeys.history(propertyId),
    queryFn: () =>
      api.get<HealthScoreHistory>(
        `/health-score/properties/${propertyId}/history?days=${days}`
      ),
    enabled: !!propertyId,
  });
}

export function useRecalculateHealthScore() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (propertyId: string) =>
      api.post<HealthScore>(`/health-score/properties/${propertyId}/recalculate`),
    onSuccess: (data, propertyId) => {
      queryClient.setQueryData(healthScoreKeys.property(propertyId), data);
      queryClient.invalidateQueries({ queryKey: propertyKeys.detail(propertyId) });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
}
```

### Gap Hooks

```tsx
// hooks/queries/useGaps.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api/client';
import type { Gap, GapAnalysis, Severity, GapStatus, GapType } from '@/types/api';

export const gapKeys = {
  all: ['gaps'] as const,
  lists: () => [...gapKeys.all, 'list'] as const,
  list: (filters?: GapFilters) => [...gapKeys.lists(), filters] as const,
  details: () => [...gapKeys.all, 'detail'] as const,
  detail: (id: string) => [...gapKeys.details(), id] as const,
  analysis: (id: string) => [...gapKeys.detail(id), 'analysis'] as const,
  property: (propertyId: string) => [...gapKeys.all, 'property', propertyId] as const,
};

interface GapFilters {
  property_id?: string;
  severity?: Severity;
  status?: GapStatus;
  gap_type?: GapType;
}

export function useGaps(filters?: GapFilters) {
  const params = new URLSearchParams();
  if (filters?.property_id) params.set('property_id', filters.property_id);
  if (filters?.severity) params.set('severity', filters.severity);
  if (filters?.status) params.set('status', filters.status);
  if (filters?.gap_type) params.set('gap_type', filters.gap_type);

  return useQuery({
    queryKey: gapKeys.list(filters),
    queryFn: () => api.get<Gap[]>(`/gaps?${params}`),
  });
}

export function useGap(id: string) {
  return useQuery({
    queryKey: gapKeys.detail(id),
    queryFn: () => api.get<Gap>(`/gaps/${id}`),
    enabled: !!id,
  });
}

export function useGapAnalysis(gapId: string) {
  return useQuery({
    queryKey: gapKeys.analysis(gapId),
    queryFn: () => api.post<GapAnalysis>(`/gaps/${gapId}/analyze`),
    enabled: !!gapId,
    staleTime: Infinity, // Analysis doesn't change
  });
}

export function useAcknowledgeGap() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ gapId, notes }: { gapId: string; notes?: string }) =>
      api.post<Gap>(`/gaps/${gapId}/acknowledge`, { notes }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: gapKeys.all });
      queryClient.invalidateQueries({ queryKey: ['dashboard', 'alerts'] });
    },
  });
}

export function useResolveGap() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ gapId, notes }: { gapId: string; notes?: string }) =>
      api.post<Gap>(`/gaps/${gapId}/resolve`, { notes }),
    onSuccess: (_, { gapId }) => {
      queryClient.invalidateQueries({ queryKey: gapKeys.all });
      queryClient.invalidateQueries({ queryKey: ['health-score'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
}

export function useTriggerGapDetection() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (propertyId?: string) =>
      api.post<{ gaps_found: number }>('/gaps/detect', { property_id: propertyId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: gapKeys.all });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
}
```

### Renewal Hooks

```tsx
// hooks/queries/useRenewals.ts
import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '@/lib/api/client';
import type {
  RenewalForecast,
  RenewalTimeline,
  MarketIntelligence,
} from '@/types/api';

export const renewalKeys = {
  all: ['renewals'] as const,
  forecast: (propertyId: string) => [...renewalKeys.all, 'forecast', propertyId] as const,
  timeline: (propertyId: string) => [...renewalKeys.all, 'timeline', propertyId] as const,
  market: (propertyId: string) => [...renewalKeys.all, 'market', propertyId] as const,
  readiness: (propertyId: string) => [...renewalKeys.all, 'readiness', propertyId] as const,
};

export function useRenewalForecast(propertyId: string) {
  return useQuery({
    queryKey: renewalKeys.forecast(propertyId),
    queryFn: () => api.get<RenewalForecast>(`/renewals/forecast/${propertyId}`),
    enabled: !!propertyId,
  });
}

export function useRenewalTimeline(propertyId: string) {
  return useQuery({
    queryKey: renewalKeys.timeline(propertyId),
    queryFn: () => api.get<RenewalTimeline>(`/renewals/timeline/${propertyId}`),
    enabled: !!propertyId,
  });
}

export function useMarketIntelligence(propertyId: string) {
  return useQuery({
    queryKey: renewalKeys.market(propertyId),
    queryFn: () =>
      api.get<MarketIntelligence>(`/enrichment/market-intelligence/${propertyId}`),
    enabled: !!propertyId,
    staleTime: 1000 * 60 * 60 * 2, // 2 hours - market data is expensive
  });
}

export function useRefreshMarketIntelligence() {
  return useMutation({
    mutationFn: (propertyId: string) =>
      api.post<MarketIntelligence>(`/enrichment/market-intelligence/${propertyId}/refresh`),
  });
}

export function useGenerateBrokerPackage() {
  return useMutation({
    mutationFn: ({
      propertyId,
      options,
    }: {
      propertyId: string;
      options?: { include_loss_runs?: boolean; custom_notes?: string };
    }) =>
      api.post<{ package_id: string; download_url: string }>(
        `/renewals/${propertyId}/package`,
        options
      ),
  });
}
```

### Chat Hooks (with Streaming)

```tsx
// hooks/queries/useChat.ts
import { useState, useCallback, useRef } from 'react';
import type { ChatMessage, ChatSource } from '@/types/api';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/v1';

interface UseChatOptions {
  onError?: (error: Error) => void;
}

export function useChat(options?: UseChatOptions) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(
    async (content: string, propertyId?: string) => {
      // Add user message immediately
      const userMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'user',
        content,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);

      // Create placeholder for assistant message
      const assistantMessageId = crypto.randomUUID();
      const assistantMessage: ChatMessage = {
        id: assistantMessageId,
        role: 'assistant',
        content: '',
        sources: [],
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMessage]);

      setIsStreaming(true);
      abortControllerRef.current = new AbortController();

      try {
        const response = await fetch(`${API_BASE}/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: content,
            conversation_id: conversationId,
            property_id: propertyId,
            stream: true,
          }),
          signal: abortControllerRef.current.signal,
        });

        if (!response.ok) {
          throw new Error(`Chat request failed: ${response.status}`);
        }

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        if (!reader) {
          throw new Error('No response body');
        }

        let fullContent = '';
        let sources: ChatSource[] = [];

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6);

              if (data === '[DONE]') {
                continue;
              }

              try {
                const parsed = JSON.parse(data);

                if (parsed.type === 'content') {
                  fullContent += parsed.content;
                  setMessages((prev) =>
                    prev.map((m) =>
                      m.id === assistantMessageId
                        ? { ...m, content: fullContent }
                        : m
                    )
                  );
                } else if (parsed.type === 'sources') {
                  sources = parsed.sources;
                  setMessages((prev) =>
                    prev.map((m) =>
                      m.id === assistantMessageId ? { ...m, sources } : m
                    )
                  );
                } else if (parsed.type === 'conversation_id') {
                  setConversationId(parsed.conversation_id);
                }
              } catch {
                // Ignore parse errors for incomplete chunks
              }
            }
          }
        }
      } catch (error) {
        if ((error as Error).name === 'AbortError') {
          // User cancelled
          return;
        }
        options?.onError?.(error as Error);
        // Remove the empty assistant message on error
        setMessages((prev) => prev.filter((m) => m.id !== assistantMessageId));
      } finally {
        setIsStreaming(false);
        abortControllerRef.current = null;
      }
    },
    [conversationId, options]
  );

  const stopStreaming = useCallback(() => {
    abortControllerRef.current?.abort();
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setConversationId(null);
  }, []);

  return {
    messages,
    isStreaming,
    conversationId,
    sendMessage,
    stopStreaming,
    clearMessages,
  };
}
```

### Document Upload Hook

```tsx
// hooks/mutations/useDocumentUpload.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api/client';

interface UploadProgress {
  stage: 'initiating' | 'uploading' | 'processing' | 'complete' | 'error';
  progress: number;
  message: string;
}

interface UseDocumentUploadOptions {
  onProgress?: (progress: UploadProgress) => void;
}

export function useDocumentUpload(options?: UseDocumentUploadOptions) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      file,
      propertyId,
    }: {
      file: File;
      propertyId: string;
    }) => {
      // Step 1: Initiate upload
      options?.onProgress?.({
        stage: 'initiating',
        progress: 10,
        message: 'Preparing upload...',
      });

      const initResponse = await api.post<{
        document_id: string;
        upload_url: string;
        upload_headers: Record<string, string>;
      }>('/documents/initiate-upload', {
        filename: file.name,
        content_type: file.type,
        file_size_bytes: file.size,
        property_id: propertyId,
      });

      // Step 2: Upload to S3
      options?.onProgress?.({
        stage: 'uploading',
        progress: 30,
        message: 'Uploading file...',
      });

      await fetch(initResponse.upload_url, {
        method: 'PUT',
        body: file,
        headers: initResponse.upload_headers,
      });

      // Step 3: Complete upload and trigger processing
      options?.onProgress?.({
        stage: 'processing',
        progress: 60,
        message: 'Processing document...',
      });

      await api.post(`/documents/${initResponse.document_id}/complete-upload`, {
        file_size_bytes: file.size,
      });

      // Step 4: Poll for completion
      let attempts = 0;
      const maxAttempts = 60; // 5 minutes max

      while (attempts < maxAttempts) {
        const doc = await api.get<{ status: string }>(
          `/documents/${initResponse.document_id}`
        );

        if (doc.status === 'completed') {
          options?.onProgress?.({
            stage: 'complete',
            progress: 100,
            message: 'Document processed successfully!',
          });
          return initResponse.document_id;
        }

        if (doc.status === 'failed') {
          throw new Error('Document processing failed');
        }

        options?.onProgress?.({
          stage: 'processing',
          progress: 60 + (attempts / maxAttempts) * 35,
          message: 'Extracting information...',
        });

        await new Promise((resolve) => setTimeout(resolve, 5000));
        attempts++;
      }

      throw new Error('Document processing timed out');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      queryClient.invalidateQueries({ queryKey: ['completeness'] });
      queryClient.invalidateQueries({ queryKey: ['health-score'] });
    },
    onError: () => {
      options?.onProgress?.({
        stage: 'error',
        progress: 0,
        message: 'Upload failed. Please try again.',
      });
    },
  });
}
```

---

## Error Handling

### Global Error Handler

```tsx
// lib/api/error-handler.ts
import { toast } from 'sonner';
import { APIError } from './client';

export function handleAPIError(error: unknown) {
  if (error instanceof APIError) {
    switch (error.status) {
      case 400:
        toast.error('Invalid request', { description: error.message });
        break;
      case 401:
        toast.error('Session expired', { description: 'Please refresh the page' });
        break;
      case 403:
        toast.error('Access denied', { description: error.message });
        break;
      case 404:
        toast.error('Not found', { description: error.message });
        break;
      case 429:
        toast.error('Too many requests', { description: 'Please slow down' });
        break;
      case 500:
      case 502:
      case 503:
        toast.error('Server error', {
          description: 'Please try again in a moment',
        });
        break;
      default:
        toast.error('Something went wrong', { description: error.message });
    }
  } else if (error instanceof Error) {
    toast.error('Error', { description: error.message });
  } else {
    toast.error('An unexpected error occurred');
  }
}
```

### Query Error Boundary

```tsx
// components/shared/QueryErrorBoundary.tsx
import { useQueryErrorResetBoundary } from '@tanstack/react-query';
import { ErrorBoundary } from 'react-error-boundary';
import { Button } from '@/components/primitives/Button';

function ErrorFallback({
  error,
  resetErrorBoundary,
}: {
  error: Error;
  resetErrorBoundary: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center">
      <div className="text-6xl mb-4">😵</div>
      <h2 className="text-xl font-semibold text-gray-900 mb-2">
        Something went wrong
      </h2>
      <p className="text-gray-600 mb-4">{error.message}</p>
      <Button onClick={resetErrorBoundary}>Try again</Button>
    </div>
  );
}

export function QueryErrorBoundary({ children }: { children: React.ReactNode }) {
  const { reset } = useQueryErrorResetBoundary();

  return (
    <ErrorBoundary FallbackComponent={ErrorFallback} onReset={reset}>
      {children}
    </ErrorBoundary>
  );
}
```

---

## Optimistic Updates

### Example: Acknowledge Gap

```tsx
export function useAcknowledgeGap() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ gapId, notes }: { gapId: string; notes?: string }) =>
      api.post<Gap>(`/gaps/${gapId}/acknowledge`, { notes }),

    // Optimistic update
    onMutate: async ({ gapId }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: gapKeys.all });

      // Snapshot previous value
      const previousGaps = queryClient.getQueryData(gapKeys.lists());

      // Optimistically update
      queryClient.setQueriesData<Gap[]>({ queryKey: gapKeys.lists() }, (old) =>
        old?.map((gap) =>
          gap.id === gapId
            ? { ...gap, status: 'acknowledged' as const }
            : gap
        )
      );

      return { previousGaps };
    },

    // Rollback on error
    onError: (err, variables, context) => {
      if (context?.previousGaps) {
        queryClient.setQueryData(gapKeys.lists(), context.previousGaps);
      }
      handleAPIError(err);
    },

    // Always refetch after success or error
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: gapKeys.all });
    },

    onSuccess: () => {
      toast.success('Gap acknowledged');
    },
  });
}
```

---

## Prefetching

### Prefetch on Hover

```tsx
// components/features/properties/PropertyCard.tsx
import { useQueryClient } from '@tanstack/react-query';
import { propertyKeys } from '@/hooks/queries/useProperties';
import { api } from '@/lib/api/client';

export function PropertyCard({ property }: { property: Property }) {
  const queryClient = useQueryClient();

  const prefetchProperty = () => {
    queryClient.prefetchQuery({
      queryKey: propertyKeys.detail(property.id),
      queryFn: () => api.get<PropertyDetail>(`/properties/${property.id}`),
      staleTime: 1000 * 60 * 5, // 5 minutes
    });
  };

  return (
    <Link
      href={`/properties/${property.id}`}
      onMouseEnter={prefetchProperty}
      onFocus={prefetchProperty}
    >
      {/* Card content */}
    </Link>
  );
}
```

### Prefetch on Route Load

```tsx
// app/properties/[id]/page.tsx
import { dehydrate, HydrationBoundary, QueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api/client';
import { propertyKeys } from '@/hooks/queries/useProperties';
import { healthScoreKeys } from '@/hooks/queries/useHealthScore';

export default async function PropertyPage({ params }: { params: { id: string } }) {
  const queryClient = new QueryClient();

  // Prefetch in parallel
  await Promise.all([
    queryClient.prefetchQuery({
      queryKey: propertyKeys.detail(params.id),
      queryFn: () => api.get(`/properties/${params.id}`),
    }),
    queryClient.prefetchQuery({
      queryKey: healthScoreKeys.property(params.id),
      queryFn: () => api.get(`/health-score/properties/${params.id}`),
    }),
  ]);

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <PropertyDetailClient propertyId={params.id} />
    </HydrationBoundary>
  );
}
```

---

## Next Steps

Continue to [05-animations-interactions.md](./05-animations-interactions.md) for Framer Motion patterns and micro-interactions.
