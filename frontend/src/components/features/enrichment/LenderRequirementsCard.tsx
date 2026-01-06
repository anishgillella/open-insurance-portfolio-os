'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Landmark,
  Shield,
  FileCheck,
  Loader2,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Clock,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Search,
  DollarSign,
} from 'lucide-react';
import { cn, formatCurrency } from '@/lib/utils';
import { Button, Card, Badge } from '@/components/primitives';
import { enrichmentApi, type LenderRequirementsResponse, type CoverageRequirement } from '@/lib/api';

interface LenderRequirementsCardProps {
  lenderName?: string;
  loanType?: string;
  className?: string;
}

const CoverageRequirementRow = ({ coverage, label }: { coverage: CoverageRequirement | null; label: string }) => {
  if (!coverage) return null;

  return (
    <div className="flex items-center justify-between p-2 rounded-lg border border-[var(--color-border-subtle)]">
      <div className="flex items-center gap-2">
        {coverage.required ? (
          <CheckCircle2 className="h-4 w-4 text-[var(--color-success-500)]" />
        ) : (
          <XCircle className="h-4 w-4 text-[var(--color-text-muted)]" />
        )}
        <span className="text-sm font-medium text-[var(--color-text-primary)]">{label}</span>
        {coverage.required && (
          <Badge variant="critical" className="text-[10px]">Required</Badge>
        )}
      </div>
      <div className="text-right">
        {coverage.minimum_limit && (
          <p className="text-sm font-medium text-[var(--color-text-primary)]">
            {formatCurrency(coverage.minimum_limit)}
          </p>
        )}
        {coverage.limit_description && !coverage.minimum_limit && (
          <p className="text-sm text-[var(--color-text-secondary)]">
            {coverage.limit_description}
          </p>
        )}
      </div>
    </div>
  );
};

export function LenderRequirementsCard({
  lenderName: initialLender,
  loanType: initialLoanType,
  className,
}: LenderRequirementsCardProps) {
  const [lenderName, setLenderName] = useState(initialLender || '');
  const [loanType, setLoanType] = useState(initialLoanType || '');
  const [searchInput, setSearchInput] = useState('');
  const [lenderData, setLenderData] = useState<LenderRequirementsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);

  const fetchLenderData = async (name?: string) => {
    const searchName = name || lenderName || searchInput;
    if (!searchName.trim()) return;

    setIsLoading(true);
    setError(null);
    setLenderName(searchName);
    try {
      const data = await enrichmentApi.getLenderRequirements(searchName, loanType || undefined);
      setLenderData(data);
      setIsExpanded(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch lender requirements');
    } finally {
      setIsLoading(false);
    }
  };

  if (!lenderData && !isLoading && !lenderName) {
    return (
      <Card padding="lg" className={className}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">
            Lender Requirements
          </h2>
          <Badge variant="info">AI-Powered</Badge>
        </div>
        <p className="text-sm text-[var(--color-text-secondary)] mb-4">
          Look up lender-specific insurance requirements including coverage limits, deductibles, and endorsements.
        </p>
        <div className="space-y-3">
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Enter lender name (e.g., Fannie Mae, Wells Fargo)..."
            className="w-full px-3 py-2 rounded-lg border border-[var(--color-border-default)] bg-[var(--color-surface)] text-[var(--color-text-primary)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-primary-500)]"
            onKeyDown={(e) => e.key === 'Enter' && fetchLenderData(searchInput)}
          />
          <input
            type="text"
            value={loanType}
            onChange={(e) => setLoanType(e.target.value)}
            placeholder="Loan type (optional, e.g., conventional, FHA)..."
            className="w-full px-3 py-2 rounded-lg border border-[var(--color-border-default)] bg-[var(--color-surface)] text-[var(--color-text-primary)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-primary-500)]"
          />
          <Button
            variant="primary"
            onClick={() => fetchLenderData(searchInput)}
            disabled={isLoading || !searchInput.trim()}
            leftIcon={isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
            className="w-full"
          >
            Look Up Requirements
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
          <p className="text-[var(--color-text-primary)] font-medium">Lookup Failed</p>
          <p className="text-sm text-[var(--color-text-muted)] mt-1">{error}</p>
          <Button variant="secondary" onClick={() => fetchLenderData()} className="mt-4">
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
          <p className="text-[var(--color-text-primary)] font-medium">Looking Up Requirements</p>
          <p className="text-sm text-[var(--color-text-muted)] mt-1">
            Researching {lenderName} insurance requirements...
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
          <Landmark className="h-5 w-5 text-[var(--color-primary-500)]" />
          <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">
            {lenderData?.lender_name}
          </h2>
          {lenderData?.loan_type && (
            <Badge variant="secondary">{lenderData.loan_type}</Badge>
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

      {/* Quick Summary */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        <div className="text-center p-3 rounded-lg bg-[var(--color-surface-sunken)]">
          <Shield className="h-5 w-5 mx-auto mb-1 text-[var(--color-success-500)]" />
          <p className="text-xs text-[var(--color-text-muted)]">Min Carrier Rating</p>
          <p className="text-sm font-bold text-[var(--color-text-primary)]">
            {lenderData?.minimum_carrier_rating || 'A-'}
          </p>
        </div>
        <div className="text-center p-3 rounded-lg bg-[var(--color-surface-sunken)]">
          <DollarSign className="h-5 w-5 mx-auto mb-1 text-[var(--color-warning-500)]" />
          <p className="text-xs text-[var(--color-text-muted)]">Max Deductible</p>
          <p className="text-sm font-bold text-[var(--color-text-primary)]">
            {lenderData?.max_property_deductible_pct
              ? `${lenderData.max_property_deductible_pct}%`
              : lenderData?.max_property_deductible_flat
              ? formatCurrency(lenderData.max_property_deductible_flat)
              : 'N/A'}
          </p>
        </div>
        <div className="text-center p-3 rounded-lg bg-[var(--color-surface-sunken)]">
          <FileCheck className="h-5 w-5 mx-auto mb-1 text-[var(--color-info-500)]" />
          <p className="text-xs text-[var(--color-text-muted)]">Cancel Notice</p>
          <p className="text-sm font-bold text-[var(--color-text-primary)]">
            {lenderData?.notice_of_cancellation_days
              ? `${lenderData.notice_of_cancellation_days} days`
              : 'N/A'}
          </p>
        </div>
      </div>

      <AnimatePresence>
        {isExpanded && lenderData && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden"
          >
            {/* Coverage Requirements */}
            <div className="mb-4">
              <h3 className="text-sm font-medium text-[var(--color-text-primary)] mb-2">
                Coverage Requirements
              </h3>
              <div className="space-y-2">
                <CoverageRequirementRow coverage={lenderData.property_coverage} label="Property Coverage" />
                <CoverageRequirementRow coverage={lenderData.liability_coverage} label="General Liability" />
                <CoverageRequirementRow coverage={lenderData.umbrella_coverage} label="Umbrella/Excess" />
                <CoverageRequirementRow coverage={lenderData.flood_coverage} label="Flood Coverage" />
                <CoverageRequirementRow coverage={lenderData.wind_coverage} label="Wind/Named Storm" />
                {lenderData.other_coverages.map((cov, idx) => (
                  <CoverageRequirementRow key={idx} coverage={cov} label={cov.coverage_type} />
                ))}
              </div>
            </div>

            {/* Required Endorsements */}
            {lenderData.required_endorsements.length > 0 && (
              <div className="mb-4">
                <h3 className="text-sm font-medium text-[var(--color-text-primary)] mb-2">
                  Required Endorsements
                </h3>
                <div className="space-y-2">
                  {lenderData.required_endorsements.map((end, idx) => (
                    <div key={idx} className="flex items-start gap-2 p-2 rounded-lg border border-[var(--color-border-subtle)]">
                      <CheckCircle2 className="h-4 w-4 text-[var(--color-success-500)] mt-0.5" />
                      <div>
                        <p className="text-sm font-medium text-[var(--color-text-primary)]">
                          {end.endorsement_name}
                        </p>
                        {end.description && (
                          <p className="text-xs text-[var(--color-text-muted)]">{end.description}</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Key Requirements */}
            <div className="grid grid-cols-2 gap-3 mb-4">
              <div className="p-3 rounded-lg border border-[var(--color-border-subtle)]">
                <p className="text-xs text-[var(--color-text-muted)] mb-1">Mortgagee Clause</p>
                <div className="flex items-center gap-1">
                  {lenderData.mortgagee_clause_required ? (
                    <>
                      <CheckCircle2 className="h-4 w-4 text-[var(--color-success-500)]" />
                      <span className="text-sm text-[var(--color-success-600)]">Required</span>
                    </>
                  ) : (
                    <>
                      <XCircle className="h-4 w-4 text-[var(--color-text-muted)]" />
                      <span className="text-sm text-[var(--color-text-muted)]">Not Required</span>
                    </>
                  )}
                </div>
              </div>
              <div className="p-3 rounded-lg border border-[var(--color-border-subtle)]">
                <p className="text-xs text-[var(--color-text-muted)] mb-1">Waiver of Subrogation</p>
                <div className="flex items-center gap-1">
                  {lenderData.waiver_of_subrogation_required ? (
                    <>
                      <CheckCircle2 className="h-4 w-4 text-[var(--color-success-500)]" />
                      <span className="text-sm text-[var(--color-success-600)]">Required</span>
                    </>
                  ) : (
                    <>
                      <XCircle className="h-4 w-4 text-[var(--color-text-muted)]" />
                      <span className="text-sm text-[var(--color-text-muted)]">Not Required</span>
                    </>
                  )}
                </div>
              </div>
            </div>

            {/* Special Requirements */}
            {lenderData.special_requirements.length > 0 && (
              <div className="p-3 rounded-lg bg-[var(--color-info-50)] dark:bg-[var(--color-info-500)]/10 border border-[var(--color-info-200)] dark:border-[var(--color-info-500)]/20 mb-4">
                <h3 className="text-sm font-medium text-[var(--color-info-600)] dark:text-[var(--color-info-400)] mb-2">
                  Special Requirements
                </h3>
                <ul className="text-sm text-[var(--color-info-700)] dark:text-[var(--color-info-300)] space-y-1">
                  {lenderData.special_requirements.map((req, idx) => (
                    <li key={idx}>• {req}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Coastal/Earthquake */}
            {(lenderData.coastal_requirements || lenderData.earthquake_requirements) && (
              <div className="grid grid-cols-2 gap-3 mb-4">
                {lenderData.coastal_requirements && (
                  <div className="p-3 rounded-lg border border-[var(--color-border-subtle)]">
                    <p className="text-xs text-[var(--color-text-muted)] mb-1">Coastal Requirements</p>
                    <p className="text-sm text-[var(--color-text-primary)]">{lenderData.coastal_requirements}</p>
                  </div>
                )}
                {lenderData.earthquake_requirements && (
                  <div className="p-3 rounded-lg border border-[var(--color-border-subtle)]">
                    <p className="text-xs text-[var(--color-text-muted)] mb-1">Earthquake Requirements</p>
                    <p className="text-sm text-[var(--color-text-primary)]">{lenderData.earthquake_requirements}</p>
                  </div>
                )}
              </div>
            )}

            {/* Source */}
            {lenderData.source_document && (
              <div className="text-xs text-[var(--color-text-muted)] mb-4">
                Source: {lenderData.source_document}
                {lenderData.source_section && ` - ${lenderData.source_section}`}
              </div>
            )}

            {/* Footer */}
            <div className="flex items-center justify-between mt-4 pt-4 border-t border-[var(--color-border-subtle)]">
              <div className="flex items-center gap-4 text-xs text-[var(--color-text-muted)]">
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {new Date(lenderData.research_date).toLocaleDateString()}
                </span>
                <span>
                  {(lenderData.total_latency_ms / 1000).toFixed(1)}s research
                </span>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setLenderData(null);
                    setLenderName('');
                    setSearchInput('');
                    setLoanType('');
                  }}
                >
                  New Search
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => fetchLenderData()}
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
