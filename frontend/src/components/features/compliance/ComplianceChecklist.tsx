'use client';

import { motion } from 'framer-motion';
import {
  CheckCircle,
  XCircle,
  MinusCircle,
  ChevronRight,
  AlertTriangle,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge, Card } from '@/components/primitives';
import { staggerContainer, staggerItem } from '@/lib/motion/variants';
import type { ComplianceCheck, ComplianceStatus } from '@/types/api';

interface ComplianceChecklistProps {
  status: ComplianceStatus;
  onCheckClick?: (check: ComplianceCheck) => void;
  showHeader?: boolean;
}

const checkStatusConfig = {
  pass: {
    icon: CheckCircle,
    color: 'text-[var(--color-success-500)]',
    bgColor: 'bg-[var(--color-success-50)]',
    label: 'Pass',
    badgeVariant: 'success' as const,
  },
  fail: {
    icon: XCircle,
    color: 'text-[var(--color-critical-500)]',
    bgColor: 'bg-[var(--color-critical-50)]',
    label: 'Fail',
    badgeVariant: 'critical' as const,
  },
  not_required: {
    icon: MinusCircle,
    color: 'text-[var(--color-text-muted)]',
    bgColor: 'bg-[var(--color-surface-sunken)]',
    label: 'N/A',
    badgeVariant: 'secondary' as const,
  },
};

function ComplianceCheckItem({
  check,
  onClick,
}: {
  check: ComplianceCheck;
  onClick?: () => void;
}) {
  const config = checkStatusConfig[check.status];
  const StatusIcon = config.icon;

  return (
    <motion.div
      variants={staggerItem}
      className={cn(
        'flex items-start gap-3 p-4 rounded-lg transition-all',
        'border border-[var(--color-border-subtle)]',
        'hover:border-[var(--color-border-default)] hover:shadow-[var(--shadow-elevation-1)]',
        onClick && 'cursor-pointer'
      )}
      onClick={onClick}
      whileHover={onClick ? { scale: 1.01 } : undefined}
    >
      <div className={cn('p-1.5 rounded-lg flex-shrink-0', config.bgColor)}>
        <StatusIcon className={cn('h-4 w-4', config.color)} />
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <h4 className="font-medium text-[var(--color-text-primary)]">
            {check.requirement}
          </h4>
          <Badge variant={config.badgeVariant} size="sm">
            {config.label}
          </Badge>
        </div>

        {check.status === 'fail' && check.issue_message && (
          <p className="text-sm text-[var(--color-critical-600)] mb-2 flex items-start gap-1">
            <AlertTriangle className="h-3.5 w-3.5 mt-0.5 flex-shrink-0" />
            {check.issue_message}
          </p>
        )}

        {(check.current_value || check.required_value) && (
          <div className="flex flex-wrap gap-4 text-sm">
            {check.current_value && (
              <div>
                <span className="text-[var(--color-text-muted)]">Current: </span>
                <span
                  className={cn(
                    'font-medium',
                    check.status === 'fail'
                      ? 'text-[var(--color-critical-600)]'
                      : 'text-[var(--color-text-primary)]'
                  )}
                >
                  {check.current_value}
                </span>
              </div>
            )}
            {check.required_value && check.status !== 'not_required' && (
              <div>
                <span className="text-[var(--color-text-muted)]">Required: </span>
                <span className="font-medium text-[var(--color-success-600)]">
                  {check.required_value}
                </span>
              </div>
            )}
            {check.gap_amount && (
              <div>
                <span className="text-[var(--color-text-muted)]">Gap: </span>
                <span className="font-medium text-[var(--color-critical-600)]">
                  ${check.gap_amount.toLocaleString()}
                </span>
              </div>
            )}
          </div>
        )}
      </div>

      {onClick && (
        <ChevronRight className="h-5 w-5 text-[var(--color-text-muted)] flex-shrink-0" />
      )}
    </motion.div>
  );
}

export function ComplianceChecklist({
  status,
  onCheckClick,
  showHeader = true,
}: ComplianceChecklistProps) {
  const passCount = status.checks.filter((c) => c.status === 'pass').length;
  const failCount = status.checks.filter((c) => c.status === 'fail').length;
  const naCount = status.checks.filter((c) => c.status === 'not_required').length;

  // Sort checks: failed first, then pass, then not_required
  const sortedChecks = [...status.checks].sort((a, b) => {
    const order = { fail: 0, pass: 1, not_required: 2 };
    return order[a.status] - order[b.status];
  });

  return (
    <div className="space-y-4">
      {showHeader && (
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-[var(--color-text-primary)]">
              Compliance Checks
            </h3>
            <p className="text-sm text-[var(--color-text-muted)]">
              {status.template_used} template • {status.lender_name || 'No lender'}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="success" size="sm">
              {passCount} passed
            </Badge>
            {failCount > 0 && (
              <Badge variant="critical" size="sm">
                {failCount} failed
              </Badge>
            )}
            {naCount > 0 && (
              <Badge variant="secondary" size="sm">
                {naCount} N/A
              </Badge>
            )}
          </div>
        </div>
      )}

      <motion.div
        variants={staggerContainer}
        initial="initial"
        animate="animate"
        className="space-y-3"
      >
        {sortedChecks.map((check, index) => (
          <ComplianceCheckItem
            key={`${check.requirement}-${index}`}
            check={check}
            onClick={onCheckClick ? () => onCheckClick(check) : undefined}
          />
        ))}
      </motion.div>
    </div>
  );
}
