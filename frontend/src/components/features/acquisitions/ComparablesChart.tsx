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
import type { ComparableProperty } from '@/lib/api/client';

interface ComparablesChartProps {
  comparables: ComparableProperty[];
}

interface ChartDataPoint {
  x: number;
  y: number;
  name: string;
  address: string;
  score: number;
}

export function ComparablesChart({ comparables }: ComparablesChartProps) {
  // Transform data for chart
  const chartData: ChartDataPoint[] = comparables.map((comp, index) => ({
    x: index,
    y: comp.premium_per_unit,
    name: comp.name,
    address: comp.address,
    score: comp.similarity_score,
  }));

  const CustomTooltip = ({
    active,
    payload,
  }: {
    active?: boolean;
    payload?: Array<{ payload: ChartDataPoint }>;
  }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3 max-w-xs">
          <p className="font-medium text-gray-900 text-sm">{data.name}</p>
          <p className="text-xs text-gray-500">{data.address}</p>
          <p className="text-sm text-teal-600 mt-1">
            Premium/Unit: ${data.y.toLocaleString()}
          </p>
          <p className="text-xs text-gray-400 mt-1">
            Similarity: {data.score}%
          </p>
        </div>
      );
    }
    return null;
  };

  if (chartData.length === 0) {
    return (
      <div className="h-48 bg-gray-50 rounded-lg flex items-center justify-center">
        <span className="text-gray-400 text-sm">
          No comparable data available
        </span>
      </div>
    );
  }

  // Calculate domain for Y axis
  const yValues = chartData.map((d) => d.y);
  const minY = Math.min(...yValues) * 0.9;
  const maxY = Math.max(...yValues) * 1.1;

  return (
    <ResponsiveContainer width="100%" height={200}>
      <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 60 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
        <XAxis
          dataKey="x"
          type="number"
          domain={[-0.5, chartData.length - 0.5]}
          axisLine={false}
          tickLine={false}
          tick={{ fill: '#6B7280', fontSize: 12 }}
          tickFormatter={(value) => {
            const months = ['Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
            return months[value % months.length] || '';
          }}
        />
        <YAxis
          dataKey="y"
          type="number"
          domain={[minY, maxY]}
          axisLine={false}
          tickLine={false}
          tick={{ fill: '#6B7280', fontSize: 12 }}
          tickFormatter={(value) => `$${(value / 1000).toFixed(0)}K`}
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
