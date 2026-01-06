'use client';

import { useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/primitives';
import { Input } from '@/components/primitives/Input';
import { Button } from '@/components/primitives/Button';
import { Lock, CheckCircle2 } from 'lucide-react';

// Password strength calculator (same as register page)
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

export default function ResetPasswordPage() {
  const router = useRouter();
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const passwordStrength = useMemo(() => getPasswordStrength(password), [password]);

  const validate = () => {
    const newErrors: Record<string, string> = {};

    if (!password) {
      newErrors.password = 'Password is required';
    } else if (password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    }

    if (!confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password';
    } else if (password !== confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
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

    setIsSuccess(true);
    setIsLoading(false);

    // Redirect to login after 2 seconds
    setTimeout(() => {
      router.push('/auth/login');
    }, 2000);
  };

  if (isSuccess) {
    return (
      <Card variant="elevated" padding="lg" className="w-full text-center">
        <div className="w-16 h-16 rounded-full bg-[var(--color-success-100)] flex items-center justify-center mx-auto mb-6">
          <CheckCircle2 size={32} className="text-[var(--color-success-500)]" />
        </div>

        <h1 className="text-2xl font-semibold text-[var(--color-text-primary)] mb-4">
          Password reset successful
        </h1>

        <p className="text-[var(--color-text-muted)]">
          Redirecting you to the login page...
        </p>
      </Card>
    );
  }

  return (
    <Card variant="elevated" padding="lg" className="w-full">
      <div className="text-center mb-8">
        <h1 className="text-2xl font-semibold text-[var(--color-text-primary)]">
          Set new password
        </h1>
        <p className="text-[var(--color-text-muted)] mt-2">
          Enter a new password below to complete the process
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <Input
            label="Password"
            type="password"
            placeholder="Password"
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

        <Input
          label="Confirm Password"
          type="password"
          placeholder="Confirm Password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          leftIcon={<Lock size={18} />}
          error={errors.confirmPassword}
        />

        <Button
          type="submit"
          variant="primary"
          size="lg"
          className="w-full"
          loading={isLoading}
        >
          Set new password
        </Button>
      </form>
    </Card>
  );
}
