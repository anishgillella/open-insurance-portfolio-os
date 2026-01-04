'use client';

import { cn } from '@/lib/utils';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface TrendIndicatorProps {
  value: number;
  direction: 'up' | 'down' | 'stable';
  period?: string;
  invert?: boolean;
  className?: string;
}

export function TrendIndicator({
  value,
  direction,
  period = 'from last month',
  invert = false,
  className,
}: TrendIndicatorProps) {
  const isPositive = invert ? direction === 'down' : direction === 'up';
  const isNegative = invert ? direction === 'up' : direction === 'down';

  const icons = {
    up: TrendingUp,
    down: TrendingDown,
    stable: Minus,
  };

  const Icon = icons[direction];

  return (
    <div className={cn('flex items-center gap-1 text-sm', className)}>
      <span
        className={cn(
          'flex items-center gap-0.5 font-medium',
          isPositive && 'text-[var(--color-success-600)]',
          isNegative && 'text-[var(--color-critical-600)]',
          direction === 'stable' && 'text-[var(--color-text-muted)]'
        )}
      >
        <Icon className="h-3.5 w-3.5" />
        {Math.abs(value)}%
      </span>
      <span className="text-[var(--color-text-muted)]">{period}</span>
    </div>
  );
}
