import dynamic from 'next/dynamic';
import { Loader2 } from 'lucide-react';

// Lazy-load heavy nivo chart components to improve initial page load time
export const PortfolioTreemap = dynamic(
  () => import('./PortfolioTreemap').then((mod) => ({ default: mod.PortfolioTreemap })),
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-[350px] flex items-center justify-center bg-[var(--color-surface-sunken)] rounded-lg">
        <Loader2 className="h-6 w-6 text-[var(--color-primary-500)] animate-spin" />
      </div>
    ),
  }
);

export const PortfolioBubbleChart = dynamic(
  () => import('./PortfolioBubbleChart').then((mod) => ({ default: mod.PortfolioBubbleChart })),
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-[350px] flex items-center justify-center bg-[var(--color-surface-sunken)] rounded-lg">
        <Loader2 className="h-6 w-6 text-[var(--color-primary-500)] animate-spin" />
      </div>
    ),
  }
);
