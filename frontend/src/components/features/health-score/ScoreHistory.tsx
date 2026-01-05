'use client';

import { motion } from 'framer-motion';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceDot,
} from 'recharts';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { cn, getScoreColor } from '@/lib/utils';
import type { ScoreHistoryPoint } from '@/lib/mock-data';

interface ScoreHistoryProps {
  history: ScoreHistoryPoint[];
  className?: string;
}

function CustomTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ value: number; payload: ScoreHistoryPoint }>;
  label?: string;
}) {
  if (!active || !payload?.length) return null;

  const data = payload[0].payload;
  const score = payload[0].value;
  const color = getScoreColor(score);

  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg shadow-lg border border-[var(--color-border-subtle)] p-3">
      <p className="text-sm text-[var(--color-text-muted)] mb-1">
        {new Date(data.date).toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
          year: 'numeric',
        })}
      </p>
      <p className="text-2xl font-bold" style={{ color }}>
        {score}
      </p>
      {/* Event info would go here if available in data model */}
    </div>
  );
}

export function ScoreHistory({ history, className }: ScoreHistoryProps) {
  if (history.length < 2) {
    return (
      <div className={cn('text-center py-8 text-[var(--color-text-muted)]', className)}>
        Not enough data to display history
      </div>
    );
  }

  const latestScore = history[history.length - 1].score;
  const previousScore = history[history.length - 2].score;
  const change = latestScore - previousScore;
  const firstScore = history[0].score;
  const totalChange = latestScore - firstScore;

  const color = getScoreColor(latestScore);

  // Format data for recharts
  const formattedData = history.map((point) => ({
    ...point,
    dateFormatted: new Date(point.date).toLocaleDateString('en-US', {
      month: 'short',
    }),
  }));

  return (
    <div className={cn('space-y-4', className)}>
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">
          Score History
        </h2>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-sm text-[var(--color-text-muted)]">30-day:</span>
            <div
              className={cn(
                'flex items-center gap-1 font-semibold',
                change > 0
                  ? 'text-[var(--color-success-500)]'
                  : change < 0
                  ? 'text-[var(--color-critical-500)]'
                  : 'text-[var(--color-text-muted)]'
              )}
            >
              {change > 0 ? (
                <TrendingUp className="h-4 w-4" />
              ) : change < 0 ? (
                <TrendingDown className="h-4 w-4" />
              ) : (
                <Minus className="h-4 w-4" />
              )}
              <span>{change > 0 ? '+' : ''}{change}</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-[var(--color-text-muted)]">Overall:</span>
            <div
              className={cn(
                'flex items-center gap-1 font-semibold',
                totalChange > 0
                  ? 'text-[var(--color-success-500)]'
                  : totalChange < 0
                  ? 'text-[var(--color-critical-500)]'
                  : 'text-[var(--color-text-muted)]'
              )}
            >
              {totalChange > 0 ? (
                <TrendingUp className="h-4 w-4" />
              ) : totalChange < 0 ? (
                <TrendingDown className="h-4 w-4" />
              ) : (
                <Minus className="h-4 w-4" />
              )}
              <span>{totalChange > 0 ? '+' : ''}{totalChange}</span>
            </div>
          </div>
        </div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="h-[300px] w-full"
      >
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={formattedData} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="scoreGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={color} stopOpacity={0.3} />
                <stop offset="95%" stopColor={color} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="var(--color-border-subtle)"
              vertical={false}
            />
            <XAxis
              dataKey="dateFormatted"
              stroke="var(--color-text-muted)"
              fontSize={12}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              domain={[0, 100]}
              stroke="var(--color-text-muted)"
              fontSize={12}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => `${value}`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Line
              type="monotone"
              dataKey="score"
              stroke={color}
              strokeWidth={3}
              dot={false}
              activeDot={{
                r: 6,
                fill: color,
                stroke: 'white',
                strokeWidth: 2,
              }}
            />
            {/* Events would be marked here if available in data model */}
          </LineChart>
        </ResponsiveContainer>
      </motion.div>

      {/* Events Legend would appear here if events were tracked in data model */}
    </div>
  );
}
