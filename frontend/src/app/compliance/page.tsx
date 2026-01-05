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
  Play,
  Loader2,
  AlertTriangle,
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
  complianceApi,
  propertiesApi,
  type ComplianceResult,
  type ComplianceTemplate,
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

  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [selectedPropertyCompliance, setSelectedPropertyCompliance] = useState<ComplianceResult | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isChecking, setIsChecking] = useState(false);

  const [properties, setProperties] = useState<Property[]>([]);
  const [templates, setTemplates] = useState<ComplianceTemplate[]>([]);
  const [complianceResults, setComplianceResults] = useState<Map<string, ComplianceResult>>(new Map());
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [propertiesData, templatesData] = await Promise.all([
        propertiesApi.list(),
        complianceApi.listTemplates(),
      ]);
      // Handle various API response formats
      const propsArray = Array.isArray(propertiesData) ? propertiesData :
        (propertiesData as { properties?: Property[]; items?: Property[] })?.properties ||
        (propertiesData as { items?: Property[] })?.items || [];
      const templatesArray = Array.isArray(templatesData) ? templatesData :
        (templatesData as { templates?: ComplianceTemplate[]; items?: ComplianceTemplate[] })?.templates ||
        (templatesData as { items?: ComplianceTemplate[] })?.items || [];
      setProperties(propsArray);
      setTemplates(templatesArray);
      if (templatesArray.length > 0) {
        setSelectedTemplate(templatesArray[0].id);
      }

      // Fetch compliance for each property
      const results = new Map<string, ComplianceResult>();
      const filteredProps = propertyFilter
        ? propsArray.filter((p) => p.id === propertyFilter)
        : propsArray;

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
      setComplianceResults(results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load compliance data');
    } finally {
      setIsLoading(false);
    }
  }, [propertyFilter]);

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
      (sum, s) => sum + s.checks.filter((c) => c.status === 'fail').length,
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

  const handleRunCheck = useCallback(async () => {
    if (!selectedTemplate) return;
    setIsChecking(true);
    try {
      const filteredProps = propertyFilter
        ? properties.filter((p) => p.id === propertyFilter)
        : properties;

      const newResults = new Map(complianceResults);
      await Promise.all(
        filteredProps.map(async (property) => {
          try {
            const result = await complianceApi.checkCompliance(property.id, selectedTemplate);
            newResults.set(property.id, result);
          } catch {
            // Skip properties that fail
          }
        })
      );
      setComplianceResults(newResults);
    } catch (err) {
      console.error('Failed to run compliance check:', err);
    } finally {
      setIsChecking(false);
    }
  }, [properties, propertyFilter, selectedTemplate, complianceResults]);

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
          <Button
            variant="primary"
            leftIcon={isChecking ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
            onClick={handleRunCheck}
            disabled={isChecking || !selectedTemplate}
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
          {/* Coverage Shield */}
          <Card padding="lg">
            <h2 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">
              Coverage Overview
            </h2>
            <div className="flex justify-center">
              <CoverageShield coverages={coverageTypes} size={300} />
            </div>
          </Card>

          {/* Template Selector (compact) */}
          <Card padding="lg">
            <h2 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4">
              Compliance Template
            </h2>
            <div className="space-y-3">
              {templates.map((template) => (
                <button
                  key={template.id}
                  onClick={() => setSelectedTemplate(template.id)}
                  className={`w-full flex items-center gap-3 p-3 rounded-lg transition-all border ${
                    selectedTemplate === template.id
                      ? 'border-[var(--color-primary-500)] bg-[var(--color-primary-50)]'
                      : 'border-[var(--color-border-subtle)] hover:border-[var(--color-border-default)]'
                  }`}
                >
                  <div
                    className={`w-3 h-3 rounded-full ${
                      selectedTemplate === template.id
                        ? 'bg-[var(--color-primary-500)]'
                        : 'bg-[var(--color-border-default)]'
                    }`}
                  />
                  <div className="flex-1 text-left">
                    <p className="font-medium text-[var(--color-text-primary)]">
                      {template.name}
                    </p>
                    <p className="text-xs text-[var(--color-text-muted)]">
                      {template.lender_name}
                    </p>
                  </div>
                  {selectedTemplate === template.id && (
                    <Badge variant="primary" size="sm">Active</Badge>
                  )}
                </button>
              ))}
              {templates.length === 0 && (
                <p className="text-sm text-[var(--color-text-muted)] text-center py-4">
                  No compliance templates available
                </p>
              )}
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
                            {status.checks.filter((c) => c.status === 'pass').length}/
                            {status.checks.filter((c) => c.status !== 'not_applicable').length} passed
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
                  {selectedPropertyCompliance.checks.map((check, index) => (
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
