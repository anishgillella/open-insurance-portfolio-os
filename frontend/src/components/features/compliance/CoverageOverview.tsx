'use client';

import { motion } from 'framer-motion';
import { CheckCircle, AlertTriangle, XCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface CoverageType {
  name: string;
  color: string;
  adequacy: number; // 0-100
}

interface CoverageOverviewProps {
  coverages: CoverageType[];
  className?: string;
}

function getStatusIcon(adequacy: number) {
  if (adequacy >= 80) {
    return <CheckCircle className="h-4 w-4 text-[var(--color-success-500)]" />;
  }
  if (adequacy >= 50) {
    return <AlertTriangle className="h-4 w-4 text-[var(--color-warning-500)]" />;
  }
  return <XCircle className="h-4 w-4 text-[var(--color-critical-500)]" />;
}

function getBarColor(adequacy: number) {
  if (adequacy >= 80) return 'bg-[var(--color-success-500)]';
  if (adequacy >= 50) return 'bg-[var(--color-warning-500)]';
  return 'bg-[var(--color-critical-500)]';
}

function getStatusLabel(adequacy: number) {
  if (adequacy >= 80) return 'Adequate';
  if (adequacy >= 50) return 'Partial';
  if (adequacy > 0) return 'Insufficient';
  return 'Missing';
}

export function CoverageOverview({ coverages, className }: CoverageOverviewProps) {
  const overallScore = Math.round(
    coverages.reduce((sum, c) => sum + c.adequacy, 0) / coverages.length
  );

  const adequate = coverages.filter((c) => c.adequacy >= 80).length;
  const partial = coverages.filter((c) => c.adequacy >= 50 && c.adequacy < 80).length;
  const gaps = coverages.filter((c) => c.adequacy < 50).length;

  return (
    <div className={cn('space-y-4', className)}>
      {/* Summary Header */}
      <div className="flex items-center justify-between pb-3 border-b border-[var(--color-border-subtle)]">
        <div className="flex items-center gap-3">
          <div
            className={cn(
              'w-12 h-12 rounded-xl flex items-center justify-center text-white font-bold text-lg',
              overallScore >= 80
                ? 'bg-[var(--color-success-500)]'
                : overallScore >= 50
                ? 'bg-[var(--color-warning-500)]'
                : 'bg-[var(--color-critical-500)]'
            )}
          >
            {overallScore}%
          </div>
          <div>
            <p className="font-semibold text-[var(--color-text-primary)]">Overall Coverage</p>
            <p className="text-sm text-[var(--color-text-muted)]">
              {adequate} adequate, {partial} partial, {gaps} gaps
            </p>
          </div>
        </div>
      </div>

      {/* Coverage Items */}
      <div className="space-y-3">
        {coverages.map((coverage, index) => (
          <motion.div
            key={coverage.name}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
            className="group"
          >
            <div className="flex items-center justify-between mb-1.5">
              <div className="flex items-center gap-2">
                {getStatusIcon(coverage.adequacy)}
                <span className="font-medium text-[var(--color-text-primary)]">
                  {coverage.name}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span
                  className={cn(
                    'text-xs px-2 py-0.5 rounded-full',
                    coverage.adequacy >= 80
                      ? 'bg-[var(--color-success-50)] text-[var(--color-success-600)]'
                      : coverage.adequacy >= 50
                      ? 'bg-[var(--color-warning-50)] text-[var(--color-warning-600)]'
                      : 'bg-[var(--color-critical-50)] text-[var(--color-critical-600)]'
                  )}
                >
                  {getStatusLabel(coverage.adequacy)}
                </span>
                <span className="text-sm font-semibold text-[var(--color-text-secondary)] w-10 text-right">
                  {coverage.adequacy}%
                </span>
              </div>
            </div>

            {/* Progress Bar */}
            <div className="h-2 bg-[var(--color-surface-sunken)] rounded-full overflow-hidden">
              <motion.div
                className={cn('h-full rounded-full', getBarColor(coverage.adequacy))}
                initial={{ width: 0 }}
                animate={{ width: `${coverage.adequacy}%` }}
                transition={{ duration: 0.5, delay: index * 0.05 }}
              />
            </div>
          </motion.div>
        ))}
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-4 pt-3 border-t border-[var(--color-border-subtle)] text-xs text-[var(--color-text-muted)]">
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-[var(--color-success-500)]" />
          <span>80-100% Adequate</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-[var(--color-warning-500)]" />
          <span>50-79% Partial</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-[var(--color-critical-500)]" />
          <span>0-49% Gap</span>
        </div>
      </div>
    </div>
  );
}
