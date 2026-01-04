'use client';

import { motion } from 'framer-motion';
import {
  AlertTriangle,
  AlertCircle,
  Info,
  Clock,
  Shield,
  DollarSign,
  FileWarning,
  Calendar,
  Droplets,
  Building2,
  CheckCircle,
  Eye,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { formatCurrency, formatDate } from '@/lib/utils';
import { Badge } from '@/components/primitives';
import { StatusBadge } from '@/components/patterns';
import type { Gap, GapType, Severity, GapStatus } from '@/types/api';

interface GapCardProps {
  gap: Gap;
  onClick?: () => void;
  compact?: boolean;
}

const severityConfig: Record<Severity, { icon: typeof AlertTriangle; color: string; bgColor: string }> = {
  critical: {
    icon: AlertTriangle,
    color: 'text-[var(--color-critical-500)]',
    bgColor: 'bg-[var(--color-critical-50)]',
  },
  warning: {
    icon: AlertCircle,
    color: 'text-[var(--color-warning-500)]',
    bgColor: 'bg-[var(--color-warning-50)]',
  },
  info: {
    icon: Info,
    color: 'text-[var(--color-info-500)]',
    bgColor: 'bg-[var(--color-info-50)]',
  },
};

const gapTypeConfig: Record<GapType, { icon: typeof Shield; label: string }> = {
  underinsurance: { icon: Shield, label: 'Underinsurance' },
  missing_coverage: { icon: FileWarning, label: 'Missing Coverage' },
  high_deductible: { icon: DollarSign, label: 'High Deductible' },
  expiring: { icon: Calendar, label: 'Expiring' },
  expiration: { icon: Calendar, label: 'Expiration' },
  non_compliant: { icon: AlertCircle, label: 'Non-Compliant' },
  outdated_valuation: { icon: Clock, label: 'Outdated Valuation' },
  missing_document: { icon: FileWarning, label: 'Missing Document' },
  missing_flood: { icon: Droplets, label: 'Missing Flood' },
};

const statusConfig: Record<GapStatus, { label: string; color: string }> = {
  open: { label: 'Open', color: 'critical' },
  acknowledged: { label: 'Acknowledged', color: 'warning' },
  resolved: { label: 'Resolved', color: 'success' },
};

export function GapCard({ gap, onClick, compact = false }: GapCardProps) {
  const severityCfg = severityConfig[gap.severity];
  const typeCfg = gapTypeConfig[gap.gap_type] || { icon: AlertTriangle, label: gap.gap_type };
  const statusCfg = statusConfig[gap.status];
  const SeverityIcon = severityCfg.icon;
  const TypeIcon = typeCfg.icon;

  if (compact) {
    return (
      <motion.div
        className={cn(
          'flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all',
          'border border-[var(--color-border-subtle)]',
          'hover:border-[var(--color-border-default)] hover:shadow-[var(--shadow-elevation-1)]',
          gap.status === 'resolved' && 'opacity-60'
        )}
        onClick={onClick}
        whileHover={{ scale: 1.01 }}
        whileTap={{ scale: 0.99 }}
      >
        <div className={cn('p-1.5 rounded-lg', severityCfg.bgColor)}>
          <SeverityIcon className={cn('h-4 w-4', severityCfg.color)} />
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-medium text-[var(--color-text-primary)] text-sm truncate">
            {gap.title}
          </p>
          <p className="text-xs text-[var(--color-text-muted)] truncate">
            {gap.property_name}
          </p>
        </div>
        <StatusBadge
          severity={gap.severity}
          label={statusCfg.label}
          pulse={gap.status === 'open' && gap.severity === 'critical'}
        />
      </motion.div>
    );
  }

  return (
    <motion.div
      className={cn(
        'p-4 rounded-xl cursor-pointer transition-all',
        'bg-[var(--color-surface)] border border-[var(--color-border-subtle)]',
        'hover:border-[var(--color-border-default)] hover:shadow-[var(--shadow-elevation-2)]',
        gap.status === 'resolved' && 'opacity-60'
      )}
      onClick={onClick}
      whileHover={{ y: -2 }}
      whileTap={{ scale: 0.99 }}
    >
      {/* Header */}
      <div className="flex items-start gap-3 mb-3">
        <div className={cn('p-2 rounded-lg', severityCfg.bgColor)}>
          <SeverityIcon className={cn('h-5 w-5', severityCfg.color)} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-semibold text-[var(--color-text-primary)] truncate">
              {gap.title}
            </h3>
          </div>
          <div className="flex items-center gap-2 text-xs text-[var(--color-text-muted)]">
            <Building2 className="h-3 w-3" />
            <span>{gap.property_name}</span>
            {gap.policy_number && (
              <>
                <span className="text-[var(--color-border-default)]">|</span>
                <span>{gap.policy_number}</span>
              </>
            )}
          </div>
        </div>
        <StatusBadge
          severity={gap.status === 'resolved' ? 'info' : gap.severity}
          label={statusCfg.label}
          pulse={gap.status === 'open' && gap.severity === 'critical'}
        />
      </div>

      {/* Description */}
      <p className="text-sm text-[var(--color-text-secondary)] mb-4 line-clamp-2">
        {gap.description}
      </p>

      {/* Values */}
      {(gap.current_value || gap.recommended_value) && (
        <div className="grid grid-cols-2 gap-3 mb-4">
          {gap.current_value && (
            <div className="p-2 rounded-lg bg-[var(--color-surface-sunken)]">
              <p className="text-xs text-[var(--color-text-muted)] mb-0.5">Current</p>
              <p className="text-sm font-medium text-[var(--color-text-primary)] truncate">
                {gap.current_value}
              </p>
            </div>
          )}
          {gap.recommended_value && (
            <div className="p-2 rounded-lg bg-[var(--color-surface-sunken)]">
              <p className="text-xs text-[var(--color-text-muted)] mb-0.5">Recommended</p>
              <p className="text-sm font-medium text-[var(--color-success-600)] truncate">
                {gap.recommended_value}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between pt-3 border-t border-[var(--color-border-subtle)]">
        <div className="flex items-center gap-2">
          <Badge variant="secondary" size="sm">
            <TypeIcon className="h-3 w-3 mr-1" />
            {typeCfg.label}
          </Badge>
          {gap.gap_amount && (
            <Badge variant="critical" size="sm">
              {formatCurrency(gap.gap_amount)} gap
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-2 text-xs text-[var(--color-text-muted)]">
          {gap.status === 'acknowledged' && gap.acknowledged_at && (
            <span className="flex items-center gap-1">
              <Eye className="h-3 w-3" />
              {formatDate(gap.acknowledged_at)}
            </span>
          )}
          {gap.status === 'resolved' && gap.resolved_at && (
            <span className="flex items-center gap-1">
              <CheckCircle className="h-3 w-3 text-[var(--color-success-500)]" />
              {formatDate(gap.resolved_at)}
            </span>
          )}
          {gap.status === 'open' && (
            <span>Detected {formatDate(gap.created_at)}</span>
          )}
        </div>
      </div>
    </motion.div>
  );
}
