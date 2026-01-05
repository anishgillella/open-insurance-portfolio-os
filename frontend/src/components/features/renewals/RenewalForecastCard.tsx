'use client';

import { motion } from 'framer-motion';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Target,
  Brain,
  ChevronRight,
  Lightbulb,
} from 'lucide-react';
import { cn, formatCurrency } from '@/lib/utils';
import { Card, Badge } from '@/components/primitives';
import { GradientProgress } from '@/components/patterns';
import type { RenewalForecastExtended } from '@/types/api';

interface RenewalForecastCardProps {
  forecast: RenewalForecastExtended;
  showDetails?: boolean;
  className?: string;
}

function FactorRow({
  factor,
}: {
  factor: {
    name: string;
    impact_percent: number;
    direction: 'increase' | 'decrease' | 'neutral';
    description: string;
  };
}) {
  const Icon = factor.direction === 'increase'
    ? TrendingUp
    : factor.direction === 'decrease'
    ? TrendingDown
    : Minus;

  const colorClass = factor.direction === 'increase'
    ? 'text-[var(--color-critical-500)]'
    : factor.direction === 'decrease'
    ? 'text-[var(--color-success-500)]'
    : 'text-[var(--color-text-muted)]';

  return (
    <div className="flex items-start gap-3 py-2">
      <div className={cn('p-1.5 rounded-lg bg-[var(--color-surface-sunken)]', colorClass)}>
        <Icon className="h-3.5 w-3.5" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between">
          <p className="text-sm font-medium text-[var(--color-text-primary)]">
            {factor.name}
          </p>
          <span className={cn('text-sm font-semibold', colorClass)}>
            {factor.direction === 'decrease' ? '' : '+'}
            {factor.impact_percent.toFixed(1)}%
          </span>
        </div>
        <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
          {factor.description}
        </p>
      </div>
    </div>
  );
}

export function RenewalForecastCard({
  forecast,
  showDetails = true,
  className,
}: RenewalForecastCardProps) {
  const midChangePositive = forecast.forecast.mid_change_percent >= 0;

  return (
    <Card padding="lg" className={className}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-[var(--color-primary-50)] dark:bg-[var(--color-primary-500)]/20">
            <Target className="h-5 w-5 text-[var(--color-primary-500)]" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-[var(--color-text-primary)]">
              Premium Forecast
            </h3>
            <p className="text-sm text-[var(--color-text-muted)]">
              AI-powered renewal prediction
            </p>
          </div>
        </div>
        <Badge variant="primary" className="gap-1">
          <Brain className="h-3 w-3" />
          {forecast.confidence}% confidence
        </Badge>
      </div>

      {/* Current vs Projected */}
      <div className="grid grid-cols-2 gap-6 mb-6">
        <div className="p-4 rounded-xl bg-[var(--color-surface-sunken)]">
          <p className="text-sm text-[var(--color-text-muted)] mb-1">Current Premium</p>
          <p className="text-2xl font-bold text-[var(--color-text-primary)]">
            {formatCurrency(forecast.current_premium)}
          </p>
          <p className="text-xs text-[var(--color-text-muted)] mt-1">
            Expires {forecast.current_expiration_date}
          </p>
        </div>
        <div
          className={cn(
            'p-4 rounded-xl',
            midChangePositive
              ? 'bg-[var(--color-warning-50)] dark:bg-[var(--color-warning-500)]/10'
              : 'bg-[var(--color-success-50)] dark:bg-[var(--color-success-500)]/10'
          )}
        >
          <p className="text-sm text-[var(--color-text-muted)] mb-1">Projected (Mid)</p>
          <p className="text-2xl font-bold text-[var(--color-text-primary)]">
            {formatCurrency(forecast.forecast.mid)}
          </p>
          <p
            className={cn(
              'text-xs font-medium mt-1',
              midChangePositive
                ? 'text-[var(--color-warning-600)]'
                : 'text-[var(--color-success-600)]'
            )}
          >
            {midChangePositive ? '+' : ''}
            {forecast.forecast.mid_change_percent.toFixed(1)}% change
          </p>
        </div>
      </div>

      {/* Forecast Range */}
      <div className="mb-6">
        <p className="text-sm font-medium text-[var(--color-text-secondary)] mb-3">
          Forecast Range
        </p>
        <div className="relative">
          {/* Range bar */}
          <div className="h-8 rounded-full bg-gradient-to-r from-[var(--color-success-100)] via-[var(--color-warning-100)] to-[var(--color-critical-100)] dark:from-[var(--color-success-500)]/20 dark:via-[var(--color-warning-500)]/20 dark:to-[var(--color-critical-500)]/20 relative overflow-hidden">
            {/* Labels */}
            <div className="absolute inset-0 flex items-center justify-between px-4">
              <span className="text-xs font-medium text-[var(--color-success-700)] dark:text-[var(--color-success-400)]">
                Low: {formatCurrency(forecast.forecast.low)}
              </span>
              <span className="text-xs font-semibold text-[var(--color-warning-700)] dark:text-[var(--color-warning-400)]">
                Mid: {formatCurrency(forecast.forecast.mid)}
              </span>
              <span className="text-xs font-medium text-[var(--color-critical-700)] dark:text-[var(--color-critical-400)]">
                High: {formatCurrency(forecast.forecast.high)}
              </span>
            </div>
          </div>

          {/* Percent changes */}
          <div className="flex justify-between mt-1 px-2">
            <span className="text-[10px] text-[var(--color-text-muted)]">
              +{forecast.forecast.low_change_percent.toFixed(1)}%
            </span>
            <span className="text-[10px] text-[var(--color-text-muted)]">
              +{forecast.forecast.mid_change_percent.toFixed(1)}%
            </span>
            <span className="text-[10px] text-[var(--color-text-muted)]">
              +{forecast.forecast.high_change_percent.toFixed(1)}%
            </span>
          </div>
        </div>
      </div>

      {showDetails && (
        <>
          {/* Key Factors */}
          <div className="mb-6">
            <p className="text-sm font-medium text-[var(--color-text-secondary)] mb-3">
              Key Factors
            </p>
            <div className="divide-y divide-[var(--color-border-subtle)]">
              {forecast.factors.map((factor, idx) => (
                <FactorRow key={idx} factor={factor} />
              ))}
            </div>
          </div>

          {/* LLM Analysis */}
          {forecast.llm_analysis && (
            <div className="mb-6">
              <div className="flex items-center gap-2 mb-3">
                <Brain className="h-4 w-4 text-[var(--color-primary-500)]" />
                <p className="text-sm font-medium text-[var(--color-text-secondary)]">
                  AI Analysis
                </p>
              </div>
              <div className="p-4 rounded-xl bg-[var(--color-primary-50)] dark:bg-[var(--color-primary-500)]/10 border border-[var(--color-primary-100)] dark:border-[var(--color-primary-500)]/20">
                <p className="text-sm text-[var(--color-text-primary)] leading-relaxed">
                  {forecast.llm_analysis}
                </p>
              </div>
            </div>
          )}

          {/* Negotiation Points */}
          {forecast.negotiation_points.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Lightbulb className="h-4 w-4 text-[var(--color-warning-500)]" />
                <p className="text-sm font-medium text-[var(--color-text-secondary)]">
                  Negotiation Leverage Points
                </p>
              </div>
              <div className="space-y-2">
                {forecast.negotiation_points.map((point, idx) => (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.1 }}
                    className="flex items-start gap-2 p-2 rounded-lg hover:bg-[var(--color-surface-sunken)] transition-colors"
                  >
                    <ChevronRight className="h-4 w-4 text-[var(--color-primary-500)] mt-0.5 flex-shrink-0" />
                    <p className="text-sm text-[var(--color-text-primary)]">{point}</p>
                  </motion.div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </Card>
  );
}
