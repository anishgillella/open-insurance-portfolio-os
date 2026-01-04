'use client';

import { use } from 'react';
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
} from 'lucide-react';
import { cn, formatCurrency, getGrade, getGradeColor } from '@/lib/utils';
import { Button, Card, Badge } from '@/components/primitives';
import { GlassCard, ScoreRing, GradientProgress, StatusBadge } from '@/components/patterns';
import { mockProperties, mockHealthComponents, mockAlerts } from '@/lib/mock-data';
import { staggerContainer, staggerItem } from '@/lib/motion/variants';

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function PropertyDetailPage({ params }: PageProps) {
  const { id } = use(params);
  const property = mockProperties.find((p) => p.id === id);

  if (!property) {
    return (
      <div className="text-center py-16">
        <Building2 className="h-12 w-12 text-[var(--color-text-muted)] mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-2">
          Property not found
        </h3>
        <Link href="/properties">
          <Button variant="secondary">Back to properties</Button>
        </Link>
      </div>
    );
  }

  const grade = getGrade(property.health_score);
  const gradeColor = getGradeColor(grade);
  const propertyAlerts = mockAlerts.filter((a) => a.property_id === property.id);
  const isExpiringSoon = (property.days_until_expiration || 999) <= 30;
  const isCritical = (property.days_until_expiration || 999) <= 14;

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
          href="/properties"
          className="inline-flex items-center gap-2 text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to properties
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
                  <Badge variant="secondary">{property.property_type}</Badge>
                  <span className="text-sm text-[var(--color-text-muted)]">
                    {property.total_buildings} buildings, {property.total_units} units
                  </span>
                  <span className="text-sm text-[var(--color-text-muted)]">
                    Built {property.year_built}
                  </span>
                </div>
              </div>
            </div>

            {/* Quick Stats */}
            <div className="flex items-center gap-8">
              <div className="text-center">
                <p className="text-sm text-[var(--color-text-muted)]">Health Score</p>
                <p className="text-3xl font-bold text-[var(--color-text-primary)]">
                  {property.health_score}
                </p>
              </div>
              <div className="h-12 w-px bg-[var(--color-border-subtle)]" />
              <div className="text-center">
                <p className="text-sm text-[var(--color-text-muted)]">TIV</p>
                <p className="text-xl font-bold text-[var(--color-text-primary)]">
                  {formatCurrency(property.total_insured_value)}
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
                  {property.days_until_expiration || 'N/A'} days
                </p>
              </div>
            </div>
          </div>
        </GlassCard>
      </motion.div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Health Score & Alerts */}
        <motion.div variants={staggerItem} className="space-y-6">
          {/* Health Score */}
          <Card padding="lg">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">
                Health Score
              </h2>
              <Link href={`/properties/${property.id}/health-score`}>
                <Button variant="ghost" size="sm" rightIcon={<ChevronRight className="h-4 w-4" />}>
                  Details
                </Button>
              </Link>
            </div>

            <div className="flex justify-center mb-6">
              <ScoreRing score={property.health_score} size={140} />
            </div>

            <div className="space-y-3">
              {mockHealthComponents.slice(0, 4).map((component) => (
                <div key={component.name}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-[var(--color-text-secondary)]">{component.name}</span>
                    <span className="font-medium text-[var(--color-text-primary)]">
                      {component.score}%
                    </span>
                  </div>
                  <GradientProgress value={component.score} size="sm" />
                </div>
              ))}
            </div>
          </Card>

          {/* Alerts */}
          {propertyAlerts.length > 0 && (
            <Card padding="lg">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">Alerts</h2>
                <Badge variant="critical" dot>
                  {propertyAlerts.length}
                </Badge>
              </div>

              <div className="space-y-3">
                {propertyAlerts.map((alert) => (
                  <div
                    key={alert.id}
                    className="p-3 rounded-lg border border-[var(--color-border-subtle)] hover:border-[var(--color-border-default)] transition-colors"
                  >
                    <div className="flex items-start gap-3">
                      <div
                        className={cn(
                          'p-1.5 rounded-lg',
                          alert.severity === 'critical'
                            ? 'bg-[var(--color-critical-50)] text-[var(--color-critical-500)]'
                            : 'bg-[var(--color-warning-50)] text-[var(--color-warning-500)]'
                        )}
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
                        <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
                          {alert.description}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </motion.div>

        {/* Middle Column - Coverage & Policies */}
        <motion.div variants={staggerItem} className="space-y-6">
          {/* Coverage Overview */}
          <Card padding="lg">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">Coverage</h2>
              <Link href={`/gaps?property=${property.id}`}>
                <Button variant="ghost" size="sm" rightIcon={<ChevronRight className="h-4 w-4" />}>
                  View gaps
                </Button>
              </Link>
            </div>

            <div className="space-y-4">
              {['Property', 'General Liability', 'Umbrella'].map((coverage) => (
                <div
                  key={coverage}
                  className="flex items-center gap-3 p-3 rounded-lg bg-[var(--color-surface-sunken)]"
                >
                  <div className="p-2 rounded-lg bg-[var(--color-primary-50)] dark:bg-[var(--color-primary-500)]/20">
                    <Shield className="h-4 w-4 text-[var(--color-primary-500)]" />
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-[var(--color-text-primary)] text-sm">
                      {coverage}
                    </p>
                    <p className="text-xs text-[var(--color-text-muted)]">Active</p>
                  </div>
                  <div className="w-2 h-2 rounded-full bg-[var(--color-success-500)]" />
                </div>
              ))}

              {(property.gaps_count.critical > 0 || property.gaps_count.warning > 0) && (
                <Link href={`/gaps?property=${property.id}`}>
                  <div className="flex items-center gap-3 p-3 rounded-lg bg-[var(--color-critical-50)] dark:bg-[var(--color-critical-500)]/10 border border-[var(--color-critical-200)] dark:border-[var(--color-critical-500)]/20 cursor-pointer hover:border-[var(--color-critical-300)] transition-colors">
                    <div className="p-2 rounded-lg bg-[var(--color-critical-100)] dark:bg-[var(--color-critical-500)]/20">
                      <AlertTriangle className="h-4 w-4 text-[var(--color-critical-500)]" />
                    </div>
                    <div className="flex-1">
                      <p className="font-medium text-[var(--color-critical-600)] dark:text-[var(--color-critical-400)] text-sm">
                        {property.gaps_count.critical + property.gaps_count.warning} Coverage Gaps Detected
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

          {/* Key Metrics */}
          <Card padding="lg">
            <h2 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">
              Key Metrics
            </h2>

            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-[var(--color-surface-sunken)]">
                <div className="flex items-center gap-2 mb-2">
                  <DollarSign className="h-4 w-4 text-[var(--color-text-muted)]" />
                  <p className="text-sm text-[var(--color-text-muted)]">Total Insured Value</p>
                </div>
                <p className="text-xl font-bold text-[var(--color-text-primary)]">
                  {formatCurrency(property.total_insured_value)}
                </p>
              </div>

              <div className="p-4 rounded-xl bg-[var(--color-surface-sunken)]">
                <div className="flex items-center gap-2 mb-2">
                  <DollarSign className="h-4 w-4 text-[var(--color-text-muted)]" />
                  <p className="text-sm text-[var(--color-text-muted)]">Annual Premium</p>
                </div>
                <p className="text-xl font-bold text-[var(--color-text-primary)]">
                  {formatCurrency(property.total_premium)}
                </p>
              </div>

              <div className="p-4 rounded-xl bg-[var(--color-surface-sunken)]">
                <div className="flex items-center gap-2 mb-2">
                  <Building2 className="h-4 w-4 text-[var(--color-text-muted)]" />
                  <p className="text-sm text-[var(--color-text-muted)]">Total Units</p>
                </div>
                <p className="text-xl font-bold text-[var(--color-text-primary)]">
                  {property.total_units.toLocaleString()}
                </p>
              </div>

              <div className="p-4 rounded-xl bg-[var(--color-surface-sunken)]">
                <div className="flex items-center gap-2 mb-2">
                  <Calendar className="h-4 w-4 text-[var(--color-text-muted)]" />
                  <p className="text-sm text-[var(--color-text-muted)]">Year Built</p>
                </div>
                <p className="text-xl font-bold text-[var(--color-text-primary)]">
                  {property.year_built}
                </p>
              </div>
            </div>
          </Card>
        </motion.div>

        {/* Right Column - Quick Actions & Documents */}
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

              <Link href={`/gaps?property=${property.id}`} className="block">
                <Button
                  variant={(property.gaps_count.critical > 0 || property.gaps_count.warning > 0) ? 'danger' : 'secondary'}
                  className="w-full justify-start"
                  leftIcon={<AlertTriangle className="h-4 w-4" />}
                >
                  {(property.gaps_count.critical + property.gaps_count.warning) > 0
                    ? `Address ${property.gaps_count.critical + property.gaps_count.warning} Gaps`
                    : 'View Gap Analysis'}
                </Button>
              </Link>

              <Link href={`/properties/${property.id}/renewals`} className="block">
                <Button variant="secondary" className="w-full justify-start" leftIcon={<Clock className="h-4 w-4" />}>
                  Renewal Planning
                </Button>
              </Link>

              <Link href={`/properties/${property.id}/documents`} className="block">
                <Button variant="secondary" className="w-full justify-start" leftIcon={<FileText className="h-4 w-4" />}>
                  View Documents
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
                label={`${property.days_until_expiration || 'N/A'}d`}
                pulse={isCritical}
              />
            </div>

            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-[var(--color-text-secondary)]">Days until expiration</span>
                  <span className="font-medium text-[var(--color-text-primary)]">
                    {property.days_until_expiration || 'N/A'}
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
                    animate={{ width: `${Math.min(100, ((property.days_until_expiration || 0) / 365) * 100)}%` }}
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

          {/* Last Updated */}
          <div className="text-center text-sm text-[var(--color-text-muted)]">
            Last updated: {property.updated_at}
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
}
