'use client';

import { useState, useMemo, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Link from 'next/link';
import {
  LayoutGrid,
  List,
  Search,
  SlidersHorizontal,
  ChevronDown,
  X,
  Building2,
  AlertTriangle,
  Clock,
  Loader2,
  RefreshCw,
  Trash2,
} from 'lucide-react';
import { cn, getGrade } from '@/lib/utils';
import { Button, Badge, Card } from '@/components/primitives';
import { PropertyCard } from '@/components/features/properties';
import { staggerContainer, staggerItem } from '@/lib/motion/variants';
import { propertiesApi, dashboardApi, adminApi, type Property, type DashboardSummary, type ResetResponse } from '@/lib/api';

type ViewMode = 'grid' | 'list';
type SortOption = 'name' | 'healthScore' | 'tiv' | 'premium' | 'expiration';
type SortDirection = 'asc' | 'desc';
type FilterGrade = 'all' | 'A' | 'B' | 'C' | 'D' | 'F';
type FilterExpiration = 'all' | '30' | '60' | '90';

export default function PropertiesPage() {
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<SortOption>('name');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');
  const [filterGrade, setFilterGrade] = useState<FilterGrade>('all');
  const [filterExpiration, setFilterExpiration] = useState<FilterExpiration>('all');
  const [showFilters, setShowFilters] = useState(false);

  const [properties, setProperties] = useState<Property[]>([]);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Delete modal state
  const [propertyToDelete, setPropertyToDelete] = useState<Property | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  // Reset modal state
  const [showResetModal, setShowResetModal] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [resetError, setResetError] = useState<string | null>(null);
  const [resetResult, setResetResult] = useState<ResetResponse | null>(null);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [propertiesData, summaryData] = await Promise.all([
        propertiesApi.list(),
        dashboardApi.getSummary(),
      ]);
      // Handle various API response formats
      setProperties(
        Array.isArray(propertiesData) ? propertiesData :
        (propertiesData as { properties?: Property[]; items?: Property[] })?.properties ||
        (propertiesData as { items?: Property[] })?.items || []
      );
      setSummary(summaryData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load properties');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const filteredAndSortedProperties = useMemo(() => {
    let result = [...properties];

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (p) =>
          p.name.toLowerCase().includes(query) ||
          p.address.street.toLowerCase().includes(query) ||
          p.address.city.toLowerCase().includes(query)
      );
    }

    // Grade filter
    if (filterGrade !== 'all') {
      result = result.filter((p) => getGrade(p.health_score) === filterGrade);
    }

    // Expiration filter
    if (filterExpiration !== 'all') {
      const days = parseInt(filterExpiration);
      result = result.filter((p) => (p.days_until_expiration || 999) <= days);
    }

    // Sort
    result.sort((a, b) => {
      let comparison = 0;
      switch (sortBy) {
        case 'name':
          comparison = a.name.localeCompare(b.name);
          break;
        case 'healthScore':
          comparison = a.health_score - b.health_score;
          break;
        case 'tiv':
          comparison = (Number(a.total_insured_value) || 0) - (Number(b.total_insured_value) || 0);
          break;
        case 'premium':
          comparison = (Number(a.total_premium) || 0) - (Number(b.total_premium) || 0);
          break;
        case 'expiration':
          comparison = (a.days_until_expiration || 999) - (b.days_until_expiration || 999);
          break;
      }
      return sortDirection === 'asc' ? comparison : -comparison;
    });

    return result;
  }, [properties, searchQuery, sortBy, sortDirection, filterGrade, filterExpiration]);

  const hasActiveFilters = filterGrade !== 'all' || filterExpiration !== 'all';

  const clearFilters = () => {
    setFilterGrade('all');
    setFilterExpiration('all');
    setSearchQuery('');
  };

  // Handle delete property
  const handleDeleteClick = (property: Property) => {
    setPropertyToDelete(property);
    setDeleteError(null);
  };

  const handleDeleteConfirm = async () => {
    if (!propertyToDelete) return;

    setIsDeleting(true);
    setDeleteError(null);

    try {
      await propertiesApi.delete(propertyToDelete.id);
      setPropertyToDelete(null);
      // Refresh data to update all counts
      await fetchData();
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : 'Failed to delete property');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleDeleteCancel = () => {
    setPropertyToDelete(null);
    setDeleteError(null);
  };

  // Handle reset all data
  const handleResetClick = () => {
    setShowResetModal(true);
    setResetError(null);
    setResetResult(null);
  };

  const handleResetConfirm = async () => {
    setIsResetting(true);
    setResetError(null);

    try {
      const result = await adminApi.resetAllData();
      setResetResult(result);
      // Refresh data after reset
      await fetchData();
    } catch (err) {
      setResetError(err instanceof Error ? err.message : 'Failed to reset data');
    } finally {
      setIsResetting(false);
    }
  };

  const handleResetCancel = () => {
    setShowResetModal(false);
    setResetError(null);
    setResetResult(null);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 text-[var(--color-primary-500)] animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-16">
        <AlertTriangle className="h-12 w-12 text-[var(--color-critical-500)] mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-2">
          Failed to load properties
        </h3>
        <p className="text-[var(--color-text-muted)] mb-4">{error}</p>
        <Button variant="secondary" onClick={fetchData}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Try Again
        </Button>
      </div>
    );
  }

  return (
    <motion.div
      variants={staggerContainer}
      initial="initial"
      animate="animate"
      className="space-y-6"
    >
      {/* Header */}
      <motion.div variants={staggerItem} className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">Properties</h1>
          <p className="text-[var(--color-text-secondary)] mt-1">
            Manage your portfolio of {properties.length} properties
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={fetchData}>
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={handleResetClick}
            className="text-[var(--color-critical-500)] hover:bg-[var(--color-critical-50)] dark:hover:bg-[var(--color-critical-500)]/10"
          >
            <Trash2 className="h-4 w-4 mr-1" />
            Reset All
          </Button>
        </div>
      </motion.div>

      {/* Summary Cards */}
      <motion.div variants={staggerItem} className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card padding="md" className="flex items-center gap-4">
          <div className="p-3 rounded-xl bg-[var(--color-primary-50)] dark:bg-[var(--color-primary-500)]/20">
            <Building2 className="h-5 w-5 text-[var(--color-primary-500)]" />
          </div>
          <div>
            <p className="text-sm text-[var(--color-text-muted)]">Total Properties</p>
            <p className="text-xl font-bold text-[var(--color-text-primary)]">
              {summary?.portfolio_stats?.total_properties || properties.length}
            </p>
          </div>
        </Card>

        <Card padding="md" className="flex items-center gap-4">
          <div className="p-3 rounded-xl bg-[var(--color-critical-50)] dark:bg-[var(--color-critical-500)]/20">
            <AlertTriangle className="h-5 w-5 text-[var(--color-critical-500)]" />
          </div>
          <div>
            <p className="text-sm text-[var(--color-text-muted)]">With Gaps</p>
            <p className="text-xl font-bold text-[var(--color-text-primary)]">
              {summary?.gap_stats?.properties_with_gaps || 0}
            </p>
          </div>
        </Card>

        <Card padding="md" className="flex items-center gap-4">
          <div className="p-3 rounded-xl bg-[var(--color-warning-50)] dark:bg-[var(--color-warning-500)]/20">
            <Clock className="h-5 w-5 text-[var(--color-warning-500)]" />
          </div>
          <div>
            <p className="text-sm text-[var(--color-text-muted)]">Expiring in 30d</p>
            <p className="text-xl font-bold text-[var(--color-text-primary)]">
              {summary?.expiration_stats?.expiring_30_days || 0}
            </p>
          </div>
        </Card>

        <Card padding="md" className="flex items-center gap-4">
          <div className="p-3 rounded-xl bg-[var(--color-success-50)] dark:bg-[var(--color-success-500)]/20">
            <Building2 className="h-5 w-5 text-[var(--color-success-500)]" />
          </div>
          <div>
            <p className="text-sm text-[var(--color-text-muted)]">Total Gaps</p>
            <p className="text-xl font-bold text-[var(--color-text-primary)]">
              {summary?.gap_stats?.total_open_gaps || 0}
            </p>
          </div>
        </Card>
      </motion.div>

      {/* Toolbar */}
      <motion.div variants={staggerItem} className="flex flex-col sm:flex-row gap-4">
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--color-text-muted)]" />
          <input
            type="text"
            placeholder="Search properties..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className={cn(
              'w-full pl-10 pr-4 py-2.5 rounded-xl',
              'bg-[var(--color-surface-sunken)]',
              'border border-transparent',
              'text-sm text-[var(--color-text-primary)]',
              'placeholder:text-[var(--color-text-muted)]',
              'focus:outline-none focus:border-[var(--color-primary-500)]',
              'focus:ring-4 focus:ring-[var(--color-primary-500)]/20',
              'transition-all'
            )}
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-full hover:bg-[var(--color-surface)]"
            >
              <X className="h-3.5 w-3.5 text-[var(--color-text-muted)]" />
            </button>
          )}
        </div>

        {/* Filters Toggle */}
        <Button
          variant={showFilters ? 'primary' : 'secondary'}
          leftIcon={<SlidersHorizontal className="h-4 w-4" />}
          onClick={() => setShowFilters(!showFilters)}
        >
          Filters
          {hasActiveFilters && (
            <span className="ml-1 px-1.5 py-0.5 text-xs rounded-full bg-white/20">
              {(filterGrade !== 'all' ? 1 : 0) + (filterExpiration !== 'all' ? 1 : 0)}
            </span>
          )}
        </Button>

        {/* Sort Dropdown */}
        <div className="relative">
          <Button
            variant="secondary"
            rightIcon={<ChevronDown className="h-4 w-4" />}
            onClick={() => {
              if (sortBy === 'healthScore') {
                setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
              } else {
                setSortBy('healthScore');
                setSortDirection('desc');
              }
            }}
          >
            Sort: {sortBy === 'name' ? 'Name' : sortBy === 'healthScore' ? 'Health' : sortBy === 'tiv' ? 'TIV' : sortBy === 'premium' ? 'Premium' : 'Expiration'}
          </Button>
        </div>

        {/* View Toggle */}
        <div className="flex items-center gap-1 p-1 rounded-lg bg-[var(--color-surface-sunken)]">
          <button
            onClick={() => setViewMode('grid')}
            className={cn(
              'p-2 rounded-md transition-all',
              viewMode === 'grid'
                ? 'bg-[var(--color-surface)] shadow-sm text-[var(--color-text-primary)]'
                : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'
            )}
          >
            <LayoutGrid className="h-4 w-4" />
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={cn(
              'p-2 rounded-md transition-all',
              viewMode === 'list'
                ? 'bg-[var(--color-surface)] shadow-sm text-[var(--color-text-primary)]'
                : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'
            )}
          >
            <List className="h-4 w-4" />
          </button>
        </div>
      </motion.div>

      {/* Filters Panel */}
      <AnimatePresence>
        {showFilters && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
          >
            <Card padding="md" className="flex flex-wrap gap-6">
              {/* Grade Filter */}
              <div>
                <p className="text-sm font-medium text-[var(--color-text-secondary)] mb-2">
                  Health Grade
                </p>
                <div className="flex gap-2">
                  {(['all', 'A', 'B', 'C', 'D', 'F'] as const).map((grade) => (
                    <button
                      key={grade}
                      onClick={() => setFilterGrade(grade)}
                      className={cn(
                        'px-3 py-1.5 rounded-lg text-sm font-medium transition-all',
                        filterGrade === grade
                          ? 'bg-[var(--color-primary-500)] text-white'
                          : 'bg-[var(--color-surface-sunken)] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-sunken)]/80'
                      )}
                    >
                      {grade === 'all' ? 'All' : grade}
                    </button>
                  ))}
                </div>
              </div>

              {/* Expiration Filter */}
              <div>
                <p className="text-sm font-medium text-[var(--color-text-secondary)] mb-2">
                  Expiring Within
                </p>
                <div className="flex gap-2">
                  {(['all', '30', '60', '90'] as const).map((days) => (
                    <button
                      key={days}
                      onClick={() => setFilterExpiration(days)}
                      className={cn(
                        'px-3 py-1.5 rounded-lg text-sm font-medium transition-all',
                        filterExpiration === days
                          ? 'bg-[var(--color-primary-500)] text-white'
                          : 'bg-[var(--color-surface-sunken)] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-sunken)]/80'
                      )}
                    >
                      {days === 'all' ? 'All' : `${days} days`}
                    </button>
                  ))}
                </div>
              </div>

              {/* Sort Options */}
              <div>
                <p className="text-sm font-medium text-[var(--color-text-secondary)] mb-2">
                  Sort By
                </p>
                <div className="flex gap-2">
                  {([
                    { value: 'name', label: 'Name' },
                    { value: 'healthScore', label: 'Health' },
                    { value: 'tiv', label: 'TIV' },
                    { value: 'premium', label: 'Premium' },
                    { value: 'expiration', label: 'Expiration' },
                  ] as const).map((option) => (
                    <button
                      key={option.value}
                      onClick={() => {
                        if (sortBy === option.value) {
                          setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
                        } else {
                          setSortBy(option.value);
                          setSortDirection('asc');
                        }
                      }}
                      className={cn(
                        'px-3 py-1.5 rounded-lg text-sm font-medium transition-all',
                        sortBy === option.value
                          ? 'bg-[var(--color-primary-500)] text-white'
                          : 'bg-[var(--color-surface-sunken)] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-sunken)]/80'
                      )}
                    >
                      {option.label}
                      {sortBy === option.value && (
                        <span className="ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                      )}
                    </button>
                  ))}
                </div>
              </div>

              {/* Clear Filters */}
              {hasActiveFilters && (
                <div className="flex items-end">
                  <Button variant="ghost" onClick={clearFilters} leftIcon={<X className="h-4 w-4" />}>
                    Clear filters
                  </Button>
                </div>
              )}
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Results Count */}
      <motion.div variants={staggerItem}>
        <p className="text-sm text-[var(--color-text-muted)]">
          Showing {filteredAndSortedProperties.length} of {properties.length} properties
          {hasActiveFilters && (
            <button onClick={clearFilters} className="ml-2 text-[var(--color-primary-500)] hover:underline">
              Clear filters
            </button>
          )}
        </p>
      </motion.div>

      {/* Property Grid/List */}
      <motion.div
        variants={staggerItem}
        className={cn(
          viewMode === 'grid'
            ? 'grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6'
            : 'flex flex-col gap-3'
        )}
      >
        <AnimatePresence mode="popLayout">
          {filteredAndSortedProperties.map((property) => (
            <motion.div
              key={property.id}
              layout
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ duration: 0.2 }}
            >
              <PropertyCard property={property} view={viewMode} onDelete={handleDeleteClick} />
            </motion.div>
          ))}
        </AnimatePresence>
      </motion.div>

      {/* Empty State */}
      {filteredAndSortedProperties.length === 0 && (
        <motion.div
          variants={staggerItem}
          className="text-center py-16"
        >
          <Building2 className="h-12 w-12 text-[var(--color-text-muted)] mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-2">
            {properties.length === 0 ? 'No properties yet' : 'No properties found'}
          </h3>
          <p className="text-[var(--color-text-muted)] mb-4">
            {properties.length === 0
              ? 'Upload documents to create properties automatically'
              : 'Try adjusting your search or filters'}
          </p>
          {properties.length === 0 ? (
            <Link href="/documents">
              <Button variant="primary">Upload Documents</Button>
            </Link>
          ) : (
            <Button variant="secondary" onClick={clearFilters}>
              Clear all filters
            </Button>
          )}
        </motion.div>
      )}

      {/* Delete Confirmation Modal */}
      <AnimatePresence>
        {propertyToDelete && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
            onClick={handleDeleteCancel}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className={cn(
                'bg-[var(--color-surface)] rounded-2xl shadow-xl',
                'max-w-md w-full overflow-hidden'
              )}
              onClick={(e) => e.stopPropagation()}
            >
              {/* Modal Header */}
              <div className="p-6 border-b border-[var(--color-border-subtle)]">
                <div className="flex items-center gap-3">
                  <div className="p-3 rounded-full bg-[var(--color-critical-50)] dark:bg-[var(--color-critical-500)]/20">
                    <Trash2 className="h-5 w-5 text-[var(--color-critical-500)]" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-[var(--color-text-primary)]">
                      Delete Property
                    </h3>
                    <p className="text-sm text-[var(--color-text-muted)]">
                      This action cannot be undone
                    </p>
                  </div>
                </div>
              </div>

              {/* Modal Body */}
              <div className="p-6">
                <p className="text-[var(--color-text-secondary)] mb-4">
                  Are you sure you want to delete <span className="font-semibold text-[var(--color-text-primary)]">{propertyToDelete.name}</span>?
                </p>
                <p className="text-sm text-[var(--color-text-muted)]">
                  This will permanently remove the property and all associated data including:
                </p>
                <ul className="mt-2 text-sm text-[var(--color-text-muted)] list-disc list-inside space-y-1">
                  <li>All uploaded documents</li>
                  <li>Coverage gaps and analysis</li>
                  <li>Insurance policies and programs</li>
                  <li>Compliance records</li>
                </ul>

                {deleteError && (
                  <div className="mt-4 p-3 rounded-lg bg-[var(--color-critical-50)] dark:bg-[var(--color-critical-500)]/10 border border-[var(--color-critical-200)] dark:border-[var(--color-critical-500)]/30">
                    <p className="text-sm text-[var(--color-critical-600)] dark:text-[var(--color-critical-400)]">
                      {deleteError}
                    </p>
                  </div>
                )}
              </div>

              {/* Modal Footer */}
              <div className="p-6 border-t border-[var(--color-border-subtle)] flex items-center justify-end gap-3">
                <Button
                  variant="secondary"
                  onClick={handleDeleteCancel}
                  disabled={isDeleting}
                >
                  Cancel
                </Button>
                <Button
                  variant="primary"
                  onClick={handleDeleteConfirm}
                  disabled={isDeleting}
                  className="bg-[var(--color-critical-500)] hover:bg-[var(--color-critical-600)]"
                  leftIcon={isDeleting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
                >
                  {isDeleting ? 'Deleting...' : 'Delete Property'}
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Reset All Data Confirmation Modal */}
      <AnimatePresence>
        {showResetModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
            onClick={handleResetCancel}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className={cn(
                'bg-[var(--color-surface)] rounded-2xl shadow-xl',
                'max-w-lg w-full overflow-hidden'
              )}
              onClick={(e) => e.stopPropagation()}
            >
              {/* Modal Header */}
              <div className="p-6 border-b border-[var(--color-border-subtle)]">
                <div className="flex items-center gap-3">
                  <div className="p-3 rounded-full bg-[var(--color-critical-50)] dark:bg-[var(--color-critical-500)]/20">
                    <Trash2 className="h-5 w-5 text-[var(--color-critical-500)]" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-[var(--color-text-primary)]">
                      Reset All Data
                    </h3>
                    <p className="text-sm text-[var(--color-text-muted)]">
                      This action is irreversible
                    </p>
                  </div>
                </div>
              </div>

              {/* Modal Body */}
              <div className="p-6">
                {resetResult ? (
                  // Show success result
                  <div className="space-y-4">
                    <div className="p-4 rounded-lg bg-[var(--color-success-50)] dark:bg-[var(--color-success-500)]/10 border border-[var(--color-success-200)] dark:border-[var(--color-success-500)]/30">
                      <p className="text-sm font-medium text-[var(--color-success-600)] dark:text-[var(--color-success-400)]">
                        {resetResult.message}
                      </p>
                    </div>
                    <div className="text-sm text-[var(--color-text-secondary)]">
                      <p><strong>Tables cleared:</strong> {resetResult.tables_cleared.length}</p>
                      <p><strong>Vectors deleted:</strong> {resetResult.vectors_deleted ? 'Yes' : 'No'}</p>
                      {resetResult.vector_count_before !== null && (
                        <p><strong>Vectors removed:</strong> {resetResult.vector_count_before}</p>
                      )}
                    </div>
                  </div>
                ) : (
                  // Show warning before reset
                  <>
                    <div className="p-4 rounded-lg bg-[var(--color-warning-50)] dark:bg-[var(--color-warning-500)]/10 border border-[var(--color-warning-200)] dark:border-[var(--color-warning-500)]/30 mb-4">
                      <p className="text-sm font-medium text-[var(--color-warning-600)] dark:text-[var(--color-warning-400)]">
                        Warning: This will permanently delete ALL data!
                      </p>
                    </div>
                    <p className="text-[var(--color-text-secondary)] mb-4">
                      Are you sure you want to reset the entire system? This will permanently remove:
                    </p>
                    <ul className="text-sm text-[var(--color-text-muted)] list-disc list-inside space-y-1 mb-4">
                      <li>All properties and buildings</li>
                      <li>All uploaded documents</li>
                      <li>All insurance policies and coverages</li>
                      <li>All valuations and certificates</li>
                      <li>All coverage gaps and analysis</li>
                      <li>All chat conversations</li>
                      <li>All vector embeddings (RAG search data)</li>
                    </ul>
                    <p className="text-sm text-[var(--color-text-muted)]">
                      After reset, you can re-upload documents to start fresh with the new extraction features.
                    </p>
                  </>
                )}

                {resetError && (
                  <div className="mt-4 p-3 rounded-lg bg-[var(--color-critical-50)] dark:bg-[var(--color-critical-500)]/10 border border-[var(--color-critical-200)] dark:border-[var(--color-critical-500)]/30">
                    <p className="text-sm text-[var(--color-critical-600)] dark:text-[var(--color-critical-400)]">
                      {resetError}
                    </p>
                  </div>
                )}
              </div>

              {/* Modal Footer */}
              <div className="p-6 border-t border-[var(--color-border-subtle)] flex items-center justify-end gap-3">
                <Button
                  variant="secondary"
                  onClick={handleResetCancel}
                  disabled={isResetting}
                >
                  {resetResult ? 'Close' : 'Cancel'}
                </Button>
                {!resetResult && (
                  <Button
                    variant="primary"
                    onClick={handleResetConfirm}
                    disabled={isResetting}
                    className="bg-[var(--color-critical-500)] hover:bg-[var(--color-critical-600)]"
                    leftIcon={isResetting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
                  >
                    {isResetting ? 'Resetting...' : 'Reset All Data'}
                  </Button>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
