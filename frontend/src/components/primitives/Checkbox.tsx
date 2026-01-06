'use client';

import { forwardRef } from 'react';
import { cn } from '@/lib/utils';
import { Check } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export interface CheckboxProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label?: string | React.ReactNode;
  description?: string;
  error?: string;
}

const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(
  ({ className, label, description, error, checked, onChange, disabled, ...props }, ref) => {
    return (
      <div className={cn('flex items-start gap-3', className)}>
        <div className="relative flex items-center justify-center">
          <input
            ref={ref}
            type="checkbox"
            checked={checked}
            onChange={onChange}
            disabled={disabled}
            className="peer sr-only"
            {...props}
          />
          <div
            className={cn(
              'h-5 w-5 rounded border-2 transition-all duration-200 flex items-center justify-center cursor-pointer',
              checked
                ? 'bg-[var(--color-primary-500)] border-[var(--color-primary-500)]'
                : 'bg-[var(--color-surface)] border-[var(--color-border-default)] hover:border-[var(--color-primary-400)]',
              disabled && 'opacity-50 cursor-not-allowed',
              error && 'border-[var(--color-critical-500)]'
            )}
            onClick={() => {
              if (!disabled && onChange) {
                const event = {
                  target: { checked: !checked },
                } as React.ChangeEvent<HTMLInputElement>;
                onChange(event);
              }
            }}
          >
            <AnimatePresence>
              {checked && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  exit={{ scale: 0 }}
                  transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                >
                  <Check size={14} className="text-white" strokeWidth={3} />
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
        {(label || description) && (
          <div className="flex flex-col">
            {label && (
              <span
                className={cn(
                  'text-sm text-[var(--color-text-primary)] cursor-pointer select-none',
                  disabled && 'opacity-50 cursor-not-allowed'
                )}
                onClick={() => {
                  if (!disabled && onChange) {
                    const event = {
                      target: { checked: !checked },
                    } as React.ChangeEvent<HTMLInputElement>;
                    onChange(event);
                  }
                }}
              >
                {label}
              </span>
            )}
            {description && (
              <span className="text-sm text-[var(--color-text-muted)]">
                {description}
              </span>
            )}
            {error && (
              <span className="text-sm text-[var(--color-critical-500)] mt-1">
                {error}
              </span>
            )}
          </div>
        )}
      </div>
    );
  }
);

Checkbox.displayName = 'Checkbox';

export { Checkbox };
