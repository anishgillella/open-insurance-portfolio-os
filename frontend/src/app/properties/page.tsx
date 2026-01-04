'use client';

import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
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
} from 'lucide-react';
import { cn, getGrade } from '@/lib/utils';
import { Button, Badge, Card } from '@/components/primitives';
import { PropertyCard } from '@/components/features/properties';
import { mockProperties, mockDashboardSummary } from '@/lib/mock-data';
import { staggerContainer, staggerItem } from '@/lib/motion/variants';

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

  const filteredAndSortedProperties = useMemo(() => {
    let result = [...mockProperties];

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
          comparison = a.total_insured_value - b.total_insured_value;
          break;
        case 'premium':
          comparison = a.total_premium - b.total_premium;
          break;
        case 'expiration':
          comparison = (a.days_until_expiration || 999) - (b.days_until_expiration || 999);
          break;
      }
      return sortDirection === 'asc' ? comparison : -comparison;
    });

    return result;
  }, [searchQuery, sortBy, sortDirection, filterGrade, filterExpiration]);

  const hasActiveFilters = filterGrade !== 'all' || filterExpiration !== 'all';

  const clearFilters = () => {
    setFilterGrade('all');
    setFilterExpiration('all');
    setSearchQuery('');
  };

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
            Manage your portfolio of {mockDashboardSummary.totalProperties} properties
          </p>
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
              {mockDashboardSummary.totalProperties}
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
              {mockDashboardSummary.propertiesWithGaps}
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
              {mockDashboardSummary.expiringIn30Days}
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
              {mockDashboardSummary.totalGaps}
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
              // Toggle sort direction on same field, or reset to asc on new field
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
          Showing {filteredAndSortedProperties.length} of {mockProperties.length} properties
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
              <PropertyCard property={property} view={viewMode} />
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
            No properties found
          </h3>
          <p className="text-[var(--color-text-muted)] mb-4">
            Try adjusting your search or filters
          </p>
          <Button variant="secondary" onClick={clearFilters}>
            Clear all filters
          </Button>
        </motion.div>
      )}
    </motion.div>
  );
}
