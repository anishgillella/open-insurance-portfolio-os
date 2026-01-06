'use client';

import { ResponsiveScatterPlot } from '@nivo/scatterplot';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { cn, getScoreColor, formatCurrency } from '@/lib/utils';
import type { Property } from '@/lib/api';

interface PortfolioBubbleChartProps {
  properties: Property[];
  className?: string;
  height?: number;
}

// Store property lookup for tooltip/click handlers
const propertyLookup = new Map<string, Property>();

export function PortfolioBubbleChart({
  properties,
  className,
  height = 400,
}: PortfolioBubbleChartProps) {
  const router = useRouter();

  // Build lookup table
  properties.forEach((p) => propertyLookup.set(p.id, p));

  // Transform data for scatter plot (keep it simple for types)
  const data = [
    {
      id: 'properties',
      data: properties.map((p) => ({
        x: Number(p.total_premium) || 0,
        y: p.health_score,
        propertyId: p.id,
      })),
    },
  ];

  // Calculate axis domains
  const maxPremium = Math.max(...properties.map((p) => Number(p.total_premium) || 0)) * 1.1;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className={cn('w-full', className)}
      style={{ height }}
    >
      <ResponsiveScatterPlot
        data={data}
        margin={{ top: 20, right: 20, bottom: 60, left: 80 }}
        xScale={{ type: 'linear', min: 0, max: maxPremium }}
        xFormat={(value) => formatCurrency(value as number)}
        yScale={{ type: 'linear', min: 0, max: 100 }}
        yFormat={(value) => `${value}`}
        blendMode="multiply"
        nodeSize={20}
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        colors={(node: any) => {
          const prop = propertyLookup.get(node.data?.propertyId);
          return prop ? getScoreColor(prop.health_score) : '#888888';
        }}
        axisTop={null}
        axisRight={null}
        axisBottom={{
          tickSize: 5,
          tickPadding: 5,
          tickRotation: 0,
          legend: 'Annual Premium ($)',
          legendPosition: 'middle',
          legendOffset: 46,
          format: (value) => {
            const v = value as number;
            if (v >= 1000000) return `${(v / 1000000).toFixed(0)}M`;
            if (v >= 1000) return `${(v / 1000).toFixed(0)}K`;
            return `${v}`;
          },
        }}
        axisLeft={{
          tickSize: 5,
          tickPadding: 5,
          tickRotation: 0,
          legend: 'Health Score',
          legendPosition: 'middle',
          legendOffset: -60,
        }}
        enableGridX={true}
        enableGridY={true}
        useMesh={true}
        motionConfig="gentle"
        onClick={(node) => {
          const propId = (node.data as { propertyId: string }).propertyId;
          router.push(`/properties/${propId}`);
        }}
        tooltip={({ node }) => {
          const propId = (node.data as { propertyId: string }).propertyId;
          const prop = propertyLookup.get(propId);
          if (!prop) return null;

          return (
            <div className="bg-gray-900 rounded-lg shadow-lg border border-gray-700 p-3 min-w-[200px]">
              <div className="font-semibold text-white mb-2">
                {prop.name}
              </div>
              <div className="space-y-1.5 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Premium:</span>
                  <span className="font-medium text-white">
                    {formatCurrency(Number(prop.total_premium) || 0)}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Health Score:</span>
                  <span
                    className="font-bold text-lg"
                    style={{ color: getScoreColor(prop.health_score) }}
                  >
                    {prop.health_score}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">TIV:</span>
                  <span className="font-medium text-white">
                    {formatCurrency(Number(prop.total_insured_value) || 0)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Location:</span>
                  <span className="text-gray-300">
                    {prop.address.city}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Expires in:</span>
                  <span
                    className={cn(
                      'font-medium',
                      (prop.days_until_expiration || 999) <= 30
                        ? 'text-red-400'
                        : (prop.days_until_expiration || 999) <= 60
                        ? 'text-amber-400'
                        : 'text-white'
                    )}
                  >
                    {prop.days_until_expiration || 'N/A'} days
                  </span>
                </div>
              </div>
              <div className="mt-2 pt-2 border-t border-gray-700 text-xs text-blue-400">
                Click to view details
              </div>
            </div>
          );
        }}
        theme={{
          background: 'transparent',
          grid: {
            line: {
              stroke: 'var(--color-border-subtle)',
              strokeWidth: 1,
            },
          },
          axis: {
            domain: {
              line: {
                stroke: 'var(--color-border-default)',
                strokeWidth: 1,
              },
            },
            ticks: {
              line: {
                stroke: 'var(--color-border-subtle)',
                strokeWidth: 1,
              },
              text: {
                fill: 'var(--color-text-muted)',
                fontSize: 11,
              },
            },
            legend: {
              text: {
                fill: 'var(--color-text-secondary)',
                fontSize: 12,
                fontWeight: 500,
              },
            },
          },
          tooltip: {
            container: {
              background: 'transparent',
              boxShadow: 'none',
              padding: 0,
            },
          },
        }}
      />
    </motion.div>
  );
}
