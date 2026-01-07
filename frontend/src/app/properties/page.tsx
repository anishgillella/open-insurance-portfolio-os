'use client';

import { useState, useMemo, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Link from 'next/link';
import {
  Search,
  SlidersHorizontal,
  ChevronDown,
  X,
  Building2,
  AlertTriangle,
  Loader2,
  RefreshCw,
  Upload,
  Download,
  Check,
  GripVertical,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/primitives';
import { staggerContainer, staggerItem } from '@/lib/motion/variants';
import {
  propertiesApi,
  type Property,
  type Policy,
  type CoverageExtractionSummary,
} from '@/lib/api';

type ViewMode = 'policy' | 'property';
type SortField = 'property' | 'policyNumber' | 'owner' | 'policyType' | 'address' | 'renewalDate' | 'status' | 'premium';
type SortDirection = 'asc' | 'desc';

// Column configuration with default widths
interface ColumnConfig {
  key: string;
  label: string;
  width: number;
  minWidth: number;
  sortable?: boolean;
  sortField?: SortField;
}

const DEFAULT_COLUMNS: ColumnConfig[] = [
  { key: 'expand', label: '', width: 40, minWidth: 40 },
  { key: 'property', label: 'Property', width: 180, minWidth: 120, sortable: true, sortField: 'property' },
  { key: 'policyNumber', label: 'Policy #', width: 120, minWidth: 80, sortable: true, sortField: 'policyNumber' },
  { key: 'owner', label: 'Owner', width: 140, minWidth: 100, sortable: true, sortField: 'owner' },
  { key: 'policyType', label: 'Policy Type', width: 120, minWidth: 80, sortable: true, sortField: 'policyType' },
  { key: 'address', label: 'Address', width: 160, minWidth: 100, sortable: true, sortField: 'address' },
  { key: 'renewalDate', label: 'Renewal Date', width: 130, minWidth: 100, sortable: true, sortField: 'renewalDate' },
  { key: 'status', label: 'Status', width: 100, minWidth: 80, sortable: true, sortField: 'status' },
  { key: 'premium', label: 'Premium', width: 130, minWidth: 90, sortable: true, sortField: 'premium' },
  { key: 'broker', label: 'Broker', width: 140, minWidth: 100 },
  { key: 'consultant', label: 'Consultant', width: 130, minWidth: 100 },
  { key: 'carrier', label: 'Carrier', width: 140, minWidth: 100 },
  { key: 'management', label: 'Management', width: 150, minWidth: 100 },
  { key: 'compliant', label: 'Compliant', width: 100, minWidth: 80 },
  { key: 'captive', label: 'Captive', width: 100, minWidth: 80 },
];

// Extended property type with policy and display data
interface PropertyRowData {
  id: string;
  propertyName: string;
  policyNumber: string;
  owner: string;
  policyType: string;
  address: string;
  renewalDate: string;
  status: 'Active' | 'Expiring' | 'Expired';
  premium: number;
  broker: string;
  consultant: string;
  carrier: string;
  management: string;
  compliant: boolean | null;
  captive: string;
  coverages: CoverageRowData[];
  isExpanded?: boolean;
}

interface CoverageRowData {
  policyType: string;
  limitType: string;
  dedSir: number;
  premium: number;
  premiumV: number;
}

// Demo data generators for missing fields
const DEMO_BROKERS = ['James & Oak', 'Marsh McLennan', 'Aon Risk', 'Willis Towers'];
const DEMO_CONSULTANTS = ['Zain Pratt', 'Sarah Chen', 'Michael Torres', 'Lisa Wang'];
const DEMO_CARRIERS = ['Plains Insurance', 'Hartford', 'Travelers', 'Chubb', 'AIG'];
const DEMO_MANAGEMENT = ['James & Oak', 'CBRE Group', 'JLL', 'Cushman & Wakefield'];

function getRandomItem<T>(arr: T[], seed: string): T {
  // Simple hash for consistent random selection based on seed
  let hash = 0;
  for (let i = 0; i < seed.length; i++) {
    hash = ((hash << 5) - hash) + seed.charCodeAt(i);
    hash |= 0;
  }
  return arr[Math.abs(hash) % arr.length];
}

function generatePolicyNumber(seed: string): string {
  let hash = 0;
  for (let i = 0; i < seed.length; i++) {
    hash = ((hash << 5) - hash) + seed.charCodeAt(i);
    hash |= 0;
  }
  return String(Math.abs(hash) % 900000 + 100000);
}

export default function PropertiesPage() {
  const [viewMode, setViewMode] = useState<ViewMode>('policy');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortField, setSortField] = useState<SortField>('property');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');
  const [showFilters, setShowFilters] = useState(false);
  const [selectedPropertyModal, setSelectedPropertyModal] = useState<PropertyRowData | null>(null);

  const [properties, setProperties] = useState<Property[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Column widths (resizable)
  const [columnWidths, setColumnWidths] = useState<Record<string, number>>(() => {
    const widths: Record<string, number> = {};
    DEFAULT_COLUMNS.forEach((col) => {
      widths[col.key] = col.width;
    });
    return widths;
  });
  const [resizingColumn, setResizingColumn] = useState<string | null>(null);
  const resizeStartX = useRef<number>(0);
  const resizeStartWidth = useRef<number>(0);
  const tableRef = useRef<HTMLTableElement>(null);

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 15;

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const propertiesData = await propertiesApi.list();
      setProperties(
        Array.isArray(propertiesData) ? propertiesData :
        (propertiesData as { properties?: Property[]; items?: Property[] })?.properties ||
        (propertiesData as { items?: Property[] })?.items || []
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load properties');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Transform properties to row data
  const rowData: PropertyRowData[] = useMemo(() => {
    return properties.map((property) => {
      const seed = property.id;
      const premium = Number(property.total_premium) || 72000.43;
      const renewalDate = property.next_expiration
        ? new Date(property.next_expiration).toLocaleDateString('en-US', { month: '2-digit', day: '2-digit', year: 'numeric' })
        : '03/09/2026';

      // Determine status based on days until expiration
      let status: 'Active' | 'Expiring' | 'Expired' = 'Active';
      if (property.days_until_expiration !== null) {
        if (property.days_until_expiration <= 0) {
          status = 'Expired';
        } else if (property.days_until_expiration <= 30) {
          status = 'Expiring';
        }
      }

      // Generate demo coverages
      const coverages: CoverageRowData[] = [
        { policyType: 'General', limitType: 'Building Limit', dedSir: premium, premium: premium, premiumV: premium },
        { policyType: 'General', limitType: 'Personal Property', dedSir: premium, premium: premium, premiumV: premium },
        { policyType: 'General', limitType: 'Business Income', dedSir: premium, premium: premium, premiumV: premium },
      ];

      return {
        id: property.id,
        propertyName: property.name || 'Property Name',
        policyNumber: generatePolicyNumber(seed),
        owner: 'Channel Capital',
        policyType: 'Property',
        address: `${property.address?.city || 'New York'}, ${property.address?.state || 'NY'}`,
        renewalDate,
        status,
        premium,
        broker: getRandomItem(DEMO_BROKERS, seed + 'broker'),
        consultant: getRandomItem(DEMO_CONSULTANTS, seed + 'consultant'),
        carrier: getRandomItem(DEMO_CARRIERS, seed + 'carrier'),
        management: getRandomItem(DEMO_MANAGEMENT, seed + 'management'),
        compliant: Math.random() > 0.3 ? true : (Math.random() > 0.5 ? false : null),
        captive: 'Type',
        coverages,
      };
    });
  }, [properties]);

  // Filter and sort data
  const filteredAndSortedData = useMemo(() => {
    let result = [...rowData];

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (row) =>
          row.propertyName.toLowerCase().includes(query) ||
          row.policyNumber.includes(query) ||
          row.address.toLowerCase().includes(query) ||
          row.carrier.toLowerCase().includes(query)
      );
    }

    // Sort
    result.sort((a, b) => {
      let comparison = 0;
      switch (sortField) {
        case 'property':
          comparison = a.propertyName.localeCompare(b.propertyName);
          break;
        case 'policyNumber':
          comparison = a.policyNumber.localeCompare(b.policyNumber);
          break;
        case 'owner':
          comparison = a.owner.localeCompare(b.owner);
          break;
        case 'policyType':
          comparison = a.policyType.localeCompare(b.policyType);
          break;
        case 'address':
          comparison = a.address.localeCompare(b.address);
          break;
        case 'renewalDate':
          comparison = new Date(a.renewalDate).getTime() - new Date(b.renewalDate).getTime();
          break;
        case 'status':
          comparison = a.status.localeCompare(b.status);
          break;
        case 'premium':
          comparison = a.premium - b.premium;
          break;
      }
      return sortDirection === 'asc' ? comparison : -comparison;
    });

    return result;
  }, [rowData, searchQuery, sortField, sortDirection]);

  // Pagination
  const totalPages = Math.ceil(filteredAndSortedData.length / itemsPerPage);
  const paginatedData = filteredAndSortedData.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const handleRowClick = (row: PropertyRowData) => {
    setSelectedPropertyModal(row);
  };

  const closePropertyModal = () => {
    setSelectedPropertyModal(null);
  };

  // Column resize handlers
  const handleResizeStart = useCallback((e: React.MouseEvent, columnKey: string) => {
    e.preventDefault();
    e.stopPropagation();
    setResizingColumn(columnKey);
    resizeStartX.current = e.clientX;
    resizeStartWidth.current = columnWidths[columnKey];
  }, [columnWidths]);

  const handleResizeMove = useCallback((e: MouseEvent) => {
    if (!resizingColumn) return;

    const diff = e.clientX - resizeStartX.current;
    const column = DEFAULT_COLUMNS.find((c) => c.key === resizingColumn);
    const newWidth = Math.max(column?.minWidth || 50, resizeStartWidth.current + diff);

    setColumnWidths((prev) => ({
      ...prev,
      [resizingColumn]: newWidth,
    }));
  }, [resizingColumn]);

  const handleResizeEnd = useCallback(() => {
    setResizingColumn(null);
  }, []);

  useEffect(() => {
    if (resizingColumn) {
      document.addEventListener('mousemove', handleResizeMove);
      document.addEventListener('mouseup', handleResizeEnd);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
      return () => {
        document.removeEventListener('mousemove', handleResizeMove);
        document.removeEventListener('mouseup', handleResizeEnd);
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
      };
    }
  }, [resizingColumn, handleResizeMove, handleResizeEnd]);

  // Calculate total table width
  const totalTableWidth = useMemo(() => {
    return Object.values(columnWidths).reduce((sum, w) => sum + w, 0);
  }, [columnWidths]);

  const formatCurrency = (value: number) => {
    return `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const SortableHeader = ({ field, children, className }: { field: SortField; children: React.ReactNode; className?: string }) => (
    <th
      className={cn(
        'px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-50 whitespace-nowrap',
        className
      )}
      onClick={() => handleSort(field)}
    >
      <div className="flex items-center gap-1">
        {children}
        {sortField === field && (
          <span className="text-gray-400">{sortDirection === 'asc' ? '↑' : '↓'}</span>
        )}
      </div>
    </th>
  );

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
      className="space-y-4"
    >
      {/* Header */}
      <motion.div variants={staggerItem} className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-gray-900">Properties &amp; Policies</h1>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {}}
            leftIcon={<Upload className="h-4 w-4" />}
            className="text-gray-500 hover:text-gray-700"
          >
            Upload Document
          </Button>
        </div>
      </motion.div>

      {/* Toolbar */}
      <motion.div variants={staggerItem} className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        {/* Left side - Search */}
        <div className="relative w-full sm:w-64">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className={cn(
              'w-full pl-10 pr-4 py-2 rounded-lg',
              'bg-white border border-gray-200',
              'text-sm text-gray-900',
              'placeholder:text-gray-400',
              'focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent',
              'transition-all'
            )}
          />
        </div>

        {/* Center - View Toggle with Switch */}
        <div className="flex items-center gap-3">
          <span className={cn(
            'text-sm font-medium transition-colors',
            viewMode === 'policy' ? 'text-gray-900' : 'text-gray-400'
          )}>
            Policy View
          </span>
          <button
            onClick={() => setViewMode(viewMode === 'policy' ? 'property' : 'policy')}
            className={cn(
              'relative w-12 h-6 rounded-full transition-colors',
              viewMode === 'property' ? 'bg-teal-500' : 'bg-gray-300'
            )}
          >
            <span
              className={cn(
                'absolute top-1 w-4 h-4 bg-white rounded-full transition-transform shadow-sm',
                viewMode === 'property' ? 'translate-x-7' : 'translate-x-1'
              )}
            />
          </button>
          <span className={cn(
            'text-sm font-medium transition-colors',
            viewMode === 'property' ? 'text-gray-900' : 'text-gray-400'
          )}>
            Property View
          </span>
        </div>

        {/* Right side - Actions */}
        <div className="flex items-center gap-2">
          <button className="flex items-center gap-1.5 px-3 py-2 text-sm text-gray-600 hover:text-gray-900 border border-gray-200 rounded-lg transition-colors">
            <SlidersHorizontal className="h-4 w-4" />
            Sort by
          </button>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={cn(
              'flex items-center gap-1.5 px-3 py-2 text-sm border border-gray-200 rounded-lg transition-colors',
              showFilters ? 'text-teal-600 border-teal-300' : 'text-gray-600 hover:text-gray-900'
            )}
          >
            <SlidersHorizontal className="h-4 w-4" />
            Filters
          </button>
          <button className="flex items-center gap-1.5 px-3 py-2 text-sm text-gray-600 hover:text-gray-900 border border-gray-200 rounded-lg transition-colors">
            <Download className="h-4 w-4" />
            Export
          </button>
        </div>
      </motion.div>

      {/* Table */}
      <motion.div variants={staggerItem} className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table ref={tableRef} className="border-collapse" style={{ width: totalTableWidth, minWidth: totalTableWidth }}>
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                {DEFAULT_COLUMNS.map((col, colIndex) => (
                  <th
                    key={col.key}
                    className="relative text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap select-none"
                    style={{ width: columnWidths[col.key], minWidth: col.minWidth }}
                  >
                    <div
                      className={cn(
                        'px-4 py-3 flex items-center gap-1',
                        col.sortable && 'cursor-pointer hover:bg-gray-100'
                      )}
                      onClick={() => col.sortField && handleSort(col.sortField)}
                    >
                      {col.label}
                      {col.sortable && (
                        <span className={cn(
                          'text-gray-400',
                          sortField === col.sortField && 'text-gray-600'
                        )}>
                          ↑↓
                        </span>
                      )}
                    </div>
                    {/* Resize handle */}
                    {colIndex < DEFAULT_COLUMNS.length - 1 && (
                      <div
                        className={cn(
                          'absolute right-0 top-0 bottom-0 w-1 cursor-col-resize group hover:bg-teal-500 transition-colors',
                          resizingColumn === col.key && 'bg-teal-500'
                        )}
                        onMouseDown={(e) => handleResizeStart(e, col.key)}
                      >
                        <div className="absolute right-0 top-1/2 -translate-y-1/2 w-4 h-6 -translate-x-1.5 flex items-center justify-center opacity-0 group-hover:opacity-100">
                          <GripVertical className="h-4 w-4 text-gray-400" />
                        </div>
                      </div>
                    )}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {paginatedData.map((row) => (
                <tr
                  key={row.id}
                  className="hover:bg-gray-50 cursor-pointer transition-colors"
                  onClick={() => handleRowClick(row)}
                >
                  {/* Spacer column */}
                  <td className="px-4 py-3" style={{ width: columnWidths.expand }} />
                  {/* Property */}
                  <td className="px-4 py-3" style={{ width: columnWidths.property }}>
                    <div className="flex items-center gap-2">
                      <div className="w-6 h-6 rounded-full bg-purple-100 flex items-center justify-center flex-shrink-0">
                        <Building2 className="h-3 w-3 text-purple-600" />
                      </div>
                      <span className="text-sm font-medium text-gray-900 truncate">{row.propertyName}</span>
                    </div>
                  </td>
                  {/* Policy # */}
                  <td className="px-4 py-3 text-sm text-gray-600 truncate" style={{ width: columnWidths.policyNumber }}>{row.policyNumber}</td>
                  {/* Owner */}
                  <td className="px-4 py-3 text-sm text-gray-600 truncate" style={{ width: columnWidths.owner }}>{row.owner}</td>
                  {/* Policy Type */}
                  <td className="px-4 py-3 text-sm text-gray-600 truncate" style={{ width: columnWidths.policyType }}>{row.policyType}</td>
                  {/* Address */}
                  <td className="px-4 py-3 text-sm text-gray-600 truncate" style={{ width: columnWidths.address }}>{row.address}</td>
                  {/* Renewal Date */}
                  <td className="px-4 py-3 text-sm text-gray-600 truncate" style={{ width: columnWidths.renewalDate }}>{row.renewalDate}</td>
                  {/* Status */}
                  <td className="px-4 py-3" style={{ width: columnWidths.status }}>
                    <span
                      className={cn(
                        'inline-flex px-2 py-0.5 text-xs font-medium rounded-full',
                        row.status === 'Active' && 'bg-green-100 text-green-700',
                        row.status === 'Expiring' && 'bg-yellow-100 text-yellow-700',
                        row.status === 'Expired' && 'bg-red-100 text-red-700'
                      )}
                    >
                      {row.status}
                    </span>
                  </td>
                  {/* Premium */}
                  <td className="px-4 py-3 text-sm text-gray-900 font-medium truncate" style={{ width: columnWidths.premium }}>{formatCurrency(row.premium)}</td>
                  {/* Broker */}
                  <td className="px-4 py-3 text-sm text-gray-600 truncate" style={{ width: columnWidths.broker }}>{row.broker}</td>
                  {/* Consultant */}
                  <td className="px-4 py-3 text-sm text-gray-600 truncate" style={{ width: columnWidths.consultant }}>{row.consultant}</td>
                  {/* Carrier */}
                  <td className="px-4 py-3 text-sm text-gray-600 truncate" style={{ width: columnWidths.carrier }}>{row.carrier}</td>
                  {/* Management */}
                  <td className="px-4 py-3 text-sm text-gray-600 truncate" style={{ width: columnWidths.management }}>{row.management}</td>
                  {/* Compliant */}
                  <td className="px-4 py-3" style={{ width: columnWidths.compliant }}>
                    {row.compliant === true ? (
                      <div className="w-5 h-5 rounded bg-green-500 flex items-center justify-center">
                        <Check className="h-3 w-3 text-white" />
                      </div>
                    ) : row.compliant === false ? (
                      <div className="w-5 h-5 rounded bg-red-500 flex items-center justify-center">
                        <X className="h-3 w-3 text-white" />
                      </div>
                    ) : (
                      <div className="w-5 h-5 rounded bg-yellow-500 flex items-center justify-center">
                        <span className="text-white text-xs font-bold">!</span>
                      </div>
                    )}
                  </td>
                  {/* Captive */}
                  <td className="px-4 py-3 text-sm text-gray-600 truncate" style={{ width: columnWidths.captive }}>{row.captive}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200 bg-white">
          <div className="text-sm text-gray-500">
            Showing {((currentPage - 1) * itemsPerPage) + 1} to {Math.min(currentPage * itemsPerPage, filteredAndSortedData.length)} of {filteredAndSortedData.length} results
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="px-3 py-1 text-sm text-gray-600 hover:bg-gray-100 rounded disabled:opacity-50 disabled:cursor-not-allowed"
            >
              &lt;
            </button>
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              let pageNum: number;
              if (totalPages <= 5) {
                pageNum = i + 1;
              } else if (currentPage <= 3) {
                pageNum = i + 1;
              } else if (currentPage >= totalPages - 2) {
                pageNum = totalPages - 4 + i;
              } else {
                pageNum = currentPage - 2 + i;
              }
              return (
                <button
                  key={pageNum}
                  onClick={() => setCurrentPage(pageNum)}
                  className={cn(
                    'px-3 py-1 text-sm rounded transition-colors',
                    currentPage === pageNum
                      ? 'bg-gray-900 text-white'
                      : 'text-gray-600 hover:bg-gray-100'
                  )}
                >
                  {pageNum}
                </button>
              );
            })}
            {totalPages > 5 && currentPage < totalPages - 2 && (
              <>
                <span className="px-2 text-gray-400">...</span>
                <button
                  onClick={() => setCurrentPage(totalPages)}
                  className="px-3 py-1 text-sm text-gray-600 hover:bg-gray-100 rounded"
                >
                  {totalPages}
                </button>
              </>
            )}
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-1 text-sm text-gray-600 hover:bg-gray-100 rounded disabled:opacity-50 disabled:cursor-not-allowed"
            >
              &gt;
            </button>
          </div>
        </div>
      </motion.div>

      {/* Empty State */}
      {filteredAndSortedData.length === 0 && (
        <motion.div
          variants={staggerItem}
          className="text-center py-16"
        >
          <Building2 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            {properties.length === 0 ? 'No properties yet' : 'No properties found'}
          </h3>
          <p className="text-gray-500 mb-4">
            {properties.length === 0
              ? 'Upload documents to create properties automatically'
              : 'Try adjusting your search or filters'}
          </p>
          {properties.length === 0 ? (
            <Link href="/documents">
              <Button variant="primary">Upload Documents</Button>
            </Link>
          ) : (
            <Button variant="secondary" onClick={() => setSearchQuery('')}>
              Clear search
            </Button>
          )}
        </motion.div>
      )}

      {/* Coverage Details Modal */}
      <AnimatePresence>
        {selectedPropertyModal && (
          <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4">
            {/* Blurred Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-black/40 backdrop-blur-sm z-[9999]"
              onClick={closePropertyModal}
            />

            {/* Modal */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ duration: 0.2, ease: [0.25, 0.46, 0.45, 0.94] }}
              className="relative bg-white rounded-xl shadow-2xl w-full max-w-2xl z-[10000] overflow-hidden"
            >
              {/* Modal Header */}
              <div className="flex items-center justify-between p-5 border-b border-gray-100">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-purple-100 flex items-center justify-center">
                    <Building2 className="h-5 w-5 text-purple-600" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{selectedPropertyModal.propertyName}</h3>
                    <p className="text-sm text-gray-500">{selectedPropertyModal.address}</p>
                  </div>
                </div>
                <button
                  onClick={closePropertyModal}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <X className="h-5 w-5 text-gray-400" />
                </button>
              </div>

              {/* Modal Content - Coverage Table */}
              <div className="p-5">
                <div className="overflow-hidden rounded-lg border border-gray-200">
                  <table className="w-full">
                    <thead>
                      <tr className="bg-teal-500 text-white">
                        <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider">Policy Type</th>
                        <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider">Limit Type</th>
                        <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider">DED/SIR</th>
                        <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider">Premium</th>
                        <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider">Premium/V</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-100">
                      {selectedPropertyModal.coverages.map((coverage, idx) => (
                        <tr key={idx} className="hover:bg-gray-50">
                          <td className="px-4 py-3 text-sm text-gray-600">{coverage.policyType}</td>
                          <td className="px-4 py-3 text-sm text-gray-600">{coverage.limitType}</td>
                          <td className="px-4 py-3 text-sm text-gray-600">{formatCurrency(coverage.dedSir)}</td>
                          <td className="px-4 py-3 text-sm text-gray-600">{formatCurrency(coverage.premium)}</td>
                          <td className="px-4 py-3 text-sm text-gray-600">{formatCurrency(coverage.premiumV)}</td>
                        </tr>
                      ))}
                      {/* Total Row */}
                      <tr className="bg-gray-50 font-medium">
                        <td className="px-4 py-3 text-sm text-gray-900" colSpan={2}>Total</td>
                        <td className="px-4 py-3 text-sm text-gray-900">
                          {formatCurrency(selectedPropertyModal.coverages.reduce((sum, c) => sum + c.dedSir, 0))}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900">
                          {formatCurrency(selectedPropertyModal.coverages.reduce((sum, c) => sum + c.premium, 0))}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900">
                          {formatCurrency(selectedPropertyModal.coverages.reduce((sum, c) => sum + c.premiumV, 0))}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Modal Footer */}
              <div className="flex items-center justify-end gap-3 p-5 border-t border-gray-100 bg-gray-50">
                <button
                  onClick={closePropertyModal}
                  className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-800 transition-colors"
                >
                  Close
                </button>
                <Link href={`/properties/${selectedPropertyModal.id}`}>
                  <button className="px-4 py-2 text-sm font-medium text-white bg-gray-900 hover:bg-gray-800 rounded-lg transition-colors">
                    View Property Details
                  </button>
                </Link>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
