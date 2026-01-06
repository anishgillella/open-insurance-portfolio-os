'use client';

import { use, useState } from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import {
  ArrowLeft,
  Building2,
  Calendar,
  Clock,
  ChevronRight,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Play,
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
import { staggerContainer, staggerItem } from '@/lib/motion/variants';
import {
  mockProperties,
  mockRenewalTimelines,
  mockRenewalForecasts,
  mockRenewalAlerts,
  mockDocumentReadiness,
  mockMarketContext,
  mockPolicyComparisons,
  mockAlertConfigs,
} from '@/lib/mock-data';
import type { RenewalAlert, AlertConfig, RenewalMilestone } from '@/types/api';

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

  // Get property data
  const property = mockProperties.find((p) => p.id === id);
  const timeline = mockRenewalTimelines.find((t) => t.property_id === id);
  const forecast = mockRenewalForecasts.find((f) => f.property_id === id);
  const propertyAlerts = mockRenewalAlerts.filter((a) => a.property_id === id);
  const readiness = mockDocumentReadiness.find((r) => r.property_id === id);
  const marketContext = mockMarketContext.find((m) => m.property_id === id);
  const comparison = mockPolicyComparisons.find((c) => c.property_id === id);
  const alertConfig = mockAlertConfigs.find((c) => c.property_id === id);

  const [alerts, setAlerts] = useState<RenewalAlert[]>(propertyAlerts);

  if (!property) {
    return (
      <div className="text-center py-16">
        <Building2 className="h-12 w-12 text-[var(--color-text-muted)] mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-2">
          Property not found
        </h3>
        <Link href="/renewals">
          <Button variant="secondary">Back to renewals</Button>
        </Link>
      </div>
    );
  }

  const severity =
    (timeline?.days_until_expiration || 999) <= 30
      ? 'critical'
      : (timeline?.days_until_expiration || 999) <= 60
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
    <motion.div
      variants={staggerContainer}
      initial="initial"
      animate="animate"
      className="space-y-6"
    >
      {/* Back Link */}
      <motion.div variants={staggerItem}>
        <Link
          href="/renewals"
          className="inline-flex items-center gap-2 text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to renewals
        </Link>
      </motion.div>

      {/* Hero Header */}
      <motion.div variants={staggerItem}>
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
                <span className="text-2xl font-bold">{timeline?.days_until_expiration || '?'}</span>
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
                    Expires {timeline?.expiration_date || 'N/A'}
                  </span>
                </div>
              </div>
            </div>

            {/* Quick Stats */}
            <div className="flex items-center gap-8">
              <div className="text-center">
                <p className="text-sm text-[var(--color-text-muted)]">Current Premium</p>
                <p className="text-2xl font-bold text-[var(--color-text-primary)]">
                  {formatCurrency(property.total_premium)}
                </p>
              </div>
              <div className="h-12 w-px bg-[var(--color-border-subtle)]" />
              {forecast && (
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
                        forecast.forecast.mid_change_percent >= 0
                          ? 'text-[var(--color-critical-500)]'
                          : 'text-[var(--color-success-500)]'
                      )}
                    >
                      {forecast.forecast.mid_change_percent >= 0 ? '+' : ''}
                      {forecast.forecast.mid_change_percent.toFixed(1)}%
                    </p>
                  </div>
                </>
              )}
            </div>
          </div>
        </GlassCard>
      </motion.div>

      {/* Tab Navigation */}
      <motion.div variants={staggerItem}>
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
      </motion.div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Timeline & Milestones */}
          <motion.div variants={staggerItem} className="lg:col-span-2">
            <Card padding="lg">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">
                  Renewal Milestones
                </h2>
                {timeline && (
                  <Badge variant="secondary">
                    {timeline.summary.completed}/{timeline.summary.total_milestones} complete
                  </Badge>
                )}
              </div>

              {timeline ? (
                <div className="space-y-4">
                  {/* Progress Bar */}
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
          </motion.div>

          {/* Alerts Sidebar */}
          <motion.div variants={staggerItem}>
            <RenewalAlertsList
              alerts={alerts}
              showPropertyName={false}
              onAcknowledge={handleAcknowledge}
              onResolve={handleResolve}
              onConfigureAlerts={() => setConfigModalOpen(true)}
            />
          </motion.div>
        </div>
      )}

      {activeTab === 'forecast' && forecast && (
        <motion.div variants={staggerItem}>
          <RenewalForecastCard forecast={forecast} showDetails />
        </motion.div>
      )}

      {activeTab === 'documents' && readiness && (
        <motion.div variants={staggerItem}>
          <ReadinessChecklist
            readiness={readiness}
            onUploadDocument={(type) => console.log('Upload:', type)}
          />
        </motion.div>
      )}

      {activeTab === 'market' && (
        <motion.div variants={staggerItem} className="space-y-6">
          {/* Live Market Intelligence from Parallel AI */}
          <MarketIntelligenceCard propertyId={id} />

          {/* Cached Market Context (from previous research) */}
          {marketContext && (
            <MarketContextPanel
              context={marketContext}
              onRefresh={() => console.log('Refresh market context')}
            />
          )}
        </motion.div>
      )}

      {activeTab === 'comparison' && comparison && (
        <motion.div variants={staggerItem}>
          <PolicyComparison comparison={comparison} />
        </motion.div>
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
    </motion.div>
  );
}
