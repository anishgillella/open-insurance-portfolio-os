'use client';

import { forwardRef, useRef, useMemo } from 'react';
import { cn } from '@/lib/utils';

export interface OTPInputProps {
  length?: number;
  value: string;
  onChange: (value: string) => void;
  error?: string;
  disabled?: boolean;
  className?: string;
}

const OTPInput = forwardRef<HTMLDivElement, OTPInputProps>(
  ({ length = 6, value, onChange, error, disabled, className }, ref) => {
    // Derive otp array from value prop
    const otp = useMemo(() => {
      return value
        ? value.split('').slice(0, length).concat(Array(Math.max(0, length - value.length)).fill(''))
        : Array(length).fill('');
    }, [value, length]);

    const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

    const handleChange = (index: number, digit: string) => {
      if (!/^\d*$/.test(digit)) return;

      const newOtp = [...otp];
      newOtp[index] = digit.slice(-1);
      onChange(newOtp.join(''));

      // Auto-focus next input
      if (digit && index < length - 1) {
        inputRefs.current[index + 1]?.focus();
      }
    };

    const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Backspace' && !otp[index] && index > 0) {
        inputRefs.current[index - 1]?.focus();
      }
      if (e.key === 'ArrowLeft' && index > 0) {
        inputRefs.current[index - 1]?.focus();
      }
      if (e.key === 'ArrowRight' && index < length - 1) {
        inputRefs.current[index + 1]?.focus();
      }
    };

    const handlePaste = (e: React.ClipboardEvent) => {
      e.preventDefault();
      const pastedData = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, length);
      onChange(pastedData);

      // Focus the next empty input or the last one
      const nextEmptyIndex = pastedData.length < length ? pastedData.length : length - 1;
      inputRefs.current[nextEmptyIndex]?.focus();
    };

    return (
      <div ref={ref} className={cn('w-full', className)}>
        <div className="flex justify-center gap-3">
          {Array.from({ length }).map((_, index) => (
            <input
              key={index}
              ref={(el) => {
                inputRefs.current[index] = el;
              }}
              type="text"
              inputMode="numeric"
              maxLength={1}
              value={otp[index] || ''}
              onChange={(e) => handleChange(index, e.target.value)}
              onKeyDown={(e) => handleKeyDown(index, e)}
              onPaste={handlePaste}
              disabled={disabled}
              className={cn(
                'w-12 h-14 text-center text-xl font-semibold rounded-lg border bg-[var(--color-surface)] text-[var(--color-text-primary)] transition-all duration-200',
                'focus:outline-none focus:ring-2 focus:ring-[var(--color-primary-500)] focus:border-transparent',
                otp[index]
                  ? 'border-[var(--color-primary-500)]'
                  : 'border-[var(--color-border-default)] hover:border-[var(--color-border-strong)]',
                error && 'border-[var(--color-critical-500)] focus:ring-[var(--color-critical-500)]',
                disabled && 'opacity-50 cursor-not-allowed'
              )}
            />
          ))}
        </div>
        {error && (
          <p className="mt-3 text-sm text-center text-[var(--color-critical-500)]">
            {error}
          </p>
        )}
      </div>
    );
  }
);

OTPInput.displayName = 'OTPInput';

export { OTPInput };
