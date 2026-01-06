'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { OnboardingProvider } from '@/lib/onboarding-context';
import { Logo } from '@/components/shared/Logo';
import { Check } from 'lucide-react';
import { cn } from '@/lib/utils';

const steps = [
  { id: 'profile', label: 'Create Account', path: '/onboarding/profile' },
  { id: 'role', label: 'Setup Info', path: '/onboarding/role' },
  { id: 'upload', label: 'Upload Policies', path: '/onboarding/upload' },
];

function ProgressStepper() {
  const pathname = usePathname();

  // Determine current step index based on pathname
  const getCurrentStepIndex = () => {
    if (pathname.includes('verify') || pathname.includes('profile')) return 0;
    if (pathname.includes('role') || pathname.includes('portfolio')) return 1;
    if (pathname.includes('upload') || pathname.includes('plan') || pathname.includes('payment') || pathname.includes('complete')) return 2;
    return 0;
  };

  const currentStepIndex = getCurrentStepIndex();

  return (
    <div className="flex items-center justify-center gap-2">
      {steps.map((step, index) => {
        const isCompleted = index < currentStepIndex;
        const isCurrent = index === currentStepIndex;

        return (
          <div key={step.id} className="flex items-center">
            <div className="flex items-center gap-2">
              <div
                className={cn(
                  'w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium transition-all',
                  isCompleted
                    ? 'bg-[var(--color-success-500)] text-white'
                    : isCurrent
                    ? 'bg-[var(--color-primary-500)] text-white'
                    : 'bg-[var(--color-surface-sunken)] text-[var(--color-text-muted)]'
                )}
              >
                {isCompleted ? <Check size={14} /> : index + 1}
              </div>
              <span
                className={cn(
                  'text-sm hidden sm:inline',
                  isCurrent
                    ? 'text-[var(--color-text-primary)] font-medium'
                    : 'text-[var(--color-text-muted)]'
                )}
              >
                {step.label}
              </span>
            </div>
            {index < steps.length - 1 && (
              <div
                className={cn(
                  'w-8 sm:w-12 h-0.5 mx-2',
                  index < currentStepIndex
                    ? 'bg-[var(--color-success-500)]'
                    : 'bg-[var(--color-border-default)]'
                )}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

export default function OnboardingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const showStepper = !pathname.includes('verify');

  return (
    <OnboardingProvider>
      <div className="min-h-screen bg-[var(--color-background)] flex flex-col">
        {/* Header with Logo and Progress */}
        <header className="w-full py-6 px-8">
          <div className="max-w-4xl mx-auto flex items-center justify-between">
            <Link href="/">
              <Logo size="md" />
            </Link>

            {showStepper && <ProgressStepper />}

            <Link
              href="/auth/login"
              className="text-sm text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors"
            >
              Back
            </Link>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1 flex items-center justify-center px-4 py-8">
          <motion.div
            key={pathname}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
            className="w-full max-w-lg"
          >
            {children}
          </motion.div>
        </main>

        {/* Footer */}
        <footer className="w-full py-6 text-center">
          <p className="text-sm text-[var(--color-text-muted)]">
            © {new Date().getFullYear()} Open Insurance.
          </p>
        </footer>
      </div>
    </OnboardingProvider>
  );
}
