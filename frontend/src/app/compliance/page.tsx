'use client';

import { useState, useMemo, useCallback, useEffect, Suspense } from 'react';
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
  Loader2,
  AlertTriangle,
} from 'lucide-react';
import { Button, Card, Badge } from '@/components/primitives';
import { DataCard } from '@/components/patterns';
import {
  ComplianceStatusCard,
  ComplianceChecklist,
  CoverageOverview,
} from '@/components/features/compliance';
import { staggerContainer, staggerItem, modalOverlay, modalContent } from '@/lib/motion/variants';
import {
  complianceApi,
  propertiesApi,
  type ComplianceResult,
  type Property,
} from '@/lib/api';

// Static coverage types for the shield visualization
const coverageTypes = [
  { name: 'Property', color: '#3b82f6', adequacy: 95 },
  { name: 'General Liability', color: '#22c55e', adequacy: 88 },
  { name: 'Umbrella', color: '#8b5cf6', adequacy: 75 },
  { name: 'Workers Comp', color: '#f59e0b', adequacy: 100 },
  { name: 'Flood', color: '#ef4444', adequacy: 0 },
  { name: 'Earthquake', color: '#6b7280', adequacy: 0 },
];

function CompliancePageContent() {
  const searchParams = useSearchParams();
  const propertyFilter = searchParams.get('property_id') || searchParams.get('property') || undefined;

  const [selectedPropertyCompliance, setSelectedPropertyCompliance] = useState<ComplianceResult | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const [properties, setProperties] = useState<Property[]>([]);
  const [complianceResults, setComplianceResults] = useState<Map<string, ComplianceResult>>(new Map());
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingCompliance, setIsLoadingCompliance] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Helper to fetch compliance data for properties
  const fetchComplianceData = useCallback(async (propsArray: Property[]) => {
    const filteredProps = propertyFilter
      ? propsArray.filter((p) => p.id === propertyFilter)
      : propsArray;

    if (filteredProps.length === 0) return;

    setIsLoadingCompliance(true);
    const results = new Map<string, ComplianceResult>();

    try {
      const batchResponse = await complianceApi.batchCheckCompliance(
        filteredProps.map((p) => p.id)
      );
      // Convert batch response to the format expected by the component
      for (const item of batchResponse.results) {
        if (item.compliance_checks.length > 0) {
          // Use the first compliance check as the main result
          const mainCheck = item.compliance_checks[0];
          // Map issues to checks format expected by the UI
          const checks = (mainCheck.issues || []).map((issue) => ({
            requirement: issue.check_name || issue.message,
            status: issue.severity === 'critical' || issue.severity === 'warning' ? 'fail' as const : 'pass' as const,
            current_value: issue.current_value,
            required_value: issue.required_value,
          }));
          results.set(item.property_id, {
            property_id: item.property_id,
            property_name: item.property_name,
            template_id: mainCheck.template_name || '',
            template_name: mainCheck.template_name || 'Default',
            lender_name: mainCheck.lender_name || '',
            is_compliant: mainCheck.is_compliant,
            checks,
            last_checked: mainCheck.checked_at || new Date().toISOString(),
          });
        } else {
          // No compliance checks - show as compliant with no checks
          results.set(item.property_id, {
            property_id: item.property_id,
            property_name: item.property_name,
            template_id: '',
            template_name: 'No Requirements',
            lender_name: '',
            is_compliant: true,
            checks: [],
            last_checked: new Date().toISOString(),
          });
        }
      }
    } catch {
      // Fall back to individual calls if batch fails
      await Promise.all(
        filteredProps.map(async (property) => {
          try {
            const result = await complianceApi.getPropertyCompliance(property.id);
            results.set(property.id, result);
          } catch {
            // Property may not have compliance data yet
          }
        })
      );
    }

    setComplianceResults(results);
    setIsLoadingCompliance(false);
  }, [propertyFilter]);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      // Show page immediately
      setIsLoading(false);

      // Load properties (can be slow due to remote DB)
      const propertiesData = await propertiesApi.list();
      const propsArray = Array.isArray(propertiesData) ? propertiesData :
        (propertiesData as { properties?: Property[]; items?: Property[] })?.properties ||
        (propertiesData as { items?: Property[] })?.items || [];
      setProperties(propsArray);

      // Load compliance data in background (slowest)
      fetchComplianceData(propsArray);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load compliance data');
      setIsLoading(false);
    }
  }, [fetchComplianceData]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Filter statuses by property if filter is provided
  const filteredStatuses = useMemo(() => {
    const results = Array.from(complianceResults.values());
    if (propertyFilter) {
      return results.filter((s) => s.property_id === propertyFilter);
    }
    return results;
  }, [complianceResults, propertyFilter]);

  // Calculate summary stats
  const stats = useMemo(() => {
    const compliant = filteredStatuses.filter((s) => s.is_compliant).length;
    const nonCompliant = filteredStatuses.filter((s) => !s.is_compliant).length;
    const totalIssues = filteredStatuses.reduce(
      (sum, s) => sum + (s.checks || []).filter((c) => c.status === 'fail').length,
      0
    );
    const propertiesChecked = filteredStatuses.length;

    return { compliant, nonCompliant, totalIssues, propertiesChecked };
  }, [filteredStatuses]);

  const handlePropertyClick = useCallback((result: ComplianceResult) => {
    setSelectedPropertyCompliance(result);
    setIsModalOpen(true);
  }, []);

  const handleCloseModal = useCallback(() => {
    setIsModalOpen(false);
    setSelectedPropertyCompliance(null);
  }, []);

  // Get property name for filter display
  const filteredPropertyName = propertyFilter
    ? properties.find((p) => p.id === propertyFilter)?.name
    : null;

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
          Failed to load compliance data
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
          <Button variant="ghost" size="sm" onClick={fetchData}>
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Button
            variant="secondary"
            leftIcon={<Download className="h-4 w-4" />}
          >
            Export Report
          </Button>
        </div>
      </motion.div>

      {/* Stats */}
      <motion.div variants={staggerItem} className="grid grid-cols-2 md:grid-cols-4 gap-6">
        <DataCard
          label="Compliant"
          value={stats.compliant}
          icon={<CheckCircle className="h-5 w-5" />}
        />
        <DataCard
          label="Non-Compliant"
          value={stats.nonCompliant}
          icon={<XCircle className="h-5 w-5" />}
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
          {/* Coverage Overview */}
          <Card padding="lg">
            <h2 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">
              Coverage Overview
            </h2>
            <CoverageOverview coverages={coverageTypes} />
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

            {isLoadingCompliance ? (
              <div className="flex flex-col items-center justify-center py-12">
                <Loader2 className="h-8 w-8 text-[var(--color-primary-500)] animate-spin mb-4" />
                <p className="text-[var(--color-text-muted)]">Loading compliance data...</p>
              </div>
            ) : filteredStatuses.length === 0 ? (
              <div className="text-center py-8">
                <Building2 className="h-12 w-12 text-[var(--color-text-muted)] mx-auto mb-4" />
                <h3 className="text-lg font-medium text-[var(--color-text-primary)] mb-2">
                  No compliance data
                </h3>
                <p className="text-[var(--color-text-secondary)]">
                  {properties.length === 0
                    ? 'Upload documents to create properties first'
                    : 'Run a compliance check to see property status'}
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {filteredStatuses.map((status) => {
                  const property = properties.find((p) => p.id === status.property_id);
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
                            {property?.name || status.property_name || 'Unknown Property'}
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
                          <span>{status.template_name}</span>
                          <span>•</span>
                          <span>
                            {(status.checks || []).filter((c) => c.status === 'pass').length}/
                            {(status.checks || []).filter((c) => c.status !== 'not_applicable').length} passed
                          </span>
                        </div>
                      </div>

                      {/* Issues count if any */}
                      {!status.is_compliant && (
                        <Badge variant="critical">
                          {(status.checks || []).filter((c) => c.status === 'fail').length} issues
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
        {isModalOpen && selectedPropertyCompliance && (
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
                        {properties.find((p) => p.id === selectedPropertyCompliance.property_id)?.name ||
                          selectedPropertyCompliance.property_name}
                      </h2>
                      <Badge
                        variant={selectedPropertyCompliance.is_compliant ? 'success' : 'critical'}
                      >
                        {selectedPropertyCompliance.is_compliant ? 'Compliant' : 'Non-Compliant'}
                      </Badge>
                    </div>
                    <p className="text-sm text-[var(--color-text-muted)]">
                      {selectedPropertyCompliance.lender_name} • {selectedPropertyCompliance.template_name}
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
                <div className="space-y-4">
                  {(selectedPropertyCompliance.checks || []).map((check, index) => (
                    <div
                      key={index}
                      className={`p-4 rounded-lg border ${
                        check.status === 'pass'
                          ? 'border-[var(--color-success-200)] bg-[var(--color-success-50)]'
                          : check.status === 'fail'
                          ? 'border-[var(--color-critical-200)] bg-[var(--color-critical-50)]'
                          : 'border-[var(--color-border-subtle)] bg-[var(--color-surface-sunken)]'
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        {check.status === 'pass' ? (
                          <CheckCircle className="h-5 w-5 text-[var(--color-success-500)] flex-shrink-0 mt-0.5" />
                        ) : check.status === 'fail' ? (
                          <XCircle className="h-5 w-5 text-[var(--color-critical-500)] flex-shrink-0 mt-0.5" />
                        ) : (
                          <AlertCircle className="h-5 w-5 text-[var(--color-text-muted)] flex-shrink-0 mt-0.5" />
                        )}
                        <div className="flex-1">
                          <p className="font-medium text-[var(--color-text-primary)]">
                            {check.requirement}
                          </p>
                          {(check.current_value || check.required_value) && (
                            <div className="mt-2 text-sm">
                              {check.current_value && (
                                <p className="text-[var(--color-text-muted)]">
                                  Current: <span className="text-[var(--color-text-primary)]">{check.current_value}</span>
                                </p>
                              )}
                              {check.required_value && (
                                <p className="text-[var(--color-text-muted)]">
                                  Required: <span className="text-[var(--color-text-primary)]">{check.required_value}</span>
                                </p>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
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
    <Suspense
      fallback={
        <div className="flex items-center justify-center min-h-[400px]">
          <Loader2 className="h-8 w-8 text-[var(--color-primary-500)] animate-spin" />
        </div>
      }
    >
      <CompliancePageContent />
    </Suspense>
  );
}
