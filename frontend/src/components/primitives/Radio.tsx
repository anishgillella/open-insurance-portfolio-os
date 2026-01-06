'use client';

import { forwardRef } from 'react';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';

export interface RadioOption {
  value: string;
  label: string;
  description?: string;
  icon?: React.ReactNode;
}

export interface RadioGroupProps {
  options: RadioOption[];
  value: string;
  onChange: (value: string) => void;
  name: string;
  label?: string;
  error?: string;
  disabled?: boolean;
  className?: string;
  orientation?: 'vertical' | 'horizontal';
  variant?: 'default' | 'card';
}

const RadioGroup = forwardRef<HTMLDivElement, RadioGroupProps>(
  (
    {
      options,
      value,
      onChange,
      name,
      label,
      error,
      disabled,
      className,
      orientation = 'vertical',
      variant = 'default',
    },
    ref
  ) => {
    if (variant === 'card') {
      return (
        <div ref={ref} className={cn('w-full', className)}>
          {label && (
            <label className="block text-sm font-medium text-[var(--color-text-primary)] mb-3">
              {label}
            </label>
          )}
          <div
            className={cn(
              'gap-3',
              orientation === 'vertical' ? 'flex flex-col' : 'grid grid-cols-2'
            )}
          >
            {options.map((option) => {
              const isSelected = value === option.value;
              return (
                <motion.div
                  key={option.value}
                  className={cn(
                    'relative flex items-center gap-4 p-4 rounded-xl border-2 cursor-pointer transition-all duration-200',
                    isSelected
                      ? 'border-[var(--color-primary-500)] bg-[var(--color-primary-50)]'
                      : 'border-[var(--color-border-default)] bg-[var(--color-surface)] hover:border-[var(--color-primary-300)]',
                    disabled && 'opacity-50 cursor-not-allowed'
                  )}
                  whileHover={!disabled ? { scale: 1.01 } : undefined}
                  whileTap={!disabled ? { scale: 0.99 } : undefined}
                  onClick={() => !disabled && onChange(option.value)}
                >
                  {option.icon && (
                    <div
                      className={cn(
                        'flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center',
                        isSelected
                          ? 'bg-[var(--color-primary-500)] text-white'
                          : 'bg-[var(--color-surface-sunken)] text-[var(--color-text-secondary)]'
                      )}
                    >
                      {option.icon}
                    </div>
                  )}
                  <div className="flex-1 min-w-0">
                    <span
                      className={cn(
                        'block font-medium',
                        isSelected
                          ? 'text-[var(--color-primary-700)]'
                          : 'text-[var(--color-text-primary)]'
                      )}
                    >
                      {option.label}
                    </span>
                    {option.description && (
                      <span className="block text-sm text-[var(--color-text-muted)] mt-0.5">
                        {option.description}
                      </span>
                    )}
                  </div>
                  <div
                    className={cn(
                      'w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0',
                      isSelected
                        ? 'border-[var(--color-primary-500)]'
                        : 'border-[var(--color-border-default)]'
                    )}
                  >
                    <AnimatePresence>
                      {isSelected && (
                        <motion.div
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          exit={{ scale: 0 }}
                          transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                          className="w-2.5 h-2.5 rounded-full bg-[var(--color-primary-500)]"
                        />
                      )}
                    </AnimatePresence>
                  </div>
                  <input
                    type="radio"
                    name={name}
                    value={option.value}
                    checked={isSelected}
                    onChange={() => onChange(option.value)}
                    disabled={disabled}
                    className="sr-only"
                  />
                </motion.div>
              );
            })}
          </div>
          {error && (
            <p className="mt-2 text-sm text-[var(--color-critical-500)]">{error}</p>
          )}
        </div>
      );
    }

    return (
      <div ref={ref} className={cn('w-full', className)}>
        {label && (
          <label className="block text-sm font-medium text-[var(--color-text-primary)] mb-2">
            {label}
          </label>
        )}
        <div
          className={cn(
            'gap-3',
            orientation === 'vertical' ? 'flex flex-col' : 'flex flex-row flex-wrap'
          )}
        >
          {options.map((option) => {
            const isSelected = value === option.value;
            return (
              <label
                key={option.value}
                className={cn(
                  'flex items-center gap-3 cursor-pointer',
                  disabled && 'opacity-50 cursor-not-allowed'
                )}
              >
                <div
                  className={cn(
                    'w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all duration-200',
                    isSelected
                      ? 'border-[var(--color-primary-500)]'
                      : 'border-[var(--color-border-default)] hover:border-[var(--color-primary-400)]'
                  )}
                >
                  <AnimatePresence>
                    {isSelected && (
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        exit={{ scale: 0 }}
                        transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                        className="w-2.5 h-2.5 rounded-full bg-[var(--color-primary-500)]"
                      />
                    )}
                  </AnimatePresence>
                </div>
                <input
                  type="radio"
                  name={name}
                  value={option.value}
                  checked={isSelected}
                  onChange={() => onChange(option.value)}
                  disabled={disabled}
                  className="sr-only"
                />
                <span className="text-sm text-[var(--color-text-primary)]">
                  {option.label}
                </span>
              </label>
            );
          })}
        </div>
        {error && (
          <p className="mt-2 text-sm text-[var(--color-critical-500)]">{error}</p>
        )}
      </div>
    );
  }
);

RadioGroup.displayName = 'RadioGroup';

export { RadioGroup };
