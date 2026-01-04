'use client';

import { useState, useMemo, useCallback, Suspense } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSearchParams } from 'next/navigation';
import {
  CheckCircle,
  XCircle,
  AlertCircle,
  RefreshCw,
  Download,
  Building2,
  ChevronRight,
  Play,
} from 'lucide-react';
import { Button, Card, Badge } from '@/components/primitives';
import { DataCard } from '@/components/patterns';
import {
  ComplianceStatusCard,
  ComplianceChecklist,
  TemplateSelector,
} from '@/components/features/compliance';
import { CoverageShield } from '@/components/three';
import { staggerContainer, staggerItem, modalOverlay, modalContent } from '@/lib/motion/variants';
import {
  mockComplianceStatuses,
  mockComplianceTemplates,
  mockProperties,
  mockCoverageTypes,
} from '@/lib/mock-data';
import type { ComplianceStatus } from '@/types/api';

function CompliancePageContent() {
  const searchParams = useSearchParams();
  const propertyFilter = searchParams.get('property') || undefined;

  const [selectedTemplate, setSelectedTemplate] = useState<string>('standard');
  const [selectedProperty, setSelectedProperty] = useState<ComplianceStatus | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isChecking, setIsChecking] = useState(false);

  // Filter statuses by property if filter is provided
  const filteredStatuses = useMemo(() => {
    if (propertyFilter) {
      return mockComplianceStatuses.filter((s) => s.property_id === propertyFilter);
    }
    return mockComplianceStatuses;
  }, [propertyFilter]);

  // Calculate summary stats
  const stats = useMemo(() => {
    const compliant = filteredStatuses.filter((s) => s.is_compliant).length;
    const nonCompliant = filteredStatuses.filter((s) => !s.is_compliant).length;
    const totalIssues = filteredStatuses.reduce(
      (sum, s) => sum + s.checks.filter((c) => c.status === 'fail').length,
      0
    );
    const propertiesChecked = filteredStatuses.length;

    return { compliant, nonCompliant, totalIssues, propertiesChecked };
  }, [filteredStatuses]);

  const handlePropertyClick = useCallback((status: ComplianceStatus) => {
    setSelectedProperty(status);
    setIsModalOpen(true);
  }, []);

  const handleCloseModal = useCallback(() => {
    setIsModalOpen(false);
    setSelectedProperty(null);
  }, []);

  const handleRunCheck = useCallback(async () => {
    setIsChecking(true);
    // Simulate compliance check
    await new Promise((resolve) => setTimeout(resolve, 2000));
    setIsChecking(false);
  }, []);

  // Get property name for filter display
  const filteredPropertyName = propertyFilter
    ? mockProperties.find((p) => p.id === propertyFilter)?.name
    : null;

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
              Compliance
            </h1>
            {filteredPropertyName && (
              <span className="px-3 py-1 rounded-full bg-[var(--color-primary-50)] text-[var(--color-primary-600)] text-sm font-medium">
                {filteredPropertyName}
              </span>
            )}
          </div>
          <p className="text-[var(--color-text-secondary)] mt-1">
            Monitor lender compliance requirements across your portfolio
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="secondary"
            leftIcon={<Download className="h-4 w-4" />}
          >
            Export Report
          </Button>
          <Button
            variant="primary"
            leftIcon={isChecking ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
            onClick={handleRunCheck}
            disabled={isChecking}
          >
            {isChecking ? 'Checking...' : 'Run Check'}
          </Button>
        </div>
      </motion.div>

      {/* Stats */}
      <motion.div variants={staggerItem} className="grid grid-cols-2 md:grid-cols-4 gap-6">
        <DataCard
          label="Compliant"
          value={stats.compliant}
          icon={<CheckCircle className="h-5 w-5" />}
          trend={{ value: stats.compliant, direction: 'up', period: 'properties' }}
        />
        <DataCard
          label="Non-Compliant"
          value={stats.nonCompliant}
          icon={<XCircle className="h-5 w-5" />}
          trend={{
            value: stats.nonCompliant,
            direction: stats.nonCompliant > 0 ? 'down' : 'up',
            period: 'properties',
          }}
        />
        <DataCard
          label="Total Issues"
          value={stats.totalIssues}
          icon={<AlertCircle className="h-5 w-5" />}
        />
        <DataCard
          label="Properties Checked"
          value={stats.propertiesChecked}
          icon={<Building2 className="h-5 w-5" />}
        />
      </motion.div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Templates & Shield */}
        <motion.div variants={staggerItem} className="lg:col-span-1 space-y-6">
          {/* Coverage Shield */}
          <Card padding="lg">
            <h2 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">
              Coverage Overview
            </h2>
            <div className="flex justify-center">
              <CoverageShield coverages={mockCoverageTypes} size={300} />
            </div>
          </Card>

          {/* Template Selector (compact) */}
          <Card padding="lg">
            <h2 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">
              Active Template
            </h2>
            <div className="space-y-3">
              {mockComplianceTemplates.map((template) => (
                <button
                  key={template.name}
                  onClick={() => setSelectedTemplate(template.name)}
                  className={`w-full flex items-center gap-3 p-3 rounded-lg transition-all border ${
                    selectedTemplate === template.name
                      ? 'border-[var(--color-primary-500)] bg-[var(--color-primary-50)]'
                      : 'border-[var(--color-border-subtle)] hover:border-[var(--color-border-default)]'
                  }`}
                >
                  <div
                    className={`w-3 h-3 rounded-full ${
                      selectedTemplate === template.name
                        ? 'bg-[var(--color-primary-500)]'
                        : 'bg-[var(--color-border-default)]'
                    }`}
                  />
                  <div className="flex-1 text-left">
                    <p className="font-medium text-[var(--color-text-primary)]">
                      {template.display_name}
                    </p>
                    <p className="text-xs text-[var(--color-text-muted)]">
                      {template.description}
                    </p>
                  </div>
                  {selectedTemplate === template.name && (
                    <Badge variant="primary" size="sm">Active</Badge>
                  )}
                </button>
              ))}
            </div>
          </Card>
        </motion.div>

        {/* Right Column - Property Compliance List */}
        <motion.div variants={staggerItem} className="lg:col-span-2">
          <Card padding="lg">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">
                Property Compliance Status
              </h2>
              <Badge variant="secondary">
                {filteredStatuses.length} properties
              </Badge>
            </div>

            {filteredStatuses.length === 0 ? (
              <div className="text-center py-8">
                <Building2 className="h-12 w-12 text-[var(--color-text-muted)] mx-auto mb-4" />
                <h3 className="text-lg font-medium text-[var(--color-text-primary)] mb-2">
                  No compliance data
                </h3>
                <p className="text-[var(--color-text-secondary)]">
                  Run a compliance check to see property status
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {filteredStatuses.map((status) => {
                  const property = mockProperties.find((p) => p.id === status.property_id);
                  return (
                    <div
                      key={status.property_id}
                      className="flex items-center gap-4 p-4 rounded-xl border border-[var(--color-border-subtle)] hover:border-[var(--color-border-default)] hover:shadow-[var(--shadow-elevation-1)] transition-all cursor-pointer"
                      onClick={() => handlePropertyClick(status)}
                    >
                      {/* Status Icon */}
                      <div
                        className={`p-2 rounded-lg ${
                          status.is_compliant
                            ? 'bg-[var(--color-success-50)]'
                            : 'bg-[var(--color-critical-50)]'
                        }`}
                      >
                        {status.is_compliant ? (
                          <CheckCircle className="h-5 w-5 text-[var(--color-success-500)]" />
                        ) : (
                          <XCircle className="h-5 w-5 text-[var(--color-critical-500)]" />
                        )}
                      </div>

                      {/* Property Info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold text-[var(--color-text-primary)]">
                            {property?.name || 'Unknown Property'}
                          </h3>
                          <Badge
                            variant={status.is_compliant ? 'success' : 'critical'}
                            size="sm"
                          >
                            {status.is_compliant ? 'Compliant' : 'Non-Compliant'}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-[var(--color-text-muted)]">
                          <span>{status.lender_name || 'No lender'}</span>
                          <span>•</span>
                          <span>{status.template_used}</span>
                          <span>•</span>
                          <span>
                            {status.checks.filter((c) => c.status === 'pass').length}/
                            {status.checks.filter((c) => c.status !== 'not_required').length} passed
                          </span>
                        </div>
                      </div>

                      {/* Issues count if any */}
                      {!status.is_compliant && (
                        <Badge variant="critical">
                          {status.checks.filter((c) => c.status === 'fail').length} issues
                        </Badge>
                      )}

                      <ChevronRight className="h-5 w-5 text-[var(--color-text-muted)]" />
                    </div>
                  );
                })}
              </div>
            )}
          </Card>
        </motion.div>
      </div>

      {/* Compliance Detail Modal */}
      <AnimatePresence>
        {isModalOpen && selectedProperty && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            {/* Backdrop */}
            <motion.div
              variants={modalOverlay}
              initial="initial"
              animate="animate"
              exit="exit"
              className="absolute inset-0 bg-black/50 backdrop-blur-sm"
              onClick={handleCloseModal}
            />

            {/* Modal */}
            <motion.div
              variants={modalContent}
              initial="initial"
              animate="animate"
              exit="exit"
              className="relative w-full max-w-2xl max-h-[90vh] overflow-hidden rounded-2xl bg-[var(--color-surface)] shadow-[var(--shadow-elevation-4)]"
            >
              {/* Header */}
              <div className="sticky top-0 z-10 bg-[var(--color-surface)] border-b border-[var(--color-border-subtle)] p-6">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <h2 className="text-xl font-bold text-[var(--color-text-primary)]">
                        {mockProperties.find((p) => p.id === selectedProperty.property_id)?.name}
                      </h2>
                      <Badge
                        variant={selectedProperty.is_compliant ? 'success' : 'critical'}
                      >
                        {selectedProperty.is_compliant ? 'Compliant' : 'Non-Compliant'}
                      </Badge>
                    </div>
                    <p className="text-sm text-[var(--color-text-muted)]">
                      {selectedProperty.lender_name} • {selectedProperty.loan_number}
                    </p>
                  </div>
                  <button
                    onClick={handleCloseModal}
                    className="p-2 rounded-lg hover:bg-[var(--color-surface-sunken)] transition-colors"
                  >
                    ×
                  </button>
                </div>
              </div>

              {/* Content */}
              <div className="overflow-y-auto p-6" style={{ maxHeight: 'calc(90vh - 120px)' }}>
                <ComplianceChecklist status={selectedProperty} showHeader={false} />
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export default function CompliancePage() {
  return (
    <Suspense fallback={<div className="animate-pulse p-8">Loading compliance...</div>}>
      <CompliancePageContent />
    </Suspense>
  );
}
