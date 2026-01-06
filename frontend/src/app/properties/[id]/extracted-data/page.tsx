'use client';

import { use, useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import {
  ArrowLeft,
  Building2,
  FileText,
  DollarSign,
  Shield,
  Calendar,
  RefreshCw,
  Loader2,
  ChevronDown,
  ChevronRight,
  AlertCircle,
  CheckCircle2,
  FileCheck,
  Database,
  type LucideIcon,
} from 'lucide-react';
import { cn, formatCurrency } from '@/lib/utils';
import { Button, Card, Badge } from '@/components/primitives';
import { GlassCard } from '@/components/patterns';
import { staggerContainer, staggerItem } from '@/lib/motion/variants';
import {
  propertiesApi,
  type PropertyExtractedDataResponse,
  type ExtractedFieldWithSources,
} from '@/lib/api';

interface PageProps {
  params: Promise<{ id: string }>;
}

// Category icons and colors
const categoryConfig: Record<string, { icon: LucideIcon; color: string; label: string }> = {
  property: { icon: Building2, color: 'text-blue-500', label: 'Property Details' },
  valuation: { icon: DollarSign, color: 'text-green-500', label: 'Valuation' },
  coverage: { icon: Shield, color: 'text-purple-500', label: 'Coverage' },
  policy: { icon: FileText, color: 'text-orange-500', label: 'Policy' },
};

// Format value for display
function formatValue(value: string | number | boolean | null): string {
  if (value === null || value === undefined) return 'N/A';
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  if (typeof value === 'number') {
    // Format large numbers as currency if they look like money
    if (value >= 1000) return formatCurrency(value);
    return value.toLocaleString();
  }
  // Check if it's a string that looks like money
  const numVal = parseFloat(value);
  if (!isNaN(numVal) && numVal >= 1000) {
    return formatCurrency(numVal);
  }
  return String(value);
}

// Format date for display
function formatDate(dateStr: string | null): string {
  if (!dateStr) return 'N/A';
  try {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return dateStr;
  }
}

// Group fields by category
function groupFieldsByCategory(fields: ExtractedFieldWithSources[]): Record<string, ExtractedFieldWithSources[]> {
  return fields.reduce((acc, field) => {
    const category = field.category || 'other';
    if (!acc[category]) acc[category] = [];
    acc[category].push(field);
    return acc;
  }, {} as Record<string, ExtractedFieldWithSources[]>);
}

export default function ExtractedDataPage({ params }: PageProps) {
  const { id } = use(params);

  const [data, setData] = useState<PropertyExtractedDataResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set(['property', 'valuation']));
  const [expandedDocuments, setExpandedDocuments] = useState<Set<string>>(new Set());
  const [activeTab, setActiveTab] = useState<'fields' | 'documents'>('fields');

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const extractedData = await propertiesApi.getExtractedData(id);
      setData(extractedData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load extracted data');
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const toggleCategory = (category: string) => {
    setExpandedCategories((prev) => {
      const next = new Set(prev);
      if (next.has(category)) {
        next.delete(category);
      } else {
        next.add(category);
      }
      return next;
    });
  };

  const toggleDocument = (docId: string) => {
    setExpandedDocuments((prev) => {
      const next = new Set(prev);
      if (next.has(docId)) {
        next.delete(docId);
      } else {
        next.add(docId);
      }
      return next;
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 text-[var(--color-primary-500)] animate-spin" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="text-center py-16">
        <AlertCircle className="h-12 w-12 text-[var(--color-critical-500)] mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-2">
          {error || 'Failed to load extracted data'}
        </h3>
        <div className="flex items-center justify-center gap-4">
          <Link href={`/properties/${id}`}>
            <Button variant="secondary">Back to property</Button>
          </Link>
          <Button variant="ghost" onClick={fetchData}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </div>
      </div>
    );
  }

  const groupedFields = groupFieldsByCategory(data.extracted_fields);
  const categories = Object.keys(groupedFields);

  return (
    <motion.div
      variants={staggerContainer}
      initial="initial"
      animate="animate"
      className="space-y-6"
    >
      {/* Back Link */}
      <motion.div variants={staggerItem} className="flex items-center justify-between">
        <Link
          href={`/properties/${id}`}
          className="inline-flex items-center gap-2 text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to property
        </Link>
        <Button variant="ghost" size="sm" onClick={fetchData}>
          <RefreshCw className="h-4 w-4" />
        </Button>
      </motion.div>

      {/* Header */}
      <motion.div variants={staggerItem}>
        <GlassCard className="p-6" gradient="from-primary-500 to-primary-600" hover={false}>
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">
                Extracted Data
              </h1>
              <p className="text-[var(--color-text-secondary)] mt-1">
                {data.property_name}
              </p>
            </div>

            <div className="flex items-center gap-6">
              <div className="text-center">
                <p className="text-sm text-[var(--color-text-muted)]">Documents</p>
                <p className="text-xl font-bold text-[var(--color-text-primary)]">
                  {data.total_documents}
                </p>
              </div>
              <div className="h-10 w-px bg-[var(--color-border-subtle)]" />
              <div className="text-center">
                <p className="text-sm text-[var(--color-text-muted)]">With Extractions</p>
                <p className="text-xl font-bold text-[var(--color-text-primary)]">
                  {data.documents_with_extractions}
                </p>
              </div>
              <div className="h-10 w-px bg-[var(--color-border-subtle)]" />
              <div className="text-center">
                <p className="text-sm text-[var(--color-text-muted)]">Fields Extracted</p>
                <p className="text-xl font-bold text-[var(--color-text-primary)]">
                  {data.extracted_fields.length}
                </p>
              </div>
            </div>
          </div>
        </GlassCard>
      </motion.div>

      {/* Tab Navigation */}
      <motion.div variants={staggerItem}>
        <div className="flex gap-2">
          <Button
            variant={activeTab === 'fields' ? 'primary' : 'ghost'}
            onClick={() => setActiveTab('fields')}
          >
            <Database className="h-4 w-4 mr-2" />
            By Field
          </Button>
          <Button
            variant={activeTab === 'documents' ? 'primary' : 'ghost'}
            onClick={() => setActiveTab('documents')}
          >
            <FileText className="h-4 w-4 mr-2" />
            By Document
          </Button>
        </div>
      </motion.div>

      {/* Fields View */}
      {activeTab === 'fields' && (
        <motion.div variants={staggerItem} className="space-y-4">
          {categories.map((category) => {
            const config = categoryConfig[category] || {
              icon: FileText,
              color: 'text-gray-500',
              label: category.charAt(0).toUpperCase() + category.slice(1),
            };
            const Icon = config.icon;
            const isExpanded = expandedCategories.has(category);
            const fields = groupedFields[category];

            return (
              <Card key={category} padding="none" className="overflow-hidden">
                <button
                  onClick={() => toggleCategory(category)}
                  className="w-full flex items-center justify-between p-4 hover:bg-[var(--color-surface-hover)] transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className={cn('p-2 rounded-lg bg-[var(--color-surface-sunken)]', config.color)}>
                      <Icon className="h-5 w-5" />
                    </div>
                    <div className="text-left">
                      <h3 className="font-semibold text-[var(--color-text-primary)]">
                        {config.label}
                      </h3>
                      <p className="text-sm text-[var(--color-text-muted)]">
                        {fields.length} field{fields.length !== 1 ? 's' : ''} extracted
                      </p>
                    </div>
                  </div>
                  {isExpanded ? (
                    <ChevronDown className="h-5 w-5 text-[var(--color-text-muted)]" />
                  ) : (
                    <ChevronRight className="h-5 w-5 text-[var(--color-text-muted)]" />
                  )}
                </button>

                {isExpanded && (
                  <div className="border-t border-[var(--color-border-subtle)]">
                    <div className="divide-y divide-[var(--color-border-subtle)]">
                      {fields.map((field) => (
                        <div key={field.field_name} className="p-4">
                          <div className="flex items-start justify-between gap-4">
                            <div className="flex-1">
                              <p className="font-medium text-[var(--color-text-primary)]">
                                {field.display_name}
                              </p>
                              <p className="text-lg font-bold text-[var(--color-text-primary)] mt-1">
                                {formatValue(field.consolidated_value)}
                              </p>
                            </div>
                            {field.values.length > 1 && (
                              <Badge variant="secondary">
                                {field.values.length} sources
                              </Badge>
                            )}
                          </div>

                          {/* Source documents */}
                          <div className="mt-3 space-y-2">
                            {field.values.map((value, idx) => (
                              <div
                                key={idx}
                                className="flex items-center gap-2 text-sm text-[var(--color-text-secondary)] bg-[var(--color-surface-sunken)] rounded-lg px-3 py-2"
                              >
                                <FileCheck className="h-4 w-4 text-[var(--color-text-muted)]" />
                                <span className="flex-1 truncate">{value.source_document_name}</span>
                                {value.source_document_type && (
                                  <Badge variant="secondary" className="text-xs">
                                    {value.source_document_type.toUpperCase()}
                                  </Badge>
                                )}
                                {value.extraction_confidence !== null && (
                                  <span className={cn(
                                    'text-xs font-medium',
                                    value.extraction_confidence >= 0.8
                                      ? 'text-[var(--color-success-500)]'
                                      : value.extraction_confidence >= 0.6
                                      ? 'text-[var(--color-warning-500)]'
                                      : 'text-[var(--color-critical-500)]'
                                  )}>
                                    {Math.round(value.extraction_confidence * 100)}%
                                  </span>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </Card>
            );
          })}

          {categories.length === 0 && (
            <Card padding="lg" className="text-center">
              <Database className="h-12 w-12 text-[var(--color-text-muted)] mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-2">
                No Extracted Data
              </h3>
              <p className="text-[var(--color-text-secondary)]">
                Upload documents to extract property and coverage information.
              </p>
            </Card>
          )}
        </motion.div>
      )}

      {/* Documents View */}
      {activeTab === 'documents' && (
        <motion.div variants={staggerItem} className="space-y-4">
          {data.document_extractions.map((doc) => {
            const isExpanded = expandedDocuments.has(doc.document_id);
            const fieldCount = Object.keys(doc.extracted_fields).length;

            return (
              <Card key={doc.document_id} padding="none" className="overflow-hidden">
                <button
                  onClick={() => toggleDocument(doc.document_id)}
                  className="w-full flex items-center justify-between p-4 hover:bg-[var(--color-surface-hover)] transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-[var(--color-surface-sunken)]">
                      <FileText className="h-5 w-5 text-[var(--color-text-muted)]" />
                    </div>
                    <div className="text-left">
                      <h3 className="font-semibold text-[var(--color-text-primary)]">
                        {doc.document_name}
                      </h3>
                      <div className="flex items-center gap-2 mt-1">
                        {doc.document_type && (
                          <Badge variant="secondary" className="text-xs">
                            {doc.document_type.toUpperCase()}
                          </Badge>
                        )}
                        <span className="text-sm text-[var(--color-text-muted)]">
                          {fieldCount} field{fieldCount !== 1 ? 's' : ''} extracted
                        </span>
                        <span className="text-sm text-[var(--color-text-muted)]">
                          &bull; {formatDate(doc.uploaded_at)}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {doc.extraction_confidence !== null && (
                      <div className="flex items-center gap-1">
                        {doc.extraction_confidence >= 0.8 ? (
                          <CheckCircle2 className="h-4 w-4 text-[var(--color-success-500)]" />
                        ) : (
                          <AlertCircle className="h-4 w-4 text-[var(--color-warning-500)]" />
                        )}
                        <span className={cn(
                          'text-sm font-medium',
                          doc.extraction_confidence >= 0.8
                            ? 'text-[var(--color-success-500)]'
                            : 'text-[var(--color-warning-500)]'
                        )}>
                          {Math.round(doc.extraction_confidence * 100)}%
                        </span>
                      </div>
                    )}
                    {isExpanded ? (
                      <ChevronDown className="h-5 w-5 text-[var(--color-text-muted)]" />
                    ) : (
                      <ChevronRight className="h-5 w-5 text-[var(--color-text-muted)]" />
                    )}
                  </div>
                </button>

                {isExpanded && fieldCount > 0 && (
                  <div className="border-t border-[var(--color-border-subtle)] p-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {Object.entries(doc.extracted_fields).map(([key, value]) => (
                        <div
                          key={key}
                          className="p-3 rounded-lg bg-[var(--color-surface-sunken)]"
                        >
                          <p className="text-xs text-[var(--color-text-muted)] uppercase tracking-wide">
                            {key.replace(/_/g, ' ')}
                          </p>
                          <p className="font-semibold text-[var(--color-text-primary)] mt-1">
                            {formatValue(value)}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {isExpanded && fieldCount === 0 && (
                  <div className="border-t border-[var(--color-border-subtle)] p-4 text-center">
                    <p className="text-[var(--color-text-muted)]">
                      No structured data extracted from this document.
                    </p>
                  </div>
                )}
              </Card>
            );
          })}

          {data.document_extractions.length === 0 && (
            <Card padding="lg" className="text-center">
              <FileText className="h-12 w-12 text-[var(--color-text-muted)] mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-2">
                No Documents
              </h3>
              <p className="text-[var(--color-text-secondary)]">
                Upload documents to see extraction results.
              </p>
            </Card>
          )}
        </motion.div>
      )}

      {/* Structured Data Sections */}
      {activeTab === 'fields' && (
        <>
          {/* Valuations */}
          {data.valuations.length > 0 && (
            <motion.div variants={staggerItem}>
              <Card padding="lg">
                <h2 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4 flex items-center gap-2">
                  <DollarSign className="h-5 w-5 text-[var(--color-success-500)]" />
                  Valuations
                </h2>
                <div className="space-y-4">
                  {data.valuations.map((val) => (
                    <div
                      key={val.id}
                      className="p-4 rounded-xl bg-[var(--color-surface-sunken)] border border-[var(--color-border-subtle)]"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <Badge variant="secondary">{val.valuation_source || 'Unknown Source'}</Badge>
                          {val.valuation_date && (
                            <span className="text-sm text-[var(--color-text-muted)] ml-2">
                              {formatDate(val.valuation_date)}
                            </span>
                          )}
                        </div>
                        {val.source_document_name && (
                          <span className="text-sm text-[var(--color-text-muted)]">
                            From: {val.source_document_name}
                          </span>
                        )}
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {val.total_insured_value && (
                          <div>
                            <p className="text-xs text-[var(--color-text-muted)]">TIV</p>
                            <p className="font-bold text-[var(--color-text-primary)]">
                              {formatCurrency(parseFloat(val.total_insured_value))}
                            </p>
                          </div>
                        )}
                        {val.building_value && (
                          <div>
                            <p className="text-xs text-[var(--color-text-muted)]">Building</p>
                            <p className="font-bold text-[var(--color-text-primary)]">
                              {formatCurrency(parseFloat(val.building_value))}
                            </p>
                          </div>
                        )}
                        {val.contents_value && (
                          <div>
                            <p className="text-xs text-[var(--color-text-muted)]">Contents</p>
                            <p className="font-bold text-[var(--color-text-primary)]">
                              {formatCurrency(parseFloat(val.contents_value))}
                            </p>
                          </div>
                        )}
                        {val.business_income_value && (
                          <div>
                            <p className="text-xs text-[var(--color-text-muted)]">Business Income</p>
                            <p className="font-bold text-[var(--color-text-primary)]">
                              {formatCurrency(parseFloat(val.business_income_value))}
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            </motion.div>
          )}

          {/* Policies */}
          {data.policies.length > 0 && (
            <motion.div variants={staggerItem}>
              <Card padding="lg">
                <h2 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4 flex items-center gap-2">
                  <Shield className="h-5 w-5 text-[var(--color-primary-500)]" />
                  Policies
                </h2>
                <div className="space-y-4">
                  {data.policies.map((policy) => (
                    <div
                      key={policy.id}
                      className="p-4 rounded-xl bg-[var(--color-surface-sunken)] border border-[var(--color-border-subtle)]"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h3 className="font-semibold text-[var(--color-text-primary)]">
                            {policy.policy_type.replace(/_/g, ' ').toUpperCase()}
                          </h3>
                          <p className="text-sm text-[var(--color-text-muted)]">
                            {policy.carrier_name || 'Unknown Carrier'} &bull; {policy.policy_number || 'No Policy #'}
                          </p>
                        </div>
                        {policy.premium && (
                          <div className="text-right">
                            <p className="text-xs text-[var(--color-text-muted)]">Premium</p>
                            <p className="font-bold text-[var(--color-text-primary)]">
                              {formatCurrency(parseFloat(policy.premium))}
                            </p>
                          </div>
                        )}
                      </div>
                      <div className="flex items-center gap-4 text-sm text-[var(--color-text-secondary)]">
                        <span className="flex items-center gap-1">
                          <Calendar className="h-4 w-4" />
                          {formatDate(policy.effective_date)} - {formatDate(policy.expiration_date)}
                        </span>
                        {policy.coverages.length > 0 && (
                          <span>{policy.coverages.length} coverage{policy.coverages.length !== 1 ? 's' : ''}</span>
                        )}
                      </div>
                      {policy.source_document_name && (
                        <p className="text-xs text-[var(--color-text-muted)] mt-2">
                          Source: {policy.source_document_name}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </Card>
            </motion.div>
          )}

          {/* Certificates */}
          {data.certificates.length > 0 && (
            <motion.div variants={staggerItem}>
              <Card padding="lg">
                <h2 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4 flex items-center gap-2">
                  <FileCheck className="h-5 w-5 text-[var(--color-info-500)]" />
                  Certificates
                </h2>
                <div className="space-y-4">
                  {data.certificates.map((cert) => (
                    <div
                      key={cert.id}
                      className="p-4 rounded-xl bg-[var(--color-surface-sunken)] border border-[var(--color-border-subtle)]"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <Badge variant="secondary">{cert.certificate_type.toUpperCase()}</Badge>
                          {cert.certificate_number && (
                            <span className="text-sm text-[var(--color-text-muted)] ml-2">
                              #{cert.certificate_number}
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                        {cert.insured_name && (
                          <div>
                            <p className="text-xs text-[var(--color-text-muted)]">Insured</p>
                            <p className="text-[var(--color-text-primary)]">{cert.insured_name}</p>
                          </div>
                        )}
                        {cert.holder_name && (
                          <div>
                            <p className="text-xs text-[var(--color-text-muted)]">Holder</p>
                            <p className="text-[var(--color-text-primary)]">{cert.holder_name}</p>
                          </div>
                        )}
                        {cert.producer_name && (
                          <div>
                            <p className="text-xs text-[var(--color-text-muted)]">Producer</p>
                            <p className="text-[var(--color-text-primary)]">{cert.producer_name}</p>
                          </div>
                        )}
                        {cert.gl_each_occurrence && (
                          <div>
                            <p className="text-xs text-[var(--color-text-muted)]">GL Each Occurrence</p>
                            <p className="font-semibold text-[var(--color-text-primary)]">
                              {formatCurrency(parseFloat(cert.gl_each_occurrence))}
                            </p>
                          </div>
                        )}
                        {cert.property_limit && (
                          <div>
                            <p className="text-xs text-[var(--color-text-muted)]">Property Limit</p>
                            <p className="font-semibold text-[var(--color-text-primary)]">
                              {formatCurrency(parseFloat(cert.property_limit))}
                            </p>
                          </div>
                        )}
                        {cert.umbrella_limit && (
                          <div>
                            <p className="text-xs text-[var(--color-text-muted)]">Umbrella</p>
                            <p className="font-semibold text-[var(--color-text-primary)]">
                              {formatCurrency(parseFloat(cert.umbrella_limit))}
                            </p>
                          </div>
                        )}
                      </div>
                      {cert.source_document_name && (
                        <p className="text-xs text-[var(--color-text-muted)] mt-3">
                          Source: {cert.source_document_name}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </Card>
            </motion.div>
          )}

          {/* Financials */}
          {data.financials.length > 0 && (
            <motion.div variants={staggerItem}>
              <Card padding="lg">
                <h2 className="text-lg font-semibold text-[var(--color-text-primary)] mb-4 flex items-center gap-2">
                  <DollarSign className="h-5 w-5 text-[var(--color-warning-500)]" />
                  Financial Records
                </h2>
                <div className="space-y-4">
                  {data.financials.map((fin) => (
                    <div
                      key={fin.id}
                      className="p-4 rounded-xl bg-[var(--color-surface-sunken)] border border-[var(--color-border-subtle)]"
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <Badge variant="secondary">{fin.record_type.toUpperCase()}</Badge>
                          <div className="mt-2 text-sm text-[var(--color-text-secondary)]">
                            {fin.invoice_date && (
                              <span>Invoice Date: {formatDate(fin.invoice_date)}</span>
                            )}
                            {fin.due_date && (
                              <span className="ml-4">Due: {formatDate(fin.due_date)}</span>
                            )}
                          </div>
                        </div>
                        {fin.total && (
                          <div className="text-right">
                            <p className="text-xs text-[var(--color-text-muted)]">Total</p>
                            <p className="text-xl font-bold text-[var(--color-text-primary)]">
                              {formatCurrency(parseFloat(fin.total))}
                            </p>
                          </div>
                        )}
                      </div>
                      {(fin.taxes || fin.fees) && (
                        <div className="flex gap-4 mt-3 text-sm">
                          {fin.taxes && (
                            <span className="text-[var(--color-text-secondary)]">
                              Taxes: {formatCurrency(parseFloat(fin.taxes))}
                            </span>
                          )}
                          {fin.fees && (
                            <span className="text-[var(--color-text-secondary)]">
                              Fees: {formatCurrency(parseFloat(fin.fees))}
                            </span>
                          )}
                        </div>
                      )}
                      {fin.source_document_name && (
                        <p className="text-xs text-[var(--color-text-muted)] mt-2">
                          Source: {fin.source_document_name}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </Card>
            </motion.div>
          )}
        </>
      )}
    </motion.div>
  );
}
