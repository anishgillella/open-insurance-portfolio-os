'use client';

import { cn } from '@/lib/utils';
import { motion, useSpring, useTransform, useInView } from 'framer-motion';
import { useRef, useEffect, useState } from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { GlassCard } from './GlassCard';

interface DataCardProps {
  label: string;
  value: string | number;
  prefix?: string;
  suffix?: string;
  trend?: {
    value: number;
    direction: 'up' | 'down' | 'stable';
    period?: string;
  };
  icon?: React.ReactNode;
  variant?: 'default' | 'glass';
  size?: 'sm' | 'md' | 'lg';
  animate?: boolean;
  onClick?: () => void;
  className?: string;
}

function CountUp({
  end,
  prefix = '',
  suffix = '',
  duration = 1.5,
}: {
  end: number;
  prefix?: string;
  suffix?: string;
  duration?: number;
}) {
  const ref = useRef<HTMLSpanElement>(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });
  const [hasAnimated, setHasAnimated] = useState(false);

  const spring = useSpring(0, {
    stiffness: 50,
    damping: 20,
  });

  const display = useTransform(spring, (value) => {
    const formatted = value.toLocaleString('en-US', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    });
    return `${prefix}${formatted}${suffix}`;
  });

  useEffect(() => {
    if (isInView && !hasAnimated) {
      spring.set(end);
      setHasAnimated(true);
    }
  }, [isInView, end, spring, hasAnimated]);

  return <motion.span ref={ref}>{display}</motion.span>;
}

export function DataCard({
  label,
  value,
  prefix = '',
  suffix = '',
  trend,
  icon,
  variant = 'default',
  size = 'md',
  animate = true,
  onClick,
  className,
}: DataCardProps) {
  const sizes = {
    sm: { value: 'text-2xl', label: 'text-xs', icon: 'p-2' },
    md: { value: 'text-3xl', label: 'text-sm', icon: 'p-3' },
    lg: { value: 'text-4xl', label: 'text-base', icon: 'p-4' },
  };

  const TrendIcon =
    trend?.direction === 'up'
      ? TrendingUp
      : trend?.direction === 'down'
      ? TrendingDown
      : Minus;

  const content = (
    <>
      <div className="flex items-start justify-between">
        <div>
          <p
            className={cn(
              'text-[var(--color-text-muted)] font-medium',
              sizes[size].label
            )}
          >
            {label}
          </p>
          <p
            className={cn(
              'font-bold text-[var(--color-text-primary)] mt-1 font-mono',
              sizes[size].value
            )}
          >
            {animate && typeof value === 'number' ? (
              <CountUp end={value} prefix={prefix} suffix={suffix} />
            ) : (
              `${prefix}${typeof value === 'number' ? value.toLocaleString() : value}${suffix}`
            )}
          </p>
          {trend && (
            <div className="flex items-center gap-1 mt-2">
              <span
                className={cn(
                  'flex items-center gap-0.5 text-sm font-medium',
                  trend.direction === 'up' && 'text-[var(--color-success-600)]',
                  trend.direction === 'down' && 'text-[var(--color-critical-600)]',
                  trend.direction === 'stable' && 'text-[var(--color-text-muted)]'
                )}
              >
                <TrendIcon className="h-3.5 w-3.5" />
                {Math.abs(trend.value)}%
              </span>
              {trend.period && (
                <span className="text-sm text-[var(--color-text-muted)]">
                  {trend.period}
                </span>
              )}
            </div>
          )}
        </div>
        {icon && (
          <div
            className={cn(
              'bg-[var(--color-primary-50)] rounded-xl text-[var(--color-primary-500)]',
              sizes[size].icon
            )}
          >
            {icon}
          </div>
        )}
      </div>
    </>
  );

  if (variant === 'glass') {
    return (
      <GlassCard
        className={cn('p-6', onClick && 'cursor-pointer', className)}
        onClick={onClick}
      >
        {content}
      </GlassCard>
    );
  }

  return (
    <motion.div
      className={cn(
        'p-6 bg-white rounded-xl shadow-[var(--shadow-elevation-2)] transition-all',
        onClick && 'cursor-pointer hover:shadow-[var(--shadow-elevation-3)]',
        className
      )}
      whileHover={onClick ? { y: -2 } : undefined}
      onClick={onClick}
    >
      {content}
    </motion.div>
  );
}
