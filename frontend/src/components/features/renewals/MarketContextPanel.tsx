'use client';

import { motion } from 'framer-motion';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Globe2,
  Building2,
  Lightbulb,
  ChevronRight,
  RefreshCw,
  ExternalLink,
  Shield,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Card, Badge, Button } from '@/components/primitives';
import { staggerContainer, staggerItem } from '@/lib/motion/variants';
import type { MarketContext } from '@/types/api';

interface MarketContextPanelProps {
  context: MarketContext;
  onRefresh?: () => void;
  className?: string;
}

const appetiteIcons = {
  growing: TrendingUp,
  stable: Minus,
  shrinking: TrendingDown,
};

const appetiteColors = {
  growing: 'text-[var(--color-success-500)]',
  stable: 'text-[var(--color-warning-500)]',
  shrinking: 'text-[var(--color-critical-500)]',
};

const appetiteBgColors = {
  growing: 'bg-[var(--color-success-50)] dark:bg-[var(--color-success-500)]/10',
  stable: 'bg-[var(--color-warning-50)] dark:bg-[var(--color-warning-500)]/10',
  shrinking: 'bg-[var(--color-critical-50)] dark:bg-[var(--color-critical-500)]/10',
};

const positionColors = {
  strong: 'text-[var(--color-success-500)]',
  moderate: 'text-[var(--color-warning-500)]',
  weak: 'text-[var(--color-critical-500)]',
};

const positionBadgeVariant = {
  strong: 'success' as const,
  moderate: 'warning' as const,
  weak: 'critical' as const,
};

export function MarketContextPanel({
  context,
  onRefresh,
  className,
}: MarketContextPanelProps) {
  const AppetiteIcon = appetiteIcons[context.carrier_appetite];
  const rateTrendPositive = context.rate_change_percent >= 0;

  return (
    <Card padding="lg" className={className}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-[var(--color-primary-50)] dark:bg-[var(--color-primary-500)]/20">
            <Globe2 className="h-5 w-5 text-[var(--color-primary-500)]" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-[var(--color-text-primary)]">
              Market Intelligence
            </h3>
            <p className="text-sm text-[var(--color-text-muted)]">
              {context.property_name}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={positionBadgeVariant[context.competitive_position]}>
            {context.competitive_position} position
          </Badge>
          {onRefresh && (
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={onRefresh}
              className="text-[var(--color-text-muted)]"
            >
              <RefreshCw className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>

      {/* Rate Trend & Carrier Appetite */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        {/* Rate Trend */}
        <div
          className={cn(
            'p-4 rounded-xl',
            rateTrendPositive
              ? 'bg-[var(--color-critical-50)] dark:bg-[var(--color-critical-500)]/10'
              : 'bg-[var(--color-success-50)] dark:bg-[var(--color-success-500)]/10'
          )}
        >
          <div className="flex items-center gap-2 mb-2">
            {rateTrendPositive ? (
              <TrendingUp className="h-4 w-4 text-[var(--color-critical-500)]" />
            ) : (
              <TrendingDown className="h-4 w-4 text-[var(--color-success-500)]" />
            )}
            <p className="text-sm font-medium text-[var(--color-text-secondary)]">
              Rate Trend
            </p>
          </div>
          <p className="text-2xl font-bold text-[var(--color-text-primary)]">
            {context.rate_trend}
          </p>
          <p
            className={cn(
              'text-sm font-medium mt-1',
              rateTrendPositive
                ? 'text-[var(--color-critical-600)]'
                : 'text-[var(--color-success-600)]'
            )}
          >
            {rateTrendPositive ? '+' : ''}
            {context.rate_change_percent.toFixed(1)}% YoY
          </p>
        </div>

        {/* Carrier Appetite */}
        <div className={cn('p-4 rounded-xl', appetiteBgColors[context.carrier_appetite])}>
          <div className="flex items-center gap-2 mb-2">
            <Building2 className={cn('h-4 w-4', appetiteColors[context.carrier_appetite])} />
            <p className="text-sm font-medium text-[var(--color-text-secondary)]">
              Carrier Appetite
            </p>
          </div>
          <p className="text-2xl font-bold text-[var(--color-text-primary)] capitalize">
            {context.carrier_appetite}
          </p>
          <div className="flex items-center gap-1 mt-1">
            <AppetiteIcon className={cn('h-4 w-4', appetiteColors[context.carrier_appetite])} />
            <span className={cn('text-sm font-medium', appetiteColors[context.carrier_appetite])}>
              {context.carrier_appetite === 'growing'
                ? 'Strong interest'
                : context.carrier_appetite === 'stable'
                ? 'Moderate interest'
                : 'Limited interest'}
            </span>
          </div>
        </div>
      </div>

      {/* Carrier Notes */}
      <div className="mb-6 p-4 rounded-xl bg-[var(--color-surface-sunken)]">
        <div className="flex items-center gap-2 mb-2">
          <Shield className="h-4 w-4 text-[var(--color-primary-500)]" />
          <p className="text-sm font-medium text-[var(--color-text-secondary)]">
            Carrier Notes
          </p>
        </div>
        <p className="text-sm text-[var(--color-text-primary)] leading-relaxed">
          {context.carrier_notes}
        </p>
      </div>

      {/* Key Factors */}
      <div className="mb-6">
        <p className="text-sm font-medium text-[var(--color-text-secondary)] mb-3">
          Key Market Factors
        </p>
        <motion.div
          variants={staggerContainer}
          initial="initial"
          animate="animate"
          className="space-y-2"
        >
          {context.key_factors.map((factor, idx) => (
            <motion.div
              key={idx}
              variants={staggerItem}
              className="flex items-start gap-2 p-2 rounded-lg bg-[var(--color-surface-sunken)]"
            >
              <ChevronRight className="h-4 w-4 text-[var(--color-primary-500)] mt-0.5 flex-shrink-0" />
              <p className="text-sm text-[var(--color-text-primary)]">{factor}</p>
            </motion.div>
          ))}
        </motion.div>
      </div>

      {/* 6-Month Forecast */}
      <div className="mb-6 p-4 rounded-xl bg-gradient-to-br from-[var(--color-primary-50)] to-[var(--color-primary-100)] dark:from-[var(--color-primary-500)]/10 dark:to-[var(--color-primary-500)]/20 border border-[var(--color-primary-100)] dark:border-[var(--color-primary-500)]/20">
        <p className="text-sm font-medium text-[var(--color-primary-700)] dark:text-[var(--color-primary-400)] mb-2">
          6-Month Outlook
        </p>
        <p className="text-sm text-[var(--color-text-primary)] leading-relaxed">
          {context.six_month_forecast}
        </p>
      </div>

      {/* Opportunities */}
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-3">
          <Lightbulb className="h-4 w-4 text-[var(--color-warning-500)]" />
          <p className="text-sm font-medium text-[var(--color-text-secondary)]">
            Opportunities
          </p>
        </div>
        <motion.div
          variants={staggerContainer}
          initial="initial"
          animate="animate"
          className="space-y-2"
        >
          {context.opportunities.map((opportunity, idx) => (
            <motion.div
              key={idx}
              variants={staggerItem}
              className="flex items-start gap-2 p-3 rounded-lg border border-[var(--color-warning-200)] dark:border-[var(--color-warning-500)]/20 bg-[var(--color-warning-50)] dark:bg-[var(--color-warning-500)]/10"
            >
              <div className="w-1.5 h-1.5 rounded-full bg-[var(--color-warning-500)] mt-1.5 flex-shrink-0" />
              <p className="text-sm text-[var(--color-text-primary)]">{opportunity}</p>
            </motion.div>
          ))}
        </motion.div>
      </div>

      {/* Recommended Actions */}
      <div className="mb-4">
        <p className="text-sm font-medium text-[var(--color-text-secondary)] mb-3">
          Recommended Actions
        </p>
        <motion.div
          variants={staggerContainer}
          initial="initial"
          animate="animate"
          className="space-y-2"
        >
          {context.recommended_actions.map((action, idx) => (
            <motion.div
              key={idx}
              variants={staggerItem}
              className="flex items-center gap-3 p-3 rounded-lg border border-[var(--color-border-subtle)] hover:border-[var(--color-primary-200)] dark:hover:border-[var(--color-primary-500)]/30 transition-colors cursor-pointer"
            >
              <div className="flex items-center justify-center w-6 h-6 rounded-full bg-[var(--color-primary-100)] dark:bg-[var(--color-primary-500)]/20 text-[var(--color-primary-600)] dark:text-[var(--color-primary-400)] text-xs font-semibold">
                {idx + 1}
              </div>
              <p className="text-sm text-[var(--color-text-primary)] flex-1">{action}</p>
              <ChevronRight className="h-4 w-4 text-[var(--color-text-muted)]" />
            </motion.div>
          ))}
        </motion.div>
      </div>

      {/* Sources */}
      <div className="pt-4 border-t border-[var(--color-border-subtle)]">
        <p className="text-xs text-[var(--color-text-muted)] mb-2">
          Data sources: {context.sources.join(' · ')}
        </p>
        <p className="text-xs text-[var(--color-text-muted)]">
          Last updated: {context.fetched_at}
        </p>
      </div>
    </Card>
  );
}
