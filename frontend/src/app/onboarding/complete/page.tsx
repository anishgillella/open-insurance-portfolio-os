'use client';

import { Card } from '@/components/primitives';
import { Button } from '@/components/primitives/Button';
import { useOnboarding } from '@/lib/onboarding-context';
import { useAuth } from '@/lib/auth-context';
import { motion } from 'framer-motion';
import { CheckCircle2, Sparkles } from 'lucide-react';

export default function CompletePage() {
  const { state, reset } = useOnboarding();
  const { login } = useAuth();

  const handleGetStarted = () => {
    // Log the user in with their onboarding data
    login({
      email: state.data.email,
      firstName: state.data.firstName,
      lastName: state.data.lastName,
      companyName: state.data.companyName,
    });
    // Clear onboarding state
    reset();
    // The login function will redirect to dashboard
  };

  return (
    <Card variant="elevated" padding="lg" className="w-full text-center">
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{
          type: 'spring',
          stiffness: 260,
          damping: 20,
          delay: 0.1,
        }}
        className="w-20 h-20 rounded-full bg-[var(--color-success-100)] flex items-center justify-center mx-auto mb-6"
      >
        <CheckCircle2
          size={48}
          className="text-[var(--color-success-500)]"
        />
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <h1 className="text-3xl font-semibold text-[var(--color-text-primary)] mb-4">
          Thanks!
        </h1>

        <p className="text-[var(--color-text-secondary)] mb-2">
          We appreciate you for being an early supporter!
        </p>
        <p className="text-[var(--color-text-muted)] mb-8">
          Please let us know if you have any questions or feedback.
          <br />
          We always love to get in touch.
        </p>

        <Button
          variant="primary"
          size="lg"
          className="w-full"
          onClick={handleGetStarted}
          leftIcon={<Sparkles size={18} />}
        >
          Get Started
        </Button>
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="mt-8 pt-6 border-t border-[var(--color-border-subtle)]"
      >
        <p className="text-sm text-[var(--color-text-muted)]">
          Need help?{' '}
          <a
            href="mailto:support@openinsurance.com"
            className="text-[var(--color-primary-500)] hover:text-[var(--color-primary-600)] transition-colors"
          >
            Contact support
          </a>
        </p>
      </motion.div>
    </Card>
  );
}
