'use client';

import type { PremiumRange } from '@/lib/api/client';

interface PremiumRangeBarProps {
  premiumRange: PremiumRange | null | undefined;
  label?: string | null;
}

export function PremiumRangeBar({ premiumRange, label }: PremiumRangeBarProps) {
  return (
    <div>
      <h3 className="text-sm font-medium text-gray-700 mb-3">Premium Ranges</h3>

      {/* Range Bar */}
      <div className="flex h-3 rounded-full overflow-hidden mb-4">
        <div className="flex-1 bg-teal-300" />
        <div className="flex-1 bg-teal-500" />
        <div className="flex-1 bg-teal-700" />
      </div>

      {/* Range Labels */}
      <div className="grid grid-cols-3 gap-4">
        <div className="text-center p-3 bg-teal-50 rounded-lg border border-teal-100">
          <div className="text-xs text-teal-600 font-medium mb-1">Low</div>
          <div className="text-sm font-semibold text-gray-900">
            {premiumRange
              ? `$${premiumRange.low.toLocaleString()}`
              : '-'}
          </div>
        </div>
        <div className="text-center p-3 bg-yellow-50 rounded-lg border border-yellow-100">
          <div className="text-xs text-yellow-600 font-medium mb-1">Medium</div>
          <div className="text-sm font-semibold text-gray-900">
            {premiumRange
              ? `$${premiumRange.mid.toLocaleString()}`
              : '-'}
          </div>
        </div>
        <div className="text-center p-3 bg-red-50 rounded-lg border border-red-100">
          <div className="text-xs text-red-600 font-medium mb-1">High</div>
          <div className="text-sm font-semibold text-gray-900">
            {premiumRange
              ? `$${premiumRange.high.toLocaleString()}`
              : '-'}
          </div>
        </div>
      </div>

      {/* Label */}
      {label && (
        <p className="text-xs text-gray-500 text-center mt-2">
          Premium per unit: {label}
        </p>
      )}
    </div>
  );
}
