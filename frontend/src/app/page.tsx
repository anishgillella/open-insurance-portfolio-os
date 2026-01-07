'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { useState, useEffect, useCallback, useRef } from 'react';
import Link from 'next/link';
import {
  Building2,
  AlertTriangle,
  RefreshCw,
  Loader2,
  MapPin,
  FileText,
  DollarSign,
  CalendarClock,
  Clock,
  ListTodo,
  Building,
  Home,
  Users,
  ChevronDown,
  X,
  Upload,
  CheckCircle,
  XCircle,
  Trash2,
} from 'lucide-react';
import { Button, Card } from '@/components/primitives';
import { DynamicPropertyMap } from '@/components/features/map';
import { staggerContainer, staggerItem } from '@/lib/motion/variants';
import {
  dashboardApi,
  propertiesApi,
  gapsApi,
  documentsApi,
  type DashboardSummary,
  type ExpirationItem,
  type DashboardAlert,
  type Property,
  type Gap,
} from '@/lib/api';
import { enrichPropertiesWithCoordinates } from '@/lib/geocoding';
import { getDemoPropertiesForMap } from '@/lib/demo-properties';

// Upload file type with metadata for display
interface UploadFileItem {
  file: File;
  id: string;
  propertyName: string;
  documentType: 'SOV' | 'COI' | 'Binder' | 'Policy' | 'Other';
  status: 'pending' | 'uploading' | 'confirmed' | 'error';
  progress?: number;
}

export default function Dashboard() {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedProperty, setSelectedProperty] = useState<Property | null>(null);
  const [taskFilter, setTaskFilter] = useState<'open' | 'all'>('open');

  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [expirations, setExpirations] = useState<ExpirationItem[]>([]);
  const [alerts, setAlerts] = useState<DashboardAlert[]>([]);
  const [properties, setProperties] = useState<Property[]>([]);
  const [mapProperties, setMapProperties] = useState<Property[]>([]);
  const [gaps, setGaps] = useState<Gap[]>([]);

  // Upload modal state
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [uploadFiles, setUploadFiles] = useState<UploadFileItem[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<{ current: number; total: number; currentFile?: string } | null>(null);
  const [uploadResults, setUploadResults] = useState<{ success: number; failed: number; errors: string[] }>({ success: 0, failed: 0, errors: [] });
  const [isDragging, setIsDragging] = useState(false);
  const [documentTypePopup, setDocumentTypePopup] = useState<{ fileId: string; position: { x: number; y: number } } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [summaryData, expirationsData, alertsData, propertiesData, gapsData] = await Promise.all([
        dashboardApi.getSummary(),
        dashboardApi.getExpirations(),
        dashboardApi.getAlerts(),
        propertiesApi.list(),
        gapsApi.list(),
      ]);
      setSummary(summaryData);
      setExpirations(
        Array.isArray(expirationsData) ? expirationsData :
        (expirationsData as { expirations?: ExpirationItem[]; items?: ExpirationItem[] })?.expirations ||
        (expirationsData as { items?: ExpirationItem[] })?.items || []
      );
      setAlerts(
        Array.isArray(alertsData) ? alertsData :
        (alertsData as { alerts?: DashboardAlert[]; items?: DashboardAlert[] })?.alerts ||
        (alertsData as { items?: DashboardAlert[] })?.items || []
      );
      const rawProperties = Array.isArray(propertiesData) ? propertiesData :
        (propertiesData as { properties?: Property[]; items?: Property[] })?.properties ||
        (propertiesData as { items?: Property[] })?.items || [];
      // Enrich properties with coordinates if they don't have them
      const enrichedProperties = enrichPropertiesWithCoordinates(rawProperties);
      setProperties(enrichedProperties);
      // Use demo properties for map if real ones don't have coordinates
      setMapProperties(getDemoPropertiesForMap(enrichedProperties));
      setGaps(
        Array.isArray(gapsData) ? gapsData :
        (gapsData as { gaps?: Gap[]; items?: Gap[] })?.gaps ||
        (gapsData as { items?: Gap[] })?.items || []
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard data');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const formatCurrency = (value: number | string | undefined) => {
    if (value === undefined) return '$0';
    const num = typeof value === 'string' ? parseFloat(value) : value;
    if (num >= 1000000) {
      return `$${(num / 1000000).toFixed(2)}M`;
    }
    return `$${num.toLocaleString()}`;
  };

  const formatNumber = (value: number | undefined) => {
    if (value === undefined) return '0';
    if (value >= 1000) {
      return value.toLocaleString();
    }
    return value.toString();
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes}B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)}KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
  };

  // Upload handlers
  const handleOpenUploadModal = () => {
    setUploadFiles([]);
    setUploadResults({ success: 0, failed: 0, errors: [] });
    setUploadProgress(null);
    setIsUploadModalOpen(true);
  };

  const handleCloseUploadModal = () => {
    if (!isUploading) {
      setIsUploadModalOpen(false);
      setUploadFiles([]);
      setIsDragging(false);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    addFiles(files);
    // Reset input so the same file can be selected again
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const addFiles = (files: File[]) => {
    const newFiles: UploadFileItem[] = files.map((file) => ({
      file,
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      propertyName: 'Property Name',
      documentType: 'SOV' as const,
      status: 'pending' as const,
    }));
    setUploadFiles((prev) => [...prev, ...newFiles]);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isUploading) {
      setIsDragging(true);
    }
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (!isUploading) {
      const files = Array.from(e.dataTransfer.files);
      addFiles(files);
    }
  };

  const handleRemoveFile = (fileId: string) => {
    setUploadFiles((prev) => prev.filter((f) => f.id !== fileId));
  };

  const handleUpdateFileType = (fileId: string, documentType: UploadFileItem['documentType']) => {
    setUploadFiles((prev) =>
      prev.map((f) => (f.id === fileId ? { ...f, documentType } : f))
    );
  };

  const handleConfirmFile = (fileId: string) => {
    setUploadFiles((prev) =>
      prev.map((f) => (f.id === fileId ? { ...f, status: 'confirmed' } : f))
    );
  };

  const handleUpload = async () => {
    if (uploadFiles.length === 0) return;

    setIsUploading(true);
    setUploadProgress({ current: 0, total: uploadFiles.length });
    setUploadResults({ success: 0, failed: 0, errors: [] });

    const results = { success: 0, failed: 0, errors: [] as string[] };
    const CONCURRENCY_LIMIT = 3;
    let completed = 0;

    const uploadFile = async (fileItem: UploadFileItem) => {
      try {
        setUploadFiles((prev) =>
          prev.map((f) => (f.id === fileItem.id ? { ...f, status: 'uploading' } : f))
        );
        await documentsApi.uploadAsync(
          fileItem.file,
          fileItem.propertyName,
          undefined,
          undefined
        );
        results.success++;
        setUploadFiles((prev) =>
          prev.map((f) => (f.id === fileItem.id ? { ...f, status: 'confirmed' } : f))
        );
      } catch (err) {
        results.failed++;
        results.errors.push(`${fileItem.file.name}: ${err instanceof Error ? err.message : 'Upload failed'}`);
        setUploadFiles((prev) =>
          prev.map((f) => (f.id === fileItem.id ? { ...f, status: 'error' } : f))
        );
      }
      completed++;
      setUploadProgress({ current: completed, total: uploadFiles.length, currentFile: fileItem.file.name });
    };

    // Process files with concurrency limit
    const chunks = [];
    for (let i = 0; i < uploadFiles.length; i += CONCURRENCY_LIMIT) {
      chunks.push(uploadFiles.slice(i, i + CONCURRENCY_LIMIT));
    }

    for (const chunk of chunks) {
      await Promise.all(chunk.map(uploadFile));
    }

    setUploadResults(results);
    setIsUploading(false);
    setUploadProgress(null);

    // Refresh data if any uploads succeeded
    if (results.success > 0) {
      fetchData();
    }
  };

  // Filter open gaps for coverage gaps section
  const openGaps = gaps.filter((g) => g.status === 'open');
  const criticalGaps = openGaps.filter((g) => g.severity === 'critical');
  const warningGaps = openGaps.filter((g) => g.severity === 'warning');
  const infoGaps = openGaps.filter((g) => g.severity === 'info');

  // Calculate totals
  const totalBuildings = properties.reduce((sum, p) => sum + (p.total_buildings || 0), 0);
  const totalUnits = properties.reduce((sum, p) => sum + (p.total_units || 0), 0);

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
          Failed to load dashboard
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
      className="space-y-4"
    >
      {/* Header */}
      <motion.div variants={staggerItem} className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-[var(--color-text-primary)]">
          Dashboard
        </h1>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleOpenUploadModal}
            leftIcon={<Upload className="h-4 w-4" />}
            className="text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]"
          >
            Upload
          </Button>
          <Button variant="ghost" size="icon-sm" onClick={fetchData}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </motion.div>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".pdf,.doc,.docx,.xls,.xlsx,.png,.jpg,.jpeg"
        onChange={handleFileSelect}
        className="hidden"
      />

      {/* Two-Row Metrics Cards */}
      <motion.div variants={staggerItem} className="space-y-3">
        {/* Top Row - Primary Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {/* Total Policies */}
          <div className="bg-white dark:bg-[var(--color-surface)] rounded-xl p-4 border border-[var(--color-border-subtle)]">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-[var(--color-text-muted)] mb-1">Total Policies</p>
                <p className="text-2xl font-bold text-[var(--color-text-primary)]">
                  {formatNumber(summary?.portfolio_stats?.total_properties)}
                </p>
              </div>
              <div className="p-2 text-teal-600">
                <FileText className="h-5 w-5" />
              </div>
            </div>
          </div>

          {/* Total Premium */}
          <div className="bg-white dark:bg-[var(--color-surface)] rounded-xl p-4 border border-[var(--color-border-subtle)]">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-[var(--color-text-muted)] mb-1">Total Premium</p>
                <p className="text-2xl font-bold text-[var(--color-text-primary)]">
                  {formatCurrency(summary?.portfolio_stats?.total_annual_premium)}
                </p>
              </div>
              <div className="p-2 text-teal-600">
                <DollarSign className="h-5 w-5" />
              </div>
            </div>
          </div>

          {/* Renewals Due */}
          <div className="bg-white dark:bg-[var(--color-surface)] rounded-xl p-4 border border-[var(--color-border-subtle)]">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-[var(--color-text-muted)] mb-1">Renewals due</p>
                <p className="text-2xl font-bold text-[var(--color-text-primary)]">
                  {formatNumber(summary?.expiration_stats?.expiring_30_days)}
                </p>
              </div>
              <div className="p-2 text-teal-600">
                <CalendarClock className="h-5 w-5" />
              </div>
            </div>
          </div>

          {/* Pending Claims */}
          <div className="bg-white dark:bg-[var(--color-surface)] rounded-xl p-4 border border-[var(--color-border-subtle)]">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-[var(--color-text-muted)] mb-1">Pending Claims</p>
                <p className="text-2xl font-bold text-[var(--color-text-primary)]">
                  {formatNumber(summary?.gap_stats?.total_open_gaps)}
                </p>
              </div>
              <div className="p-2 text-teal-600">
                <Clock className="h-5 w-5" />
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Row - Secondary Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {/* Actions */}
          <div className="bg-white dark:bg-[var(--color-surface)] rounded-xl p-4 border border-[var(--color-border-subtle)]">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-[var(--color-text-muted)] mb-1">Actions</p>
                <p className="text-2xl font-bold text-[var(--color-text-primary)]">
                  {formatNumber(openGaps.length + expirations.length)}
                </p>
              </div>
              <div className="p-2 text-teal-600">
                <ListTodo className="h-5 w-5" />
              </div>
            </div>
          </div>

          {/* Buildings */}
          <div className="bg-white dark:bg-[var(--color-surface)] rounded-xl p-4 border border-[var(--color-border-subtle)]">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-[var(--color-text-muted)] mb-1">Buildings</p>
                <p className="text-2xl font-bold text-[var(--color-text-primary)]">
                  {formatNumber(totalBuildings)}
                </p>
              </div>
              <div className="p-2 text-teal-600">
                <Building className="h-5 w-5" />
              </div>
            </div>
          </div>

          {/* Properties */}
          <div className="bg-white dark:bg-[var(--color-surface)] rounded-xl p-4 border border-[var(--color-border-subtle)]">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-[var(--color-text-muted)] mb-1">Properties</p>
                <p className="text-2xl font-bold text-[var(--color-text-primary)]">
                  {formatNumber(properties.length)}
                </p>
              </div>
              <div className="p-2 text-teal-600">
                <Home className="h-5 w-5" />
              </div>
            </div>
          </div>

          {/* Units */}
          <div className="bg-white dark:bg-[var(--color-surface)] rounded-xl p-4 border border-[var(--color-border-subtle)]">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-[var(--color-text-muted)] mb-1">Units</p>
                <p className="text-2xl font-bold text-[var(--color-text-primary)]">
                  {formatNumber(totalUnits)}
                </p>
              </div>
              <div className="p-2 text-teal-600">
                <Users className="h-5 w-5" />
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Main Content - Map and Tasks Panel */}
      <motion.div variants={staggerItem} className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Map Section - Takes 2 columns */}
        <div className="lg:col-span-2 relative">
          <Card padding="none" className="overflow-hidden h-[calc(100vh-420px)] min-h-[350px]">
            <DynamicPropertyMap
              properties={mapProperties}
              onPropertySelect={setSelectedProperty}
              height="100%"
              selectedPropertyId={selectedProperty?.id}
            />

            {/* Selected Property Overlay Card */}
            {selectedProperty && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="absolute bottom-4 left-4 right-4 z-[1000]"
              >
                <div className="bg-white dark:bg-[var(--color-surface)] rounded-lg shadow-lg border border-[var(--color-border-subtle)] p-4">
                  <div className="flex items-start gap-3">
                    <div className="p-2 bg-teal-100 dark:bg-teal-900/30 rounded-lg flex-shrink-0">
                      <Building2 className="h-5 w-5 text-teal-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-[var(--color-text-primary)]">
                        {selectedProperty.name}
                      </h3>
                      <p className="text-sm text-[var(--color-text-muted)] flex items-center gap-1">
                        <MapPin className="h-3 w-3" />
                        {selectedProperty.address.street}, {selectedProperty.address.city}, {selectedProperty.address.state} {selectedProperty.address.zip}
                      </p>
                    </div>
                    <Link href={`/properties/${selectedProperty.id}`}>
                      <Button variant="primary" size="sm">
                        View Details
                      </Button>
                    </Link>
                    <button
                      onClick={() => setSelectedProperty(null)}
                      className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full transition-colors"
                      aria-label="Close"
                    >
                      <X className="h-4 w-4 text-[var(--color-text-muted)]" />
                    </button>
                  </div>
                </div>
              </motion.div>
            )}
          </Card>
        </div>

        {/* Tasks Panel - Right side */}
        <div className="h-[calc(100vh-420px)] min-h-[350px] overflow-y-auto space-y-4">
          {/* Tasks Section */}
          <Card padding="md">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">Tasks</h2>
              <div className="flex items-center gap-2">
                <button
                  className="flex items-center gap-1 px-3 py-1.5 text-sm border border-[var(--color-border-subtle)] rounded-lg hover:bg-[var(--color-surface-sunken)]"
                  onClick={() => setTaskFilter(taskFilter === 'open' ? 'all' : 'open')}
                >
                  {taskFilter === 'open' ? 'Open' : 'All'}
                  <ChevronDown className="h-4 w-4" />
                </button>
                <Link href="/renewals">
                  <button className="text-sm text-teal-600 hover:text-teal-700 font-medium">
                    See All
                  </button>
                </Link>
              </div>
            </div>

            {/* Task Items */}
            <div className="space-y-3">
              {expirations.length > 0 ? (
                expirations.slice(0, 2).map((expiration) => (
                  <div
                    key={expiration.policy_id}
                    className="flex items-center justify-between py-2"
                  >
                    <div>
                      <p className="font-medium text-[var(--color-text-primary)]">
                        Renew Policy #{expiration.policy_number || expiration.policy_id.slice(-10)}
                      </p>
                      <p className="text-sm text-[var(--color-text-muted)]">
                        {expiration.property_name} • Open
                      </p>
                    </div>
                    <Link href={`/properties/${expiration.property_id}`}>
                      <Button variant="outline" size="sm">
                        View
                      </Button>
                    </Link>
                  </div>
                ))
              ) : (
                // Demo task items when no real expirations
                <>
                  <div className="flex items-center justify-between py-2">
                    <div>
                      <p className="font-medium text-[var(--color-text-primary)]">
                        Renew Policy #L1234567890
                      </p>
                      <p className="text-sm text-[var(--color-text-muted)]">
                        Manhattan Tower • Open
                      </p>
                    </div>
                    <Button variant="outline" size="sm">
                      View
                    </Button>
                  </div>
                  <div className="flex items-center justify-between py-2">
                    <div>
                      <p className="font-medium text-[var(--color-text-primary)]">
                        Renew Policy #L0987654321
                      </p>
                      <p className="text-sm text-[var(--color-text-muted)]">
                        Brooklyn Heights • Open
                      </p>
                    </div>
                    <Button variant="outline" size="sm">
                      View
                    </Button>
                  </div>
                </>
              )}
            </div>
          </Card>

          {/* Coverage Gaps Section */}
          <Card padding="md">
            <h3 className="font-semibold text-[var(--color-text-primary)] mb-4">Coverage Gaps</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-sm text-[var(--color-text-primary)]">Properties missing property insurance</p>
                <span className="px-3 py-1 text-sm font-medium rounded-full bg-emerald-100 text-emerald-700">
                  {String(criticalGaps.length).padStart(2, '0')}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <p className="text-sm text-[var(--color-text-primary)]">Properties missing liability insurance</p>
                <span className="px-3 py-1 text-sm font-medium rounded-full bg-amber-100 text-amber-700">
                  {String(warningGaps.length).padStart(2, '0')}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <p className="text-sm text-[var(--color-text-primary)]">AI-driven insights available</p>
                <span className="px-3 py-1 text-sm font-medium rounded-full bg-blue-100 text-blue-700">
                  {String(infoGaps.length).padStart(2, '0')}
                </span>
              </div>
            </div>
          </Card>

          {/* Upcoming Policies to Renew Section */}
          <Card padding="md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-[var(--color-text-primary)]">Upcoming Policies to Renew</h3>
              <Link href="/renewals">
                <button className="text-sm text-teal-600 hover:text-teal-700 font-medium">
                  See All
                </button>
              </Link>
            </div>

            {/* Table Header */}
            <div className="grid grid-cols-3 gap-2 text-xs text-[var(--color-text-muted)] pb-2 border-b border-[var(--color-border-subtle)]">
              <span>Property Name</span>
              <span>LOB</span>
              <span>Date</span>
            </div>

            {/* Table Body */}
            <div className="space-y-0">
              {expirations.length > 0 ? (
                expirations.slice(0, 6).map((expiration) => (
                  <Link
                    key={expiration.policy_id}
                    href={`/properties/${expiration.property_id}`}
                    className="block"
                  >
                    <div className="grid grid-cols-3 gap-2 py-3 text-sm hover:bg-[var(--color-surface-sunken)] -mx-4 px-4 transition-colors">
                      <span className="text-[var(--color-text-primary)] truncate">
                        {expiration.property_name}
                      </span>
                      <span className="text-[var(--color-text-muted)]">
                        {expiration.coverage_type || 'Property'}
                      </span>
                      <span className="text-[var(--color-text-muted)]">
                        {new Date(expiration.expiration_date).toLocaleDateString('en-US', {
                          month: '2-digit',
                          day: '2-digit',
                          year: '2-digit'
                        })}
                      </span>
                    </div>
                  </Link>
                ))
              ) : (
                // Demo upcoming policies when no real expirations
                <>
                  {[
                    { name: 'Manhattan Tower', lob: 'Property', date: '03/15/26' },
                    { name: 'Brooklyn Heights', lob: 'Liability', date: '02/10/26' },
                    { name: 'Upper East Plaza', lob: 'Property', date: '04/01/26' },
                    { name: 'Jersey City', lob: 'Property', date: '01/20/26' },
                    { name: 'SoHo Lofts', lob: 'Umbrella', date: '05/15/26' },
                    { name: 'Midtown Center', lob: 'Property', date: '06/30/26' },
                  ].map((item, index) => (
                    <div
                      key={index}
                      className="grid grid-cols-3 gap-2 py-3 text-sm hover:bg-[var(--color-surface-sunken)] -mx-4 px-4 transition-colors cursor-pointer"
                    >
                      <span className="text-[var(--color-text-primary)] truncate">
                        {item.name}
                      </span>
                      <span className="text-[var(--color-text-muted)]">
                        {item.lob}
                      </span>
                      <span className="text-[var(--color-text-muted)]">
                        {item.date}
                      </span>
                    </div>
                  ))}
                </>
              )}
            </div>
          </Card>
        </div>
      </motion.div>

      {/* Empty State if no properties */}
      {properties.length === 0 && (
        <motion.div variants={staggerItem}>
          <Card padding="lg">
            <div className="text-center py-12">
              <Building2 className="h-12 w-12 text-[var(--color-text-muted)] mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-2">
                No properties yet
              </h3>
              <p className="text-[var(--color-text-muted)] mb-4 max-w-md mx-auto">
                Upload your insurance documents to get started. Properties will be automatically created from your folder structure.
              </p>
              <Button variant="primary" onClick={handleOpenUploadModal}>
                Upload Documents
              </Button>
            </div>
          </Card>
        </motion.div>
      )}

      {/* Upload Documents Modal */}
      <AnimatePresence>
        {isUploadModalOpen && (
          <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4">
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-black/50 z-[9999]"
              onClick={handleCloseUploadModal}
            />

            {/* Modal */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="relative bg-white rounded-xl shadow-2xl w-full max-w-md z-[10000]"
            >
              {/* Header */}
              <div className="flex items-center justify-between p-5 border-b border-gray-100">
                <h3 className="text-lg font-semibold text-gray-900">Upload Documents</h3>
                <button
                  onClick={handleCloseUploadModal}
                  disabled={isUploading}
                  className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
                >
                  <X className="h-5 w-5 text-gray-400" />
                </button>
              </div>

              {/* Content */}
              <div className="p-5 space-y-4">
                {/* Drop Zone */}
                <div
                  onClick={() => !isUploading && fileInputRef.current?.click()}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all ${
                    isDragging
                      ? 'border-teal-500 bg-teal-50'
                      : isUploading
                      ? 'border-gray-200 bg-gray-50 cursor-not-allowed'
                      : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  <Upload className="h-8 w-8 text-gray-400 mx-auto mb-3" />
                  <p className="text-sm text-gray-600 font-medium">
                    Drag & drop or choose files to upload
                  </p>
                  <p className="text-xs text-gray-400 mt-1">Max file size: 100MB</p>
                </div>

                {/* Upload Progress */}
                {isUploading && uploadProgress && (
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Uploading...</span>
                      <span className="text-sm font-medium text-gray-900">
                        {Math.round((uploadProgress.current / uploadProgress.total) * 100)}%
                      </span>
                    </div>
                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${(uploadProgress.current / uploadProgress.total) * 100}%` }}
                        className="h-full bg-teal-500 rounded-full"
                        style={{ borderColor: '#14B8A6' }}
                      />
                    </div>
                    <p className="text-xs text-gray-400">
                      {formatFileSize(uploadFiles.reduce((acc, f) => acc + (f.status === 'uploading' ? f.file.size * (uploadProgress.current / uploadProgress.total) : f.status === 'confirmed' ? f.file.size : 0), 0))} of {formatFileSize(uploadFiles.reduce((acc, f) => acc + f.file.size, 0))}
                    </p>
                  </div>
                )}

                {/* File List */}
                {uploadFiles.length > 0 && (
                  <div className="space-y-2 max-h-[240px] overflow-y-auto">
                    {uploadFiles.map((fileItem) => (
                      <div
                        key={fileItem.id}
                        className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg border border-gray-100"
                      >
                        {/* File Icon */}
                        <div className="p-2 bg-white rounded-lg border border-gray-100">
                          <FileText className="h-4 w-4 text-gray-400" />
                        </div>

                        {/* File Info */}
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {fileItem.file.name}
                          </p>
                          <p className="text-xs text-gray-400">{formatFileSize(fileItem.file.size)}</p>
                        </div>

                        {/* Property Name Badge */}
                        <div className="flex items-center gap-1.5">
                          <span className="px-2 py-1 text-xs font-medium bg-teal-100 text-teal-700 rounded">
                            {fileItem.propertyName}
                          </span>

                          {/* Document Type Button (opens popup) */}
                          <div className="relative">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                if (!isUploading) {
                                  const rect = e.currentTarget.getBoundingClientRect();
                                  setDocumentTypePopup(
                                    documentTypePopup?.fileId === fileItem.id
                                      ? null
                                      : { fileId: fileItem.id, position: { x: rect.left, y: rect.bottom + 4 } }
                                  );
                                }
                              }}
                              disabled={isUploading}
                              className="px-2 py-1 text-xs font-medium bg-amber-100 text-amber-700 rounded hover:bg-amber-200 transition-colors disabled:opacity-50 flex items-center gap-1"
                            >
                              {fileItem.documentType}
                              <ChevronDown className="h-3 w-3" />
                            </button>
                          </div>
                        </div>

                        {/* Status / Actions */}
                        <div className="flex items-center gap-1">
                          {fileItem.status === 'confirmed' ? (
                            <span className="text-xs text-gray-500">Confirmed</span>
                          ) : fileItem.status === 'uploading' ? (
                            <Loader2 className="h-4 w-4 text-teal-500 animate-spin" />
                          ) : fileItem.status === 'error' ? (
                            <XCircle className="h-4 w-4 text-red-500" />
                          ) : (
                            <button
                              onClick={() => handleConfirmFile(fileItem.id)}
                              disabled={isUploading}
                              className="text-xs text-teal-600 hover:text-teal-700 font-medium disabled:opacity-50"
                            >
                              Confirm
                            </button>
                          )}

                          {/* Delete Button */}
                          {!isUploading && (
                            <button
                              onClick={() => handleRemoveFile(fileItem.id)}
                              className="p-1 hover:bg-gray-200 rounded transition-colors"
                            >
                              <Trash2 className="h-4 w-4 text-gray-400" />
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Document Type Popup */}
                <AnimatePresence>
                  {documentTypePopup && (
                    <>
                      {/* Backdrop to close popup */}
                      <div
                        className="fixed inset-0 z-[10001]"
                        onClick={() => setDocumentTypePopup(null)}
                      />
                      <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: -5 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: -5 }}
                        transition={{ duration: 0.15 }}
                        className="fixed z-[10002] bg-white rounded-lg shadow-xl border border-gray-200 py-1 min-w-[120px]"
                        style={{
                          left: documentTypePopup.position.x,
                          top: documentTypePopup.position.y,
                        }}
                      >
                        {(['SOV', 'COI', 'Binder', 'Policy', 'Other'] as const).map((type) => {
                          const currentFile = uploadFiles.find((f) => f.id === documentTypePopup.fileId);
                          const isSelected = currentFile?.documentType === type;
                          return (
                            <button
                              key={type}
                              onClick={() => {
                                handleUpdateFileType(documentTypePopup.fileId, type);
                                setDocumentTypePopup(null);
                              }}
                              className={`w-full px-4 py-2 text-left text-sm hover:bg-gray-50 transition-colors flex items-center justify-between ${
                                isSelected ? 'text-teal-600 font-medium' : 'text-gray-700'
                              }`}
                            >
                              {type}
                              {isSelected && <CheckCircle className="h-4 w-4 text-teal-600" />}
                            </button>
                          );
                        })}
                      </motion.div>
                    </>
                  )}
                </AnimatePresence>

                {/* Upload Results */}
                {!isUploading && (uploadResults.success > 0 || uploadResults.failed > 0) && (
                  <div className="space-y-2 p-3 bg-gray-50 rounded-lg">
                    {uploadResults.success > 0 && (
                      <div className="flex items-center gap-2 text-sm text-green-600">
                        <CheckCircle className="h-4 w-4" />
                        <span>{uploadResults.success} file{uploadResults.success !== 1 ? 's' : ''} uploaded successfully</span>
                      </div>
                    )}
                    {uploadResults.failed > 0 && (
                      <div className="space-y-1">
                        <div className="flex items-center gap-2 text-sm text-red-600">
                          <XCircle className="h-4 w-4" />
                          <span>{uploadResults.failed} file{uploadResults.failed !== 1 ? 's' : ''} failed</span>
                        </div>
                        {uploadResults.errors.length > 0 && (
                          <div className="text-xs text-red-500 pl-6 space-y-0.5">
                            {uploadResults.errors.slice(0, 3).map((err, i) => (
                              <div key={i}>{err}</div>
                            ))}
                            {uploadResults.errors.length > 3 && (
                              <div>...and {uploadResults.errors.length - 3} more errors</div>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Footer */}
              <div className="flex items-center justify-end gap-3 p-5 border-t border-gray-100">
                <button
                  onClick={handleCloseUploadModal}
                  disabled={isUploading}
                  className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-800 transition-colors disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleUpload}
                  disabled={isUploading || uploadFiles.length === 0}
                  className="px-4 py-2 text-sm font-medium text-white bg-gray-900 hover:bg-gray-800 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {isUploading && <Loader2 className="h-4 w-4 animate-spin" />}
                  Done
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
