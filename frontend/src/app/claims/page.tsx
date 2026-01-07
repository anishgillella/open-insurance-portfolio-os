'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  Search,
  Plus,
  Upload,
  ChevronDown,
  MoreVertical,
  Paperclip,
  Clock,
  AlertTriangle,
  X,
  Edit,
  Download,
  ChevronRight,
  Eye,
  Bell,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/primitives';
import {
  claimsApi,
  propertiesApi,
  type ClaimListItem,
  type ClaimDetail,
  type ClaimKanbanResponse,
  type Property,
} from '@/lib/api';

// Types
type KanbanColumn = 'open' | 'in_review' | 'processing' | 'closed';

interface KanbanColumnConfig {
  id: KanbanColumn;
  title: string;
  color: string;
}

const columns: KanbanColumnConfig[] = [
  { id: 'open', title: 'Open', color: 'text-green-600' },
  { id: 'in_review', title: 'In Review', color: 'text-blue-600' },
  { id: 'processing', title: 'Processing', color: 'text-orange-600' },
  { id: 'closed', title: 'Closed', color: 'text-gray-600' },
];

// Mock data for when API returns empty
const mockClaims: ClaimKanbanResponse = {
  open: [
    {
      id: 'mock-1',
      claim_number: '#12345',
      property_id: 'prop-1',
      property_name: 'Solana Apartments',
      status: 'open',
      claim_type: 'property_damage',
      date_of_loss: '2025-11-01',
      date_reported: '2025-11-11',
      total_incurred: 15000,
      attachment_count: 3,
      days_open: 7,
      has_alert: true,
      created_at: '2025-11-11T00:00:00Z',
    },
    {
      id: 'mock-2',
      claim_number: '#12345',
      property_id: 'prop-1',
      property_name: 'Solana Apartments',
      status: 'open',
      claim_type: 'water_damage',
      date_of_loss: '2025-11-05',
      date_reported: '2025-11-11',
      total_incurred: 8500,
      attachment_count: 2,
      days_open: 6,
      has_alert: false,
      created_at: '2025-11-11T00:00:00Z',
    },
    {
      id: 'mock-3',
      claim_number: '#12345',
      property_id: 'prop-1',
      property_name: 'Solana Apartments',
      status: 'open',
      claim_type: 'liability',
      date_of_loss: '2025-11-10',
      date_reported: '2025-11-11',
      total_incurred: 25000,
      attachment_count: 1,
      days_open: 1,
      has_alert: false,
      created_at: '2025-11-11T00:00:00Z',
    },
  ],
  in_review: [
    {
      id: 'mock-4',
      claim_number: '#12345',
      property_id: 'prop-1',
      property_name: 'Solana Apartments',
      status: 'in_review',
      claim_type: 'fire',
      date_of_loss: '2025-10-15',
      date_reported: '2025-11-11',
      total_incurred: 45000,
      attachment_count: 0,
      days_open: 1,
      has_alert: false,
      created_at: '2025-11-11T00:00:00Z',
    },
    {
      id: 'mock-5',
      claim_number: '#12345',
      property_id: 'prop-1',
      property_name: 'Solana Apartments',
      status: 'in_review',
      claim_type: 'theft',
      date_of_loss: '2025-11-07',
      date_reported: '2025-11-11',
      total_incurred: 12000,
      attachment_count: 1,
      days_open: 4,
      has_alert: false,
      created_at: '2025-11-11T00:00:00Z',
    },
  ],
  processing: [],
  closed: [
    {
      id: 'mock-6',
      claim_number: '#12345',
      property_id: 'prop-1',
      property_name: 'Solana Apartments',
      status: 'closed',
      claim_type: 'slip_fall',
      date_of_loss: '2025-09-01',
      date_reported: '2025-09-05',
      total_incurred: 5000,
      attachment_count: 4,
      days_open: null,
      has_alert: false,
      created_at: '2025-09-05T00:00:00Z',
    },
    {
      id: 'mock-7',
      claim_number: '#12345',
      property_id: 'prop-1',
      property_name: 'Solana Apartments',
      status: 'closed',
      claim_type: 'vandalism',
      date_of_loss: '2025-08-15',
      date_reported: '2025-08-20',
      total_incurred: 3500,
      attachment_count: 2,
      days_open: null,
      has_alert: false,
      created_at: '2025-08-20T00:00:00Z',
    },
    {
      id: 'mock-8',
      claim_number: '#12345',
      property_id: 'prop-1',
      property_name: 'Solana Apartments',
      status: 'closed',
      claim_type: 'equipment_breakdown',
      date_of_loss: '2025-07-10',
      date_reported: '2025-07-12',
      total_incurred: 18000,
      attachment_count: 2,
      days_open: null,
      has_alert: false,
      created_at: '2025-07-12T00:00:00Z',
    },
  ],
  total: 8,
};

// Mock claim detail for demo
const mockClaimDetail: ClaimDetail = {
  id: 'mock-1',
  claim_number: '#12345',
  property_id: 'prop-1',
  property_name: 'Solana Apartments',
  policy_id: null,
  status: 'in_review',
  litigation_status: null,
  claim_type: 'property_damage',
  date_of_loss: '2025-11-20',
  date_reported: '2025-11-20',
  date_closed: null,
  description: 'This claim pertains to reported damage or loss affecting the insured property. The incident involved damage to the structure and/or contents due to a covered event, such as fire, water, wind, theft, or vandalism. The policyholder has provided documentation and photographs of the affected areas to support the claim.',
  cause_of_loss: 'Structural collapse resulting in no injury',
  location_description: null,
  location_address: null,
  location_name: null,
  carrier_name: 'ABC Insurance',
  paid_loss: null,
  paid_expense: null,
  paid_medical: null,
  paid_indemnity: null,
  total_paid: null,
  reserve_loss: null,
  reserve_expense: null,
  reserve_medical: null,
  reserve_indemnity: null,
  total_reserve: null,
  incurred_loss: null,
  incurred_expense: null,
  total_incurred: 15000,
  deductible_applied: null,
  deductible_recovered: null,
  salvage_amount: null,
  subrogation_amount: null,
  net_incurred: null,
  claimant_name: null,
  claimant_type: null,
  injury_description: null,
  notes: null,
  attachment_count: 3,
  days_open: 7,
  has_alert: true,
  created_at: '2025-11-11T00:00:00Z',
  updated_at: '2025-12-05T00:00:00Z',
  timeline: [
    { status: 'open', label: 'Open', step_date: '2025-11-20', is_current: false, is_completed: true },
    { status: 'in_review', label: 'In Review', step_date: '2025-11-25', is_current: true, is_completed: false },
    { status: 'processing', label: 'Processing', step_date: null, is_current: false, is_completed: false },
    { status: 'closed', label: 'Closed', step_date: null, is_current: false, is_completed: false },
  ],
  contacts: [
    { role: 'Internal Lead', name: 'John Walker', email: 'john@walker.com', phone: '345-434-3625' },
    { role: 'Roofer', name: 'Brad Roofer', email: 'brad@roofer.com', phone: '334-343-66%' },
    { role: 'Insurer', name: 'Sarah Jones', email: 'sarah@jones.com', phone: '334-343-66%' },
    { role: 'Contact 4', name: 'Phil Eric', email: 'phil@eric.com', phone: '334-343-66%' },
    { role: 'Contact 5', name: 'Tom Sly', email: 'tom@sly.com', phone: '334-343-66%' },
    { role: 'Contact 6', name: 'Harry Sends', email: 'harry@sends.com', phone: '334-343-66%' },
    { role: 'Contact 7', name: 'Sam Serif', email: 'sam@serif.com', phone: '334-343-66%' },
    { role: 'Contact', name: 'Ciera Long', email: 'ciera@long.com', phone: '334-343-66%' },
  ],
  attachment_groups: [
    { category: 'evidence_photos', display_name: 'Evidence Photos', count: 3, attachments: [] },
    { category: 'policy_documents', display_name: 'Policy Documents', count: 3, attachments: [] },
    { category: 'payments', display_name: 'Payments', count: 5, attachments: [] },
  ],
};

// Claim Card Component
function ClaimCard({
  claim,
  onClick,
  onDragStart,
}: {
  claim: ClaimListItem;
  onClick: () => void;
  onDragStart: (e: React.DragEvent, claim: ClaimListItem) => void;
}) {
  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  return (
    <div
      draggable
      onDragStart={(e) => onDragStart(e, claim)}
      onClick={onClick}
      className="bg-white rounded-lg p-3 cursor-grab hover:shadow-md transition-shadow shadow-sm active:cursor-grabbing"
    >
      <div className="mb-3">
        <h4 className="font-medium text-gray-900 text-sm">Claim {claim.claim_number}</h4>
        <p className="text-sm text-gray-500">{claim.property_name}</p>
      </div>
      <div className="flex items-center gap-2 text-xs text-gray-400 pt-2 border-t border-gray-100">
        <span className="flex items-center gap-1">
          <Paperclip className="h-3 w-3" />
          {claim.attachment_count}
        </span>
        {claim.days_open !== null && (
          <span className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {claim.days_open}d
          </span>
        )}
        {claim.has_alert && (
          <span className="flex items-center gap-1 text-amber-500">
            <AlertTriangle className="h-3 w-3" />
          </span>
        )}
        <span>{formatDate(claim.date_reported)}</span>
      </div>
    </div>
  );
}

// Kanban Column Component
function KanbanColumnComponent({
  config,
  claims,
  onClaimClick,
  onAddClick,
  onDragStart,
  onDragOver,
  onDrop,
  isDragOver,
}: {
  config: KanbanColumnConfig;
  claims: ClaimListItem[];
  onClaimClick: (claim: ClaimListItem) => void;
  onAddClick: () => void;
  onDragStart: (e: React.DragEvent, claim: ClaimListItem) => void;
  onDragOver: (e: React.DragEvent) => void;
  onDrop: (e: React.DragEvent, targetColumn: KanbanColumn) => void;
  isDragOver: boolean;
}) {
  return (
    <div
      onDragOver={onDragOver}
      onDrop={(e) => onDrop(e, config.id)}
      className={cn(
        'bg-gray-200/60 rounded-xl p-3 flex-1 flex flex-col transition-colors',
        isDragOver && 'bg-gray-300/70 ring-2 ring-teal-400 ring-inset'
      )}
    >
      {/* Column Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <h3 className="font-medium text-gray-900 text-sm">{config.title}</h3>
          <span className={cn('text-sm font-medium', config.color)}>{claims.length}</span>
        </div>
        <div className="flex items-center gap-0.5">
          <button
            onClick={onAddClick}
            className="p-1 text-gray-400 hover:text-gray-600 rounded"
          >
            <Plus className="h-4 w-4" />
          </button>
          <button className="p-1 text-gray-400 hover:text-gray-600 rounded">
            <MoreVertical className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Column Content */}
      <div className="space-y-3 flex-1">
        {claims.map((claim) => (
          <ClaimCard
            key={claim.id}
            claim={claim}
            onClick={() => onClaimClick(claim)}
            onDragStart={onDragStart}
          />
        ))}
      </div>
    </div>
  );
}

// Claim Detail Modal Component
function ClaimDetailModal({
  claim,
  onClose,
}: {
  claim: ClaimDetail;
  onClose: () => void;
}) {
  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'TBD';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'numeric', day: 'numeric', year: 'numeric' });
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/20" onClick={onClose} />

      {/* Modal */}
      <div className="relative w-1/2 bg-white shadow-xl overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 z-10">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-500">Last Updated {formatDate(claim.updated_at)}</span>
            <button
              onClick={onClose}
              className="p-1 text-gray-400 hover:text-gray-600 rounded"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Claim {claim.claim_number}</h2>
              <p className="text-sm text-gray-500">{claim.property_name}</p>
            </div>
            <div className="flex items-center gap-2">
              <button className="flex items-center gap-1 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded-lg">
                <Upload className="h-4 w-4" />
                Upload
              </button>
              <button className="flex items-center gap-1 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded-lg">
                <Edit className="h-4 w-4" />
                Edit
              </button>
              <button className="flex items-center gap-1 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded-lg">
                <Download className="h-4 w-4" />
                Export
              </button>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="px-6 py-6 space-y-8">
          {/* Summary Section */}
          <section>
            <h3 className="text-sm font-semibold text-gray-900 mb-4">Summary</h3>
            <div className="space-y-3">
              <div className="flex">
                <span className="w-40 text-sm text-gray-500">Loss Date</span>
                <span className="text-sm text-gray-900">{formatDate(claim.date_of_loss)}</span>
              </div>
              <div className="flex">
                <span className="w-40 text-sm text-gray-500">Reported Date</span>
                <span className="text-sm text-gray-900">{formatDate(claim.date_reported)}</span>
              </div>
              <div className="flex">
                <span className="w-40 text-sm text-gray-500">Short Description</span>
                <span className="text-sm text-gray-900">{claim.cause_of_loss || 'N/A'}</span>
              </div>
              <div className="flex flex-col">
                <span className="text-sm text-gray-500 mb-1">Full Description</span>
                <p className="text-sm text-gray-700">{claim.description || 'No description provided.'}</p>
              </div>
            </div>
          </section>

          {/* Timeline Section */}
          <section>
            <h3 className="text-sm font-semibold text-gray-900 mb-4">Timeline</h3>
            <div className="flex items-center gap-2">
              {claim.timeline.map((step, index) => (
                <div key={step.status} className="flex items-center">
                  <div className="flex flex-col items-center">
                    <div
                      className={cn(
                        'w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium',
                        step.is_completed
                          ? 'bg-green-100 text-green-700'
                          : step.is_current
                          ? 'bg-green-500 text-white'
                          : 'bg-gray-100 text-gray-400'
                      )}
                    >
                      {index + 1}
                    </div>
                    <span className="text-xs text-gray-600 mt-1">{step.label}</span>
                    {step.step_date && (
                      <span className="text-xs text-gray-400">{formatDate(step.step_date)}</span>
                    )}
                  </div>
                  {index < claim.timeline.length - 1 && (
                    <ChevronRight className="h-4 w-4 text-gray-300 mx-2" />
                  )}
                </div>
              ))}
            </div>
          </section>

          {/* Contacts Section */}
          <section>
            <h3 className="text-sm font-semibold text-gray-900 mb-2">Contacts</h3>
            <p className="text-xs text-gray-500 mb-4">
              Internal Note: All contacts from the claim will be here for record keeping.
            </p>
            <div className="space-y-4">
              {claim.contacts.map((contact, index) => (
                <div key={index} className="flex justify-between items-start">
                  <span className="text-sm text-gray-500 w-32">{contact.role}</span>
                  <div className="text-right">
                    <p className="text-sm text-gray-900">{contact.name}</p>
                    <p className="text-xs text-gray-500">{contact.email}</p>
                    <p className="text-xs text-gray-500">{contact.phone}</p>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Attachments Section */}
          <section>
            <h3 className="text-sm font-semibold text-gray-900 mb-4">Attachments</h3>
            <div className="space-y-2">
              {claim.attachment_groups.map((group) => (
                <div
                  key={group.category}
                  className="flex items-center justify-between py-2 border-b border-gray-100"
                >
                  <div className="flex items-center gap-2">
                    <Paperclip className="h-4 w-4 text-gray-400" />
                    <span className="text-sm text-gray-900">{group.display_name}</span>
                    <span className="text-xs text-gray-400">{group.count} files</span>
                    <ChevronDown className="h-4 w-4 text-gray-400" />
                  </div>
                  <div className="flex items-center gap-2">
                    <button className="p-1 text-gray-400 hover:text-gray-600">
                      <Eye className="h-4 w-4" />
                    </button>
                    <button className="p-1 text-gray-400 hover:text-gray-600">
                      <Download className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

// Dropdown Component
function Dropdown({
  value,
  options,
  onChange,
  placeholder,
}: {
  value: string;
  options: { value: string; label: string }[];
  onChange: (value: string) => void;
  placeholder?: string;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const selectedOption = options.find((o) => o.value === value);

  return (
    <div className="relative w-full">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between w-full px-3 py-2 text-sm bg-white border border-gray-200 rounded-lg hover:bg-gray-50"
      >
        <span className="text-gray-700 truncate">{selectedOption?.label || placeholder}</span>
        <ChevronDown className="h-4 w-4 text-gray-400 flex-shrink-0 ml-2" />
      </button>
      {isOpen && (
        <>
          <div className="fixed inset-0" onClick={() => setIsOpen(false)} />
          <div className="absolute top-full mt-1 left-0 right-0 bg-white border border-gray-200 rounded-lg shadow-lg py-1 min-w-[160px] z-20">
            {options.map((option) => (
              <button
                key={option.value}
                onClick={() => {
                  onChange(option.value);
                  setIsOpen(false);
                }}
                className={cn(
                  'w-full px-3 py-2 text-left text-sm hover:bg-gray-50',
                  option.value === value ? 'text-teal-600 bg-teal-50' : 'text-gray-700'
                )}
              >
                {option.label}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

// Main Page Component
export default function ClaimsPage() {
  const [properties, setProperties] = useState<Property[]>([]);
  const [kanbanData, setKanbanData] = useState<ClaimKanbanResponse>(mockClaims);
  const [selectedClaim, setSelectedClaim] = useState<ClaimDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  // Drag and drop state
  const [draggedClaim, setDraggedClaim] = useState<ClaimListItem | null>(null);
  const [dragOverColumn, setDragOverColumn] = useState<KanbanColumn | null>(null);

  // Filters
  const [propertyFilter, setPropertyFilter] = useState<string>('all');
  const [yearFilter, setYearFilter] = useState<string>('last-year');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  // Fetch data
  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      try {
        const [propsData, kanbanResponse] = await Promise.all([
          propertiesApi.list(),
          claimsApi.getKanban(),
        ]);

        const propsArray = Array.isArray(propsData)
          ? propsData
          : (propsData as { properties?: Property[] })?.properties || [];
        setProperties(propsArray);

        // Use API data if available, otherwise use mock
        if (kanbanResponse.total > 0) {
          setKanbanData(kanbanResponse);
        }
      } catch (error) {
        console.error('Failed to fetch claims:', error);
        // Keep mock data on error
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleClaimClick = useCallback(async (claim: ClaimListItem) => {
    try {
      // Try to fetch real claim detail
      const detail = await claimsApi.get(claim.id);
      setSelectedClaim(detail);
    } catch {
      // Fall back to mock detail
      setSelectedClaim({
        ...mockClaimDetail,
        id: claim.id,
        claim_number: claim.claim_number,
        property_name: claim.property_name,
        status: claim.status,
      });
    }
  }, []);

  const handleAddClaim = useCallback(() => {
    alert('Add Claim functionality coming soon!');
  }, []);

  // Drag and drop handlers
  const handleDragStart = useCallback((e: React.DragEvent, claim: ClaimListItem) => {
    setDraggedClaim(claim);
    e.dataTransfer.effectAllowed = 'move';
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  }, []);

  const handleDragEnter = useCallback((column: KanbanColumn) => {
    setDragOverColumn(column);
  }, []);

  const handleDragLeave = useCallback(() => {
    setDragOverColumn(null);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent, targetColumn: KanbanColumn) => {
    e.preventDefault();

    if (!draggedClaim) return;

    const sourceColumn = draggedClaim.status as KanbanColumn;

    // Don't do anything if dropping in the same column
    if (sourceColumn === targetColumn) {
      setDraggedClaim(null);
      setDragOverColumn(null);
      return;
    }

    // Update the kanban data
    setKanbanData((prev) => {
      const newData = { ...prev };

      // Remove from source column
      newData[sourceColumn] = prev[sourceColumn].filter((c) => c.id !== draggedClaim.id);

      // Add to target column with updated status
      const updatedClaim = { ...draggedClaim, status: targetColumn };
      newData[targetColumn] = [...prev[targetColumn], updatedClaim];

      return newData;
    });

    // Reset drag state
    setDraggedClaim(null);
    setDragOverColumn(null);
  }, [draggedClaim]);

  const propertyOptions = [
    { value: 'all', label: 'All Properties' },
    ...properties.map((p) => ({ value: p.id, label: p.name })),
  ];

  const yearOptions = [
    { value: 'last-year', label: 'Last Year' },
    { value: 'last-2-years', label: 'Last 2 Years' },
    { value: 'last-5-years', label: 'Last 5 Years' },
    { value: 'all', label: 'All Time' },
  ];

  const statusOptions = [
    { value: 'all', label: 'All Statuses' },
    { value: 'open', label: 'Open' },
    { value: 'in_review', label: 'In Review' },
    { value: 'processing', label: 'Processing' },
    { value: 'closed', label: 'Closed' },
  ];

  return (
    <div className="flex flex-col h-full bg-gray-100 -m-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-semibold text-gray-900">Claims</h1>
        <div className="flex items-center gap-3">
          <button className="p-2 text-gray-400 hover:text-gray-600">
            <Bell className="h-5 w-5" />
          </button>
          <Button variant="ghost" size="sm" leftIcon={<Upload className="h-4 w-4" />}>
            Upload Document
          </Button>
        </div>
      </div>

      {/* Filters Row */}
      <div className="flex items-center gap-4 mb-4 w-full">
        {/* Search */}
        <div className="relative flex-[2] min-w-0">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search"
            className="w-full pl-10 pr-4 py-2 text-sm bg-white border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
          />
        </div>

        {/* Dropdowns */}
        <div className="flex-1 min-w-0">
          <Dropdown
            value={propertyFilter}
            options={propertyOptions}
            onChange={setPropertyFilter}
          />
        </div>
        <div className="flex-1 min-w-0">
          <Dropdown
            value={yearFilter}
            options={yearOptions}
            onChange={setYearFilter}
          />
        </div>
        <div className="flex-1 min-w-0">
          <Dropdown
            value={statusFilter}
            options={statusOptions}
            onChange={setStatusFilter}
          />
        </div>

        {/* Actions */}
        <Button
          variant="ghost"
          size="sm"
          leftIcon={<Plus className="h-4 w-4" />}
          onClick={handleAddClaim}
        >
          Add Claim
        </Button>
        <Button variant="ghost" size="sm" leftIcon={<Download className="h-4 w-4" />}>
          Export
        </Button>
      </div>

      {/* Kanban Board */}
      <div className="flex-1 flex flex-col min-h-0">
        <div className="flex gap-4 w-full flex-1">
          {columns.map((column) => (
            <div
              key={column.id}
              onDragEnter={() => handleDragEnter(column.id)}
              onDragLeave={handleDragLeave}
              className="flex-1 min-w-0 flex flex-col h-full"
            >
              <KanbanColumnComponent
                config={column}
                claims={kanbanData[column.id]}
                onClaimClick={handleClaimClick}
                onAddClick={handleAddClaim}
                onDragStart={handleDragStart}
                onDragOver={handleDragOver}
                onDrop={handleDrop}
                isDragOver={dragOverColumn === column.id}
              />
            </div>
          ))}
        </div>
      </div>

      {/* Claim Detail Modal */}
      {selectedClaim && (
        <ClaimDetailModal
          claim={selectedClaim}
          onClose={() => setSelectedClaim(null)}
        />
      )}
    </div>
  );
}
