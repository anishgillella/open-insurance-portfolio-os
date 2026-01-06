'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/primitives';
import { Input } from '@/components/primitives/Input';
import { Checkbox } from '@/components/primitives/Checkbox';
import { Button } from '@/components/primitives/Button';
import {
  useOnboarding,
  getRoleLabels,
  roleNeedsQuantities,
  getMetricType,
  PropertyType,
  GeographicRegion,
} from '@/lib/onboarding-context';

const propertyTypeOptions: { value: PropertyType; label: string }[] = [
  { value: 'multifamily', label: 'Multifamily' },
  { value: 'office', label: 'Office' },
  { value: 'retail', label: 'Retail' },
  { value: 'industrial', label: 'Industrial' },
  { value: 'self-storage', label: 'Self-Storage' },
  { value: 'other', label: 'Other' },
];

const regionOptions: { value: GeographicRegion; label: string }[] = [
  { value: 'northeast', label: 'Northeast' },
  { value: 'midwest', label: 'Midwest' },
  { value: 'south', label: 'South' },
  { value: 'west', label: 'West' },
  { value: 'national', label: 'National' },
];

export default function PortfolioDetailsPage() {
  const router = useRouter();
  const { state, updateData, completeStep } = useOnboarding();
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const [formData, setFormData] = useState({
    propertyCount: state.data.propertyCount || '',
    propertyTypes: state.data.propertyTypes || [],
    approximateUnits: state.data.approximateUnits || '',
    approximateSqFt: state.data.approximateSqFt || '',
    geographicFocus: state.data.geographicFocus || [],
  });

  const role = state.data.role;
  const labels = getRoleLabels(role);
  const needsQuantities = roleNeedsQuantities(role);
  const metricType = getMetricType(formData.propertyTypes);

  // Redirect if no role selected
  useEffect(() => {
    if (!role) {
      router.push('/onboarding/role');
    }
  }, [role, router]);

  const handlePropertyTypeChange = (type: PropertyType, checked: boolean) => {
    setFormData((prev) => ({
      ...prev,
      propertyTypes: checked
        ? [...prev.propertyTypes, type]
        : prev.propertyTypes.filter((t) => t !== type),
    }));
  };

  const handleRegionChange = (region: GeographicRegion, checked: boolean) => {
    setFormData((prev) => ({
      ...prev,
      geographicFocus: checked
        ? [...prev.geographicFocus, region]
        : prev.geographicFocus.filter((r) => r !== region),
    }));
  };

  const validate = () => {
    const newErrors: Record<string, string> = {};

    if (formData.propertyTypes.length === 0) {
      newErrors.propertyTypes = 'Please select at least one property type';
    }

    if (needsQuantities && !formData.propertyCount) {
      newErrors.propertyCount = 'Please enter the number of properties';
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
    completeStep('portfolio');

    // Navigate to upload page
    router.push('/onboarding/upload');

    setIsLoading(false);
  };

  if (!role) return null;

  return (
    <Card variant="elevated" padding="lg" className="w-full">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-[var(--color-text-primary)]">
          Tell us about your portfolio
        </h1>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Property Count - only for roles that need quantities */}
        {needsQuantities && (
          <Input
            label={labels.countLabel}
            type="number"
            placeholder="Enter here"
            value={formData.propertyCount}
            onChange={(e) =>
              setFormData((prev) => ({ ...prev, propertyCount: e.target.value }))
            }
            error={errors.propertyCount}
          />
        )}

        {/* Property Types */}
        <div>
          <label className="block text-sm font-medium text-[var(--color-text-primary)] mb-3">
            {labels.typesLabel}
          </label>
          <div className="space-y-3">
            {propertyTypeOptions.map((option) => (
              <Checkbox
                key={option.value}
                checked={formData.propertyTypes.includes(option.value)}
                onChange={(e) =>
                  handlePropertyTypeChange(option.value, e.target.checked)
                }
                label={option.label}
              />
            ))}
          </div>
          {errors.propertyTypes && (
            <p className="mt-2 text-sm text-[var(--color-critical-500)]">
              {errors.propertyTypes}
            </p>
          )}
        </div>

        {/* Approximate Units or Square Footage - dynamic based on property types */}
        {needsQuantities && formData.propertyTypes.length > 0 && (
          <>
            {(metricType === 'units' || metricType === 'both') && (
              <Input
                label={labels.unitsLabel}
                type="number"
                placeholder="Enter here"
                value={formData.approximateUnits}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    approximateUnits: e.target.value,
                  }))
                }
              />
            )}
            {(metricType === 'sqft' || metricType === 'both') && (
              <Input
                label={labels.sqftLabel}
                type="number"
                placeholder="Enter here"
                value={formData.approximateSqFt}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    approximateSqFt: e.target.value,
                  }))
                }
              />
            )}
          </>
        )}

        {/* Geographic Focus - only for roles that need quantities */}
        {needsQuantities && (
          <div>
            <label className="block text-sm font-medium text-[var(--color-text-primary)] mb-3">
              Geographic Focus
            </label>
            <div className="space-y-3">
              {regionOptions.map((option) => (
                <Checkbox
                  key={option.value}
                  checked={formData.geographicFocus.includes(option.value)}
                  onChange={(e) =>
                    handleRegionChange(option.value, e.target.checked)
                  }
                  label={option.label}
                />
              ))}
            </div>
          </div>
        )}

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
