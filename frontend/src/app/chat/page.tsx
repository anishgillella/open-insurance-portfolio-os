'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import {
  Send,
  Loader2,
  Upload,
  Bell,
  FileText,
  ChevronDown,
  Paperclip,
  Globe,
  ThumbsUp,
  Image,
  ArrowLeft,
  Sparkles,
  AlertCircle,
} from 'lucide-react';
import { Button } from '@/components/primitives';
import { cn } from '@/lib/utils';
import {
  streamChat,
  propertiesApi,
  renewalsApi,
  documentsApi,
  type ChatSource,
  type Property,
  type RenewalAlert,
  type Document,
} from '@/lib/api';

type TaskStatus = 'Open' | 'Acknowledged' | 'Resolved';

interface TaskViewState {
  task: RenewalAlert;
  response: string;
  isLoading: boolean;
}

// Mock tasks for demo when no real tasks exist
const mockTasks: RenewalAlert[] = [
  {
    id: 'mock-1',
    property_id: 'prop-1',
    property_name: 'Solana Apartments',
    policy_number: 'L1234567890',
    expiration_date: '2025-03-15',
    days_until_expiration: 45,
    severity: 'warning',
    title: 'Policy Renewal Required',
    message: 'Policy expires in 45 days',
    status: 'pending',
    created_at: new Date().toISOString(),
  },
  {
    id: 'mock-2',
    property_id: 'prop-2',
    property_name: 'Solana Apartments',
    policy_number: 'L1234567890',
    expiration_date: '2025-03-20',
    days_until_expiration: 50,
    severity: 'info',
    title: 'Policy Renewal Required',
    message: 'Policy expires in 50 days',
    status: 'pending',
    created_at: new Date().toISOString(),
  },
  {
    id: 'mock-3',
    property_id: 'prop-3',
    property_name: 'Solana Apartments',
    policy_number: 'L1234567890',
    expiration_date: '2025-04-01',
    days_until_expiration: 62,
    severity: 'info',
    title: 'Policy Renewal Required',
    message: 'Policy expires in 62 days',
    status: 'pending',
    created_at: new Date().toISOString(),
  },
  {
    id: 'mock-4',
    property_id: 'prop-4',
    property_name: 'Solana Apartments',
    policy_number: 'L1234567890',
    expiration_date: '2025-04-15',
    days_until_expiration: 76,
    severity: 'info',
    title: 'Policy Renewal Required',
    message: 'Policy expires in 76 days',
    status: 'pending',
    created_at: new Date().toISOString(),
  },
];

export default function AIAssistantPage() {
  // Data state - initialize tasks with mock data
  const [properties, setProperties] = useState<Property[]>([]);
  const [tasks, setTasks] = useState<RenewalAlert[]>(mockTasks);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoadingData, setIsLoadingData] = useState(true);

  // Filter state
  const [taskStatusFilter, setTaskStatusFilter] = useState<TaskStatus>('Open');
  const [selectedPropertyId, setSelectedPropertyId] = useState<string>('');

  // Chat state
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>();

  // View state - when viewing a specific task's AI response
  const [taskView, setTaskView] = useState<TaskViewState | null>(null);

  const inputRef = useRef<HTMLInputElement>(null);

  // Fetch data
  useEffect(() => {
    const fetchData = async () => {
      setIsLoadingData(true);
      try {
        const [propsData, alertsData, docsData] = await Promise.all([
          propertiesApi.list(),
          renewalsApi.getAlerts(),
          documentsApi.list(),
        ]);

        // Handle various API response formats for properties
        const propertiesList = Array.isArray(propsData)
          ? propsData
          : (propsData as { properties?: Property[] })?.properties || [];
        setProperties(propertiesList);

        // Handle alerts - use mock tasks if none exist
        const alertsList = Array.isArray(alertsData) ? alertsData : [];
        // Always use mock tasks if no real alerts, or merge them
        if (alertsList.length === 0) {
          setTasks(mockTasks);
        } else {
          setTasks(alertsList);
        }

        // Handle documents
        const docsList = docsData?.documents || [];
        setDocuments(docsList);
      } catch (error) {
        console.error('Error fetching data:', error);
        // On error, still show mock tasks
        setTasks(mockTasks);
      } finally {
        setIsLoadingData(false);
      }
    };

    fetchData();
  }, []);

  // Filter tasks by status
  const filteredTasks = tasks.filter((task) => {
    if (taskStatusFilter === 'Open') return task.status === 'pending';
    if (taskStatusFilter === 'Acknowledged') return task.status === 'acknowledged';
    if (taskStatusFilter === 'Resolved') return task.status === 'resolved';
    return true;
  });

  // Filter documents by property
  const filteredDocuments = selectedPropertyId
    ? documents.filter((doc) => doc.property_id === selectedPropertyId)
    : documents;

  // Handle viewing a task
  const handleViewTask = async (task: RenewalAlert) => {
    setTaskView({ task, response: '', isLoading: true });

    const query = `Please provide a summary for the renewal task: Policy ${task.policy_number || 'N/A'} for property ${task.property_name}. Include property details, insurance policy summary, and next actions.`;

    try {
      let content = '';
      await streamChat(
        query,
        {
          onContent: (chunk) => {
            content += chunk;
            setTaskView((prev) => (prev ? { ...prev, response: content } : null));
          },
          onSources: () => {},
          onDone: (newConversationId) => {
            setConversationId(newConversationId);
            setTaskView((prev) => (prev ? { ...prev, isLoading: false } : null));
          },
          onError: (error) => {
            setTaskView((prev) =>
              prev ? { ...prev, response: `Error: ${error}`, isLoading: false } : null
            );
          },
        },
        conversationId,
        task.property_id
      );
    } catch (err) {
      setTaskView((prev) =>
        prev
          ? {
              ...prev,
              response: `Error: ${err instanceof Error ? err.message : 'Failed to get response'}`,
              isLoading: false,
            }
          : null
      );
    }
  };

  // Handle chat send
  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const query = input.trim();
    setInput('');
    setIsLoading(true);

    // For demo, just show an alert
    alert(`Sending query: "${query}"\n\nIn production, this would start a new conversation.`);
    setIsLoading(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const formatFileSize = (bytes: number) => {
    if (!bytes) return '';
    if (bytes < 1024) return `${bytes}B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)}KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just Now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  const getDocumentIcon = (docType: string) => {
    return <FileText className="h-4 w-4 text-gray-400" />;
  };

  // Task View - when viewing a specific task's AI response
  if (taskView) {
    return (
      <div className="flex flex-col h-[calc(100vh-8rem)]">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-xl font-semibold text-gray-900">AI Assistant</h1>
          <div className="flex items-center gap-3">
            <button className="p-2 text-gray-400 hover:text-gray-600">
              <Bell className="h-5 w-5" />
            </button>
            <Button variant="ghost" size="sm" leftIcon={<Upload className="h-4 w-4" />}>
              Upload Document
            </Button>
          </div>
        </div>

        {/* Task Link */}
        <div className="flex items-center gap-2 mb-4">
          <button
            onClick={() => setTaskView(null)}
            className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700"
          >
            <ArrowLeft className="h-4 w-4" />
            Back
          </button>
          <span className="text-sm text-gray-400">|</span>
          <Sparkles className="h-4 w-4 text-gray-400" />
          <span className="text-sm text-gray-600">
            View task for Policy #{taskView.task.policy_number || 'N/A'}
          </span>
        </div>

        {/* Response Content */}
        <div className="flex-1 overflow-y-auto bg-white rounded-xl border border-gray-200 p-6">
          {taskView.isLoading && !taskView.response ? (
            <div className="flex items-center justify-center h-full">
              <Loader2 className="h-8 w-8 animate-spin text-teal-500" />
            </div>
          ) : (
            <div className="prose prose-sm max-w-none">
              <ReactMarkdown>{taskView.response}</ReactMarkdown>
              {taskView.isLoading && (
                <span className="inline-block w-2 h-4 bg-teal-500 animate-pulse ml-1" />
              )}
            </div>
          )}

          {!taskView.isLoading && taskView.response && (
            <div className="mt-6 pt-4 border-t border-gray-100">
              <p className="text-sm text-gray-500">Would you like me to assist with this?</p>
            </div>
          )}
        </div>

        {/* Chat Input */}
        <div className="mt-4">
          <ChatInput
            value={input}
            onChange={setInput}
            onSend={handleSend}
            onKeyDown={handleKeyDown}
            isLoading={isLoading}
            inputRef={inputRef}
          />
        </div>
      </div>
    );
  }

  // Main Dashboard View
  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold text-gray-900">AI Assistant</h1>
        <div className="flex items-center gap-3">
          <button className="p-2 text-gray-400 hover:text-gray-600">
            <Bell className="h-5 w-5" />
          </button>
          <Button variant="ghost" size="sm" leftIcon={<Upload className="h-4 w-4" />}>
            Upload Document
          </Button>
        </div>
      </div>

      {/* Welcome Message */}
      <div className="text-center mb-8">
        <h2 className="text-2xl font-semibold text-gray-900 mb-2">How can I help you today?</h2>
        <p className="text-gray-500">
          Ask me anything about your policies, documents, or upcoming renewals.
        </p>
      </div>

      {/* Two Column Layout */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-6 min-h-0 overflow-hidden">
        {/* Tasks Section */}
        <div className="flex flex-col min-h-0">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-gray-700">Tasks</h3>
            <div className="relative">
              <select
                value={taskStatusFilter}
                onChange={(e) => setTaskStatusFilter(e.target.value as TaskStatus)}
                className="appearance-none pl-3 pr-8 py-1.5 text-sm border border-gray-200 rounded-lg bg-white text-gray-700 cursor-pointer focus:outline-none focus:ring-2 focus:ring-teal-500"
              >
                <option value="Open">Open</option>
                <option value="Acknowledged">Acknowledged</option>
                <option value="Resolved">Resolved</option>
              </select>
              <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
            </div>
          </div>

          <div className="flex-1 overflow-y-auto space-y-2">
            {isLoadingData ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
              </div>
            ) : filteredTasks.length === 0 ? (
              <div className="text-center py-8 text-gray-500 text-sm">
                No {taskStatusFilter.toLowerCase()} tasks
              </div>
            ) : (
              filteredTasks.map((task) => (
                <div
                  key={task.id}
                  className="flex items-center justify-between p-3 bg-white rounded-lg border border-gray-200 hover:border-gray-300 transition-colors"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {task.property_name || 'Unknown Property'}
                    </p>
                    <p className="text-xs text-gray-500 truncate">
                      Renew Policy #{task.policy_number || 'N/A'} &bull; {task.status}
                    </p>
                  </div>
                  <button
                    onClick={() => handleViewTask(task)}
                    className="ml-3 px-3 py-1 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded transition-colors"
                  >
                    View
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Documents Section */}
        <div className="flex flex-col min-h-0">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-gray-700">Documents</h3>
            <div className="relative">
              <select
                value={selectedPropertyId}
                onChange={(e) => setSelectedPropertyId(e.target.value)}
                className="appearance-none pl-3 pr-8 py-1.5 text-sm border border-gray-200 rounded-lg bg-white text-gray-700 cursor-pointer focus:outline-none focus:ring-2 focus:ring-teal-500 max-w-[180px]"
              >
                <option value="">All Properties</option>
                {properties.map((property) => (
                  <option key={property.id} value={property.id}>
                    {property.name}
                  </option>
                ))}
              </select>
              <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
            </div>
          </div>

          <div className="flex-1 overflow-y-auto space-y-2">
            {isLoadingData ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
              </div>
            ) : filteredDocuments.length === 0 ? (
              <div className="text-center py-8 text-gray-500 text-sm">No documents found</div>
            ) : (
              filteredDocuments.slice(0, 10).map((doc) => (
                <div
                  key={doc.id}
                  className="flex items-center gap-3 p-3 bg-white rounded-lg border border-gray-200 hover:border-gray-300 transition-colors cursor-pointer"
                >
                  {getDocumentIcon(doc.document_type)}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {doc.file_name || 'Untitled Document'}
                    </p>
                    <p className="text-xs text-gray-500">
                      Uploaded {formatDate(doc.created_at)}
                      {doc.document_type && ` \u2022 ${doc.document_type}`}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Chat Input */}
      <div className="mt-6">
        <ChatInput
          value={input}
          onChange={setInput}
          onSend={handleSend}
          onKeyDown={handleKeyDown}
          isLoading={isLoading}
          inputRef={inputRef}
        />
      </div>
    </div>
  );
}

// Chat Input Component
interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  onKeyDown: (e: React.KeyboardEvent) => void;
  isLoading: boolean;
  inputRef: React.RefObject<HTMLInputElement | null>;
}

function ChatInput({ value, onChange, onSend, onKeyDown, isLoading, inputRef }: ChatInputProps) {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 p-3 bg-white rounded-xl border border-gray-200 focus-within:ring-2 focus-within:ring-teal-500 focus-within:border-transparent">
        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Ask AI anything"
          className="flex-1 bg-transparent text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none"
          disabled={isLoading}
        />

        {/* Action Buttons */}
        <div className="flex items-center gap-1">
          {/* Model Selector */}
          <div className="flex items-center gap-1 px-2 py-1 text-xs text-gray-500 bg-gray-100 rounded-lg">
            <span>GPT-5</span>
            <ChevronDown className="h-3 w-3" />
          </div>

          <button className="p-1.5 text-gray-400 hover:text-gray-600 rounded">
            <Paperclip className="h-4 w-4" />
          </button>
          <button className="p-1.5 text-gray-400 hover:text-gray-600 rounded">
            <Globe className="h-4 w-4" />
          </button>
          <button className="p-1.5 text-gray-400 hover:text-gray-600 rounded">
            <ThumbsUp className="h-4 w-4" />
          </button>
          <button className="p-1.5 text-gray-400 hover:text-gray-600 rounded">
            <Image className="h-4 w-4" />
          </button>

          {/* Send Button */}
          <button
            onClick={onSend}
            disabled={!value.trim() || isLoading}
            className={cn(
              'p-2 rounded-full transition-colors',
              value.trim() && !isLoading
                ? 'bg-teal-500 text-white hover:bg-teal-600'
                : 'bg-gray-200 text-gray-400 cursor-not-allowed'
            )}
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </button>
        </div>
      </div>

      {/* Disclaimer */}
      <p className="text-xs text-gray-400 text-center flex items-center justify-center gap-1">
        <AlertCircle className="h-3 w-3" />
        Openia is trained with insights from top brokers, consultants, and attorneys. Responses may
        contain inaccuracies, please verify before taking action.
      </p>
    </div>
  );
}
