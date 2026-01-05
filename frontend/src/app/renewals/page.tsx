'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import {
  Calendar,
  DollarSign,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  XCircle,
  ChevronRight,
  Bell,
  Eye,
  Activity,
  Loader2,
  RefreshCw,
} from 'lucide-react';
import { cn, formatCurrency } from '@/lib/utils';
import { Card, Badge, Button } from '@/components/primitives';
import { DataCard, StatusBadge, GlassCard } from '@/components/patterns';
import { RenewalAlertsList, AlertConfigModal } from '@/components/features/renewals';
import { staggerContainer, staggerItem } from '@/lib/motion/variants';
import {
  renewalsApi,
  propertiesApi,
  dashboardApi,
  type RenewalTimelineItem,
  type RenewalTimelineSummary,
  type RenewalAlert,
  type RenewalForecast,
  type Property,
} from '@/lib/api';

export default function RenewalsPage() {
  const [selectedPropertyId, setSelectedPropertyId] = useState<string | undefined>();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [properties, setProperties] = useState<Property[]>([]);
  const [timelines, setTimelines] = useState<RenewalTimelineItem[]>([]);
  const [timelineSummary, setTimelineSummary] = useState<RenewalTimelineSummary | null>(null);
  const [alerts, setAlerts] = useState<RenewalAlert[]>([]);
  const [forecasts, setForecasts] = useState<Map<string, RenewalForecast>>(new Map());

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [propertiesData, timelinesData, alertsData] = await Promise.all([
        propertiesApi.list(),
        renewalsApi.getTimeline(undefined, 365), // Look ahead 365 days for renewals
        renewalsApi.getAlerts(),
      ]);
      // Handle various API response formats
      const propsArray = Array.isArray(propertiesData) ? propertiesData :
        (propertiesData as { properties?: Property[]; items?: Property[] })?.properties ||
        (propertiesData as { items?: Property[] })?.items || [];

      // Timeline response has { timeline: [...], summary: {...} } structure
      const timelinesArray = timelinesData?.timeline || [];
      const summaryData = timelinesData?.summary || null;

      const alertsArray = Array.isArray(alertsData) ? alertsData :
        (alertsData as { alerts?: RenewalAlert[]; items?: RenewalAlert[] })?.alerts ||
        (alertsData as { items?: RenewalAlert[] })?.items || [];
      setProperties(propsArray);
      setTimelines(timelinesArray);
      setTimelineSummary(summaryData);
      setAlerts(alertsArray);

      // Fetch forecasts for each property with timeline
      const forecastMap = new Map<string, RenewalForecast>();
      await Promise.all(
        timelinesArray.map(async (timeline) => {
          try {
            const forecast = await renewalsApi.getForecast(timeline.property_id);
            forecastMap.set(timeline.property_id, forecast);
          } catch {
            // Property may not have forecast yet
          }
        })
      );
      setForecasts(forecastMap);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load renewal data');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleAcknowledge = useCallback(async (alertId: string) => {
    try {
      const updatedAlert = await renewalsApi.acknowledgeAlert(alertId);
      setAlerts((prev) => prev.map((a) => (a.id === alertId ? updatedAlert : a)));
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
    }
  }, []);

  const handleResolve = useCallback(async (alertId: string) => {
    try {
      const updatedAlert = await renewalsApi.resolveAlert(alertId);
      setAlerts((prev) => prev.map((a) => (a.id === alertId ? updatedAlert : a)));
    } catch (err) {
      console.error('Failed to resolve alert:', err);
    }
  }, []);

  // Calculate summary stats - use backend summary when available, fallback to calculation
  const forecastValues = Array.from(forecasts.values());
  const summary = {
    total_upcoming_renewals: timelineSummary?.total_renewals ?? timelines.length,
    total_premium_at_risk: timelineSummary?.total_premium_at_risk ?? timelines.reduce((sum, t) => {
      return sum + (t.current_premium || 0);
    }, 0),
    avg_forecast_change_pct: forecastValues.length > 0
      ? forecastValues.reduce((sum, f) => sum + (f.forecast?.mid_change_percent ?? 0), 0) / forecastValues.length
      : 0,
    projected_total_premium: forecastValues.reduce((sum, f) => sum + (f.forecast?.mid ?? 0), 0),
    by_urgency: {
      critical: timelineSummary?.expiring_30_days ?? timelines.filter((t) => t.days_until_expiration <= 30).length,
      warning: timelineSummary?.expiring_60_days ?? timelines.filter((t) => t.days_until_expiration > 30 && t.days_until_expiration <= 60).length,
      info: timelineSummary?.expiring_90_days ?? timelines.filter((t) => t.days_until_expiration > 60).length,
    },
    by_status: {
      // Use alert counts from timeline items to determine status
      on_track: timelines.filter((t) => !t.has_active_alerts).length,
      needs_attention: timelines.filter((t) => t.has_active_alerts && t.days_until_expiration > 30).length,
      overdue: timelines.filter((t) => t.has_active_alerts && t.days_until_expiration <= 30).length,
    },
  };

  // Sort renewals by urgency
  const sortedTimelines = [...timelines].sort(
    (a, b) => a.days_until_expiration - b.days_until_expiration
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 text-[var(--color-primary-500)] animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-16">
        <AlertTriangle className="h-12 w-12 text-[var(--color-critical-500)] mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-2">
          Failed to load renewal data
        </h3>
        <p className="text-[var(--color-text-muted)] mb-4">{error}</p>
        <Button variant="secondary" onClick={fetchData}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Try Again
        </Button>
      </div>
    );
  }

  return (
    <motion.div
      variants={staggerContainer}
      initial="initial"
      animate="animate"
      className="space-y-6"
    >
      {/* Header */}
      <motion.div variants={staggerItem} className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">
            Renewal Intelligence
          </h1>
          <p className="text-[var(--color-text-secondary)] mt-1">
            Portfolio-wide renewal tracking and forecasting
          </p>
        </div>
        <Button variant="ghost" size="sm" onClick={fetchData}>
          <RefreshCw className="h-4 w-4" />
        </Button>
      </motion.div>

      {/* Summary Stats */}
      <motion.div
        variants={staggerItem}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
      >
        <DataCard
          label="Upcoming Renewals"
          value={summary.total_upcoming_renewals}
          icon={<Calendar className="h-5 w-5" />}
        />
        <DataCard
          label="Premium at Risk"
          value={summary.total_premium_at_risk}
          prefix="$"
          icon={<DollarSign className="h-5 w-5" />}
        />
        <DataCard
          label="Avg Forecast Change"
          value={`${summary.avg_forecast_change_pct >= 0 ? '+' : ''}${summary.avg_forecast_change_pct.toFixed(1)}%`}
          icon={<TrendingUp className="h-5 w-5" />}
        />
        <DataCard
          label="Projected Premium"
          value={summary.projected_total_premium}
          prefix="$"
          icon={<Activity className="h-5 w-5" />}
        />
      </motion.div>

      {/* Status Overview */}
      <motion.div variants={staggerItem}>
        <GlassCard className="p-6" gradient="from-primary-500 to-primary-600">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* By Urgency */}
            <div>
              <h3 className="text-sm font-medium text-[var(--color-text-secondary)] mb-4">
                By Urgency
              </h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-[var(--color-critical-500)]" />
                    <span className="text-sm text-[var(--color-text-primary)]">
                      Critical (&lt;30d)
                    </span>
                  </div>
                  <span className="text-lg font-bold text-[var(--color-critical-500)]">
                    {summary.by_urgency.critical}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-[var(--color-warning-500)]" />
                    <span className="text-sm text-[var(--color-text-primary)]">
                      Warning (30-60d)
                    </span>
                  </div>
                  <span className="text-lg font-bold text-[var(--color-warning-500)]">
                    {summary.by_urgency.warning}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-[var(--color-info-500)]" />
                    <span className="text-sm text-[var(--color-text-primary)]">
                      Early (&gt;60d)
                    </span>
                  </div>
                  <span className="text-lg font-bold text-[var(--color-info-500)]">
                    {summary.by_urgency.info}
                  </span>
                </div>
              </div>
            </div>

            {/* By Status */}
            <div>
              <h3 className="text-sm font-medium text-[var(--color-text-secondary)] mb-4">
                By Status
              </h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-[var(--color-success-500)]" />
                    <span className="text-sm text-[var(--color-text-primary)]">On Track</span>
                  </div>
                  <span className="text-lg font-bold text-[var(--color-success-500)]">
                    {summary.by_status.on_track}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-[var(--color-warning-500)]" />
                    <span className="text-sm text-[var(--color-text-primary)]">Needs Attention</span>
                  </div>
                  <span className="text-lg font-bold text-[var(--color-warning-500)]">
                    {summary.by_status.needs_attention}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <XCircle className="h-4 w-4 text-[var(--color-critical-500)]" />
                    <span className="text-sm text-[var(--color-text-primary)]">Overdue</span>
                  </div>
                  <span className="text-lg font-bold text-[var(--color-critical-500)]">
                    {summary.by_status.overdue}
                  </span>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div>
              <h3 className="text-sm font-medium text-[var(--color-text-secondary)] mb-4">
                Quick Actions
              </h3>
              <div className="space-y-2">
                <Button variant="secondary" className="w-full justify-start" size="sm">
                  <Bell className="h-4 w-4 mr-2" />
                  Configure Alert Defaults
                </Button>
                <Button variant="secondary" className="w-full justify-start" size="sm">
                  <Eye className="h-4 w-4 mr-2" />
                  Generate Renewal Report
                </Button>
              </div>
            </div>
          </div>
        </GlassCard>
      </motion.div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Timeline List */}
        <motion.div variants={staggerItem} className="lg:col-span-2">
          <Card padding="lg">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">
                Renewal Timeline
              </h2>
              <span className="text-sm text-[var(--color-text-muted)]">
                {sortedTimelines.length} upcoming
              </span>
            </div>

            {sortedTimelines.length === 0 ? (
              <div className="text-center py-12">
                <Calendar className="h-12 w-12 text-[var(--color-text-muted)] mx-auto mb-4" />
                <h3 className="text-lg font-medium text-[var(--color-text-primary)] mb-2">
                  No upcoming renewals
                </h3>
                <p className="text-[var(--color-text-secondary)]">
                  {properties.length === 0
                    ? 'Upload documents to create properties first'
                    : 'All policies are current'}
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {sortedTimelines.map((timeline) => {
                  const property = properties.find((p) => p.id === timeline.property_id);
                  const forecast = forecasts.get(timeline.property_id);
                  const severity =
                    timeline.days_until_expiration <= 30
                      ? 'critical'
                      : timeline.days_until_expiration <= 60
                      ? 'warning'
                      : 'info';

                  return (
                    <Link
                      key={timeline.policy_id}
                      href={`/properties/${timeline.property_id}/renewals`}
                    >
                      <div
                        className={cn(
                          'p-4 rounded-lg border transition-all cursor-pointer',
                          'hover:border-[var(--color-primary-300)] dark:hover:border-[var(--color-primary-500)]/50',
                          selectedPropertyId === timeline.property_id
                            ? 'border-[var(--color-primary-500)] bg-[var(--color-primary-50)] dark:bg-[var(--color-primary-500)]/10'
                            : 'border-[var(--color-border-subtle)]'
                        )}
                        onClick={(e) => {
                          e.preventDefault();
                          setSelectedPropertyId(timeline.property_id);
                        }}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <div
                              className={cn(
                                'w-12 h-12 rounded-lg flex items-center justify-center text-white font-bold',
                                severity === 'critical'
                                  ? 'bg-[var(--color-critical-500)]'
                                  : severity === 'warning'
                                  ? 'bg-[var(--color-warning-500)]'
                                  : 'bg-[var(--color-info-500)]'
                              )}
                            >
                              {timeline.days_until_expiration}d
                            </div>
                            <div>
                              <p className="font-medium text-[var(--color-text-primary)]">
                                {property?.name || timeline.property_name}
                              </p>
                              <div className="flex items-center gap-2 mt-1">
                                <StatusBadge severity={severity} label={severity} />
                                <span className="text-xs text-[var(--color-text-muted)]">
                                  Expires {timeline.expiration_date}
                                </span>
                              </div>
                            </div>
                          </div>
                          <div className="text-right">
                            {forecast?.forecast && (
                              <>
                                <p className="text-sm text-[var(--color-text-muted)]">
                                  Forecast: {formatCurrency(forecast.forecast.mid)}
                                </p>
                                <p
                                  className={cn(
                                    'text-sm font-medium',
                                    (forecast.forecast.mid_change_percent ?? 0) >= 0
                                      ? 'text-[var(--color-critical-500)]'
                                      : 'text-[var(--color-success-500)]'
                                  )}
                                >
                                  {(forecast.forecast.mid_change_percent ?? 0) >= 0 ? '+' : ''}
                                  {(forecast.forecast.mid_change_percent ?? 0).toFixed(1)}%
                                </p>
                              </>
                            )}
                          </div>
                          <ChevronRight className="h-5 w-5 text-[var(--color-text-muted)]" />
                        </div>

                        {/* Policy Info & Status */}
                        <div className="mt-3 flex items-center justify-between text-xs text-[var(--color-text-muted)]">
                          <div className="flex items-center gap-3">
                            <span>{timeline.policy_type}</span>
                            {timeline.carrier_name && (
                              <>
                                <span>•</span>
                                <span>{timeline.carrier_name}</span>
                              </>
                            )}
                            {timeline.current_premium && (
                              <>
                                <span>•</span>
                                <span>{formatCurrency(timeline.current_premium)}</span>
                              </>
                            )}
                          </div>
                          <div className="flex items-center gap-2">
                            {timeline.has_forecast && (
                              <Badge variant="secondary" className="text-xs">Forecast Ready</Badge>
                            )}
                            {timeline.has_active_alerts && (
                              <Badge variant="warning" className="text-xs">{timeline.alert_count} Alert{timeline.alert_count > 1 ? 's' : ''}</Badge>
                            )}
                          </div>
                        </div>
                      </div>
                    </Link>
                  );
                })}
              </div>
            )}
          </Card>
        </motion.div>

        {/* Alerts Panel */}
        <motion.div variants={staggerItem}>
          <RenewalAlertsList
            alerts={alerts}
            onAcknowledge={handleAcknowledge}
            onResolve={handleResolve}
          />
        </motion.div>
      </div>

      {/* Forecasts Table */}
      {forecasts.size > 0 && (
        <motion.div variants={staggerItem}>
          <Card padding="lg">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">
                Renewal Forecasts
              </h2>
              <Button variant="ghost" size="sm" rightIcon={<ChevronRight className="h-4 w-4" />}>
                Export Report
              </Button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-[var(--color-border-subtle)]">
                    <th className="text-left py-3 px-4 text-sm font-medium text-[var(--color-text-muted)]">
                      Property
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-[var(--color-text-muted)]">
                      Expiration
                    </th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-[var(--color-text-muted)]">
                      Current Premium
                    </th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-[var(--color-text-muted)]">
                      Forecast (Low-High)
                    </th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-[var(--color-text-muted)]">
                      Change
                    </th>
                    <th className="text-center py-3 px-4 text-sm font-medium text-[var(--color-text-muted)]">
                      Confidence
                    </th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-[var(--color-text-muted)]">
                      Action
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {Array.from(forecasts.values()).map((forecast) => {
                    const timeline = timelines.find(
                      (t) => t.property_id === forecast.property_id
                    );
                    const severity =
                      (timeline?.days_until_expiration || 999) <= 30
                        ? 'critical'
                        : (timeline?.days_until_expiration || 999) <= 60
                        ? 'warning'
                        : 'info';

                    return (
                      <tr
                        key={forecast.id}
                        className="border-b border-[var(--color-border-subtle)] last:border-0 hover:bg-[var(--color-surface-sunken)] transition-colors"
                      >
                        <td className="py-4 px-4">
                          <div>
                            <p className="font-medium text-[var(--color-text-primary)]">
                              {forecast.property_name}
                            </p>
                            <p className="text-xs text-[var(--color-text-muted)]">
                              {forecast.days_until_expiration}d remaining
                            </p>
                          </div>
                        </td>
                        <td className="py-4 px-4">
                          <div className="flex items-center gap-2">
                            <StatusBadge severity={severity} label={severity} />
                            <span className="text-sm text-[var(--color-text-primary)]">
                              {forecast.current_expiration_date}
                            </span>
                          </div>
                        </td>
                        <td className="py-4 px-4 text-right">
                          <p className="font-medium text-[var(--color-text-primary)]">
                            {formatCurrency(forecast.current_premium)}
                          </p>
                        </td>
                        <td className="py-4 px-4 text-right">
                          {forecast.forecast ? (
                            <>
                              <p className="text-sm text-[var(--color-text-primary)]">
                                {formatCurrency(forecast.forecast.low)} - {formatCurrency(forecast.forecast.high)}
                              </p>
                              <p className="text-xs text-[var(--color-text-muted)]">
                                Mid: {formatCurrency(forecast.forecast.mid)}
                              </p>
                            </>
                          ) : (
                            <p className="text-sm text-[var(--color-text-muted)]">—</p>
                          )}
                        </td>
                        <td className="py-4 px-4 text-right">
                          {forecast.forecast ? (
                            <p
                              className={cn(
                                'font-medium',
                                (forecast.forecast.mid_change_percent ?? 0) >= 0
                                  ? 'text-[var(--color-critical-500)]'
                                  : 'text-[var(--color-success-500)]'
                              )}
                            >
                              {(forecast.forecast.mid_change_percent ?? 0) >= 0 ? '+' : ''}
                              {(forecast.forecast.mid_change_percent ?? 0).toFixed(1)}%
                            </p>
                          ) : (
                            <p className="text-[var(--color-text-muted)]">—</p>
                          )}
                        </td>
                        <td className="py-4 px-4 text-center">
                          <Badge variant={(forecast.confidence ?? 0) >= 80 ? 'success' : 'secondary'}>
                            {Math.round((forecast.confidence ?? 0) * 100)}%
                          </Badge>
                        </td>
                        <td className="py-4 px-4 text-right">
                          <Link href={`/properties/${forecast.property_id}/renewals`}>
                            <Button variant="ghost" size="sm">
                              View Details
                            </Button>
                          </Link>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </Card>
        </motion.div>
      )}
    </motion.div>
  );
}
