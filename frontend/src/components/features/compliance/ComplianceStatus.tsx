'use client';

import { motion } from 'framer-motion';
import {
  CheckCircle,
  XCircle,
  AlertCircle,
  Building2,
  FileText,
  Calendar,
  ExternalLink,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { formatDate } from '@/lib/utils';
import { Badge, Card } from '@/components/primitives';
import type { ComplianceStatus as ComplianceStatusType } from '@/types/api';

interface ComplianceStatusProps {
  status: ComplianceStatusType;
  onClick?: () => void;
  compact?: boolean;
}

const statusConfig = {
  compliant: {
    icon: CheckCircle,
    color: 'text-[var(--color-success-500)]',
    bgColor: 'bg-[var(--color-success-50)]',
    borderColor: 'border-[var(--color-success-200)]',
    label: 'Compliant',
    badgeVariant: 'success' as const,
  },
  non_compliant: {
    icon: XCircle,
    color: 'text-[var(--color-critical-500)]',
    bgColor: 'bg-[var(--color-critical-50)]',
    borderColor: 'border-[var(--color-critical-200)]',
    label: 'Non-Compliant',
    badgeVariant: 'critical' as const,
  },
  partial: {
    icon: AlertCircle,
    color: 'text-[var(--color-warning-500)]',
    bgColor: 'bg-[var(--color-warning-50)]',
    borderColor: 'border-[var(--color-warning-200)]',
    label: 'Partial',
    badgeVariant: 'warning' as const,
  },
};

export function ComplianceStatusCard({ status, onClick, compact = false }: ComplianceStatusProps) {
  const config = status.is_compliant
    ? statusConfig.compliant
    : statusConfig.non_compliant;
  const StatusIcon = config.icon;

  const passCount = status.checks.filter((c) => c.status === 'pass').length;
  const failCount = status.checks.filter((c) => c.status === 'fail').length;
  const totalChecks = status.checks.filter((c) => c.status !== 'not_required').length;

  if (compact) {
    return (
      <motion.div
        className={cn(
          'flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all',
          'border',
          config.borderColor,
          config.bgColor,
          'hover:shadow-[var(--shadow-elevation-1)]'
        )}
        onClick={onClick}
        whileHover={{ scale: 1.01 }}
        whileTap={{ scale: 0.99 }}
      >
        <StatusIcon className={cn('h-5 w-5', config.color)} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <p className="font-medium text-[var(--color-text-primary)] text-sm">
              {status.lender_name || 'No Lender'}
            </p>
            <Badge variant={config.badgeVariant} size="sm">
              {config.label}
            </Badge>
          </div>
          <p className="text-xs text-[var(--color-text-muted)]">
            {passCount}/{totalChecks} checks passed
          </p>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      className={cn(
        'p-4 rounded-xl cursor-pointer transition-all',
        'border',
        config.borderColor,
        'bg-[var(--color-surface)]',
        'hover:shadow-[var(--shadow-elevation-2)]'
      )}
      onClick={onClick}
      whileHover={{ y: -2 }}
      whileTap={{ scale: 0.99 }}
    >
      {/* Header */}
      <div className="flex items-start gap-3 mb-4">
        <div className={cn('p-2 rounded-lg', config.bgColor)}>
          <StatusIcon className={cn('h-5 w-5', config.color)} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-semibold text-[var(--color-text-primary)]">
              {status.lender_name || 'No Lender Assigned'}
            </h3>
            <Badge variant={config.badgeVariant}>{config.label}</Badge>
          </div>
          <div className="flex items-center gap-3 text-sm text-[var(--color-text-muted)]">
            {status.loan_number && (
              <span className="flex items-center gap-1">
                <FileText className="h-3 w-3" />
                {status.loan_number}
              </span>
            )}
            <span className="flex items-center gap-1">
              <Building2 className="h-3 w-3" />
              {status.template_used}
            </span>
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-4">
        <div className="flex justify-between text-xs mb-1">
          <span className="text-[var(--color-text-muted)]">Compliance Progress</span>
          <span className="font-medium text-[var(--color-text-primary)]">
            {passCount}/{totalChecks} passed
          </span>
        </div>
        <div className="h-2 rounded-full bg-[var(--color-surface-sunken)] overflow-hidden">
          <div
            className={cn(
              'h-full rounded-full transition-all',
              status.is_compliant
                ? 'bg-[var(--color-success-500)]'
                : failCount > passCount
                ? 'bg-[var(--color-critical-500)]'
                : 'bg-[var(--color-warning-500)]'
            )}
            style={{ width: `${(passCount / totalChecks) * 100}%` }}
          />
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-3 gap-2 mb-4">
        <div className="p-2 rounded-lg bg-[var(--color-success-50)] text-center">
          <p className="text-lg font-bold text-[var(--color-success-600)]">{passCount}</p>
          <p className="text-xs text-[var(--color-success-600)]">Passed</p>
        </div>
        <div className="p-2 rounded-lg bg-[var(--color-critical-50)] text-center">
          <p className="text-lg font-bold text-[var(--color-critical-600)]">{failCount}</p>
          <p className="text-xs text-[var(--color-critical-600)]">Failed</p>
        </div>
        <div className="p-2 rounded-lg bg-[var(--color-surface-sunken)] text-center">
          <p className="text-lg font-bold text-[var(--color-text-primary)]">
            {status.checks.filter((c) => c.status === 'not_required').length}
          </p>
          <p className="text-xs text-[var(--color-text-muted)]">N/A</p>
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between pt-3 border-t border-[var(--color-border-subtle)]">
        <span className="text-xs text-[var(--color-text-muted)]">
          <Calendar className="h-3 w-3 inline mr-1" />
          Checked {formatDate(status.last_checked)}
        </span>
        <ExternalLink className="h-4 w-4 text-[var(--color-text-muted)]" />
      </div>
    </motion.div>
  );
}
