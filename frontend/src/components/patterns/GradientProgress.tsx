'use client';

import { cn, getGrade, getGradeColor } from '@/lib/utils';
import { motion } from 'framer-motion';

interface GradientProgressProps {
  value: number;
  max?: number;
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
  animated?: boolean;
  className?: string;
}

export function GradientProgress({
  value,
  max = 100,
  showLabel = false,
  size = 'md',
  animated = true,
  className,
}: GradientProgressProps) {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));
  const grade = getGrade(percentage);
  const color = getGradeColor(grade);

  const sizes = {
    sm: 'h-1.5',
    md: 'h-2.5',
    lg: 'h-4',
  };

  return (
    <div className={cn('relative', className)}>
      <div
        className={cn(
          'w-full rounded-full bg-gray-100 overflow-hidden',
          sizes[size]
        )}
      >
        <motion.div
          className="h-full rounded-full"
          style={{ backgroundColor: color }}
          initial={animated ? { width: 0 } : { width: `${percentage}%` }}
          animate={{ width: `${percentage}%` }}
          transition={{
            duration: 1,
            ease: [0.22, 1, 0.36, 1],
            delay: 0.2,
          }}
        />
      </div>
      {showLabel && (
        <motion.span
          className="absolute right-0 -top-6 text-sm font-medium text-[var(--color-text-secondary)]"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          {Math.round(percentage)}%
        </motion.span>
      )}
    </div>
  );
}
