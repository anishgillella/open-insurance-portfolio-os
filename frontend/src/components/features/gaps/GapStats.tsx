'use client';

import { motion } from 'framer-motion';
import {
  AlertTriangle,
  AlertCircle,
  Info,
  Shield,
  DollarSign,
  FileWarning,
  Calendar,
  Clock,
  Droplets,
  CheckCircle,
  Eye,
  TrendingDown,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { formatCurrency } from '@/lib/utils';
import { Card, Badge } from '@/components/primitives';
import { staggerContainer, staggerItem } from '@/lib/motion/variants';
import type { Gap, GapType } from '@/types/api';

interface GapStatsProps {
  gaps: Gap[];
  className?: string;
}

const gapTypeConfig: Record<GapType, { icon: typeof Shield; label: string; color: string }> = {
  underinsurance: { icon: Shield, label: 'Underinsurance', color: 'var(--color-critical-500)' },
  missing_coverage: { icon: FileWarning, label: 'Missing Coverage', color: 'var(--color-warning-500)' },
  high_deductible: { icon: DollarSign, label: 'High Deductible', color: 'var(--color-critical-500)' },
  expiring: { icon: Calendar, label: 'Expiring', color: 'var(--color-warning-500)' },
  expiration: { icon: Calendar, label: 'Expiration', color: 'var(--color-warning-500)' },
  non_compliant: { icon: AlertCircle, label: 'Non-Compliant', color: 'var(--color-critical-500)' },
  outdated_valuation: { icon: Clock, label: 'Outdated Valuation', color: 'var(--color-info-500)' },
  missing_document: { icon: FileWarning, label: 'Missing Document', color: 'var(--color-info-500)' },
  missing_flood: { icon: Droplets, label: 'Missing Flood', color: 'var(--color-warning-500)' },
};

export function GapStats({ gaps, className }: GapStatsProps) {
  const openGaps = gaps.filter((g) => g.status !== 'resolved');
  const criticalGaps = openGaps.filter((g) => g.severity === 'critical');
  const warningGaps = openGaps.filter((g) => g.severity === 'warning');
  const infoGaps = openGaps.filter((g) => g.severity === 'info');
  const acknowledgedGaps = gaps.filter((g) => g.status === 'acknowledged');
  const resolvedGaps = gaps.filter((g) => g.status === 'resolved');

  // Calculate total gap exposure
  const totalExposure = openGaps.reduce((sum, g) => sum + (g.gap_amount || 0), 0);

  // Group by type
  const byType = openGaps.reduce((acc, gap) => {
    acc[gap.gap_type] = (acc[gap.gap_type] || 0) + 1;
    return acc;
  }, {} as Record<GapType, number>);

  // Get affected properties count
  const affectedProperties = new Set(openGaps.map((g) => g.property_id)).size;

  return (
    <motion.div
      variants={staggerContainer}
      initial="initial"
      animate="animate"
      className={cn('space-y-6', className)}
    >
      {/* Summary Cards */}
      <motion.div variants={staggerItem} className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Total Open */}
        <Card padding="md" className="bg-gradient-to-br from-[var(--color-surface)] to-[var(--color-surface-sunken)]">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-[var(--color-primary-50)]">
              <AlertTriangle className="h-5 w-5 text-[var(--color-primary-500)]" />
            </div>
            <div>
              <p className="text-2xl font-bold text-[var(--color-text-primary)]">{openGaps.length}</p>
              <p className="text-sm text-[var(--color-text-muted)]">Open Gaps</p>
            </div>
          </div>
        </Card>

        {/* Critical */}
        <Card padding="md" className="bg-gradient-to-br from-[var(--color-critical-50)] to-[var(--color-surface)]">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-[var(--color-critical-100)]">
              <AlertTriangle className="h-5 w-5 text-[var(--color-critical-500)]" />
            </div>
            <div>
              <p className="text-2xl font-bold text-[var(--color-critical-600)]">{criticalGaps.length}</p>
              <p className="text-sm text-[var(--color-text-muted)]">Critical</p>
            </div>
          </div>
        </Card>

        {/* Total Exposure */}
        <Card padding="md" className="bg-gradient-to-br from-[var(--color-warning-50)] to-[var(--color-surface)]">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-[var(--color-warning-100)]">
              <TrendingDown className="h-5 w-5 text-[var(--color-warning-500)]" />
            </div>
            <div>
              <p className="text-2xl font-bold text-[var(--color-warning-600)]">
                {formatCurrency(totalExposure)}
              </p>
              <p className="text-sm text-[var(--color-text-muted)]">Total Exposure</p>
            </div>
          </div>
        </Card>

        {/* Affected Properties */}
        <Card padding="md" className="bg-gradient-to-br from-[var(--color-info-50)] to-[var(--color-surface)]">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-[var(--color-info-100)]">
              <Shield className="h-5 w-5 text-[var(--color-info-500)]" />
            </div>
            <div>
              <p className="text-2xl font-bold text-[var(--color-info-600)]">{affectedProperties}</p>
              <p className="text-sm text-[var(--color-text-muted)]">Properties Affected</p>
            </div>
          </div>
        </Card>
      </motion.div>

      {/* Severity Breakdown & Status */}
      <motion.div variants={staggerItem} className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* By Severity */}
        <Card padding="lg">
          <h3 className="text-sm font-semibold text-[var(--color-text-secondary)] uppercase tracking-wide mb-4">
            By Severity
          </h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-[var(--color-critical-500)]" />
                <span className="text-[var(--color-text-primary)]">Critical</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-32 h-2 rounded-full bg-[var(--color-surface-sunken)] overflow-hidden">
                  <div
                    className="h-full bg-[var(--color-critical-500)] rounded-full"
                    style={{ width: `${(criticalGaps.length / Math.max(openGaps.length, 1)) * 100}%` }}
                  />
                </div>
                <Badge variant="critical" size="sm">{criticalGaps.length}</Badge>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-[var(--color-warning-500)]" />
                <span className="text-[var(--color-text-primary)]">Warning</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-32 h-2 rounded-full bg-[var(--color-surface-sunken)] overflow-hidden">
                  <div
                    className="h-full bg-[var(--color-warning-500)] rounded-full"
                    style={{ width: `${(warningGaps.length / Math.max(openGaps.length, 1)) * 100}%` }}
                  />
                </div>
                <Badge variant="warning" size="sm">{warningGaps.length}</Badge>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Info className="h-4 w-4 text-[var(--color-info-500)]" />
                <span className="text-[var(--color-text-primary)]">Info</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-32 h-2 rounded-full bg-[var(--color-surface-sunken)] overflow-hidden">
                  <div
                    className="h-full bg-[var(--color-info-500)] rounded-full"
                    style={{ width: `${(infoGaps.length / Math.max(openGaps.length, 1)) * 100}%` }}
                  />
                </div>
                <Badge variant="info" size="sm">{infoGaps.length}</Badge>
              </div>
            </div>
          </div>
        </Card>

        {/* By Status */}
        <Card padding="lg">
          <h3 className="text-sm font-semibold text-[var(--color-text-secondary)] uppercase tracking-wide mb-4">
            By Status
          </h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-[var(--color-critical-500)]" />
                <span className="text-[var(--color-text-primary)]">Open</span>
              </div>
              <Badge variant="critical" size="sm">{gaps.filter((g) => g.status === 'open').length}</Badge>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Eye className="h-4 w-4 text-[var(--color-warning-500)]" />
                <span className="text-[var(--color-text-primary)]">Acknowledged</span>
              </div>
              <Badge variant="warning" size="sm">{acknowledgedGaps.length}</Badge>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-[var(--color-success-500)]" />
                <span className="text-[var(--color-text-primary)]">Resolved</span>
              </div>
              <Badge variant="success" size="sm">{resolvedGaps.length}</Badge>
            </div>
          </div>
        </Card>
      </motion.div>

      {/* By Type */}
      <motion.div variants={staggerItem}>
        <Card padding="lg">
          <h3 className="text-sm font-semibold text-[var(--color-text-secondary)] uppercase tracking-wide mb-4">
            By Gap Type
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(byType)
              .sort((a, b) => b[1] - a[1])
              .map(([type, count]) => {
                const config = gapTypeConfig[type as GapType];
                if (!config) return null;
                const Icon = config.icon;
                return (
                  <div
                    key={type}
                    className="flex items-center gap-3 p-3 rounded-lg bg-[var(--color-surface-sunken)]"
                  >
                    <Icon className="h-5 w-5" style={{ color: config.color }} />
                    <div>
                      <p className="font-semibold text-[var(--color-text-primary)]">{count}</p>
                      <p className="text-xs text-[var(--color-text-muted)]">{config.label}</p>
                    </div>
                  </div>
                );
              })}
          </div>
        </Card>
      </motion.div>
    </motion.div>
  );
}
