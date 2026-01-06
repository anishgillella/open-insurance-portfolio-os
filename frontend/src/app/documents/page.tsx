'use client';

import { useState, useMemo, useCallback, useEffect, Suspense } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import {
  RefreshCw,
  Download,
  Upload,
  Loader2,
  AlertTriangle,
  FileText,
  CheckCircle,
  Clock,
  XCircle,
  Eye,
  Building2,
  Filter,
  Search,
  LayoutGrid,
  List,
  Calendar,
  Shield,
  FileCheck,
  X,
} from 'lucide-react';
import { Button, Card, Badge } from '@/components/primitives';
import { staggerContainer, staggerItem } from '@/lib/motion/variants';
import { documentsApi, propertiesApi, type Document, type Property } from '@/lib/api';

function DocumentsPageContent() {
  const searchParams = useSearchParams();
  const propertyFilter = searchParams.get('property_id') || searchParams.get('property') || undefined;

  const [documents, setDocuments] = useState<Document[]>([]);
  const [properties, setProperties] = useState<Property[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [selectedPropertyFilter, setSelectedPropertyFilter] = useState<string>(propertyFilter || 'all');
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('grid');
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [docsData, propertiesData] = await Promise.all([
        documentsApi.list(undefined, propertyFilter),
        propertiesApi.list(),
      ]);
      // Handle various API response formats
      const docsArray = Array.isArray(docsData) ? docsData :
        (docsData as { documents?: Document[]; items?: Document[] })?.documents ||
        (docsData as { items?: Document[] })?.items || [];
      const propsArray = Array.isArray(propertiesData) ? propertiesData :
        (propertiesData as { properties?: Property[]; items?: Property[] })?.properties ||
        (propertiesData as { items?: Property[] })?.items || [];
      setDocuments(docsArray);
      setProperties(propsArray);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load documents');
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

  // Get unique document types for filter
  const documentTypes = useMemo(() => {
    const types = new Set(documents.map((d) => d.document_type).filter(Boolean));
    return Array.from(types).sort();
  }, [documents]);

  // Filter documents
  const filteredDocuments = useMemo(() => {
    return documents.filter((doc) => {
      // Search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        const matchesSearch =
          doc.file_name?.toLowerCase().includes(query) ||
          doc.document_type?.toLowerCase().includes(query) ||
          doc.carrier?.toLowerCase().includes(query) ||
          doc.policy_number?.toLowerCase().includes(query) ||
          doc.property_name?.toLowerCase().includes(query);
        if (!matchesSearch) return false;
      }

      // Type filter
      if (typeFilter !== 'all' && doc.document_type !== typeFilter) {
        return false;
      }

      // Status filter
      if (statusFilter !== 'all' && doc.upload_status !== statusFilter) {
        return false;
      }

      // Property filter (when not using URL param)
      if (!propertyFilter && selectedPropertyFilter !== 'all' && doc.property_id !== selectedPropertyFilter) {
        return false;
      }

      return true;
    });
  }, [documents, searchQuery, typeFilter, statusFilter, propertyFilter, selectedPropertyFilter]);

  // Stats
  const stats = useMemo(() => {
    const total = documents.length;
    const completed = documents.filter((d) => d.upload_status === 'completed').length;
    const processing = documents.filter((d) => d.upload_status === 'processing').length;
    const failed = documents.filter((d) => d.upload_status === 'failed').length;
    const needsReview = documents.filter((d) => d.needs_human_review).length;
    return { total, completed, processing, failed, needsReview };
  }, [documents]);

  const getDocumentTypeIcon = (type: string | undefined) => {
    const t = (type || '').toLowerCase();
    if (t.includes('policy') || t.includes('certificate')) {
      return <Shield className="h-5 w-5 text-[var(--color-primary-500)]" />;
    }
    if (t.includes('endorsement') || t.includes('amendment')) {
      return <FileCheck className="h-5 w-5 text-[var(--color-info-500)]" />;
    }
    if (t.includes('schedule') || t.includes('sov')) {
      return <Calendar className="h-5 w-5 text-[var(--color-warning-500)]" />;
    }
    return <FileText className="h-5 w-5 text-[var(--color-text-muted)]" />;
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-[var(--color-success-500)]" />;
      case 'processing':
        return <Clock className="h-4 w-4 text-[var(--color-warning-500)] animate-pulse" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-[var(--color-critical-500)]" />;
      default:
        return <Clock className="h-4 w-4 text-[var(--color-text-muted)]" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge variant="success">Completed</Badge>;
      case 'processing':
        return <Badge variant="warning">Processing</Badge>;
      case 'failed':
        return <Badge variant="critical">Failed</Badge>;
      default:
        return <Badge variant="neutral">Pending</Badge>;
    }
  };

  const formatDate = (dateStr: string | undefined) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const getConfidenceBadge = (confidence: number | undefined) => {
    if (confidence === undefined || confidence === null) return null;
    const pct = Math.round(confidence * 100);
    if (pct >= 80) return <Badge variant="success">{pct}%</Badge>;
    if (pct >= 60) return <Badge variant="warning">{pct}%</Badge>;
    return <Badge variant="critical">{pct}%</Badge>;
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
          Failed to load documents
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
      <motion.div variants={staggerItem} className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">
              Documents
            </h1>
            {filteredProperty && (
              <span className="px-3 py-1 rounded-full bg-[var(--color-primary-50)] text-[var(--color-primary-600)] text-sm font-medium">
                {filteredProperty.name}
              </span>
            )}
          </div>
          <p className="text-[var(--color-text-secondary)] mt-1">
            {filteredProperty
              ? `Viewing documents for ${filteredProperty.name}`
              : 'Manage and view all insurance documents across your portfolio'}
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
          <Button
            variant="primary"
            leftIcon={<Upload className="h-4 w-4" />}
          >
            Upload
          </Button>
        </div>
      </motion.div>

      {/* Stats Row - Compact horizontal layout */}
      <motion.div variants={staggerItem}>
        <Card padding="md">
          <div className="flex items-center justify-between divide-x divide-[var(--color-border-primary)]">
            <div className="flex-1 flex items-center gap-3 px-4 first:pl-0">
              <div className="p-2 rounded-lg bg-[var(--color-primary-50)]">
                <FileText className="h-5 w-5 text-[var(--color-primary-500)]" />
              </div>
              <div>
                <div className="text-2xl font-bold text-[var(--color-text-primary)]">{stats.total}</div>
                <div className="text-xs text-[var(--color-text-muted)]">Total</div>
              </div>
            </div>
            <div className="flex-1 flex items-center gap-3 px-4">
              <div className="p-2 rounded-lg bg-[var(--color-success-50)]">
                <CheckCircle className="h-5 w-5 text-[var(--color-success-500)]" />
              </div>
              <div>
                <div className="text-2xl font-bold text-[var(--color-text-primary)]">{stats.completed}</div>
                <div className="text-xs text-[var(--color-text-muted)]">Completed</div>
              </div>
            </div>
            <div className="flex-1 flex items-center gap-3 px-4">
              <div className="p-2 rounded-lg bg-[var(--color-warning-50)]">
                <Clock className="h-5 w-5 text-[var(--color-warning-500)]" />
              </div>
              <div>
                <div className="text-2xl font-bold text-[var(--color-text-primary)]">{stats.processing}</div>
                <div className="text-xs text-[var(--color-text-muted)]">Processing</div>
              </div>
            </div>
            <div className="flex-1 flex items-center gap-3 px-4">
              <div className="p-2 rounded-lg bg-[var(--color-critical-50)]">
                <XCircle className="h-5 w-5 text-[var(--color-critical-500)]" />
              </div>
              <div>
                <div className="text-2xl font-bold text-[var(--color-text-primary)]">{stats.failed}</div>
                <div className="text-xs text-[var(--color-text-muted)]">Failed</div>
              </div>
            </div>
            <div className="flex-1 flex items-center gap-3 px-4 last:pr-0">
              <div className="p-2 rounded-lg bg-[var(--color-info-50)]">
                <Eye className="h-5 w-5 text-[var(--color-info-500)]" />
              </div>
              <div>
                <div className="text-2xl font-bold text-[var(--color-text-primary)]">{stats.needsReview}</div>
                <div className="text-xs text-[var(--color-text-muted)]">Review</div>
              </div>
            </div>
          </div>
        </Card>
      </motion.div>

      {/* Filters & View Toggle */}
      <motion.div variants={staggerItem}>
        <Card padding="md">
          <div className="flex items-center gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--color-text-muted)]" />
              <input
                type="text"
                placeholder="Search by filename, carrier, policy number..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 rounded-lg border border-[var(--color-border-primary)] bg-[var(--color-bg-primary)] text-[var(--color-text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary-500)]"
              />
            </div>
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-[var(--color-text-muted)]" />
              {!propertyFilter && (
                <select
                  value={selectedPropertyFilter}
                  onChange={(e) => setSelectedPropertyFilter(e.target.value)}
                  className="px-3 py-2 rounded-lg border border-[var(--color-border-primary)] bg-[var(--color-bg-primary)] text-[var(--color-text-primary)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-primary-500)]"
                >
                  <option value="all">All Properties</option>
                  {properties.map((prop) => (
                    <option key={prop.id} value={prop.id}>{prop.name}</option>
                  ))}
                </select>
              )}
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="px-3 py-2 rounded-lg border border-[var(--color-border-primary)] bg-[var(--color-bg-primary)] text-[var(--color-text-primary)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-primary-500)]"
              >
                <option value="all">All Types</option>
                {documentTypes.map((type) => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-3 py-2 rounded-lg border border-[var(--color-border-primary)] bg-[var(--color-bg-primary)] text-[var(--color-text-primary)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-primary-500)]"
              >
                <option value="all">All Status</option>
                <option value="completed">Completed</option>
                <option value="processing">Processing</option>
                <option value="failed">Failed</option>
                <option value="pending">Pending</option>
              </select>
            </div>
            <div className="flex items-center border border-[var(--color-border-primary)] rounded-lg overflow-hidden">
              <button
                onClick={() => setViewMode('grid')}
                className={`p-2 ${viewMode === 'grid' ? 'bg-[var(--color-primary-50)] text-[var(--color-primary-600)]' : 'text-[var(--color-text-muted)] hover:bg-[var(--color-bg-secondary)]'}`}
              >
                <LayoutGrid className="h-4 w-4" />
              </button>
              <button
                onClick={() => setViewMode('table')}
                className={`p-2 ${viewMode === 'table' ? 'bg-[var(--color-primary-50)] text-[var(--color-primary-600)]' : 'text-[var(--color-text-muted)] hover:bg-[var(--color-bg-secondary)]'}`}
              >
                <List className="h-4 w-4" />
              </button>
            </div>
          </div>
        </Card>
      </motion.div>

      {/* Documents Count */}
      <motion.div variants={staggerItem} className="flex items-center justify-between">
        <span className="text-sm text-[var(--color-text-muted)]">
          {filteredDocuments.length} document{filteredDocuments.length !== 1 ? 's' : ''} found
        </span>
      </motion.div>

      {/* Documents Views - Grid or Table */}
      <AnimatePresence mode="wait">
      {viewMode === 'grid' && (
        <motion.div
          key="grid-view"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
        >
          {filteredDocuments.length === 0 ? (
            <Card padding="lg">
              <div className="text-center py-12">
                <FileText className="h-12 w-12 text-[var(--color-text-muted)] mx-auto mb-4" />
                <h3 className="text-lg font-medium text-[var(--color-text-primary)] mb-2">
                  No documents found
                </h3>
                <p className="text-[var(--color-text-muted)]">
                  {searchQuery || typeFilter !== 'all' || statusFilter !== 'all'
                    ? 'Try adjusting your filters'
                    : 'Upload your first document to get started'}
                </p>
              </div>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {filteredDocuments.map((doc) => (
                <Card
                  key={doc.id}
                  padding="md"
                  className="hover:shadow-lg transition-shadow cursor-pointer group"
                  onClick={() => setSelectedDocument(doc)}
                >
                  <div className="flex items-start gap-3">
                    <div className="p-3 rounded-lg bg-[var(--color-bg-tertiary)] group-hover:bg-[var(--color-primary-50)] transition-colors">
                      {getDocumentTypeIcon(doc.document_type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-[var(--color-text-primary)] truncate" title={doc.file_name}>
                        {doc.file_name}
                      </div>
                      <div className="text-xs text-[var(--color-text-muted)] mt-0.5">
                        {doc.document_type || 'Unknown Type'}
                      </div>
                    </div>
                    <div className="flex-shrink-0">
                      {getStatusIcon(doc.upload_status)}
                    </div>
                  </div>

                  <div className="mt-4 pt-4 border-t border-[var(--color-border-secondary)] space-y-2">
                    {doc.property_name && (
                      <div className="flex items-center gap-2 text-sm">
                        <Building2 className="h-3.5 w-3.5 text-[var(--color-text-muted)]" />
                        <span className="text-[var(--color-text-secondary)] truncate">{doc.property_name}</span>
                      </div>
                    )}
                    {doc.carrier && (
                      <div className="flex items-center gap-2 text-sm">
                        <Shield className="h-3.5 w-3.5 text-[var(--color-text-muted)]" />
                        <span className="text-[var(--color-text-secondary)] truncate">{doc.carrier}</span>
                      </div>
                    )}
                    {doc.policy_number && (
                      <div className="flex items-center gap-2 text-sm">
                        <FileText className="h-3.5 w-3.5 text-[var(--color-text-muted)]" />
                        <span className="text-[var(--color-text-secondary)] truncate">{doc.policy_number}</span>
                      </div>
                    )}
                  </div>

                  <div className="mt-4 flex items-center justify-between">
                    <span className="text-xs text-[var(--color-text-muted)]">
                      {formatDate(doc.created_at)}
                    </span>
                    <div className="flex items-center gap-2">
                      {doc.needs_human_review && (
                        <Badge variant="warning" className="text-xs">Review</Badge>
                      )}
                      {getConfidenceBadge(doc.extraction_confidence)}
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </motion.div>
      )}

      {viewMode === 'table' && (
        <motion.div
          key="table-view"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
        >
          <Card padding="lg">
            {filteredDocuments.length === 0 ? (
              <div className="text-center py-12">
                <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  No documents found
                </h3>
                <p className="text-gray-500">
                  {searchQuery || typeFilter !== 'all' || statusFilter !== 'all'
                    ? 'Try adjusting your filters'
                    : 'Upload your first document to get started'}
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Document</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Type</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Property</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Carrier</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Status</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Confidence</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Uploaded</th>
                      <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredDocuments.map((doc) => (
                      <tr
                        key={doc.id}
                        className="border-b border-gray-100 hover:bg-gray-50 transition-colors cursor-pointer"
                        onClick={() => setSelectedDocument(doc)}
                      >
                        <td className="py-4 px-4">
                          <div className="flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-gray-100">
                              {getDocumentTypeIcon(doc.document_type)}
                            </div>
                            <div>
                              <div className="font-medium text-gray-900 truncate max-w-[200px]">
                                {doc.file_name}
                              </div>
                              {doc.policy_number && (
                                <div className="text-xs text-gray-500">
                                  Policy: {doc.policy_number}
                                </div>
                              )}
                            </div>
                          </div>
                        </td>
                        <td className="py-4 px-4">
                          <Badge variant="neutral">{doc.document_type || 'Unknown'}</Badge>
                        </td>
                        <td className="py-4 px-4">
                          {doc.property_id ? (
                            <Link
                              href={`/properties/${doc.property_id}`}
                              className="flex items-center gap-2 text-blue-600 hover:text-blue-700"
                              onClick={(e) => e.stopPropagation()}
                            >
                              <Building2 className="h-4 w-4" />
                              <span className="truncate max-w-[120px]">{doc.property_name || 'View'}</span>
                            </Link>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </td>
                        <td className="py-4 px-4">
                          <span className="text-gray-700">
                            {doc.carrier || '-'}
                          </span>
                        </td>
                        <td className="py-4 px-4">
                          <div className="flex items-center gap-2">
                            {getStatusIcon(doc.upload_status)}
                            {getStatusBadge(doc.upload_status)}
                          </div>
                        </td>
                        <td className="py-4 px-4">
                          {getConfidenceBadge(doc.extraction_confidence)}
                        </td>
                        <td className="py-4 px-4">
                          <span className="text-sm text-gray-500">
                            {formatDate(doc.created_at)}
                          </span>
                        </td>
                        <td className="py-4 px-4 text-right">
                          <button
                            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                            onClick={(e: React.MouseEvent) => { e.stopPropagation(); setSelectedDocument(doc); }}
                          >
                            <Eye className="h-4 w-4 text-gray-500" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </motion.div>
      )}
      </AnimatePresence>

      {/* Document Detail Modal */}
      {selectedDocument && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/60" onClick={() => setSelectedDocument(null)} />
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="relative bg-white rounded-xl shadow-2xl border border-gray-300 w-full max-w-2xl max-h-[90vh] overflow-y-auto z-10"
          >
            <div className="sticky top-0 bg-white border-b border-gray-200 p-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">Document Details</h3>
              <button
                onClick={() => setSelectedDocument(null)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X className="h-5 w-5 text-gray-500" />
              </button>
            </div>

            <div className="p-6 space-y-6">
              {/* Document Header */}
              <div className="flex items-start gap-4">
                <div className="p-4 rounded-xl bg-gray-100">
                  {getDocumentTypeIcon(selectedDocument.document_type)}
                </div>
                <div className="flex-1">
                  <h4 className="text-xl font-semibold text-gray-900">
                    {selectedDocument.file_name}
                  </h4>
                  <div className="flex items-center gap-3 mt-2">
                    <Badge variant="neutral">{selectedDocument.document_type || 'Unknown'}</Badge>
                    {getStatusBadge(selectedDocument.upload_status)}
                    {selectedDocument.needs_human_review && (
                      <Badge variant="warning">Needs Review</Badge>
                    )}
                  </div>
                </div>
              </div>

              {/* Details Grid */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <div className="text-xs text-gray-500 uppercase tracking-wide">Property</div>
                  <div className="text-gray-900">
                    {selectedDocument.property_name || '-'}
                  </div>
                </div>
                <div className="space-y-1">
                  <div className="text-xs text-gray-500 uppercase tracking-wide">Carrier</div>
                  <div className="text-gray-900">
                    {selectedDocument.carrier || '-'}
                  </div>
                </div>
                <div className="space-y-1">
                  <div className="text-xs text-gray-500 uppercase tracking-wide">Policy Number</div>
                  <div className="text-gray-900">
                    {selectedDocument.policy_number || '-'}
                  </div>
                </div>
                <div className="space-y-1">
                  <div className="text-xs text-gray-500 uppercase tracking-wide">Extraction Confidence</div>
                  <div className="text-gray-900">
                    {selectedDocument.extraction_confidence
                      ? `${Math.round(selectedDocument.extraction_confidence * 100)}%`
                      : '-'}
                  </div>
                </div>
                <div className="space-y-1">
                  <div className="text-xs text-gray-500 uppercase tracking-wide">Effective Date</div>
                  <div className="text-gray-900">
                    {formatDate(selectedDocument.effective_date)}
                  </div>
                </div>
                <div className="space-y-1">
                  <div className="text-xs text-gray-500 uppercase tracking-wide">Expiration Date</div>
                  <div className="text-gray-900">
                    {formatDate(selectedDocument.expiration_date)}
                  </div>
                </div>
                <div className="space-y-1">
                  <div className="text-xs text-gray-500 uppercase tracking-wide">Uploaded</div>
                  <div className="text-gray-900">
                    {formatDate(selectedDocument.created_at)}
                  </div>
                </div>
                <div className="space-y-1">
                  <div className="text-xs text-gray-500 uppercase tracking-wide">Last Updated</div>
                  <div className="text-gray-900">
                    {formatDate(selectedDocument.updated_at)}
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-3 pt-4 border-t border-gray-200">
                {selectedDocument.property_id && (
                  <Link href={`/properties/${selectedDocument.property_id}`}>
                    <Button variant="secondary" leftIcon={<Building2 className="h-4 w-4" />}>
                      View Property
                    </Button>
                  </Link>
                )}
                <Button variant="secondary" leftIcon={<Eye className="h-4 w-4" />}>
                  View Extraction
                </Button>
                <Button variant="secondary" leftIcon={<Download className="h-4 w-4" />}>
                  Download
                </Button>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </motion.div>
  );
}

export default function DocumentsPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 text-[var(--color-primary-500)] animate-spin" />
      </div>
    }>
      <DocumentsPageContent />
    </Suspense>
  );
}
