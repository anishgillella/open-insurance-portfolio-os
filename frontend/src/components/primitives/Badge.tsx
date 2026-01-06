'use client';

import { cn } from '@/lib/utils';
import { cva, type VariantProps } from 'class-variance-authority';

const badgeVariants = cva(
  'inline-flex items-center rounded-md px-2.5 py-0.5 text-xs font-medium transition-colors',
  {
    variants: {
      variant: {
        critical:
          'bg-[var(--color-critical-50)] text-[var(--color-critical-600)] border border-[var(--color-critical-200)]',
        warning:
          'bg-[var(--color-warning-50)] text-[var(--color-warning-600)] border border-[var(--color-warning-200)]',
        success:
          'bg-[var(--color-success-50)] text-[var(--color-success-600)] border border-[var(--color-success-200)]',
        info: 'bg-[var(--color-info-50)] text-[var(--color-info-600)] border border-[var(--color-info-200)]',
        neutral:
          'bg-[var(--color-surface-sunken)] text-[var(--color-text-secondary)] border border-[var(--color-border-default)]',
        secondary:
          'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-200 border border-gray-200 dark:border-gray-700',
        primary:
          'bg-[var(--color-primary-50)] text-[var(--color-primary-600)] border border-[var(--color-primary-200)]',
        // Solid variants
        'critical-solid': 'gradient-critical text-white',
        'warning-solid': 'gradient-warning text-white',
        'success-solid': 'gradient-success text-white',
        'primary-solid': 'gradient-primary text-white',
      },
      size: {
        sm: 'text-[10px] px-1.5 py-0.5',
        md: 'text-xs px-2.5 py-0.5',
        lg: 'text-sm px-3 py-1',
      },
    },
    defaultVariants: {
      variant: 'neutral',
      size: 'md',
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {
  dot?: boolean;
}

export function Badge({
  className,
  variant,
  size,
  dot,
  children,
  ...props
}: BadgeProps) {
  const getDotColor = () => {
    switch (variant) {
      case 'critical':
      case 'critical-solid':
        return 'bg-[var(--color-critical-500)]';
      case 'warning':
      case 'warning-solid':
        return 'bg-[var(--color-warning-500)]';
      case 'success':
      case 'success-solid':
        return 'bg-[var(--color-success-500)]';
      case 'info':
        return 'bg-[var(--color-info-500)]';
      case 'primary':
      case 'primary-solid':
        return 'bg-[var(--color-primary-500)]';
      default:
        return 'bg-[var(--color-text-muted)]';
    }
  };

  return (
    <span
      className={cn(badgeVariants({ variant, size }), className)}
      {...props}
    >
      {dot && (
        <span
          className={cn('mr-1.5 h-1.5 w-1.5 rounded-full', getDotColor())}
        />
      )}
      {children}
    </span>
  );
}
