'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';
import {
  Building2,
  MapPin,
  Calendar,
  AlertTriangle,
  TrendingUp,
  ArrowRight,
} from 'lucide-react';
import { cn, formatCurrency, getGrade, getGradeColor } from '@/lib/utils';
import { Badge } from '@/components/primitives';
import type { Property } from '@/lib/api';

interface PropertyCardProps {
  property: Property;
  view?: 'grid' | 'list';
}

export function PropertyCard({ property, view = 'grid' }: PropertyCardProps) {
  // Handle health_score being either a number or an object with a score property
  const healthScoreValue = typeof property.health_score === 'object' && property.health_score !== null
    ? (property.health_score as { score?: number }).score ?? 0
    : (property.health_score ?? 0);
  const grade = getGrade(healthScoreValue);
  const gradeColor = getGradeColor(grade);
  const daysUntilExp = property.days_until_expiration || 999;
  const isExpiringSoon = daysUntilExp <= 30;
  const isCritical = daysUntilExp <= 14;
  const gapsCount = property.gaps_count || { critical: 0, warning: 0, info: 0 };
  const hasGaps = gapsCount.critical > 0 || gapsCount.warning > 0;
  const gapCount = gapsCount.critical + gapsCount.warning;

  if (view === 'list') {
    return (
      <Link href={`/properties/${property.id}`}>
        <motion.div
          className={cn(
            'flex items-center gap-6 p-4 rounded-xl',
            'bg-[var(--color-surface)] border border-[var(--color-border-subtle)]',
            'hover:shadow-[var(--shadow-elevation-2)] hover:border-[var(--color-border-default)]',
            'transition-all duration-200 cursor-pointer'
          )}
          whileHover={{ x: 4 }}
          transition={{ type: 'spring', stiffness: 400, damping: 25 }}
        >
          {/* Health Score */}
          <div
            className={cn(
              'flex-shrink-0 w-14 h-14 rounded-xl flex items-center justify-center',
              `bg-gradient-to-br ${gradeColor}`
            )}
          >
            <span className="text-white text-xl font-bold">{grade}</span>
          </div>

          {/* Main Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-[var(--color-text-primary)] truncate">
                {property.name}
              </h3>
              {hasGaps && (
                <Badge variant="critical" size="sm" dot>
                  {gapCount} gaps
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-4 mt-1 text-sm text-[var(--color-text-muted)]">
              <span className="flex items-center gap-1">
                <MapPin className="h-3.5 w-3.5" />
                {property.address.city}, {property.address.state}
              </span>
              <span>{property.property_type || 'Unknown'}</span>
              <span>{property.total_units ?? 0} units</span>
            </div>
          </div>

          {/* TIV */}
          <div className="text-right">
            <p className="text-sm text-[var(--color-text-muted)]">TIV</p>
            <p className="font-semibold text-[var(--color-text-primary)]">
              {formatCurrency(Number(property.total_insured_value) || 0)}
            </p>
          </div>

          {/* Premium */}
          <div className="text-right">
            <p className="text-sm text-[var(--color-text-muted)]">Premium</p>
            <p className="font-semibold text-[var(--color-text-primary)]">
              {formatCurrency(Number(property.total_premium) || 0)}
            </p>
          </div>

          {/* Expiration */}
          <div className="text-right min-w-[100px]">
            <p className="text-sm text-[var(--color-text-muted)]">Expires</p>
            <p
              className={cn(
                'font-semibold',
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

          <ArrowRight className="h-5 w-5 text-[var(--color-text-muted)]" />
        </motion.div>
      </Link>
    );
  }

  // Grid view
  return (
    <Link href={`/properties/${property.id}`}>
      <motion.div
        className={cn(
          'relative p-6 rounded-2xl',
          'bg-[var(--color-surface)] border border-[var(--color-border-subtle)]',
          'hover:shadow-[var(--shadow-elevation-3)] hover:border-[var(--color-border-default)]',
          'transition-all duration-300 cursor-pointer h-full'
        )}
        whileHover={{ y: -4 }}
        transition={{ type: 'spring', stiffness: 300, damping: 25 }}
      >
        {/* Expiration Warning Badge */}
        {isExpiringSoon && (
          <div
            className={cn(
              'absolute -top-2 -right-2 px-2.5 py-1 rounded-full text-xs font-medium text-white flex items-center gap-1',
              isCritical ? 'bg-[var(--color-critical-500)]' : 'bg-[var(--color-warning-500)]'
            )}
          >
            <Calendar className="h-3 w-3" />
            {property.days_until_expiration}d
          </div>
        )}

        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-[var(--color-surface-sunken)]">
              <Building2 className="h-5 w-5 text-[var(--color-text-secondary)]" />
            </div>
            <div>
              <h3 className="font-semibold text-[var(--color-text-primary)] line-clamp-1">
                {property.name}
              </h3>
              <p className="text-sm text-[var(--color-text-muted)] flex items-center gap-1">
                <MapPin className="h-3 w-3" />
                {property.address.city}, {property.address.state}
              </p>
            </div>
          </div>

          {/* Health Score Badge */}
          <div
            className={cn(
              'w-12 h-12 rounded-xl flex items-center justify-center',
              `bg-gradient-to-br ${gradeColor}`
            )}
          >
            <span className="text-white text-lg font-bold">{grade}</span>
          </div>
        </div>

        {/* Property Type & Units */}
        <div className="flex items-center gap-2 mb-4">
          <Badge variant="secondary" size="sm">
            {property.property_type || 'Unknown'}
          </Badge>
          <span className="text-sm text-[var(--color-text-muted)]">
            {property.total_buildings} buildings, {property.total_units ?? 0} units
          </span>
        </div>

        {/* Metrics */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <p className="text-xs text-[var(--color-text-muted)] uppercase tracking-wider">
              Total Insured Value
            </p>
            <p className="text-lg font-semibold text-[var(--color-text-primary)]">
              {formatCurrency(Number(property.total_insured_value) || 0)}
            </p>
          </div>
          <div>
            <p className="text-xs text-[var(--color-text-muted)] uppercase tracking-wider">
              Annual Premium
            </p>
            <p className="text-lg font-semibold text-[var(--color-text-primary)]">
              {formatCurrency(Number(property.total_premium) || 0)}
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between pt-4 border-t border-[var(--color-border-subtle)]">
          <div className="flex items-center gap-2">
            {hasGaps ? (
              <div className="flex items-center gap-1.5 text-[var(--color-critical-500)]">
                <AlertTriangle className="h-4 w-4" />
                <span className="text-sm font-medium">{gapCount} coverage gaps</span>
              </div>
            ) : (
              <div className="flex items-center gap-1.5 text-[var(--color-success-500)]">
                <TrendingUp className="h-4 w-4" />
                <span className="text-sm font-medium">Fully covered</span>
              </div>
            )}
          </div>

          <div className="flex items-center gap-1 text-sm text-[var(--color-primary-500)] font-medium">
            View details
            <ArrowRight className="h-4 w-4" />
          </div>
        </div>
      </motion.div>
    </Link>
  );
}
