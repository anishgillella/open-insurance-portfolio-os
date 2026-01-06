'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Droplets,
  Flame,
  CloudLightning,
  Shield,
  AlertTriangle,
  Loader2,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  MapPin,
  Clock,
  ExternalLink,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button, Card, Badge } from '@/components/primitives';
import { enrichmentApi, type PropertyRiskResponse } from '@/lib/api';

interface PropertyRiskCardProps {
  propertyId: string;
  propertyAddress?: string;
  className?: string;
}

const getRiskColor = (level: string) => {
  switch (level.toLowerCase()) {
    case 'low':
      return 'text-[var(--color-success-500)]';
    case 'moderate':
    case 'medium':
      return 'text-[var(--color-warning-500)]';
    case 'high':
    case 'very high':
      return 'text-[var(--color-critical-500)]';
    default:
      return 'text-[var(--color-text-muted)]';
  }
};

const getRiskBadgeVariant = (level: string): 'success' | 'warning' | 'critical' | 'neutral' => {
  switch (level.toLowerCase()) {
    case 'low':
      return 'success';
    case 'moderate':
    case 'medium':
      return 'warning';
    case 'high':
    case 'very high':
      return 'critical';
    default:
      return 'neutral';
  }
};

export function PropertyRiskCard({ propertyId, propertyAddress, className }: PropertyRiskCardProps) {
  const [riskData, setRiskData] = useState<PropertyRiskResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);

  const fetchRiskData = async (updateProperty = false) => {
    console.log('[PropertyRiskCard] Starting risk analysis for property:', propertyId);
    setIsLoading(true);
    setError(null);
    try {
      console.log('[PropertyRiskCard] Calling enrichmentApi.enrichPropertyRisk...');
      const data = await enrichmentApi.enrichPropertyRisk(propertyId, updateProperty);
      console.log('[PropertyRiskCard] Received data:', data);
      setRiskData(data);
      setIsExpanded(true);
    } catch (err) {
      console.error('[PropertyRiskCard] Error:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch risk data');
    } finally {
      setIsLoading(false);
    }
  };

  if (!riskData && !isLoading) {
    return (
      <Card padding="lg" className={className}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">
            Property Risk Analysis
          </h2>
          <Badge variant="info">AI-Powered</Badge>
        </div>
        <p className="text-sm text-[var(--color-text-secondary)] mb-4">
          Get comprehensive risk data including flood zones, fire protection, weather exposure, and more using AI-powered web research.
        </p>
        <Button
          variant="primary"
          onClick={() => fetchRiskData(false)}
          disabled={isLoading}
          leftIcon={isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Shield className="h-4 w-4" />}
          className="w-full"
        >
          {isLoading ? 'Analyzing...' : 'Analyze Property Risk'}
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
          <p className="text-[var(--color-text-primary)] font-medium">Analysis Failed</p>
          <p className="text-sm text-[var(--color-text-muted)] mt-1">{error}</p>
          <Button variant="secondary" onClick={() => fetchRiskData(false)} className="mt-4">
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
          <p className="text-[var(--color-text-primary)] font-medium">Analyzing Property Risk</p>
          <p className="text-sm text-[var(--color-text-muted)] mt-1">
            Researching public records, FEMA data, and local sources...
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
            Property Risk Analysis
          </h2>
          {riskData?.overall_risk_score !== null && riskData?.overall_risk_score !== undefined && (
            <Badge variant={getRiskBadgeVariant(
              riskData.overall_risk_score <= 30 ? 'low' :
              riskData.overall_risk_score <= 60 ? 'moderate' : 'high'
            )}>
              Score: {riskData.overall_risk_score}/100
            </Badge>
          )}
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </Button>
      </div>

      {/* Summary Row */}
      <div className="grid grid-cols-4 gap-3 mb-4">
        <div className="text-center p-2 rounded-lg bg-[var(--color-surface-sunken)]">
          <Droplets className={cn('h-5 w-5 mx-auto mb-1', getRiskColor(riskData?.flood_risk.risk_level || 'unknown'))} />
          <p className="text-xs text-[var(--color-text-muted)]">Flood</p>
          <p className={cn('text-sm font-medium', getRiskColor(riskData?.flood_risk.risk_level || 'unknown'))}>
            {riskData?.flood_risk.risk_level || 'Unknown'}
          </p>
        </div>
        <div className="text-center p-2 rounded-lg bg-[var(--color-surface-sunken)]">
          <Flame className={cn('h-5 w-5 mx-auto mb-1', getRiskColor(
            riskData?.weather_risk.wildfire_risk || 'unknown'
          ))} />
          <p className="text-xs text-[var(--color-text-muted)]">Wildfire</p>
          <p className={cn('text-sm font-medium', getRiskColor(riskData?.weather_risk.wildfire_risk || 'unknown'))}>
            {riskData?.weather_risk.wildfire_risk || 'Unknown'}
          </p>
        </div>
        <div className="text-center p-2 rounded-lg bg-[var(--color-surface-sunken)]">
          <CloudLightning className={cn('h-5 w-5 mx-auto mb-1', getRiskColor(
            riskData?.weather_risk.hurricane_risk || 'unknown'
          ))} />
          <p className="text-xs text-[var(--color-text-muted)]">Hurricane</p>
          <p className={cn('text-sm font-medium', getRiskColor(riskData?.weather_risk.hurricane_risk || 'unknown'))}>
            {riskData?.weather_risk.hurricane_risk || 'Unknown'}
          </p>
        </div>
        <div className="text-center p-2 rounded-lg bg-[var(--color-surface-sunken)]">
          <Shield className={cn('h-5 w-5 mx-auto mb-1', getRiskColor(
            riskData?.crime_risk.risk_level || 'unknown'
          ))} />
          <p className="text-xs text-[var(--color-text-muted)]">Crime</p>
          <p className={cn('text-sm font-medium', getRiskColor(riskData?.crime_risk.risk_level || 'unknown'))}>
            {riskData?.crime_risk.risk_level || 'Unknown'}
          </p>
        </div>
      </div>

      <AnimatePresence>
        {isExpanded && riskData && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden"
          >
            {/* Risk Summary */}
            {riskData.risk_summary && (
              <div className="mb-4 p-3 rounded-lg bg-[var(--color-surface-sunken)]">
                <p className="text-sm text-[var(--color-text-primary)]">{riskData.risk_summary}</p>
              </div>
            )}

            {/* Detailed Risks */}
            <div className="space-y-3">
              {/* Flood Risk */}
              <div className="p-3 rounded-lg border border-[var(--color-border-subtle)]">
                <div className="flex items-center gap-2 mb-2">
                  <Droplets className="h-4 w-4 text-[var(--color-info-500)]" />
                  <span className="font-medium text-[var(--color-text-primary)]">Flood Risk</span>
                  <Badge variant={getRiskBadgeVariant(riskData.flood_risk.risk_level)} className="ml-auto">
                    {riskData.flood_risk.risk_level}
                  </Badge>
                </div>
                {riskData.flood_risk.zone && (
                  <p className="text-sm text-[var(--color-text-secondary)]">
                    FEMA Zone: <span className="font-medium">{riskData.flood_risk.zone}</span>
                    {riskData.flood_risk.zone_description && ` - ${riskData.flood_risk.zone_description}`}
                  </p>
                )}
              </div>

              {/* Fire Protection */}
              <div className="p-3 rounded-lg border border-[var(--color-border-subtle)]">
                <div className="flex items-center gap-2 mb-2">
                  <Flame className="h-4 w-4 text-[var(--color-warning-500)]" />
                  <span className="font-medium text-[var(--color-text-primary)]">Fire Protection</span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  {riskData.fire_protection.protection_class && (
                    <p className="text-[var(--color-text-secondary)]">
                      ISO Class: <span className="font-medium">{riskData.fire_protection.protection_class}</span>
                    </p>
                  )}
                  {riskData.fire_protection.fire_station_distance_miles && (
                    <p className="text-[var(--color-text-secondary)]">
                      Fire Station: <span className="font-medium">{riskData.fire_protection.fire_station_distance_miles} mi</span>
                    </p>
                  )}
                </div>
              </div>

              {/* Weather Risks */}
              <div className="p-3 rounded-lg border border-[var(--color-border-subtle)]">
                <div className="flex items-center gap-2 mb-2">
                  <CloudLightning className="h-4 w-4 text-[var(--color-primary-500)]" />
                  <span className="font-medium text-[var(--color-text-primary)]">Weather Exposure</span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <p className="text-[var(--color-text-secondary)]">
                    Tornado: <span className={cn('font-medium', getRiskColor(riskData.weather_risk.tornado_risk))}>{riskData.weather_risk.tornado_risk}</span>
                  </p>
                  <p className="text-[var(--color-text-secondary)]">
                    Hail: <span className={cn('font-medium', getRiskColor(riskData.weather_risk.hail_risk))}>{riskData.weather_risk.hail_risk}</span>
                  </p>
                  <p className="text-[var(--color-text-secondary)]">
                    Earthquake: <span className={cn('font-medium', getRiskColor(riskData.weather_risk.earthquake_risk))}>{riskData.weather_risk.earthquake_risk}</span>
                  </p>
                </div>
                {riskData.weather_risk.historical_events.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-[var(--color-border-subtle)]">
                    <p className="text-xs text-[var(--color-text-muted)] mb-1">Historical Events:</p>
                    <ul className="text-xs text-[var(--color-text-secondary)] space-y-0.5">
                      {riskData.weather_risk.historical_events.slice(0, 3).map((event, idx) => (
                        <li key={idx}>• {event}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* Insurance Implications */}
              {riskData.insurance_implications.length > 0 && (
                <div className="p-3 rounded-lg bg-[var(--color-warning-50)] dark:bg-[var(--color-warning-500)]/10 border border-[var(--color-warning-200)] dark:border-[var(--color-warning-500)]/20">
                  <div className="flex items-center gap-2 mb-2">
                    <AlertTriangle className="h-4 w-4 text-[var(--color-warning-500)]" />
                    <span className="font-medium text-[var(--color-warning-600)] dark:text-[var(--color-warning-400)]">
                      Insurance Implications
                    </span>
                  </div>
                  <ul className="text-sm text-[var(--color-warning-700)] dark:text-[var(--color-warning-300)] space-y-1">
                    {riskData.insurance_implications.map((imp, idx) => (
                      <li key={idx}>• {imp}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between mt-4 pt-4 border-t border-[var(--color-border-subtle)]">
              <div className="flex items-center gap-4 text-xs text-[var(--color-text-muted)]">
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {new Date(riskData.enrichment_date).toLocaleDateString()}
                </span>
                <span>
                  {(riskData.total_latency_ms / 1000).toFixed(1)}s research
                </span>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => fetchRiskData(true)}
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
