'use client';

import { AlertCircle, Download, Mail } from 'lucide-react';
import { Button } from '@/components/primitives';
import { RiskFactorsList } from './RiskFactorsList';
import { PremiumRangeBar } from './PremiumRangeBar';
import type { AcquisitionResult } from '@/lib/api/client';

interface UniquePropertyModalProps {
  result: AcquisitionResult;
}

export function UniquePropertyModal({ result }: UniquePropertyModalProps) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 overflow-y-auto">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">
          Acquisition Calculation
        </h2>
        <div className="flex gap-2">
          <button className="flex items-center gap-1 text-sm text-gray-400 cursor-not-allowed">
            <Download className="h-4 w-4" /> PDF
          </button>
          <button className="flex items-center gap-1 text-sm text-gray-400 cursor-not-allowed">
            <Mail className="h-4 w-4" /> Email
          </button>
        </div>
      </div>

      {/* Unique Property Alert */}
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <div className="w-16 h-16 bg-amber-100 rounded-full flex items-center justify-center mb-4">
          <AlertCircle className="h-8 w-8 text-amber-600" />
        </div>

        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          This property is a bit unique.
        </h3>

        <p className="text-gray-600 max-w-md mb-2">
          We need our insurance consultants to put their eyes on it and will
          circulate an email with estimates in the next 24 hours.
        </p>

        <p className="text-gray-500 text-sm max-w-md mb-6">
          Thanks for being a valued partner of Open Insurance.
        </p>

        {/* Preliminary Estimate if available */}
        {result.preliminary_estimate && (
          <div className="w-full max-w-md mb-6">
            <p className="text-sm text-gray-500 mb-2">
              Preliminary estimate (low confidence):
            </p>
            <PremiumRangeBar
              premiumRange={result.preliminary_estimate}
              label="preliminary range"
            />
          </div>
        )}

        {/* Uniqueness reason */}
        {result.uniqueness_reason && (
          <div className="w-full max-w-md p-3 bg-amber-50 border border-amber-100 rounded-lg mb-6">
            <p className="text-sm text-amber-700">{result.uniqueness_reason}</p>
          </div>
        )}

        {/* Risk factors if any */}
        {result.risk_factors && result.risk_factors.length > 0 && (
          <div className="w-full max-w-md">
            <RiskFactorsList riskFactors={result.risk_factors} />
          </div>
        )}

        <Button variant="primary" className="mt-6 min-w-[200px]">
          Close
        </Button>
      </div>
    </div>
  );
}
