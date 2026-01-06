'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Building,
  Star,
  TrendingUp,
  TrendingDown,
  Loader2,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Clock,
  AlertTriangle,
  Newspaper,
  Award,
  Search,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button, Card, Badge } from '@/components/primitives';
import { enrichmentApi, type CarrierResearchResponse } from '@/lib/api';

interface CarrierResearchCardProps {
  carrierName?: string;
  propertyType?: string;
  className?: string;
  onCarrierSelect?: (carrier: string) => void;
}

const getSentimentIcon = (sentiment: string) => {
  switch (sentiment.toLowerCase()) {
    case 'positive':
      return <TrendingUp className="h-3 w-3 text-[var(--color-success-500)]" />;
    case 'negative':
      return <TrendingDown className="h-3 w-3 text-[var(--color-critical-500)]" />;
    default:
      return null;
  }
};

const getAppetiteVariant = (appetite: string): 'success' | 'warning' | 'critical' | 'neutral' => {
  switch (appetite.toLowerCase()) {
    case 'strong':
    case 'expanding':
      return 'success';
    case 'moderate':
    case 'stable':
      return 'neutral';
    case 'selective':
    case 'contracting':
      return 'warning';
    case 'limited':
    case 'exiting':
      return 'critical';
    default:
      return 'neutral';
  }
};

export function CarrierResearchCard({
  carrierName: initialCarrier,
  propertyType,
  className,
  onCarrierSelect,
}: CarrierResearchCardProps) {
  const [carrierName, setCarrierName] = useState(initialCarrier || '');
  const [searchInput, setSearchInput] = useState('');
  const [carrierData, setCarrierData] = useState<CarrierResearchResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);

  const fetchCarrierData = async (name?: string) => {
    const searchName = name || carrierName || searchInput;
    if (!searchName.trim()) return;

    setIsLoading(true);
    setError(null);
    setCarrierName(searchName);
    try {
      const data = await enrichmentApi.researchCarrier(searchName, propertyType);
      setCarrierData(data);
      setIsExpanded(true);
      onCarrierSelect?.(searchName);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch carrier data');
    } finally {
      setIsLoading(false);
    }
  };

  if (!carrierData && !isLoading && !carrierName) {
    return (
      <Card padding="lg" className={className}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">
            Carrier Research
          </h2>
          <Badge variant="info">AI-Powered</Badge>
        </div>
        <p className="text-sm text-[var(--color-text-secondary)] mb-4">
          Research carrier financial strength, ratings, market appetite, and recent news.
        </p>
        <div className="flex gap-2">
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Enter carrier name..."
            className="flex-1 px-3 py-2 rounded-lg border border-[var(--color-border-default)] bg-[var(--color-surface)] text-[var(--color-text-primary)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-primary-500)]"
            onKeyDown={(e) => e.key === 'Enter' && fetchCarrierData(searchInput)}
          />
          <Button
            variant="primary"
            onClick={() => fetchCarrierData(searchInput)}
            disabled={isLoading || !searchInput.trim()}
            leftIcon={isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
          >
            Research
          </Button>
        </div>
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
          <Button variant="secondary" onClick={() => fetchCarrierData()} className="mt-4">
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
          <p className="text-[var(--color-text-primary)] font-medium">Researching {carrierName}</p>
          <p className="text-sm text-[var(--color-text-muted)] mt-1">
            Analyzing ratings, financials, and market position...
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
          <Building className="h-5 w-5 text-[var(--color-primary-500)]" />
          <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">
            {carrierData?.carrier_name}
          </h2>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </Button>
      </div>

      {/* Ratings Summary */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        <div className="text-center p-3 rounded-lg bg-[var(--color-surface-sunken)]">
          <Award className="h-5 w-5 mx-auto mb-1 text-[var(--color-warning-500)]" />
          <p className="text-xs text-[var(--color-text-muted)]">A.M. Best</p>
          <p className="text-lg font-bold text-[var(--color-text-primary)]">
            {carrierData?.ratings.am_best_rating || 'N/A'}
          </p>
          {carrierData?.ratings.am_best_outlook && (
            <p className="text-xs text-[var(--color-text-muted)]">
              {carrierData.ratings.am_best_outlook}
            </p>
          )}
        </div>
        <div className="text-center p-3 rounded-lg bg-[var(--color-surface-sunken)]">
          <Star className="h-5 w-5 mx-auto mb-1 text-[var(--color-info-500)]" />
          <p className="text-xs text-[var(--color-text-muted)]">Financial</p>
          <p className="text-sm font-bold text-[var(--color-text-primary)]">
            {carrierData?.financial_strength || 'N/A'}
          </p>
        </div>
        <div className="text-center p-3 rounded-lg bg-[var(--color-surface-sunken)]">
          <TrendingUp className="h-5 w-5 mx-auto mb-1 text-[var(--color-success-500)]" />
          <p className="text-xs text-[var(--color-text-muted)]">CRE Appetite</p>
          <Badge variant={getAppetiteVariant(carrierData?.commercial_property_appetite || '')} className="mt-1">
            {carrierData?.commercial_property_appetite || 'Unknown'}
          </Badge>
        </div>
      </div>

      <AnimatePresence>
        {isExpanded && carrierData && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden"
          >
            {/* Financial Summary */}
            {carrierData.financial_summary && (
              <div className="mb-4 p-3 rounded-lg bg-[var(--color-surface-sunken)]">
                <p className="text-sm text-[var(--color-text-primary)]">{carrierData.financial_summary}</p>
              </div>
            )}

            {/* Market Position */}
            {carrierData.market_position && (
              <div className="mb-4">
                <h3 className="text-sm font-medium text-[var(--color-text-primary)] mb-2">Market Position</h3>
                <p className="text-sm text-[var(--color-text-secondary)]">{carrierData.market_position}</p>
              </div>
            )}

            {/* Specialties */}
            {carrierData.specialty_areas.length > 0 && (
              <div className="mb-4">
                <h3 className="text-sm font-medium text-[var(--color-text-primary)] mb-2">Specialty Areas</h3>
                <div className="flex flex-wrap gap-2">
                  {carrierData.specialty_areas.map((specialty, idx) => (
                    <Badge key={idx} variant="secondary">
                      {specialty.line_of_business}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Appetite Notes */}
            {carrierData.appetite_notes && (
              <div className="mb-4 p-3 rounded-lg bg-[var(--color-info-50)] dark:bg-[var(--color-info-500)]/10 border border-[var(--color-info-200)] dark:border-[var(--color-info-500)]/20">
                <p className="text-sm text-[var(--color-info-700)] dark:text-[var(--color-info-300)]">
                  {carrierData.appetite_notes}
                </p>
              </div>
            )}

            {/* Recent News */}
            {carrierData.recent_news.length > 0 && (
              <div className="mb-4">
                <h3 className="text-sm font-medium text-[var(--color-text-primary)] mb-2 flex items-center gap-2">
                  <Newspaper className="h-4 w-4" />
                  Recent News
                </h3>
                <div className="space-y-2">
                  {carrierData.recent_news.slice(0, 3).map((news, idx) => (
                    <div key={idx} className="p-2 rounded-lg border border-[var(--color-border-subtle)]">
                      <div className="flex items-start gap-2">
                        {getSentimentIcon(news.sentiment)}
                        <div>
                          <p className="text-sm font-medium text-[var(--color-text-primary)]">{news.headline}</p>
                          {news.summary && (
                            <p className="text-xs text-[var(--color-text-muted)] mt-0.5 line-clamp-2">
                              {news.summary}
                            </p>
                          )}
                          <p className="text-xs text-[var(--color-text-muted)] mt-1">
                            {news.date} {news.source && `• ${news.source}`}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                {carrierData.news_summary && (
                  <p className="text-sm text-[var(--color-text-secondary)] mt-2">
                    {carrierData.news_summary}
                  </p>
                )}
              </div>
            )}

            {/* Concerns */}
            {carrierData.concerns.length > 0 && (
              <div className="p-3 rounded-lg bg-[var(--color-warning-50)] dark:bg-[var(--color-warning-500)]/10 border border-[var(--color-warning-200)] dark:border-[var(--color-warning-500)]/20 mb-4">
                <h3 className="text-sm font-medium text-[var(--color-warning-600)] dark:text-[var(--color-warning-400)] mb-2">
                  Concerns to Note
                </h3>
                <ul className="text-sm text-[var(--color-warning-700)] dark:text-[var(--color-warning-300)] space-y-1">
                  {carrierData.concerns.map((concern, idx) => (
                    <li key={idx}>• {concern}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Customer Experience */}
            {(carrierData.customer_satisfaction || carrierData.claims_reputation) && (
              <div className="grid grid-cols-2 gap-3 mb-4">
                {carrierData.customer_satisfaction && (
                  <div className="p-3 rounded-lg border border-[var(--color-border-subtle)]">
                    <p className="text-xs text-[var(--color-text-muted)] mb-1">Customer Satisfaction</p>
                    <p className="text-sm text-[var(--color-text-primary)]">{carrierData.customer_satisfaction}</p>
                  </div>
                )}
                {carrierData.claims_reputation && (
                  <div className="p-3 rounded-lg border border-[var(--color-border-subtle)]">
                    <p className="text-xs text-[var(--color-text-muted)] mb-1">Claims Reputation</p>
                    <p className="text-sm text-[var(--color-text-primary)]">{carrierData.claims_reputation}</p>
                  </div>
                )}
              </div>
            )}

            {/* Footer */}
            <div className="flex items-center justify-between mt-4 pt-4 border-t border-[var(--color-border-subtle)]">
              <div className="flex items-center gap-4 text-xs text-[var(--color-text-muted)]">
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {new Date(carrierData.research_date).toLocaleDateString()}
                </span>
                <span>
                  {(carrierData.total_latency_ms / 1000).toFixed(1)}s research
                </span>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setCarrierData(null);
                    setCarrierName('');
                    setSearchInput('');
                  }}
                >
                  New Search
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => fetchCarrierData()}
                  disabled={isLoading}
                >
                  <RefreshCw className={cn('h-3 w-3 mr-1', isLoading && 'animate-spin')} />
                  Refresh
                </Button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </Card>
  );
}
