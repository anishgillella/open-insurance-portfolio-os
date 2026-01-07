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
  { key: 'checkbox', label: '', width: 40, minWidth: 40 },
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
  city: string;
  state: string;
  renewalDate: string;
  renewalDateObj: Date;
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

  // Active filters - each filter has a field, operator, and value
  interface ActiveFilter {
    id: string;
    field: string;
    operator: 'is' | 'contains';
    value: string;
  }
  const [activeFilters, setActiveFilters] = useState<ActiveFilter[]>([]);
  const [showFilterDropdown, setShowFilterDropdown] = useState(false);
  const filterDropdownRef = useRef<HTMLDivElement>(null);

  // Selection state
  const [selectedRows, setSelectedRows] = useState<Set<string>>(new Set());

  // Export modal state
  const [showExportModal, setShowExportModal] = useState(false);
  const [exportSOV, setExportSOV] = useState(false);
  const [exportDocuments, setExportDocuments] = useState(true);
  const [exportCSV, setExportCSV] = useState(false);

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

      const city = property.address?.city || 'New York';
      const state = property.address?.state || 'NY';
      const renewalDateObj = property.next_expiration ? new Date(property.next_expiration) : new Date('2026-03-09');

      return {
        id: property.id,
        propertyName: property.name || 'Property Name',
        policyNumber: generatePolicyNumber(seed),
        owner: 'Channel Capital',
        policyType: 'Property',
        address: `${city}, ${state}`,
        city,
        state,
        renewalDate,
        renewalDateObj,
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

  // Filter field definitions
  const FILTER_FIELDS = [
    { key: 'property', label: 'Property', type: 'select' as const },
    { key: 'owner', label: 'Owner', type: 'select' as const },
    { key: 'policyType', label: 'Policy Type', type: 'select' as const },
    { key: 'city', label: 'City', type: 'select' as const },
    { key: 'state', label: 'State', type: 'select' as const },
    { key: 'expirationDate', label: 'Expiration Date', type: 'range' as const },
    { key: 'status', label: 'Status', type: 'select' as const },
    { key: 'premium', label: 'Premium', type: 'range' as const },
    { key: 'broker', label: 'Broker', type: 'select' as const },
    { key: 'consultant', label: 'Consultant', type: 'select' as const },
    { key: 'carrier', label: 'Carrier', type: 'select' as const },
    { key: 'management', label: 'Management Company', type: 'select' as const },
    { key: 'compliance', label: 'Compliance Status', type: 'select' as const },
    { key: 'captive', label: 'Captive Participation', type: 'select' as const },
  ];

  // Extract unique filter options from data
  const filterValueOptions = useMemo(() => {
    return {
      property: [...new Set(rowData.map((r) => r.propertyName))].sort(),
      owner: [...new Set(rowData.map((r) => r.owner))].sort(),
      policyType: [...new Set(rowData.map((r) => r.policyType))].sort(),
      city: [...new Set(rowData.map((r) => r.city))].sort(),
      state: [...new Set(rowData.map((r) => r.state))].sort(),
      expirationDate: [
        { value: 'expired', label: 'Expired' },
        { value: '30days', label: 'Within 30 Days' },
        { value: '60days', label: 'Within 60 Days' },
        { value: '90days', label: 'Within 90 Days' },
        { value: '6months', label: 'Within 6 Months' },
        { value: '1year', label: 'Within 1 Year' },
      ],
      status: ['Active', 'Expiring', 'Expired'],
      premium: [
        { value: 'under25k', label: 'Under $25,000' },
        { value: '25k-50k', label: '$25,000 - $50,000' },
        { value: '50k-100k', label: '$50,000 - $100,000' },
        { value: '100k-250k', label: '$100,000 - $250,000' },
        { value: 'over250k', label: 'Over $250,000' },
      ],
      broker: [...new Set(rowData.map((r) => r.broker))].sort(),
      consultant: [...new Set(rowData.map((r) => r.consultant))].sort(),
      carrier: [...new Set(rowData.map((r) => r.carrier))].sort(),
      management: [...new Set(rowData.map((r) => r.management))].sort(),
      compliance: [
        { value: 'compliant', label: 'Compliant' },
        { value: 'non-compliant', label: 'Non-Compliant' },
        { value: 'pending', label: 'Pending Review' },
      ],
      captive: [...new Set(rowData.map((r) => r.captive))].sort(),
    };
  }, [rowData]);

  // Check if any filters are active
  const hasActiveFilters = activeFilters.length > 0;
  const activeFilterCount = activeFilters.length;

  // Add a new filter
  const addFilter = (fieldKey: string) => {
    const newFilter: ActiveFilter = {
      id: `${fieldKey}-${Date.now()}`,
      field: fieldKey,
      operator: 'is',
      value: '',
    };
    setActiveFilters([...activeFilters, newFilter]);
    setShowFilterDropdown(false);
  };

  // Update a filter value
  const updateFilter = (filterId: string, updates: Partial<ActiveFilter>) => {
    setActiveFilters(activeFilters.map((f) =>
      f.id === filterId ? { ...f, ...updates } : f
    ));
  };

  // Remove a filter
  const removeFilter = (filterId: string) => {
    setActiveFilters(activeFilters.filter((f) => f.id !== filterId));
  };

  // Clear all filters
  const clearFilters = () => {
    setActiveFilters([]);
  };

  // Selection handlers
  const toggleRowSelection = (id: string) => {
    const newSelected = new Set(selectedRows);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedRows(newSelected);
  };

  // Export handler
  const handleExport = () => {
    // For now, just close the modal - actual export logic would go here
    console.log('Exporting...', {
      selectedRows: Array.from(selectedRows),
      exportSOV,
      exportDocuments,
      exportCSV,
    });
    setShowExportModal(false);
    // Reset export options
    setExportSOV(false);
    setExportDocuments(true);
    setExportCSV(false);
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (filterDropdownRef.current && !filterDropdownRef.current.contains(event.target as Node)) {
        setShowFilterDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

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

    // Apply active filters
    activeFilters.forEach((filter) => {
      if (!filter.value) return; // Skip filters without values

      result = result.filter((row) => {
        const today = new Date();
        switch (filter.field) {
          case 'property':
            return row.propertyName === filter.value;
          case 'owner':
            return row.owner === filter.value;
          case 'policyType':
            return row.policyType === filter.value;
          case 'city':
            return row.city === filter.value;
          case 'state':
            return row.state === filter.value;
          case 'expirationDate': {
            const daysUntil = Math.ceil((row.renewalDateObj.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
            switch (filter.value) {
              case 'expired': return daysUntil < 0;
              case '30days': return daysUntil >= 0 && daysUntil <= 30;
              case '60days': return daysUntil >= 0 && daysUntil <= 60;
              case '90days': return daysUntil >= 0 && daysUntil <= 90;
              case '6months': return daysUntil >= 0 && daysUntil <= 180;
              case '1year': return daysUntil >= 0 && daysUntil <= 365;
              default: return true;
            }
          }
          case 'status':
            return row.status === filter.value;
          case 'premium':
            switch (filter.value) {
              case 'under25k': return row.premium < 25000;
              case '25k-50k': return row.premium >= 25000 && row.premium < 50000;
              case '50k-100k': return row.premium >= 50000 && row.premium < 100000;
              case '100k-250k': return row.premium >= 100000 && row.premium < 250000;
              case 'over250k': return row.premium >= 250000;
              default: return true;
            }
          case 'broker':
            return row.broker === filter.value;
          case 'consultant':
            return row.consultant === filter.value;
          case 'carrier':
            return row.carrier === filter.value;
          case 'management':
            return row.management === filter.value;
          case 'compliance':
            switch (filter.value) {
              case 'compliant': return row.compliant === true;
              case 'non-compliant': return row.compliant === false;
              case 'pending': return row.compliant === null;
              default: return true;
            }
          case 'captive':
            return row.captive === filter.value;
          default:
            return true;
        }
      });
    });

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
  }, [rowData, searchQuery, sortField, sortDirection, activeFilters]);

  // Pagination
  const totalPages = Math.ceil(filteredAndSortedData.length / itemsPerPage);
  const paginatedData = filteredAndSortedData.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  // Selection computed values (must be after paginatedData)
  const toggleSelectAll = () => {
    if (selectedRows.size === paginatedData.length) {
      setSelectedRows(new Set());
    } else {
      setSelectedRows(new Set(paginatedData.map((row) => row.id)));
    }
  };

  const isAllSelected = paginatedData.length > 0 && selectedRows.size === paginatedData.length;
  const isSomeSelected = selectedRows.size > 0 && selectedRows.size < paginatedData.length;

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
              showFilters ? 'text-teal-600 border-teal-300 bg-teal-50' : 'text-gray-600 hover:text-gray-900'
            )}
          >
            <SlidersHorizontal className="h-4 w-4" />
            Filters
            {activeFilterCount > 0 && (
              <span className="ml-1 px-1.5 py-0.5 text-xs font-medium bg-teal-500 text-white rounded-full">
                {activeFilterCount}
              </span>
            )}
          </button>
          <button
            onClick={() => setShowExportModal(true)}
            className="flex items-center gap-1.5 px-3 py-2 text-sm text-gray-600 hover:text-gray-900 border border-gray-200 rounded-lg transition-colors"
          >
            <Download className="h-4 w-4" />
            Download
          </button>
        </div>
      </motion.div>

      {/* Filter Panel */}
      <AnimatePresence>
        {showFilters && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-visible"
          >
            <div className="bg-white rounded-xl border border-gray-200 p-4 relative z-20">
              {/* Header with title and clear all */}
              <div className="flex items-center justify-between mb-4">
                <span className="text-sm font-medium text-gray-700">Filters</span>
                {hasActiveFilters && (
                  <button
                    onClick={clearFilters}
                    className="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1"
                  >
                    <X className="h-3.5 w-3.5" />
                    Clear All
                  </button>
                )}
              </div>

              {/* Active Filters */}
              <div className="space-y-3">
                {activeFilters.map((filter) => {
                  const fieldDef = FILTER_FIELDS.find((f) => f.key === filter.field);
                  const options = filterValueOptions[filter.field as keyof typeof filterValueOptions] || [];

                  return (
                    <div key={filter.id} className="flex items-center gap-2">
                      {/* Field Name */}
                      <select
                        value={filter.field}
                        onChange={(e) => updateFilter(filter.id, { field: e.target.value, value: '' })}
                        className="px-3 py-2 text-sm rounded-lg border border-gray-200 bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent min-w-[160px]"
                      >
                        {FILTER_FIELDS.map((f) => (
                          <option key={f.key} value={f.key}>{f.label}</option>
                        ))}
                      </select>

                      {/* Operator */}
                      <select
                        value={filter.operator}
                        onChange={(e) => updateFilter(filter.id, { operator: e.target.value as 'is' | 'contains' })}
                        className="px-3 py-2 text-sm rounded-lg border border-gray-200 bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent w-24"
                      >
                        <option value="is">is</option>
                      </select>

                      {/* Value */}
                      <select
                        value={filter.value}
                        onChange={(e) => updateFilter(filter.id, { value: e.target.value })}
                        className="flex-1 px-3 py-2 text-sm rounded-lg border border-gray-200 bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent min-w-[200px]"
                      >
                        <option value="">Select value...</option>
                        {Array.isArray(options) && options.map((opt) => {
                          if (typeof opt === 'string') {
                            return <option key={opt} value={opt}>{opt}</option>;
                          } else if (typeof opt === 'object' && opt !== null && 'value' in opt) {
                            return <option key={opt.value} value={opt.value}>{opt.label}</option>;
                          }
                          return null;
                        })}
                      </select>

                      {/* Remove Button */}
                      <button
                        onClick={() => removeFilter(filter.id)}
                        className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  );
                })}

                {/* Select Filter Dropdown */}
                <div className="relative" ref={filterDropdownRef}>
                  <button
                    onClick={() => setShowFilterDropdown(!showFilterDropdown)}
                    className={cn(
                      'flex items-center justify-between gap-2 px-3 py-2 text-sm rounded-lg border border-gray-200 bg-white min-w-[180px] transition-colors',
                      showFilterDropdown ? 'border-teal-500 ring-2 ring-teal-500' : 'hover:border-gray-300'
                    )}
                  >
                    <span className="text-gray-500">Select Filter</span>
                    <ChevronDown className={cn(
                      'h-4 w-4 text-gray-400 transition-transform',
                      showFilterDropdown && 'rotate-180'
                    )} />
                  </button>

                  {/* Dropdown Menu */}
                  {showFilterDropdown && (
                    <div className="absolute top-full left-0 mt-1 w-64 bg-white rounded-lg border border-gray-200 shadow-xl z-[100] py-1 max-h-80 overflow-y-auto">
                      {FILTER_FIELDS.map((field) => (
                        <button
                          key={field.key}
                          onClick={() => addFilter(field.key)}
                          className="w-full px-4 py-2 text-sm text-left text-gray-700 hover:bg-gray-50 transition-colors"
                        >
                          {field.label}
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {/* + Add Filter link */}
                {activeFilters.length > 0 && (
                  <button
                    onClick={() => setShowFilterDropdown(true)}
                    className="flex items-center gap-1.5 text-sm text-teal-600 hover:text-teal-700 font-medium py-2"
                  >
                    <span className="text-lg leading-none">+</span>
                    Add Filter
                  </button>
                )}
              </div>

              {/* Results count */}
              {hasActiveFilters && (
                <div className="mt-4 pt-4 border-t border-gray-100">
                  <span className="text-sm text-gray-500">
                    Showing {filteredAndSortedData.length} of {rowData.length} results
                  </span>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

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
                    {col.key === 'checkbox' ? (
                      <div className="px-4 py-3 flex items-center justify-center">
                        <input
                          type="checkbox"
                          checked={isAllSelected}
                          ref={(el) => {
                            if (el) el.indeterminate = isSomeSelected;
                          }}
                          onChange={toggleSelectAll}
                          className="h-4 w-4 rounded border-gray-300 text-teal-600 focus:ring-teal-500 cursor-pointer"
                        />
                      </div>
                    ) : (
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
                    )}
                    {/* Resize handle */}
                    {colIndex < DEFAULT_COLUMNS.length - 1 && col.key !== 'checkbox' && (
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
                  className={cn(
                    'hover:bg-gray-50 cursor-pointer transition-colors',
                    selectedRows.has(row.id) && 'bg-teal-50'
                  )}
                  onClick={() => handleRowClick(row)}
                >
                  {/* Checkbox column */}
                  <td
                    className="px-4 py-3"
                    style={{ width: columnWidths.checkbox }}
                    onClick={(e) => e.stopPropagation()}
                  >
                    <div className="flex items-center justify-center">
                      <input
                        type="checkbox"
                        checked={selectedRows.has(row.id)}
                        onChange={() => toggleRowSelection(row.id)}
                        className="h-4 w-4 rounded border-gray-300 text-teal-600 focus:ring-teal-500 cursor-pointer"
                      />
                    </div>
                  </td>
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

      {/* Property Details Slide-Over Panel */}
      <AnimatePresence>
        {selectedPropertyModal && (
          <div className="fixed inset-0 z-[9999]">
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-black/40"
              onClick={closePropertyModal}
            />

            {/* Slide-over Panel */}
            <motion.div
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 30, stiffness: 300 }}
              className="absolute right-0 top-0 h-full w-full max-w-4xl bg-white shadow-2xl overflow-hidden flex flex-col"
            >
              {/* Panel Header */}
              <div className="flex-shrink-0 border-b border-gray-200 bg-white">
                {/* Last Updated Badge */}
                <div className="px-6 pt-4">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-700 border border-gray-200">
                    Last Updated {new Date().toLocaleDateString('en-US', { month: '2-digit', day: '2-digit', year: 'numeric' })}
                  </span>
                </div>

                {/* Title and Actions */}
                <div className="flex items-start justify-between px-6 py-4">
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900">{selectedPropertyModal.propertyName}</h2>
                    <p className="text-sm text-gray-500">{selectedPropertyModal.address}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <button className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 border border-gray-200 rounded-lg transition-colors">
                      <Upload className="h-4 w-4" />
                      Upload
                    </button>
                    <button className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 border border-gray-200 rounded-lg transition-colors">
                      <Pencil className="h-4 w-4" />
                      Edit
                    </button>
                    <button className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 border border-gray-200 rounded-lg transition-colors">
                      <Download className="h-4 w-4" />
                      Export
                    </button>
                    <button className="p-1.5 text-gray-400 hover:text-gray-600 border border-gray-200 rounded-lg transition-colors">
                      <MoreHorizontal className="h-4 w-4" />
                    </button>
                    <button
                      onClick={closePropertyModal}
                      className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors ml-2"
                    >
                      <X className="h-5 w-5" />
                    </button>
                  </div>
                </div>
              </div>

              {/* Scrollable Content */}
              <div className="flex-1 overflow-y-auto">
                <div className="p-6 space-y-8">
                  {/* Details Section */}
                  <section>
                    <h3 className="text-sm font-semibold text-gray-900 mb-4">Details</h3>
                    <div className="grid grid-cols-4 lg:grid-cols-8 gap-3">
                      <div className="p-3 border border-gray-200 rounded-lg">
                        <p className="text-xs text-gray-500 mb-1">Units</p>
                        <p className="text-lg font-semibold text-gray-900">100</p>
                      </div>
                      <div className="p-3 border border-gray-200 rounded-lg">
                        <p className="text-xs text-gray-500 mb-1">Deductible</p>
                        <p className="text-lg font-semibold text-gray-900">10</p>
                      </div>
                      <div className="p-3 border border-gray-200 rounded-lg">
                        <p className="text-xs text-gray-500 mb-1">Total Premium</p>
                        <p className="text-lg font-semibold text-gray-900">{formatCurrency(selectedPropertyModal.premium)}</p>
                      </div>
                      <div className="p-3 border border-gray-200 rounded-lg">
                        <p className="text-xs text-gray-500 mb-1">Ins/U</p>
                        <p className="text-lg font-semibold text-gray-900">20</p>
                      </div>
                      <div className="p-3 border border-gray-200 rounded-lg">
                        <p className="text-xs text-gray-500 mb-1">Renewals Date</p>
                        <p className="text-lg font-semibold text-gray-900">{selectedPropertyModal.renewalDate}</p>
                      </div>
                      <div className="p-3 border border-gray-200 rounded-lg">
                        <p className="text-xs text-gray-500 mb-1">Claims / Claim $</p>
                        <p className="text-lg font-semibold text-gray-900">2/~$400k</p>
                      </div>
                      <div className="p-3 border border-gray-200 rounded-lg">
                        <p className="text-xs text-gray-500 mb-1">Policies</p>
                        <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-teal-500 text-white text-sm font-semibold">03</span>
                      </div>
                      <div className="p-3 border border-gray-200 rounded-lg">
                        <p className="text-xs text-gray-500 mb-1">Carriers</p>
                        <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-teal-500 text-white text-sm font-semibold">03</span>
                      </div>
                    </div>
                  </section>

                  {/* Coverage Section */}
                  <section>
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-sm font-semibold text-gray-900">Coverage (3 Policies)</h3>
                      <div className="flex gap-2">
                        <button className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-teal-700 bg-white border-2 border-teal-500 rounded-full">
                          <Check className="h-4 w-4" />
                          General - {selectedPropertyModal.policyNumber}
                        </button>
                        <button className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-gray-600 bg-white border border-gray-200 rounded-full hover:border-gray-300">
                          Equipment - 12313124123
                        </button>
                        <button className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-gray-600 bg-white border border-gray-200 rounded-full hover:border-gray-300">
                          Umbrella - 12313124
                        </button>
                      </div>
                    </div>

                    {/* Policy Details */}
                    <div className="grid grid-cols-4 gap-4 mb-4 text-sm">
                      <div>
                        <p className="text-xs text-gray-500 mb-1">Policy Type</p>
                        <p className="font-medium text-gray-900">General</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500 mb-1">Policy Number</p>
                        <p className="font-medium text-gray-900">{selectedPropertyModal.policyNumber}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500 mb-1">Broker</p>
                        <p className="font-medium text-gray-900">{selectedPropertyModal.broker}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500 mb-1">Carrier</p>
                        <p className="font-medium text-gray-900">{selectedPropertyModal.carrier}</p>
                      </div>
                    </div>

                    {/* Coverage Table */}
                    <div className="overflow-hidden rounded-lg border border-gray-200">
                      <table className="w-full">
                        <thead>
                          <tr className="bg-gray-50 border-b border-gray-200">
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Limit Type ↑↓</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Limits ↑↓</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Expiration ↑↓</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">DED/SIR ↑↓</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Premium ↑↓</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Premium/U ↑↓</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                          {selectedPropertyModal.coverages.map((coverage, idx) => (
                            <tr key={idx} className="hover:bg-gray-50">
                              <td className="px-4 py-3 text-sm text-gray-900">{coverage.limitType}</td>
                              <td className="px-4 py-3 text-sm text-gray-600">{formatCurrency(coverage.premium)}</td>
                              <td className="px-4 py-3 text-sm text-gray-600">{selectedPropertyModal.renewalDate}</td>
                              <td className="px-4 py-3 text-sm text-gray-600">{formatCurrency(coverage.dedSir)}</td>
                              <td className="px-4 py-3 text-sm text-gray-600">{formatCurrency(coverage.premium)}</td>
                              <td className="px-4 py-3 text-sm text-gray-600">{formatCurrency(coverage.premiumV)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </section>

                  {/* SOV Section */}
                  <section>
                    <h3 className="text-sm font-semibold text-gray-900 mb-4">SOV</h3>
                    <div className="overflow-x-auto rounded-lg border border-gray-200">
                      <table className="w-full">
                        <thead>
                          <tr className="bg-gray-50 border-b border-gray-200">
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase whitespace-nowrap">Bldg # ↑↓</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase whitespace-nowrap">Address ↑↓</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase whitespace-nowrap">County ↑↓</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase whitespace-nowrap">Building Description ↑↓</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase whitespace-nowrap"># of MF Units ↑↓</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase whitespace-nowrap">Area / SQFT ↑↓</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase whitespace-nowrap">Total Building Area ↑↓</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                          <tr className="hover:bg-gray-50">
                            <td className="px-4 py-3 text-sm text-gray-900">1</td>
                            <td className="px-4 py-3 text-sm text-gray-600">100 East Road, New York, NY 10000</td>
                            <td className="px-4 py-3 text-sm text-gray-600">Kings County</td>
                            <td className="px-4 py-3 text-sm text-gray-600">Multi-unit</td>
                            <td className="px-4 py-3 text-sm text-gray-600">12</td>
                            <td className="px-4 py-3 text-sm text-gray-600">Yes</td>
                            <td className="px-4 py-3 text-sm text-gray-600">17,500</td>
                          </tr>
                          <tr className="hover:bg-gray-50">
                            <td className="px-4 py-3 text-sm text-gray-900">2</td>
                            <td className="px-4 py-3 text-sm text-gray-600">100 East Road, New York, NY 10000</td>
                            <td className="px-4 py-3 text-sm text-gray-600">Kings County</td>
                            <td className="px-4 py-3 text-sm text-gray-600">Multi-unit</td>
                            <td className="px-4 py-3 text-sm text-gray-600">12</td>
                            <td className="px-4 py-3 text-sm text-gray-600">-</td>
                            <td className="px-4 py-3 text-sm text-gray-600">17,500</td>
                          </tr>
                          <tr className="hover:bg-gray-50">
                            <td className="px-4 py-3 text-sm text-gray-900">3</td>
                            <td className="px-4 py-3 text-sm text-gray-600">100 East Road, New York, NY 10000</td>
                            <td className="px-4 py-3 text-sm text-gray-600">Kings County</td>
                            <td className="px-4 py-3 text-sm text-gray-600">Multi-unit</td>
                            <td className="px-4 py-3 text-sm text-gray-600">12</td>
                            <td className="px-4 py-3 text-sm text-gray-600">-</td>
                            <td className="px-4 py-3 text-sm text-gray-600">17,500</td>
                          </tr>
                          <tr className="bg-gray-50 font-medium">
                            <td className="px-4 py-3 text-sm text-gray-900" colSpan={4}>Totals</td>
                            <td className="px-4 py-3 text-sm text-gray-900">36</td>
                            <td className="px-4 py-3 text-sm text-gray-900"></td>
                            <td className="px-4 py-3 text-sm text-gray-900">50,000</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </section>

                  {/* Additional Info Section */}
                  <section>
                    <h3 className="text-sm font-semibold text-gray-900 mb-4">Additional Info</h3>
                    <div className="overflow-x-auto rounded-lg border border-gray-200">
                      <table className="w-full">
                        <thead>
                          <tr className="bg-gray-50 border-b border-gray-200">
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase whitespace-nowrap">Bldg # ↑↓</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase whitespace-nowrap">Roof Type ↑↓</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase whitespace-nowrap">Roof Year Last Replaced ↑↓</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase whitespace-nowrap">Roof Material ↑↓</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase whitespace-nowrap">Plumbing Year ↑↓</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase whitespace-nowrap">Electrical Year ↑↓</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase whitespace-nowrap">HVAC Year ↑↓</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase whitespace-nowrap">Fire Alarm Type ↑↓</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                          <tr className="hover:bg-gray-50">
                            <td className="px-4 py-3 text-sm text-gray-900">1</td>
                            <td className="px-4 py-3 text-sm text-gray-600">Flat</td>
                            <td className="px-4 py-3 text-sm text-gray-600">2020</td>
                            <td className="px-4 py-3 text-sm text-gray-600">TPO</td>
                            <td className="px-4 py-3 text-sm text-gray-600">2000</td>
                            <td className="px-4 py-3 text-sm text-gray-600">2000</td>
                            <td className="px-4 py-3 text-sm text-gray-600">2000</td>
                            <td className="px-4 py-3 text-sm text-gray-600">Manual</td>
                          </tr>
                          <tr className="hover:bg-gray-50">
                            <td className="px-4 py-3 text-sm text-gray-900">2</td>
                            <td className="px-4 py-3 text-sm text-gray-600">Pitched</td>
                            <td className="px-4 py-3 text-sm text-gray-600">2020</td>
                            <td className="px-4 py-3 text-sm text-gray-600">Ashphalt</td>
                            <td className="px-4 py-3 text-sm text-gray-600">2000</td>
                            <td className="px-4 py-3 text-sm text-gray-600">2000</td>
                            <td className="px-4 py-3 text-sm text-gray-600">2000</td>
                            <td className="px-4 py-3 text-sm text-gray-600">Automatic</td>
                          </tr>
                          <tr className="hover:bg-gray-50">
                            <td className="px-4 py-3 text-sm text-gray-900">3</td>
                            <td className="px-4 py-3 text-sm text-gray-600">Gable</td>
                            <td className="px-4 py-3 text-sm text-gray-600">2020</td>
                            <td className="px-4 py-3 text-sm text-gray-600">Metal</td>
                            <td className="px-4 py-3 text-sm text-gray-600">2000</td>
                            <td className="px-4 py-3 text-sm text-gray-600">2000</td>
                            <td className="px-4 py-3 text-sm text-gray-600">2000</td>
                            <td className="px-4 py-3 text-sm text-gray-600">Monitored</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </section>

                  {/* Non-Indoor Amenities Section */}
                  <section>
                    <h3 className="text-sm font-semibold text-gray-900 mb-4">Non-Indoor Amenities</h3>
                    <div className="overflow-hidden rounded-lg border border-gray-200">
                      <table className="w-full">
                        <thead>
                          <tr className="bg-gray-50 border-b border-gray-200">
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Non-Indoor Amenities ↑↓</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Included ↑↓</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                          <tr className="hover:bg-gray-50">
                            <td className="px-4 py-3 text-sm text-gray-900">Swimming Pool</td>
                            <td className="px-4 py-3 text-sm text-gray-600">Yes</td>
                          </tr>
                          <tr className="hover:bg-gray-50">
                            <td className="px-4 py-3 text-sm text-gray-900">Sand Volleyball Court</td>
                            <td className="px-4 py-3 text-sm text-gray-600">Yes</td>
                          </tr>
                          <tr className="hover:bg-gray-50">
                            <td className="px-4 py-3 text-sm text-gray-900">Basketball Court</td>
                            <td className="px-4 py-3 text-sm text-gray-600">Yes</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </section>

                  {/* Attachments Section */}
                  <section>
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-sm font-semibold text-gray-900">Attachments</h3>
                      <select className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg bg-white text-gray-700">
                        <option>2025</option>
                        <option>2024</option>
                        <option>2023</option>
                      </select>
                    </div>
                    <div className="space-y-2">
                      {/* Policy Documents */}
                      <div className="border border-gray-200 rounded-lg">
                        <div className="flex items-center justify-between px-4 py-3 hover:bg-gray-50 cursor-pointer">
                          <div className="flex items-center gap-3">
                            <FileText className="h-5 w-5 text-gray-400" />
                            <div>
                              <p className="text-sm font-medium text-gray-900">Policy Documents</p>
                              <p className="text-xs text-gray-500">3 files</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <button className="p-1.5 text-gray-400 hover:text-gray-600 rounded">
                              <Eye className="h-4 w-4" />
                            </button>
                            <button className="p-1.5 text-gray-400 hover:text-gray-600 rounded">
                              <Download className="h-4 w-4" />
                            </button>
                            <ChevronDown className="h-4 w-4 text-gray-400" />
                          </div>
                        </div>
                      </div>

                      {/* Certificates & Evidence */}
                      <div className="border border-gray-200 rounded-lg">
                        <div className="flex items-center justify-between px-4 py-3 hover:bg-gray-50 cursor-pointer">
                          <div className="flex items-center gap-3">
                            <FileText className="h-5 w-5 text-gray-400" />
                            <div>
                              <p className="text-sm font-medium text-gray-900">Certificates & Evidence</p>
                              <p className="text-xs text-gray-500">5 files</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <button className="p-1.5 text-gray-400 hover:text-gray-600 rounded">
                              <Eye className="h-4 w-4" />
                            </button>
                            <button className="p-1.5 text-gray-400 hover:text-gray-600 rounded">
                              <Download className="h-4 w-4" />
                            </button>
                            <ChevronDown className="h-4 w-4 text-gray-400" />
                          </div>
                        </div>
                      </div>

                      {/* Loss / Risk Files */}
                      <div className="border border-gray-200 rounded-lg">
                        <div className="flex items-center justify-between px-4 py-3 hover:bg-gray-50 cursor-pointer">
                          <div className="flex items-center gap-3">
                            <FileText className="h-5 w-5 text-gray-400" />
                            <div>
                              <p className="text-sm font-medium text-gray-900">Loss / Risk Files</p>
                              <p className="text-xs text-gray-500">5 files</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <button className="p-1.5 text-gray-400 hover:text-gray-600 rounded">
                              <Eye className="h-4 w-4" />
                            </button>
                            <button className="p-1.5 text-gray-400 hover:text-gray-600 rounded">
                              <Download className="h-4 w-4" />
                            </button>
                            <ChevronDown className="h-4 w-4 text-gray-400" />
                          </div>
                        </div>
                      </div>

                      {/* Endorsements */}
                      <div className="border border-gray-200 rounded-lg">
                        <div className="flex items-center justify-between px-4 py-3 hover:bg-gray-50 cursor-pointer">
                          <div className="flex items-center gap-3">
                            <FileText className="h-5 w-5 text-gray-400" />
                            <div>
                              <p className="text-sm font-medium text-gray-900">Endorsements</p>
                              <p className="text-xs text-gray-500">5 files</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <button className="p-1.5 text-gray-400 hover:text-gray-600 rounded">
                              <Eye className="h-4 w-4" />
                            </button>
                            <button className="p-1.5 text-gray-400 hover:text-gray-600 rounded">
                              <Download className="h-4 w-4" />
                            </button>
                            <ChevronDown className="h-4 w-4 text-gray-400" />
                          </div>
                        </div>
                      </div>
                    </div>
                  </section>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Export Modal */}
      <AnimatePresence>
        {showExportModal && (
          <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4">
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-black/40 backdrop-blur-sm"
              onClick={() => setShowExportModal(false)}
            />

            {/* Modal */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ duration: 0.2, ease: [0.25, 0.46, 0.45, 0.94] }}
              className="relative bg-white rounded-xl shadow-2xl w-full max-w-md z-[10000] overflow-hidden"
            >
              {/* Modal Header */}
              <div className="flex items-center justify-between p-5 border-b border-gray-100">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Export</h3>
                  <p className="text-sm text-gray-500">Select files to export</p>
                </div>
                <button
                  onClick={() => setShowExportModal(false)}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <X className="h-5 w-5 text-gray-400" />
                </button>
              </div>

              {/* Modal Content */}
              <div className="p-5 space-y-4">
                {/* SOV Option */}
                <div className="flex items-center justify-between py-2">
                  <div>
                    <p className="text-sm font-medium text-gray-900">SOV</p>
                    <p className="text-xs text-gray-500">Export SOV</p>
                  </div>
                  <button
                    onClick={() => setExportSOV(!exportSOV)}
                    className={cn(
                      'relative w-11 h-6 rounded-full transition-colors',
                      exportSOV ? 'bg-teal-500' : 'bg-gray-200'
                    )}
                  >
                    <span
                      className={cn(
                        'absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform shadow-sm',
                        exportSOV ? 'translate-x-5' : 'translate-x-0'
                      )}
                    />
                  </button>
                </div>

                {/* Other Documents Option */}
                <div className="flex items-center justify-between py-2">
                  <div>
                    <p className="text-sm font-medium text-gray-900">Other Documents</p>
                    <p className="text-xs text-gray-500">Export all property documents and reports</p>
                  </div>
                  <button
                    onClick={() => setExportDocuments(!exportDocuments)}
                    className={cn(
                      'relative w-11 h-6 rounded-full transition-colors',
                      exportDocuments ? 'bg-teal-500' : 'bg-gray-200'
                    )}
                  >
                    <span
                      className={cn(
                        'absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform shadow-sm',
                        exportDocuments ? 'translate-x-5' : 'translate-x-0'
                      )}
                    />
                  </button>
                </div>

                {/* CSV Option */}
                <div className="flex items-center justify-between py-2">
                  <div>
                    <p className="text-sm font-medium text-gray-900">CSV</p>
                    <p className="text-xs text-gray-500">Export all data to CSV file</p>
                  </div>
                  <button
                    onClick={() => setExportCSV(!exportCSV)}
                    className={cn(
                      'relative w-11 h-6 rounded-full transition-colors',
                      exportCSV ? 'bg-teal-500' : 'bg-gray-200'
                    )}
                  >
                    <span
                      className={cn(
                        'absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform shadow-sm',
                        exportCSV ? 'translate-x-5' : 'translate-x-0'
                      )}
                    />
                  </button>
                </div>

                {/* Selected count */}
                {selectedRows.size > 0 && (
                  <p className="text-xs text-gray-500 pt-2">
                    {selectedRows.size} {selectedRows.size === 1 ? 'property' : 'properties'} selected
                  </p>
                )}
              </div>

              {/* Modal Footer */}
              <div className="flex items-center justify-end gap-3 p-5 border-t border-gray-100 bg-gray-50">
                <button
                  onClick={() => setShowExportModal(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-800 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleExport}
                  disabled={!exportSOV && !exportDocuments && !exportCSV}
                  className="px-4 py-2 text-sm font-medium text-white bg-gray-900 hover:bg-gray-800 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Confirm
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
