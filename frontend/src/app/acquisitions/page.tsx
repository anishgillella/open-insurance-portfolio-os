'use client';

import { useState, useCallback } from 'react';
import { Bell, Upload } from 'lucide-react';
import { Button } from '@/components/primitives';
import { AcquisitionForm } from '@/components/features/acquisitions/AcquisitionForm';
import { AcquisitionResults } from '@/components/features/acquisitions/AcquisitionResults';
import {
  acquisitionsApi,
  type AcquisitionRequest,
  type AcquisitionResult,
} from '@/lib/api/client';

export default function AcquisitionsPage() {
  const [result, setResult] = useState<AcquisitionResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCalculate = useCallback(async (formData: AcquisitionRequest) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await acquisitionsApi.calculate(formData);
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to calculate');
      setResult(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleReset = useCallback(() => {
    setResult(null);
    setError(null);
  }, []);

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold text-gray-900">Acquisitions</h1>
        <div className="flex items-center gap-3">
          <button className="p-2 text-gray-400 hover:text-gray-600">
            <Bell className="h-5 w-5" />
          </button>
          <Button
            variant="ghost"
            size="sm"
            leftIcon={<Upload className="h-4 w-4" />}
          >
            Upload Document
          </Button>
        </div>
      </div>

      {/* Two-column layout */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Form */}
        <AcquisitionForm
          onCalculate={handleCalculate}
          onReset={handleReset}
          isLoading={isLoading}
        />

        {/* Right: Results */}
        <AcquisitionResults
          result={result}
          isLoading={isLoading}
          error={error}
        />
      </div>
    </div>
  );
}
