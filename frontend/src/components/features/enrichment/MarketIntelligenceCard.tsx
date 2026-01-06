'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Loader2,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Clock,
  Building2,
  AlertTriangle,
  Lightbulb,
  BarChart3,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button, Card, Badge } from '@/components/primitives';
import { enrichmentApi, type MarketIntelligenceResponse } from '@/lib/api';

interface MarketIntelligenceCardProps {
  propertyId: string;
  className?: string;
}

const getTrendIcon = (direction: string) => {
  switch (direction.toLowerCase()) {
    case 'increasing':
      return <TrendingUp className="h-5 w-5 text-[var(--color-critical-500)]" />;
    case 'decreasing':
      return <TrendingDown className="h-5 w-5 text-[var(--color-success-500)]" />;
    default:
      return <Minus className="h-5 w-5 text-[var(--color-text-muted)]" />;
  }
};

const getTrendColor = (direction: string) => {
  switch (direction.toLowerCase()) {
    case 'increasing':
      return 'text-[var(--color-critical-500)]';
    case 'decreasing':
      return 'text-[var(--color-success-500)]';
    default:
      return 'text-[var(--color-text-muted)]';
  }
};

const getAppetiteVariant = (appetite: string): 'success' | 'warning' | 'critical' | 'neutral' => {
  switch (appetite.toLowerCase()) {
    case 'expanding':
      return 'success';
    case 'stable':
      return 'neutral';
    case 'contracting':
      return 'warning';
    case 'exiting':
      return 'critical';
    default:
      return 'neutral';
  }
};

export function MarketIntelligenceCard({ propertyId, className }: MarketIntelligenceCardProps) {
  const [marketData, setMarketData] = useState<MarketIntelligenceResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);

  const fetchMarketData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await enrichmentApi.getMarketIntelligence(propertyId);
      setMarketData(data);
      setIsExpanded(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch market data');
    } finally {
      setIsLoading(false);
    }
  };

  if (!marketData && !isLoading) {
    return (
      <Card padding="lg" className={className}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">
            Market Intelligence
          </h2>
          <Badge variant="info">Live Research</Badge>
        </div>
        <p className="text-sm text-[var(--color-text-secondary)] mb-4">
          Get real-time market conditions including rate trends, carrier appetite, and pricing forecasts for your renewal.
        </p>
        <Button
          variant="primary"
          onClick={fetchMarketData}
          disabled={isLoading}
          leftIcon={isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <BarChart3 className="h-4 w-4" />}
          className="w-full"
        >
          {isLoading ? 'Researching...' : 'Get Market Intelligence'}
        </Button>
        <p className="text-xs text-[var(--color-text-muted)] mt-2 text-center">
          Takes 30-120 seconds to complete
        </p>
      </Card>
    );
  }

  if (error) {
    return (
      <Card padding="lg" className={className}>
        <div className="text-center py-4">
          <AlertTriangle className="h-8 w-8 text-[var(--color-critical-500)] mx-auto mb-2" />
          <p className="text-[var(--color-text-primary)] font-medium">Research Failed</p>
          <p className="text-sm text-[var(--color-text-muted)] mt-1">{error}</p>
          <Button variant="secondary" onClick={fetchMarketData} className="mt-4">
            <RefreshCw className="h-4 w-4 mr-2" />
            Try Again
          </Button>
        </div>
      </Card>
    );
  }

  if (isLoading) {
    return (
      <Card padding="lg" className={className}>
        <div className="text-center py-8">
          <Loader2 className="h-8 w-8 text-[var(--color-primary-500)] animate-spin mx-auto mb-4" />
          <p className="text-[var(--color-text-primary)] font-medium">Researching Market Conditions</p>
          <p className="text-sm text-[var(--color-text-muted)] mt-1">
            Analyzing rate trends, carrier appetite, and market forecasts...
          </p>
        </div>
      </Card>
    );
  }

  return (
    <Card padding="lg" className={className}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">
            Market Intelligence
          </h2>
          <Badge variant="secondary">
            {marketData?.property_type} • {marketData?.state}
          </Badge>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </Button>
      </div>

      {/* Rate Trend Summary */}
      <div className="flex items-center gap-4 p-4 rounded-lg bg-[var(--color-surface-sunken)] mb-4">
        {getTrendIcon(marketData?.rate_trend.direction || 'stable')}
        <div className="flex-1">
          <p className="text-sm text-[var(--color-text-muted)]">Rate Trend</p>
          <p className={cn('text-2xl font-bold', getTrendColor(marketData?.rate_trend.direction || 'stable'))}>
            {marketData?.rate_trend.rate_change_pct !== null
              ? `${marketData.rate_trend.rate_change_pct > 0 ? '+' : ''}${marketData.rate_trend.rate_change_pct}%`
              : marketData?.rate_trend.rate_change_range || 'Unknown'}
          </p>
        </div>
        <div className="text-right">
          <p className="text-sm text-[var(--color-text-muted)]">Confidence</p>
          <Badge variant={
            marketData?.rate_trend.confidence === 'high' ? 'success' :
            marketData?.rate_trend.confidence === 'medium' ? 'warning' : 'neutral'
          }>
            {marketData?.rate_trend.confidence || 'Unknown'}
          </Badge>
        </div>
      </div>

      <AnimatePresence>
        {isExpanded && marketData && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden"
          >
            {/* Rate Trend Reasoning */}
            {marketData.rate_trend_reasoning && (
              <div className="mb-4 p-3 rounded-lg bg-[var(--color-surface-sunken)]">
                <p className="text-sm text-[var(--color-text-primary)]">{marketData.rate_trend_reasoning}</p>
              </div>
            )}

            {/* Key Factors */}
            {marketData.key_factors.length > 0 && (
              <div className="mb-4">
                <h3 className="text-sm font-medium text-[var(--color-text-primary)] mb-2 flex items-center gap-2">
                  <Lightbulb className="h-4 w-4 text-[var(--color-warning-500)]" />
                  Key Factors Driving Rates
                </h3>
                <ul className="space-y-1">
                  {marketData.key_factors.map((factor, idx) => (
                    <li key={idx} className="text-sm text-[var(--color-text-secondary)] flex items-start gap-2">
                      <span className="text-[var(--color-primary-500)]">•</span>
                      {factor}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Carrier Appetite */}
            {marketData.carrier_appetite.length > 0 && (
              <div className="mb-4">
                <h3 className="text-sm font-medium text-[var(--color-text-primary)] mb-2 flex items-center gap-2">
                  <Building2 className="h-4 w-4 text-[var(--color-info-500)]" />
                  Carrier Appetite
                </h3>
                <div className="grid grid-cols-2 gap-2">
                  {marketData.carrier_appetite.slice(0, 6).map((carrier, idx) => (
                    <div key={idx} className="p-2 rounded-lg border border-[var(--color-border-subtle)]">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-[var(--color-text-primary)] truncate">
                          {carrier.carrier_name}
                        </span>
                        <Badge variant={getAppetiteVariant(carrier.appetite)} className="text-[10px]">
                          {carrier.appetite}
                        </Badge>
                      </div>
                      {carrier.notes && (
                        <p className="text-xs text-[var(--color-text-muted)] mt-1 line-clamp-1">
                          {carrier.notes}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
                {marketData.carrier_summary && (
                  <p className="text-sm text-[var(--color-text-secondary)] mt-2">
                    {marketData.carrier_summary}
                  </p>
                )}
              </div>
            )}

            {/* Forecasts */}
            <div className="grid grid-cols-2 gap-3 mb-4">
              {marketData.forecast_6mo && (
                <div className="p-3 rounded-lg border border-[var(--color-border-subtle)]">
                  <p className="text-xs text-[var(--color-text-muted)] mb-1">6-Month Forecast</p>
                  <p className="text-sm text-[var(--color-text-primary)]">{marketData.forecast_6mo}</p>
                </div>
              )}
              {marketData.forecast_12mo && (
                <div className="p-3 rounded-lg border border-[var(--color-border-subtle)]">
                  <p className="text-xs text-[var(--color-text-muted)] mb-1">12-Month Forecast</p>
                  <p className="text-sm text-[var(--color-text-primary)]">{marketData.forecast_12mo}</p>
                </div>
              )}
            </div>

            {/* Benchmarks */}
            {(marketData.premium_benchmark || marketData.rate_per_sqft) && (
              <div className="p-3 rounded-lg bg-[var(--color-info-50)] dark:bg-[var(--color-info-500)]/10 border border-[var(--color-info-200)] dark:border-[var(--color-info-500)]/20 mb-4">
                <h3 className="text-sm font-medium text-[var(--color-info-600)] dark:text-[var(--color-info-400)] mb-2">
                  Market Benchmarks
                </h3>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  {marketData.premium_benchmark && (
                    <p className="text-[var(--color-info-700)] dark:text-[var(--color-info-300)]">
                      Premium: <span className="font-medium">{marketData.premium_benchmark}</span>
                    </p>
                  )}
                  {marketData.rate_per_sqft && (
                    <p className="text-[var(--color-info-700)] dark:text-[var(--color-info-300)]">
                      Rate/sqft: <span className="font-medium">${marketData.rate_per_sqft.toFixed(2)}</span>
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* Regulatory Changes */}
            {marketData.regulatory_changes.length > 0 && (
              <div className="p-3 rounded-lg bg-[var(--color-warning-50)] dark:bg-[var(--color-warning-500)]/10 border border-[var(--color-warning-200)] dark:border-[var(--color-warning-500)]/20 mb-4">
                <h3 className="text-sm font-medium text-[var(--color-warning-600)] dark:text-[var(--color-warning-400)] mb-2">
                  Regulatory Changes
                </h3>
                <ul className="text-sm text-[var(--color-warning-700)] dark:text-[var(--color-warning-300)] space-y-1">
                  {marketData.regulatory_changes.map((change, idx) => (
                    <li key={idx}>• {change}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Footer */}
            <div className="flex items-center justify-between mt-4 pt-4 border-t border-[var(--color-border-subtle)]">
              <div className="flex items-center gap-4 text-xs text-[var(--color-text-muted)]">
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {new Date(marketData.research_date).toLocaleDateString()}
                </span>
                <span>
                  {(marketData.total_latency_ms / 1000).toFixed(1)}s research
                </span>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={fetchMarketData}
                disabled={isLoading}
              >
                <RefreshCw className={cn('h-3 w-3 mr-1', isLoading && 'animate-spin')} />
                Refresh
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </Card>
  );
}
