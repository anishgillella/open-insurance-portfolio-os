'use client';

import { motion } from 'framer-motion';
import { ChevronDown, AlertTriangle, CheckCircle } from 'lucide-react';
import { useState } from 'react';
import { cn, getScoreColor } from '@/lib/utils';
import { GradientProgress } from '@/components/patterns';
import type { HealthComponent } from '@/lib/mock-data';

interface ComponentBreakdownProps {
  components: HealthComponent[];
  className?: string;
}

function ComponentRow({
  component,
  index,
}: {
  component: HealthComponent;
  index: number;
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const color = getScoreColor(component.score);
  const hasIssues = component.issues.length > 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1, duration: 0.4 }}
      className="border border-[var(--color-border-subtle)] rounded-xl overflow-hidden"
    >
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-4 text-left hover:bg-[var(--color-surface-sunken)] transition-colors"
      >
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <div
              className="w-10 h-10 rounded-lg flex items-center justify-center text-white font-bold text-sm"
              style={{ backgroundColor: color }}
            >
              {component.score}
            </div>
            <div>
              <h3 className="font-semibold text-[var(--color-text-primary)]">
                {component.name}
              </h3>
              <p className="text-sm text-[var(--color-text-muted)]">
                Weight: {component.weight}%
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {hasIssues ? (
              <div className="flex items-center gap-1 text-[var(--color-warning-500)]">
                <AlertTriangle className="h-4 w-4" />
                <span className="text-sm font-medium">{component.issues.length} issues</span>
              </div>
            ) : (
              <div className="flex items-center gap-1 text-[var(--color-success-500)]">
                <CheckCircle className="h-4 w-4" />
                <span className="text-sm font-medium">All good</span>
              </div>
            )}
            <ChevronDown
              className={cn(
                'h-5 w-5 text-[var(--color-text-muted)] transition-transform',
                isExpanded && 'rotate-180'
              )}
            />
          </div>
        </div>

        <GradientProgress value={component.score} size="md" />
      </button>

      <motion.div
        initial={false}
        animate={{
          height: isExpanded ? 'auto' : 0,
          opacity: isExpanded ? 1 : 0,
        }}
        transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
        className="overflow-hidden"
      >
        <div className="px-4 pb-4 pt-2 border-t border-[var(--color-border-subtle)]">
          <p className="text-sm text-[var(--color-text-secondary)] mb-3">
            {component.description}
          </p>

          {hasIssues && (
            <div className="space-y-2">
              <p className="text-sm font-medium text-[var(--color-text-primary)]">Issues:</p>
              <ul className="space-y-2">
                {component.issues.map((issue, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-2 text-sm text-[var(--color-warning-600)] dark:text-[var(--color-warning-400)] bg-[var(--color-warning-50)] dark:bg-[var(--color-warning-500)]/10 p-2 rounded-lg"
                  >
                    <AlertTriangle className="h-4 w-4 flex-shrink-0 mt-0.5" />
                    <span>{issue}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
}

export function ComponentBreakdown({ components, className }: ComponentBreakdownProps) {
  // Calculate weighted score
  const weightedScore = components.reduce((acc, c) => acc + c.score * (c.weight / 100), 0);

  return (
    <div className={cn('space-y-4', className)}>
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">
          Component Breakdown
        </h2>
        <div className="text-sm text-[var(--color-text-muted)]">
          Weighted Score: <span className="font-semibold text-[var(--color-text-primary)]">{Math.round(weightedScore)}</span>
        </div>
      </div>

      <div className="space-y-3">
        {components.map((component, index) => (
          <ComponentRow key={component.name} component={component} index={index} />
        ))}
      </div>
    </div>
  );
}
