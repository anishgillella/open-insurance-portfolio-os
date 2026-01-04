'use client';

import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';
import type { ReactNode } from 'react';

interface GlassCardProps {
  className?: string;
  gradient?: string;
  hover?: boolean;
  glow?: 'primary' | 'success' | 'warning' | 'critical';
  children: ReactNode;
  onClick?: () => void;
}

const glowColors = {
  primary: 'shadow-[var(--shadow-glow-primary)]',
  success: 'shadow-[var(--shadow-glow-success)]',
  warning: 'shadow-[var(--shadow-glow-warning)]',
  critical: 'shadow-[var(--shadow-glow-critical)]',
};

export function GlassCard({
  className,
  gradient,
  hover = true,
  glow,
  children,
  onClick,
}: GlassCardProps) {
  const baseClassName = cn(
    'relative overflow-hidden rounded-2xl',
    'bg-white/70 dark:bg-[#1C1C24]/80 backdrop-blur-xl',
    'border border-white/20 dark:border-white/10',
    'shadow-[var(--shadow-glass)]',
    hover && 'transition-all duration-300 hover:shadow-[var(--shadow-elevation-4)] hover:bg-white/80 dark:hover:bg-[#1C1C24]/90',
    glow && glowColors[glow],
    className
  );

  const content = (
    <>
      {gradient && (
        <div
          className={cn(
            'absolute inset-0 opacity-5 pointer-events-none',
            `bg-gradient-to-br ${gradient}`
          )}
        />
      )}
      <div className="relative">{children}</div>
    </>
  );

  if (hover) {
    return (
      <motion.div
        className={baseClassName}
        whileHover={{ y: -4 }}
        transition={{ type: 'spring', stiffness: 300, damping: 25 }}
        onClick={onClick}
      >
        {content}
      </motion.div>
    );
  }

  return <div className={baseClassName} onClick={onClick}>{content}</div>;
}
