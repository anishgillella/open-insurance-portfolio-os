'use client';

import { useState, useMemo, useCallback, Suspense } from 'react';
import { motion } from 'framer-motion';
import { useSearchParams } from 'next/navigation';
import {
  RefreshCw,
  Download,
  Play,
} from 'lucide-react';
import { Button, Card } from '@/components/primitives';
import { GapList, GapDetailModal, GapStats } from '@/components/features/gaps';
import { staggerContainer, staggerItem } from '@/lib/motion/variants';
import { mockGaps, mockProperties } from '@/lib/mock-data';
import type { Gap } from '@/types/api';

function GapsPageContent() {
  const searchParams = useSearchParams();
  const propertyFilter = searchParams.get('property') || undefined;

  const [selectedGap, setSelectedGap] = useState<Gap | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [gaps, setGaps] = useState<Gap[]>(mockGaps);
  const [isDetecting, setIsDetecting] = useState(false);

  // Get property name for filter display
  const filteredProperty = propertyFilter
    ? mockProperties.find((p) => p.id === propertyFilter)
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
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 500));
    setGaps((prev) =>
      prev.map((g) =>
        g.id === gapId
          ? {
              ...g,
              status: 'acknowledged' as const,
              acknowledged_by: 'Current User',
              acknowledged_at: new Date().toISOString(),
            }
          : g
      )
    );
    setSelectedGap((prev) =>
      prev?.id === gapId
        ? {
            ...prev,
            status: 'acknowledged' as const,
            acknowledged_by: 'Current User',
            acknowledged_at: new Date().toISOString(),
          }
        : prev
    );
  }, []);

  const handleResolve = useCallback(async (gapId: string, notes: string) => {
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 500));
    setGaps((prev) =>
      prev.map((g) =>
        g.id === gapId
          ? {
              ...g,
              status: 'resolved' as const,
              resolved_by: 'Current User',
              resolved_at: new Date().toISOString(),
              resolution_notes: notes || undefined,
            }
          : g
      )
    );
  }, []);

  const handleRunDetection = useCallback(async () => {
    setIsDetecting(true);
    // Simulate gap detection
    await new Promise((resolve) => setTimeout(resolve, 2000));
    setIsDetecting(false);
  }, []);

  const filteredGaps = useMemo(() => {
    if (propertyFilter) {
      return gaps.filter((g) => g.property_id === propertyFilter);
    }
    return gaps;
  }, [gaps, propertyFilter]);

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
          <Button
            variant="secondary"
            leftIcon={<Download className="h-4 w-4" />}
          >
            Export
          </Button>
          <Button
            variant="primary"
            leftIcon={isDetecting ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
            onClick={handleRunDetection}
            disabled={isDetecting}
          >
            {isDetecting ? 'Detecting...' : 'Run Detection'}
          </Button>
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
    <Suspense fallback={<div className="animate-pulse p-8">Loading gaps...</div>}>
      <GapsPageContent />
    </Suspense>
  );
}
