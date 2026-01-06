'use client';

import { useState, useMemo } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/primitives';
import { Input } from '@/components/primitives/Input';
import { Checkbox } from '@/components/primitives/Checkbox';
import { Button } from '@/components/primitives/Button';
import { Mail, Lock } from 'lucide-react';

// Password strength calculator
function getPasswordStrength(password: string): {
  score: number;
  label: string;
  color: string;
} {
  let score = 0;

  if (password.length >= 8) score++;
  if (password.length >= 12) score++;
  if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score++;
  if (/\d/.test(password)) score++;
  if (/[^a-zA-Z0-9]/.test(password)) score++;

  if (score <= 1) return { score, label: 'Weak', color: 'var(--color-critical-500)' };
  if (score <= 2) return { score, label: 'Fair', color: 'var(--color-warning-500)' };
  if (score <= 3) return { score, label: 'Good', color: 'var(--color-success-400)' };
  return { score, label: 'Strong', color: 'var(--color-success-500)' };
}

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [agreedToTerms, setAgreedToTerms] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const passwordStrength = useMemo(() => getPasswordStrength(password), [password]);

  const validate = () => {
    const newErrors: Record<string, string> = {};

    if (!email) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      newErrors.email = 'Please enter a valid email';
    }

    if (!password) {
      newErrors.password = 'Password is required';
    } else if (password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    }

    if (!agreedToTerms) {
      newErrors.terms = 'You must agree to the Terms of Service';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) return;

    setIsLoading(true);

    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1000));

    // Store email in sessionStorage for verification page
    sessionStorage.setItem('pendingVerificationEmail', email);

    // Navigate to verification page
    router.push('/onboarding/verify');

    setIsLoading(false);
  };

  const handleGoogleSignup = () => {
    alert('Google sign-up coming soon!');
  };

  return (
    <Card variant="elevated" padding="lg" className="w-full">
      <div className="text-center mb-8">
        <h1 className="text-2xl font-semibold text-[var(--color-text-primary)]">
          Create your account
        </h1>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <Input
          label="Email"
          type="email"
          placeholder="email@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          leftIcon={<Mail size={18} />}
          error={errors.email}
        />

        <div>
          <Input
            label="Password"
            type="password"
            placeholder="Create a password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            leftIcon={<Lock size={18} />}
            error={errors.password}
          />
          {password && (
            <div className="mt-2">
              <div className="flex items-center gap-2">
                <div className="flex-1 h-1.5 bg-[var(--color-surface-sunken)] rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-300"
                    style={{
                      width: `${(passwordStrength.score / 5) * 100}%`,
                      backgroundColor: passwordStrength.color,
                    }}
                  />
                </div>
                <span
                  className="text-xs font-medium"
                  style={{ color: passwordStrength.color }}
                >
                  {passwordStrength.label}
                </span>
              </div>
            </div>
          )}
        </div>

        <Checkbox
          checked={agreedToTerms}
          onChange={(e) => setAgreedToTerms(e.target.checked)}
          label={
            <span className="text-sm">
              I agree to the{' '}
              <Link
                href="/terms"
                className="text-[var(--color-primary-500)] hover:underline"
              >
                Terms of Service
              </Link>{' '}
              and{' '}
              <Link
                href="/privacy"
                className="text-[var(--color-primary-500)] hover:underline"
              >
                Privacy Statement
              </Link>
            </span>
          }
          error={errors.terms}
        />

        <Button
          type="submit"
          variant="primary"
          size="lg"
          className="w-full"
          loading={isLoading}
        >
          Get Started
        </Button>

        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-[var(--color-border-default)]" />
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-4 bg-[var(--color-surface)] text-[var(--color-text-muted)]">
              -or-
            </span>
          </div>
        </div>

        <Button
          type="button"
          variant="secondary"
          size="lg"
          className="w-full"
          onClick={handleGoogleSignup}
          leftIcon={
            <svg viewBox="0 0 24 24" className="w-5 h-5">
              <path
                fill="#4285F4"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="#34A853"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="#FBBC05"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
              />
              <path
                fill="#EA4335"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
              />
            </svg>
          }
        >
          Continue with Google
        </Button>
      </form>

      <p className="text-center mt-6 text-sm text-[var(--color-text-muted)]">
        Already have an account?{' '}
        <Link
          href="/auth/login"
          className="text-[var(--color-primary-500)] hover:text-[var(--color-primary-600)] font-medium transition-colors"
        >
          Log in
        </Link>
      </p>
    </Card>
  );
}
