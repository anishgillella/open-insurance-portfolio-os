'use client';

import { forwardRef } from 'react';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';

export interface CardProps {
  className?: string;
  variant?: 'default' | 'glass' | 'elevated' | 'interactive';
  padding?: 'sm' | 'md' | 'lg' | 'none';
  children?: React.ReactNode;
  onClick?: () => void;
}

const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant = 'default', padding = 'md', children, onClick }, ref) => {
    const variants = {
      default: 'bg-[var(--color-surface)] border border-[var(--color-border-subtle)] shadow-[var(--shadow-elevation-1)]',
      glass: 'glass shadow-[var(--shadow-glass)]',
      elevated: 'bg-[var(--color-surface)] shadow-[var(--shadow-elevation-3)]',
      interactive: 'bg-[var(--color-surface)] shadow-[var(--shadow-elevation-2)] cursor-pointer',
    };

    const paddings = {
      none: '',
      sm: 'p-4',
      md: 'p-6',
      lg: 'p-8',
    };

    const baseClassName = cn(
      'rounded-xl transition-all duration-300',
      variants[variant],
      paddings[padding],
      className
    );

    if (variant === 'interactive') {
      return (
        <motion.div
          ref={ref}
          className={baseClassName}
          whileHover={{
            y: -4,
            scale: 1.01,
            boxShadow: 'var(--shadow-elevation-4)',
          }}
          transition={{ type: 'spring', stiffness: 300, damping: 25 }}
          onClick={onClick}
        >
          {children}
        </motion.div>
      );
    }

    return (
      <div ref={ref} className={baseClassName} onClick={onClick}>
        {children}
      </div>
    );
  }
);

Card.displayName = 'Card';

const CardHeader = forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn('flex flex-col space-y-1.5', className)}
    {...props}
  />
));
CardHeader.displayName = 'CardHeader';

const CardTitle = forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn(
      'text-lg font-semibold leading-none tracking-tight text-[var(--color-text-primary)]',
      className
    )}
    {...props}
  />
));
CardTitle.displayName = 'CardTitle';

const CardDescription = forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn('text-sm text-[var(--color-text-muted)]', className)}
    {...props}
  />
));
CardDescription.displayName = 'CardDescription';

const CardContent = forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn('', className)} {...props} />
));
CardContent.displayName = 'CardContent';

const CardFooter = forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn('flex items-center pt-4', className)}
    {...props}
  />
));
CardFooter.displayName = 'CardFooter';

export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent };
