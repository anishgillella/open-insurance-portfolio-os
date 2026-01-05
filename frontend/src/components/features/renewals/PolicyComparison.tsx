'use client';

import { motion } from 'framer-motion';
import {
  ArrowRight,
  TrendingUp,
  TrendingDown,
  Minus,
  Scale,
  DollarSign,
  Shield,
  Calendar,
} from 'lucide-react';
import { cn, formatCurrency, formatDate } from '@/lib/utils';
import { Card, Badge } from '@/components/primitives';
import { staggerContainer, staggerItem } from '@/lib/motion/variants';
import type { PolicyComparison as PolicyComparisonType } from '@/types/api';

interface PolicyComparisonProps {
  comparison: PolicyComparisonType;
  className?: string;
}

const changeIcons = {
  increase: TrendingUp,
  decrease: TrendingDown,
  same: Minus,
  new: TrendingUp,
  removed: TrendingDown,
};

const changeColors = {
  positive: 'text-[var(--color-success-500)]',
  negative: 'text-[var(--color-critical-500)]',
  neutral: 'text-[var(--color-text-muted)]',
};

const changeBgColors = {
  positive: 'bg-[var(--color-success-50)] dark:bg-[var(--color-success-500)]/10',
  negative: 'bg-[var(--color-critical-50)] dark:bg-[var(--color-critical-500)]/10',
  neutral: 'bg-[var(--color-surface-sunken)]',
};

export function PolicyComparison({
  comparison,
  className,
}: PolicyComparisonProps) {
  const premiumChangePositive = comparison.premium_change_pct > 0;

  return (
    <Card padding="lg" className={className}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-[var(--color-primary-50)] dark:bg-[var(--color-primary-500)]/20">
            <Scale className="h-5 w-5 text-[var(--color-primary-500)]" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-[var(--color-text-primary)]">
              Year-over-Year Comparison
            </h3>
            <p className="text-sm text-[var(--color-text-muted)]">
              {comparison.property_name}
            </p>
          </div>
        </div>
        <Badge
          variant={premiumChangePositive ? 'critical' : 'success'}
          className="text-sm"
        >
          {premiumChangePositive ? '+' : ''}
          {comparison.premium_change_pct.toFixed(1)}% YoY
        </Badge>
      </div>

      {/* Policy Period Comparison */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        {/* Prior Policy */}
        <div className="p-4 rounded-xl bg-[var(--color-surface-sunken)]">
          <p className="text-sm font-medium text-[var(--color-text-secondary)] mb-3">
            Prior Term
          </p>
          <div className="space-y-2">
            <div>
              <p className="text-xs text-[var(--color-text-muted)]">Policy #</p>
              <p className="text-sm font-medium text-[var(--color-text-primary)]">
                {comparison.prior_policy.policy_number}
              </p>
            </div>
            <div>
              <p className="text-xs text-[var(--color-text-muted)]">Carrier</p>
              <p className="text-sm font-medium text-[var(--color-text-primary)]">
                {comparison.prior_policy.carrier}
              </p>
            </div>
            <div>
              <p className="text-xs text-[var(--color-text-muted)]">Term</p>
              <p className="text-sm text-[var(--color-text-primary)]">
                {formatDate(comparison.prior_policy.effective_date)} -{' '}
                {formatDate(comparison.prior_policy.expiration_date)}
              </p>
            </div>
            <div>
              <p className="text-xs text-[var(--color-text-muted)]">Premium</p>
              <p className="text-lg font-bold text-[var(--color-text-primary)]">
                {formatCurrency(comparison.prior_policy.premium)}
              </p>
            </div>
          </div>
        </div>

        {/* Arrow */}
        <div className="flex items-center justify-center">
          <div className="flex flex-col items-center gap-2">
            <ArrowRight className="h-8 w-8 text-[var(--color-primary-500)]" />
            <Badge variant="primary" className="text-xs">
              Renewal
            </Badge>
          </div>
        </div>

        {/* Current Policy */}
        <div
          className={cn(
            'p-4 rounded-xl border-2',
            'border-[var(--color-primary-200)] dark:border-[var(--color-primary-500)]/30',
            'bg-[var(--color-primary-50)] dark:bg-[var(--color-primary-500)]/10'
          )}
        >
          <p className="text-sm font-medium text-[var(--color-primary-700)] dark:text-[var(--color-primary-400)] mb-3">
            Current Term
          </p>
          <div className="space-y-2">
            <div>
              <p className="text-xs text-[var(--color-text-muted)]">Policy #</p>
              <p className="text-sm font-medium text-[var(--color-text-primary)]">
                {comparison.current_policy.policy_number}
              </p>
            </div>
            <div>
              <p className="text-xs text-[var(--color-text-muted)]">Carrier</p>
              <p className="text-sm font-medium text-[var(--color-text-primary)]">
                {comparison.current_policy.carrier}
              </p>
            </div>
            <div>
              <p className="text-xs text-[var(--color-text-muted)]">Term</p>
              <p className="text-sm text-[var(--color-text-primary)]">
                {formatDate(comparison.current_policy.effective_date)} -{' '}
                {formatDate(comparison.current_policy.expiration_date)}
              </p>
            </div>
            <div>
              <p className="text-xs text-[var(--color-text-muted)]">Premium</p>
              <p className="text-lg font-bold text-[var(--color-text-primary)]">
                {formatCurrency(comparison.current_policy.premium)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Changes Summary */}
      <div className="mb-4">
        <p className="text-sm font-medium text-[var(--color-text-secondary)] mb-3">
          Key Changes
        </p>
        <motion.div
          variants={staggerContainer}
          initial="initial"
          animate="animate"
          className="space-y-2"
        >
          {comparison.changes.map((change, idx) => {
            const ChangeIcon = changeIcons[change.change_type];
            const colorClass = changeColors[change.impact];
            const bgClass = changeBgColors[change.impact];

            return (
              <motion.div
                key={idx}
                variants={staggerItem}
                className={cn(
                  'p-3 rounded-lg flex items-center gap-3',
                  bgClass
                )}
              >
                <div className={cn('p-1.5 rounded-lg bg-white/50 dark:bg-black/20', colorClass)}>
                  <ChangeIcon className="h-4 w-4" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-[var(--color-text-primary)]">
                    {change.field}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-[var(--color-text-muted)]">
                    {change.prior_value}
                  </p>
                  <p className={cn('text-sm font-medium', colorClass)}>
                    {change.current_value}
                  </p>
                </div>
              </motion.div>
            );
          })}
        </motion.div>
      </div>

      {/* Coverage Comparison */}
      <div>
        <p className="text-sm font-medium text-[var(--color-text-secondary)] mb-3">
          Coverage Details
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--color-border-subtle)]">
                <th className="text-left py-2 text-[var(--color-text-muted)] font-medium">
                  Coverage
                </th>
                <th className="text-right py-2 text-[var(--color-text-muted)] font-medium">
                  Prior Limit
                </th>
                <th className="text-right py-2 text-[var(--color-text-muted)] font-medium">
                  Current Limit
                </th>
                <th className="text-right py-2 text-[var(--color-text-muted)] font-medium">
                  Prior Ded.
                </th>
                <th className="text-right py-2 text-[var(--color-text-muted)] font-medium">
                  Current Ded.
                </th>
              </tr>
            </thead>
            <tbody>
              {comparison.current_policy.coverages.map((coverage, idx) => {
                const priorCoverage = comparison.prior_policy.coverages.find(
                  (c) => c.type === coverage.type
                );

                const limitChanged = priorCoverage && priorCoverage.limit !== coverage.limit;
                const deductibleChanged =
                  priorCoverage && priorCoverage.deductible !== coverage.deductible;

                return (
                  <tr
                    key={idx}
                    className="border-b border-[var(--color-border-subtle)] last:border-0"
                  >
                    <td className="py-3 text-[var(--color-text-primary)] font-medium">
                      {coverage.type}
                    </td>
                    <td className="py-3 text-right text-[var(--color-text-muted)]">
                      {priorCoverage ? formatCurrency(priorCoverage.limit) : '—'}
                    </td>
                    <td
                      className={cn(
                        'py-3 text-right font-medium',
                        limitChanged
                          ? coverage.limit > (priorCoverage?.limit || 0)
                            ? 'text-[var(--color-success-500)]'
                            : 'text-[var(--color-critical-500)]'
                          : 'text-[var(--color-text-primary)]'
                      )}
                    >
                      {formatCurrency(coverage.limit)}
                    </td>
                    <td className="py-3 text-right text-[var(--color-text-muted)]">
                      {priorCoverage ? formatCurrency(priorCoverage.deductible) : '—'}
                    </td>
                    <td
                      className={cn(
                        'py-3 text-right font-medium',
                        deductibleChanged
                          ? coverage.deductible > (priorCoverage?.deductible || 0)
                            ? 'text-[var(--color-critical-500)]'
                            : 'text-[var(--color-success-500)]'
                          : 'text-[var(--color-text-primary)]'
                      )}
                    >
                      {formatCurrency(coverage.deductible)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </Card>
  );
}
