'use client';

import { Loader2, Download, Mail, Info } from 'lucide-react';
import { PremiumRangeBar } from './PremiumRangeBar';
import { ComparablesChart } from './ComparablesChart';
import { RiskFactorsList } from './RiskFactorsList';
import { UniquePropertyModal } from './UniquePropertyModal';
import type { AcquisitionResult } from '@/lib/api/client';

interface AcquisitionResultsProps {
  result: AcquisitionResult | null;
  isLoading: boolean;
  error: string | null;
}

export function AcquisitionResults({
  result,
  isLoading,
  error,
}: AcquisitionResultsProps) {
  // Empty state
  if (!result && !isLoading && !error) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6">
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

        {/* Empty Premium Ranges */}
        <PremiumRangeBar premiumRange={null} />

        {/* Empty Chart */}
        <div className="mt-6">
          <h3 className="text-sm font-medium text-gray-700 mb-3">
            Recent Premium/Unit (Last 360 days)
          </h3>
          <div className="h-48 bg-gray-50 rounded-lg flex items-center justify-center">
            <span className="text-gray-400 text-sm">
              Enter property details to see comparables
            </span>
          </div>
        </div>

        {/* Empty Risk Factors */}
        <RiskFactorsList riskFactors={[]} />
      </div>
    );
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6 flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-teal-500 mx-auto mb-3" />
          <p className="text-gray-500">Analyzing property...</p>
          <p className="text-gray-400 text-sm mt-1">
            Finding comparables and assessing risks
          </p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6 flex items-center justify-center min-h-[400px]">
        <div className="text-center text-red-500">
          <p className="font-medium">Error</p>
          <p className="text-sm mt-1">{error}</p>
        </div>
      </div>
    );
  }

  // Unique property modal
  if (result?.is_unique) {
    return <UniquePropertyModal result={result} />;
  }

  // Normal results
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 overflow-y-auto">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">
          Acquisition Calculation
        </h2>
        <div className="flex gap-2">
          <button className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700">
            <Download className="h-4 w-4" /> PDF
          </button>
          <button className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700">
            <Mail className="h-4 w-4" /> Email
          </button>
        </div>
      </div>

      {/* Message */}
      {result?.message && (
        <p className="text-sm text-gray-600 italic mb-4">{result.message}</p>
      )}

      {/* Premium Ranges */}
      <PremiumRangeBar
        premiumRange={result?.premium_range}
        label={result?.premium_range_label}
      />

      {/* Comparables Chart */}
      <div className="mt-6">
        <h3 className="text-sm font-medium text-gray-700 mb-3">
          Recent Premium/Unit (Last 360 days)
        </h3>
        <ComparablesChart comparables={result?.comparables || []} />
      </div>

      {/* Risk Factors */}
      <RiskFactorsList riskFactors={result?.risk_factors || []} />

      {/* Footnote */}
      {result?.comparables && result.comparables.length > 0 && (
        <div className="mt-4 flex items-center gap-2 text-xs text-gray-500">
          <Info className="h-3 w-3" />
          <span>
            The comparable set is from similar vintage and sized properties
            within ~20 miles.
          </span>
        </div>
      )}

      {/* LLM Explanation */}
      {result?.llm_explanation && (
        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <p className="text-xs text-gray-600">{result.llm_explanation}</p>
        </div>
      )}
    </div>
  );
}
