'use client';

import { motion } from 'framer-motion';
import {
  FileCheck,
  FileX,
  AlertTriangle,
  Clock,
  CheckCircle2,
  XCircle,
  FileQuestion,
  ExternalLink,
} from 'lucide-react';
import { cn, getGrade, getGradeColor } from '@/lib/utils';
import { Card, Badge, Button } from '@/components/primitives';
import { ScoreRing, GradientProgress } from '@/components/patterns';
import { staggerContainer, staggerItem } from '@/lib/motion/variants';
import type { DocumentReadiness } from '@/types/api';

interface ReadinessChecklistProps {
  readiness: DocumentReadiness;
  onUploadDocument?: (documentType: string) => void;
  className?: string;
}

const statusIcons = {
  found: CheckCircle2,
  missing: XCircle,
  stale: AlertTriangle,
  not_applicable: FileQuestion,
};

const statusColors = {
  found: 'text-[var(--color-success-500)]',
  missing: 'text-[var(--color-critical-500)]',
  stale: 'text-[var(--color-warning-500)]',
  not_applicable: 'text-[var(--color-text-muted)]',
};

const statusBgColors = {
  found: 'bg-[var(--color-success-50)] dark:bg-[var(--color-success-500)]/10',
  missing: 'bg-[var(--color-critical-50)] dark:bg-[var(--color-critical-500)]/10',
  stale: 'bg-[var(--color-warning-50)] dark:bg-[var(--color-warning-500)]/10',
  not_applicable: 'bg-[var(--color-surface-sunken)]',
};

const statusLabels = {
  found: 'Ready',
  missing: 'Missing',
  stale: 'Outdated',
  not_applicable: 'N/A',
};

export function ReadinessChecklist({
  readiness,
  onUploadDocument,
  className,
}: ReadinessChecklistProps) {
  const grade = getGrade(readiness.overall_score);
  const gradeColor = getGradeColor(grade);

  // Group documents by status for summary
  const documentsByStatus = readiness.documents.reduce(
    (acc, doc) => {
      acc[doc.status] = (acc[doc.status] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  const totalDocuments = readiness.documents.length;
  const readyCount = documentsByStatus.found || 0;

  return (
    <Card padding="lg" className={className}>
      {/* Header with Score */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-lg bg-[var(--color-primary-50)] dark:bg-[var(--color-primary-500)]/20">
              <FileCheck className="h-5 w-5 text-[var(--color-primary-500)]" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-[var(--color-text-primary)]">
                Document Readiness
              </h3>
              <p className="text-sm text-[var(--color-text-muted)]">
                {readiness.property_name}
              </p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <ScoreRing score={readiness.overall_score} size={64} />
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-4 gap-3 mb-6">
        <div className={cn('p-3 rounded-lg text-center', statusBgColors.found)}>
          <p className="text-2xl font-bold text-[var(--color-success-500)]">
            {documentsByStatus.found || 0}
          </p>
          <p className="text-xs text-[var(--color-text-muted)]">Ready</p>
        </div>
        <div className={cn('p-3 rounded-lg text-center', statusBgColors.missing)}>
          <p className="text-2xl font-bold text-[var(--color-critical-500)]">
            {documentsByStatus.missing || 0}
          </p>
          <p className="text-xs text-[var(--color-text-muted)]">Missing</p>
        </div>
        <div className={cn('p-3 rounded-lg text-center', statusBgColors.stale)}>
          <p className="text-2xl font-bold text-[var(--color-warning-500)]">
            {documentsByStatus.stale || 0}
          </p>
          <p className="text-xs text-[var(--color-text-muted)]">Outdated</p>
        </div>
        <div className="p-3 rounded-lg text-center bg-[var(--color-surface-sunken)]">
          <p className="text-2xl font-bold text-[var(--color-text-primary)]">
            {totalDocuments}
          </p>
          <p className="text-xs text-[var(--color-text-muted)]">Total</p>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-6">
        <div className="flex justify-between text-sm mb-2">
          <span className="text-[var(--color-text-secondary)]">Completion Progress</span>
          <span className="font-medium text-[var(--color-text-primary)]">
            {readyCount}/{totalDocuments} documents
          </span>
        </div>
        <GradientProgress value={readiness.overall_score} size="md" />
      </div>

      {/* Document List */}
      <motion.div
        variants={staggerContainer}
        initial="initial"
        animate="animate"
        className="space-y-2"
      >
        {readiness.documents.map((doc, idx) => {
          const StatusIcon = statusIcons[doc.status];
          const showUpload = doc.status === 'missing' || doc.status === 'stale';

          return (
            <motion.div
              key={idx}
              variants={staggerItem}
              className={cn(
                'p-3 rounded-lg border transition-colors',
                doc.status === 'found'
                  ? 'border-[var(--color-success-200)] dark:border-[var(--color-success-500)]/20'
                  : doc.status === 'missing'
                  ? 'border-[var(--color-critical-200)] dark:border-[var(--color-critical-500)]/20'
                  : doc.status === 'stale'
                  ? 'border-[var(--color-warning-200)] dark:border-[var(--color-warning-500)]/20'
                  : 'border-[var(--color-border-subtle)]',
                statusBgColors[doc.status]
              )}
            >
              <div className="flex items-start gap-3">
                <div className={cn('mt-0.5', statusColors[doc.status])}>
                  <StatusIcon className="h-5 w-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="font-medium text-[var(--color-text-primary)] text-sm">
                      {doc.label}
                    </p>
                    <Badge
                      variant={
                        doc.status === 'found'
                          ? 'success'
                          : doc.status === 'missing'
                          ? 'critical'
                          : doc.status === 'stale'
                          ? 'warning'
                          : 'secondary'
                      }
                    >
                      {statusLabels[doc.status]}
                    </Badge>
                  </div>

                  {/* Document details */}
                  {doc.filename && (
                    <p className="text-xs text-[var(--color-text-muted)] mt-1 flex items-center gap-1">
                      {doc.filename}
                      {doc.age_days !== undefined && (
                        <span className="text-[var(--color-text-muted)]">
                          ({doc.age_days} days old)
                        </span>
                      )}
                    </p>
                  )}

                  {/* Issues */}
                  {doc.issues && doc.issues.length > 0 && (
                    <div className="mt-2 space-y-1">
                      {doc.issues.map((issue, issueIdx) => (
                        <p
                          key={issueIdx}
                          className="text-xs text-[var(--color-critical-600)] dark:text-[var(--color-critical-400)] flex items-start gap-1"
                        >
                          <AlertTriangle className="h-3 w-3 mt-0.5 flex-shrink-0" />
                          {issue}
                        </p>
                      ))}
                    </div>
                  )}
                </div>

                {/* Actions */}
                {showUpload && onUploadDocument && (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => onUploadDocument(doc.type)}
                  >
                    Upload
                  </Button>
                )}

                {doc.document_id && doc.status === 'found' && (
                  <Button
                    variant="ghost"
                    size="sm"
                    rightIcon={<ExternalLink className="h-3.5 w-3.5" />}
                  >
                    View
                  </Button>
                )}
              </div>
            </motion.div>
          );
        })}
      </motion.div>

      {/* Last assessed */}
      <div className="mt-4 pt-4 border-t border-[var(--color-border-subtle)] flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs text-[var(--color-text-muted)]">
          <Clock className="h-3.5 w-3.5" />
          Last assessed: {readiness.last_assessed}
        </div>
        <Button variant="ghost" size="sm">
          Refresh Assessment
        </Button>
      </div>
    </Card>
  );
}
