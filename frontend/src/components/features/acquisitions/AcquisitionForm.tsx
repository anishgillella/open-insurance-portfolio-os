'use client';

import { useState, useCallback } from 'react';
import { Search, Link as LinkIcon } from 'lucide-react';
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

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 overflow-y-auto">
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
