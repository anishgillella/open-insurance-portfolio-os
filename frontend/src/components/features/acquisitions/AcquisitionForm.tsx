'use client';

import { useState, useCallback } from 'react';
import { Search, Link as LinkIcon, Zap } from 'lucide-react';
import { Button } from '@/components/primitives';
import type { AcquisitionRequest } from '@/lib/api/client';

interface AcquisitionFormProps {
  onCalculate: (data: AcquisitionRequest) => Promise<void>;
  onReset: () => void;
  isLoading: boolean;
}

const initialFormState: AcquisitionRequest = {
  address: '',
  link: '',
  unit_count: 0,
  vintage: 0,
  stories: 0,
  total_buildings: 0,
  total_sf: 0,
  current_occupancy_pct: 0,
  estimated_annual_income: 0,
  notes: '',
};

// Example properties for quick testing
const EXAMPLE_PROPERTIES: Array<{
  name: string;
  description: string;
  color: string;
  data: AcquisitionRequest;
}> = [
  {
    name: 'Modern Midwest',
    description: 'New construction, low risk',
    color: 'bg-emerald-100 text-emerald-700 hover:bg-emerald-200',
    data: {
      address: '1500 Parkview Dr, Fort Wayne, IN 46845',
      link: '',
      unit_count: 180,
      vintage: 2018,
      stories: 3,
      total_buildings: 8,
      total_sf: 175000,
      current_occupancy_pct: 94,
      estimated_annual_income: 2800000,
      notes: 'Recently built garden-style community with modern amenities. Close to shopping and interstate access.',
    },
  },
  {
    name: 'Lakefront Vintage',
    description: 'Older property, flood risk',
    color: 'bg-amber-100 text-amber-700 hover:bg-amber-200',
    data: {
      address: '200 Lakeside Blvd, Indianapolis, IN 46220',
      link: '',
      unit_count: 64,
      vintage: 1962,
      stories: 4,
      total_buildings: 1,
      total_sf: 58000,
      current_occupancy_pct: 78,
      estimated_annual_income: 720000,
      notes: 'Historic lakefront property with water views. Built in 1962 with original knob-and-tube wiring and galvanized plumbing. Located in flood zone. Flat tar roof needs replacement. Currently 78% occupied due to ongoing renovations.',
    },
  },
  {
    name: 'Florida Coastal',
    description: 'High wind/hurricane zone',
    color: 'bg-rose-100 text-rose-700 hover:bg-rose-200',
    data: {
      address: '8500 Ocean Drive, Miami Beach, FL 33139',
      link: '',
      unit_count: 120,
      vintage: 2005,
      stories: 12,
      total_buildings: 1,
      total_sf: 145000,
      current_occupancy_pct: 91,
      estimated_annual_income: 4200000,
      notes: 'Beachfront high-rise condo conversion. 2 blocks from Atlantic Ocean. Impact-rated windows installed 2019. Concrete construction.',
    },
  },
];

export function AcquisitionForm({
  onCalculate,
  onReset,
  isLoading,
}: AcquisitionFormProps) {
  const [formData, setFormData] =
    useState<AcquisitionRequest>(initialFormState);

  const handleChange = useCallback(
    (field: keyof AcquisitionRequest, value: string | number) => {
      setFormData((prev) => ({ ...prev, [field]: value }));
    },
    []
  );

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      await onCalculate(formData);
    },
    [formData, onCalculate]
  );

  const handleReset = useCallback(() => {
    setFormData(initialFormState);
    onReset();
  }, [onReset]);

  const handleLoadExample = useCallback((example: AcquisitionRequest) => {
    setFormData(example);
  }, []);

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 overflow-y-auto">
      {/* Quick Examples Section */}
      <div className="mb-6 pb-4 border-b border-gray-100">
        <div className="flex items-center gap-2 mb-3">
          <Zap className="h-4 w-4 text-teal-600" />
          <span className="text-sm font-medium text-gray-700">Quick Examples</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {EXAMPLE_PROPERTIES.map((example) => (
            <button
              key={example.name}
              type="button"
              onClick={() => handleLoadExample(example.data)}
              disabled={isLoading}
              className={`
                px-3 py-1.5 rounded-full text-xs font-medium transition-colors
                ${example.color}
                disabled:opacity-50 disabled:cursor-not-allowed
              `}
              title={example.description}
            >
              {example.name}
            </button>
          ))}
        </div>
        <p className="text-xs text-gray-400 mt-2">
          Click an example to auto-fill the form and see different LLM responses
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Address */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Address<span className="text-red-500">*</span>
          </label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              value={formData.address}
              onChange={(e) => handleChange('address', e.target.value)}
              placeholder="Address"
              className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
              required
            />
          </div>
        </div>

        {/* Link (Optional) */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Link (Optional)
          </label>
          <div className="relative">
            <LinkIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="url"
              value={formData.link || ''}
              onChange={(e) => handleChange('link', e.target.value)}
              placeholder="Link (Optional)"
              className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
            />
          </div>
        </div>

        {/* Unit Count */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Unit Count<span className="text-red-500">*</span>
          </label>
          <input
            type="number"
            value={formData.unit_count || ''}
            onChange={(e) =>
              handleChange('unit_count', parseInt(e.target.value) || 0)
            }
            placeholder="Enter # of units"
            className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
            required
            min={1}
          />
        </div>

        {/* Vintage */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Vintage<span className="text-red-500">*</span>
          </label>
          <input
            type="number"
            value={formData.vintage || ''}
            onChange={(e) =>
              handleChange('vintage', parseInt(e.target.value) || 0)
            }
            placeholder="Enter vintage (year built)"
            className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
            required
            min={1800}
            max={2030}
          />
        </div>

        {/* Stories */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Stories<span className="text-red-500">*</span>
          </label>
          <input
            type="number"
            value={formData.stories || ''}
            onChange={(e) =>
              handleChange('stories', parseInt(e.target.value) || 0)
            }
            placeholder="Enter # of stories"
            className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
            required
            min={1}
          />
        </div>

        {/* Total Buildings */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Total Buildings<span className="text-red-500">*</span>
          </label>
          <input
            type="number"
            value={formData.total_buildings || ''}
            onChange={(e) =>
              handleChange('total_buildings', parseInt(e.target.value) || 0)
            }
            placeholder="Enter # of buildings"
            className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
            required
            min={1}
          />
        </div>

        {/* Total SF */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Total SF (Gross incl. non-residential buildings)
            <span className="text-red-500">*</span>
          </label>
          <input
            type="number"
            value={formData.total_sf || ''}
            onChange={(e) =>
              handleChange('total_sf', parseInt(e.target.value) || 0)
            }
            placeholder="Enter total square footage"
            className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
            required
            min={100}
          />
        </div>

        {/* Current Occupation */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Current Occupation (%)<span className="text-red-500">*</span>
          </label>
          <input
            type="number"
            value={formData.current_occupancy_pct || ''}
            onChange={(e) =>
              handleChange(
                'current_occupancy_pct',
                parseFloat(e.target.value) || 0
              )
            }
            placeholder="Enter % of occupation"
            className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
            required
            min={0}
            max={100}
            step="0.1"
          />
        </div>

        {/* Estimated Annual Gross Income */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Estimated Annual Gross Income<span className="text-red-500">*</span>
          </label>
          <input
            type="number"
            value={formData.estimated_annual_income || ''}
            onChange={(e) =>
              handleChange(
                'estimated_annual_income',
                parseInt(e.target.value) || 0
              )
            }
            placeholder="Enter estimated annual income"
            className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
            required
            min={0}
          />
        </div>

        {/* Notes */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Anything else noteworthy about community?
          </label>
          <textarea
            value={formData.notes || ''}
            onChange={(e) => handleChange('notes', e.target.value)}
            placeholder="Enter additional notes here..."
            className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 min-h-[80px] resize-none"
            maxLength={2000}
          />
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3 pt-4">
          <Button
            type="submit"
            variant="primary"
            className="flex-1"
            loading={isLoading}
          >
            Calculate
          </Button>
          <Button
            type="button"
            variant="outline"
            className="flex-1"
            onClick={handleReset}
            disabled={isLoading}
          >
            Reset
          </Button>
        </div>
      </form>
    </div>
  );
}
