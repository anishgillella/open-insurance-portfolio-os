'use client';

import { use, useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import {
  ArrowLeft,
  ArrowLeftRight,
  Building2,
  Calendar,
  Clock,
  ChevronRight,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Play,
  Loader2,
  RefreshCw,
  TrendingUp,
  FileText,
} from 'lucide-react';
import { cn, formatCurrency, formatDate } from '@/lib/utils';
import { Card, Badge, Button } from '@/components/primitives';
import { GlassCard, StatusBadge, GradientProgress } from '@/components/patterns';
import {
  RenewalForecastCard,
  ReadinessChecklist,
  MarketContextPanel,
  RenewalAlertsList,
  AlertConfigModal,
  PolicyComparison,
} from '@/components/features/renewals';
import { MarketIntelligenceCard } from '@/components/features/enrichment';
import {
  propertiesApi,
  renewalsApi,
  type PropertyDetail,
  type RenewalForecast,
  type RenewalAlert,
  type DocumentReadiness as ApiDocumentReadiness,
  type MarketContext as ApiMarketContext,
} from '@/lib/api';
import {
  mockRenewalTimelines,
  mockPolicyComparisons,
  mockAlertConfigs,
} from '@/lib/mock-data';
import type { AlertConfig, DocumentReadiness, MarketContext } from '@/types/api';

interface PageProps {
  params: Promise<{ id: string }>;
}

const milestoneStatusIcons = {
  completed: CheckCircle,
  in_progress: Play,
  upcoming: Clock,
  overdue: XCircle,
};

const milestoneStatusColors = {
  completed: 'text-[var(--color-success-500)] bg-[var(--color-success-50)] dark:bg-[var(--color-success-500)]/10',
  in_progress: 'text-[var(--color-primary-500)] bg-[var(--color-primary-50)] dark:bg-[var(--color-primary-500)]/10',
  upcoming: 'text-[var(--color-text-muted)] bg-[var(--color-surface-sunken)]',
  overdue: 'text-[var(--color-critical-500)] bg-[var(--color-critical-50)] dark:bg-[var(--color-critical-500)]/10',
};

export default function PropertyRenewalsPage({ params }: PageProps) {
  const { id } = use(params);
  const [activeTab, setActiveTab] = useState<'overview' | 'forecast' | 'documents' | 'market' | 'comparison'>('overview');
  const [configModalOpen, setConfigModalOpen] = useState(false);

  // State for API data
  const [property, setProperty] = useState<PropertyDetail | null>(null);
  const [forecast, setForecast] = useState<RenewalForecast | null>(null);
  const [alerts, setAlerts] = useState<RenewalAlert[]>([]);
  const [readiness, setReadiness] = useState<DocumentReadiness | null>(null);
  const [marketContext, setMarketContext] = useState<MarketContext | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Mock data for features not yet in API
  const timeline = mockRenewalTimelines.find((t) => t.property_id === id);
  const comparison = mockPolicyComparisons.find((c) => c.property_id === id);
  const alertConfig = mockAlertConfigs.find((c) => c.property_id === id);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      // Fetch property details from real API
      const propertyData = await propertiesApi.get(id);
      setProperty(propertyData);

      // Try to fetch forecast (may not exist)
      try {
        const forecastData = await renewalsApi.getForecast(id);
        setForecast(forecastData);
      } catch {
        // Property may not have a forecast yet
        setForecast(null);
      }

      // Fetch alerts for this property
      try {
        const alertsData = await renewalsApi.getAlerts(id);
        const alertsArray = Array.isArray(alertsData) ? alertsData :
          (alertsData as { alerts?: RenewalAlert[] })?.alerts || [];
        setAlerts(alertsArray);
      } catch {
        setAlerts([]);
      }

      // Fetch document readiness
      try {
        const readinessData = await renewalsApi.getReadiness(id);
        console.log('Raw readiness data from API:', readinessData);
        // Map API response to component expected type
        // Backend returns required_documents and recommended_documents separately
        // Frontend component expects a single documents array
        const apiResponse = readinessData as unknown as {
          property_id: string;
          property_name: string;
          readiness_score: number;
          readiness_grade: string;
          required_documents: Array<{
            type: string;
            label: string;
            status: string;
            document_id?: string;
            filename?: string;
            age_days?: number;
            verified: boolean;
            issues?: string[];
          }>;
          recommended_documents: Array<{
            type: string;
            label: string;
            status: string;
            document_id?: string;
            filename?: string;
            age_days?: number;
            verified: boolean;
            issues?: string[];
          }>;
          last_assessed?: string;
        };

        // Combine required and recommended documents into single array
        const allDocuments = [
          ...(apiResponse.required_documents || []),
          ...(apiResponse.recommended_documents || []),
        ];

        const mappedReadiness = {
          property_id: apiResponse.property_id,
          property_name: apiResponse.property_name,
          overall_score: apiResponse.readiness_score,
          grade: apiResponse.readiness_grade as 'A' | 'B' | 'C' | 'D' | 'F',
          documents: allDocuments.map(doc => ({
            type: doc.type,
            label: doc.label,
            status: doc.status as 'found' | 'missing' | 'stale' | 'not_applicable',
            document_id: doc.document_id,
            filename: doc.filename,
            age_days: doc.age_days,
            verified: doc.verified,
            issues: doc.issues,
          })),
          last_assessed: apiResponse.last_assessed || new Date().toISOString(),
        };
        console.log('Setting readiness:', mappedReadiness);
        setReadiness(mappedReadiness);
      } catch (err) {
        console.error('Error fetching readiness:', err);
        setReadiness(null);
      }

      // Fetch market context
      try {
        const marketData = await renewalsApi.getMarketContext(id);
        // Map API response to component expected type
        setMarketContext({
          ...marketData,
          id: marketData.property_id,
          competitive_position: marketData.competitive_position || 'moderate',
          recommended_actions: marketData.recommended_actions || [],
        } as MarketContext);
      } catch {
        setMarketContext(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load property data');
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 text-[var(--color-primary-500)] animate-spin" />
      </div>
    );
  }

  if (error || !property) {
    return (
      <div className="text-center py-16">
        <Building2 className="h-12 w-12 text-[var(--color-text-muted)] mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-2">
          {error || 'Property not found'}
        </h3>
        <div className="flex items-center justify-center gap-3">
          <Link href="/renewals">
            <Button variant="secondary">Back to renewals</Button>
          </Link>
          {error && (
            <Button variant="secondary" onClick={fetchData}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Try Again
            </Button>
          )}
        </div>
      </div>
    );
  }

  // Calculate days until expiration from property's insurance_summary
  const nextExpiration = property.insurance_summary?.next_expiration;
  const daysUntilExpiration = property.insurance_summary?.days_until_expiration ??
    (nextExpiration
      ? Math.ceil((new Date(nextExpiration).getTime() - Date.now()) / (1000 * 60 * 60 * 24))
      : null);
  const totalPremium = typeof property.insurance_summary?.total_annual_premium === 'number'
    ? property.insurance_summary.total_annual_premium
    : parseFloat(property.insurance_summary?.total_annual_premium || '0');

  const severity =
    (daysUntilExpiration || 999) <= 30
      ? 'critical'
      : (daysUntilExpiration || 999) <= 60
      ? 'warning'
      : 'info';

  const handleAcknowledge = (alertId: string) => {
    setAlerts((prev) =>
      prev.map((a) =>
        a.id === alertId
          ? { ...a, status: 'acknowledged' as const, acknowledged_at: new Date().toISOString() }
          : a
      )
    );
  };

  const handleResolve = (alertId: string) => {
    setAlerts((prev) =>
      prev.map((a) =>
        a.id === alertId
          ? { ...a, status: 'resolved' as const, resolved_at: new Date().toISOString() }
          : a
      )
    );
  };

  const handleSaveConfig = (config: AlertConfig) => {
    console.log('Saving config:', config);
    setConfigModalOpen(false);
  };

  return (
    <div className="space-y-6">
      {/* Back Link */}
      <div>
        <Link
          href="/renewals"
          className="inline-flex items-center gap-2 text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to renewals
        </Link>
      </div>

      {/* Hero Header */}
      <div>
        <GlassCard className="p-8" gradient="from-primary-500 to-primary-600" hover={false}>
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
            {/* Property Info */}
            <div className="flex items-start gap-6">
              <div
                className={cn(
                  'w-20 h-20 rounded-2xl flex flex-col items-center justify-center text-white',
                  severity === 'critical'
                    ? 'bg-[var(--color-critical-500)]'
                    : severity === 'warning'
                    ? 'bg-[var(--color-warning-500)]'
                    : 'bg-[var(--color-primary-500)]'
                )}
              >
                <span className="text-2xl font-bold">{daysUntilExpiration ?? '?'}</span>
                <span className="text-xs opacity-80">days</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">
                  {property.name}
                </h1>
                <p className="text-[var(--color-text-secondary)] flex items-center gap-2 mt-1">
                  <Calendar className="h-4 w-4" />
                  Renewal Planning
                </p>
                <div className="flex items-center gap-3 mt-3">
                  <StatusBadge severity={severity} label={severity} pulse={severity === 'critical'} />
                  <span className="text-sm text-[var(--color-text-muted)]">
                    Expires {nextExpiration || 'N/A'}
                  </span>
                </div>
              </div>
            </div>

            {/* Quick Stats */}
            <div className="flex items-center gap-8">
              <div className="text-center">
                <p className="text-sm text-[var(--color-text-muted)]">Current Premium</p>
                <p className="text-2xl font-bold text-[var(--color-text-primary)]">
                  {formatCurrency(totalPremium)}
                </p>
              </div>
              <div className="h-12 w-px bg-[var(--color-border-subtle)]" />
              {forecast?.forecast && (
                <>
                  <div className="text-center">
                    <p className="text-sm text-[var(--color-text-muted)]">Forecast (Mid)</p>
                    <p className="text-2xl font-bold text-[var(--color-text-primary)]">
                      {formatCurrency(forecast.forecast.mid)}
                    </p>
                  </div>
                  <div className="h-12 w-px bg-[var(--color-border-subtle)]" />
                  <div className="text-center">
                    <p className="text-sm text-[var(--color-text-muted)]">Est. Change</p>
                    <p
                      className={cn(
                        'text-2xl font-bold',
                        (forecast.forecast.mid_change_percent ?? 0) >= 0
                          ? 'text-[var(--color-critical-500)]'
                          : 'text-[var(--color-success-500)]'
                      )}
                    >
                      {(forecast.forecast.mid_change_percent ?? 0) >= 0 ? '+' : ''}
                      {(forecast.forecast.mid_change_percent ?? 0).toFixed(1)}%
                    </p>
                  </div>
                </>
              )}
            </div>
          </div>
        </GlassCard>
      </div>

      {/* Tab Navigation */}
      <div>
        <div className="flex items-center gap-2 overflow-x-auto pb-2">
          {[
            { id: 'overview', label: 'Overview' },
            { id: 'forecast', label: 'Forecast Details' },
            { id: 'documents', label: 'Document Readiness' },
            { id: 'market', label: 'Market Intelligence' },
            { id: 'comparison', label: 'YoY Comparison' },
          ].map((tab) => (
            <Button
              key={tab.id}
              variant={activeTab === tab.id ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => setActiveTab(tab.id as typeof activeTab)}
            >
              {tab.label}
            </Button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Timeline & Milestones */}
          <div className="lg:col-span-2">
            <Card padding="lg">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">
                  Renewal Milestones
                </h2>
                {timeline?.summary && (
                  <Badge variant="secondary">
                    {timeline.summary.completed}/{timeline.summary.total_milestones} complete
                  </Badge>
                )}
              </div>

              {timeline?.milestones ? (
                <div className="space-y-4">
                  {/* Progress Bar */}
                  {timeline.summary && (
                    <div className="mb-6">
                      <div className="flex justify-between text-sm mb-2">
                        <span className="text-[var(--color-text-secondary)]">Overall Progress</span>
                        <span className="font-medium text-[var(--color-text-primary)]">
                          {Math.round(
                            (timeline.summary.completed / timeline.summary.total_milestones) * 100
                          )}
                          %
                        </span>
                      </div>
                      <GradientProgress
                        value={(timeline.summary.completed / timeline.summary.total_milestones) * 100}
                        size="md"
                      />
                    </div>
                  )}

                  {/* Milestones */}
                  <div className="space-y-3">
                    {timeline.milestones.map((milestone, idx) => {
                      const StatusIcon = milestoneStatusIcons[milestone.status];
                      const colorClass = milestoneStatusColors[milestone.status];

                      return (
                        <div
                          key={idx}
                          className={cn(
                            'p-4 rounded-lg border transition-all',
                            milestone.status === 'overdue'
                              ? 'border-[var(--color-critical-200)] dark:border-[var(--color-critical-500)]/30'
                              : 'border-[var(--color-border-subtle)]'
                          )}
                        >
                          <div className="flex items-start gap-4">
                            <div className={cn('p-2 rounded-lg', colorClass)}>
                              <StatusIcon className="h-5 w-5" />
                            </div>
                            <div className="flex-1">
                              <div className="flex items-center justify-between">
                                <p className="font-medium text-[var(--color-text-primary)]">
                                  {milestone.name}
                                </p>
                                <Badge
                                  variant={
                                    milestone.status === 'completed'
                                      ? 'success'
                                      : milestone.status === 'overdue'
                                      ? 'critical'
                                      : milestone.status === 'in_progress'
                                      ? 'primary'
                                      : 'secondary'
                                  }
                                >
                                  {milestone.status.replace('_', ' ')}
                                </Badge>
                              </div>
                              <p className="text-sm text-[var(--color-text-muted)] mt-1">
                                Target: {formatDate(milestone.target_date)} ({milestone.days_before_expiration}d before expiration)
                              </p>

                              {/* Action Items */}
                              {milestone.action_items.length > 0 && (
                                <div className="mt-3 space-y-1">
                                  {milestone.action_items.map((item, itemIdx) => (
                                    <div
                                      key={itemIdx}
                                      className="flex items-center gap-2 text-sm"
                                    >
                                      <div
                                        className={cn(
                                          'w-4 h-4 rounded border flex items-center justify-center',
                                          milestone.status === 'completed'
                                            ? 'bg-[var(--color-success-500)] border-[var(--color-success-500)]'
                                            : 'border-[var(--color-border-default)]'
                                        )}
                                      >
                                        {milestone.status === 'completed' && (
                                          <CheckCircle className="h-3 w-3 text-white" />
                                        )}
                                      </div>
                                      <span className="text-[var(--color-text-secondary)]">
                                        {item}
                                      </span>
                                    </div>
                                  ))}
                                </div>
                              )}

                              {/* Documents Ready */}
                              {Object.keys(milestone.documents_ready).length > 0 && (
                                <div className="mt-3 flex flex-wrap gap-2">
                                  {Object.entries(milestone.documents_ready).map(
                                    ([doc, ready]) => (
                                      <Badge
                                        key={doc}
                                        variant={ready ? 'success' : 'secondary'}
                                        className="text-xs"
                                      >
                                        {doc}: {ready ? 'Ready' : 'Pending'}
                                      </Badge>
                                    )
                                  )}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ) : (
                <p className="text-center text-[var(--color-text-muted)] py-8">
                  No timeline data available
                </p>
              )}
            </Card>
          </div>

          {/* Alerts Sidebar */}
          <div>
            <RenewalAlertsList
              alerts={alerts}
              showPropertyName={false}
              onAcknowledge={handleAcknowledge}
              onResolve={handleResolve}
              onConfigureAlerts={() => setConfigModalOpen(true)}
            />
          </div>
        </div>
      )}

      {activeTab === 'forecast' && (
        <div>
          {forecast ? (
            <RenewalForecastCard
              forecast={{
                ...forecast,
                status: 'active',
                rule_based_estimate: forecast.forecast?.mid ?? 0,
                rule_based_change_pct: forecast.forecast?.mid_change_percent ?? 0,
                model_used: 'rule_based',
              }}
              showDetails
            />
          ) : (
            <Card padding="lg">
              <div className="text-center py-12">
                <TrendingUp className="h-12 w-12 text-[var(--color-text-muted)] mx-auto mb-4" />
                <h3 className="text-lg font-medium text-[var(--color-text-primary)] mb-2">
                  No Forecast Available
                </h3>
                <p className="text-[var(--color-text-secondary)] mb-4">
                  Generate a renewal forecast to see premium predictions and negotiation insights.
                </p>
                <Button variant="primary" onClick={() => renewalsApi.generateForecast(id).then(setForecast)}>
                  Generate Forecast
                </Button>
              </div>
            </Card>
          )}
        </div>
      )}

      {activeTab === 'documents' && (
        <div>
          {readiness ? (
            <ReadinessChecklist
              readiness={readiness}
              onUploadDocument={(type) => console.log('Upload:', type)}
            />
          ) : (
            <Card padding="lg">
              <div className="text-center py-12">
                <FileText className="h-12 w-12 text-[var(--color-text-muted)] mx-auto mb-4" />
                <h3 className="text-lg font-medium text-[var(--color-text-primary)] mb-2">
                  No Readiness Assessment
                </h3>
                <p className="text-[var(--color-text-secondary)]">
                  Upload policy documents to assess renewal readiness.
                </p>
              </div>
            </Card>
          )}
        </div>
      )}

      {activeTab === 'market' && (
        <div className="space-y-6">
          {/* Live Market Intelligence from Parallel AI */}
          <MarketIntelligenceCard propertyId={id} />

          {/* Cached Market Context (from previous research) */}
          {marketContext && (
            <MarketContextPanel
              context={marketContext}
              onRefresh={() => console.log('Refresh market context')}
            />
          )}
        </div>
      )}

      {activeTab === 'comparison' && (
        <div>
          {comparison ? (
            <PolicyComparison comparison={comparison} />
          ) : (
            <Card padding="lg">
              <div className="text-center py-12">
                <ArrowLeftRight className="h-12 w-12 text-[var(--color-text-muted)] mx-auto mb-4" />
                <h3 className="text-lg font-medium text-[var(--color-text-primary)] mb-2">
                  No Comparison Available
                </h3>
                <p className="text-[var(--color-text-secondary)]">
                  Year-over-year comparison requires policy data from multiple years.
                </p>
              </div>
            </Card>
          )}
        </div>
      )}

      {/* Alert Config Modal */}
      {alertConfig && (
        <AlertConfigModal
          isOpen={configModalOpen}
          onClose={() => setConfigModalOpen(false)}
          config={alertConfig}
          propertyName={property.name}
          onSave={handleSaveConfig}
        />
      )}
    </div>
  );
}
