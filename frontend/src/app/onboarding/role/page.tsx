'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/primitives';
import { RadioGroup } from '@/components/primitives/Radio';
import { Button } from '@/components/primitives/Button';
import { useOnboarding, UserRole } from '@/lib/onboarding-context';
import { Building2, Users, Landmark, Briefcase, UserCog } from 'lucide-react';

const roleOptions = [
  {
    value: 'owner',
    label: 'Owner / Operator',
    description: 'I own and operate properties',
    icon: <Building2 size={20} />,
  },
  {
    value: 'property-manager',
    label: 'Property Manager',
    description: 'I manage properties for owners',
    icon: <Users size={20} />,
  },
  {
    value: 'lender',
    label: 'Lender',
    description: 'I finance real estate investments',
    icon: <Landmark size={20} />,
  },
  {
    value: 'broker',
    label: 'Broker',
    description: 'I broker insurance or real estate',
    icon: <Briefcase size={20} />,
  },
  {
    value: 'consultant',
    label: 'Consultant',
    description: 'I advise on property/insurance matters',
    icon: <UserCog size={20} />,
  },
];

export default function RoleSelectionPage() {
  const router = useRouter();
  const { state, updateData, completeStep } = useOnboarding();
  const [selectedRole, setSelectedRole] = useState<string>(state.data.role || '');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedRole) {
      setError('Please select a role');
      return;
    }

    setIsLoading(true);

    // Save to context
    updateData({ role: selectedRole as UserRole });
    completeStep('role');

    // Navigate to portfolio details
    router.push('/onboarding/portfolio');

    setIsLoading(false);
  };

  return (
    <Card variant="elevated" padding="lg" className="w-full">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-[var(--color-text-primary)]">
          Select your role
        </h1>
      </div>

      <form onSubmit={handleSubmit}>
        <RadioGroup
          name="role"
          options={roleOptions}
          value={selectedRole}
          onChange={(value) => {
            setSelectedRole(value);
            setError('');
          }}
          variant="card"
          error={error}
        />

        <Button
          type="submit"
          variant="primary"
          size="lg"
          className="w-full mt-6"
          loading={isLoading}
        >
          Next
        </Button>
      </form>
    </Card>
  );
}
