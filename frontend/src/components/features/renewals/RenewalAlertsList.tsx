'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Bell,
  AlertTriangle,
  CheckCircle,
  Clock,
  ChevronRight,
  Settings,
  Brain,
  X,
  Check,
  Calendar,
} from 'lucide-react';
import { cn, formatDate } from '@/lib/utils';
import { Card, Badge, Button } from '@/components/primitives';
import { StatusBadge } from '@/components/patterns';
import { staggerContainer, staggerItem } from '@/lib/motion/variants';
import type { RenewalAlert, RenewalAlertStatus } from '@/types/api';

interface RenewalAlertsListProps {
  alerts: RenewalAlert[];
  onAcknowledge?: (alertId: string) => void;
  onResolve?: (alertId: string) => void;
  onConfigureAlerts?: (propertyId: string) => void;
  showPropertyName?: boolean;
  className?: string;
}

const statusIcons = {
  pending: AlertTriangle,
  acknowledged: Clock,
  resolved: CheckCircle,
  expired: X,
};

const statusColors = {
  pending: 'border-l-[var(--color-warning-500)]',
  acknowledged: 'border-l-[var(--color-primary-500)]',
  resolved: 'border-l-[var(--color-success-500)]',
  expired: 'border-l-[var(--color-text-muted)]',
};

export function RenewalAlertsList({
  alerts,
  onAcknowledge,
  onResolve,
  onConfigureAlerts,
  showPropertyName = true,
  className,
}: RenewalAlertsListProps) {
  const [expandedAlertId, setExpandedAlertId] = useState<string | null>(null);
  const [filter, setFilter] = useState<RenewalAlertStatus | 'all'>('all');

  const filteredAlerts = filter === 'all'
    ? alerts
    : alerts.filter((a) => a.status === filter);

  // Count by status
  const statusCounts = alerts.reduce(
    (acc, alert) => {
      acc[alert.status] = (acc[alert.status] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  return (
    <Card padding="lg" className={className}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-[var(--color-warning-50)] dark:bg-[var(--color-warning-500)]/20">
            <Bell className="h-5 w-5 text-[var(--color-warning-500)]" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-[var(--color-text-primary)]">
              Renewal Alerts
            </h3>
            <p className="text-sm text-[var(--color-text-muted)]">
              {alerts.length} total alerts
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {statusCounts.pending > 0 && (
            <Badge variant="warning" dot>
              {statusCounts.pending} pending
            </Badge>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2 mb-4 overflow-x-auto pb-2">
        {(['all', 'pending', 'acknowledged', 'resolved'] as const).map((status) => (
          <Button
            key={status}
            variant={filter === status ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => setFilter(status)}
          >
            {status === 'all' ? 'All' : status.charAt(0).toUpperCase() + status.slice(1)}
            {status !== 'all' && statusCounts[status] > 0 && (
              <span className="ml-1 opacity-70">({statusCounts[status]})</span>
            )}
          </Button>
        ))}
      </div>

      {/* Alerts List - Scrollable container */}
      <motion.div
        variants={staggerContainer}
        initial="initial"
        animate="animate"
        className="space-y-3 max-h-[400px] overflow-y-auto pr-1"
      >
        {filteredAlerts.length === 0 ? (
          <div className="text-center py-8">
            <CheckCircle className="h-12 w-12 text-[var(--color-success-500)] mx-auto mb-3" />
            <p className="text-[var(--color-text-secondary)]">
              {filter === 'all' ? 'No alerts' : `No ${filter} alerts`}
            </p>
          </div>
        ) : (
          filteredAlerts.map((alert) => {
            const StatusIcon = statusIcons[alert.status];
            const isExpanded = expandedAlertId === alert.id;

            return (
              <motion.div
                key={alert.id}
                variants={staggerItem}
                className={cn(
                  'border-l-4 rounded-lg bg-[var(--color-surface-sunken)] overflow-hidden transition-all',
                  statusColors[alert.status]
                )}
              >
                {/* Alert Header */}
                <div
                  className="p-4 cursor-pointer hover:bg-[var(--color-surface)] transition-colors"
                  onClick={() => setExpandedAlertId(isExpanded ? null : alert.id)}
                >
                  <div className="flex items-start gap-3">
                    <div
                      className={cn(
                        'p-1.5 rounded-lg',
                        alert.severity === 'critical'
                          ? 'bg-[var(--color-critical-50)] text-[var(--color-critical-500)]'
                          : alert.severity === 'warning'
                          ? 'bg-[var(--color-warning-50)] text-[var(--color-warning-500)]'
                          : 'bg-[var(--color-info-50)] text-[var(--color-info-500)]'
                      )}
                    >
                      <AlertTriangle className="h-4 w-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <p className="font-medium text-[var(--color-text-primary)] text-sm">
                          {alert.title}
                        </p>
                        <StatusBadge
                          severity={alert.severity}
                          label={alert.severity}
                          pulse={alert.severity === 'critical' && alert.status === 'pending'}
                        />
                      </div>
                      {showPropertyName && (
                        <p className="text-xs text-[var(--color-text-muted)] mt-1">
                          {alert.property_name}
                        </p>
                      )}
                      <p className="text-sm text-[var(--color-text-secondary)] mt-1">
                        {alert.message}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="text-right">
                        <p className="text-xs text-[var(--color-text-muted)]">
                          {alert.days_until_expiration}d left
                        </p>
                        <p className="text-xs text-[var(--color-text-muted)]">
                          Expires {formatDate(alert.expiration_date)}
                        </p>
                      </div>
                      <ChevronRight
                        className={cn(
                          'h-5 w-5 text-[var(--color-text-muted)] transition-transform',
                          isExpanded && 'rotate-90'
                        )}
                      />
                    </div>
                  </div>
                </div>

                {/* Expanded Content */}
                <AnimatePresence>
                  {isExpanded && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="border-t border-[var(--color-border-subtle)]"
                    >
                      <div className="p-4 space-y-4">
                        {/* LLM Priority Score */}
                        <div className="flex items-center gap-4">
                          <div className="flex items-center gap-2">
                            <Brain className="h-4 w-4 text-[var(--color-primary-500)]" />
                            <span className="text-sm text-[var(--color-text-secondary)]">
                              AI Priority Score:
                            </span>
                            <span className="text-sm font-semibold text-[var(--color-text-primary)]">
                              {alert.llm_priority_score}/100
                            </span>
                          </div>
                          <div className="flex-1 h-2 rounded-full bg-[var(--color-surface)]">
                            <div
                              className={cn(
                                'h-full rounded-full',
                                alert.llm_priority_score >= 80
                                  ? 'bg-[var(--color-critical-500)]'
                                  : alert.llm_priority_score >= 60
                                  ? 'bg-[var(--color-warning-500)]'
                                  : 'bg-[var(--color-success-500)]'
                              )}
                              style={{ width: `${alert.llm_priority_score}%` }}
                            />
                          </div>
                        </div>

                        {/* LLM Strategy */}
                        <div className="p-3 rounded-lg bg-[var(--color-primary-50)] dark:bg-[var(--color-primary-500)]/10 border border-[var(--color-primary-100)] dark:border-[var(--color-primary-500)]/20">
                          <div className="flex items-center gap-2 mb-2">
                            <Brain className="h-4 w-4 text-[var(--color-primary-500)]" />
                            <p className="text-sm font-medium text-[var(--color-primary-700)] dark:text-[var(--color-primary-400)]">
                              AI Strategy Recommendation
                            </p>
                          </div>
                          <p className="text-sm text-[var(--color-text-primary)]">
                            {alert.llm_renewal_strategy}
                          </p>
                        </div>

                        {/* Key Actions */}
                        <div>
                          <p className="text-sm font-medium text-[var(--color-text-secondary)] mb-2">
                            Key Actions
                          </p>
                          <div className="space-y-1">
                            {alert.llm_key_actions.map((action, idx) => (
                              <div
                                key={idx}
                                className="flex items-start gap-2 p-2 rounded-lg hover:bg-[var(--color-surface)] transition-colors"
                              >
                                <div className="flex items-center justify-center w-5 h-5 rounded-full bg-[var(--color-primary-100)] dark:bg-[var(--color-primary-500)]/20 text-[var(--color-primary-600)] dark:text-[var(--color-primary-400)] text-xs font-semibold flex-shrink-0">
                                  {idx + 1}
                                </div>
                                <p className="text-sm text-[var(--color-text-primary)]">{action}</p>
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* Actions */}
                        <div
                          className="flex items-center gap-2 pt-2 border-t border-[var(--color-border-subtle)]"
                          onClick={(e) => e.stopPropagation()}
                        >
                          {alert.status === 'pending' && onAcknowledge && (
                            <Button
                              variant="secondary"
                              size="sm"
                              leftIcon={<Check className="h-4 w-4" />}
                              onClick={() => onAcknowledge(alert.id)}
                            >
                              Acknowledge
                            </Button>
                          )}
                          {(alert.status === 'pending' || alert.status === 'acknowledged') &&
                            onResolve && (
                              <Button
                                variant="success"
                                size="sm"
                                leftIcon={<CheckCircle className="h-4 w-4" />}
                                onClick={() => onResolve(alert.id)}
                              >
                                Mark Resolved
                              </Button>
                            )}
                          {onConfigureAlerts && (
                            <Button
                              variant="ghost"
                              size="sm"
                              leftIcon={<Settings className="h-4 w-4" />}
                              onClick={() => onConfigureAlerts(alert.property_id)}
                            >
                              Configure Alerts
                            </Button>
                          )}
                        </div>

                        {/* Timestamps */}
                        <div className="flex items-center gap-4 text-xs text-[var(--color-text-muted)]">
                          <div className="flex items-center gap-1">
                            <Calendar className="h-3 w-3" />
                            Created: {formatDate(alert.created_at)}
                          </div>
                          {alert.acknowledged_at && (
                            <div>Acknowledged: {formatDate(alert.acknowledged_at)}</div>
                          )}
                          {alert.resolved_at && (
                            <div>Resolved: {formatDate(alert.resolved_at)}</div>
                          )}
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            );
          })
        )}
      </motion.div>
    </Card>
  );
}
