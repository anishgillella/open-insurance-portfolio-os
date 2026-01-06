'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/primitives';
import { Input } from '@/components/primitives/Input';
import { Button } from '@/components/primitives/Button';
import { useOnboarding } from '@/lib/onboarding-context';

export default function ProfileSetupPage() {
  const router = useRouter();
  const { state, updateData, completeStep } = useOnboarding();
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const [formData, setFormData] = useState({
    firstName: state.data.firstName || '',
    lastName: state.data.lastName || '',
    companyName: state.data.companyName || '',
    companyWebsite: state.data.companyWebsite || '',
    phoneNumber: state.data.phoneNumber || '',
  });

  const handleChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    // Clear error when user types
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: '' }));
    }
  };

  const validate = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.firstName.trim()) {
      newErrors.firstName = 'First name is required';
    }
    if (!formData.lastName.trim()) {
      newErrors.lastName = 'Last name is required';
    }
    if (!formData.companyName.trim()) {
      newErrors.companyName = 'Company name is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) return;

    setIsLoading(true);

    // Save to context
    updateData(formData);
    completeStep('profile');

    // Navigate to role selection
    router.push('/onboarding/role');

    setIsLoading(false);
  };

  return (
    <Card variant="elevated" padding="lg" className="w-full">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-[var(--color-text-primary)]">
          Create your account
        </h1>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <Input
          label="First Name"
          type="text"
          placeholder="John"
          value={formData.firstName}
          onChange={(e) => handleChange('firstName', e.target.value)}
          error={errors.firstName}
        />

        <Input
          label="Last Name"
          type="text"
          placeholder="Doe"
          value={formData.lastName}
          onChange={(e) => handleChange('lastName', e.target.value)}
          error={errors.lastName}
        />

        <Input
          label="Company Name"
          type="text"
          placeholder="Acme Inc"
          value={formData.companyName}
          onChange={(e) => handleChange('companyName', e.target.value)}
          error={errors.companyName}
        />

        <Input
          label="Company Website"
          type="url"
          placeholder="www.acme.com"
          value={formData.companyWebsite}
          onChange={(e) => handleChange('companyWebsite', e.target.value)}
          hint="Optional"
        />

        <Input
          label="Phone Number"
          type="tel"
          placeholder="888-888-8888"
          value={formData.phoneNumber}
          onChange={(e) => handleChange('phoneNumber', e.target.value)}
          hint="Optional"
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
