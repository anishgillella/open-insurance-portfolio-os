'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Card } from '@/components/primitives';
import { Input } from '@/components/primitives/Input';
import { Button } from '@/components/primitives/Button';
import { useAuth } from '@/lib/auth-context';
import { Mail, Lock } from 'lucide-react';

export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    // Simulate login - in real app, this would call an API
    await new Promise((resolve) => setTimeout(resolve, 1000));

    // For demo purposes, accept any credentials
    if (email && password) {
      // Log the user in (this will redirect to dashboard)
      login({
        email,
        firstName: 'Demo',
        lastName: 'User',
        companyName: 'Demo Company',
      });
    } else {
      setError('Please enter your email and password');
    }

    setIsLoading(false);
  };

  const handleGoogleLogin = () => {
    // Placeholder for Google OAuth
    alert('Google sign-in coming soon!');
  };

  return (
    <Card variant="elevated" padding="lg" className="w-full">
      <div className="text-center mb-8">
        <h1 className="text-2xl font-semibold text-[var(--color-text-primary)]">
          Login
        </h1>
        <p className="text-[var(--color-text-muted)] mt-2">
          Sign into your account with your email or SSO.
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
          error={error && !email ? 'Email is required' : undefined}
        />

        <div>
          <Input
            label="Password"
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            leftIcon={<Lock size={18} />}
            error={error && !password ? 'Password is required' : undefined}
          />
          <div className="text-right mt-1.5">
            <Link
              href="/auth/forgot-password"
              className="text-sm text-[var(--color-primary-500)] hover:text-[var(--color-primary-600)] transition-colors"
            >
              Forgot password?
            </Link>
          </div>
        </div>

        {error && email && password && (
          <p className="text-sm text-[var(--color-critical-500)] text-center">
            {error}
          </p>
        )}

        <Button
          type="submit"
          variant="primary"
          size="lg"
          className="w-full"
          loading={isLoading}
        >
          Log in
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
          onClick={handleGoogleLogin}
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
        Don&apos;t have an account?{' '}
        <Link
          href="/auth/register"
          className="text-[var(--color-primary-500)] hover:text-[var(--color-primary-600)] font-medium transition-colors"
        >
          Register now!
        </Link>
      </p>
    </Card>
  );
}
