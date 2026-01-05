'use client';

import { motion } from 'framer-motion';
import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import {
  Building2,
  DollarSign,
  CreditCard,
  Activity,
  AlertTriangle,
  Clock,
  CheckCircle,
  ArrowRight,
  LayoutGrid,
  BarChart3,
  RefreshCw,
  Loader2,
} from 'lucide-react';
import { DataCard, GlassCard, ScoreRing, GradientProgress, StatusBadge } from '@/components/patterns';
import { Button, Card, Badge } from '@/components/primitives';
import { PortfolioTreemap, PortfolioBubbleChart } from '@/components/features/portfolio';
import { staggerContainer, staggerItem } from '@/lib/motion/variants';
import {
  dashboardApi,
  propertiesApi,
  type DashboardSummary,
  type ExpirationItem,
  type DashboardAlert,
  type Property,
} from '@/lib/api';

function getGreeting() {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 18) return 'Good afternoon';
  return 'Good evening';
}

export default function Dashboard() {
  const [portfolioView, setPortfolioView] = useState<'treemap' | 'bubble'>('treemap');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [expirations, setExpirations] = useState<ExpirationItem[]>([]);
  const [alerts, setAlerts] = useState<DashboardAlert[]>([]);
  const [properties, setProperties] = useState<Property[]>([]);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [summaryData, expirationsData, alertsData, propertiesData] = await Promise.all([
        dashboardApi.getSummary(),
        dashboardApi.getExpirations(),
        dashboardApi.getAlerts(),
        propertiesApi.list(),
      ]);
      setSummary(summaryData);
      // Handle various API response formats
      setExpirations(
        Array.isArray(expirationsData) ? expirationsData :
        (expirationsData as { expirations?: ExpirationItem[]; items?: ExpirationItem[] })?.expirations ||
        (expirationsData as { items?: ExpirationItem[] })?.items || []
      );
      setAlerts(
        Array.isArray(alertsData) ? alertsData :
        (alertsData as { alerts?: DashboardAlert[]; items?: DashboardAlert[] })?.alerts ||
        (alertsData as { items?: DashboardAlert[] })?.items || []
      );
      setProperties(
        Array.isArray(propertiesData) ? propertiesData :
        (propertiesData as { properties?: Property[]; items?: Property[] })?.properties ||
        (propertiesData as { items?: Property[] })?.items || []
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard data');
    } finally {
      setIsLoading(false);
    }
  }, []);

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

  if (error) {
    return (
      <div className="text-center py-16">
        <AlertTriangle className="h-12 w-12 text-[var(--color-critical-500)] mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-2">
          Failed to load dashboard
        </h3>
        <p className="text-[var(--color-text-muted)] mb-4">{error}</p>
        <Button variant="secondary" onClick={fetchData}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Try Again
        </Button>
      </div>
    );
  }

  // Group expirations by urgency
  const getExpirationSeverity = (days: number): 'critical' | 'warning' | 'info' => {
    if (days <= 14) return 'critical';
    if (days <= 30) return 'warning';
    return 'info';
  };

  return (
    <motion.div
      variants={staggerContainer}
      initial="initial"
      animate="animate"
      className="space-y-8"
    >
      {/* Header */}
      <motion.div variants={staggerItem} className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">
            {getGreeting()}
          </h1>
          <p className="text-[var(--color-text-secondary)] mt-1">
            Your portfolio at a glance
          </p>
        </div>
        <Button variant="ghost" size="sm" onClick={fetchData}>
          <RefreshCw className="h-4 w-4" />
        </Button>
      </motion.div>

      {/* Stats Grid */}
      <motion.div
        variants={staggerItem}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
      >
        <DataCard
          label="Properties"
          value={summary?.portfolio_stats?.total_properties || 0}
          icon={<Building2 className="h-5 w-5" />}
        />
        <DataCard
          label="Total Insured Value"
          value={Number(summary?.portfolio_stats?.total_insured_value) || 0}
          prefix="$"
          icon={<DollarSign className="h-5 w-5" />}
        />
        <DataCard
          label="Annual Premium"
          value={Number(summary?.portfolio_stats?.total_annual_premium) || 0}
          prefix="$"
          icon={<CreditCard className="h-5 w-5" />}
        />
        <DataCard
          label="Health Score"
          value={summary?.health_score?.portfolio_average || 0}
          icon={<Activity className="h-5 w-5" />}
        />
      </motion.div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Expiration Timeline */}
        <motion.div variants={staggerItem}>
          <Card padding="lg">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">
                Expiration Timeline
              </h2>
              <Clock className="h-5 w-5 text-[var(--color-text-muted)]" />
            </div>
            {expirations.length === 0 ? (
              <div className="text-center py-8">
                <Clock className="h-8 w-8 text-[var(--color-text-muted)] mx-auto mb-2" />
                <p className="text-[var(--color-text-muted)]">No upcoming expirations</p>
              </div>
            ) : (
              <div className="space-y-4">
                {expirations.slice(0, 4).map((expiration) => {
                  const severity = getExpirationSeverity(expiration.days_until_expiration);
                  return (
                    <Link
                      key={expiration.policy_id}
                      href={`/properties/${expiration.property_id}`}
                      className="block"
                    >
                      <div className="flex items-center gap-4 p-3 rounded-lg bg-[var(--color-surface-sunken)] hover:bg-[var(--color-surface)] transition-colors">
                        <div
                          className={`w-3 h-3 rounded-full ${
                            severity === 'critical'
                              ? 'bg-[var(--color-critical-500)]'
                              : severity === 'warning'
                              ? 'bg-[var(--color-warning-500)]'
                              : 'bg-[var(--color-info-500)]'
                          }`}
                        />
                        <div className="flex-1">
                          <p className="font-medium text-[var(--color-text-primary)] text-sm">
                            {expiration.property_name}
                          </p>
                          <p className="text-xs text-[var(--color-text-muted)]">
                            {expiration.coverage_type}
                          </p>
                        </div>
                        <StatusBadge
                          severity={severity}
                          label={`${expiration.days_until_expiration}d`}
                          pulse={severity === 'critical'}
                        />
                      </div>
                    </Link>
                  );
                })}
              </div>
            )}
            <Link href="/renewals">
              <Button variant="ghost" className="w-full mt-4" rightIcon={<ArrowRight className="h-4 w-4" />}>
                View all expirations
              </Button>
            </Link>
          </Card>
        </motion.div>

        {/* Alerts Panel */}
        <motion.div variants={staggerItem}>
          <Card padding="lg">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">
                Alerts
              </h2>
              {alerts.length > 0 && (
                <Badge variant="critical" dot>{alerts.length} Active</Badge>
              )}
            </div>
            {alerts.length === 0 ? (
              <div className="text-center py-8">
                <CheckCircle className="h-8 w-8 text-[var(--color-success-500)] mx-auto mb-2" />
                <p className="text-[var(--color-text-muted)]">No active alerts</p>
              </div>
            ) : (
              <div className="space-y-3">
                {alerts.slice(0, 3).map((alert) => (
                  <Link
                    key={alert.id}
                    href={alert.property_id ? `/properties/${alert.property_id}` : '/gaps'}
                    className="block"
                  >
                    <div className="p-3 rounded-lg border border-[var(--color-border-subtle)] hover:border-[var(--color-border-default)] transition-colors cursor-pointer">
                      <div className="flex items-start gap-3">
                        <div
                          className={`p-1.5 rounded-lg ${
                            alert.severity === 'critical'
                              ? 'bg-[var(--color-critical-50)] text-[var(--color-critical-500)]'
                              : alert.severity === 'warning'
                              ? 'bg-[var(--color-warning-50)] text-[var(--color-warning-500)]'
                              : 'bg-[var(--color-info-50)] text-[var(--color-info-500)]'
                          }`}
                        >
                          <AlertTriangle className="h-4 w-4" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <p className="font-medium text-[var(--color-text-primary)] text-sm">
                              {alert.title}
                            </p>
                            <StatusBadge
                              severity={alert.severity}
                              label={alert.severity}
                              pulse={alert.severity === 'critical'}
                            />
                          </div>
                          <p className="text-xs text-[var(--color-text-muted)] mt-0.5 truncate">
                            {alert.description}
                          </p>
                        </div>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            )}
            <Link href="/gaps">
              <Button variant="ghost" className="w-full mt-4" rightIcon={<ArrowRight className="h-4 w-4" />}>
                View all alerts
              </Button>
            </Link>
          </Card>
        </motion.div>

        {/* Health Score Widget */}
        <motion.div variants={staggerItem}>
          <GlassCard className="p-6" gradient="from-primary-500 to-success-500">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">
                Portfolio Health
              </h2>
              <Badge variant="primary">Score</Badge>
            </div>
            <div className="flex justify-center mb-6">
              <ScoreRing score={summary?.health_score?.portfolio_average || 0} size={160} />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-3 rounded-lg bg-[var(--color-surface)]/50">
                <p className="text-2xl font-bold text-[var(--color-text-primary)]">
                  {summary?.gap_stats?.properties_with_gaps || 0}
                </p>
                <p className="text-xs text-[var(--color-text-muted)]">Properties with Gaps</p>
              </div>
              <div className="text-center p-3 rounded-lg bg-[var(--color-surface)]/50">
                <p className="text-2xl font-bold text-[var(--color-text-primary)]">
                  {summary?.gap_stats?.critical_gaps || 0}
                </p>
                <p className="text-xs text-[var(--color-text-muted)]">Critical Gaps</p>
              </div>
            </div>
            <Link href="/gaps">
              <Button variant="ghost" className="w-full mt-4" rightIcon={<ArrowRight className="h-4 w-4" />}>
                View full breakdown
              </Button>
            </Link>
          </GlassCard>
        </motion.div>
      </div>

      {/* Portfolio Visualization */}
      {properties.length > 0 && (
        <motion.div variants={staggerItem}>
          <Card padding="lg">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">
                  Portfolio Overview
                </h2>
                <p className="text-sm text-[var(--color-text-muted)]">
                  Click any property to view details
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant={portfolioView === 'treemap' ? 'primary' : 'ghost'}
                  size="sm"
                  leftIcon={<LayoutGrid className="h-4 w-4" />}
                  onClick={() => setPortfolioView('treemap')}
                >
                  Treemap
                </Button>
                <Button
                  variant={portfolioView === 'bubble' ? 'primary' : 'ghost'}
                  size="sm"
                  leftIcon={<BarChart3 className="h-4 w-4" />}
                  onClick={() => setPortfolioView('bubble')}
                >
                  Bubble
                </Button>
              </div>
            </div>
            {portfolioView === 'treemap' ? (
              <PortfolioTreemap properties={properties} height={350} />
            ) : (
              <PortfolioBubbleChart properties={properties} height={350} />
            )}
            <div className="mt-4 flex justify-center">
              <Link href="/properties">
                <Button variant="ghost" rightIcon={<ArrowRight className="h-4 w-4" />}>
                  View all properties
                </Button>
              </Link>
            </div>
          </Card>
        </motion.div>
      )}

      {/* Empty State if no data */}
      {properties.length === 0 && (
        <motion.div variants={staggerItem}>
          <Card padding="lg">
            <div className="text-center py-12">
              <Building2 className="h-12 w-12 text-[var(--color-text-muted)] mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-2">
                No properties yet
              </h3>
              <p className="text-[var(--color-text-muted)] mb-4 max-w-md mx-auto">
                Upload your insurance documents to get started. Properties will be automatically created from your folder structure.
              </p>
              <Link href="/documents">
                <Button variant="primary">
                  Upload Documents
                </Button>
              </Link>
            </div>
          </Card>
        </motion.div>
      )}
    </motion.div>
  );
}
