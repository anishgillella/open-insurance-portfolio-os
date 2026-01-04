'use client';

import { motion } from 'framer-motion';
import { ArrowRight, Sparkles, ChevronRight } from 'lucide-react';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/primitives';
import { staggerContainer, staggerItem } from '@/lib/motion/variants';
import type { Recommendation } from '@/lib/mock-data';

interface RecommendationListProps {
  recommendations: Recommendation[];
  className?: string;
  showAll?: boolean;
}

const priorityConfig = {
  high: {
    variant: 'critical' as const,
    bgColor: 'bg-[var(--color-critical-50)] dark:bg-[var(--color-critical-500)]/10',
    borderColor: 'border-[var(--color-critical-200)] dark:border-[var(--color-critical-500)]/20',
    iconColor: 'text-[var(--color-critical-500)]',
  },
  medium: {
    variant: 'warning' as const,
    bgColor: 'bg-[var(--color-warning-50)] dark:bg-[var(--color-warning-500)]/10',
    borderColor: 'border-[var(--color-warning-200)] dark:border-[var(--color-warning-500)]/20',
    iconColor: 'text-[var(--color-warning-500)]',
  },
  low: {
    variant: 'info' as const,
    bgColor: 'bg-[var(--color-info-50)] dark:bg-[var(--color-info-500)]/10',
    borderColor: 'border-[var(--color-info-200)] dark:border-[var(--color-info-500)]/20',
    iconColor: 'text-[var(--color-info-500)]',
  },
};

function RecommendationCard({
  recommendation,
  index,
}: {
  recommendation: Recommendation;
  index: number;
}) {
  const config = priorityConfig[recommendation.priority];

  const content = (
    <motion.div
      variants={staggerItem}
      whileHover={{ scale: 1.01, y: -2 }}
      transition={{ duration: 0.2 }}
      className={cn(
        'p-4 rounded-xl border cursor-pointer transition-shadow hover:shadow-[var(--shadow-elevation-2)]',
        config.bgColor,
        config.borderColor
      )}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3 flex-1">
          <div
            className={cn(
              'w-8 h-8 rounded-lg flex items-center justify-center font-bold text-sm text-white',
              recommendation.priority === 'high'
                ? 'bg-[var(--color-critical-500)]'
                : recommendation.priority === 'medium'
                ? 'bg-[var(--color-warning-500)]'
                : 'bg-[var(--color-info-500)]'
            )}
          >
            {index + 1}
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <Badge variant={config.variant}>{recommendation.priority}</Badge>
              <span className="text-xs text-[var(--color-text-muted)]">
                {recommendation.category}
              </span>
            </div>
            <h3 className="font-medium text-[var(--color-text-primary)] mb-1">
              {recommendation.title}
            </h3>
            <p className="text-sm text-[var(--color-text-secondary)]">
              {recommendation.description}
            </p>
          </div>
        </div>
        <div className="flex flex-col items-end gap-2">
          <div className="flex items-center gap-1 text-[var(--color-success-600)] dark:text-[var(--color-success-400)]">
            <Sparkles className="h-4 w-4" />
            <span className="font-semibold">+{recommendation.points} pts</span>
          </div>
          <ChevronRight className="h-5 w-5 text-[var(--color-text-muted)]" />
        </div>
      </div>
    </motion.div>
  );

  if (recommendation.actionUrl) {
    return <Link href={recommendation.actionUrl}>{content}</Link>;
  }

  return content;
}

export function RecommendationList({
  recommendations,
  className,
  showAll = false,
}: RecommendationListProps) {
  const displayRecommendations = showAll ? recommendations : recommendations.slice(0, 5);
  const totalPoints = recommendations.reduce((sum, r) => sum + r.points, 0);

  return (
    <div className={cn('space-y-4', className)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">
            Recommendations
          </h2>
          <Badge variant="success">
            +{totalPoints} pts available
          </Badge>
        </div>
        {!showAll && recommendations.length > 5 && (
          <Link
            href="#"
            className="flex items-center gap-1 text-sm text-[var(--color-primary-500)] hover:text-[var(--color-primary-600)] font-medium"
          >
            View all
            <ArrowRight className="h-4 w-4" />
          </Link>
        )}
      </div>

      <motion.div
        variants={staggerContainer}
        initial="initial"
        animate="animate"
        className="space-y-3"
      >
        {displayRecommendations.map((recommendation, index) => (
          <RecommendationCard
            key={recommendation.id}
            recommendation={recommendation}
            index={index}
          />
        ))}
      </motion.div>

      {displayRecommendations.length === 0 && (
        <div className="text-center py-8 text-[var(--color-text-muted)]">
          <Sparkles className="h-12 w-12 mx-auto mb-3 opacity-50" />
          <p>No recommendations at this time. Great job!</p>
        </div>
      )}
    </div>
  );
}
