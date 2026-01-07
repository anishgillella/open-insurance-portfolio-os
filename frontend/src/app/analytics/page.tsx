'use client';

import { useState, useRef, useEffect } from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { Bell, ChevronDown, Upload, Info } from 'lucide-react';
import { Button } from '@/components/primitives';
import { cn } from '@/lib/utils';

// Types
type TabType =
  | 'premium-unit-trends'
  | 'premium-unit'
  | 'total-premium'
  | 'tiv-unit'
  | 'total-tiv'
  | 'rate'
  | 'loss-run';

type TimeRange = 'Last Year' | 'Last 2 Years' | 'Last 5 Years' | 'Last 10 Years';

type PropertyFilter = 'All' | 'All Multifamily' | 'All Office' | string;

// Tab configuration
const tabs: { id: TabType; label: string }[] = [
  { id: 'premium-unit-trends', label: 'Premium/Unit Trends' },
  { id: 'premium-unit', label: 'Premium / Unit' },
  { id: 'total-premium', label: 'Total Premium' },
  { id: 'tiv-unit', label: 'TIV/Unit' },
  { id: 'total-tiv', label: 'Total TIV' },
  { id: 'rate', label: 'Rate' },
  { id: 'loss-run', label: 'Loss Run' },
];

// Properties for filter
const properties = [
  { id: 'all', name: 'All' },
  { id: 'all-multifamily', name: 'All Multifamily' },
  { id: 'all-office', name: 'All Office' },
  { id: 'solana', name: 'Solana Apartments' },
  { id: 'bend', name: 'Bend Apartments' },
  { id: 'retreat', name: 'Retreat Apartments' },
];

// Generate mock data for Premium/Unit Trends (comparison with market)
const generatePremiumTrendsData = () => {
  const data = [];
  const startDate = new Date('2024-10-01');

  for (let i = 0; i < 13; i++) {
    const date = new Date(startDate);
    date.setMonth(date.getMonth() + i);
    const monthLabel = `${(date.getMonth() + 1).toString().padStart(2, '0')}/${date.getFullYear().toString().slice(2)}`;

    // Your premiums - relatively stable around $1200
    const yourPremium = 1100 + Math.random() * 150 + (i > 6 ? 100 : 0);

    // Comparable premiums - more volatile, generally lower
    const comparablePremium = 1000 + Math.random() * 300 + (i > 3 && i < 8 ? -50 : 0);

    data.push({
      month: monthLabel,
      yourPremiums: Math.round(yourPremium),
      comparablePremiums: Math.round(comparablePremium),
    });
  }
  return data;
};

// Generate mock data for multi-property line charts
const generateMultiPropertyData = (baseValues: { solana: number; bend: number; retreat: number }, growth: number) => {
  const data = [];
  const startDate = new Date('2024-10-01');

  for (let i = 0; i < 13; i++) {
    const date = new Date(startDate);
    date.setMonth(date.getMonth() + i);
    const monthLabel = `${(date.getMonth() + 1).toString().padStart(2, '0')}/${date.getFullYear().toString().slice(2)}`;

    data.push({
      month: monthLabel,
      solana: Math.round(baseValues.solana * (1 + (growth * i / 12))),
      bend: Math.round(baseValues.bend * (1 + (growth * i / 12))),
      retreat: Math.round(baseValues.retreat * (1 + (growth * i / 12))),
    });
  }
  return data;
};

// Generate Loss Run data (bar chart by year)
const generateLossRunData = () => {
  return [
    { year: '2020', solana: 32000, bend: 38000, retreat: 28000 },
    { year: '2021', solana: 35000, bend: 40000, retreat: 30000 },
    { year: '2022', solana: 30000, bend: 35000, retreat: 32000 },
    { year: '2023', solana: 20000, bend: 28000, retreat: 12000 },
    { year: '2024', solana: 38000, bend: 32000, retreat: 35000 },
    { year: '2025', solana: 32000, bend: 35000, retreat: 30000 },
  ];
};

// Mock data sets
const premiumTrendsData = generatePremiumTrendsData();
const premiumUnitData = generateMultiPropertyData({ solana: 1150, bend: 1050, retreat: 950 }, 0.15);
const totalPremiumData = generateMultiPropertyData({ solana: 220000, bend: 180000, retreat: 45000 }, 0.20);
const tivUnitData = generateMultiPropertyData({ solana: 340000, bend: 290000, retreat: 250000 }, 0.12);
const totalTivData = generateMultiPropertyData({ solana: 3400000, bend: 2900000, retreat: 2500000 }, 0.12);
const rateData = generateMultiPropertyData({ solana: 0.29, bend: 0.25, retreat: 0.20 }, 0.35);
const lossRunData = generateLossRunData();

// Custom tooltip for Premium Trends
const PremiumTrendsTooltip = ({ active, payload }: { active?: boolean; payload?: Array<{ value: number; dataKey: string }> }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3">
        <p className="text-sm font-medium text-gray-900 mb-1">Premium</p>
        <p className="text-sm text-gray-600">Your Premium: ${payload[0]?.value?.toLocaleString()}</p>
        <p className="text-sm text-gray-600">Comparable Premium: ${payload[1]?.value?.toLocaleString()}</p>
      </div>
    );
  }
  return null;
};

// Custom tooltip for multi-property charts
const MultiPropertyTooltip = ({
  active,
  payload,
  title,
  prefix = '$',
  suffix = '',
  formatter = (v: number) => v.toLocaleString()
}: {
  active?: boolean;
  payload?: Array<{ value: number; dataKey: string }>;
  title: string;
  prefix?: string;
  suffix?: string;
  formatter?: (v: number) => string;
}) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3">
        <p className="text-sm font-medium text-gray-900 mb-1">{title}</p>
        <p className="text-sm text-gray-600">Solana Apartments: {prefix}{formatter(payload[0]?.value || 0)}{suffix}</p>
        <p className="text-sm text-gray-600">Bend Apartments: {prefix}{formatter(payload[1]?.value || 0)}{suffix}</p>
        <p className="text-sm text-gray-600">Retreat Apartments: {prefix}{formatter(payload[2]?.value || 0)}{suffix}</p>
      </div>
    );
  }
  return null;
};

// Custom tooltip for comparison charts (with comparable and recommended)
const ComparisonTooltip = ({
  active,
  payload,
  title,
  prefix = '$',
  suffix = '',
  formatter = (v: number) => v.toLocaleString()
}: {
  active?: boolean;
  payload?: Array<{ value: number; dataKey: string }>;
  title: string;
  prefix?: string;
  suffix?: string;
  formatter?: (v: number) => string;
}) => {
  if (active && payload && payload.length) {
    const solanaValue = payload[0]?.value || 0;
    // Mock comparable and recommended values
    const comparableValue = solanaValue * 0.85;
    const recommendedValue = solanaValue * 0.75;

    return (
      <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3">
        <p className="text-sm font-medium text-gray-900 mb-1">{title}</p>
        <p className="text-sm text-gray-600">Solana Apartments: {prefix}{formatter(solanaValue)}{suffix}</p>
        <p className="text-sm text-gray-600">Comparable Coverage: {prefix}{formatter(Math.round(comparableValue))}{suffix}</p>
        <p className="text-sm text-gray-600">Recommended Coverage: {prefix}{formatter(Math.round(recommendedValue))}{suffix}</p>
      </div>
    );
  }
  return null;
};

// Loss Run tooltip
const LossRunTooltip = ({ active, payload }: { active?: boolean; payload?: Array<{ value: number; dataKey: string }> }) => {
  if (active && payload && payload.length) {
    const solanaValue = payload[0]?.value || 0;
    // Mock comparable and recommended
    const comparableValue = solanaValue * 1.5;
    const recommendedValue = solanaValue * 0.5;

    return (
      <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3">
        <p className="text-sm font-medium text-gray-900 mb-1">Loss Run</p>
        <p className="text-sm text-gray-600">Solana Apartments: ${solanaValue.toLocaleString()}</p>
        <p className="text-sm text-gray-600">Comparable Coverage: ${comparableValue.toLocaleString()}</p>
        <p className="text-sm text-gray-600">Recommended Coverage: ${recommendedValue.toLocaleString()}</p>
      </div>
    );
  }
  return null;
};

// Dropdown component
function Dropdown({
  value,
  options,
  onChange,
  className = ''
}: {
  value: string;
  options: { value: string; label: string }[];
  onChange: (value: string) => void;
  className?: string;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const selectedOption = options.find(o => o.value === value);

  return (
    <div className={cn("relative", className)} ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 text-sm bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
      >
        <span className="text-gray-700">{selectedOption?.label}</span>
        <ChevronDown className="h-4 w-4 text-gray-400" />
      </button>
      {isOpen && (
        <div className="absolute top-full mt-1 right-0 bg-white border border-gray-200 rounded-lg shadow-lg py-1 min-w-[160px] z-20">
          {options.map((option) => (
            <button
              key={option.value}
              onClick={() => {
                onChange(option.value);
                setIsOpen(false);
              }}
              className={cn(
                'w-full px-3 py-2 text-left text-sm hover:bg-gray-50 transition-colors',
                option.value === value ? 'text-teal-600 bg-teal-50' : 'text-gray-700'
              )}
            >
              {option.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default function AnalyticsPage() {
  const [activeTab, setActiveTab] = useState<TabType>('premium-unit-trends');
  const [propertyFilter, setPropertyFilter] = useState<string>('solana');
  const [timeRange, setTimeRange] = useState<string>('last-year');

  const propertyOptions = properties.map(p => ({ value: p.id, label: p.name }));

  const timeRangeOptions = [
    { value: 'last-year', label: 'Last Year' },
    { value: 'last-2-years', label: 'Last 2 Years' },
    { value: 'last-5-years', label: 'Last 5 Years' },
    { value: 'last-10-years', label: 'Last 10 Years' },
  ];

  // Chart colors matching the mockups
  const colors = {
    green: '#10B981',  // Teal/green for primary (Solana / Your Premiums)
    blue: '#3B82F6',   // Blue for secondary (Bend / Comparable)
    yellow: '#F59E0B', // Yellow/orange for tertiary (Retreat)
  };

  const formatYAxisValue = (value: number, type: string) => {
    if (type === 'currency-k') {
      return `$${(value / 1000).toFixed(0)}k`;
    }
    if (type === 'currency-m') {
      return `$${(value / 1000000).toFixed(1)}m`;
    }
    if (type === 'currency') {
      return `$${value.toLocaleString()}`;
    }
    if (type === 'decimal') {
      return value.toFixed(2);
    }
    return value.toString();
  };

  const renderChart = () => {
    switch (activeTab) {
      case 'premium-unit-trends':
        return (
          <div className="space-y-4">
            <h2 className="text-lg font-medium text-gray-900">Premium Trends Compared to Market</h2>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={premiumTrendsData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis
                  dataKey="month"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#6B7280', fontSize: 12 }}
                />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#6B7280', fontSize: 12 }}
                  tickFormatter={(value) => `$${value.toLocaleString()}`}
                  domain={[1000, 1500]}
                />
                <Tooltip content={<PremiumTrendsTooltip />} />
                <Legend
                  verticalAlign="bottom"
                  height={36}
                  formatter={(value) => {
                    if (value === 'yourPremiums') return 'Your Premiums';
                    if (value === 'comparablePremiums') return 'Comparable Premiums';
                    return value;
                  }}
                />
                <Line
                  type="linear"
                  dataKey="yourPremiums"
                  stroke={colors.green}
                  strokeWidth={2}
                  dot={{ fill: colors.green, r: 4 }}
                  activeDot={{ r: 6 }}
                />
                <Line
                  type="linear"
                  dataKey="comparablePremiums"
                  stroke={colors.blue}
                  strokeWidth={2}
                  dot={{ fill: colors.blue, r: 4 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        );

      case 'premium-unit':
        return (
          <div className="space-y-4">
            <h2 className="text-lg font-medium text-gray-900">Premium / Unit</h2>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={premiumUnitData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis
                  dataKey="month"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#6B7280', fontSize: 12 }}
                />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#6B7280', fontSize: 12 }}
                  tickFormatter={(value) => `$${value.toLocaleString()}`}
                  domain={[900, 1500]}
                />
                <Tooltip content={<MultiPropertyTooltip title="Total Premium" />} />
                <Legend
                  verticalAlign="bottom"
                  height={36}
                  formatter={(value) => {
                    if (value === 'solana') return 'Solana Apartments';
                    if (value === 'bend') return 'Bend Apartments';
                    if (value === 'retreat') return 'Retreat Apartments';
                    return value;
                  }}
                />
                <Line
                  type="linear"
                  dataKey="solana"
                  stroke={colors.green}
                  strokeWidth={2}
                  dot={{ fill: colors.green, r: 4 }}
                />
                <Line
                  type="linear"
                  dataKey="bend"
                  stroke={colors.blue}
                  strokeWidth={2}
                  dot={{ fill: colors.blue, r: 4 }}
                />
                <Line
                  type="linear"
                  dataKey="retreat"
                  stroke={colors.yellow}
                  strokeWidth={2}
                  dot={{ fill: colors.yellow, r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        );

      case 'total-premium':
        return (
          <div className="space-y-4">
            <h2 className="text-lg font-medium text-gray-900">Total Premium</h2>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={totalPremiumData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis
                  dataKey="month"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#6B7280', fontSize: 12 }}
                />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#6B7280', fontSize: 12 }}
                  tickFormatter={(value) => formatYAxisValue(value, 'currency-k')}
                  domain={[0, 550000]}
                />
                <Tooltip content={<ComparisonTooltip title="Total Premium" formatter={(v) => `${(v / 1000).toFixed(0)}k`} />} />
                <Legend
                  verticalAlign="bottom"
                  height={36}
                  formatter={(value) => {
                    if (value === 'solana') return 'Solana Apartments';
                    if (value === 'bend') return 'Bend Apartments';
                    if (value === 'retreat') return 'Retreat Apartments';
                    return value;
                  }}
                />
                <Line
                  type="linear"
                  dataKey="solana"
                  stroke={colors.green}
                  strokeWidth={2}
                  dot={{ fill: colors.green, r: 4 }}
                />
                <Line
                  type="linear"
                  dataKey="bend"
                  stroke={colors.blue}
                  strokeWidth={2}
                  dot={{ fill: colors.blue, r: 4 }}
                />
                <Line
                  type="linear"
                  dataKey="retreat"
                  stroke={colors.yellow}
                  strokeWidth={2}
                  dot={{ fill: colors.yellow, r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        );

      case 'tiv-unit':
        return (
          <div className="space-y-4">
            <h2 className="text-lg font-medium text-gray-900">TIV/Unit</h2>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={tivUnitData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis
                  dataKey="month"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#6B7280', fontSize: 12 }}
                />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#6B7280', fontSize: 12 }}
                  tickFormatter={(value) => formatYAxisValue(value, 'currency-k')}
                  domain={[200000, 500000]}
                />
                <Tooltip content={<ComparisonTooltip title="TIV/Unit" formatter={(v) => `${(v / 1000).toFixed(0)}k`} />} />
                <Legend
                  verticalAlign="bottom"
                  height={36}
                  formatter={(value) => {
                    if (value === 'solana') return 'Solana Apartments';
                    if (value === 'bend') return 'Bend Apartments';
                    if (value === 'retreat') return 'Retreat Apartments';
                    return value;
                  }}
                />
                <Line
                  type="linear"
                  dataKey="solana"
                  stroke={colors.green}
                  strokeWidth={2}
                  dot={{ fill: colors.green, r: 4 }}
                />
                <Line
                  type="linear"
                  dataKey="bend"
                  stroke={colors.blue}
                  strokeWidth={2}
                  dot={{ fill: colors.blue, r: 4 }}
                />
                <Line
                  type="linear"
                  dataKey="retreat"
                  stroke={colors.yellow}
                  strokeWidth={2}
                  dot={{ fill: colors.yellow, r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        );

      case 'total-tiv':
        return (
          <div className="space-y-4">
            <h2 className="text-lg font-medium text-gray-900">Total TIV</h2>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={totalTivData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis
                  dataKey="month"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#6B7280', fontSize: 12 }}
                />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#6B7280', fontSize: 12 }}
                  tickFormatter={(value) => formatYAxisValue(value, 'currency-m')}
                  domain={[2000000, 6000000]}
                />
                <Tooltip content={<ComparisonTooltip title="Total TIV" formatter={(v) => `${(v / 1000000).toFixed(1)}m`} />} />
                <Legend
                  verticalAlign="bottom"
                  height={36}
                  formatter={(value) => {
                    if (value === 'solana') return 'Solana Apartments';
                    if (value === 'bend') return 'Bend Apartments';
                    if (value === 'retreat') return 'Retreat Apartments';
                    return value;
                  }}
                />
                <Line
                  type="linear"
                  dataKey="solana"
                  stroke={colors.green}
                  strokeWidth={2}
                  dot={{ fill: colors.green, r: 4 }}
                />
                <Line
                  type="linear"
                  dataKey="bend"
                  stroke={colors.blue}
                  strokeWidth={2}
                  dot={{ fill: colors.blue, r: 4 }}
                />
                <Line
                  type="linear"
                  dataKey="retreat"
                  stroke={colors.yellow}
                  strokeWidth={2}
                  dot={{ fill: colors.yellow, r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        );

      case 'rate':
        return (
          <div className="space-y-4">
            <h2 className="text-lg font-medium text-gray-900">Rate (/100 TIV)</h2>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={rateData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis
                  dataKey="month"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#6B7280', fontSize: 12 }}
                />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#6B7280', fontSize: 12 }}
                  tickFormatter={(value) => value.toFixed(2)}
                  domain={[0.15, 0.50]}
                />
                <Tooltip content={<ComparisonTooltip title="Rate" prefix="" formatter={(v) => v.toFixed(2)} />} />
                <Legend
                  verticalAlign="bottom"
                  height={36}
                  formatter={(value) => {
                    if (value === 'solana') return 'Solana Apartments';
                    if (value === 'bend') return 'Bend Apartments';
                    if (value === 'retreat') return 'Retreat Apartments';
                    return value;
                  }}
                />
                <Line
                  type="linear"
                  dataKey="solana"
                  stroke={colors.green}
                  strokeWidth={2}
                  dot={{ fill: colors.green, r: 4 }}
                />
                <Line
                  type="linear"
                  dataKey="bend"
                  stroke={colors.blue}
                  strokeWidth={2}
                  dot={{ fill: colors.blue, r: 4 }}
                />
                <Line
                  type="linear"
                  dataKey="retreat"
                  stroke={colors.yellow}
                  strokeWidth={2}
                  dot={{ fill: colors.yellow, r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        );

      case 'loss-run':
        return (
          <div className="space-y-4">
            <h2 className="text-lg font-medium text-gray-900">Loss Incurred</h2>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={lossRunData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis
                  dataKey="year"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#6B7280', fontSize: 12 }}
                />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#6B7280', fontSize: 12 }}
                  tickFormatter={(value) => formatYAxisValue(value, 'currency-k')}
                  domain={[0, 50000]}
                />
                <Tooltip content={<LossRunTooltip />} />
                <Legend
                  verticalAlign="bottom"
                  height={36}
                  formatter={(value) => {
                    if (value === 'solana') return 'Solana Apartments';
                    if (value === 'bend') return 'Bend Apartments';
                    if (value === 'retreat') return 'Retreat Apartments';
                    return value;
                  }}
                />
                <Bar dataKey="solana" fill={colors.green} radius={[4, 4, 0, 0]} />
                <Bar dataKey="bend" fill={colors.blue} radius={[4, 4, 0, 0]} />
                <Bar dataKey="retreat" fill={colors.yellow} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        );

      default:
        return null;
    }
  };

  // Determine which filters to show based on active tab
  const showPropertyFilter = activeTab === 'premium-unit-trends';
  const showAllFilter = activeTab !== 'premium-unit-trends';

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold text-gray-900">Analytics</h1>
        <div className="flex items-center gap-3">
          <button className="p-2 text-gray-400 hover:text-gray-600">
            <Bell className="h-5 w-5" />
          </button>
          <Button variant="ghost" size="sm" leftIcon={<Upload className="h-4 w-4" />}>
            Upload Document
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <div className="flex gap-1 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                'px-4 py-2.5 text-sm font-medium whitespace-nowrap transition-colors rounded-t-lg',
                activeTab === tab.id
                  ? 'bg-white text-gray-900 border border-gray-200 border-b-white -mb-px'
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
              )}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Chart Area */}
      <div className="flex-1 bg-white rounded-xl border border-gray-200 p-6">
        {/* Filters */}
        <div className="flex items-center justify-end gap-3 mb-6">
          {showPropertyFilter && (
            <Dropdown
              value={propertyFilter}
              options={propertyOptions}
              onChange={setPropertyFilter}
            />
          )}
          {showAllFilter && (
            <Dropdown
              value="all"
              options={[{ value: 'all', label: 'All' }]}
              onChange={() => {}}
            />
          )}
          <Dropdown
            value={timeRange}
            options={activeTab === 'loss-run'
              ? [{ value: 'last-5-years', label: 'Last 5 Years' }, ...timeRangeOptions.filter(o => o.value !== 'last-5-years')]
              : timeRangeOptions
            }
            onChange={setTimeRange}
          />
          <Button variant="ghost" size="sm" leftIcon={<Upload className="h-4 w-4" />}>
            Export
          </Button>
        </div>

        {/* Chart */}
        {renderChart()}

        {/* Info note for Premium Trends */}
        {activeTab === 'premium-unit-trends' && (
          <div className="mt-6 flex items-center justify-center gap-2 text-sm text-gray-500">
            <Info className="h-4 w-4" />
            <span>The comparable set is from similar vintage and sized properties within ~20 miles.</span>
          </div>
        )}
      </div>
    </div>
  );
}
