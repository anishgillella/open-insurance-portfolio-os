'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/primitives';
import { Button } from '@/components/primitives/Button';
import { Input } from '@/components/primitives/Input';
import { useOnboarding, SubscriptionPlan } from '@/lib/onboarding-context';
import { Check } from 'lucide-react';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';

const plans = [
  {
    id: 'monthly',
    name: 'Monthly',
    price: '$100',
    period: '/month',
    description: 'Up to 10 users, $0.04 per unit',
    features: ['Up to 10 users', 'Unlimited policies', 'Email support'],
  },
  {
    id: 'annual',
    name: 'Annual',
    price: '$800',
    period: '/year',
    description: 'Up to 50 users, $0.04 per unit',
    features: [
      'Up to 50 users',
      'Unlimited policies',
      'Priority support',
      'Save $400/year',
    ],
    popular: true,
  },
];

export default function PlanSelectionPage() {
  const router = useRouter();
  const { state, updateData, completeStep } = useOnboarding();
  const [selectedPlan, setSelectedPlan] = useState<SubscriptionPlan>(
    state.data.plan || 'monthly'
  );
  const [showDiscountInput, setShowDiscountInput] = useState(false);
  const [discountCode, setDiscountCode] = useState(state.data.discountCode || '');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    // Save to context
    updateData({
      plan: selectedPlan,
      discountCode,
    });
    completeStep('plan');

    // Navigate to payment
    router.push('/onboarding/payment');

    setIsLoading(false);
  };

  return (
    <Card variant="elevated" padding="lg" className="w-full">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-[var(--color-text-primary)]">
          Select a plan
        </h1>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="space-y-4">
          {plans.map((plan) => {
            const isSelected = selectedPlan === plan.id;
            return (
              <motion.div
                key={plan.id}
                className={cn(
                  'relative p-5 rounded-xl border-2 cursor-pointer transition-all',
                  isSelected
                    ? 'border-[var(--color-primary-500)] bg-[var(--color-primary-50)]'
                    : 'border-[var(--color-border-default)] hover:border-[var(--color-primary-300)]'
                )}
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
                onClick={() => setSelectedPlan(plan.id as SubscriptionPlan)}
              >
                {plan.popular && (
                  <span className="absolute -top-3 right-4 px-3 py-1 text-xs font-medium bg-[var(--color-primary-500)] text-white rounded-full">
                    Popular
                  </span>
                )}

                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-baseline gap-2">
                      <span className="text-lg font-semibold text-[var(--color-text-primary)]">
                        {plan.name}
                      </span>
                      <span className="text-2xl font-bold text-[var(--color-text-primary)]">
                        {plan.price}
                      </span>
                      <span className="text-sm text-[var(--color-text-muted)]">
                        {plan.period}
                      </span>
                    </div>
                    <p className="text-sm text-[var(--color-text-muted)] mt-1">
                      {plan.description}
                    </p>
                  </div>

                  <div
                    className={cn(
                      'w-6 h-6 rounded-full border-2 flex items-center justify-center flex-shrink-0',
                      isSelected
                        ? 'border-[var(--color-primary-500)] bg-[var(--color-primary-500)]'
                        : 'border-[var(--color-border-default)]'
                    )}
                  >
                    {isSelected && <Check size={14} className="text-white" />}
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* Discount Code Section */}
        {showDiscountInput ? (
          <div className="pt-2">
            <Input
              label="Discount Code"
              placeholder="Enter your code"
              value={discountCode}
              onChange={(e) => setDiscountCode(e.target.value)}
            />
          </div>
        ) : (
          <button
            type="button"
            onClick={() => setShowDiscountInput(true)}
            className="w-full text-center text-sm text-[var(--color-primary-500)] hover:text-[var(--color-primary-600)] transition-colors py-2"
          >
            Enter Discount Code
          </button>
        )}

        <Button
          type="submit"
          variant="primary"
          size="lg"
          className="w-full"
          loading={isLoading}
        >
          Next
        </Button>
      </form>
    </Card>
  );
}
