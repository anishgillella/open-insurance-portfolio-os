'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/primitives';
import { Input } from '@/components/primitives/Input';
import { Select } from '@/components/primitives/Select';
import { Button } from '@/components/primitives/Button';
import { useOnboarding } from '@/lib/onboarding-context';
import { CreditCard } from 'lucide-react';

const countryOptions = [
  { value: 'US', label: 'United States' },
  { value: 'CA', label: 'Canada' },
  { value: 'GB', label: 'United Kingdom' },
  { value: 'AU', label: 'Australia' },
];

const stateOptions = [
  { value: 'CA', label: 'California' },
  { value: 'NY', label: 'New York' },
  { value: 'TX', label: 'Texas' },
  { value: 'FL', label: 'Florida' },
  { value: 'IL', label: 'Illinois' },
  { value: 'WA', label: 'Washington' },
  { value: 'MA', label: 'Massachusetts' },
  { value: 'CO', label: 'Colorado' },
];

export default function PaymentPage() {
  const router = useRouter();
  const { state, updateData, completeStep } = useOnboarding();
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const [formData, setFormData] = useState({
    cardName: state.data.cardName || '',
    cardNumber: state.data.cardNumber || '',
    cardExpiry: state.data.cardExpiry || '',
    cardCvv: state.data.cardCvv || '',
    billingAddress: state.data.billingAddress || '',
    billingCity: state.data.billingCity || '',
    billingState: state.data.billingState || '',
    billingZip: state.data.billingZip || '',
    billingCountry: state.data.billingCountry || 'US',
  });

  const handleChange = (field: string, value: string) => {
    let formattedValue = value;

    // Format card number with spaces
    if (field === 'cardNumber') {
      formattedValue = value
        .replace(/\s/g, '')
        .replace(/(\d{4})/g, '$1 ')
        .trim()
        .slice(0, 19);
    }

    // Format expiry as MM/YY
    if (field === 'cardExpiry') {
      formattedValue = value
        .replace(/\D/g, '')
        .replace(/(\d{2})(\d)/, '$1/$2')
        .slice(0, 5);
    }

    // Limit CVV to 4 digits
    if (field === 'cardCvv') {
      formattedValue = value.replace(/\D/g, '').slice(0, 4);
    }

    setFormData((prev) => ({ ...prev, [field]: formattedValue }));

    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: '' }));
    }
  };

  const validate = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.cardName.trim()) {
      newErrors.cardName = 'Name on card is required';
    }

    const cardNumberClean = formData.cardNumber.replace(/\s/g, '');
    if (!cardNumberClean) {
      newErrors.cardNumber = 'Card number is required';
    } else if (cardNumberClean.length < 15) {
      newErrors.cardNumber = 'Please enter a valid card number';
    }

    if (!formData.cardExpiry) {
      newErrors.cardExpiry = 'Expiry date is required';
    } else if (!/^\d{2}\/\d{2}$/.test(formData.cardExpiry)) {
      newErrors.cardExpiry = 'Please enter MM/YY format';
    }

    if (!formData.cardCvv) {
      newErrors.cardCvv = 'CVV is required';
    } else if (formData.cardCvv.length < 3) {
      newErrors.cardCvv = 'Please enter a valid CVV';
    }

    if (!formData.billingAddress.trim()) {
      newErrors.billingAddress = 'Billing address is required';
    }

    if (!formData.billingCity.trim()) {
      newErrors.billingCity = 'City is required';
    }

    if (!formData.billingZip.trim()) {
      newErrors.billingZip = 'ZIP code is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) return;

    setIsLoading(true);

    // Simulate payment processing
    await new Promise((resolve) => setTimeout(resolve, 1500));

    // Save to context
    updateData(formData);
    completeStep('payment');

    // Navigate to complete page
    router.push('/onboarding/complete');

    setIsLoading(false);
  };

  const planPrice = state.data.plan === 'monthly' ? '$100/month' : '$800/year';

  return (
    <Card variant="elevated" padding="lg" className="w-full">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-[var(--color-text-primary)]">
          Add payment details
        </h1>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <Input
          label="Name on card"
          type="text"
          placeholder="Anna Taylor"
          value={formData.cardName}
          onChange={(e) => handleChange('cardName', e.target.value)}
          error={errors.cardName}
        />

        <div className="grid grid-cols-2 gap-4">
          <div className="col-span-2">
            <Input
              label="Card number"
              type="text"
              placeholder="1234 5678 8876 5432"
              value={formData.cardNumber}
              onChange={(e) => handleChange('cardNumber', e.target.value)}
              leftIcon={<CreditCard size={18} />}
              error={errors.cardNumber}
            />
          </div>
          <Input
            label="Exp Date"
            type="text"
            placeholder="05/27"
            value={formData.cardExpiry}
            onChange={(e) => handleChange('cardExpiry', e.target.value)}
            error={errors.cardExpiry}
          />
          <Input
            label="CVV"
            type="password"
            placeholder="•••"
            value={formData.cardCvv}
            onChange={(e) => handleChange('cardCvv', e.target.value)}
            error={errors.cardCvv}
          />
        </div>

        <Input
          label="Billing Address"
          type="text"
          placeholder="Skynd Avenue 66"
          value={formData.billingAddress}
          onChange={(e) => handleChange('billingAddress', e.target.value)}
          error={errors.billingAddress}
        />

        <Input
          label="City"
          type="text"
          placeholder="Los Angeles"
          value={formData.billingCity}
          onChange={(e) => handleChange('billingCity', e.target.value)}
          error={errors.billingCity}
        />

        <div className="grid grid-cols-2 gap-4">
          <Select
            label="State/Province"
            options={stateOptions}
            value={formData.billingState}
            onChange={(value) => handleChange('billingState', value)}
            placeholder="Select state"
          />
          <Input
            label="ZIP"
            type="text"
            placeholder="12345"
            value={formData.billingZip}
            onChange={(e) => handleChange('billingZip', e.target.value)}
            error={errors.billingZip}
          />
        </div>

        <Select
          label="Country"
          options={countryOptions}
          value={formData.billingCountry}
          onChange={(value) => handleChange('billingCountry', value)}
        />

        <Button
          type="submit"
          variant="primary"
          size="lg"
          className="w-full mt-6"
          loading={isLoading}
        >
          Pay {planPrice}
        </Button>
      </form>
    </Card>
  );
}
