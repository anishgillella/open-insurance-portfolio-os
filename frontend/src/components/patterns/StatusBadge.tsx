'use client';

import { cn } from '@/lib/utils';
import { Badge } from '@/components/primitives';
import { motion } from 'framer-motion';
import type { Severity } from '@/types/api';

interface StatusBadgeProps {
  severity: Severity;
  label: string;
  pulse?: boolean;
  icon?: React.ReactNode;
  className?: string;
}

export function StatusBadge({
  severity,
  label,
  pulse = false,
  icon,
  className,
}: StatusBadgeProps) {
  const pulseColors = {
    critical: 'bg-[var(--color-critical-500)]',
    warning: 'bg-[var(--color-warning-500)]',
    info: 'bg-[var(--color-info-500)]',
  };

  return (
    <Badge variant={severity} className={cn('relative', className)}>
      {pulse && (
        <motion.span
          className={cn(
            'absolute -left-0.5 -top-0.5 h-2 w-2 rounded-full',
            pulseColors[severity]
          )}
          animate={{ scale: [1, 1.5, 1], opacity: [1, 0.5, 1] }}
          transition={{ duration: 1.5, repeat: Infinity }}
        />
      )}
      {icon && <span className="mr-1">{icon}</span>}
      {label}
    </Badge>
  );
}
