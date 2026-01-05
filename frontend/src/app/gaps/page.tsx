'use client';

import { useState, useMemo, useCallback, useEffect, Suspense } from 'react';
import { motion } from 'framer-motion';
import { useSearchParams } from 'next/navigation';
import {
  RefreshCw,
  Download,
  Play,
  Loader2,
  AlertTriangle,
} from 'lucide-react';
import { Button, Card } from '@/components/primitives';
import { GapList, GapDetailModal, GapStats } from '@/components/features/gaps';
import { staggerContainer, staggerItem } from '@/lib/motion/variants';
import { gapsApi, propertiesApi, type Gap, type Property } from '@/lib/api';

function GapsPageContent() {
  const searchParams = useSearchParams();
  const propertyFilter = searchParams.get('property_id') || searchParams.get('property') || undefined;

  const [selectedGap, setSelectedGap] = useState<Gap | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [gaps, setGaps] = useState<Gap[]>([]);
  const [properties, setProperties] = useState<Property[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDetecting, setIsDetecting] = useState(false);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [gapsData, propertiesData] = await Promise.all([
        gapsApi.list(undefined, propertyFilter ? { property_id: propertyFilter } : undefined),
        propertiesApi.list(),
      ]);
      // Handle various API response formats
      setGaps(
        Array.isArray(gapsData) ? gapsData :
        (gapsData as { gaps?: Gap[]; items?: Gap[] })?.gaps ||
        (gapsData as { items?: Gap[] })?.items || []
      );
      setProperties(
        Array.isArray(propertiesData) ? propertiesData :
        (propertiesData as { properties?: Property[]; items?: Property[] })?.properties ||
        (propertiesData as { items?: Property[] })?.items || []
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load gaps');
    } finally {
      setIsLoading(false);
    }
  }, [propertyFilter]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Get property name for filter display
  const filteredProperty = propertyFilter
    ? properties.find((p) => p.id === propertyFilter)
    : null;

  const handleGapClick = useCallback((gap: Gap) => {
    setSelectedGap(gap);
    setIsModalOpen(true);
  }, []);

  const handleCloseModal = useCallback(() => {
    setIsModalOpen(false);
    setSelectedGap(null);
  }, []);

  const handleAcknowledge = useCallback(async (gapId: string, notes: string) => {
    try {
      const updatedGap = await gapsApi.acknowledge(gapId, notes);
      setGaps((prev) => prev.map((g) => (g.id === gapId ? updatedGap : g)));
      setSelectedGap((prev) => (prev?.id === gapId ? updatedGap : prev));
    } catch (err) {
      console.error('Failed to acknowledge gap:', err);
    }
  }, []);

  const handleResolve = useCallback(async (gapId: string, notes: string) => {
    try {
      const updatedGap = await gapsApi.resolve(gapId, notes);
      setGaps((prev) => prev.map((g) => (g.id === gapId ? updatedGap : g)));
      setIsModalOpen(false);
      setSelectedGap(null);
    } catch (err) {
      console.error('Failed to resolve gap:', err);
    }
  }, []);

  const handleRunDetection = useCallback(async () => {
    if (!propertyFilter) return;
    setIsDetecting(true);
    try {
      const newGaps = await gapsApi.detect(propertyFilter);
      setGaps((prev) => [...prev.filter((g) => g.property_id !== propertyFilter), ...newGaps]);
    } catch (err) {
      console.error('Failed to detect gaps:', err);
    } finally {
      setIsDetecting(false);
    }
  }, [propertyFilter]);

  const filteredGaps = useMemo(() => {
    if (propertyFilter) {
      return gaps.filter((g) => g.property_id === propertyFilter);
    }
    return gaps;
  }, [gaps, propertyFilter]);

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
          Failed to load gaps
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
      className="space-y-8"
    >
      {/* Header */}
      <motion.div variants={staggerItem} className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">
              Coverage Gaps
            </h1>
            {filteredProperty && (
              <span className="px-3 py-1 rounded-full bg-[var(--color-primary-50)] text-[var(--color-primary-600)] text-sm font-medium">
                {filteredProperty.name}
              </span>
            )}
          </div>
          <p className="text-[var(--color-text-secondary)] mt-1">
            {filteredProperty
              ? `Viewing gaps for ${filteredProperty.name}`
              : 'Monitor and resolve insurance coverage gaps across your portfolio'}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={fetchData}>
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Button
            variant="secondary"
            leftIcon={<Download className="h-4 w-4" />}
          >
            Export
          </Button>
          {propertyFilter && (
            <Button
              variant="primary"
              leftIcon={isDetecting ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
              onClick={handleRunDetection}
              disabled={isDetecting}
            >
              {isDetecting ? 'Detecting...' : 'Run Detection'}
            </Button>
          )}
        </div>
      </motion.div>

      {/* Stats */}
      <motion.div variants={staggerItem}>
        <GapStats gaps={filteredGaps} />
      </motion.div>

      {/* Gap List */}
      <motion.div variants={staggerItem}>
        <Card padding="lg">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">
              All Gaps
            </h2>
            <span className="text-sm text-[var(--color-text-muted)]">
              {filteredGaps.length} gap{filteredGaps.length !== 1 ? 's' : ''} found
            </span>
          </div>
          <GapList
            gaps={filteredGaps}
            onGapClick={handleGapClick}
            showFilters
          />
        </Card>
      </motion.div>

      {/* Gap Detail Modal */}
      <GapDetailModal
        gap={selectedGap}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        onAcknowledge={handleAcknowledge}
        onResolve={handleResolve}
      />
    </motion.div>
  );
}

export default function GapsPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 text-[var(--color-primary-500)] animate-spin" />
      </div>
    }>
      <GapsPageContent />
    </Suspense>
  );
}
