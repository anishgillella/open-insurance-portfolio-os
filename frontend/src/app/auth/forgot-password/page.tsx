'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Card } from '@/components/primitives';
import { Input } from '@/components/primitives/Input';
import { Button } from '@/components/primitives/Button';
import { Mail, ArrowLeft } from 'lucide-react';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!email) {
      setError('Please enter your email address');
      return;
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError('Please enter a valid email address');
      return;
    }

    setIsLoading(true);

    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1000));

    setIsSubmitted(true);
    setIsLoading(false);
  };

  if (isSubmitted) {
    return (
      <Card variant="elevated" padding="lg" className="w-full text-center">
        <div className="w-16 h-16 rounded-full bg-[var(--color-success-100)] flex items-center justify-center mx-auto mb-6">
          <Mail size={32} className="text-[var(--color-success-500)]" />
        </div>

        <h1 className="text-2xl font-semibold text-[var(--color-text-primary)] mb-4">
          Check your email
        </h1>

        <p className="text-[var(--color-text-muted)] mb-6">
          We&apos;ve sent a password reset link to
          <br />
          <span className="font-medium text-[var(--color-text-primary)]">
            {email}
          </span>
        </p>

        <Link
          href="/auth/login"
          className="inline-flex items-center gap-2 text-[var(--color-primary-500)] hover:text-[var(--color-primary-600)] font-medium transition-colors"
        >
          <ArrowLeft size={16} />
          Back to log in
        </Link>
      </Card>
    );
  }

  return (
    <Card variant="elevated" padding="lg" className="w-full">
      <div className="text-center mb-8">
        <h1 className="text-2xl font-semibold text-[var(--color-text-primary)]">
          Reset your password
        </h1>
        <p className="text-[var(--color-text-muted)] mt-2">
          Enter your email, and we&apos;ll send you an email to reset it
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <Input
          label="Email"
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          leftIcon={<Mail size={18} />}
          error={error}
        />

        <Button
          type="submit"
          variant="primary"
          size="lg"
          className="w-full"
          loading={isLoading}
        >
          Continue
        </Button>
      </form>

      <div className="text-center mt-6">
        <Link
          href="/auth/login"
          className="inline-flex items-center gap-2 text-sm text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors"
        >
          <ArrowLeft size={14} />
          Back to log in
        </Link>
      </div>
    </Card>
  );
}
