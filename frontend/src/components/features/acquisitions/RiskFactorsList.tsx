'use client';

import { AlertTriangle, Info } from 'lucide-react';
import type { RiskFactor } from '@/lib/api/client';

interface RiskFactorsListProps {
  riskFactors: RiskFactor[];
}

const DEFAULT_RISK_FACTORS = [
  'Flood Zone',
  'Wind Exposure',
  'Vintage Wiring',
  'Fire Exposure',
  'Vintage Plumbing',
  'Tort Environments',
];

export function RiskFactorsList({ riskFactors }: RiskFactorsListProps) {
  // Create a map of actual risk factors
  const riskMap = new Map(riskFactors.map((r) => [r.name, r]));

  // Show all 6 slots, filled or empty
  const displayRisks = DEFAULT_RISK_FACTORS.map((name) => {
    const risk = riskMap.get(name);
    return {
      name,
      severity: risk?.severity,
      reason: risk?.reason,
      isActive: !!risk,
    };
  });

  const getSeverityStyles = (severity?: string, isActive?: boolean) => {
    if (!isActive) {
      return 'bg-gray-50 border-gray-200 text-gray-400';
    }

    switch (severity) {
      case 'critical':
        return 'bg-red-50 border-red-200 text-red-700';
      case 'warning':
        return 'bg-yellow-50 border-yellow-200 text-yellow-700';
      case 'info':
        return 'bg-blue-50 border-blue-200 text-blue-700';
      default:
        return 'bg-gray-50 border-gray-200 text-gray-400';
    }
  };

  const getIconColor = (severity?: string, isActive?: boolean) => {
    if (!isActive) return 'text-gray-300';

    switch (severity) {
      case 'critical':
        return 'text-red-500';
      case 'warning':
        return 'text-yellow-500';
      case 'info':
        return 'text-blue-500';
      default:
        return 'text-gray-300';
    }
  };

  return (
    <div className="mt-6">
      <div className="flex items-center gap-2 mb-3">
        <h3 className="text-sm font-medium text-gray-700">Insurance Factors</h3>
        <Info className="h-4 w-4 text-gray-400" />
      </div>

      <div className="grid grid-cols-2 gap-3">
        {displayRisks.map((risk) => (
          <div
            key={risk.name}
            className={`
              flex items-center gap-2 px-3 py-2.5 rounded-lg border transition-colors
              ${getSeverityStyles(risk.severity, risk.isActive)}
            `}
            title={risk.reason || undefined}
          >
            <AlertTriangle
              className={`h-4 w-4 flex-shrink-0 ${getIconColor(risk.severity, risk.isActive)}`}
            />
            <span className="text-sm font-medium truncate">
              {risk.isActive ? risk.name : '-'}
            </span>
          </div>
        ))}
      </div>

      {/* Active risk details */}
      {riskFactors.length > 0 && (
        <div className="mt-4 space-y-2">
          {riskFactors.map((risk) => (
            <div
              key={risk.name}
              className="text-xs text-gray-600 bg-gray-50 rounded p-2"
            >
              <span className="font-medium">{risk.name}:</span>{' '}
              {risk.reason || 'Risk identified'}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
