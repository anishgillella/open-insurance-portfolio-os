# Frontend Components

## Overview

The Acquisitions page follows existing frontend patterns from the codebase:
- Next.js 16 App Router (`'use client'` directive)
- Tailwind CSS for styling
- Recharts for data visualization
- Lucide React for icons
- Framer Motion for animations

---

## Page Structure

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Header: "Acquisitions"                          [Bell] [Upload Document] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────┐  ┌─────────────────────────────────────┐  │
│  │                         │  │                                     │  │
│  │    ACQUISITION FORM     │  │      ACQUISITION CALCULATION        │  │
│  │                         │  │                                     │  │
│  │  Address*               │  │  Premium Ranges                     │  │
│  │  [________________]     │  │  [Low][Medium][High] indicator      │  │
│  │                         │  │                                     │  │
│  │  Link (Optional)        │  │  Recent Premium/Unit (Last 360d)    │  │
│  │  [________________]     │  │  [Scatter Chart]                    │  │
│  │                         │  │                                     │  │
│  │  Unit Count*            │  │  Insurance Factors                  │  │
│  │  [________________]     │  │  [Risk][Risk][Risk]                 │  │
│  │                         │  │  [Risk][Risk][Risk]                 │  │
│  │  ... more fields ...    │  │                                     │  │
│  │                         │  │                                     │  │
│  │  [Calculate] [Reset]    │  │                                     │  │
│  │                         │  │                                     │  │
│  └─────────────────────────┘  └─────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Component Hierarchy

```
app/acquisitions/page.tsx
├── AcquisitionForm.tsx
│   └── Form fields + Calculate/Reset buttons
└── AcquisitionResults.tsx
    ├── PremiumRangeBar.tsx
    ├── ComparablesChart.tsx
    ├── RiskFactorsList.tsx
    └── UniquePropertyModal.tsx (conditional)
```

---

## File: `app/acquisitions/page.tsx`

Main page component with two-column layout.

```typescript
'use client';

import { useState, useCallback } from 'react';
import { Bell, Upload } from 'lucide-react';
import { Button } from '@/components/primitives';
import { AcquisitionForm } from '@/components/features/acquisitions/AcquisitionForm';
import { AcquisitionResults } from '@/components/features/acquisitions/AcquisitionResults';
import { acquisitionsApi, type AcquisitionRequest, type AcquisitionResult } from '@/lib/api';

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
          <Button variant="ghost" size="sm" leftIcon={<Upload className="h-4 w-4" />}>
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
```

---

## File: `AcquisitionForm.tsx`

Form component with all input fields.

```typescript
'use client';

import { useState, useCallback } from 'react';
import { Search, Link as LinkIcon } from 'lucide-react';
import { Button, Input } from '@/components/primitives';
import type { AcquisitionRequest } from '@/lib/api';

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

export function AcquisitionForm({ onCalculate, onReset, isLoading }: AcquisitionFormProps) {
  const [formData, setFormData] = useState<AcquisitionRequest>(initialFormState);

  const handleChange = useCallback((field: keyof AcquisitionRequest, value: string | number) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  }, []);

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
    <div className="bg-white rounded-xl border border-gray-200 p-6">
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
            onChange={(e) => handleChange('unit_count', parseInt(e.target.value) || 0)}
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
            onChange={(e) => handleChange('vintage', parseInt(e.target.value) || 0)}
            placeholder="Enter vintage"
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
            onChange={(e) => handleChange('stories', parseInt(e.target.value) || 0)}
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
            onChange={(e) => handleChange('total_buildings', parseInt(e.target.value) || 0)}
            placeholder="Enter # of buildings"
            className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
            required
            min={1}
          />
        </div>

        {/* Total SF */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Total SF (Gross incl. non-residential buildings)<span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={formData.total_sf ? `${formData.total_sf.toLocaleString()} sq ft` : ''}
            onChange={(e) => {
              const value = e.target.value.replace(/[^0-9]/g, '');
              handleChange('total_sf', parseInt(value) || 0);
            }}
            placeholder="Enter total square footage"
            className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
            required
          />
        </div>

        {/* Current Occupation */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Current Occupation<span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={formData.current_occupancy_pct ? `${formData.current_occupancy_pct}%` : ''}
            onChange={(e) => {
              const value = e.target.value.replace(/[^0-9.]/g, '');
              handleChange('current_occupancy_pct', parseFloat(value) || 0);
            }}
            placeholder="Enter % of occupation"
            className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
            required
          />
        </div>

        {/* Estimated Annual Gross Income */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Estimated Annual Gross Income<span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={formData.estimated_annual_income ? `$${formData.estimated_annual_income.toLocaleString()}` : ''}
            onChange={(e) => {
              const value = e.target.value.replace(/[^0-9]/g, '');
              handleChange('estimated_annual_income', parseInt(value) || 0);
            }}
            placeholder="Enter here"
            className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
            required
          />
        </div>

        {/* Notes */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Anything else noteworthy about community?
          </label>
          <input
            type="text"
            value={formData.notes || ''}
            onChange={(e) => handleChange('notes', e.target.value)}
            placeholder="Enter here"
            className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
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
          >
            Reset
          </Button>
        </div>
      </form>
    </div>
  );
}
```

---

## File: `AcquisitionResults.tsx`

Results panel with conditional rendering.

```typescript
'use client';

import { Loader2, Download, Mail, Info } from 'lucide-react';
import { PremiumRangeBar } from './PremiumRangeBar';
import { ComparablesChart } from './ComparablesChart';
import { RiskFactorsList } from './RiskFactorsList';
import { UniquePropertyModal } from './UniquePropertyModal';
import type { AcquisitionResult } from '@/lib/api';

interface AcquisitionResultsProps {
  result: AcquisitionResult | null;
  isLoading: boolean;
  error: string | null;
}

export function AcquisitionResults({ result, isLoading, error }: AcquisitionResultsProps) {
  // Empty state
  if (!result && !isLoading && !error) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Acquisition Calculation</h2>
          <div className="flex gap-2">
            <button className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700">
              <Download className="h-4 w-4" /> PDF
            </button>
            <button className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700">
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
            <span className="text-gray-400 text-sm">Enter property details to see comparables</span>
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
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6 flex items-center justify-center min-h-[400px]">
        <div className="text-center text-red-500">
          <p>{error}</p>
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
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Acquisition Calculation</h2>
        <div className="flex gap-2">
          <button className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700">
            <Download className="h-4 w-4" /> PDF
          </button>
          <button className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700">
            <Mail className="h-4 w-4" /> Email
          </button>
        </div>
      </div>

      {/* Premium Ranges */}
      <PremiumRangeBar
        premiumRange={result?.premium_range}
        label={result?.premium_range_label}
        message={result?.message}
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
            The comparable set is from similar vintage and sized properties within ~20 miles.
          </span>
        </div>
      )}
    </div>
  );
}
```

---

## File: `PremiumRangeBar.tsx`

Visual indicator for premium ranges.

```typescript
'use client';

import type { PremiumRange } from '@/lib/api';

interface PremiumRangeBarProps {
  premiumRange: PremiumRange | null | undefined;
  label?: string | null;
  message?: string | null;
}

export function PremiumRangeBar({ premiumRange, label, message }: PremiumRangeBarProps) {
  return (
    <div>
      <h3 className="text-sm font-medium text-gray-700 mb-2">Premium Ranges</h3>

      {message && (
        <p className="text-sm text-gray-600 italic mb-3">{message}</p>
      )}

      {/* Range Bar */}
      <div className="flex h-2 rounded-full overflow-hidden mb-3">
        <div className="flex-1 bg-teal-400" />
        <div className="flex-1 bg-teal-500" />
        <div className="flex-1 bg-teal-600" />
      </div>

      {/* Range Labels */}
      <div className="grid grid-cols-3 gap-4">
        <div className="text-center">
          <div className="text-xs text-teal-500 font-medium mb-1">Low</div>
          <div className="text-sm text-gray-900">
            {premiumRange ? `$${premiumRange.low.toLocaleString()} - $${premiumRange.mid.toLocaleString()}` : '-'}
          </div>
        </div>
        <div className="text-center">
          <div className="text-xs text-yellow-500 font-medium mb-1">Medium</div>
          <div className="text-sm text-gray-900">
            {premiumRange ? `$${premiumRange.mid.toLocaleString()} - $${premiumRange.high.toLocaleString()}` : '-'}
          </div>
        </div>
        <div className="text-center">
          <div className="text-xs text-red-500 font-medium mb-1">High</div>
          <div className="text-sm text-gray-900">
            {premiumRange ? `$${premiumRange.high.toLocaleString()}+` : '-'}
          </div>
        </div>
      </div>
    </div>
  );
}
```

---

## File: `ComparablesChart.tsx`

Scatter chart for comparable properties.

```typescript
'use client';

import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import type { ComparableProperty } from '@/lib/api';

interface ComparablesChartProps {
  comparables: ComparableProperty[];
}

export function ComparablesChart({ comparables }: ComparablesChartProps) {
  // Transform data for chart
  const chartData = comparables.map((comp, index) => ({
    x: index,
    y: comp.premium_per_unit,
    name: comp.name,
    address: comp.address,
    date: comp.premium_date,
  }));

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3">
          <p className="font-medium text-gray-900">{data.name}</p>
          <p className="text-sm text-gray-500">{data.address}</p>
          <p className="text-sm text-teal-600">
            Premium/Unit: ${data.y.toLocaleString()}
          </p>
        </div>
      );
    }
    return null;
  };

  if (chartData.length === 0) {
    return (
      <div className="h-48 bg-gray-50 rounded-lg flex items-center justify-center">
        <span className="text-gray-400 text-sm">No comparable data available</span>
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={200}>
      <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
        <XAxis
          dataKey="x"
          type="number"
          name="Month"
          axisLine={false}
          tickLine={false}
          tick={{ fill: '#6B7280', fontSize: 12 }}
          tickFormatter={(value) => {
            const months = ['Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov'];
            return months[value] || '';
          }}
        />
        <YAxis
          dataKey="y"
          type="number"
          name="Premium/Unit"
          axisLine={false}
          tickLine={false}
          tick={{ fill: '#6B7280', fontSize: 12 }}
          tickFormatter={(value) => `$${value.toLocaleString()}`}
        />
        <Tooltip content={<CustomTooltip />} />
        <Scatter
          data={chartData}
          fill="#10B981"
          shape="circle"
        />
      </ScatterChart>
    </ResponsiveContainer>
  );
}
```

---

## File: `RiskFactorsList.tsx`

Grid of risk factor badges.

```typescript
'use client';

import { AlertTriangle, Info } from 'lucide-react';
import type { RiskFactor } from '@/lib/api';

interface RiskFactorsListProps {
  riskFactors: RiskFactor[];
}

const defaultRiskFactors = [
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
  const displayRisks = defaultRiskFactors.map((name) => {
    const risk = riskMap.get(name);
    return {
      name,
      severity: risk?.severity,
      reason: risk?.reason,
      isActive: !!risk,
    };
  });

  const getSeverityColor = (severity?: string) => {
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
              flex items-center gap-2 px-3 py-2 rounded-lg border
              ${getSeverityColor(risk.severity)}
            `}
          >
            <AlertTriangle className="h-4 w-4 flex-shrink-0" />
            <span className="text-sm font-medium">
              {risk.isActive ? risk.name : '-'}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## File: `UniquePropertyModal.tsx`

Modal for unique properties requiring consultant review.

```typescript
'use client';

import { AlertCircle } from 'lucide-react';
import { Button } from '@/components/primitives';
import type { AcquisitionResult } from '@/lib/api';

interface UniquePropertyModalProps {
  result: AcquisitionResult;
}

export function UniquePropertyModal({ result }: UniquePropertyModalProps) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 flex flex-col items-center justify-center min-h-[400px]">
      <AlertCircle className="h-12 w-12 text-gray-400 mb-4" />

      <h2 className="text-lg font-semibold text-gray-900 mb-2">
        This property is a bit unique.
      </h2>

      <p className="text-gray-600 text-center max-w-md mb-2">
        We need our insurance consultants to put their eyes on it and will circulate
        an email with estimates in the next 24 hours.
      </p>

      <p className="text-gray-600 text-center max-w-md mb-6">
        Thanks for being a valued partner of Open Insurance.
      </p>

      <Button variant="primary" className="min-w-[200px]">
        Close
      </Button>
    </div>
  );
}
```

---

## Sidebar Navigation

### File: `Sidebar.tsx` (modification)

Add to navigation items:

```typescript
import { Calculator } from 'lucide-react';

// Add to nav items array
{
  label: 'Acquisitions',
  href: '/acquisitions',
  icon: Calculator,
},
```

---

## API Integration

### File: `lib/api/index.ts` (additions)

```typescript
// Types
export interface AcquisitionRequest {
  address: string;
  link?: string;
  unit_count: number;
  vintage: number;
  stories: number;
  total_buildings: number;
  total_sf: number;
  current_occupancy_pct: number;
  estimated_annual_income: number;
  notes?: string;
}

export interface PremiumRange {
  low: number;
  mid: number;
  high: number;
}

export interface ComparableProperty {
  property_id: string;
  name: string;
  address: string;
  premium_per_unit: number;
  premium_date: string;
  similarity_score: number;
  similarity_reason?: string;
}

export interface RiskFactor {
  name: string;
  severity: 'info' | 'warning' | 'critical';
  reason?: string;
}

export interface AcquisitionResult {
  is_unique: boolean;
  uniqueness_reason?: string;
  confidence: 'high' | 'medium' | 'low';
  premium_range?: PremiumRange;
  premium_range_label?: string;
  preliminary_estimate?: PremiumRange;
  message?: string;
  comparables: ComparableProperty[];
  risk_factors: RiskFactor[];
  llm_explanation?: string;
}

// API
export const acquisitionsApi = {
  calculate: (data: AcquisitionRequest) =>
    apiPost<AcquisitionResult>('/acquisitions/calculate', data),
};
```

---

## Related Documents

- [01-data-model.md](./01-data-model.md) - TypeScript types match these schemas
- [03-api-design.md](./03-api-design.md) - API endpoint these components call
- [05-implementation-phases.md](./05-implementation-phases.md) - Build order
