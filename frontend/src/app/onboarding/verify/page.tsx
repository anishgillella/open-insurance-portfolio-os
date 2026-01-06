'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/primitives';
import { OTPInput } from '@/components/primitives/OTPInput';
import { Button } from '@/components/primitives/Button';
import { Mail, X } from 'lucide-react';
import { motion } from 'framer-motion';

// Get email outside component to avoid setState in effect
function getStoredEmail(): string {
  if (typeof window === 'undefined') return '';
  return sessionStorage.getItem('pendingVerificationEmail') || '';
}

export default function VerifyEmailPage() {
  const router = useRouter();
  const [otp, setOtp] = useState('');
  const [email] = useState(getStoredEmail);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    // Redirect if no email (after hydration)
    if (!email) {
      router.push('/auth/register');
    }
  }, [email, router]);

  const handleVerify = async () => {
    if (otp.length !== 6) {
      setError('Please enter the 6-digit code');
      return;
    }

    setIsLoading(true);
    setError('');

    // Simulate API verification
    await new Promise((resolve) => setTimeout(resolve, 1000));

    // For demo, accept any 6-digit code
    // Clear the pending email
    sessionStorage.removeItem('pendingVerificationEmail');

    // Navigate to profile setup
    router.push('/onboarding/profile');

    setIsLoading(false);
  };

  const handleResend = () => {
    // Simulate resending code
    alert('A new verification code has been sent to your email.');
  };

  const handleClose = () => {
    router.push('/auth/register');
  };

  if (!email) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.2 }}
      >
        <Card variant="elevated" padding="lg" className="w-full max-w-md relative">
          <button
            onClick={handleClose}
            className="absolute top-4 right-4 p-1 rounded-full hover:bg-[var(--color-surface-sunken)] text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors"
          >
            <X size={20} />
          </button>

          <div className="text-center mb-8">
            <div className="w-16 h-16 rounded-full bg-[var(--color-surface-sunken)] flex items-center justify-center mx-auto mb-4">
              <Mail size={28} className="text-[var(--color-text-muted)]" />
            </div>
            <p className="text-[var(--color-text-secondary)]">
              Please enter the code we sent to
            </p>
            <p className="font-medium text-[var(--color-text-primary)]">{email}</p>
          </div>

          <div className="space-y-6">
            <OTPInput
              length={6}
              value={otp}
              onChange={setOtp}
              error={error}
            />

            <Button
              type="button"
              variant="primary"
              size="lg"
              className="w-full"
              loading={isLoading}
              onClick={handleVerify}
            >
              Verify
            </Button>

            <p className="text-center text-sm text-[var(--color-text-muted)]">
              Didn&apos;t receive the code?{' '}
              <button
                type="button"
                onClick={handleResend}
                className="text-[var(--color-primary-500)] hover:text-[var(--color-primary-600)] font-medium transition-colors"
              >
                Resend
              </button>
            </p>
          </div>

          <p className="text-center mt-6 text-xs text-[var(--color-text-muted)]">
            Secured by Open Insurance
          </p>
        </Card>
      </motion.div>
    </div>
  );
}
