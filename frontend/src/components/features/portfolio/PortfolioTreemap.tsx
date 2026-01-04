'use client';

import { ResponsiveTreeMap } from '@nivo/treemap';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { cn, getScoreColor, formatCurrency } from '@/lib/utils';
import type { Property } from '@/lib/mock-data';

interface PortfolioTreemapProps {
  properties: Property[];
  className?: string;
  height?: number;
}

export function PortfolioTreemap({
  properties,
  className,
  height = 400,
}: PortfolioTreemapProps) {
  const router = useRouter();

  const data = {
    name: 'Portfolio',
    children: properties.map((p) => ({
      id: p.id,
      name: p.name,
      value: p.total_insured_value,
      healthScore: p.health_score,
      premium: p.total_premium,
      city: p.address.city,
      color: getScoreColor(p.health_score),
    })),
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className={cn('w-full', className)}
      style={{ height }}
    >
      <ResponsiveTreeMap
        data={data}
        identity="name"
        value="value"
        valueFormat={(value) => formatCurrency(value)}
        tile="squarify"
        leavesOnly={true}
        innerPadding={3}
        outerPadding={3}
        margin={{ top: 10, right: 10, bottom: 10, left: 10 }}
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        colors={(node: any) => node.data?.color || '#888888'}
        borderWidth={2}
        borderColor={{
          from: 'color',
          modifiers: [['darker', 0.3]],
        }}
        labelSkipSize={50}
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        label={(node: any) => node.data?.name || ''}
        labelTextColor={{
          from: 'color',
          modifiers: [['darker', 2]],
        }}
        parentLabelPosition="left"
        parentLabelTextColor={{
          from: 'color',
          modifiers: [['darker', 2]],
        }}
        enableParentLabel={false}
        motionConfig="gentle"
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        onClick={(node: any) => {
          if (node.data?.id) {
            router.push(`/properties/${node.data.id}`);
          }
        }}
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        tooltip={({ node }: any) => (
          <div className="bg-white dark:bg-gray-900 rounded-lg shadow-lg border border-[var(--color-border-subtle)] p-3 min-w-[180px]">
            <div className="font-semibold text-[var(--color-text-primary)] mb-2">
              {node.data?.name}
            </div>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-[var(--color-text-muted)]">TIV:</span>
                <span className="font-medium text-[var(--color-text-primary)]">
                  {formatCurrency(node.value)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--color-text-muted)]">Premium:</span>
                <span className="font-medium text-[var(--color-text-primary)]">
                  {formatCurrency(node.data?.premium || 0)}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-[var(--color-text-muted)]">Health:</span>
                <span
                  className="font-bold"
                  style={{ color: node.data?.color }}
                >
                  {node.data?.healthScore}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--color-text-muted)]">Location:</span>
                <span className="text-[var(--color-text-secondary)]">{node.data?.city}</span>
              </div>
            </div>
            <div className="mt-2 pt-2 border-t border-[var(--color-border-subtle)] text-xs text-[var(--color-primary-500)]">
              Click to view details
            </div>
          </div>
        )}
        theme={{
          labels: {
            text: {
              fontSize: 12,
              fontWeight: 600,
              fill: '#ffffff',
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
