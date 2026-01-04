'use client';

import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  AlertTriangle,
  AlertCircle,
  Info,
  Filter,
  SortAsc,
  SortDesc,
  ChevronDown,
  X,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button, Badge, Card } from '@/components/primitives';
import { GapCard } from './GapCard';
import { staggerContainer, staggerItem } from '@/lib/motion/variants';
import type { Gap, GapType, Severity, GapStatus } from '@/types/api';

interface GapListProps {
  gaps: Gap[];
  onGapClick?: (gap: Gap) => void;
  showFilters?: boolean;
  compact?: boolean;
  maxItems?: number;
  propertyFilter?: string;
}

type SortField = 'severity' | 'created_at' | 'property_name' | 'gap_type';
type SortDirection = 'asc' | 'desc';

const severityOrder: Record<Severity, number> = {
  critical: 0,
  warning: 1,
  info: 2,
};

const gapTypeLabels: Record<GapType, string> = {
  underinsurance: 'Underinsurance',
  missing_coverage: 'Missing Coverage',
  high_deductible: 'High Deductible',
  expiring: 'Expiring',
  expiration: 'Expiration',
  non_compliant: 'Non-Compliant',
  outdated_valuation: 'Outdated Valuation',
  missing_document: 'Missing Document',
  missing_flood: 'Missing Flood',
};

export function GapList({
  gaps,
  onGapClick,
  showFilters = true,
  compact = false,
  maxItems,
  propertyFilter,
}: GapListProps) {
  const [selectedSeverity, setSelectedSeverity] = useState<Severity | 'all'>('all');
  const [selectedType, setSelectedType] = useState<GapType | 'all'>('all');
  const [selectedStatus, setSelectedStatus] = useState<GapStatus | 'all'>('all');
  const [sortField, setSortField] = useState<SortField>('severity');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');
  const [showFilterPanel, setShowFilterPanel] = useState(false);

  const filteredAndSortedGaps = useMemo(() => {
    let result = [...gaps];

    // Apply property filter if provided
    if (propertyFilter) {
      result = result.filter((g) => g.property_id === propertyFilter);
    }

    // Apply severity filter
    if (selectedSeverity !== 'all') {
      result = result.filter((g) => g.severity === selectedSeverity);
    }

    // Apply type filter
    if (selectedType !== 'all') {
      result = result.filter((g) => g.gap_type === selectedType);
    }

    // Apply status filter
    if (selectedStatus !== 'all') {
      result = result.filter((g) => g.status === selectedStatus);
    }

    // Sort
    result.sort((a, b) => {
      let comparison = 0;

      switch (sortField) {
        case 'severity':
          comparison = severityOrder[a.severity] - severityOrder[b.severity];
          break;
        case 'created_at':
          comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
          break;
        case 'property_name':
          comparison = a.property_name.localeCompare(b.property_name);
          break;
        case 'gap_type':
          comparison = a.gap_type.localeCompare(b.gap_type);
          break;
      }

      return sortDirection === 'asc' ? comparison : -comparison;
    });

    // Limit items if specified
    if (maxItems) {
      result = result.slice(0, maxItems);
    }

    return result;
  }, [gaps, selectedSeverity, selectedType, selectedStatus, sortField, sortDirection, maxItems, propertyFilter]);

  const hasActiveFilters = selectedSeverity !== 'all' || selectedType !== 'all' || selectedStatus !== 'all';

  const clearFilters = () => {
    setSelectedSeverity('all');
    setSelectedType('all');
    setSelectedStatus('all');
  };

  const toggleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const SortIcon = sortDirection === 'asc' ? SortAsc : SortDesc;

  // Get unique gap types from the data
  const availableTypes = useMemo(() => {
    const types = new Set(gaps.map((g) => g.gap_type));
    return Array.from(types);
  }, [gaps]);

  return (
    <div className="space-y-4">
      {showFilters && (
        <>
          {/* Filter Bar */}
          <div className="flex items-center gap-3 flex-wrap">
            {/* Severity Quick Filters */}
            <div className="flex items-center gap-1">
              <Button
                variant={selectedSeverity === 'all' ? 'primary' : 'ghost'}
                size="sm"
                onClick={() => setSelectedSeverity('all')}
              >
                All
              </Button>
              <Button
                variant={selectedSeverity === 'critical' ? 'primary' : 'ghost'}
                size="sm"
                onClick={() => setSelectedSeverity('critical')}
                className={selectedSeverity === 'critical' ? '' : 'text-[var(--color-critical-500)]'}
              >
                <AlertTriangle className="h-4 w-4 mr-1" />
                Critical ({gaps.filter((g) => g.severity === 'critical').length})
              </Button>
              <Button
                variant={selectedSeverity === 'warning' ? 'primary' : 'ghost'}
                size="sm"
                onClick={() => setSelectedSeverity('warning')}
                className={selectedSeverity === 'warning' ? '' : 'text-[var(--color-warning-500)]'}
              >
                <AlertCircle className="h-4 w-4 mr-1" />
                Warning ({gaps.filter((g) => g.severity === 'warning').length})
              </Button>
              <Button
                variant={selectedSeverity === 'info' ? 'primary' : 'ghost'}
                size="sm"
                onClick={() => setSelectedSeverity('info')}
                className={selectedSeverity === 'info' ? '' : 'text-[var(--color-info-500)]'}
              >
                <Info className="h-4 w-4 mr-1" />
                Info ({gaps.filter((g) => g.severity === 'info').length})
              </Button>
            </div>

            <div className="flex-1" />

            {/* More Filters */}
            <Button
              variant={showFilterPanel ? 'secondary' : 'ghost'}
              size="sm"
              onClick={() => setShowFilterPanel(!showFilterPanel)}
              leftIcon={<Filter className="h-4 w-4" />}
            >
              Filters
              {hasActiveFilters && (
                <Badge variant="primary" size="sm" className="ml-1">
                  {(selectedSeverity !== 'all' ? 1 : 0) +
                    (selectedType !== 'all' ? 1 : 0) +
                    (selectedStatus !== 'all' ? 1 : 0)}
                </Badge>
              )}
            </Button>

            {/* Sort */}
            <div className="relative">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => toggleSort(sortField)}
                leftIcon={<SortIcon className="h-4 w-4" />}
              >
                Sort
              </Button>
            </div>
          </div>

          {/* Extended Filter Panel */}
          <AnimatePresence>
            {showFilterPanel && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="overflow-hidden"
              >
                <Card padding="md" className="bg-[var(--color-surface-sunken)]">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* Type Filter */}
                    <div>
                      <label className="block text-sm font-medium text-[var(--color-text-secondary)] mb-2">
                        Gap Type
                      </label>
                      <select
                        value={selectedType}
                        onChange={(e) => setSelectedType(e.target.value as GapType | 'all')}
                        className="w-full px-3 py-2 rounded-lg border border-[var(--color-border-default)] bg-[var(--color-surface)] text-[var(--color-text-primary)]"
                      >
                        <option value="all">All Types</option>
                        {availableTypes.map((type) => (
                          <option key={type} value={type}>
                            {gapTypeLabels[type]}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Status Filter */}
                    <div>
                      <label className="block text-sm font-medium text-[var(--color-text-secondary)] mb-2">
                        Status
                      </label>
                      <select
                        value={selectedStatus}
                        onChange={(e) => setSelectedStatus(e.target.value as GapStatus | 'all')}
                        className="w-full px-3 py-2 rounded-lg border border-[var(--color-border-default)] bg-[var(--color-surface)] text-[var(--color-text-primary)]"
                      >
                        <option value="all">All Statuses</option>
                        <option value="open">Open</option>
                        <option value="acknowledged">Acknowledged</option>
                        <option value="resolved">Resolved</option>
                      </select>
                    </div>

                    {/* Sort Field */}
                    <div>
                      <label className="block text-sm font-medium text-[var(--color-text-secondary)] mb-2">
                        Sort By
                      </label>
                      <select
                        value={sortField}
                        onChange={(e) => setSortField(e.target.value as SortField)}
                        className="w-full px-3 py-2 rounded-lg border border-[var(--color-border-default)] bg-[var(--color-surface)] text-[var(--color-text-primary)]"
                      >
                        <option value="severity">Severity</option>
                        <option value="created_at">Date Detected</option>
                        <option value="property_name">Property Name</option>
                        <option value="gap_type">Gap Type</option>
                      </select>
                    </div>
                  </div>

                  {hasActiveFilters && (
                    <div className="mt-4 pt-4 border-t border-[var(--color-border-subtle)]">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={clearFilters}
                        leftIcon={<X className="h-4 w-4" />}
                      >
                        Clear all filters
                      </Button>
                    </div>
                  )}
                </Card>
              </motion.div>
            )}
          </AnimatePresence>
        </>
      )}

      {/* Results Count */}
      <div className="flex items-center justify-between text-sm text-[var(--color-text-muted)]">
        <span>
          Showing {filteredAndSortedGaps.length} of {gaps.length} gaps
        </span>
        {hasActiveFilters && (
          <button
            onClick={clearFilters}
            className="text-[var(--color-primary-500)] hover:underline"
          >
            Clear filters
          </button>
        )}
      </div>

      {/* Gap List */}
      {filteredAndSortedGaps.length === 0 ? (
        <Card padding="lg" className="text-center">
          <div className="py-8">
            <AlertCircle className="h-12 w-12 text-[var(--color-text-muted)] mx-auto mb-4" />
            <h3 className="text-lg font-medium text-[var(--color-text-primary)] mb-2">
              No gaps found
            </h3>
            <p className="text-[var(--color-text-secondary)]">
              {hasActiveFilters
                ? 'Try adjusting your filters to see more results.'
                : 'All coverage gaps have been addressed.'}
            </p>
          </div>
        </Card>
      ) : (
        <motion.div
          variants={staggerContainer}
          initial="initial"
          animate="animate"
          className={cn(compact ? 'space-y-2' : 'space-y-4')}
        >
          {filteredAndSortedGaps.map((gap) => (
            <motion.div key={gap.id} variants={staggerItem}>
              <GapCard
                gap={gap}
                onClick={() => onGapClick?.(gap)}
                compact={compact}
              />
            </motion.div>
          ))}
        </motion.div>
      )}
    </div>
  );
}
