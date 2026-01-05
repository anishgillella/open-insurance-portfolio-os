'use client';

import { use, useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import {
  ArrowLeft,
  Building2,
  MapPin,
  Calendar,
  DollarSign,
  FileText,
  AlertTriangle,
  Shield,
  TrendingUp,
  Clock,
  ChevronRight,
  ExternalLink,
  Loader2,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Upload,
} from 'lucide-react';
import { cn, formatCurrency, getGrade, getGradeColor } from '@/lib/utils';
import { Button, Card, Badge } from '@/components/primitives';
import { GlassCard, ScoreRing, GradientProgress, StatusBadge } from '@/components/patterns';
import { staggerContainer, staggerItem } from '@/lib/motion/variants';
import {
  propertiesApi,
  healthScoreApi,
  gapsApi,
  type PropertyDetail,
  type HealthScoreResponse,
  type Gap,
} from '@/lib/api';

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function PropertyDetailPage({ params }: PageProps) {
  const { id } = use(params);

  const [property, setProperty] = useState<PropertyDetail | null>(null);
  const [healthScore, setHealthScore] = useState<HealthScoreResponse | null>(null);
  const [gaps, setGaps] = useState<Gap[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [propertyData, healthData, gapsData] = await Promise.all([
        propertiesApi.get(id),
        healthScoreApi.get(id).catch(() => null),
        gapsApi.list(undefined, { property_id: id }).catch(() => []),
      ]);
      setProperty(propertyData);
      setHealthScore(healthData);
      // Handle various API response formats for gaps
      setGaps(
        Array.isArray(gapsData) ? gapsData :
        (gapsData as { gaps?: Gap[]; items?: Gap[] })?.gaps ||
        (gapsData as { items?: Gap[] })?.items || []
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load property');
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
        <div className="flex items-center justify-center gap-4">
          <Link href="/properties">
            <Button variant="secondary">Back to properties</Button>
          </Link>
          <Button variant="ghost" onClick={fetchData}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </div>
      </div>
    );
  }

  // Extract values from nested structures (PropertyDetail uses nested objects)
  const healthScoreValue = property.health_score?.score ?? 0;
  const grade = property.health_score?.grade ?? getGrade(healthScoreValue);
  const gradeColor = getGradeColor(grade);
  const criticalGaps = gaps.filter((g) => g.severity === 'critical');
  const warningGaps = gaps.filter((g) => g.severity === 'warning');
  const daysUntilExpiration = property.insurance_summary?.days_until_expiration ?? 999;
  const isExpiringSoon = daysUntilExpiration <= 30;
  const isCritical = daysUntilExpiration <= 14;

  // Extract insurance values (handle string or number from API)
  const totalInsuredValue = Number(property.insurance_summary?.total_insured_value) || 0;
  const totalPremium = Number(property.insurance_summary?.total_annual_premium) || 0;

  return (
    <motion.div
      variants={staggerContainer}
      initial="initial"
      animate="animate"
      className="space-y-6"
    >
      {/* Back Link */}
      <motion.div variants={staggerItem} className="flex items-center justify-between">
        <Link
          href="/properties"
          className="inline-flex items-center gap-2 text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to properties
        </Link>
        <Button variant="ghost" size="sm" onClick={fetchData}>
          <RefreshCw className="h-4 w-4" />
        </Button>
      </motion.div>

      {/* Hero Header */}
      <motion.div variants={staggerItem}>
        <GlassCard className="p-8" gradient="from-primary-500 to-primary-600" hover={false}>
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
            {/* Property Info */}
            <div className="flex items-start gap-6">
              <div
                className={cn(
                  'w-20 h-20 rounded-2xl flex items-center justify-center',
                  `bg-gradient-to-br ${gradeColor}`
                )}
              >
                <span className="text-white text-3xl font-bold">{grade}</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">
                  {property.name}
                </h1>
                <p className="text-[var(--color-text-secondary)] flex items-center gap-2 mt-1">
                  <MapPin className="h-4 w-4" />
                  {property.address.street}, {property.address.city}, {property.address.state} {property.address.zip}
                </p>
                <div className="flex items-center gap-3 mt-3">
                  <Badge variant="secondary">{property.property_type ?? 'Unknown'}</Badge>
                  <span className="text-sm text-[var(--color-text-muted)]">
                    {property.total_buildings ?? 0} buildings, {property.total_units ?? 0} units
                  </span>
                  <span className="text-sm text-[var(--color-text-muted)]">
                    Built {property.year_built ?? 'N/A'}
                  </span>
                </div>
              </div>
            </div>

            {/* Quick Stats */}
            <div className="flex items-center gap-8">
              <div className="text-center">
                <p className="text-sm text-[var(--color-text-muted)]">Health Score</p>
                <p className="text-3xl font-bold text-[var(--color-text-primary)]">
                  {healthScoreValue}
                </p>
              </div>
              <div className="h-12 w-px bg-[var(--color-border-subtle)]" />
              <div className="text-center">
                <p className="text-sm text-[var(--color-text-muted)]">TIV</p>
                <p className="text-xl font-bold text-[var(--color-text-primary)]">
                  {formatCurrency(totalInsuredValue)}
                </p>
              </div>
              <div className="h-12 w-px bg-[var(--color-border-subtle)]" />
              <div className="text-center">
                <p className="text-sm text-[var(--color-text-muted)]">Expires In</p>
                <p
                  className={cn(
                    'text-xl font-bold',
                    isCritical
                      ? 'text-[var(--color-critical-500)]'
                      : isExpiringSoon
                      ? 'text-[var(--color-warning-500)]'
                      : 'text-[var(--color-text-primary)]'
                  )}
                >
                  {daysUntilExpiration < 999 ? `${daysUntilExpiration} days` : 'N/A'}
                </p>
              </div>
            </div>
          </div>
        </GlassCard>
      </motion.div>

      {/* Main Content Grid - 2 Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Takes 2/3 width */}
        <motion.div variants={staggerItem} className="lg:col-span-2 space-y-6">
          {/* Top Row: Health Score + Key Metrics side by side */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Health Score */}
            <Card padding="lg">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">
                  Health Score
                </h2>
                <Link href={`/properties/${property.id}/health-score`}>
                  <Button variant="ghost" size="sm" rightIcon={<ChevronRight className="h-4 w-4" />}>
                    Details
                  </Button>
                </Link>
              </div>

              <div className="flex justify-center mb-4">
                <ScoreRing score={healthScoreValue} size={120} />
              </div>

              {healthScore?.components && Array.isArray(healthScore.components) && (
                <div className="space-y-2">
                  {healthScore.components.slice(0, 3).map((component) => (
                    <div key={component.name}>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-[var(--color-text-secondary)]">{component.name}</span>
                        <span className="font-medium text-[var(--color-text-primary)]">
                          {component.percentage}%
                        </span>
                      </div>
                      <GradientProgress value={component.percentage} size="sm" />
                    </div>
                  ))}
                </div>
              )}
            </Card>

            {/* Key Metrics */}
            <Card padding="lg">
              <h2 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">
                Key Metrics
              </h2>

              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-xl bg-[var(--color-surface-sunken)]">
                  <div className="flex items-center gap-2 mb-1">
                    <DollarSign className="h-4 w-4 text-[var(--color-text-muted)]" />
                    <p className="text-xs text-[var(--color-text-muted)]">Total Insured Value</p>
                  </div>
                  <p className="text-lg font-bold text-[var(--color-text-primary)]">
                    {formatCurrency(totalInsuredValue)}
                  </p>
                </div>

                <div className="p-3 rounded-xl bg-[var(--color-surface-sunken)]">
                  <div className="flex items-center gap-2 mb-1">
                    <DollarSign className="h-4 w-4 text-[var(--color-text-muted)]" />
                    <p className="text-xs text-[var(--color-text-muted)]">Annual Premium</p>
                  </div>
                  <p className="text-lg font-bold text-[var(--color-text-primary)]">
                    {formatCurrency(totalPremium)}
                  </p>
                </div>

                <div className="p-3 rounded-xl bg-[var(--color-surface-sunken)]">
                  <div className="flex items-center gap-2 mb-1">
                    <Building2 className="h-4 w-4 text-[var(--color-text-muted)]" />
                    <p className="text-xs text-[var(--color-text-muted)]">Total Units</p>
                  </div>
                  <p className="text-lg font-bold text-[var(--color-text-primary)]">
                    {(property.total_units ?? 0).toLocaleString() || 'N/A'}
                  </p>
                </div>

                <div className="p-3 rounded-xl bg-[var(--color-surface-sunken)]">
                  <div className="flex items-center gap-2 mb-1">
                    <Calendar className="h-4 w-4 text-[var(--color-text-muted)]" />
                    <p className="text-xs text-[var(--color-text-muted)]">Year Built</p>
                  </div>
                  <p className="text-lg font-bold text-[var(--color-text-primary)]">
                    {property.year_built ?? 'N/A'}
                  </p>
                </div>
              </div>
            </Card>
          </div>

          {/* Bottom Row: Coverage + Gaps */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Coverage Overview */}
            <Card padding="lg">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">Coverage</h2>
                <Link href={`/gaps?property_id=${property.id}`}>
                  <Button variant="ghost" size="sm" rightIcon={<ChevronRight className="h-4 w-4" />}>
                    View gaps
                  </Button>
                </Link>
              </div>

              <div className="space-y-3">
                {property.policies?.slice(0, 3).map((policy) => (
                  <div
                    key={policy.id}
                    className="flex items-center gap-3 p-3 rounded-lg bg-[var(--color-surface-sunken)]"
                  >
                    <div className="p-2 rounded-lg bg-[var(--color-primary-50)] dark:bg-[var(--color-primary-500)]/20">
                      <Shield className="h-4 w-4 text-[var(--color-primary-500)]" />
                    </div>
                    <div className="flex-1">
                      <p className="font-medium text-[var(--color-text-primary)] text-sm">
                        {policy.policy_type}
                      </p>
                      <p className="text-xs text-[var(--color-text-muted)]">{policy.carrier}</p>
                    </div>
                    <div
                      className={cn(
                        'w-2 h-2 rounded-full',
                        policy.status === 'active'
                          ? 'bg-[var(--color-success-500)]'
                          : 'bg-[var(--color-warning-500)]'
                      )}
                    />
                  </div>
                ))}

                {(!property.policies || property.policies.length === 0) && (
                  <div className="text-center py-6 text-[var(--color-text-muted)]">
                    <Shield className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">No policies found</p>
                  </div>
                )}

                {(criticalGaps.length > 0 || warningGaps.length > 0) && (
                  <Link href={`/gaps?property_id=${property.id}`}>
                    <div className="flex items-center gap-3 p-3 rounded-lg bg-[var(--color-critical-50)] dark:bg-[var(--color-critical-500)]/10 border border-[var(--color-critical-200)] dark:border-[var(--color-critical-500)]/20 cursor-pointer hover:border-[var(--color-critical-300)] transition-colors">
                      <div className="p-2 rounded-lg bg-[var(--color-critical-100)] dark:bg-[var(--color-critical-500)]/20">
                        <AlertTriangle className="h-4 w-4 text-[var(--color-critical-500)]" />
                      </div>
                      <div className="flex-1">
                        <p className="font-medium text-[var(--color-critical-600)] dark:text-[var(--color-critical-400)] text-sm">
                          {criticalGaps.length + warningGaps.length} Coverage Gaps Detected
                        </p>
                        <p className="text-xs text-[var(--color-critical-500)]">
                          Review and address gaps
                        </p>
                      </div>
                      <ChevronRight className="h-4 w-4 text-[var(--color-critical-500)]" />
                    </div>
                  </Link>
                )}
              </div>
            </Card>

            {/* Gaps or Document Completeness Preview */}
            {gaps.length > 0 ? (
              <Card padding="lg">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">Gaps</h2>
                  <Badge variant="critical" dot>
                    {gaps.length}
                  </Badge>
                </div>

                <div className="space-y-3">
                  {gaps.slice(0, 3).map((gap) => (
                    <div
                      key={gap.id}
                      className="p-3 rounded-lg border border-[var(--color-border-subtle)] hover:border-[var(--color-border-default)] transition-colors"
                    >
                      <div className="flex items-start gap-3">
                        <div
                          className={cn(
                            'p-1.5 rounded-lg',
                            gap.severity === 'critical'
                              ? 'bg-[var(--color-critical-50)] text-[var(--color-critical-500)]'
                              : 'bg-[var(--color-warning-50)] text-[var(--color-warning-500)]'
                          )}
                        >
                          <AlertTriangle className="h-4 w-4" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <p className="font-medium text-[var(--color-text-primary)] text-sm">
                              {gap.title}
                            </p>
                            <StatusBadge
                              severity={gap.severity}
                              label={gap.severity}
                              pulse={gap.severity === 'critical'}
                            />
                          </div>
                          <p className="text-xs text-[var(--color-text-muted)] mt-0.5 line-clamp-1">
                            {gap.description}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                {gaps.length > 3 && (
                  <Link href={`/gaps?property_id=${property.id}`}>
                    <Button variant="ghost" className="w-full mt-3">
                      View all {gaps.length} gaps
                    </Button>
                  </Link>
                )}
              </Card>
            ) : (
              <Card padding="lg">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">
                    Coverage Status
                  </h2>
                  <Badge variant="success">No Gaps</Badge>
                </div>
                <div className="text-center py-6">
                  <div className="w-16 h-16 mx-auto mb-3 rounded-full bg-[var(--color-success-50)] dark:bg-[var(--color-success-500)]/10 flex items-center justify-center">
                    <CheckCircle2 className="h-8 w-8 text-[var(--color-success-500)]" />
                  </div>
                  <p className="text-[var(--color-text-secondary)]">
                    All coverage requirements are met
                  </p>
                </div>
              </Card>
            )}
          </div>
        </motion.div>

        {/* Right Column - Takes 1/3 width */}
        <motion.div variants={staggerItem} className="space-y-6">
          {/* Quick Actions */}
          <Card padding="lg">
            <h2 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">
              Quick Actions
            </h2>

            <div className="space-y-3">
              <Link href={`/properties/${property.id}/health-score`} className="block">
                <Button variant="secondary" className="w-full justify-start" leftIcon={<TrendingUp className="h-4 w-4" />}>
                  View Health Score Details
                </Button>
              </Link>

              <Link href={`/gaps?property_id=${property.id}`} className="block">
                <Button
                  variant={gaps.length > 0 ? 'danger' : 'secondary'}
                  className="w-full justify-start"
                  leftIcon={<AlertTriangle className="h-4 w-4" />}
                >
                  {gaps.length > 0
                    ? `Address ${gaps.length} Gaps`
                    : 'View Gap Analysis'}
                </Button>
              </Link>

              <Link href={`/properties/${property.id}/renewals`} className="block">
                <Button variant="secondary" className="w-full justify-start" leftIcon={<Clock className="h-4 w-4" />}>
                  Renewal Planning
                </Button>
              </Link>

              <Link href={`/documents?property_id=${property.id}`} className="block">
                <Button variant="secondary" className="w-full justify-start" leftIcon={<FileText className="h-4 w-4" />}>
                  View Documents ({property.documents?.length || 0})
                </Button>
              </Link>
            </div>
          </Card>

          {/* Renewal Status */}
          <Card padding="lg">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">
                Renewal Status
              </h2>
              <StatusBadge
                severity={isCritical ? 'critical' : isExpiringSoon ? 'warning' : 'info'}
                label={daysUntilExpiration < 999 ? `${daysUntilExpiration}d` : 'N/A'}
                pulse={isCritical}
              />
            </div>

            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-[var(--color-text-secondary)]">Days until expiration</span>
                  <span className="font-medium text-[var(--color-text-primary)]">
                    {daysUntilExpiration < 999 ? daysUntilExpiration : 'N/A'}
                  </span>
                </div>
                <div className="h-2 rounded-full bg-[var(--color-surface-sunken)] overflow-hidden">
                  <motion.div
                    className={cn(
                      'h-full rounded-full',
                      isCritical
                        ? 'bg-[var(--color-critical-500)]'
                        : isExpiringSoon
                        ? 'bg-[var(--color-warning-500)]'
                        : 'bg-[var(--color-success-500)]'
                    )}
                    initial={{ width: 0 }}
                    animate={{ width: `${Math.min(100, (daysUntilExpiration / 365) * 100)}%` }}
                    transition={{ duration: 1, delay: 0.5 }}
                  />
                </div>
              </div>

              <Link href={`/properties/${property.id}/renewals`}>
                <Button variant="primary" className="w-full" rightIcon={<ExternalLink className="h-4 w-4" />}>
                  Start Renewal Process
                </Button>
              </Link>
            </div>
          </Card>

          {/* Document Completeness */}
          <Card padding="lg">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">
                Document Completeness
              </h2>
              <Badge
                variant={
                  property.completeness.percentage >= 75
                    ? 'success'
                    : property.completeness.percentage >= 50
                    ? 'warning'
                    : 'danger'
                }
              >
                {property.completeness.percentage.toFixed(0)}%
              </Badge>
            </div>

            <div className="mb-4">
              <div className="flex justify-between text-sm mb-2">
                <span className="text-[var(--color-text-secondary)]">
                  Required: {property.completeness.required_present}/{property.completeness.required_total}
                </span>
                <span className="text-[var(--color-text-secondary)]">
                  Optional: {property.completeness.optional_present}/{property.completeness.optional_total}
                </span>
              </div>
              <div className="h-2 rounded-full bg-[var(--color-surface-sunken)] overflow-hidden">
                <motion.div
                  className={cn(
                    'h-full rounded-full',
                    property.completeness.percentage >= 75
                      ? 'bg-[var(--color-success-500)]'
                      : property.completeness.percentage >= 50
                      ? 'bg-[var(--color-warning-500)]'
                      : 'bg-[var(--color-critical-500)]'
                  )}
                  initial={{ width: 0 }}
                  animate={{ width: `${property.completeness.percentage}%` }}
                  transition={{ duration: 1, delay: 0.3 }}
                />
              </div>
            </div>

            <div className="space-y-2 max-h-[280px] overflow-y-auto">
              {property.completeness.checklist?.map((item) => (
                <div
                  key={item.document_type}
                  className={cn(
                    'p-2.5 rounded-lg border',
                    item.is_present
                      ? 'bg-[var(--color-success-50)] border-[var(--color-success-200)] dark:bg-[var(--color-success-500)]/10 dark:border-[var(--color-success-500)]/30'
                      : 'bg-[var(--color-surface-sunken)] border-[var(--color-border-subtle)]'
                  )}
                >
                  <div className="flex items-start gap-2.5">
                    {item.is_present ? (
                      <CheckCircle2 className="h-4 w-4 text-[var(--color-success-500)] flex-shrink-0 mt-0.5" />
                    ) : (
                      <XCircle className="h-4 w-4 text-[var(--color-text-muted)] flex-shrink-0 mt-0.5" />
                    )}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className={cn(
                          'font-medium text-sm',
                          item.is_present
                            ? 'text-[var(--color-success-700)] dark:text-[var(--color-success-400)]'
                            : 'text-[var(--color-text-primary)]'
                        )}>
                          {item.display_name}
                        </span>
                        {item.is_required && (
                          <Badge variant="secondary" className="text-[10px] px-1 py-0">
                            Required
                          </Badge>
                        )}
                      </div>
                      {item.is_present ? (
                        <p className="text-xs text-[var(--color-success-600)] dark:text-[var(--color-success-400)] truncate mt-0.5">
                          {item.uploaded_file}
                        </p>
                      ) : (
                        <p className="text-xs text-[var(--color-text-muted)] mt-0.5 line-clamp-1">
                          Provides: {item.fields_provided.slice(0, 2).join(', ')}
                          {item.fields_provided.length > 2 && '...'}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <Link href={`/documents?property_id=${property.id}`} className="block mt-4">
              <Button variant="secondary" className="w-full" leftIcon={<Upload className="h-4 w-4" />}>
                Upload Missing Documents
              </Button>
            </Link>
          </Card>

          {/* Last Updated */}
          <div className="text-center text-sm text-[var(--color-text-muted)]">
            Last updated: {new Date(property.updated_at).toLocaleDateString()}
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
}
