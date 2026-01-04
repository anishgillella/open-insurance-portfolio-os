'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X,
  AlertTriangle,
  AlertCircle,
  Info,
  Building2,
  FileText,
  Calendar,
  DollarSign,
  CheckCircle,
  Eye,
  Clock,
  Shield,
  TrendingUp,
  Lightbulb,
  ExternalLink,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { formatCurrency, formatDate, getScoreColor } from '@/lib/utils';
import { Button, Badge, Card } from '@/components/primitives';
import { StatusBadge } from '@/components/patterns';
import { modalOverlay, modalContent } from '@/lib/motion/variants';
import type { Gap, Severity } from '@/types/api';

interface GapDetailModalProps {
  gap: Gap | null;
  isOpen: boolean;
  onClose: () => void;
  onAcknowledge?: (gapId: string, notes: string) => void;
  onResolve?: (gapId: string, notes: string) => void;
}

const severityConfig: Record<Severity, { icon: typeof AlertTriangle; color: string; bgColor: string; label: string }> = {
  critical: {
    icon: AlertTriangle,
    color: 'text-[var(--color-critical-500)]',
    bgColor: 'bg-[var(--color-critical-50)]',
    label: 'Critical',
  },
  warning: {
    icon: AlertCircle,
    color: 'text-[var(--color-warning-500)]',
    bgColor: 'bg-[var(--color-warning-50)]',
    label: 'Warning',
  },
  info: {
    icon: Info,
    color: 'text-[var(--color-info-500)]',
    bgColor: 'bg-[var(--color-info-50)]',
    label: 'Info',
  },
};

// Mock LLM analysis data - would come from API in real implementation
const mockLLMAnalysis = {
  risk_score: 8,
  recommendations: [
    'Increase building coverage to at least 80% of replacement cost to avoid coinsurance penalty',
    'Request updated appraisal to ensure accurate replacement cost valuation',
    'Consider blanket coverage across portfolio to maximize protection',
  ],
  potential_consequences: [
    'Coinsurance penalty could reduce claim payout by 20-30% on partial losses',
    'Out-of-pocket exposure of $2.1M in the event of significant damage',
    'Lender may require immediate remediation to maintain compliance',
  ],
  industry_context: 'NAIOP and BOMA standards recommend maintaining building coverage at 90-100% of replacement cost. Current coverage at 75% is significantly below industry norms.',
  action_priority: 'immediate' as const,
  estimated_impact: '$2.1M potential underinsurance exposure',
};

export function GapDetailModal({
  gap,
  isOpen,
  onClose,
  onAcknowledge,
  onResolve,
}: GapDetailModalProps) {
  const [notes, setNotes] = useState('');
  const [activeTab, setActiveTab] = useState<'details' | 'analysis' | 'history'>('details');
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!gap) return null;

  const severityCfg = severityConfig[gap.severity];
  const SeverityIcon = severityCfg.icon;

  const handleAcknowledge = async () => {
    setIsSubmitting(true);
    await onAcknowledge?.(gap.id, notes);
    setIsSubmitting(false);
    setNotes('');
  };

  const handleResolve = async () => {
    setIsSubmitting(true);
    await onResolve?.(gap.id, notes);
    setIsSubmitting(false);
    setNotes('');
    onClose();
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <motion.div
            variants={modalOverlay}
            initial="initial"
            animate="animate"
            exit="exit"
            className="absolute inset-0 bg-black/50 backdrop-blur-sm"
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            variants={modalContent}
            initial="initial"
            animate="animate"
            exit="exit"
            className="relative w-full max-w-3xl max-h-[90vh] overflow-hidden rounded-2xl bg-[var(--color-surface)] shadow-[var(--shadow-elevation-4)]"
          >
            {/* Header */}
            <div className="sticky top-0 z-10 bg-[var(--color-surface)] border-b border-[var(--color-border-subtle)] p-6">
              <div className="flex items-start gap-4">
                <div className={cn('p-3 rounded-xl', severityCfg.bgColor)}>
                  <SeverityIcon className={cn('h-6 w-6', severityCfg.color)} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-2">
                    <h2 className="text-xl font-bold text-[var(--color-text-primary)]">
                      {gap.title}
                    </h2>
                    <StatusBadge
                      severity={gap.status === 'resolved' ? 'info' : gap.severity}
                      label={gap.status.charAt(0).toUpperCase() + gap.status.slice(1)}
                      pulse={gap.status === 'open' && gap.severity === 'critical'}
                    />
                  </div>
                  <div className="flex items-center gap-4 text-sm text-[var(--color-text-muted)]">
                    <span className="flex items-center gap-1">
                      <Building2 className="h-4 w-4" />
                      {gap.property_name}
                    </span>
                    {gap.policy_number && (
                      <span className="flex items-center gap-1">
                        <FileText className="h-4 w-4" />
                        {gap.policy_number}
                      </span>
                    )}
                    <span className="flex items-center gap-1">
                      <Calendar className="h-4 w-4" />
                      Detected {formatDate(gap.created_at)}
                    </span>
                  </div>
                </div>
                <button
                  onClick={onClose}
                  className="p-2 rounded-lg hover:bg-[var(--color-surface-sunken)] transition-colors"
                >
                  <X className="h-5 w-5 text-[var(--color-text-muted)]" />
                </button>
              </div>

              {/* Tabs */}
              <div className="flex gap-1 mt-6">
                {(['details', 'analysis', 'history'] as const).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={cn(
                      'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                      activeTab === tab
                        ? 'bg-[var(--color-primary-50)] text-[var(--color-primary-600)]'
                        : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-sunken)]'
                    )}
                  >
                    {tab.charAt(0).toUpperCase() + tab.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            {/* Content */}
            <div className="overflow-y-auto p-6" style={{ maxHeight: 'calc(90vh - 200px)' }}>
              {activeTab === 'details' && (
                <div className="space-y-6">
                  {/* Description */}
                  <div>
                    <h3 className="text-sm font-semibold text-[var(--color-text-secondary)] uppercase tracking-wide mb-2">
                      Description
                    </h3>
                    <p className="text-[var(--color-text-primary)]">{gap.description}</p>
                  </div>

                  {/* Values Comparison */}
                  {(gap.current_value || gap.recommended_value) && (
                    <div className="grid grid-cols-2 gap-4">
                      {gap.current_value && (
                        <Card padding="md" className="bg-[var(--color-surface-sunken)]">
                          <div className="flex items-center gap-2 mb-2">
                            <AlertCircle className="h-4 w-4 text-[var(--color-critical-500)]" />
                            <span className="text-sm font-medium text-[var(--color-text-secondary)]">
                              Current Value
                            </span>
                          </div>
                          <p className="text-lg font-semibold text-[var(--color-text-primary)]">
                            {gap.current_value}
                          </p>
                        </Card>
                      )}
                      {gap.recommended_value && (
                        <Card padding="md" className="bg-[var(--color-surface-sunken)]">
                          <div className="flex items-center gap-2 mb-2">
                            <CheckCircle className="h-4 w-4 text-[var(--color-success-500)]" />
                            <span className="text-sm font-medium text-[var(--color-text-secondary)]">
                              Recommended
                            </span>
                          </div>
                          <p className="text-lg font-semibold text-[var(--color-success-600)]">
                            {gap.recommended_value}
                          </p>
                        </Card>
                      )}
                    </div>
                  )}

                  {/* Gap Amount */}
                  {gap.gap_amount && (
                    <div className="flex items-center gap-4 p-4 rounded-xl bg-[var(--color-critical-50)] border border-[var(--color-critical-200)]">
                      <DollarSign className="h-8 w-8 text-[var(--color-critical-500)]" />
                      <div>
                        <p className="text-sm text-[var(--color-critical-600)]">Coverage Gap</p>
                        <p className="text-2xl font-bold text-[var(--color-critical-700)]">
                          {formatCurrency(gap.gap_amount)}
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Action Section */}
                  {gap.status !== 'resolved' && (
                    <div className="pt-6 border-t border-[var(--color-border-subtle)]">
                      <h3 className="text-sm font-semibold text-[var(--color-text-secondary)] uppercase tracking-wide mb-4">
                        Take Action
                      </h3>
                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-[var(--color-text-secondary)] mb-2">
                            Notes (optional)
                          </label>
                          <textarea
                            value={notes}
                            onChange={(e) => setNotes(e.target.value)}
                            placeholder="Add any notes about this action..."
                            className="w-full px-4 py-3 rounded-lg border border-[var(--color-border-default)] bg-[var(--color-surface)] text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary-500)]"
                            rows={3}
                          />
                        </div>
                        <div className="flex gap-3">
                          {gap.status === 'open' && (
                            <Button
                              variant="secondary"
                              onClick={handleAcknowledge}
                              disabled={isSubmitting}
                              leftIcon={<Eye className="h-4 w-4" />}
                            >
                              Acknowledge
                            </Button>
                          )}
                          <Button
                            variant="primary"
                            onClick={handleResolve}
                            disabled={isSubmitting}
                            leftIcon={<CheckCircle className="h-4 w-4" />}
                          >
                            Mark Resolved
                          </Button>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Resolution Info */}
                  {gap.status === 'resolved' && gap.resolution_notes && (
                    <div className="p-4 rounded-xl bg-[var(--color-success-50)] border border-[var(--color-success-200)]">
                      <div className="flex items-center gap-2 mb-2">
                        <CheckCircle className="h-5 w-5 text-[var(--color-success-500)]" />
                        <span className="font-medium text-[var(--color-success-700)]">Resolved</span>
                        {gap.resolved_at && (
                          <span className="text-sm text-[var(--color-success-600)]">
                            on {formatDate(gap.resolved_at)}
                          </span>
                        )}
                      </div>
                      <p className="text-[var(--color-success-700)]">{gap.resolution_notes}</p>
                      {gap.resolved_by && (
                        <p className="text-sm text-[var(--color-success-600)] mt-2">
                          by {gap.resolved_by}
                        </p>
                      )}
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'analysis' && (
                <div className="space-y-6">
                  {/* Risk Score */}
                  <div className="flex items-center gap-4 p-4 rounded-xl bg-[var(--color-surface-sunken)]">
                    <div
                      className="w-16 h-16 rounded-full flex items-center justify-center text-white text-2xl font-bold"
                      style={{ backgroundColor: getScoreColor(100 - mockLLMAnalysis.risk_score * 10) }}
                    >
                      {mockLLMAnalysis.risk_score}
                    </div>
                    <div>
                      <p className="text-sm text-[var(--color-text-muted)]">AI Risk Score</p>
                      <p className="text-lg font-semibold text-[var(--color-text-primary)]">
                        {mockLLMAnalysis.risk_score >= 7 ? 'High Risk' : mockLLMAnalysis.risk_score >= 4 ? 'Medium Risk' : 'Low Risk'}
                      </p>
                      <p className="text-sm text-[var(--color-text-secondary)]">
                        Priority: <span className="font-medium capitalize">{mockLLMAnalysis.action_priority.replace('_', ' ')}</span>
                      </p>
                    </div>
                  </div>

                  {/* Estimated Impact */}
                  <Card padding="md">
                    <div className="flex items-center gap-2 mb-2">
                      <TrendingUp className="h-5 w-5 text-[var(--color-warning-500)]" />
                      <h3 className="font-semibold text-[var(--color-text-primary)]">Estimated Impact</h3>
                    </div>
                    <p className="text-[var(--color-text-secondary)]">{mockLLMAnalysis.estimated_impact}</p>
                  </Card>

                  {/* Recommendations */}
                  <div>
                    <div className="flex items-center gap-2 mb-3">
                      <Lightbulb className="h-5 w-5 text-[var(--color-primary-500)]" />
                      <h3 className="font-semibold text-[var(--color-text-primary)]">AI Recommendations</h3>
                    </div>
                    <ul className="space-y-2">
                      {mockLLMAnalysis.recommendations.map((rec, i) => (
                        <li key={i} className="flex items-start gap-3 p-3 rounded-lg bg-[var(--color-surface-sunken)]">
                          <span className="flex-shrink-0 w-6 h-6 rounded-full bg-[var(--color-primary-100)] text-[var(--color-primary-600)] text-sm font-medium flex items-center justify-center">
                            {i + 1}
                          </span>
                          <span className="text-[var(--color-text-primary)]">{rec}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Potential Consequences */}
                  <div>
                    <div className="flex items-center gap-2 mb-3">
                      <AlertTriangle className="h-5 w-5 text-[var(--color-critical-500)]" />
                      <h3 className="font-semibold text-[var(--color-text-primary)]">Potential Consequences</h3>
                    </div>
                    <ul className="space-y-2">
                      {mockLLMAnalysis.potential_consequences.map((consequence, i) => (
                        <li key={i} className="flex items-start gap-3 p-3 rounded-lg bg-[var(--color-critical-50)]">
                          <AlertCircle className="h-5 w-5 text-[var(--color-critical-500)] flex-shrink-0 mt-0.5" />
                          <span className="text-[var(--color-text-primary)]">{consequence}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Industry Context */}
                  <Card padding="md" className="bg-[var(--color-info-50)] border border-[var(--color-info-200)]">
                    <div className="flex items-center gap-2 mb-2">
                      <Shield className="h-5 w-5 text-[var(--color-info-500)]" />
                      <h3 className="font-semibold text-[var(--color-info-700)]">Industry Context</h3>
                    </div>
                    <p className="text-[var(--color-info-700)]">{mockLLMAnalysis.industry_context}</p>
                  </Card>
                </div>
              )}

              {activeTab === 'history' && (
                <div className="space-y-4">
                  {/* Timeline */}
                  <div className="relative">
                    <div className="absolute left-4 top-0 bottom-0 w-px bg-[var(--color-border-default)]" />

                    {/* Created */}
                    <div className="relative flex gap-4 pb-6">
                      <div className="w-8 h-8 rounded-full bg-[var(--color-info-100)] flex items-center justify-center z-10">
                        <Clock className="h-4 w-4 text-[var(--color-info-500)]" />
                      </div>
                      <div className="flex-1 pt-1">
                        <p className="font-medium text-[var(--color-text-primary)]">Gap Detected</p>
                        <p className="text-sm text-[var(--color-text-muted)]">{formatDate(gap.created_at)}</p>
                        <p className="text-sm text-[var(--color-text-secondary)] mt-1">
                          Automated detection identified this coverage gap
                        </p>
                      </div>
                    </div>

                    {/* Acknowledged */}
                    {gap.acknowledged_at && (
                      <div className="relative flex gap-4 pb-6">
                        <div className="w-8 h-8 rounded-full bg-[var(--color-warning-100)] flex items-center justify-center z-10">
                          <Eye className="h-4 w-4 text-[var(--color-warning-500)]" />
                        </div>
                        <div className="flex-1 pt-1">
                          <p className="font-medium text-[var(--color-text-primary)]">Acknowledged</p>
                          <p className="text-sm text-[var(--color-text-muted)]">
                            {formatDate(gap.acknowledged_at)} by {gap.acknowledged_by}
                          </p>
                        </div>
                      </div>
                    )}

                    {/* Resolved */}
                    {gap.resolved_at && (
                      <div className="relative flex gap-4">
                        <div className="w-8 h-8 rounded-full bg-[var(--color-success-100)] flex items-center justify-center z-10">
                          <CheckCircle className="h-4 w-4 text-[var(--color-success-500)]" />
                        </div>
                        <div className="flex-1 pt-1">
                          <p className="font-medium text-[var(--color-text-primary)]">Resolved</p>
                          <p className="text-sm text-[var(--color-text-muted)]">
                            {formatDate(gap.resolved_at)} by {gap.resolved_by}
                          </p>
                          {gap.resolution_notes && (
                            <p className="text-sm text-[var(--color-text-secondary)] mt-1">
                              {gap.resolution_notes}
                            </p>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="sticky bottom-0 bg-[var(--color-surface)] border-t border-[var(--color-border-subtle)] p-4 flex justify-between items-center">
              <Button variant="ghost" onClick={onClose}>
                Close
              </Button>
              <Button
                variant="ghost"
                rightIcon={<ExternalLink className="h-4 w-4" />}
                onClick={() => window.open(`/properties/${gap.property_id}`, '_blank')}
              >
                View Property
              </Button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
