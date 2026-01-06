import dynamic from 'next/dynamic';
import { Loader2 } from 'lucide-react';

export { ComponentBreakdown } from './ComponentBreakdown';
export { RecommendationList } from './RecommendationList';

// Lazy-load ScoreHistory which uses heavy recharts library
export const ScoreHistory = dynamic(
  () => import('./ScoreHistory').then((mod) => ({ default: mod.ScoreHistory })),
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-[300px] flex items-center justify-center bg-[var(--color-surface-sunken)] rounded-lg">
        <Loader2 className="h-6 w-6 text-[var(--color-primary-500)] animate-spin" />
      </div>
    ),
  }
);
